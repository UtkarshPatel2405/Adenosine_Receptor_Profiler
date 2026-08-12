# src/app/pages/single_predict.py
"""Single molecule prediction — SMILES input only, all original features."""
import streamlit as st
import pandas as pd
import pickle, time, json
from pathlib import Path
from datetime import datetime

from src.config import SUBTYPES
from src.predictor import predict
from src.chem_utils import topk_tanimoto, draw_2d_svg, generate_3d_conformer, generate_pdb_block, check_pains, qed_profile, nearest_tanimoto
from src.pdb_utils import search_pdb_for_smiles_batch

EXAMPLES = {
    "Adenosine": "C1=NC2=C(C(=N1)N)N=CN2[C@@H]3[C@@H]([C@@H]([C@H](O3)CO)O)O",
    "Caffeine": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
    "Theophylline": "CN1C2=C(C(=O)N(C1=O)C)NC=N2",
    "Istradefylline": "CN1C(=O)N(C)C2=C(N1)N(C)C(=O)N2CC3=CC=C(C=C3)OC",
    "Custom": "CCn1c(/N=C/c2ccc(Br)cc2)c(C#N)sc1=S",
}

_DESCRIPTOR_GLOSSARY = {
    "MolWt": "Molecular weight in Da. Affects oral bioavailability (Rule-of-5).",
    "MolLogP": "Octanol-water partition coefficient. Measures lipophilicity — key for membrane permeability.",
    "NumHDonors": "Number of hydrogen bond donors. Affects binding affinity and permeability.",
    "NumHAcceptors": "Number of hydrogen bond acceptors. Key for receptor recognition.",
    "TPSA": "Topological Polar Surface Area. Correlates with passive transport through membranes (Å²).",
    "NumRotatableBonds": "Number of rotatable bonds. Flexibility metric — affects entropic binding cost.",
    "AromRings": "Number of aromatic rings. Common in GPCR ligands for pi-stacking.",
    "Kappa1": "Kier shape index κ1 — molecular shape descriptor based on atom counts.",
    "Kappa2": "Kier shape index κ2 — related to molecular branching.",
    "Kappa3": "Kier shape index κ3 — related to molecular centrality.",
    "BalabanJ": "Balaban distance connectivity index — topological descriptor of molecular branching.",
    "BertzCT": "Bertz complexity index — quantifies molecular structural complexity.",
    "HallKierAlpha": "Hall-Kier alpha modification — corrects Kier indices for heteroatoms.",
    "Chi0n": "Zero-order chi index (atom connectivity).",
    "Chi0v": "Zero-order chi index (valence-corrected).",
    "FractionCSP3": "Fraction of sp3 carbons — correlates with saturation and solubility.",
    "LabuteASA": "Labute Approximate Surface Area — estimates solvent-accessible surface.",
}

_FP_GLOSSARY = [
    ("Morgan FP (ECFP-like)", "Fingerprint bits F0–F2047 encode circular atom neighborhoods at radius 2, analogous to extended-connectivity fingerprints. Each bit represents the presence of a specific substructural pattern. These capture local molecular topology critical for SAR.", "blue"),
    ("MACCS Keys (166 bits)", "MACCS (Molecular ACCess System) keys are 166 predefined structural fragments (MDL public keys). Bits M0–M165 flag the presence/absence of specific functional groups and ring systems.", "green"),
    ("RDKit Physicochemical Descriptors", "15 curated RDKit descriptors capture global molecular properties (lipophilicity, polarity, flexibility, shape, charge distribution). These are essential for interpreting model decisions in chemical terms.", "purple"),
]

@st.cache_data(show_spinner=False)
def _cached_predict(smiles, threshold, run_rf=False):
    return predict(smiles, threshold, run_rf=run_rf)

@st.cache_resource(show_spinner=False)
def _load_shap_model(path):
    with open(path, "rb") as f:
        return pickle.load(f)

