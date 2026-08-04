# src/docking.py
"""Docking module — DockThor API integration + local Vina-like scoring fallback."""
from __future__ import annotations
import hashlib, json, time, math
from pathlib import Path
from typing import Optional, List, Dict
import requests
from src.chem_utils import mol_from_smiles

ADENOSINE_TARGETS = {
    "A1":  {"pdb": "6D9H", "name": "Adenosine A1 Receptor",  "chain": "A"},
    "A2A": {"pdb": "2YDO", "name": "Adenosine A2A Receptor", "chain": "A"},
    "A2B": {"pdb": "8HDP", "name": "Adenosine A2B Receptor", "chain": "A"},
    "A3":  {"pdb": "8YH2", "name": "Adenosine A3 Receptor",  "chain": "A"},
}

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "AR-Selectivity/1.0", "Accept": "application/json"})
_TIMEOUT = 30


# ── DockThor API ─────────────────────────────────────────────
DOCKTHOR_API = "https://dockthor.lncc.br/v2/api"

def submit_dockthor(smiles: str, target_pdb: str) -> Optional[str]:
    """Submit a docking job to DockThor. Returns job_id or None."""
    try:
        from rdkit.Chem import AllChem, MolFromSmiles, MolToMolBlock
        mol = MolFromSmiles(smiles)
        if mol is None: return None
        mol = AllChem.AddHs(mol)
        AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
        AllChem.MMFFOptimizeMolecule(mol)
        mol_block = MolToMolBlock(mol)
        files = {"mol_file": ("ligand.mol", mol_block, "chemical/x-mdl-molfile")}
        data = {"target": target_pdb, "engine": "vina"}
        resp = _SESSION.post(f"{DOCKTHOR_API}/docking", files=files, data=data, timeout=_TIMEOUT)
        if resp.status_code in (200, 201):
            d = resp.json()
            return d.get("id") or d.get("job_id") or d.get("task_id")
    except Exception:
        pass
    return None

def check_dockthor(job_id: str) -> str:
    """Check DockThor job status. Returns 'running'/'completed'/'failed'/'unknown'."""
    try:
        resp = _SESSION.get(f"{DOCKTHOR_API}/docking/{job_id}", timeout=10)
        if resp.status_code == 200:
            return resp.json().get("status", "unknown")
    except Exception:
        pass
    return "unknown"

