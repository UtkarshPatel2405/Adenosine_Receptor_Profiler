from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd

def _get_mode_infix(base: str) -> str:
    """Extract mode infix (std, strict, root, precise) from directory path."""
    b = str(base).lower()
    if "standard" in b or b.endswith("std"):
        return "std"
    elif "strict" in b:
        return "strict"
    elif "precise" in b:
        return "precise"
    else:
        return "root"

def _find_file(base: str, pattern: str) -> Path:
    """Find file in base dir matching pattern, with fallback to 'root' or 'precise' if missing."""
    p1 = Path(base) / pattern
    if p1.exists():
        return p1
    
    infix = _get_mode_infix(base)
    if infix == "precise":
        fallback_pattern = pattern.replace("_precise_", "_root_")
        p2 = Path(base) / fallback_pattern
        if p2.exists():
            return p2
    elif infix == "root":
        fallback_pattern = pattern.replace("_root_", "_precise_")
        p2 = Path(base) / fallback_pattern
        if p2.exists():
            return p2
    return p1

def _load_json(path: str) -> dict:
    """Safely load JSON, returning empty dict if file is missing."""
    p = Path(path)
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "actual_file" in data:
        actual_path = p.parent / data["actual_file"]
        if actual_path.exists():
            with open(actual_path, "r", encoding="utf-8") as f_act:
                return json.load(f_act)
    return data

def load_evaluation_tables(base: str = "outputs/validoutput/standard") -> Tuple[pd.DataFrame, pd.DataFrame]:
    infix = _get_mode_infix(base)
    path = _find_file(base, f"evaluation_{infix}_report.json")
    report = _load_json(str(path))
    if not report:
        return pd.DataFrame(), pd.DataFrame()

    overall = report.get("overall", {})
    overall_df = pd.DataFrame([{
        "Ensemble/XGB MAE": round(overall.get("model_mae", 0), 4),
        "Ensemble/XGB RMSE": round(overall.get("model_rmse", 0), 4),
        "Ensemble/XGB R²": round(overall.get("model_r2", 0), 4),
        "Baseline R²": round(overall.get("baseline_r2", 0), 4),
        "Conformal Coverage (90%)": f"{overall.get('conformal_coverage_90', 0.0) * 100:.1f}%" if overall.get("conformal_coverage_90") is not None else "N/A",
    }])

    per = report.get("per_subtype", {})
    rows = []
    for st, m in per.items():
        if m.get("skipped"): continue
        rows.append({
            "Subtype": st,
            "XGBoost R²": round(m.get("model_r2", 0), 4) if m.get("model_r2") is not None else "N/A",
            "RandomForest R²": round(m.get("rf_r2", 0), 4) if m.get("rf_r2") is not None else "N/A",
            "LightGBM R²": round(m.get("lgb_r2", 0), 4) if m.get("lgb_r2") is not None else "N/A",
            "XGBoost MAE": round(m.get("model_mae", 0), 4) if m.get("model_mae") is not None else "N/A",
            "RandomForest MAE": round(m.get("rf_mae", 0), 4) if m.get("rf_mae") is not None else "N/A",
            "LightGBM MAE": round(m.get("lgb_mae", 0), 4) if m.get("lgb_mae") is not None else "N/A",
            "Conformal Coverage (90%)": f"{m.get('conformal_coverage_90', 0.0) * 100:.1f}%" if m.get("conformal_coverage_90") is not None else "N/A",
            "n_test": m.get("n_test"),
        })
    per_df = pd.DataFrame(rows).sort_values("Subtype") if rows else pd.DataFrame()
    return overall_df, per_df

def load_fingerprint_comparison(base: str = "outputs/validoutput/standard") -> pd.DataFrame:
    infix = _get_mode_infix(base)
    path = _find_file(base, f"fingerprint_{infix}_comparison.csv")
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

def load_scaffold_ood(base: str = "outputs/validoutput/standard") -> pd.DataFrame:
    infix = _get_mode_infix(base)
    path = _find_file(base, f"scaffold_ood_{infix}_report.json")
    data = _load_json(str(path))
    ood = data.get("ood_by_scaffold", {})
    if not ood:
        return pd.DataFrame()
    rows = [{"Scaffold": k, **v} for k, v in ood.items()]
    return pd.DataFrame(rows).sort_values("n", ascending=False)

def load_run_summary(base: str = "outputs/validoutput/standard") -> pd.DataFrame:
    infix = _get_mode_infix(base)
    path = _find_file(base, f"run_{infix}_summary.json")
    s = _load_json(str(path))
    if not s:
        return pd.DataFrame([{"Status": "Data not found"}])
    return pd.DataFrame([{
        "Mode": s.get("mode", "N/A").upper(),
        "Total Rows": s.get("n_rows_clean"),
        "DB Size": s.get("n_lookup_smiles"),
        "Train": s.get("split", {}).get("n_train"),
        "Test": s.get("split", {}).get("n_test"),
        "X_train_shape": str(s.get("features", {}).get("X_train_shape")),
    }])

def _examples_to_df(path: str) -> pd.DataFrame:
    """Formats prediction examples with Reliability labels for the UI."""
    from src.chem_utils import nearest_tanimoto
    data = _load_json(path)
    if not data: return pd.DataFrame()
    
    rows = []
    for item in data:
        smi = item.get("smiles")
        r = item.get("result", {})
        preds = r.get("predictions", {})
        preds_str = ", ".join([f"{k}: {v:.2f}" for k, v in preds.items()]) if preds else "N/A"
        
        try:
            sim = nearest_tanimoto(smi)
            if sim is not None:
                if sim >= 0.6: label = "High"
                elif sim >= 0.4: label = "Med"
                else: label = "Low"
                sim_str = f"{sim:.3f} ({label})"
            else:
                sim_str = "0"
        except Exception:
            sim_str = "0"
 
        rows.append({
            "SMILES": smi,
            "Source": r.get("source"),
            "Best": r.get("best_target"),
            "Predictions": preds_str,
            "Similarity (AD)": sim_str,
            "Hits": ", ".join(r.get("target_hits", [])) if r.get("target_hits") else "None",
        })
    return pd.DataFrame(rows)

def load_mode_examples(mode: str, base: str = "outputs/validoutput"):
    base_dir = f"{base}/{mode}"
    infix = "std" if mode == "standard" else "strict" if mode == "strict" else "root"
    db_path = _find_file(base_dir, f"predictor_db_{infix}_examples.json")
    novel_path = _find_file(base_dir, f"predictor_novel_{infix}_examples.json")
    db_df = _examples_to_df(str(db_path))
    novel_df = _examples_to_df(str(novel_path))
    summary_df = load_run_summary(base=base_dir)
    return summary_df, db_df, novel_df

def load_examples(base: str = "outputs/validoutput/standard") -> Tuple[pd.DataFrame, pd.DataFrame]:
    infix = _get_mode_infix(base)
    db_path = _find_file(base, f"predictor_db_{infix}_examples.json")
    novel_path = _find_file(base, f"predictor_novel_{infix}_examples.json")
    db_df = _examples_to_df(str(db_path))
    novel_df = _examples_to_df(str(novel_path))
    return db_df, novel_df

def outputs_exist(base: str = "outputs/validoutput/standard") -> Dict[str, bool]:
    infix = _get_mode_infix(base)
    files = [
        f"run_{infix}_summary.json",
        f"predictor_db_{infix}_examples.json",
        f"predictor_novel_{infix}_examples.json",
        f"evaluation_{infix}_report.json",
    ]
    return {f: _find_file(base, f).exists() for f in files}