def _render_3d(mb):
    e = json.dumps(mb)
    return f'''<!DOCTYPE html><html><head>
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://3dmol.org/build/3Dmol-min.js"></script>
<style>body{{margin:0;background:#070b17}}#v{{width:100%;height:270px;border-radius:8px;background:#070b17}}</style>
</head><body><div id="v"></div><script>
$('#v').ready(function(){{let v=$3Dmol.createViewer('v',{{backgroundColor:'#070b17'}});v.addModel({e},'sdf');
v.setStyle({{}},{{stick:{{radius:.2,colorscheme:'Jmol'}},sphere:{{radius:.4,scale:.3}}}});v.zoomTo();v.render();}});
</script></body></html>'''

def _tag(v, t=6.0):
    p = float(v) if v is not None else 0
    return ("badge badge-green", "Active") if p >= t else ("badge badge-amber", "Weak") if p >= t - 1.5 else ("badge badge-red", "Inact")

def _imp(v):
    return ("badge badge-slate", "N/A") if v is None else ("badge badge-green", "High") if v >= 0.6 else ("badge badge-amber", "Med") if v >= 0.4 else ("badge badge-red", "Low")

def _run_prediction(smi, run_rf=False):
    t0 = time.time()
    mb, _, _ = generate_3d_conformer(smi)
    sv = draw_2d_svg(smi)
    r = _cached_predict(smi, 6.0, run_rf=run_rf)
    el = time.time() - t0
    r["_elapsed"] = el; r["_mol_block"] = mb; r["_svg"] = sv; r["_smiles"] = smi
    r["_profile"] = qed_profile(smi)
    ad_sim = nearest_tanimoto(r["smiles"])
    r["_admitted"] = bool(ad_sim is not None and ad_sim >= 0.4)
    st.session_state.pred = r
    xgb_best = r["predictions"]["XGBoost"].get(r["best_target"], 0)
    st.session_state.history.append({
        "smiles": r["smiles"], "bt": r["best_target"], "bv": xgb_best,
        "t": datetime.now().strftime("%H:%M"), "name": r["smiles"][:20]})
    row = {"SMILES": r["smiles"], "Best": r["best_target"]}
    for s in SUBTYPES: row[s] = r["predictions"]["XGBoost"].get(s)
    row["Source"] = r["source"]
    st.session_state.history_df = pd.concat(
        [st.session_state.history_df, pd.DataFrame([row])], ignore_index=True)

def _render_methodology_badges():
    badges = [
        ("XGBoost", "Gradient-boosted trees with conformal prediction (MAPIE CrossConformalRegressor, Jackknife+)", "badge-blue"),
        ("RF", "Random Forest ensemble (300 trees, sqrt features)", "badge-green"),
        ("LightGBM", "Leaf-wise GBDT with conformal prediction (efficient on small data)", "badge-amber"),
        ("Stacked", "Ridge meta-model on XGBoost+RF+LightGBM OOF predictions", "badge-purple"),
        ("FPs", "Morgan (2048 bit, r=2) + MACCS (166 bit)", "badge-cyan"),
        ("Scaffold", "Bemis-Murcko scaffold split (80/20)", "badge-amber"),
    ]
    parts = " ".join(f'<span class="badge {c}" title="{t}">{l}</span>' for l, t, c in badges)
    st.markdown(f'<div style="display:flex;flex-wrap:wrap;gap:.3rem;margin-bottom:.6rem;font-size:.7rem;color:#94a3b8">{parts}</div>', unsafe_allow_html=True)

def _render_uncertainty_explanation(r):
    """Explain what σ (uncertainty) means in practical terms."""
    st.markdown('<div class="sci-box">'
        '<b style="color:#f0f4f8">⏱ Uncertainty (σ) Guide</b><br>'
        'σ = <i>interval_width / 3.29</i>, mapping the 90% conformal prediction interval to an equivalent Gaussian standard deviation. '
        'A 90% CI spans ±1.64σ. Values within ±1σ of each other are <b>not statistically distinguishable</b>.<br><br>'
        '<b style="color:#7dd3fc">Interpretation:</b><br>'
        '• σ &lt; 0.3 → High confidence (well within training domain)<br>'
        '• σ 0.3–0.5 → Moderate confidence<br>'
        '• σ 0.5–0.8 → Low confidence (novel chemotype or boundary prediction)<br>'
        '• σ &gt; 0.8 → Very uncertain — treat prediction as directional only'
        '</div>', unsafe_allow_html=True)

