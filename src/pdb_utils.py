from __future__ import annotations
import re
import time
from typing import Optional
import requests

RCSB_CORE = "https://data.rcsb.org/rest/v1/core"
RCSB_SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"
_TIMEOUT = 15


def _get(url: str, params: dict = None) -> dict | None:
    try:
        r = requests.get(url, params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _post(url: str, payload: dict) -> dict | None:
    try:
        r = requests.post(url, json=payload, timeout=_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def fetch_pdb_entry(pdb_id: str) -> dict | None:
    pdb_id = pdb_id.strip().upper()
    if not re.match(r"^[A-Za-z0-9]{4}$", pdb_id):
        return None
    return _get(f"{RCSB_CORE}/entry/{pdb_id}")


def get_chemical_component(ccd_code: str) -> dict | None:
    ccd_code = ccd_code.strip().upper()
    return _get(f"{RCSB_CORE}/chemcomp/{ccd_code}")


def pdb_to_smiles(pdb_id: str) -> list[dict]:
    pdb_id = pdb_id.strip().upper()
    if not re.match(r"^[A-Za-z0-9]{4}$", pdb_id):
        return []

    entry = fetch_pdb_entry(pdb_id)
    if not entry:
        return []

    entities = entry.get("rcsb_entry_container_identifiers", {}).get(
        "non_polymer_entity_ids", []
    )
    if not entities:
        return []

    ligands = []
    for ent_id in entities:
        np_url = f"{RCSB_CORE}/nonpolymer_entity/{pdb_id}/{ent_id}"
        np_data = _get(np_url)
        if not np_data:
            continue
        ccd_code = np_data.get("rcsb_nonpolymer_entity_container_identifiers", {}).get("nonpolymer_comp_id")
        if not ccd_code:
            continue
        
        # Exclude common crystallization/buffer/solvent agents
        if ccd_code in ("HOH", "DOD", "GOL", "SO4", "PO4", "NA", "CL", "EDT", "ACT", "DMS", "PEG", "EDO", "FMT", "BU1"):
            continue

        chem = get_chemical_component(ccd_code)
        if chem:
            smiles = chem.get("rcsb_chem_comp_descriptor", {}).get("SMILES")
            chem_comp = chem.get("chem_comp", {})
            ligands.append(
                {
                    "ccd": ccd_code,
                    "name": chem_comp.get("name", ccd_code),
                    "smiles": smiles,
                    "formula": chem_comp.get("formula", ""),
                    "mw": chem_comp.get("formula_weight", ""),
                }
            )
    return ligands


def _try_ligand_search(pdb_id: str) -> list[dict]:
    query = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "value": pdb_id.strip().upper(),
                "attribute": "rcsb_entry_id",
                "operator": "exact_match"
            },
        },
        "return_type": "entry",
        "request_options": {"paginate": {"start": 0, "rows": 10}},
    }
    result = _post(RCSB_SEARCH, query)
    if not result:
        return []
    entries = []
    for item in result.get("result_set") or []:
        eid = item.get("identifier", "")
        if eid:
            entries.append({"pdb_id": eid, "url": f"https://www.rcsb.org/structure/{eid}"})
    return entries


def molecules_from_smiles(smiles: str) -> list[dict]:
    if not smiles or len(smiles) < 3:
        return []
    query = {
        "query": {
            "type": "terminal",
            "service": "chemical",
            "parameters": {
                "value": smiles,
                "type": "descriptor",
                "descriptor_type": "SMILES",
                "match_type": "graph-strict"
            },
        },
        "return_type": "mol_definition",
        "request_options": {"paginate": {"start": 0, "rows": 20}},
    }
    result = _post(RCSB_SEARCH, query)
    if not result:
        return []

    matches = []
    for chem_id in (result.get("result_set") or []):
        ccd = chem_id.get("identifier", "")
        if ccd:
            chem = get_chemical_component(ccd)
            if chem:
                chem_comp = chem.get("chem_comp", {})
                sm = chem.get("rcsb_chem_comp_descriptor", {}).get("SMILES")
                matches.append(
                    {
                        "ccd": ccd,
                        "name": chem_comp.get("name", ccd),
                        "smiles": sm,
                        "formula": chem_comp.get("formula", ""),
                    }
                )
    return matches


def resolve_input(user_input: str) -> dict:
    stripped = user_input.strip()
    is_pdb_id = bool(re.match(r"^[A-Za-z0-9]{4}$", stripped))
    if is_pdb_id:
        ligands = pdb_to_smiles(stripped)
        if ligands:
            return {"type": "pdb", "value": stripped.upper(), "ligands": ligands}
    return {"type": "smiles", "value": stripped, "ligands": []}


