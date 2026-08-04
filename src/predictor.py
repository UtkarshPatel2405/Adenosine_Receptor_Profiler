import json
import logging
import pickle
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski

try:
    import lightgbm as lgb
    import lightgbm.sklearn
except ImportError:
    lgb = None

try:
    import xgboost as xgb
except ImportError:
    xgb = None

try:
    import mapie
except ImportError:
    mapie = None

from src.features import build_features
from src.config import SUBTYPES, MODELS_DIR, PROCESSED_DATA_DIR

logger = logging.getLogger(__name__)


class AverageEnsemble:
    """Equal-weight average ensemble model wrapper for stacked prediction."""
    def predict(self, X):
        return np.mean(X, axis=1)

setattr(sys.modules['__main__'], 'AverageEnsemble', AverageEnsemble)


def _try_gnn_predict(smiles, subtype):
    try:
        from src.gnn_model import predict_gnn
        return predict_gnn(smiles, subtype)
    except ImportError:
        return None
    except Exception as e:
        logger.warning("GNN prediction failed for %s/%s: %s", subtype, smiles[:30], e)
        return None


@lru_cache(maxsize=4)
def _load_scaler(mode: str = "precise"):
    candidate_paths = [
        MODELS_DIR / mode / f"scaler_{mode}.pkl",
        MODELS_DIR / mode / "scaler.pkl",
        MODELS_DIR / "scaler.pkl",
    ]
    last_err = None
    for path in candidate_paths:
        if path.exists():
            try:
                with open(path, "rb") as f:
                    return pickle.load(f)
            except Exception as e:
                logger.error("Failed to load scaler from %s: %s", path, e)
                last_err = e
    raise FileNotFoundError(f"No scaler found for mode={mode} in any path. Last error: {last_err}")


@lru_cache(maxsize=1)
def _load_db_lookup():
    p = PROCESSED_DATA_DIR / "db_lookup_train.json"
    if p.exists():
        with open(p) as f:
            return json.load(f)
    return {}


# ponytail: single parameterized loader replaces 4 identical copy-paste functions
_MODEL_PREFIXES = {
    "xgboost": "xgboost",
    "rf": "rf",
    "lgb": "lgb",
    "stack_ridge": "stack_ridge",
}


@lru_cache(maxsize=8)
def _load_models(prefix: str):
    """Load models for all subtypes, trying multiple legacy path patterns."""
    models = {}
    for st in SUBTYPES:
        candidates = [
            MODELS_DIR / "precise" / f"{prefix}_{st}_production.pkl",
            MODELS_DIR / f"{prefix}_{st}_production.pkl",
            MODELS_DIR / f"{prefix}_precise_{st.lower()}_model.pkl",
            MODELS_DIR / f"{prefix}_{st.lower()}_model.pkl",
        ]
        for path in candidates:
            if path.exists():
                try:
                    if prefix == "lgb":
                        try:
                            import lightgbm
                            import lightgbm.sklearn
                        except ModuleNotFoundError:
                            logger.warning("LightGBM module not installed in Python environment. Skipping LGB models.")
                            return {}
                    elif prefix == "xgboost":
                        try:
                            import xgboost
                            import xgboost.sklearn
                        except ModuleNotFoundError:
                            logger.warning("XGBoost module not installed in Python environment. Skipping XGB models.")
                            return {}
                    with open(path, "rb") as f:
                        header = f.read(10)
                        if header.startswith(b"version https") or header.startswith(b"oid sha256"):
                            logger.info("Model file %s is a Git LFS pointer. Skipping binary load.", path)
                            continue
                        f.seek(0)
                        models[st] = pickle.load(f)
                    break
                except Exception as e:
                    logger.error("Failed to load %s model for %s from %s: %s", prefix, st, path, e)
        else:
            logger.warning("%s model for %s not found at any path", prefix, st)
    return models



# Backward-compatible aliases — callers import these names
def _load_xgb_models():
    return _load_models("xgboost")

def _load_rf_models():
    return _load_models("rf")

def _load_lgb_models():
    return _load_models("lgb")

def _load_stack_models():
    return _load_models("stack_ridge")