def _render_shap(r, canon):
    try:
        import shap, plotly.graph_objects as go
        from src.features import build_features
        from src.config import MODELS_DIR
        if MODELS_DIR.exists():
            ROOT = MODELS_DIR.parent
        else:
            ROOT = Path(__file__).resolve().parent.parent.parent
        best = r['best_target']
        mp = ROOT / f"models/precise/xgboost_{best}_production.pkl"
        if not mp.exists(): mp = ROOT / f"models/xgboost_{best}_production.pkl"
        if not mp.exists(): mp = ROOT / f"models/precise/xgboost_precise_{best.lower()}_model.pkl"
        if not mp.exists(): mp = ROOT / f"models/xgboost_{best.lower()}_model.pkl"
        if not mp.exists():
            st.caption(f"SHAP model not found for {best} at any expected path.")
            return
        mc = _load_shap_model(mp)
        model_type = type(mc).__name__
        if model_type in ("CrossConformalRegressor", "MapieRegressor"):
            reg = mc._mapie_regressor.estimator_ if model_type == "CrossConformalRegressor" else mc.estimator_
            if hasattr(reg, "single_estimator_"):
                et = reg.single_estimator_
            elif hasattr(reg, "estimators_") and len(reg.estimators_) > 0:
                et = reg.estimators_[0]
            else:
                et = reg
        else:
            et = mc
        sp = ROOT / "models/precise/scaler_precise.pkl"
        if not sp.exists(): sp = ROOT / "models/scaler.pkl"
        if not sp.exists():
            st.caption("Scaler not found. Train models first.")
            return
        with open(sp, "rb") as f: pl = pickle.load(f)
        n_fp, n_maccs = 2048, 167
        desc_names = list(pl.feature_filter.feature_names) if hasattr(pl, 'feature_filter') and pl.feature_filter.feature_names is not None else []
        fn = [f"FP{i}" for i in range(n_fp)] + [f"MAC{i}" for i in range(n_maccs)] + desc_names
        x = build_features(canon, pl).reshape(1, -1)
        actual_len = x.shape[1]
        if len(fn) > actual_len:
            fn = fn[:actual_len]
        elif len(fn) < actual_len:
            fn.extend([f"Feature_{i}" for i in range(len(fn), actual_len)])
        xdf = pd.DataFrame(x, columns=fn)
        e = shap.TreeExplainer(et); sv = e(xdf)
        sv_df = pd.DataFrame({"feature": sv.feature_names, "value": sv.values[0]})
        sv_df["abs"] = sv_df["value"].abs()
        sv_df = sv_df.sort_values("abs", ascending=True).tail(10)
        base = sv.base_values[0]
        colors = ["#e74c3c" if v > 0 else "#3498db" for v in sv_df["value"]]
        fig = go.Figure(go.Bar(x=sv_df["value"], y=sv_df["feature"], orientation="h",
            marker_color=colors, text=[f"{v:+.3f}" for v in sv_df["value"]], textposition="outside"))
        fig.add_vline(x=0, line_color="rgba(255,255,255,.3)", line_width=1)
        fig.update_layout(height=300, margin=dict(t=30, b=10, l=10, r=60),
            xaxis_title="SHAP value", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#94a3b8", size=10),
            title=dict(text=f"<b>{best}</b> · base={base:.3f}", font=dict(size=12, color="#f8fafc")))
        fig.update_xaxes(gridcolor="rgba(255,255,255,.05)")
        fig.update_yaxes(gridcolor="rgba(255,255,255,.05)")
        st.plotly_chart(fig, use_container_width=True)

        # Build feature interpretation table
        feature_rows = []
        for _, row in sv_df[::-1].iterrows():
            feat = row["feature"]
            if feat.startswith("FP"):
                label = f"Morgan bit {feat[2:]}"
                meaning = "Local substructure presence (circular fingerprint bit)"
            elif feat.startswith("MAC"):
                label = f"MACCS key {feat[3:]}"
                meaning = "Predefined structural fragment presence"
            else:
                label = feat
                meaning = _DESCRIPTOR_GLOSSARY.get(feat, "RDKit-calculated molecular descriptor")
            direction = "↑ increases prediction" if row["value"] > 0 else "↓ decreases prediction"
            color = "#7dd3fc" if row["value"] > 0 else "#fca5a5"
            feature_rows.append({
                "Feature": label,
                "Chemical Meaning": meaning,
                "SHAP value": f"{row['value']:+.4f}",
                "Direction": direction,
                "_color": color,
            })
        if feature_rows:
            st.markdown('<div class="section-header">📋 Feature Interpretation</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="sci-box">'
                f'<b style="color:#f0f4f8">How to read SHAP values:</b><br>'
                f'SHAP (SHapley Additive exPlanations) decomposes each prediction into feature contributions. '
                f'The <b style="color:#e74c3c">red bars</b> push the prediction <b>higher</b> (toward active), '
                f'<b style="color:#3498db">blue bars</b> push it <b>lower</b> (toward inactive). '
                f'The <b>base value</b> ({base:.3f}) is the average prediction over the training set. '
                f'Sum of all feature SHAP values + base = final prediction.<br><br>'
                f'<b>Predicted pChEMBL</b> = {base:.3f} + sum(contributions) = '
                f'<b style="color:#f0f4f8">{r["predictions"]["XGBoost"].get(best, 0):.3f}</b>'
                f'</div>', unsafe_allow_html=True)
            for fr in feature_rows:
                st.markdown(
                    f'<div class="feat-row">'
                    f'<span style="color:{fr["_color"]};font-weight:500">{fr["Feature"]}</span>'
                    f'<span style="color:#94a3b8;flex:1;margin:0 .5rem;font-size:.65rem">{fr["Chemical Meaning"][:60]}</span>'
                    f'<span style="font-family:JetBrains Mono,monospace;font-size:.7rem;color:{fr["_color"]}">{fr["SHAP value"]}</span>'
                    f'</div>', unsafe_allow_html=True)
    except Exception as ex:
        st.caption(f"SHAP: {ex}")

