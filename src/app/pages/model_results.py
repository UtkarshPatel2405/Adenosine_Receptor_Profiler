# src/app/pages/model_results.py
"""Model results page — all 7 tabs with fallback messages when no data."""
import streamlit as st
import pandas as pd
import json
from pathlib import Path
import plotly.graph_objects as go
from src.config import SUBTYPES
from src.app.components.model_reports import load_evaluation_tables, load_run_summary, load_examples, _load_json

BD = "outputs/validoutput/precise"

@st.cache_data
def get_file_bytes(filepath: str):
    return Path(filepath).read_bytes()

def _methodology():
    st.markdown('''
    <div class="section-header">📐 Pipeline Methodology</div>
    <div class="card" style="padding:.8rem 1rem;margin-bottom:.6rem">
    <div style="font-size:.7rem;color:#94a3b8;line-height:1.5;margin-bottom:.6rem">
    <b>Pipeline Overview.</b> 33,401 pChEMBL values across 4 adenosine receptor subtypes curated from ChEMBL.
    Morgan FP (2048), MACCS (167), 15 RDKit descriptors = 2,230 features.
    Scaffold split (Murcko, 80/20) ensures OOD generalization.
    </div>''', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="card card-glow anim-in" style="text-align:center;padding:.5rem .3rem"><div class="section-header" style="font-size:.55rem;justify-content:center;margin-bottom:.2rem">📚 Data Curation</div><div style="color:#94a3b8;font-size:.55rem">ChEMBL + Lit · 33K values · 4 subtypes</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="card card-glow anim-in-d1" style="text-align:center;padding:.5rem .3rem"><div class="section-header" style="font-size:.55rem;justify-content:center;margin-bottom:.2rem">🧪 Featurization</div><div style="color:#94a3b8;font-size:.55rem">Morgan (2048) · MACCS (167) · RDKit (15)</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="card card-glow anim-in-d2" style="text-align:center;padding:.5rem .3rem"><div class="section-header" style="font-size:.55rem;justify-content:center;margin-bottom:.2rem">🔀 Scaffold Split</div><div style="color:#94a3b8;font-size:.55rem">Murcko 80/20 · Novel chemotypes</div></div>', unsafe_allow_html=True)

    st.markdown('<div style="display:flex;flex-wrap:wrap;gap:.4rem;justify-content:center;margin:.5rem 0">'
        '<span class="badge badge-blue">🌲 XGBoost</span>'
        '<span class="badge badge-green">🌳 RandomForest</span>'
        '<span class="badge badge-amber">⚡ LightGBM</span>'
        '<span class="badge badge-purple">🛡️ Conformal Prediction (MAPIE CV+ 90% CI)</span>'
        '<span class="badge badge-cyan">🎯 Prediction</span>'
        '</div>', unsafe_allow_html=True)

    st.markdown('''
    <div style="display:flex;flex-wrap:wrap;gap:.4rem;justify-content:center;margin:.5rem 0 .3rem;font-size:.6rem;color:#64748b">
    <span>↓ </span> <span class="badge badge-blue">XGBoost</span>
    <span>→ </span> <span class="badge badge-green">RandomForest</span>
    <span>→ </span> <span class="badge badge-amber">LightGBM</span>
    <span>→ </span> <span class="badge badge-purple">Conformal</span>
    <span>→ </span> <span class="badge badge-cyan">Ensemble</span>
    </div>''', unsafe_allow_html=True)

    st.markdown('<div style="font-size:.55rem;color:#64748b;margin-top:.3rem"><b>Conformal Prediction:</b> Each prediction is accompanied by a 90% confidence interval. Coverage (the fraction of true values within predicted intervals) is the primary reliability metric — target: ≥0.85.</div>', unsafe_allow_html=True)


def _dataset_section():
    st.markdown('<div class="sd"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header">📥 Training Dataset Download</div>', unsafe_allow_html=True)
    st.markdown('''
    <div class="sci-box">
    <b>Training Data Sources.</b> The model is trained on a curated dataset combining:
    <ul style="margin:.4rem 0;padding-left:1.2rem;font-size:.7rem;line-height:1.6">
    <li><b>ChEMBL</b> (v34+): Primary bioactivity database. 33,401 high-quality pChEMBL values (K<sub>i</sub>, K<sub>d</sub>, IC<sub>50</sub>, EC<sub>50</sub>) across A<sub>1</sub>, A<sub>2A</sub>, A<sub>2B</sub>, A<sub>3</sub> human adenosine receptors. Filtered for confidence score ≥ 6, direct binding/functional assays, equality relations only.</li>
    <li><b>GPCRdb</b>: Structural data and ligand annotations for GPCR targets. Provides additional validated actives and decoys for A<sub>1</sub>, A<sub>2A</sub>, A<sub>2B</sub>, A<sub>3</sub>.</li>
    <li><b>P2Y Structural Decoys</b>: Property-matched decoys for negative control training.</li>
    </ul>
    <b>Data Processing Pipeline:</b>
    <ol style="margin:.4rem 0;padding-left:1.2rem;font-size:.7rem;line-height:1.6">
    <li>Standardization: Canonical SMILES via RDKit, salt stripping, charge neutralization</li>
    <li>Deduplication: Median pChEMBL per (SMILES, subtype) pair; priority to K<sub>i</sub>/K<sub>d</sub> over IC<sub>50</sub>/EC<sub>50</sub></li>
    <li>Scaffold Split: Bemis-Murcko scaffolds, 80/20 train/test — ensures no scaffold overlap</li>
    <li>Featurization: Morgan FP (2048-bit, r=2) + MACCS (166-bit) + 15 RDKit physicochemical descriptors</li>
    <li>Feature Filtering: Remove features with >5% NaN, variance <0.01, correlation >0.90</li>
    </ol>
    </div>
    ''', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('''
        <div class="card" style="padding:.8rem">
        <b style="color:#e2e8f0">Raw Data Files (data/raw/)</b>
        <ul style="font-size:.65rem;color:#94a3b8;margin:.4rem 0;padding-left:1rem;line-height:1.8">
        <li><code>AR_all_unique_parents_with_smiles.csv</code> — ChEMBL export</li>
        <li><code>GPCRdb_A1.xlsx</code> — A<sub>1</sub> receptor ligands</li>
        <li><code>GPCRdb_A2A.xlsx</code> — A<sub>2A</sub> receptor ligands</li>
        <li><code>GPCRdb_A2B.xlsx</code> — A<sub>2B</sub> receptor ligands</li>
        <li><code>GPCRdb_A3.xlsx</code> — A<sub>3</sub> receptor ligands</li>
        </ul>
        <a href="https://www.ebi.ac.uk/chembl/" target="_blank" style="color:#38bdf8;font-size:.6rem">ChEMBL Database →</a>
        <span style="color:#64748b;font-size:.6rem"> | </span>
        <a href="https://gpcrdb.org/" target="_blank" style="color:#38bdf8;font-size:.6rem">GPCRdb →</a>
        </div>
        ''', unsafe_allow_html=True)
    with col2:
        st.markdown('''
        <div class="card" style="padding:.8rem">
        <b style="color:#e2e8f0">Processed Data (data/processed/)</b>
        <ul style="font-size:.65rem;color:#94a3b8;margin:.4rem 0;padding-left:1rem;line-height:1.8">
        <li><code>db_lookup.json</code> — SMILES → pChEMBL lookup (all subtypes)</li>
        <li><code>db_lookup_train.json</code> — Training set lookup</li>
        <li><code>global_split.json</code> — Scaffold train/test indices</li>
        <li><code>train_smiles.pkl / test_smiles.pkl</code> — Split SMILES lists</li>
        <li><code>train_fps.pkl</code> — Training fingerprints for AD</li>
        <li><code>features_train.pkl / features_test.pkl</code> — Feature matrices</li>
        <li><code>smiles_to_pdb.json</code> — SMILES ↔ PDB mapping</li>
        </ul>
        </div>
        ''', unsafe_allow_html=True)

    st.markdown('''
    <div style="font-size:.55rem;color:#64748b;margin-top:.4rem">
    <b>Reproducibility:</b> Run <code>python src/retrain_production.py</code> to regenerate all processed data and models from raw sources.
    The pipeline uses <code>data/raw/</code> as input and writes to <code>data/processed/</code>, <code>models/precise/</code>, <code>outputs/validoutput/precise/</code>.
    </div>
    ''', unsafe_allow_html=True)


def _no_data(tab_name="this tab"):
    st.markdown(
        f'<div style="text-align:center;padding:1.5rem;color:#64748b;font-size:.75rem">'
        f'No {tab_name} data available. Run <code>python src/retrain_production.py</code> to generate evaluation reports.'
        f'</div>', unsafe_allow_html=True)


def render_model_results():
    has_data = Path(f"{BD}/evaluation_precise_report.json").exists()
    if not has_data:
        st.markdown(
            '<div class="card" style="text-align:center;padding:.8rem;margin-bottom:.5rem">'
            '<span style="font-size:.75rem;color:#94a3b8">📊 Model evaluation reports not yet generated.</span>'
            '<span style="font-size:.65rem;color:#64748b;margin-left:.3rem">Run <code>python src/retrain_production.py</code></span>'
            '</div>', unsafe_allow_html=True)

    tabs = st.tabs(["📊 Metrics", "🧩 SHAP/Y-Rand", "📋 Diagnostics", "🔍 Examples", "🔬 External", "📂 Raw Dataset", "📐 Method."])

    with tabs[0]:
        st.markdown('<div class="section-header">📊 Model Performance</div>', unsafe_allow_html=True)
        st.markdown('''
        <div class="sci-box">
        <b>Model Performance Metrics.</b> All metrics computed on the scaffold-split test set (20% of data, no scaffold overlap with training).
        <br><br>
        <b>Key Metrics Explained:</b>
        <ul style="margin:.4rem 0;padding-left:1rem;font-size:.65rem;line-height:1.7">
        <li><b>MAE (Mean Absolute Error):</b> Average absolute difference between predicted and experimental pChEMBL. Lower is better. Typical assay noise is ±0.3–0.5 pChEMBL units.</li>
        <li><b>RMSE (Root Mean Squared Error):</b> Penalizes large errors more heavily than MAE. Useful for detecting catastrophic failures.</li>
        <li><b>R² (Coefficient of Determination):</b> Fraction of variance explained. 1.0 = perfect prediction, 0 = random guessing, negative = worse than mean.</li>
        <li><b>Baseline R²:</b> R² of a simple mean predictor. Model R² should significantly exceed this.</li>
        <li><b>Conformal Coverage (90%):</b> Fraction of test points where the true value falls within the predicted 90% confidence interval. Target: ≥0.85 (well-calibrated).</li>
        </ul>
        <b>Per-Subtype Metrics:</b> Show performance for each adenosine receptor (A1, A2A, A2B, A3) separately. n_test = number of test compounds for that subtype.
        </div>''', unsafe_allow_html=True)
        if not has_data:
            _no_data("metrics")
        else:
            try:
                o, p = load_evaluation_tables(BD)
                if not o.empty:
                    st.markdown('<b style="font-size:.7rem;color:#e2e8f0">Overall Metrics (All Subtypes Combined)</b>', unsafe_allow_html=True)
                    st.dataframe(o, use_container_width=True, hide_index=True)
                if not p.empty:
                    st.markdown('<b style="font-size:.7rem;color:#e2e8f0">Per-Subtype Metrics</b>', unsafe_allow_html=True)
                    st.dataframe(p, use_container_width=True, hide_index=True)
            except Exception as e: st.caption(f"Tables: {e}")
            c1, c2 = st.columns(2)
            with c1:
                for fp in ["outputs/validoutput/precise/calibration_precise_plot.png", "outputs/calibration_plot.png"]:
                    if Path(fp).exists(): st.image(fp, use_container_width=True, caption="Calibration Plot"); break
                st.markdown('''
                <div style="font-size:.55rem;color:#64748b;margin-top:.3rem">
                <b>Calibration Plot:</b> Shows how well the 90% conformal prediction intervals are calibrated.
                X-axis: Predicted confidence level (should match nominal 90%). Y-axis: Observed coverage (fraction of true values within interval).
                <br>• Points on the diagonal (y=x) = perfectly calibrated.
                <br>• Points above diagonal = conservative intervals (wider than needed).
                <br>• Points below diagonal = overconfident intervals (too narrow, missing true values).
                </div>''', unsafe_allow_html=True)
            with c2:
                st.markdown('''
                <div style="font-size:.55rem;color:#64748b;margin-bottom:.3rem">
                <b>MAE by Uncertainty Quartile:</b> Test predictions grouped into 4 bins by predicted uncertainty (σ).
                Well-calibrated models show monotonically increasing MAE with uncertainty.
                </div>''', unsafe_allow_html=True)
                rp = Path(f"{BD}/evaluation_precise_report.json")
                if rp.exists():
                    ed = _load_json(str(rp)) or {}
                    cq = ed.get("overall", {}).get("calibration_quartiles")
                    if cq:
                        fig = go.Figure(go.Bar(x=[f"Q{q['bin']}" for q in cq], y=[q["mae_mean"] for q in cq],
                            marker_color=["#00b4d8","#2ecc71","#f39c12","#e74c3c"],
                            text=[f"{q['mae_mean']:.3f}" for q in cq], textposition="outside"))
                        fig.update_layout(height=220, margin=dict(t=20,b=10,l=10,r=10),
                            xaxis_title="Uncertainty Quartile (Q1=lowest σ, Q4=highest σ)", yaxis_title="MAE",
                            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="#94a3b8", size=10))
                        st.plotly_chart(fig, use_container_width=True)
                        st.markdown('''
                        <div style="font-size:.5rem;color:#64748b;margin-top:.2rem">
                        <b>Interpretation:</b> Q1 (lowest uncertainty) should have lowest MAE. Q4 (highest uncertainty) highest MAE.
                        If MAE is flat across quartiles, uncertainty estimates are not informative.
                        </div>''', unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="section-header">🧩 SHAP & Y-Randomization</div>', unsafe_allow_html=True)
        st.markdown('''
        <div class="sci-box">
        <b>SHAP (SHapley Additive exPlanations)</b> — Game-theoretic method to explain model predictions by computing each feature's contribution.
        <br><br>
        <b>SHAP Bar Plot:</b> Mean absolute SHAP value per feature (global importance). Higher = feature more influential on average.
        <br><b>SHAP Beeswarm Plot:</b> Each dot = one test compound. X-position = SHAP value (impact on prediction). Color = feature value (red=high, blue=low). Vertical spread = feature's impact range.
        <br><br>
        <b>Y-Randomization (Response Permutation Test):</b> Validates the model learns true structure-activity relationships (SAR), not dataset artifacts.
        <ul style="margin:.3rem 0;padding-left:1rem;font-size:.65rem;line-height:1.6">
        <li>Shuffle pChEMBL values randomly (break SMILES→activity link)</li>
        <li>Retrain model on shuffled data, record R²</li>
        <li>Repeat 20× to get null distribution of R² under "no SAR"</li>
        <li><b>Pass criterion:</b> Real R² > Shuffled mean + 3×Shuffled std (p < 0.001)</li>
        </ul>
        If real model R² falls within shuffled distribution → model captures noise/artifacts, not chemistry.
        </div>''', unsafe_allow_html=True)
        if not has_data:
            _no_data("SHAP/Y-Randomization")
        else:
            sc = st.selectbox("Subtype", SUBTYPES, key="sy")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<b style="font-size:.65rem;color:#e2e8f0">SHAP Feature Importance</b>', unsafe_allow_html=True)
                for f in [Path(f"outputs/shap/{sc}_bar.png"), Path(f"outputs/shap/{sc}_beeswarm.png")]:
                    if f.exists(): st.image(str(f), use_container_width=True)
                st.markdown('''
                <div style="font-size:.5rem;color:#64748b;margin-top:.3rem">
                <b>Reading SHAP plots:</b> Top features should be chemically interpretable (LogP, HBD/HBA, TPSA, aromatic rings, MW).
                If only fingerprint bits (FP0, FP123, etc.) dominate → model may overfit to specific training compounds.
                </div>''', unsafe_allow_html=True)
            with c2:
                st.markdown('<b style="font-size:.65rem;color:#e2e8f0">Y-Randomization Test</b>', unsafe_allow_html=True)
                for p in [Path(f"outputs/y_randomization/{sc}_distribution.png")]:
                    if p.exists(): st.image(str(p), use_container_width=True)
                yr = Path(f"outputs/y_randomization/{sc}_report.json")
                if yr.exists():
                    yd = json.loads(yr.read_text())
                    c1m, c2m, c3m = st.columns(3)
                    c1m.metric("Real R²", f"{yd['real_r2']:.3f}")
                    c2m.metric("Shuffled μ", f"{yd['shuffled_r2_mean']:.3f}")
                    c3m.metric("Shuffled σ", f"{yd['shuffled_r2_std']:.3f}")
                    st.markdown(f'''
                    <div style="font-size:.55rem;color:#64748b;margin:.3rem 0">
                    <b>Separation:</b> {(yd["real_r2"] - yd["shuffled_r2_mean"]) / max(yd["shuffled_r2_std"], 1e-6):.1f}σ from shuffled mean.
                    </div>''', unsafe_allow_html=True)
                    if not yd.get("leakage_warning", True):
                        st.markdown('<span class="badge badge-green">✅ True SAR — model captures genuine structure-activity relationships</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="badge badge-amber">⚠ Potential leakage — R² indistinguishable from shuffled</span>', unsafe_allow_html=True)

    with tabs[2]:
        st.markdown('<div class="section-header">📋 Diagnostics</div>', unsafe_allow_html=True)
        st.markdown('''
        <div class="sci-box">
        <b>Dataset Diagnostics.</b> Quality metrics to assess chemical space coverage and data reliability.
        <br><br>
        <b>Key Metrics:</b>
        <ul style="margin:.3rem 0;padding-left:1rem;font-size:.65rem;line-height:1.7">
        <li><b>Compounds:</b> Total unique molecules (after deduplication)</li>
        <li><b>Scaffolds:</b> Unique Bemis-Murcko scaffolds — higher = more diverse chemical space</li>
        <li><b>Diversity Ratio:</b> Scaffolds / Compounds. ~1.0 = all unique scaffolds; <0.3 = many analogs</li>
        <li><b>Activity Cliffs:</b> Pairs with Tanimoto ≥0.85 but ΔpChEMBL ≥1.0. High cliffs = sharp SAR, harder to model</li>
        <li><b>pChEMBL Mean ± Std:</b> Activity range. Mean ~5-7 typical; Std >1.5 = wide dynamic range</li>
        </ul>
        <b>Plots:</b>
        <ul style="margin:.3rem 0;padding-left:1rem;font-size:.65rem;line-height:1.7">
        <li><b>pChEMBL Distribution:</b> Histogram of activity values. Should be roughly unimodal, not bimodal (which suggests mixed assay types)</li>
        <li><b>Activity Cliffs Shifts:</b> For each cliff pair, shows structural change vs activity change. Identifies SAR hotspots.</li>
        </ul>
        </div>''', unsafe_allow_html=True)
        if not has_data:
            _no_data("diagnostics")
        else:
            dg = st.selectbox("Target", ["Combined","A1","A2A","A2B","A3"], key="dg")
            if dg == "Combined":
                dp = Path("outputs/diagnostics/combined_diagnosis_report.json")
                if dp.exists():
                    dd = json.loads(dp.read_text())
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Compounds", dd["n_compounds"])
                    c2.metric("Scaffolds", dd["scaffold_diversity"]["n_unique_scaffolds"])
                    c3.metric("Diversity Ratio", f"{dd['scaffold_diversity']['diversity_ratio']:.3f}")
                if Path("outputs/diagnostics/combined_pchembl_distribution.png").exists():
                    st.image("outputs/diagnostics/combined_pchembl_distribution.png", use_container_width=True)
                    st.markdown('<div style="font-size:.5rem;color:#64748b;margin-top:.2rem">Combined pChEMBL distribution across all 4 subtypes. Vertical lines = mean per subtype.</div>', unsafe_allow_html=True)
            else:
                pf = dg.lower(); dp = Path(f"outputs/diagnostics/{pf}_diagnosis_report.json")
                if dp.exists():
                    dd = json.loads(dp.read_text())
                    c1, c2 = st.columns(2)
                    with c1:
                        st.metric("Compounds", dd["n_compounds"])
                        st.metric("Unique Scaffolds", dd["scaffold_diversity"]["n_unique_scaffolds"])
                    with c2:
                        st.metric("Activity Cliffs", dd.get("n_activity_cliffs", 0))
                        st.metric("pChEMBL Mean±Std", f'{dd["pchembl_stats"]["mean"]:.2f}±{dd["pchembl_stats"]["std"]:.2f}')
                    for px in ["pchembl_distribution", "activity_cliffs_shifts"]:
                        f = Path(f"outputs/diagnostics/{pf}_{px}.png")
                        if f.exists(): 
                            st.image(str(f), use_container_width=True)
                            st.markdown(f'<div style="font-size:.5rem;color:#64748b;margin-top:.2rem"><b>{px.replace("_"," ").title()}:</b> {"Activity value histogram" if "pchembl" in px else "Structural changes vs activity jumps for cliff pairs"}</div>', unsafe_allow_html=True)

    with tabs[3]:
        st.markdown('<div class="section-header">🔍 Example Predictions</div>', unsafe_allow_html=True)
        st.markdown('''
        <div class="sci-box">
        <b>Example Predictions on Test Set.</b> These are molecules from the scaffold-split test set (never seen during training).
        <br><br>
        <b>Columns Explained:</b>
        <ul style="margin:.4rem 0;padding-left:1rem;font-size:.65rem;line-height:1.7">
        <li><b>SMILES:</b> Canonical SMILES of the test molecule</li>
        <li><b>Source:</b> "database" = exact match in training DB (experimental value returned); "model" = ML prediction</li>
        <li><b>Best:</b> Subtype with highest predicted pChEMBL (primary target)</li>
        <li><b>Predictions:</b> pChEMBL values for A1, A2A, A2B, A3 from XGBoost conformal model</li>
        <li><b>Similarity (AD):</b> Max Tanimoto to training set (Morgan FP). ≥0.6=High, 0.4-0.6=Med, <0.4=Low reliability</li>
        <li><b>Hits:</b> Subtypes where predicted pChEMBL ≥ 6.0 (active threshold)</li>
        </ul>
        <b>Database molecules:</b> Compounds present in ChEMBL/GPCRdb — model returns experimental values (zero uncertainty).<br>
        <b>Novel molecules:</b> Not in database — true out-of-sample predictions with conformal intervals.
        </div>''', unsafe_allow_html=True)
        if not has_data:
            _no_data("example predictions")
        else:
            try:
                sm = load_run_summary(BD); db, no = load_examples(BD)
                if not sm.empty:
                    st.markdown('<b style="font-size:.65rem;color:#e2e8f0">Run Summary</b>', unsafe_allow_html=True)
                    st.dataframe(sm, use_container_width=True, hide_index=True)
                if not db.empty:
                    st.markdown('<b style="font-size:.65rem;color:#e2e8f0">Database Molecules (Experimental Values)</b>', unsafe_allow_html=True)
                    st.dataframe(db, use_container_width=True, hide_index=True)
                if not no.empty:
                    st.markdown('<b style="font-size:.65rem;color:#e2e8f0">Novel Molecules (Model Predictions)</b>', unsafe_allow_html=True)
                    st.dataframe(no, use_container_width=True, hide_index=True)
            except: pass

    with tabs[4]:
        st.markdown('<div class="section-header">🔬 External Validation</div>', unsafe_allow_html=True)
        st.markdown('''
        <div class="sci-box">
        <b>External Validation (Literature Test Set).</b> Blind test on molecules from recent literature <b>not in ChEMBL/GPCRdb</b> at training time.
        This is a stricter generalization test than the scaffold split — evaluates real-world prospective performance.
        <br><br>
        <b>Metrics:</b>
        <ul style="margin:.4rem 0;padding-left:1rem;font-size:.65rem;line-height:1.7">
        <li><b>Molecules:</b> Number of external test compounds</li>
        <li><b>OK:</b> Successfully predicted (valid SMILES, features computable)</li>
        <li><b>Errors:</b> Failed predictions (parsing/feature errors)</li>
        <li><b>Per-Subtype R²/MAE:</b> Performance on external set (may be lower than internal test due to domain shift)</li>
        <li><b>Selectivity Recall@1:</b> For multi-target compounds, fraction where top predicted subtype matches experimental top subtype</li>
        </ul>
        </div>''', unsafe_allow_html=True)
        ep = Path("outputs/external_validation/external_validation_report.json")
        if not ep.exists():
            _no_data("external validation")
        else:
            ed = json.loads(ep.read_text())
            c1, c2, c3 = st.columns(3)
            c1.metric("Molecules", ed.get("n_novel_molecules", 0))
            c2.metric("OK", ed.get("n_successful_predictions", 0))
            c3.metric("Errors", ed.get("n_errors", 0))
            rows = []
            for sn, m in ed.get("per_subtype_metrics", {}).items():
                if sn == "selectivity_recall_at_1": continue
                rows.append({"Subtype": sn, "N": m.get("n"), "R²": "—" if m.get("insufficient_data") else f'{m.get("r2"):.3f}', "MAE": "—" if m.get("insufficient_data") else f'{m.get("mae"):.3f}'})
            if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            if "selectivity_recall_at_1" in ed.get("per_subtype_metrics", {}):
                sel = ed["per_subtype_metrics"]["selectivity_recall_at_1"]
                st.markdown(f'<div style="font-size:.6rem;color:#94a3b8;margin-top:.3rem"><b>Selectivity Recall@1:</b> {sel.get("recall",0):.1%} ({sel.get("correct",0)}/{sel.get("total",0)} multi-target compounds correctly ranked)</div>', unsafe_allow_html=True)
    with tabs[5]:
        st.markdown('<div class="section-header">📥 Raw Dataset Files</div>', unsafe_allow_html=True)
        st.markdown('''
        <div class="sci-box">
        <b>Original Datasets.</b> Download the original experimental bioactivity datasets and query scripts used to compile the model training sets.
        Only raw source data is listed here; processed feature matrices and model lookups are excluded.
        </div>
        ''', unsafe_allow_html=True)

        raw_files = [
            ("AR_all_unique_parents_with_smiles.csv", "ChEMBL raw parent compounds with bioactivity values"),
            ("GPCRdb_A1.xlsx", "A1 adenosine receptor ligands from GPCRdb"),
            ("GPCRdb_A2A.xlsx", "A2A adenosine receptor ligands from GPCRdb"),
            ("GPCRdb_A2B.xlsx", "A2B adenosine receptor ligands from GPCRdb"),
            ("GPCRdb_A3.xlsx", "A3 adenosine receptor ligands from GPCRdb"),
            ("1_get_entries_ARs", "Shell script to fetch parent entries from ChEMBL database"),
            ("2_add_smiles_to_db_new", "Python utility script to map SMILES descriptors and compile registry")
        ]

        cols = st.columns(2)
        for idx, (filename, description) in enumerate(raw_files):
            col = cols[idx % 2]
            filepath = Path("data/raw") / filename
            if filepath.exists():
                file_size_bytes = filepath.stat().st_size
                file_size_kb = file_size_bytes / 1024.0
                size_str = f"{file_size_kb:.1f} KB" if file_size_kb < 1024 else f"{file_size_kb/1024.0:.2f} MB"
                
                with col:
                    st.markdown(f"""
                    <div style="margin-top:0.8rem; margin-bottom:0.2rem">
                        <span style="font-size:0.75rem; color:#e2e8f0; font-weight:600; font-family: monospace">{filename}</span>
                        <span style="font-size:0.6rem; color:#64748b; margin-left:0.3rem">({size_str})</span>
                    </div>
                    <div style="font-size:0.65rem; color:#94a3b8; margin-bottom:0.4rem">{description}</div>
                    """, unsafe_allow_html=True)
                    
                    st.download_button(
                        label=f"Download {filename}",
                        data=get_file_bytes(str(filepath)),
                        file_name=filename,
                        mime="text/csv" if filename.endswith(".csv") else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if filename.endswith(".xlsx") else "application/octet-stream",
                        key=f"dl_tab_{filename}"
                    )

        # Full curated database download
        st.markdown('<div class="sd"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-header">📦 Full Curated Database Download</div>', unsafe_allow_html=True)
        st.markdown('''
        <div class="sci-box">
        <b>Complete Training Database.</b> Download the full curated pChEMBL dataset used for model training.
        Each row is a unique compound (canonical SMILES) with experimental pChEMBL values for each adenosine receptor subtype where data is available.
        </div>
        ''', unsafe_allow_html=True)
        
        db_path = Path("data/processed/db_lookup_train.json")
        if db_path.exists():
            try:
                db_data = json.loads(db_path.read_text())
                rows = []
                for smiles, subtypes in db_data.items():
                    row = {"SMILES": smiles}
                    for s in ["A1", "A2A", "A2B", "A3"]:
                        val = subtypes.get(s)
                        row[f"pChEMBL_{s}"] = float(val) if val is not None and str(val).lower() != "nan" else None
                    rows.append(row)
                df_db = pd.DataFrame(rows)
                n_compounds = len(df_db)
                n_values = df_db[["pChEMBL_A1", "pChEMBL_A2A", "pChEMBL_A2B", "pChEMBL_A3"]].notna().sum().sum()
                st.markdown(f'<div style="font-size:.7rem;color:#b0bec5;margin-bottom:.4rem">'
                    f'<b>{n_compounds:,}</b> unique compounds · <b>{int(n_values):,}</b> pChEMBL values across 4 subtypes'
                    f'</div>', unsafe_allow_html=True)
                csv_bytes = df_db.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download Full Database (CSV)",
                    data=csv_bytes,
                    file_name="adenosine_receptor_database.csv",
                    mime="text/csv",
                    key="dl_full_database",
                    use_container_width=True,
                )
            except Exception as e:
                st.warning(f"Could not load database: {e}")
        else:
            st.info("Database file not found. Run `python -m src.retrain_production` first.")

    with tabs[6]:
        _methodology()
        lp = Path("outputs/benchmark/benchmark_comparison.json")
        if lp.exists():
            st.markdown('<div class="sd"></div>', unsafe_allow_html=True)
            ld = json.loads(lp.read_text())
            rows = [{"Model": k, "Method": v.get("method",""), "Split": v.get("split",""),
                **{f"{s} R²": v.get("metrics",{}).get(s,{}).get("r2") for s in SUBTYPES}} for k,v in ld.items()]
            st.markdown('<div class="section-header">📚 Literature Benchmarks</div>', unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Dataset Download Section
        st.markdown('<div class="sd"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-header">📥 Training Dataset & Resources</div>', unsafe_allow_html=True)
        st.markdown('''
        <div class="sci-box">
        <b>Training Data Sources.</b> The models are trained on a curated dataset combining ChEMBL bioactivity data and GPCRdb annotations for human adenosine receptors.
        </div>''', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('''
            <div class="card" style="padding:.8rem 1rem">
            <div style="font-size:.7rem;color:#38bdf8;font-weight:600;margin-bottom:.4rem">📊 ChEMBL (Primary Source)</div>
            <div style="font-size:.65rem;color:#94a3b8;line-height:1.6">
            <b>File:</b> <code>data/raw/AR_all_unique_parents_with_smiles.csv</code><br>
            <b>Content:</b> 33,401 pChEMBL values across A1, A2A, A2B, A3 subtypes<br>
            <b>Filters:</b> Standard relation "=", confidence ≥ 6, binding/functional assays, K<sub>i</sub>/K<sub>d</sub>/IC<sub>50</sub>/EC<sub>50</sub><br>
            <b>Deduplication:</b> Median pChEMBL per (SMILES, subtype) pair, Bemis-Murcko scaffold split
            </div>
            </div>''', unsafe_allow_html=True)
        with col2:
            st.markdown('''
            <div class="card" style="padding:.8rem 1rem">
            <div style="font-size:.7rem;color:#38bdf8;font-weight:600;margin-bottom:.4rem">🧬 GPCRdb (Supplementary)</div>
            <div style="font-size:.65rem;color:#94a3b8;line-height:1.6">
            <b>Files:</b> <code>data/raw/GPCRdb_A1.xlsx</code>, <code>_A2A.xlsx</code>, <code>_A2B.xlsx</code>, <code>_A3.xlsx</code><br>
            <b>Content:</b> Curated ligand annotations from GPCRdb with pK<sub>i</sub>/pK<sub>d</sub> values<br>
            <b>Confidence:</b> Score 9 (high-confidence experimental data)<br>
            <b>Use:</b> Augments ChEMBL with additional validated actives
            </div>
            </div>''', unsafe_allow_html=True)

        st.markdown('''
        <div class="card" style="padding:.8rem 1rem;margin-top:.5rem">
        <div style="font-size:.7rem;color:#38bdf8;font-weight:600;margin-bottom:.4rem">📦 Processed Training Artifacts (Generated)</div>
        <div style="font-size:.65rem;color:#94a3b8;line-height:1.6">
        <b>data/processed/train_smiles.pkl</b> — Canonical training SMILES list (pickle)<br>
        <b>data/processed/train_fps.pkl</b> — Morgan fingerprints for training set (for AD/Tanimoto)<br>
        <b>data/processed/features_train.pkl</b> — Full feature matrix (Morgan + MACCS + RDKit descriptors)<br>
        <b>data/processed/features_test.pkl</b> — Test set feature matrix<br>
        <b>data/processed/global_split.json</b> — Scaffold split indices (train/test)<br>
        <b>data/processed/db_lookup_train.json</b> — SMILES → pChEMBL lookup for database hits<br>
        <b>data/processed/smiles_to_pdb.json</b> — Known ligand PDB mappings for structure visualization
        </div>
        </div>''', unsafe_allow_html=True)

        st.markdown('''
        <div style="font-size:.55rem;color:#64748b;margin-top:.5rem">
        <b>Reproducibility:</b> Run <code>python -m src.retrain_production</code> to regenerate all processed data and models from raw sources.<br>
        <b>Data License:</b> ChEMBL data (CC BY-SA 4.0), GPCRdb (CC BY 4.0). Processed derivatives inherit source licenses.
        </div>''', unsafe_allow_html=True)