def _ensemble_predict(model_ens, x: np.ndarray) -> Tuple[Any, Any, Any, Any]:
    """
    Returns (pred_mean, uncertainty_std_equiv, lower_bound, upper_bound).

    Supports both single sample and batch inputs.
    """
    if x.ndim == 1:
        x = x.reshape(1, -1)

    is_batch = x.shape[0] > 1
    model_type_name = type(model_ens).__name__

    if model_type_name == "CrossConformalRegressor":
        try:
            y_pred, y_pis = model_ens.predict_interval(x)
            if y_pis.ndim == 3:
                lower = y_pis[:, 0, 0]
                upper = y_pis[:, 1, 0]
            else:
                lower = y_pis[:, 0]
                upper = y_pis[:, 1]
            std_equiv = (upper - lower) / 3.29
            if not is_batch:
                return float(y_pred[0]), float(std_equiv[0]), float(lower[0]), float(upper[0])
            return y_pred, std_equiv, lower, upper
        except Exception as e:
            logger.warning("CrossConformalRegressor predict_interval failed: %s. Falling back.", e)
            y_pred = model_ens.predict(x)
            if not is_batch:
                return float(y_pred[0]), 0.0, float(y_pred[0]), float(y_pred[0])
            zeros = np.zeros_like(y_pred)
            return y_pred, zeros, y_pred, y_pred

    elif model_type_name == "MapieRegressor":
        try:
            y_pred, y_pis = model_ens.predict(x)
            if y_pis.ndim == 3:
                lower = y_pis[:, 0, 0]
                upper = y_pis[:, 1, 0]
            else:
                lower = y_pis[:, 0]
                upper = y_pis[:, 1]
            std_equiv = (upper - lower) / 3.29
            if not is_batch:
                return float(y_pred[0]), float(std_equiv[0]), float(lower[0]), float(upper[0])
            return y_pred, std_equiv, lower, upper
        except Exception as e:
            logger.warning("MapieRegressor predict failed: %s. Falling back.", e)
            y_pred = model_ens.predict(x)
            if not is_batch:
                return float(y_pred[0]), 0.0, float(y_pred[0]), float(y_pred[0])
            zeros = np.zeros_like(y_pred)
            return y_pred, zeros, y_pred, y_pred

    elif isinstance(model_ens, (list, tuple)):
        member_preds = np.array([m.predict(x) for m in model_ens])
        mean = member_preds.mean(axis=0)
        std = member_preds.std(axis=0, ddof=0)
        if not is_batch:
            return float(mean[0]), float(std[0]), float(mean[0] - 1.96 * std[0]), float(mean[0] + 1.96 * std[0])
        return mean, std, mean - 1.96 * std, mean + 1.96 * std

    else:
        pred = model_ens.predict(x)
        if not is_batch:
            return float(pred[0]), 0.0, float(pred[0]), float(pred[0])
        zeros = np.zeros_like(pred)
        return pred, zeros, pred, pred


_ZERO_RESULT = (0.0, 0.0, {"lower": 0.0, "upper": 0.0, "width": 0.0})


def _predict_one_model(model_dict, x, in_db, lookup, canon, st):
    """Predict with one model type for one subtype. Returns (pred, unc, interval).

    For database hits: return experimental value with σ=0 (no prediction uncertainty).
    For novel compounds: return model prediction with conformal interval.
    """
    # DB hits take priority — experimental value, zero uncertainty
    if in_db and isinstance(lookup.get(canon), dict):
        val = lookup[canon].get(st)
        if pd.notna(val) and str(val).lower() != 'nan':
            p_val = float(val)
            return p_val, 0.0, {"lower": p_val, "upper": p_val, "width": 0.0}
    # Model prediction with conformal intervals
    if st in model_dict and x is not None:
        m, s, low, high = _ensemble_predict(model_dict[st], x)
        return m, s, {"lower": round(low, 3), "upper": round(high, 3), "width": round(high - low, 3)}
    return _ZERO_RESULT