def search_pdb_by_smiles(smiles: str, max_results: int = 3) -> list[dict]:
    if not smiles or len(smiles) < 3:
        return []
    query = {
        "query": {
            "type": "terminal",
            "service": "chemical",
            "parameters": {
                "value": smiles,
                "type": "descriptor",
                "descriptor_type": "SMILES",
                "match_type": "graph-strict"
            },
        },
        "return_type": "entry",
        "request_options": {"paginate": {"start": 0, "rows": max_results}},
    }
    result = _post(RCSB_SEARCH, query)
    if not result:
        return []
    entries = []
    for item in result.get("result_set") or []:
        eid = item.get("identifier", "")
        if eid:
            entries.append({"pdb_id": eid, "url": f"https://www.rcsb.org/structure/{eid}"})
    return entries


from functools import lru_cache

@lru_cache(maxsize=512)
def get_pdb_ids_for_smiles(smiles: str) -> list[dict]:
    """Get real PDB IDs for a SMILES string.
    First checks local lookup index (lookup_pdb_ids), then queries RCSB PDB Search API.
    Returns list of dicts with 'pdb_id', 'name', and 'url'.
    """
    try:
        from src.chem_utils import lookup_pdb_ids
        local_matches = lookup_pdb_ids(smiles)
        if local_matches:
            return [{"pdb_id": m["pdb_id"], "name": m.get("name", m.get("ccd", "")), "url": f"https://www.rcsb.org/structure/{m['pdb_id']}"} for m in local_matches]
    except Exception:
        pass

    try:
        api_matches = search_pdb_by_smiles(smiles, max_results=3)
        if api_matches:
            return [{"pdb_id": m["pdb_id"], "name": m["pdb_id"], "url": m["url"]} for m in api_matches]
    except Exception:
        pass

    return []


def search_pdb_by_ccd(ccd_code: str) -> list[dict]:
    ccd_code = ccd_code.strip().upper()
    query = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "value": ccd_code,
                "attribute": "rcsb_nonpolymer_entity_container_identifiers.nonpolymer_comp_id",
                "operator": "exact_match"
            },
        },
        "return_type": "entry",
        "request_options": {"paginate": {"start": 0, "rows": 10}},
    }
    result = _post(RCSB_SEARCH, query)
    if not result:
        return []
    entries = []
    for item in result.get("result_set") or []:
        eid = item.get("identifier", "")
        if eid:
            entries.append({"pdb_id": eid, "url": f"https://www.rcsb.org/structure/{eid}"})
    return entries


def search_pdb_similar(smiles: str, max_results: int = 3) -> list[dict]:
    """Search PDB for entries containing molecules similar to the given SMILES.
    Uses RCSB chemical similarity search."""
    if not smiles or len(smiles) < 3:
        return []
    query = {
        "query": {
            "type": "terminal",
            "service": "chemical",
            "parameters": {
                "value": smiles,
                "type": "descriptor",
                "descriptor_type": "SMILES",
                "match_type": "fingerprint-similarity"
            },
        },
        "return_type": "entry",
        "request_options": {"paginate": {"start": 0, "rows": max_results}},
    }
    result = _post(RCSB_SEARCH, query)
    if not result:
        return []
    entries = []
    for item in result.get("result_set") or []:
        eid = item.get("identifier", "")
        score = item.get("score", 0)
        if eid:
            entries.append({"pdb_id": eid, "score": round(score, 2),
                "url": f"https://www.rcsb.org/structure/{eid}"})
    return entries


def search_pdb_for_smiles_batch(smiles_list: list[str]) -> dict[str, list[dict]]:
    results = {}
    for sm in smiles_list:
        try:
            # First try exact chemical component match
            chem_components = molecules_from_smiles(sm)
            pdb_entries = []
            for comp in chem_components[:2]:
                ccd = comp.get("ccd", "")
                if ccd:
                    entries = search_pdb_by_ccd(ccd)
                    for e in entries:
                        e["ccd"] = ccd
                        e["name"] = comp.get("name", "")
                    pdb_entries.extend(entries[:3])

            # If nothing found, try broader similarity search
            if not pdb_entries:
                sim_entries = search_pdb_similar(sm, max_results=3)
                pdb_entries = [{"pdb_id": e["pdb_id"], "url": e["url"],
                    "ccd": "similar", "name": f"Similar structure (score: {e.get('score','?')})"}
                    for e in sim_entries]

            results[sm] = pdb_entries[:4]
        except Exception:
            results[sm] = []
    return results
