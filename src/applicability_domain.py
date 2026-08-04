import numpy as np
import pandas as pd
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem

# ponytail: this module has 0 callers in the codebase — candidate for deletion.
# Keeping it minimal for now.


def build_fps(smiles_list, n_bits=2048, radius=2):
    fps = []
    valid_mask = []
    for s in smiles_list:
        mol = Chem.MolFromSmiles(s)
        if mol is not None:
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
            fps.append(fp)
            valid_mask.append(True)
        else:
            fps.append(None)
            valid_mask.append(False)
    return fps, np.array(valid_mask, dtype=bool)

def nearest_tanimoto_similarity(test_fps, train_fps):
    sims = np.zeros(len(test_fps), dtype=float)
    for i, fp in enumerate(test_fps):
        if fp is None:
            sims[i] = np.nan
            continue
        s = DataStructs.BulkTanimotoSimilarity(fp, [t for t in train_fps if t is not None])
        sims[i] = float(np.max(s)) if len(s) else np.nan
    return sims

def ad_summary(similarities: np.ndarray):
    sims = pd.Series(similarities).dropna()
    return {
        "n": int(sims.shape[0]),
        "mean": float(sims.mean()),
        "median": float(sims.median()),
        "pct_ge_0_4": float((sims >= 0.4).mean()),
        "pct_ge_0_5": float((sims >= 0.5).mean()),
        "pct_ge_0_6": float((sims >= 0.6).mean()),
    }