def predict(smiles: str, threshold: float = 6.0, run_rf: bool = True) -> Dict[str, Any]:
    lookup = _load_db_lookup()

    try:
        scaler = _load_scaler("precise")
    except Exception:
        scaler = None

    xgb_models = _load_xgb_models()
    lgb_models = _load_lgb_models()
    stack_models = _load_stack_models()
    rf_models = _load_rf_models()

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("Invalid SMILES")
    canon = Chem.MolToSmiles(mol, canonical=True)

    # Compute display descriptors inline (no separate _descriptors function needed)
    desc_results = {
        "MW": round(float(Descriptors.MolWt(mol)), 2),
        "LogP": round(float(Descriptors.MolLogP(mol)), 2),
        "HBD": int(Lipinski.NumHDonors(mol)),
        "HBA": int(Lipinski.NumHAcceptors(mol)),
        "RotBonds": int(Lipinski.NumRotatableBonds(mol)),
        "AromRings": int(Lipinski.NumAromaticRings(mol)),
        "TPSA": round(float(Descriptors.TPSA(mol)), 2),
    }

    in_db = canon in lookup

    model_names = ["XGBoost", "RandomForest", "LightGBM", "Stacked", "PyTorch"]
    preds = {n: {} for n in model_names}
    unc = {n: {} for n in model_names}
    intervals = {n: {} for n in model_names}

    x = build_features(canon, scaler) if scaler is not None else None

    source = "database" if in_db else "model"

    base_model_map = {
        "XGBoost": xgb_models,
        "RandomForest": rf_models,
        "LightGBM": lgb_models,
    }

    for st in SUBTYPES:
        for mod_name, mod_dict in base_model_map.items():
            p, u, iv = _predict_one_model(mod_dict, x, in_db, lookup, canon, st)
            preds[mod_name][st] = p
            unc[mod_name][st] = u
            intervals[mod_name][st] = iv

        # --- Stacked ensemble ---
        if in_db and isinstance(lookup.get(canon), dict):
            val = lookup[canon].get(st)
            p_val = float(val) if (pd.notna(val) and str(val).lower() != 'nan') else 0.0
            preds["Stacked"][st] = p_val
            unc["Stacked"][st] = 0.0

            intervals["Stacked"][st] = {"lower": p_val, "upper": p_val, "width": 0.0}
        else:
            # Exclude zero or missing base model predictions from Stacked ensemble mean
            valid_base_vals = [
                preds[mod_name].get(st, 0.0) 
                for mod_name in ("XGBoost", "RandomForest", "LightGBM") 
                if isinstance(preds[mod_name].get(st, 0.0), (int, float)) and preds[mod_name].get(st, 0.0) > 0
            ]
            if st in stack_models and x is not None and len(valid_base_vals) == 3:
                try:
                    meta_x = np.array([valid_base_vals])
                    m = float(stack_models[st].predict(meta_x)[0])
                except Exception:
                    m = float(np.mean(valid_base_vals)) if valid_base_vals else 0.0
            else:
                m = float(np.mean(valid_base_vals)) if valid_base_vals else 0.0

            preds["Stacked"][st] = round(m, 3)
            unc["Stacked"][st] = 0.0
            intervals["Stacked"][st] = {"lower": round(m, 3), "upper": round(m, 3), "width": 0.0}

        # --- PyTorch / GNN ---
        pred_val = _try_gnn_predict(canon, st)
        if pred_val is not None:
            m = float(pred_val)
            preds["PyTorch"][st] = m
            unc["PyTorch"][st] = 0.0
            intervals["PyTorch"][st] = {"lower": m, "upper": m, "width": 0.0}
        else:
            preds["PyTorch"][st], unc["PyTorch"][st], intervals["PyTorch"][st] = _ZERO_RESULT

    selectivity = {}
    pairs = [("A2A", "A1"), ("A2A", "A3")]
    try:
        from src.selectivity_models import predict_direct_selectivity
        for subA, subB in pairs:
            pred_sel = predict_direct_selectivity(canon, subA, subB)
            if pred_sel is not None:
                selectivity[f"{subA}_vs_{subB}"] = round(pred_sel, 3)
    except Exception:
        pass

    ref_preds = preds["XGBoost"]

    return {
        "smiles": canon,
        "in_database": in_db,
        "predictions": preds,
        "descriptors": desc_results,
        "uncertainty": unc,
        "intervals": intervals,
        "selectivity_profile": selectivity,
        "best_target": max(ref_preds, key=ref_preds.get) if ref_preds else None,
        "target_hits": [st for st, v in ref_preds.items() if v >= threshold] if ref_preds else [],
        "source": source,
    }