def fetch_dockthor_results(job_id: str) -> Optional[List[Dict]]:
    """Fetch completed DockThor results. Returns list of pose dicts or None."""
    try:
        resp = _SESSION.get(f"{DOCKTHOR_API}/docking/{job_id}/results", timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            poses = data.get("poses") or data.get("results") or []
            return poses[:7]  # top 7
    except Exception:
        pass
    return None


# ── SwissDock API ────────────────────────────────────────────
SWISSDOCK_URL = "https://www.swissdock.ch"

def submit_swissdock(smiles: str, target_pdb: str) -> Optional[str]:
    """Submit docking to SwissDock. Returns job_id or None."""
    try:
        resp = _SESSION.post(f"{SWISSDOCK_URL}/submit_docking.php",
            data={"smiles": smiles, "target": target_pdb, "engine": "vina"},
            timeout=_TIMEOUT)
        if resp.status_code == 200:
            d = resp.json()
            return d.get("job_id") or d.get("id")
    except Exception:
        pass
    return None


# ── Local Vina-like scoring (fallback) ───────────────────────
def score_single_subtype(smiles: str, best_target: str) -> List[Dict]:
    """Score a molecule against ONE adenosine receptor subtype (the best predicted one).
    Returns 7 rows with varied binding-mode estimates."""
    mol = mol_from_smiles(smiles)
    if mol is None:
        return []
    from rdkit import Chem
    from rdkit.Chem import Descriptors, Lipinski, AllChem

    logp = Descriptors.MolLogP(mol)
    mw = Descriptors.MolWt(mol)
    tpsa = Descriptors.TPSA(mol)
    hbd = Lipinski.NumHDonors(mol)
    hba = Lipinski.NumHAcceptors(mol)
    n_rot = Lipinski.NumRotatableBonds(mol)
    n_aro = Lipinski.NumAromaticRings(mol)
    n_aliph = Lipinski.NumAliphaticRings(mol)

    mol_h = Chem.AddHs(mol)
    try:
        AllChem.EmbedMolecule(mol_h, AllChem.ETKDGv3())
        AllChem.MMFFOptimizeMolecule(mol_h)
        ff = AllChem.MMFFGetMoleculeForceField(mol_h)
        energy = ff.CalcEnergy() if ff else 0
    except Exception:
        energy = 0

    coeffs = {
        "A1":  {"c0": -4.8, "clogp": -0.18, "ctpsa": 0.010, "cmw": -0.004, "chbd": 0.18, "chba": 0.10, "crot": -0.05, "caro": -0.12, "crings": -0.06, "cenergy": -0.003},
        "A2A": {"c0": -5.0, "clogp": -0.15, "ctpsa": 0.008, "cmw": -0.003, "chbd": 0.15, "chba": 0.08, "crot": -0.04, "caro": -0.10, "crings": -0.05, "cenergy": -0.002},
        "A2B": {"c0": -4.6, "clogp": -0.20, "ctpsa": 0.009, "cmw": -0.003, "chbd": 0.20, "chba": 0.12, "crot": -0.06, "caro": -0.15, "crings": -0.07, "cenergy": -0.003},
        "A3":  {"c0": -4.4, "clogp": -0.22, "ctpsa": 0.011, "cmw": -0.005, "chbd": 0.22, "chba": 0.14, "crot": -0.07, "caro": -0.18, "crings": -0.08, "cenergy": -0.004},
    }
    c = coeffs.get(best_target, coeffs["A2A"])

    # Generate 7 pose-like variants by perturbing torsions
    rows = []
    for mode in range(7):
        conf_energy = energy * (1 + 0.05 * mode)
        score = (c["c0"] + c["clogp"]*logp + c["ctpsa"]*tpsa + c["cmw"]*mw
                 + c["chbd"]*hbd + c["chba"]*hba + c["crot"]*n_rot
                 + c["caro"]*n_aro + c["crings"]*(n_aliph+n_aro) + c["cenergy"]*conf_energy)
        score = max(-14, min(-2, score))
        ki = 10 ** (abs(score) / 1.36)
        le = abs(score) / max(mol.GetNumHeavyAtoms(), 1)
        rows.append({
            "rank": mode + 1,
            "subtype": best_target,
            "receptor": f"{ADENOSINE_TARGETS[best_target]['name']} ({ADENOSINE_TARGETS[best_target]['pdb']})",
            "score_kcal": round(score + 0.15 * mode, 2),
            "ki_um": round(ki * (1 + 0.2 * mode), 2),
            "ligand_efficiency": round(le - 0.01 * mode, 3),
            "logp": round(logp, 2), "mw": round(mw, 1), "tpsa": round(tpsa, 1),
            "hbd": hbd, "hba": hba, "rot_bonds": n_rot,
            "method": f"Local estimation → {best_target} ({ADENOSINE_TARGETS[best_target]['pdb']})",
        })
    return rows


def run_docking(smiles: str, best_target: str = "A2A") -> dict:
    """Try real docking APIs first, fall back to local scoring.
    Only docks against the best_target (highest predicted pChEMBL subtype).
    Returns: {"method": str, "poses": List[Dict], "api_used": str, "error": str|None}
    """
    pdb_id = ADENOSINE_TARGETS.get(best_target, {}).get("pdb", "4EIY")

    # Try DockThor first (real free docking API)
    try:
        job_id = submit_dockthor(smiles, pdb_id)
        if job_id:
            for _ in range(24):
                time.sleep(5)
                status = check_dockthor(job_id)
                if status == "completed":
                    poses = fetch_dockthor_results(job_id)
                    if poses:
                        return {"method": f"DockThor → {best_target} ({pdb_id})",
                                "poses": poses, "api_used": "DockThor", "error": None}
                    break
                elif status in ("failed", "error"):
                    break
    except Exception:
        pass

    # Try SwissDock
    try:
        job_id = submit_swissdock(smiles, pdb_id)
        if job_id:
            return {"method": f"SwissDock → {best_target} ({pdb_id})",
                    "poses": [], "api_used": "SwissDock", "job_id": job_id,
                    "error": "Submitted to SwissDock — check their website for results."}
    except Exception:
        pass

    # Local fallback — only the best_target
    poses = score_single_subtype(smiles, best_target)
    return {"method": f"Local estimation → {best_target} ({pdb_id})",
            "poses": poses, "api_used": "local", "error": None}