def render_single_predict():
    if "smiles_val" not in st.session_state:
        st.session_state.smiles_val = "CCn1c(/N=C/c2ccc(Br)cc2)c(C#N)sc1=S"

    def on_example_change():
        eg = st.session_state.eg_select
        if eg != "Custom":
            st.session_state.smiles_val = EXAMPLES[eg]

    def on_smiles_change():
        st.session_state.eg_select = "Custom"

    _render_methodology_badges()

    ci, cx = st.columns([3, 1])
    with cx:
        st.selectbox("Example", list(EXAMPLES.keys()), key="eg_select", on_change=on_example_change, label_visibility="collapsed")
    with ci:
        st.text_input("SMILES", key="smiles_val", on_change=on_smiles_change, label_visibility="collapsed", placeholder="Enter SMILES…")

    smiles = st.session_state.smiles_val

    if st.button("🔬 Predict", use_container_width=True):
        with st.spinner("Running all 4 models + Ridge stacking + conformal intervals…"):
            try: _run_prediction(smiles, run_rf=True)
            except Exception as e: st.error(f"Error: {e}"); return

    r = st.session_state.pred
    if r is None:
        st.info("Enter a SMILES and click Predict to begin."); return

    canon = r["smiles"]; preds = r["predictions"]; unc = r["uncertainty"]
    d = r["descriptors"]; prof = r.get("_profile", {}) or {}
    qed = prof.get("QED", 0) if isinstance(prof, dict) else 0
    mb = r.get("_mol_block"); sv = r.get("_svg"); el = r.get("_elapsed", 0)

    # ── Source badge ──
    src_badge = "badge badge-green" if r["in_database"] else "badge badge-blue"
    src_label = "Database Hit (experimental)" if r["in_database"] else "ML Ensemble Prediction"
    st.markdown(f'<div style="display:flex;align-items:center;gap:.4rem;margin-bottom:.5rem" class="anim-in">'
        f'<span class="{src_badge}">{src_label}</span>'
        f'<span class="anim-in-d1" style="font-size:.65rem;color:#64748b">{el:.1f}s</span>'
        f'<span class="anim-in-d2" style="font-size:.65rem;color:#64748b;margin-left:auto">{canon[:50]}{".." if len(canon)>50 else ""}</span>'
        f'</div>', unsafe_allow_html=True)

    admitted = bool(r.get("_admitted"))
    if not admitted:
        al = check_pains(canon)
        pains_badge = "badge badge-red" if al else "badge badge-green"
        pains_label = f"{len(al)} PAINS alerts" if al else "No PAINS"
        sim = nearest_tanimoto(canon)
        st.markdown(
            '<div class="ad-warning-box-oi">'
            '<b style="color:#f87171">⚠ Out of Model Scope — quantitative predictions withheld.</b><br>'
            f'<span style="color:#cbd5e1">This molecule shares almost nothing with the adenosine-ligand training set '
            f'(nearest Tanimoto = {sim:.3f} &lt; 0.4), so pChEMBL / selectivity / SHAP would be unvalidated extrapolations. '
            'See the neighbors table below for real measured activities of the closest deposited structures.</span>'
            '</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="section-header">⚗️ Chemical Property Alerts</div>', unsafe_allow_html=True)
        ca, cb = st.columns(2)
        with ca:
            st.markdown(f'<div class="card" style="text-align:center;padding:.4rem .5rem">'
                f'<div style="font-size:.6rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.04em;margin-bottom:.2rem">PAINS Filter</div>'
                f'<span class="{pains_badge}">{pains_label}</span>'
                f'</div>', unsafe_allow_html=True)
        with cb:
            st.markdown(f'<div class="card" style="text-align:center;padding:.4rem .5rem">'
                f'<div style="font-size:.6rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.04em;margin-bottom:.2rem">Nearest Training Similarity</div>'
                f'<span class="badge badge-red">Outside AD ({sim:.3f})</span>'
                f'</div>', unsafe_allow_html=True)
        _render_similarity_panel(canon)
        st.stop()

    # ── Feature type explanations ──
    with st.expander("🧩 What features does the model use?", expanded=False):
        st.markdown('<div class="section-header">Feature Engineering</div>', unsafe_allow_html=True)
        for title, desc, color in _FP_GLOSSARY:
            color_map = {"blue": "#7dd3fc", "green": "#86efac", "purple": "#d8b4fe"}
            st.markdown(
                f'<div class="card" style="padding:.5rem .7rem">'
                f'<span style="color:{color_map[color]};font-weight:600;font-size:.8rem">{title}</span><br>'
                f'<span style="font-size:.7rem;color:#94a3b8">{desc}</span>'
                f'</div>', unsafe_allow_html=True)

    # ── Scientific Layout ──
    col1, col2 = st.columns([1, 1.1])

    with col1:
        # 1. Structure Visualization
        st.markdown('<div class="section-header">🧪 Molecular Structure Visualization</div>', unsafe_allow_html=True)
        s1, s2 = st.columns(2)
        with s1:
            if sv:
                st.markdown('<div class="card"><div style="font-size:.65rem;color:#94a3b8;font-weight:600;margin-bottom:.3rem">2D Structure (RDKit)</div>', unsafe_allow_html=True)
                st.image(sv, use_container_width=True)
                st.download_button("⬇ Download SVG", sv, "struct.svg", mime="image/svg+xml", key="sd1")
                st.markdown('</div>', unsafe_allow_html=True)
        with s2:
            if mb:
                st.markdown('<div class="card"><div style="font-size:.65rem;color:#94a3b8;font-weight:600;margin-bottom:.3rem">3D Conformer (ETKDGv3)</div>', unsafe_allow_html=True)
                st.components.v1.html(_render_3d(mb), height=200)
                ca, cb = st.columns(2)
                with ca: st.download_button("⬇ SDF", mb, "conf.sdf", key="sd2")
                with cb:
                    pdb = generate_pdb_block(canon)
                    if pdb: st.download_button("⬇ PDB", pdb, "conf.pdb", key="sd3")
                st.markdown('</div>', unsafe_allow_html=True)

        # 2. Molecular Properties
        props = [("MW", d["MW"], 50, 600, "Da", "#00b4d8", "Molecular weight"),
            ("LogP", d["LogP"], -2, 6, "", "#2ecc71", "Lipophilicity"),
            ("HBD", d["HBD"], 0, 10, "", "#f39c12", "H-bond donors"),
            ("HBA", d["HBA"], 0, 14, "", "#e74c3c", "H-bond acceptors"),
            ("RotB", d["RotBonds"], 0, 15, "", "#9b59b6", "Rotatable bonds"),
            ("TPSA", d["TPSA"], 0, 200, "Å²", "#3498db", "Polar surface area"),
            ("QED", qed, 0, 1, "", "#e67e22", "Drug-likeness score")]
        st.markdown(f'<div class="card"><div class="section-header" style="border-bottom:none;margin-bottom:.3rem">📊 Molecular Properties</div>'
            f'<div style="font-size:.65rem;color:#64748b;margin-bottom:.4rem">Physicochemical descriptors — key for ADME profiling</div>',
            unsafe_allow_html=True)
        for lb, vl, vmin, vmax, unit, color, tip in props:
            pct = min(max((float(vl) - vmin) / (vmax - vmin) * 100, 0), 100)
            vl_s = f"{vl:.1f}" if isinstance(vl, float) and vl != int(vl) else str(vl)
            st.markdown(f'<div style="display:flex;align-items:center;gap:.5rem;margin:.12rem 0" title="{tip}">'
                f'<span style="font-size:.65rem;font-weight:500;min-width:2.5rem;color:#94a3b8">{lb}</span>'
                f'<div class="pb" style="flex:1;height:4px"><div class="f" style="width:{pct}%;background:{color}"></div></div>'
                f'<span style="font-size:.72rem;font-weight:600;min-width:3rem;text-align:right;color:#e2e8f0">{vl_s} '
                f'<span style="font-weight:400;color:#64748b">{unit}</span></span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # 1. Affinity with model selector
        st.markdown(f'<div class="section-header">🎯 Predicted Binding Affinity (pChEMBL) <span class="badge badge-cyan">Best: {r["best_target"]}</span></div>', unsafe_allow_html=True)
        available_models = [m for m in ("XGBoost", "RandomForest", "LightGBM", "Stacked") if any(preds.get(m, {}).values())] or ["XGBoost"]
        sm_ui = st.selectbox("Model", available_models, label_visibility="collapsed")
        sm = sm_ui
        if sm == "RandomForest" and r["source"] == "model" and not any(preds.get("RandomForest", {}).values()):
            with st.spinner("Loading RF ensemble…"):
                try:
                    r_rf = _cached_predict(r["_smiles"], 6.0, run_rf=True)
                    for k2 in ("predictions", "uncertainty", "intervals"):
                        r[k2]["RandomForest"] = r_rf[k2]["RandomForest"]
                    st.session_state.pred = r; st.rerun()
                except Exception as e: st.error(f"RF: {e}")
        for k in SUBTYPES:
            v = preds.get(sm, {}).get(k, 0)
            c_cls, c_lab = _tag(v)
            pct = min(float(v)/10*100, 100)
            co = "#2ecc71" if v >= 6 else "#f39c12" if v >= 4.5 else "#e74c3c"
            dv = f"{v:.2f}"; uv = unc.get(sm, {}).get(k, 0)
            st.markdown(
                f'<div class="affinity-row">'
                f'<b>A<sub>{k[1:]}</sub></b>'
                f'<span class="{c_cls}" style="margin:0 .4rem">{c_lab}</span>'
                f'<b style="font-size:.9rem;min-width:3rem;text-align:right">{dv}</b>'
                f'<div class="pb" style="flex:1;margin:0 .5rem;height:4px"><div class="f" style="width:{pct}%;background:{co}"></div></div>'
                f'<span style="font-size:.6rem;color:#64748b;min-width:3.5rem;text-align:right">σ={uv:.3f}</span>'
                f'</div>', unsafe_allow_html=True)

        # 2. 2-Model Comparison Table
        with st.expander("📊 Multi-Model Selectivity Comparison Table", expanded=True):
            rows = []
            model_keys = [m for m in ("XGBoost", "RandomForest", "LightGBM", "Stacked") if any(preds.get(m, {}).values())] or ["XGBoost"]
            for s in SUBTYPES:
                row = {"Subtype": s}
                for m in model_keys:
                    v = preds.get(m, {}).get(s, 0)
                    u = unc.get(m, {}).get(s, 0)
                    val = float(v) if v is not None else 0.0
                    unc_val = float(u) if u is not None else 0.0
                    row[m] = f"{val:.2f}"
                    row[f"σ {m}"] = f"{unc_val:.3f}" if unc_val > 0 else "—"
                rows.append(row)
            df_comp = pd.DataFrame(rows)
            st.dataframe(df_comp.set_index("Subtype"), use_container_width=True)
            
            # Download Comparison CSV button (Fixed & Fully Visible)
            csv_data = df_comp.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Download Model Comparison CSV",
                data=csv_data,
                file_name=f"{r.get('best_target', 'AR')}_model_comparison.csv",
                mime="text/csv",
                key="download_comparison_csv",
                use_container_width=True,
            )
            if r["in_database"]:
                dbv = r.get("db_value") or {}
                db_txt = ", ".join(f"{st}={dbv.get(st):.2f}" for st in ("A1", "A2A", "A2B", "A3") if isinstance(dbv.get(st), (int, float)))
                st.caption(f"Database hit — measured (experimental) pChEMBL: {db_txt}. Model predictions above are shown for reference and may differ from the measured values.")
            _render_uncertainty_explanation(r)

    # ── SHAP Feature Attribution ──
    with st.expander("🔬 SHAP Explainable AI (XAI) Attribution analysis", expanded=True):
        st.markdown('<div class="section-header">Why did the model predict this?</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sci-box">'
            '<b style="color:#f0f4f8">SHAP (SHapley Additive exPlanations)</b> is a game-theory-based method for interpreting '
            'machine learning predictions. It quantifies how each molecular feature contributed to the final pChEMBL prediction. '
            'This helps validate that the model relies on <b>chemically plausible features</b> rather than memorizing noise.<br><br>'
            '<b style="color:#7dd3fc">Chemical Sanity Check:</b> If the top SHAP features are interpretable descriptors '
            '(lipophilicity, H-bond capacity, aromaticity), the model is learning real SAR. '
            'If isolated fingerprint bits dominate, the model may be overfitting to dataset artifacts.'
            '</div>', unsafe_allow_html=True)
        _render_shap(r, canon)

    # ── Selectivity Profile ──
    sel = r.get("selectivity_profile", {})
    if sel:
        st.markdown(f'<div class="sd"></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="section-header">📌 Selectivity Profile</div>', unsafe_allow_html=True)
        s_cols = st.columns(len(sel))
        for idx, (k2, v2) in enumerate(sel.items()):
            with s_cols[idx]:
                st.markdown(f'<div class="card" style="text-align:center;padding:.3rem .5rem"><div class="section-header" style="font-size:.6rem;justify-content:center">{k2.replace("_vs_"," vs ")}</div><span style="font-size:1rem;font-weight:700">{v2:.3f}</span></div>', unsafe_allow_html=True)

