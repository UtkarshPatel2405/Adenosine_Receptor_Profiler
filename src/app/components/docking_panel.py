# src/app/components/docking_panel.py
"""Docking panel — Ligand (SMILES) and multiple receptor options with similarity to training neighbors per receptor."""
import json, pickle
import streamlit as st
import pandas as pd
import numpy as np
from functools import lru_cache
from rdkit import Chem
from rdkit.Chem import DataStructs
from rdkit.Chem.rdFingerprintGenerator import GetMorganGenerator
from src.docking import ADENOSINE_TARGETS
from src.config import PROCESSED_DATA_DIR

_MORGAN = GetMorganGenerator(radius=2, fpSize=2048)

# Non-pharmacological CCD codes: membrane lipids, detergents, ions, buffers
# that co-crystallize with GPCRs but are NOT the drug-like ligand.
_NON_PHARMA_CCD = {
    "CLR", "OLA", "OLB", "PLM", "P4G", "Y01", "P6G", "PEG", "GOL",
    "SO4", "PO4", "EDO", "ACE", "BOG", "LDA", "MYR", "PAM", "STE",
    "DMS", "MES", "TRS", "CIT", "MPD", "EPE", "PGE", "PG4", "BMA",
    "NAG", "FUC", "MAN", "GAL", "GLC",
}


@lru_cache(maxsize=1)
def _load_training_data():
    """Load training SMILES, fingerprints, and lookup table."""
    train_smiles_path = PROCESSED_DATA_DIR / "train_smiles.pkl"
    train_fps_path = PROCESSED_DATA_DIR / "train_fps.pkl"
    db_lookup_path = PROCESSED_DATA_DIR / "db_lookup_train.json"
    if not all(p.exists() for p in [train_smiles_path, train_fps_path, db_lookup_path]):
        return None, None, None
    try:
        with open(train_smiles_path, "rb") as f:
            train_smiles = pickle.load(f)
        with open(train_fps_path, "rb") as f:
            train_fps = pickle.load(f)
        with open(db_lookup_path) as f:
            lookup = json.load(f)
        return train_smiles, train_fps, lookup
    except Exception:
        return None, None, None


def _get_receptor_neighbors(smiles: str, subtype: str, top_k: int = 10):
    """Find top-k nearest training set neighbors for a given receptor subtype."""
    train_smiles, train_fps, lookup = _load_training_data()
    if train_smiles is None or train_fps is None or lookup is None:
        return None
    
    query_mol = Chem.MolFromSmiles(smiles)
    if query_mol is None:
        return None
    query_fp = _MORGAN.GetFingerprint(query_mol)
    
    # Build per-subtype fingerprint index
    results = []
    seen_smiles = set()
    for i, tsmiles in enumerate(train_smiles):
        if tsmiles in seen_smiles:
            continue
        seen_smiles.add(tsmiles)
        entry = lookup.get(tsmiles)
        if entry and subtype in entry and entry[subtype] is not None:
            try:
                pchembl = float(entry[subtype])
                if pchembl > 0:
                    sim = DataStructs.TanimotoSimilarity(query_fp, train_fps[i])
                    results.append((sim, tsmiles, pchembl, i))
            except (ValueError, TypeError):
                continue
    
    results.sort(key=lambda x: x[0], reverse=True)
    return results[:top_k]


def _calc_tanimoto(smiles1: str, smiles2: str) -> float:
    mol1 = Chem.MolFromSmiles(smiles1)
    mol2 = Chem.MolFromSmiles(smiles2)
    if mol1 is None or mol2 is None:
        return 0.0
    fp1 = _MORGAN.GetFingerprint(mol1)
    fp2 = _MORGAN.GetFingerprint(mol2)
    return DataStructs.TanimotoSimilarity(fp1, fp2)


