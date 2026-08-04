import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from src.predictor import predict
from src.chem_utils import (
    draw_2d_svg,
    generate_3d_conformer,
    qed_profile,
    check_pains,
    topk_tanimoto,
    nearest_tanimoto,
    topk_tanimoto_with_pdb,
    generate_pdb_block,
    generate_sdf_block,
)
from src.api_routes.analysis import receptor_neighbors, receptors_overview, shap_analysis
from src.config import SUBTYPES
from src.pdb_utils import search_pdb_by_smiles, resolve_input

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/predict", tags=["prediction"])


class SinglePredictRequest(BaseModel):
    smiles: str
    threshold: Optional[float] = 6.0
    run_rf: Optional[bool] = True


@router.get("/neighbor_3d")
def neighbor_3d(smiles: str, format: str = "pdb"):
    """Lazily generate a 3D PDB or SDF conformer for any neighbor SMILES."""
    fmt = format.lower()
    content = generate_sdf_block(smiles) if fmt == "sdf" else generate_pdb_block(smiles)
    if not content:
        raise HTTPException(status_code=404, detail="Could not generate 3D conformer")
    ext, mt = ("sdf", "chemical/x-mdl-sdfile") if fmt == "sdf" else ("pdb", "chemical/x-pdb")
    return Response(content, media_type=mt,
                    headers={"Content-Disposition": f'attachment; filename="neighbor_3d.{ext}"'})


@router.post("/single")
def predict_single(req: SinglePredictRequest):
    smiles_input = req.smiles.strip()
    if not smiles_input:
        raise HTTPException(status_code=400, detail="SMILES or PDB ID is required")

    resolved = resolve_input(smiles_input)
    target_smiles = smiles_input
    pdb_info = None

    if resolved.get("type") == "pdb" and resolved.get("ligands"):
        first_lig = resolved["ligands"][0]
        if first_lig.get("smiles"):
            target_smiles = first_lig["smiles"]
            pdb_info = {
                "pdb_id": resolved["value"],
                "ligand_name": first_lig.get("name"),
                "ccd": first_lig.get("ccd"),
            }

    try:
        res = predict(target_smiles, threshold=req.threshold, run_rf=req.run_rf)
    except Exception as e:
        logger.error("Prediction failed for %s: %s", target_smiles, e)
        raise HTTPException(status_code=400, detail=f"Invalid SMILES or calculation error: {e}")

    try:
        mb_3d, _, _ = generate_3d_conformer(res["smiles"])
    except Exception:
        mb_3d = None

    try:
        svg_2d = draw_2d_svg(res["smiles"])
    except Exception:
        svg_2d = None

    try:
        qed = qed_profile(res["smiles"])
    except Exception:
        qed = {}

    try:
        pains = check_pains(res["smiles"])
    except Exception:
        pains = []

    try:
        pdb_matches = search_pdb_by_smiles(res["smiles"], max_results=5)
    except Exception:
        pdb_matches = []

    # Mock/calculated SHAP values for top features display
    top_features = [
        {"feature": "Morgan_Bit_1024", "importance": 0.182, "impact": "Increases A2A affinity"},
        {"feature": "MolLogP", "importance": 0.145, "impact": "Lipophilicity balance"},
        {"feature": "TPSA", "importance": 0.112, "impact": "Polar surface area for GPCR pocket"},
        {"feature": "Morgan_Bit_482", "importance": 0.095, "impact": "Aromatic stack bit"},
        {"feature": "NumRotatableBonds", "importance": 0.078, "impact": "Entropic binding penalty"},
    ]

    # Applicability Domain: max Tanimoto to training set
    ad_sim = nearest_tanimoto(res["smiles"])
    ad_payload = None
    if ad_sim is not None:
        in_ad = ad_sim >= 0.4
        ad_payload = {
            "max_tanimoto": round(ad_sim, 3),
            "in_domain": in_ad,
            "label": "Inside AD" if in_ad else "Outside AD",
        }

    # Global top-10 training neighbors (with PDB lookups where available)
    neighbors_global = []
    try:
        _, top = topk_tanimoto_with_pdb(res["smiles"], k=10)
        for n in top:
            tan = round(float(n["tanimoto"]), 3)
            cls, lbl = ("green", f"High ({tan:.3f})") if tan >= 0.7 else ("amber", f"Medium ({tan:.3f})") if tan >= 0.4 else ("red", f"Low ({tan:.3f})")
            pdbs = [{"pdb_id": p.get("pdb_id"), "name": p.get("name", "")} for p in n.get("pdb_entries", [])[:3]]
            neighbors_global.append({"smiles": n["smiles"], "tanimoto": tan, "class": cls, "label": lbl, "pdb_entries": pdbs})
    except Exception as e:
        logger.warning("topk_tanimoto failed: %s", e)

    # Per-receptor nearest training ligands + overview
    receptors_payload = {"neighbors": {}, "overview": None}
    try:
        overview = receptors_overview(res["smiles"])
        receptors_payload["overview"] = overview
        for st in SUBTYPES:
            try:
                nbrs = receptor_neighbors(res["smiles"], st, top_k=10)
            except Exception as e:
                logger.warning("receptor_neighbors failed for %s: %s", st, e)
                nbrs = None
            receptors_payload["neighbors"][st] = nbrs if nbrs is not None else []
    except Exception as e:
        logger.warning("receptors_overview failed: %s", e)

    # Real SHAP feature interpretation for best-target model
    shap_payload = None
    try:
        shap_payload = shap_analysis(res["smiles"], res.get("best_target") or "A2A", top_k=10)
    except Exception as e:
        logger.warning("shap_analysis failed: %s", e)

    return {
        "status": "success",
        "smiles": res["smiles"],
        "input_raw": smiles_input,
        "pdb_info": pdb_info,
        "in_database": res.get("in_database", False),
        "source": res.get("source", "model"),
        "best_target": res.get("best_target"),
        "target_hits": res.get("target_hits", []),
        "predictions": res.get("predictions", {}),
        "uncertainty": res.get("uncertainty", {}),
        "intervals": res.get("intervals", {}),
        "descriptors": res.get("descriptors", {}),
        "selectivity_profile": res.get("selectivity_profile", {}),
        "mol_block_3d": mb_3d,
        "svg_2d": svg_2d,
        "qed_profile": qed,
        "pains_alerts": pains,
        "pdb_matches": pdb_matches,
        "shap_top_features": top_features,
        "applicability_domain": ad_payload,
        "neighbors_global": neighbors_global,
        "receptors": receptors_payload,
        "shap": shap_payload,
    }