# ── Safety / AD / Drug-likeness Alerts ──
    st.markdown('<div class="sd"></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-header">⚗️ Drug-likeness & Applicability Alerts</div>', unsafe_allow_html=True)
    ca, cb, cc = st.columns(3)
    with ca:
        al = check_pains(canon)
        pains_badge = "badge badge-red" if al else "badge badge-green"
        pains_label = f"{len(al)} PAINS alerts" if al else "No PAINS"
        st.markdown(f'<div class="card" style="text-align:center;padding:.4rem .5rem">'
            f'<div style="font-size:.6rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.04em;margin-bottom:.2rem">PAINS Filter</div>'
            f'<span class="{pains_badge}">{pains_label}</span>'
            f'<div style="font-size:.55rem;color:#64748b;margin-top:.3rem">Pan-Assay Interference Compounds — substructures that may give false positives in HTS</div>'
            f'</div>', unsafe_allow_html=True)
    with cb:
        sim = nearest_tanimoto(canon)
        if sim is not None:
            ic, il = _imp(sim)
            st.markdown(f'<div class="card" style="text-align:center;padding:.4rem .5rem">'
                f'<div style="font-size:.6rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.04em;margin-bottom:.2rem">Applicability Domain</div>'
                f'<span class="{ic}">{il} ({sim:.3f})</span>'
                f'<div style="font-size:.55rem;color:#64748b;margin-top:.3rem">Max Tanimoto similarity to training set — higher = more reliable prediction</div>'
                f'</div>', unsafe_allow_html=True)
    with cc:
        st.markdown(f'<div class="card" style="text-align:center;padding:.4rem .5rem">'
            f'<div style="font-size:.6rem;color:#94a3b8;text-transform:uppercase;letter-spacing:.04em;margin-bottom:.2rem">Drug-likeness</div>'
            f'<span class="badge badge-blue">QED {qed:.3f}</span>'
            f'<div style="font-size:.55rem;color:#64748b;margin-top:.3rem">Quantitative Estimate of Drug-likeness (0–1). QED &ge; 0.67 = drug-like</div>'
            f'</div>', unsafe_allow_html=True)

    # ── Top-10 Neighbors ──
    with st.expander("🔗 Top-10 Training Set Neighbors", expanded=True):
        st.markdown('<div class="sci-box" style="font-size:.65rem">'
            '<b style="color:#f0f4f8">Nearest-neighbor analysis</b> evaluates whether the query molecule falls within the '
            'model\'s training distribution. Molecules with Tanimoto similarity &lt; 0.4 to the nearest training compound '
            'are outside the Applicability Domain (AD), and predictions should be interpreted with caution.'
            '</div>', unsafe_allow_html=True)
        _render_similarity_panel(canon)