def render_docking_panel(smiles: str, best_target: str):
    """Show ligand info, multiple receptor options, and similarity to training neighbors for that receptor."""
    st.markdown('<div class="sd"></div>', unsafe_allow_html=True)
    
    st.markdown(
        f'<div class="ct">🧬 Receptor Binding Analysis  <span class="tag tp">Ligand (SMILES) → Adenosine Receptors</span></div>',
        unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:.7rem;color:#94a3b8;line-height:1.5;margin-bottom:.5rem">'
        f'Ligand: <code style="font-size:.65rem;color:#e2e8f0">{smiles[:80]}{".." if len(smiles)>80 else ""}</code>'
        f'</div>', unsafe_allow_html=True)

    receptor_options = list(ADENOSINE_TARGETS.keys())
    receptor_labels = {k: f"{k} ({ADENOSINE_TARGETS[k]['pdb']})" for k in receptor_options}
    
    selected_receptor = st.selectbox(
        "Select Receptor Subtype",
        receptor_options,
        format_func=lambda x: receptor_labels[x],
        index=receptor_options.index(best_target) if best_target in receptor_options else 1,
        key="dock_receptor_select"
    )

    target_info = ADENOSINE_TARGETS[selected_receptor]
    
    # ── Dynamic PDB Template Suggestion ──
    suggested_pdbs = []
    pdb_registry_path = PROCESSED_DATA_DIR / "adenosine_pdb_ligands.json"
    if pdb_registry_path.exists():
        try:
            with open(pdb_registry_path) as f:
                pdb_reg = json.load(f)
            subtype_pdbs = pdb_reg.get(selected_receptor, [])
            query_mol = Chem.MolFromSmiles(smiles)
            if query_mol:
                query_fp = _MORGAN.GetFingerprint(query_mol)
                for entry in subtype_pdbs:
                    pdb_id = entry["pdb_id"]
                    max_sim = 0.0
                    best_lig_name = ""
                    for lig in entry["ligands"]:
                        # Skip non-pharmacological ligands (lipids, detergents, etc.)
                        if lig.get("ccd", "") in _NON_PHARMA_CCD:
                            continue
                        lig_mol = Chem.MolFromSmiles(lig["smiles"])
                        if lig_mol:
                            lig_fp = _MORGAN.GetFingerprint(lig_mol)
                            sim = DataStructs.TanimotoSimilarity(query_fp, lig_fp)
                            if sim > max_sim:
                                max_sim = sim
                                best_lig_name = lig["name"]
                    if max_sim > 0:  # Only include PDB entries with real pharmacological ligands
                        suggested_pdbs.append((max_sim, pdb_id, best_lig_name))
                suggested_pdbs.sort(key=lambda x: x[0], reverse=True)
        except Exception:
            pass

    best_pdb = target_info["pdb"]
    best_sim = 0.0
    best_lig = ""
    if suggested_pdbs:
        best_sim, best_pdb, best_lig = suggested_pdbs[0]

    if best_sim >= 0.4:
        st.markdown(
            f'<div class="sci-box" style="margin-bottom:.5rem;border-left:4px solid #10b981;padding:.4rem">'
            f'💡 <b>Dynamically suggested template for docking: <a href="https://www.rcsb.org/structure/{best_pdb}" target="_blank" style="color:#38bdf8">{best_pdb}</a></b> '
            f'(ligand: {best_lig}, Tanimoto similarity: <b>{best_sim:.3f}</b>)<br>'
            f'Receptor: {target_info["name"]} (Chain {target_info["chain"]}). '
            f'This resolved structure was co-crystallized with a highly similar chemical scaffold.'
            f'</div>', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="sci-box" style="margin-bottom:.5rem;padding:.4rem">'
            f'💡 Suggested template for docking: <b><a href="https://www.rcsb.org/structure/{best_pdb}" target="_blank" style="color:#38bdf8">{best_pdb}</a></b> '
            f'(Default template)<br>'
            f'Receptor: {target_info["name"]}. No matching co-crystallized ligand scaffolds found.'
            f'</div>', unsafe_allow_html=True)

    # Similarity to training set neighbors for this receptor
    st.markdown('<div class="ct" style="margin-top:.6rem">📊 Nearest Training Ligands for Selected Receptor</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:.6rem;color:#64748b;margin-bottom:.3rem">'
        'Tanimoto similarity (Morgan FP, radius=2, 2048-bit) between query ligand and training set compounds '
        'with known activity for this receptor subtype. Higher similarity = more reliable binding prediction.'
        '</div>', unsafe_allow_html=True)

    neighbors = _get_receptor_neighbors(smiles, selected_receptor, top_k=10)
    if neighbors is None:
        st.info("Training data not available. Run `python -m src.retrain_production` first.")
    elif not neighbors:
        st.info(f"No training compounds with activity data for {selected_receptor} found.")
    else:
        rows = []
        for sim, tsmiles, pchembl, _ in neighbors:
            if sim >= 0.7:
                sim_class = "badge badge-green"
                sim_label = f"High ({sim:.3f})"
            elif sim >= 0.4:
                sim_class = "badge badge-amber"
                sim_label = f"Medium ({sim:.3f})"
            else:
                sim_class = "badge badge-red"
                sim_label = f"Low ({sim:.3f})"
            activity_class = "badge badge-green" if pchembl >= 6.0 else "badge badge-amber" if pchembl >= 4.5 else "badge badge-red"
            
            # Lookup real PDB IDs or generate 3D PDB/SDF conformers
            from src.pdb_utils import get_pdb_ids_for_smiles
            from src.chem_utils import generate_pdb_block, generate_sdf_block
            import base64

            pdbs = get_pdb_ids_for_smiles(tsmiles)
            if pdbs:
                pdb_links = " ".join(
                    f'<a href="{p["url"]}" target="_blank" class="badge badge-blue" title="{p.get("name", p["pdb_id"])}">{p["pdb_id"]}</a>'
                    for p in pdbs[:3]
                )
            else:
                # Generate 3D PDB & 3D SDF conformers on-the-fly
                gen_links = []
                pdb_text = generate_pdb_block(tsmiles)
                if pdb_text:
                    pdb_b64 = base64.b64encode(pdb_text.encode('utf-8')).decode('utf-8')
                    gen_links.append(f'<a href="data:chemical/x-pdb;base64,{pdb_b64}" download="ligand_3d.pdb" class="badge badge-cyan" title="Download generated 3D PDB conformer">📥 3D PDB</a>')
                sdf_text = generate_sdf_block(tsmiles)
                if sdf_text:
                    sdf_b64 = base64.b64encode(sdf_text.encode('utf-8')).decode('utf-8')
                    gen_links.append(f'<a href="data:chemical/x-mdl-sdfile;base64,{sdf_b64}" download="ligand_3d.sdf" class="badge badge-purple" title="Download generated 3D SDF conformer">📥 3D SDF</a>')
                pdb_links = " ".join(gen_links) if gen_links else '<span style="color:#64748b;font-size:.65rem">—</span>'

            rows.append({
                "SMILES": f'<span title="{tsmiles}" style="display:inline-block;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;vertical-align:middle;font-family:monospace;font-size:.68rem;color:#e2e8f0">{tsmiles}</span>',
                "Tanimoto": sim_label,
                "pChEMBL": f'{pchembl:.2f}',
                "Activity": f'<span class="{activity_class}">{"Active" if pchembl >= 6 else "Weak" if pchembl >= 4.5 else "Inactive"}</span>',
                "PDB / 3D Structure": pdb_links,
            })
        
        df = pd.DataFrame(rows)
        st.markdown(
            df.to_html(escape=False, index=False, classes="dataframe"),
            unsafe_allow_html=True
        )
        st.markdown(
            '<div style="font-size:.55rem;color:#64748b;margin-top:.3rem">'
            'Tanimoto ≥ 0.7 = high confidence in similar binding; 0.4–0.7 = moderate; < 0.4 = low confidence. '
            'pChEMBL ≥ 6.0 = active (μM affinity or better). PDB / 3D Structure provides co-crystal PDB entries or generated 3D PDB / 3D SDF conformer downloads.</div>',
            unsafe_allow_html=True)

    # All receptors overview
    with st.expander("📋 All Receptor Subtypes Overview", expanded=False):
        st.markdown('<div class="section-header">Adenosine Receptor Subtypes & PDB Structures</div>', unsafe_allow_html=True)
        
        overview_rows = []
        for rec in receptor_options:
            info = ADENOSINE_TARGETS[rec]
            rec_neighbors = _get_receptor_neighbors(smiles, rec, top_k=3)
            max_sim = rec_neighbors[0][0] if rec_neighbors else 0.0
            best_smiles = rec_neighbors[0][1] if rec_neighbors else ""
            n_active = sum(1 for n in rec_neighbors if n[2] >= 6.0) if rec_neighbors else 0
            
            sim_class = "badge badge-green" if max_sim >= 0.7 else "badge badge-amber" if max_sim >= 0.4 else "badge badge-red"
            
            overview_rows.append({
                "Subtype": rec,
                "Receptor Name": info["name"],
                "PDB ID": f'<a href="https://www.rcsb.org/structure/{info["pdb"]}" target="_blank" style="color:#38bdf8">{info["pdb"]}</a>',
                "Max Similarity": f'<span class="{sim_class}">{max_sim:.3f}</span>',
                "Active Neighbors": n_active,
            })
        
        df_overview = pd.DataFrame(overview_rows)
        st.markdown(
            df_overview.to_html(escape=False, index=False, classes="dataframe"),
            unsafe_allow_html=True
        )
        st.markdown(
            '<div style="font-size:.55rem;color:#64748b;margin-top:.3rem">'
            'Max similarity to any training compound with activity data for that receptor subtype.</div>',
            unsafe_allow_html=True)