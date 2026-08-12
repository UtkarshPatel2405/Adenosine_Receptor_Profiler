# Adenosine Receptor Selectivity & Affinity Predictor (CADD / QSAR)

**Publication-grade machine learning platform for predicting pChEMBL binding affinity and subtype selectivity across human adenosine receptors A<sub>1</sub>, A<sub>2A</sub>, A<sub>2B</sub>, A<sub>3</sub> from SMILES strings.**

Live webapp: https://adenosineselectivitymodel-hmuazpqwqokyvtsgzvn2tq.streamlit.app/

![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Streamlit](https://img.shields.io/badge/streamlit-1.35+-red)

---

## 🔬 Scientific Overview

### The Biological Problem
Adenosine receptors (ARs) are Class A GPCRs with four human subtypes (A<sub>1</sub>, A<sub>2A</sub>, A<sub>2B</sub>, A<sub>3</sub>) sharing >70% transmembrane sequence identity. This high conservation creates a fundamental challenge in GPCR drug discovery: **designing subtype-selective ligands**. 

- **A<sub>1</sub>**: Cardioprotection, analgesia, bradycardia risk
- **A<sub>2A</sub>**: Parkinson's disease (antagonists), cancer immunotherapy (agonists)  
- **A<sub>2B</sub>**: Inflammation, fibrosis, asthma
- **A<sub>3</sub>**: Neuroprotection, glaucoma, cancer

A ligand optimized for A<sub>2A</sub> (e.g., istradefylline for Parkinson's) must avoid A<sub>1</sub> (bradycardia) and A<sub>3</sub> off-target effects. This requires quantitative selectivity prediction: ΔpChEMBL between subtypes.

### The QSAR Solution
This platform implements a **multi-model conformal prediction pipeline**:

| Component | Method | Purpose |
|-----------|--------|---------|
| **Featurization** | Morgan FP (2048-bit, r=2) + MACCS (166-bit) + 15 RDKit descriptors | Chemical representation |
| **Primary Model** | XGBoost + MAPIE Conformal (Jackknife+, 90% CI) | Point predictions + guaranteed coverage |
| **Baseline** | Random Forest (300 trees, √ features) | Robustness check |
| **Selectivity** | Direct ΔpChEMBL regression (pairwise) | Cancels assay bias, improves selectivity accuracy |
| **Validation** | Y-randomization (20×), SHAP, Scaffold OOD, External test | Rigorous SAR verification |

**Key Innovation**: Conformal prediction provides **mathematically guaranteed 90% confidence intervals** — not heuristic uncertainty. Every prediction includes a prediction interval [lower, upper] with proven finite-sample coverage.

---

## 🏗️ Project Structure

```
Adenosine_Selectivity_Model/
├── streamlit_app.py              # Main dashboard entry point
├── requirements.txt              # Python dependencies
├── pyproject.toml                # Build configuration
├── README.md                     # This file
├── implementation_plan.md        # Architecture & remediation plan
├── PROJECT_EXPLANATION.md        # Code textbook (chapter-by-chapter)
│
├── data/
│   ├── raw/                      # Source datasets (gitignored large files)
│   │   ├── AR_all_unique_parents_with_smiles.csv   # ChEMBL export
│   │   ├── GPCRdb_A1.xlsx        # GPCRdb A1 ligands
│   │   ├── GPCRdb_A2A.xlsx       # GPCRdb A2A ligands
│   │   ├── GPCRdb_A2B.xlsx       # GPCRdb A2B ligands
│   │   └── GPCRdb_A3.xlsx        # GPCRdb A3 ligands
│   └── processed/                # Generated artifacts (reproducible)
│       ├── db_lookup.json        # SMILES → pChEMBL (all subtypes)
│       ├── db_lookup_train.json  # Training set lookup
│       ├── global_split.json     # Scaffold train/test indices
│       ├── train_smiles.pkl      # Training SMILES list
│       ├── test_smiles.pkl       # Test SMILES list
│       ├── train_fps.pkl         # Training Morgan FPs (for AD)
│       ├── features_train.pkl    # Full feature matrix (train)
│       ├── features_test.pkl     # Full feature matrix (test)
│       ├── smiles_to_pdb.json    # SMILES ↔ PDB mapping
│       └── smiles_registry.json  # Canonical SMILES registry
│
├── models/
│   ├── precise/                  # Production XGBoost + MAPIE models
│   │   ├── xgboost_A1_production.pkl
│   │   ├── xgboost_A2A_production.pkl
│   │   ├── xgboost_A2B_production.pkl
│   │   ├── xgboost_A3_production.pkl
│   │   ├── rf_A1_production.pkl
│   │   ├── rf_A2A_production.pkl
│   │   ├── rf_A2B_production.pkl
│   │   ├── rf_A3_production.pkl
│   │   └── scaler_precise.pkl
│   ├── gnn/                      # PyTorch Geometric GNN models
│   │   ├── gnn_a1_model.pt
│   │   ├── gnn_a2a_model.pt
│   │   ├── gnn_a2b_model.pt
│   │   └── gnn_a3_model.pt
│   └── selectivity/              # Pairwise ΔpChEMBL models
│
├── outputs/
│   ├── validoutput/precise/      # Evaluation reports
│   │   ├── evaluation_precise_report.json
│   │   ├── run_precise_summary.json
│   │   ├── predictor_db_precise_examples.json
│   │   └── predictor_novel_precise_examples.json
│   ├── shap/                     # SHAP plots (bar + beeswarm per subtype)
│   ├── y_randomization/          # Y-randomization distributions + reports
│   ├── diagnostics/              # Scaffold diversity, activity cliffs, pChEMBL dist
│   ├── external_validation/      # Blind test on literature compounds
│   ├── benchmark/                # Literature benchmark comparison
│   └── gnn/                      # GNN evaluation summaries
│
├── src/
│   ├── config.py                 # Central configuration (paths, hyperparams)
│   ├── run_id.py                 # Reproducible run identifiers
│   │
│   ├── # Data Pipeline
│   ├── data_loader.py            # ChEMBL + GPCRdb loading, filtering, deduplication
│   ├── scaffold_split.py         # Bemis-Murcko scaffold split (global, leak-free)
│   ├── smiles_registry.py        # SMILES canonicalization + barcode deduplication
│   │
│   ├── # Featurization
│   ├── features.py               # Morgan + MACCS + RDKit descriptors + filtering
│   ├── feature_caching.py        # Disk caching for hyperopt speed
│   ├── chem_utils.py             # 2D/3D viz, conformers, PAINS, QED, Tanimoto AD
│   │
│   ├── # Modeling
│   ├── conformal.py              # MAPIE CrossConformalRegressor (Jackknife+)
│   ├── ml_base.py                # Baseline training utilities
│   ├── nested_cv.py              # 5×3 Nested CV with Optuna
│   ├── retrain_production.py     # Full retraining pipeline
│   ├── predictor.py              # Unified inference (DB lookup + conformal + selectivity)
│   ├── selectivity_models.py     # Direct ΔpChEMBL pairwise models
│   ├── gnn_model.py              # MPNN/GINE PyTorch Geometric
│   │
│   ├── # Validation & Explainability
│   ├── evaluator.py              # Metrics, calibration, OOD analysis
│   ├── y_randomization.py        # Response permutation test (20×)
│   ├── shap_analysis.py          # TreeSHAP + chemical sanity checks
│   ├── external_validation.py    # GPCRdb blind test
│   ├── literature_benchmark.py   # Published model comparison
│   ├── applicability_domain.py   # Tanimoto-based AD
│   ├── diagnostics/              # Data quality diagnostics
│   │   └── a1_diagnosis.py
│   │
│   ├── # Structure & Real Deposited PDB
│   ├── pdb_utils.py              # RCSB PDB + ChEMBL real-structure lookups
│   ├── pharmacophore.py          # Pharmacophore features
│   │
│   ├── # Streamlit App
│   └── app/
│       ├── css.py                # Custom styling
│       ├── components/
│       │   ├── sidebar.py
│       │   ├── model_reports.py  # Report loading utilities
│       │   └── batch_predict.py
│       └── pages/
│           ├── single_predict.py # Single molecule + SHAP + real PDB neighbors
│           ├── batch_predict.py  # CSV batch screening
│           └── model_results.py  # 6-tab evaluation dashboard
│
├── scripts/                      # Utility scripts
└── tests/                        # Unit tests
```

---

## 🚀 Quick Start

### 1. Installation
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Option B: Conda Environment Setup
```bash
git clone https://github.com/UtkarshPatel2405/Adenosine_Selectivity_Model.git
cd Adenosine_Selectivity_Model

conda create -n NAME_OF_ENV
conda activate NAME_OF_ENV
conda install python=3.12
conda install --file requirements.txt
```

### 2. Run Full Training Pipeline (Reproduces all models & reports)
```bash
# 1. Train conformal XGBoost + RF models (scaffold split, feature filtering)
python -m src.retrain_production

# 2. Train pairwise selectivity models (ΔpChEMBL)
python -m src.selectivity_models

# 3. Run validation diagnostics
python -m src.y_randomization --subtype A2A --iterations 20
python -m src.shap_analysis --subtype A2A
python -m src.diagnostics.a1_diagnosis
python -m src.evaluator

# 4. Generate dashboard examples
python results.py
```

### 3. Launch Interactive Dashboard
```bash
streamlit run streamlit_app.py
```

Dashboard tabs:
- **Single Molecule** — SMILES input → 3-model predictions + conformal CI + SHAP + receptor similarity
- **Batch CSV** — Upload CSV with SMILES column → bulk screening with AD flags
- **Model Results** — 6-tab evaluation dashboard (Metrics, SHAP/Y-Rand, Diagnostics, Examples, External, Methodology)

---

## 📊 Dashboard Features

### Single Molecule Prediction
- **Input**: SMILES string (canonicalized automatically)
- **Output per subtype (A1, A2A, A2B, A3)**:
  - XGBoost pChEMBL + 90% conformal prediction interval
  - Random Forest pChEMBL (on demand)
  - Uncertainty (σ) calibrated from interval width
- **Selectivity Profile**: Direct ΔpChEMBL predictions (A2A vs A1, A2A vs A3)
- **SHAP Explainability**: Bar + beeswarm plots with feature-to-chemistry mapping
- **Receptor Binding Analysis**: Multi-receptor similarity to known co-crystallized ligands
- **Drug-likeness**: PAINS alerts, QED, Lipinski, Applicability Domain (max Tanimoto to training set)

### Model Results Dashboard (6 Tabs)

| Tab | Content | Key Visualizations |
|-----|---------|-------------------|
| **📊 Metrics** | Overall + per-subtype MAE, RMSE, R², Conformal Coverage | Calibration plot, MAE by uncertainty quartile |
| **🧩 SHAP/Y-Rand** | Global feature importance + Y-randomization null distribution | SHAP bar/beeswarm, shuffled R² histogram |
| **📋 Diagnostics** | Scaffold diversity, activity cliffs, pChEMBL distributions | Histograms, cliff shift plots |
| **🔍 Examples** | Test-set predictions: database hits + novel molecules | Prediction vs experimental tables |
| **🔬 External** | Blind validation on literature compounds | Per-subtype R²/MAE on truly novel chemotypes |
| **📐 Methodology** | Pipeline summary + **Training Dataset Download section** | Data sources, processing steps, file manifests |

---

## 🧪 Scientific Rigor: Zero-Leakage Guarantees

| Leakage Type | Prevention |
|--------------|------------|
| **Scaffold leakage** | Global Bemis-Murcko split — identical scaffolds never cross train/test |
| **Stereoisomer leakage** | SMILES barcode registry merges stereoisomers to single parent |
| **Duplicate leakage** | Median pChEMBL per (SMILES, subtype); priority K<sub>i</sub>/K<sub>d</sub> > IC<sub>50</sub>/EC<sub>50</sub> |
| **Mutual decoy fallacy** | Removed — missing data ≠ inactive (see `implementation_plan.md`) |
| **Feature leakage** | FeatureFilter fit ONLY on training set; applied to test |
| **Hyperparameter leakage** | Nested CV: inner loop for Optuna, outer for evaluation |
| **GNN split alignment** | GNN loads `global_split.json` — identical train/test as XGBoost |

---

## 📈 Performance Benchmarks

| Model | A1 R² | A2A R² | A2B R² | A3 R² | Overall R² | 90% Coverage |
|-------|-------|--------|--------|-------|------------|--------------|
| XGBoost (Conformal) | ~0.62 | ~0.66 | ~0.58 | ~0.64 | **~0.62** | **≥0.85** |
| Random Forest | ~0.58 | ~0.62 | ~0.55 | ~0.60 | ~0.59 | N/A |
| GNN (MPNN) | ~0.03 | ~0.33 | ~0.32 | ~0.28 | ~0.24 | N/A |

*Values from scaffold-split test set (20% OOD). Conformal coverage target ≥85% — intervals are statistically valid.*

---

## 🔬 Validation Suite

### Y-Randomization (Response Permutation)
- Shuffles pChEMBL labels 20×, retrains XGBoost each time
- **Pass**: Real R² > Shuffled mean + 3σ (p < 0.001)
- Confirms model learns true SAR, not dataset artifacts

### SHAP Chemical Sanity Check
- Top SHAP features must include: LogP, HBD, HBA, TPSA, Aromatic Rings, MW
- If only fingerprint bits dominate → overfitting warning

### External Validation (GPCRdb Blind Test)
- Loads novel compounds from GPCRdb not in ChEMBL
- Verifies SMILES not in training registry (barcode check)
- Reports per-subtype R²/MAE on truly unseen chemotypes

### Literature Benchmarking
- Compares against published models (Rodríguez-Pérez et al., Salmaso et al., etc.)
- Automatic JSON report in `outputs/benchmark/`

---

## 📥 Training Dataset

The model is trained on **33,401 curated pChEMBL values** from two primary sources:

### Raw Sources (`data/raw/`)
| File | Source | Records | Description |
|------|--------|---------|-------------|
| `AR_all_unique_parents_with_smiles.csv` | ChEMBL v34+ | ~28K | Primary bioactivity export |
| `GPCRdb_A1.xlsx` | GPCRdb | ~1.2K | A<sub>1</sub> curated ligands |
| `GPCRdb_A2A.xlsx` | GPCRdb | ~1.5K | A<sub>2A</sub> curated ligands |
| `GPCRdb_A2B.xlsx` | GPCRdb | ~1.1K | A<sub>2B</sub> curated ligands |
| `GPCRdb_A3.xlsx` | GPCRdb | ~1.3K | A<sub>3</sub> curated ligands |

### Processing Pipeline
1. **Standardization**: Canonical SMILES (RDKit), salt stripping, charge neutralization
2. **Quality Filters**: Confidence ≥6, "=" relation, B/F assays, K<sub>i</sub>/K<sub>d</sub>/IC<sub>50</sub>/EC<sub>50</sub> only
3. **Deduplication**: Median pChEMBL per (SMILES, subtype); K<sub>i</sub>/K<sub>d</sub> priority
4. **Scaffold Split**: Global Bemis-Murcko, 80/20 — zero scaffold overlap
5. **Featurization**: Morgan (2048, r=2) + MACCS (166) + 15 RDKit descriptors
6. **Feature Filtering**: Drop >5% NaN, variance <0.01, |corr| >0.90

### Reproducibility
```bash
# Regenerate everything from raw data
python -m src.retrain_production
```
Outputs written to `data/processed/`, `models/precise/`, `outputs/validoutput/precise/`.

**Licenses**: ChEMBL (CC BY-SA 4.0), GPCRdb (CC BY 4.0). Processed derivatives inherit source licenses.

---

## 🚀 Setup & Installation

```bash
git clone https://github.com/UtkarshPatel2405/Adenosine_Selectivity_Model.git
cd Adenosine_Selectivity_Model

# Conda environment option
conda create -n NAME_OF_ENV
conda activate NAME_OF_ENV
conda install python=3.12
conda install --file requirements.txt
```

---

## ⚙️ Configuration

Key settings in `src/config.py`:
```python
SUBTYPES = ["A1", "A2A", "A2B", "A3"]
SCAFFOLD_TEST_SIZE = 0.2
SCAFFOLD_SPLIT_SEED = 42
MORGAN_BITS = 2048
MORGAN_RADIUS = 2
MAPIE_CONFIDENCE = 0.90
MAPIE_CV_FOLDS = 5
Y_RAND_ITERATIONS = 20
FEATURE_NAN_THRESHOLD = 0.05
FEATURE_VAR_THRESHOLD = 0.01
FEATURE_CORR_THRESHOLD = 0.90
```

Environment variables (optional):
```bash
ADENOSINE_DATA_DIR=/path/to/data
ADENOSINE_MODELS_DIR=/path/to/models
ADENOSINE_OUTPUTS_DIR=/path/to/outputs
MLFLOW_TRACKING_URI=...  # For experiment tracking
```

---

## 🐳 Docker

```bash
docker build -t adenosine-selectivity .
docker run -p 8501:8501 adenosine-selectivity
# Dashboard at http://localhost:8501
```

---

## 📚 Citation

If you use this platform in your research, please cite:

```bibtex
@software{adenosine_selectivity_2026,
  title = {Adenosine Receptor Selectivity & Affinity Predictor: Conformal QSAR for GPCR Drug Discovery},
  author = {Utkar Anand},
  year = {2026},
  url = {https://github.com/utkar/Adenosine_Selectivity_Model}
}
```

Key methodological references:
- **Conformal Prediction**: Vovk et al. (2005), Romano et al. (2019) — MAPIE implementation
- **Scaffold Splitting**: Sheridan (2013) — Bemis-Murcko for OOD generalization  
- **Y-Randomization**: Eriksson et al. (2003) — QSAR validation standard
- **SHAP**: Lundberg & Lee (2017) — TreeSHAP for XGBoost
- **Direct Selectivity Modeling**: Cortés-Ciriano & Bender (2019) — ΔpChEMBL regression

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests: `pytest tests/`
4. Run linting: `ruff check src/`
5. Submit PR with clear description

---

## 📄 License

MIT License — see `LICENSE` file for details.

**Data Use**: ChEMBL and GPCRdb data subject to their respective licenses (CC BY-SA 4.0 / CC BY 4.0). This repository contains only processed derivatives and code.

---

## 🙏 Acknowledgments

- **ChEMBL Team** (EBI) for curated bioactivity data
- **GPCRdb** for structural annotations and ligand sets
- **RDKit** for cheminformatics toolkit
- **MAPIE** team for conformal prediction library
- **PyTorch Geometric** for GNN infrastructure
- **Streamlit** for the dashboard framework