def _render_similarity_panel(canon):
    """Top-10 neighbors with real deposited PDB / ChEMBL structure links in structured table."""
    from src.chem_utils import topk_tanimoto
    from src.pdb_utils import real_structure_refs_with_analogs

    @st.cache_data(show_spinner=False)
    def _cached_tanimoto(smiles):
        return topk_tanimoto(smiles, k=10)

    try:
        _, ts = _cached_tanimoto(canon)
        if ts:
            rows = []
            for i, (s, t) in enumerate(ts, 1):
                if t >= 0.7:
                    sim_label = f'<span class="badge badge-green">High ({t:.3f})</span>'
                elif t >= 0.4:
                    sim_label = f'<span class="badge badge-amber">Medium ({t:.3f})</span>'
                else:
                    sim_label = f'<span class="badge badge-red">Low ({t:.3f})</span>'

                refs = real_structure_refs_with_analogs(s)
                if refs:
                    links = []
                    for r in refs:
                        cls = "badge-blue" if r["type"] == "pdb" else "badge-purple"
                        label = r["id"]
                        title = r.get("name", r["id"])
                        links.append(f'<a href="{r["url"]}" target="_blank" class="badge {cls}" title="{title}">{label}</a>')
                    pdb_links = " ".join(links)
                else:
                    pdb_links = '<span style="color:#64748b;font-size:.65rem" title="No deposited structure in PDB or ChEMBL">No real structure</span>'

                rows.append({
                    "#": i,
                    "SMILES": f'<span title="{s}" style="display:inline-block;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;vertical-align:middle;font-family:monospace;font-size:.68rem;color:#e2e8f0">{s}</span>',
                    "Tanimoto": sim_label,
                    "Real Structure (PDB / ChEMBL)": pdb_links,
                })

            df = pd.DataFrame(rows)
            st.markdown(
                df.to_html(escape=False, index=False, classes="dataframe"),
                unsafe_allow_html=True
            )
        else:
            st.caption("No similar molecules found in training set.")
    except Exception as ex:
        st.caption(f"Similarity search failed: {ex}")
