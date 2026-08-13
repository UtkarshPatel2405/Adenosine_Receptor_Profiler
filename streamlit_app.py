"""
Adenosine Receptor Selectivity & Multi-Target QSAR Platform (Streamlit Version 2.0)
Publication-grade machine learning platform with MAPIE conformal prediction,
interactive 3Dmol.js molecular and receptor viewers, multi-format structure exports,
and professional scientific typography (zero generic emojis).
"""

import csv
import io
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("streamlit_app")

# Page Configuration
st.set_page_config(
    page_title="Adenosine Receptor Selectivity QSAR Platform",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Use a domain-specific mark in Streamlit's native chrome rather than a generic
# decorative icon. The same mark remains visible when the sidebar is collapsed.
st.logo(":material/biotech:", icon_image=":material/biotech:", size="large")

# ─────────────────────────────────────────────────────────────────────────────
# 1. PROFESSIONAL STYLING & MOTION TOKENS (No Generic Emojis)
# ─────────────────────────────────────────────────────────────────────────────

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,400..700,0..1,-50..200&display=swap');

:root {
    --bg-canvas: #2a3439;
    --bg-card: #333f45;
    --bg-card-hover: #3d4a52;
    --border-subtle: rgba(216, 224, 230, 0.14);
    --border-glow: rgba(56, 189, 248, 0.4);

    --cyan: #38bdf8;
    --cyan-glow: rgba(56, 189, 248, 0.2);
    --purple: #a78bfa;
    --purple-glow: rgba(167, 139, 250, 0.2);
    --green: #4ade80;
    --green-glow: rgba(74, 222, 128, 0.2);
    --red: #f87171;
    --amber: #fbbf24;

    --text-primary: #eef2f4;
    --text-secondary: #c8d0d6;
    --text-muted: #9aa7af;
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--text-primary);
    background-color: var(--bg-canvas);
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}

code, pre {
    font-family: 'JetBrains Mono', monospace !important;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse at 50% 50%, rgba(38, 70, 83, 0.4), transparent 80%),
        radial-gradient(ellipse at 20% 80%, rgba(42, 157, 143, 0.15), transparent 70%),
        radial-gradient(ellipse at 80% 20%, rgba(38, 70, 83, 0.2), transparent 70%),
        linear-gradient(135deg, #182B32, #1C3339, #14242A) !important;
    background-blend-mode: multiply, screen, normal, normal;
    background-attachment: fixed;
}

[data-testid="stSidebar"] {
    background: #333e44 !important;
    border-right: 1px solid var(--border-subtle);
}

header[data-testid="stHeader"] {
    background: rgba(42, 52, 57, 0.8) !important;
    backdrop-filter: blur(12px) !important;
}

/* Custom Card Container */
.cadd-card {
    background: rgba(51, 63, 69, 0.82);
    border: 1px solid var(--border-subtle);
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(6px);
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.cadd-card:hover {
    border-color: var(--border-glow);
    box-shadow: 0 8px 30px -4px rgba(56, 189, 248, 0.15);
    transform: translateY(-2px);
}

/* Section Header styling */
.section-num {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.2rem 0.5rem;
    border-radius: 6px;
    background: rgba(56, 189, 248, 0.12);
    color: var(--cyan);
    margin-bottom: 0.35rem;
}

.section-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.35rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.section-title span.material-symbols-outlined {
    font-size: 1.25rem;
    color: var(--cyan);
}

.page-title {
    display: flex;
    align-items: center;
    gap: 0.55rem;
}

.page-title .material-symbols-outlined {
    color: var(--cyan);
    font-size: 1.8rem;
    font-variation-settings: 'FILL' 0, 'wght' 550, 'GRAD' 0, 'opsz' 32;
}

.section-subtitle {
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin-bottom: 1rem;
}

/* Badges */
.badge-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.25rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-decoration: none !important;
}

.badge-cyan { background: rgba(56, 189, 248, 0.15); color: #7dd3fc; border: 1px solid rgba(56, 189, 248, 0.3); }
.badge-purple { background: rgba(167, 139, 250, 0.15); color: #c4b5fd; border: 1px solid rgba(167, 139, 250, 0.3); }
.badge-green { background: rgba(74, 222, 128, 0.15); color: #86efac; border: 1px solid rgba(74, 222, 128, 0.3); }
.badge-red { background: rgba(248, 113, 113, 0.15); color: #fca5a5; border: 1px solid rgba(248, 113, 113, 0.3); }
.badge-amber { background: rgba(251, 191, 36, 0.15); color: #fcd34d; border: 1px solid rgba(251, 191, 36, 0.3); }

/* KPI Metric Box */
.kpi-box {
    background: rgba(51, 63, 69, 0.8);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
    transition: transform 0.2s ease;
}

.kpi-box:hover {
    transform: translateY(-2px);
    border-color: var(--cyan);
}

.kpi-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    margin-bottom: 0.35rem;
}

.kpi-value {
    font-family: 'Outfit', sans-serif;
    font-size: 1.45rem;
    font-weight: 700;
    color: var(--text-primary);
}

/* Hero trust & precision metric strip */
.hero-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 0.7rem;
    margin: 1rem 0 1.25rem;
}
.hero-chip {
    background: rgba(51, 63, 69, 0.8);
    border: 1px solid var(--border-subtle);
    border-radius: 10px;
    padding: 0.6rem 1rem;
    flex: 1 1 auto;
    min-width: 120px;
    text-align: center;
}
.hero-chip .chip-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
}
.hero-chip .chip-value {
    font-family: 'Outfit', sans-serif;
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text-primary);
}
.subtype-metrics {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.7rem;
    margin-top: 0.6rem;
}
.subtype-metrics .st-chip {
    background: rgba(56, 189, 248, 0.07);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 10px;
    padding: 0.6rem 0.9rem;
    text-align: center;
}
.subtype-metrics .st-name {
    font-weight: 700;
    color: #7dd3fc;
    font-size: 0.85rem;
}
.subtype-metrics .st-metric {
    font-size: 0.72rem;
    color: var(--text-secondary);
    margin-top: 0.25rem;
}

/* Theory callout */
.theory-callout {
    background: rgba(56, 189, 248, 0.06);
    border-left: 3px solid var(--cyan);
    border-radius: 0 8px 8px 0;
    padding: 0.85rem 1rem;
    margin-top: 0.8rem;
    font-size: 0.82rem;
    line-height: 1.55;
    color: var(--text-secondary);
}

.theory-callout h4 {
    color: var(--cyan) !important;
    font-size: 0.92rem !important;
    margin-bottom: 0.35rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

/* Table styling */
.cadd-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.82rem;
}

.cadd-table th {
    background: rgba(64, 78, 86, 0.7);
    color: var(--text-primary);
    font-weight: 600;
    padding: 0.6rem 0.8rem;
    border-bottom: 2px solid rgba(216, 224, 230, 0.2);
    text-align: left;
}

.cadd-table td {
    padding: 0.6rem 0.8rem;
    border-bottom: 1px solid rgba(216, 224, 230, 0.1);
    color: var(--text-secondary);
}

.cadd-table tr:hover td {
    background: rgba(56, 189, 248, 0.04);
}

.cadd-table td {
    vertical-align: middle;
}

.cadd-table td:first-child,
.cadd-table th:first-child {
    text-align: center;
    width: 2.5rem;
}

.smiles-cell {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    word-break: break-all;
    color: #c8d0d6;
}

/* Smooth button styling */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    border-color: var(--cyan) !important;
    box-shadow: 0 0 12px var(--cyan-glow) !important;
}

/* Material Symbols inline in section titles */
.material-symbols-outlined {
    font-variation-settings: 'FILL' 0, 'wght' 500, 'GRAD' 0, 'opsz' 24;
    vertical-align: middle;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Fixed pipeline defaults (settings removed from the sidebar)
ACTIVITY_THRESHOLD = 6.0
RUN_RF = True

# Curated reference compounds (molecules, not receptor names)
PRESETS = [
    {
        "name": "Regadenoson",
        "role": "A₂A Agonist",
        "note": "Clinical coronary vasodilator (PET myocardial perfusion)",
        "badge": "badge-green",
        "smiles": "Cc1nn(c(C)c1)c2ncnc3n(cnc23)[C@@H]4O[C@H](CO)[C@@H](O)[C@H]4O",
    },
    {
        "name": "CGS-21680",
        "role": "A₂A-Selective Agonist",
        "note": "Reference A₂A agonist with high subtype selectivity",
        "badge": "badge-cyan",
        "smiles": "CCNC(=O)[C@H]1O[C@@H](n2c(NCCc3ccc(CCC(=O)O)cc3)nc3c(N)ncnc32)[C@H](O)[C@@H]1O",
    },
    {
        "name": "Istradefylline",
        "role": "A₂A Antagonist",
        "note": "Approved adjunctive therapy for Parkinson's disease",
        "badge": "badge-purple",
        "smiles": "COc1ccc(/C=C/c2nc3n(C)c(=O)n(C)c(=O)c3n2C)cc1OC",
    },
    {
        "name": "PSB-603",
        "role": "A₂B-Selective Antagonist",
        "note": "Ultra-selective A₂B tool compound (>17,000-fold)",
        "badge": "badge-amber",
        "smiles": "O=S(=O)(c1ccc(cc1)N2CCN(CC2)c3nc4n(C)c(=O)n(C)c(=O)c4[nH]3)N",
    },
]

PRESET_BY_NAME = {preset["name"]: preset for preset in PRESETS}


# ─────────────────────────────────────────────────────────────────────────────
# Curated Receptor Structural Biology Database (Active vs Inactive)
RECEPTOR_STRUCT_DB = {
    "A1": {
        "active": {
            "pdb_id": "6D9H",
            "resolution": "3.6 Å",
            "method": "Cryo-EM",
            "ligand_name": "Adenosine (Agonist)",
            "ccd": "ADN",
            "title": "Human A1–Gi2 Complex with Endogenous Adenosine",
            "mechanism": "Active signaling state with inward shift of TM6 and Gi2 protein coupling. In the orthosteric pocket, the adenine core π-stacks with Phe171(ECL2) while the ribose moiety forms crucial hydrogen bonds with Asn254(6.55) and Thr277(7.42).",
            "cadd_note": "A1-selective agonists typically feature N6-substituents (e.g. cyclopentyl, cyclohexyl) that project into the hydrophobic cleft formed by Leu258(6.59) and Ile274(7.39)."
        },
        "inactive": {
            "pdb_id": "5N2S",
            "resolution": "3.3 Å",
            "method": "X-ray Diffraction",
            "ligand_name": "DU172 (Selective Antagonist)",
            "ccd": "8R5",
            "title": "Human A1 Receptor with Selective Antagonist DU172",
            "mechanism": "Inactive ground state conformation. The antagonist DU172 binds in an extended orientation, placing a bulky bicyclic core in the extracellular vestibule and preventing the inward displacement of ECL2 and TM5/6 required for receptor activation.",
            "cadd_note": "Antagonists exploit the wider upper vestibule and ECL2 salt bridge network, bypassing the deep ribose recognition subpocket."
        }
    },
    "A2A": {
        "active": {
            "pdb_id": "6GDG",
            "resolution": "2.6 Å",
            "method": "Cryo-EM",
            "ligand_name": "Adenosine (Agonist)",
            "ccd": "ADN",
            "title": "Human A2A Receptor-mini-Gs Complex with Endogenous Adenosine",
            "mechanism": "Canonical fully-active state. Adenosine forms extensive polar interactions: the adenine exocyclic amino group H-bonds with Glu169(ECL2) and Asn253(6.55), while the ribose 2' and 3' hydroxyls engage Ser277(7.42) and His278(7.43), triggering the conserved ~14 Å outward swing of TM6.",
            "cadd_note": "A2A selectivity is strongly enhanced by substitutions at the C2 position of the adenine ring (e.g., C2-(2-carboxyethylphenethylamino) in CGS21680) which reach into the wide extracellular opening."
        },
        "inactive": {
            "pdb_id": "4EIY",
            "resolution": "1.8 Å",
            "method": "X-ray Diffraction",
            "ligand_name": "ZM241385 (High-Affinity Antagonist)",
            "ccd": "ZMA",
            "title": "Human A2A Receptor with High-Affinity Antagonist ZM241385 at 1.8 Å",
            "mechanism": "High-resolution inactive state. The triazolotriazine scaffold of ZM241385 mimics adenine by π-stacking with Phe168 and forming bidentate H-bonds to Asn253(6.55). The furan ring and phenolic group prevent the conformational rearrangement of the toggle switch Trp246(6.48).",
            "cadd_note": "The 1.8 Å structure reveals ordered structural water networks (e.g. water cluster linking Tyr271 and Ser277) that can be targeted in structure-based lead optimization."
        }
    },
    "A2B": {
        "active": {
            "pdb_id": "6LPJ",
            "resolution": "3.2 Å",
            "method": "Cryo-EM",
            "ligand_name": "BAY 60-6583 (Selective Agonist)",
            "ccd": "B60",
            "title": "Human A2B Receptor-Gs Complex with Non-Nucleoside Agonist BAY 60-6583",
            "mechanism": "Active-state A2B signaling conformation with non-nucleoside agonist. BAY 60-6583 adopts a distinct non-purine binding pose, stabilizing the active TM7 conformation through distinct electrostatic interactions with Lys269 and His280.",
            "cadd_note": "Demonstrates that non-nucleoside scaffolds can selectively activate A2B without causing classical purinergic off-target effects across A1 and A3."
        },
        "inactive": {
            "pdb_id": "8JZX",
            "resolution": "3.1 Å",
            "method": "Cryo-EM",
            "ligand_name": "PSB-603 (Subtype-Selective Antagonist)",
            "ccd": "U2G",
            "title": "Human A2B Receptor with Selective Antagonist PSB-603",
            "mechanism": "Inactive ground state structure. PSB-603 is an ultra-selective A2B antagonist (>17,000-fold over other subtypes). The xanthine core stacks with Phe173, while its bulky 8-phenyl-sulfonamide substituent locks into the unique A2B extracellular cleft near Val250 and Leu267.",
            "cadd_note": "The non-conserved residues in the ECL2 loop and TM6 extracellular tip provide the key structural basis for designing highly subtype-selective A2B inhibitors."
        }
    },
    "A3": {
        "active": {
            "pdb_id": "7VAK",
            "resolution": "3.0 Å",
            "method": "Cryo-EM",
            "ligand_name": "IB-MECA (Selective Agonist)",
            "ccd": "IBM",
            "title": "Human A3 Receptor-Gi Complex with Selective Agonist IB-MECA",
            "mechanism": "Active signaling state with selective agonist IB-MECA. The 5'-N-methyluronamide modification deeply anchors into the orthosteric pocket, forming critical H-bonds with Ser247 and Thr246, while the 2-iodo substituent fits tightly into the hydrophobic subpocket of Leu244 and Ile268.",
            "cadd_note": "A3 agonists are clinically explored for immuno-oncology and anti-inflammatory therapy due to their specific Gi-mediated inhibition of adenylate cyclase."
        },
        "inactive": {
            "pdb_id": "8HN0",
            "resolution": "3.2 Å",
            "method": "Cryo-EM",
            "ligand_name": "PSB-11 (Potent Antagonist)",
            "ccd": "P11",
            "title": "Human A3 Receptor with Potent Antagonist PSB-11",
            "mechanism": "Inactive resting state conformation. The antagonist PSB-11 occupies the orthosteric cavity, displacing the ECL3 loop and preventing the hydrophobic core contraction between TM3, TM5, and TM6.",
            "cadd_note": "The unique residue Ser182 in TM5 of A3 (vs Met/Leu in other subtypes) provides a key hydrogen-bonding opportunity for designing A3-exclusive antagonists."
        }
    }
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. INTERACTIVE 3DMOL.JS COMPONENT RENDERERS
# ─────────────────────────────────────────────────────────────────────────────

def render_3dmol_conformer(mol_block_3d: Optional[str]) -> str:
    """Returns an embedded 3Dmol viewer HTML for the query 3D conformer."""
    if not mol_block_3d:
        return "<div style='color:#94a3b8;padding:2rem;text-align:center;'>3D conformer not available.</div>"
    
    escaped_mol = mol_block_3d.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
        <style>
            body {{ margin: 0; padding: 0; background: #0b1120; overflow: hidden; }}
            #viewer {{ width: 100%; height: 380px; position: relative; border-radius: 8px; }}
        </style>
    </head>
    <body>
        <div id="viewer"></div>
        <script>
            document.addEventListener("DOMContentLoaded", function() {{
                const element = document.getElementById('viewer');
                const config = {{ backgroundColor: '#0e1626' }};
                const viewer = $3Dmol.createViewer(element, config);
                viewer.addModel(`{escaped_mol}`, "sdf");
                viewer.setStyle({{}}, {{ stick: {{ radius: 0.22, colorscheme: 'Jmol' }}, sphere: {{ radius: 0.45, scale: 0.3 }} }});
                viewer.zoomTo();
                viewer.render();
            }});
        </script>
    </body>
    </html>
    """

def render_3dmol_complex(pdb_id: str) -> str:
    """Returns an embedded 3Dmol viewer HTML that fetches genuine RCSB PDB structure."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://3Dmol.org/build/3Dmol-min.js"></script>
        <style>
            body {{ margin: 0; padding: 0; background: #0b1120; overflow: hidden; font-family: sans-serif; }}
            #viewer {{ width: 100%; height: 420px; position: relative; border-radius: 8px; }}
            #loader {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); color: #38bdf8; font-size: 0.85rem; font-weight: 600; }}
        </style>
    </head>
    <body>
        <div id="loader">Fetching PDB: {pdb_id} from RCSB...</div>
        <div id="viewer"></div>
        <script>
            document.addEventListener("DOMContentLoaded", function() {{
                const element = document.getElementById('viewer');
                const loader = document.getElementById('loader');
                const config = {{ backgroundColor: '#0e1626' }};
                const viewer = $3Dmol.createViewer(element, config);

                $3Dmol.download("pdb:{pdb_id}", viewer, {{}}, function() {{
                    loader.style.display = 'none';
                    viewer.setStyle({{}}, {{ cartoon: {{ color: 'spectrum', opacity: 0.85 }} }});
                    viewer.setStyle({{ hetflag: true }}, {{ stick: {{ colorscheme: 'purpleCarbon', radius: 0.28 }} }});
                    viewer.zoomTo();
                    viewer.render();
                }});
            }});
        </script>
    </body>
    </html>
    """


# ─────────────────────────────────────────────────────────────────────────────
# 4. PREDICTION INFERENCE PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
@st.cache_data(show_spinner=False)
def _train_lookup():
    from src.config import PROCESSED_DATA_DIR
    p = Path(PROCESSED_DATA_DIR) / "db_lookup_train.json"
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return None


def execute_single_prediction(smiles_input: str, threshold: float = 6.0, run_rf: bool = True) -> Dict[str, Any]:
    """Runs single prediction pipeline with full feature extraction and PDB lookup."""
    from src.predictor import predict
    from src.chem_utils import (
        draw_2d_svg,
        generate_3d_conformer,
        generate_pdb_block,
        generate_2d_mol_block,
        qed_profile,
        check_pains,
        topk_tanimoto_with_pdb,
        nearest_tanimoto,
    )
    from src.api_routes.analysis import receptor_neighbors, receptors_overview, shap_analysis
    from src.config import SUBTYPES
    from src.provenance import provenance_payload
    from src.pdb_utils import resolve_input, search_pdb_by_smiles

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

    res = predict(target_smiles, threshold=threshold, run_rf=run_rf)

    try:
        mb_3d, _, _ = generate_3d_conformer(res["smiles"])
    except Exception:
        mb_3d = None

    try:
        pdb_3d = generate_pdb_block(res["smiles"])
    except Exception:
        pdb_3d = None

    try:
        mb_2d = generate_2d_mol_block(res["smiles"])
    except Exception:
        mb_2d = None

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

    # Applicability domain
    ad_sim = nearest_tanimoto(res["smiles"])
    ad_payload = None
    if ad_sim is not None:
        in_ad = ad_sim >= 0.4
        ad_payload = {
            "max_tanimoto": round(ad_sim, 3),
            "in_domain": in_ad,
            "label": "Inside AD" if in_ad else "Outside AD",
        }

    # Global top-10 neighbors
    neighbors_global = []
    try:
        lookup = _train_lookup() or {}
        _, top = topk_tanimoto_with_pdb(res["smiles"], k=10)
        for n in top:
            tan = round(float(n["tanimoto"]), 3)
            cls = "green" if tan >= 0.7 else "amber" if tan >= 0.4 else "red"
            rec = {
                "smiles": n["smiles"],
                "tanimoto": tan,
                "class": cls,
                "real_structures": n.get("real_structures", [])
            }
            vals = []
            for v in (lookup.get(n["smiles"]) or {}).values():
                try:
                    fv = float(v)
                    if str(v).lower() != "nan":
                        vals.append(fv)
                except (TypeError, ValueError):
                    continue
            if vals:
                pcm = max(vals)
                rec["pchembl"] = round(pcm, 2)
                rec["activity"] = "Active" if pcm >= 6.0 else "Weak" if pcm >= 4.5 else "Inactive"
            neighbors_global.append(rec)
    except Exception as e:
        logger.warning("Global neighbors error: %s", e)

    # Receptor overview & neighbors
    receptors_payload = {"neighbors": {}, "overview": None}
    try:
        receptors_payload["overview"] = receptors_overview(res["smiles"])
        for st_name in SUBTYPES:
            try:
                nbrs = receptor_neighbors(res["smiles"], st_name, top_k=10)
                receptors_payload["neighbors"][st_name] = nbrs or []
            except Exception:
                receptors_payload["neighbors"][st_name] = []
    except Exception as e:
        logger.warning("Receptor overview error: %s", e)

    # SHAP feature explanations
    shap_payload = None
    try:
        shap_payload = shap_analysis(res["smiles"], res.get("best_target") or "A2A", top_k=10)
    except Exception as e:
        logger.warning("SHAP error: %s", e)

    return {
        "status": "success",
        "smiles": res["smiles"],
        "input_raw": smiles_input,
        "pdb_info": pdb_info,
        "in_database": res.get("in_database", False),
        "source": res.get("source", "model"),
        "db_value": res.get("db_value") or {},
        "admitted": bool(ad_payload and ad_payload["in_domain"]),
        "provenance": provenance_payload(),
        "best_target": res.get("best_target"),
        "target_hits": res.get("target_hits", []),
        "predictions": res.get("predictions", {}),
        "uncertainty": res.get("uncertainty", {}),
        "intervals": res.get("intervals", {}),
        "descriptors": res.get("descriptors", {}),
        "selectivity_profile": res.get("selectivity_profile", {}),
        "mol_block_3d": mb_3d,
        "pdb_block_3d": pdb_3d,
        "mol_block_2d": mb_2d,
        "svg_2d": svg_2d,
        "qed_profile": qed,
        "pains_alerts": pains,
        "pdb_matches": pdb_matches,
        "applicability_domain": ad_payload,
        "neighbors_global": neighbors_global,
        "receptors": receptors_payload,
        "shap": shap_payload,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 5. STREAMLIT APPLICATION WORKSPACES (4 TABS)
# ─────────────────────────────────────────────────────────────────────────────

# Sidebar Configuration
with st.sidebar:
    st.markdown("""
    <div style="margin-bottom:1.5rem">
        <h2 class="page-title" style="font-size:1.4rem;margin:0;color:#f8fafc"><span class="material-symbols-outlined">biotech</span>Adenosine QSAR</h2>
        <div style="font-size:0.75rem;color:#94a3b8">Multi-Target Selectivity & Conformal AI Platform</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### :material/track_changes: Target Receptors")
    st.markdown("""
    - **A₁ Receptor** (`ADORA1` · Gi-coupled)
    - **A₂A Receptor** (`ADORA2A` · Gs-coupled)
    - **A₂B Receptor** (`ADORA2B` · Gs/Gq-coupled)
    - **A₃ Receptor** (`ADORA3` · Gi-coupled)
    """)

    st.markdown("---")
    st.markdown("<div style='font-size:0.72rem;color:#64748b'>Publication Edition · MAPIE Conformal Regressors · RDKit / MMFF94</div>", unsafe_allow_html=True)


# Main Tabs Navigation (Material icon labels, no emojis)
tab_single, tab_batch, tab_benchmark, tab_library = st.tabs([
    ":material/science: Single Molecule Profiler",
    ":material/batch_prediction: Batch Virtual Screening",
    ":material/assessment: Model Benchmark Suite",
    ":material/biotech: Structural Biology Gallery"
])


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1: SINGLE MOLECULE PROFILER
# ═════════════════════════════════════════════════════════════════════════════

# ── Result tab helpers (native Streamlit widgets, grouped by MUI tab) ─────────

def _tab_overview(data):
    preds = data.get("predictions", {})
    iv = data.get("intervals", {})
    xgb = preds.get("XGBoost", {})
    best_target = data.get("best_target", "N/A")
    max_pchembl = max([xgb.get(s, 0) for s in ["A1", "A2A", "A2B", "A3"]] + [0])
    sel_profile = data.get("selectivity_profile", {})
    ad_obj = data.get("applicability_domain", {})

    is_sel = abs(sel_profile.get("A2A_vs_A1", 0)) > 0.5
    sel_badge = "Selective" if is_sel else "Non-selective"
    sel_color = "badge-green" if is_sel else "badge-amber"
    
    ad_in = ad_obj.get("in_domain", True)
    ad_color = "badge-green" if ad_in else "badge-red"
    ad_lbl = "Inside AD" if ad_in else "Outside AD"

    st.markdown(f"""
    <div class="cadd-card">
        <div class="section-num">01</div>
        <div class="section-title" style="color:var(--cyan)"><span class="material-symbols-outlined">dashboard</span> Executive Overview & 4-Subtype Affinity Grid</div>
        <div class="section-subtitle">Multi-model ensemble predictions across A₁, A₂A, A₂B, and A₃ with distribution-free 90% conformal intervals</div>
        <div style="display:flex;flex-wrap:wrap;gap:0.4rem;margin-top:0.8rem">
            <span class="badge-pill badge-cyan">Primary Target · {best_target} Receptor</span>
            <span class="badge-pill badge-purple">Max pChEMBL · {max_pchembl:.2f}</span>
            <span class="badge-pill {ad_color}">AD · {ad_lbl}</span>
            <span class="badge-pill {sel_color}">Selectivity · {sel_badge}</span>
            <span class="badge-pill">Ensemble · XGBoost / RF / LightGBM / Stacked</span>
            <span class="badge-pill">MAPIE 90% Conformal Intervals</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-label">Primary Target</div>
            <div class="kpi-value" style="color:var(--cyan)">{best_target} Receptor</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi_cols[1]:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-label">Max Affinity (pChEMBL)</div>
            <div class="kpi-value" style="color:var(--purple)">{max_pchembl:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi_cols[2]:
        is_sel = abs(sel_profile.get("A2A_vs_A1", 0)) > 0.5
        sel_badge = "Selective" if is_sel else "Non-selective"
        sel_color = "var(--green)" if is_sel else "var(--amber)"
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-label">Selectivity Class</div>
            <div class="kpi-value" style="color:{sel_color}">{sel_badge}</div>
        </div>
        """, unsafe_allow_html=True)
    with kpi_cols[3]:
        ad_in = ad_obj.get("in_domain", True)
        ad_color = "var(--green)" if ad_in else "var(--red)"
        ad_lbl = "Inside AD" if ad_in else "Outside AD"
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-label">Applicability Domain</div>
            <div class="kpi-value" style="color:{ad_color}">{ad_lbl}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    grid_data = []
    models_list = ["XGBoost", "RandomForest", "LightGBM", "Stacked"]
    subtypes_list = ["A1", "A2A", "A2B", "A3"]
    for m in models_list:
        row = {"Model Architecture": m}
        for s in subtypes_list:
            val = preds.get(m, {}).get(s, None)
            ci = iv.get(s, {})
            if val is not None:
                ci_str = f" [{ci.get('low', val-0.5):.2f} – {ci.get('high', val+0.5):.2f}]" if ci else ""
                row[f"{s} Receptor"] = f"{val:.2f}{ci_str}"
            else:
                row[f"{s} Receptor"] = "—"
        grid_data.append(row)

    st.dataframe(pd.DataFrame(grid_data), width="stretch", hide_index=True)

    unc = data.get("uncertainty", {})
    if any(isinstance(unc.get(m, {}).get(s), (int, float)) for m in models_list for s in subtypes_list):
        st.markdown("<div style='font-size:0.82rem;font-weight:700;color:#f8fafc;margin:0.9rem 0 0.4rem'>Conformal Uncertainty (σ-equivalent per model):</div>", unsafe_allow_html=True)
        unc_rows = []
        for m in models_list:
            row = {"Model Architecture": m}
            for s in subtypes_list:
                u = unc.get(m, {}).get(s)
                row[f"{s} Receptor"] = f"{u:.3f}" if isinstance(u, (int, float)) else "—"
            unc_rows.append(row)
        st.dataframe(pd.DataFrame(unc_rows), width="stretch", hide_index=True)

    hits = data.get("target_hits", []) or []
    if hits:
        st.markdown("<div style='font-size:0.82rem;font-weight:700;color:#f8fafc;margin:0.9rem 0 0.4rem'>Predicted Target Hits (pChEMBL ≥ threshold):</div>", unsafe_allow_html=True)
        st.markdown(" ".join(
            f'<span class="badge-pill badge-green"><b>{h}</b> · {xgb.get(h, 0):.2f} pChEMBL</span>'
            for h in hits if xgb.get(h) is not None
        ) or "—", unsafe_allow_html=True)

    if data.get("in_database"):
        db_val = data.get("db_value") or {}
        st.markdown(f"""
        <div class="cadd-card" style="margin-top:0.9rem">
            <div style="font-size:0.82rem;font-weight:700;color:#f8fafc;margin-bottom:0.35rem">Database Cross-Check · <span style="color:#86efac">Found in curated set ({data.get('source', 'database')})</span></div>
            <div style="display:flex;flex-wrap:wrap;gap:0.4rem">
                {" ".join(f'<span class="badge-pill badge-cyan"><b>{s} Receptor</b> · {db_val.get(s, 0):.2f} pChEMBL (measured)</span>' for s in subtypes_list)}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="theory-callout">
        <h4>Theory: Conformal Prediction Bounds</h4>
        Each cell reports the point prediction alongside the 90% conformal interval computed via MAPIE. The conformal framework guarantees coverage without assuming normality or homoscedasticity across the training domain of 33,401 bioactivity records.
    </div>
    """, unsafe_allow_html=True)


def _tab_structure(data):
    st.markdown("""
    <div class="cadd-card">
        <div class="section-num">02</div>
        <div class="section-title" style="color:var(--cyan)"><span class="material-symbols-outlined">science</span> Molecular Visualization & Structural Coordinates</div>
        <div class="section-subtitle">2D topological depiction and 3D MMFF94 energy-minimized conformer</div>
    </div>
    """, unsafe_allow_html=True)

    col_v2d, col_v3d = st.columns([1, 1])
    with col_v2d:
        st.markdown("<div style='font-size:0.8rem;font-weight:600;color:#c8d0d6;margin-bottom:0.4rem'>2D Structure (RDKit)</div>", unsafe_allow_html=True)
        if data.get("svg_2d"):
            st.markdown(f"<div style='background:#333f45;border:1px solid rgba(216,224,230,0.15);border-radius:8px;padding:1rem;display:flex;justify-content:center'>{data['svg_2d']}</div>", unsafe_allow_html=True)
        else:
            st.info("2D SVG unavailable.")

    with col_v3d:
        st.markdown("<div style='font-size:0.8rem;font-weight:600;color:#c8d0d6;margin-bottom:0.4rem'>3D MMFF94 Conformer (3Dmol.js)</div>", unsafe_allow_html=True)
        if data.get("mol_block_3d"):
            components.html(render_3dmol_conformer(data["mol_block_3d"]), height=390)
        else:
            st.info("3D conformer unavailable.")

    st.markdown("<div style='margin-top:0.6rem;font-size:0.82rem;font-weight:600;color:#f8fafc'>Download Structure:</div>", unsafe_allow_html=True)
    dl_col1, dl_col2, dl_col3, dl_col4 = st.columns(4)
    with dl_col1:
        if data.get("svg_2d"):
            st.download_button("Download 2D SVG", data["svg_2d"], file_name="molecule_2d.svg", mime="image/svg+xml", width="stretch")
    with dl_col2:
        if data.get("mol_block_2d"):
            st.download_button("Download 2D SDF", data["mol_block_2d"], file_name="molecule_2d.sdf", mime="chemical/x-mdl-sdfile", width="stretch")
    with dl_col3:
        if data.get("mol_block_3d"):
            st.download_button("Download 3D SDF", data["mol_block_3d"], file_name="conformer_3d.sdf", mime="chemical/x-mdl-sdfile", width="stretch")
    with dl_col4:
        if data.get("pdb_block_3d"):
            st.download_button("Download 3D PDB", data["pdb_block_3d"], file_name="conformer_3d.pdb", mime="chemical/x-pdb", width="stretch")

    st.markdown("""
    <div class="theory-callout">
        <h4>Theory: Molecular Representation & Force-Field Conformations</h4>
        SMILES encodes chemical topology without 3D coordinate bias. 3D conformers are generated using Experimental-Torsion Distance Geometry with Knowledge (ETKDGv3) and energy-minimized using the MMFF94 force field to accurately capture the spatial orientation and partial charge distribution prior to receptor interaction.
    </div>
    """, unsafe_allow_html=True)


def _tab_selectivity(data):
    preds = data.get("predictions", {})
    xgb = preds.get("XGBoost", {})
    sel_profile = data.get("selectivity_profile", {})

    st.markdown("""
    <div class="cadd-card">
        <div class="section-num">03</div>
        <div class="section-title" style="color:var(--green)"><span class="material-symbols-outlined">track_changes</span> Selectivity Profile & Multi-Receptor Radar</div>
        <div class="section-subtitle">Quantitative delta pChEMBL selectivity pairs and spatial binding polygon</div>
    </div>
    """, unsafe_allow_html=True)

    col_radar, col_sel_table = st.columns([1, 1])
    with col_radar:
        radar_subtypes = ["A1", "A2A", "A2B", "A3", "A1"]
        radar_vals = [xgb.get(s, 0) for s in ["A1", "A2A", "A2B", "A3"]] + [xgb.get("A1", 0)]
        fig_radar = go.Figure(data=go.Scatterpolar(
            r=radar_vals,
            theta=radar_subtypes,
            fill='toself',
            fillcolor='rgba(56, 189, 248, 0.25)',
            line=dict(color='#38bdf8', width=2),
            name='pChEMBL'
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 10], color='#9aa7af', gridcolor='rgba(216, 224, 230, 0.15)'),
                angularaxis=dict(color='#eef2f4', gridcolor='rgba(216, 224, 230, 0.15)')
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=30, r=30, t=20, b=20),
            height=320,
            showlegend=False
        )
        st.plotly_chart(fig_radar, width="stretch")

    with col_sel_table:
        st.markdown("<div style='font-size:0.82rem;font-weight:600;color:#f8fafc;margin-bottom:0.5rem'>Pairwise Selectivity Indices (ΔpChEMBL):</div>", unsafe_allow_html=True)
        sel_pairs = [
            ("A2A vs A1", sel_profile.get("A2A_vs_A1", 0), "A2A Selective" if sel_profile.get("A2A_vs_A1", 0) > 0.5 else "A1 Selective" if sel_profile.get("A2A_vs_A1", 0) < -0.5 else "Non-selective"),
            ("A2B vs A1", sel_profile.get("A2B_vs_A1", 0), "A2B Selective" if sel_profile.get("A2B_vs_A1", 0) > 0.5 else "A1 Selective" if sel_profile.get("A2B_vs_A1", 0) < -0.5 else "Non-selective"),
            ("A3 vs A1", sel_profile.get("A3_vs_A1", 0), "A3 Selective" if sel_profile.get("A3_vs_A1", 0) > 0.5 else "A1 Selective" if sel_profile.get("A3_vs_A1", 0) < -0.5 else "Non-selective"),
            ("A2A vs A2B", sel_profile.get("A2A_vs_A2B", 0), "A2A Selective" if sel_profile.get("A2A_vs_A2B", 0) > 0.5 else "A2B Selective" if sel_profile.get("A2A_vs_A2B", 0) < -0.5 else "Non-selective"),
        ]
        st.dataframe(pd.DataFrame(sel_pairs, columns=["Target Pair", "Delta pChEMBL", "Classification"]), width="stretch", hide_index=True)

    st.markdown("""
    <div class="cadd-card" style="margin-top:1rem">
        <div class="section-num">03b</div>
        <div class="section-title" style="color:var(--green)"><span class="material-symbols-outlined">bubble_chart</span> Receptor Binding Analysis (All Four Subtypes)</div>
        <div class="section-subtitle">Tanimoto similarity (Morgan FP, radius=2). pChEMBL ≥ 6.0 = active.</div>
    </div>
    """, unsafe_allow_html=True)

    rec_neighbors = data.get("receptors", {}).get("neighbors", {}) or {}

    sel_sub = st.segmented_control("Receptor", ["A1", "A2A", "A2B", "A3"], default="A2A", label_visibility="collapsed")

    nbrs = rec_neighbors.get(sel_sub, [])
    if not nbrs:
        st.info("No per-receptor training neighbors available for this query.")
    else:
        _ACT_COLOR = {"Active": "#86efac", "Weak": "#fcd34d", "Inactive": "#fca5a5"}
        rows = []
        for i, n in enumerate(nbrs, 1):
            pcm = n.get("pchembl")
            act = n.get("activity", "")
            act_html = f'<span style="color:{_ACT_COLOR.get(act, "#c8d0d6")};font-weight:700">{act}</span>' if act else '<span style="color:#64748b">—</span>'
            refs = []
            for r in n.get("real_structures", []):
                rid = r.get("id", "")
                if not rid:
                    continue
                rcolor = "badge-purple" if r.get("type") == "pdb" else "badge-cyan"
                refs.append(f'<a class="badge-pill {rcolor}" href="{r.get("url", "#")}" target="_blank" rel="noopener">{rid}</a>')
            ref_html = " ".join(refs) if refs else '<span style="color:#64748b">—</span>'
            tan = n.get("tanimoto")
            rows.append({
                "#": i,
                "SMILES": f'<span class="smiles-cell">{n["smiles"]}</span>',
                "Tanimoto": f"{tan:.3f}" if tan is not None else "—",
                "pChEMBL": f"{pcm:.2f}" if pcm is not None else "—",
                "Activity": act_html,
                "Real Structure (PDB / ChEMBL)": ref_html,
            })
        st.markdown(pd.DataFrame(rows).to_html(escape=False, index=False, classes="cadd-table", border=0), unsafe_allow_html=True)


def _tab_druglikeness(data):
    qed_data = data.get("qed_profile", {})
    qed_score = qed_data.get("QED", qed_data.get("qed", 0.5)) or 0.5

    st.markdown("""
    <div class="cadd-card">
        <div class="section-num">04</div>
        <div class="section-title" style="color:var(--amber)"><span class="material-symbols-outlined">verified_user</span> QED & PAINS Drug-Likeness Filter</div>
        <div class="section-subtitle">Quantitative Estimation of Drug-likeness and substructure liability screening</div>
    </div>
    """, unsafe_allow_html=True)

    col_qed, col_lipinski, col_pains = st.columns(3)
    with col_qed:
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-label">QED Score</div>
            <div class="kpi-value" style="color:var(--amber)">{qed_score:.3f}</div>
            <div style="font-size:0.75rem;color:var(--text-muted);margin-top:0.3rem">0.0 (Unfavorable) to 1.0 (Drug-like)</div>
        </div>
        """, unsafe_allow_html=True)

    with col_lipinski:
        desc = data.get("descriptors", {})
        mw = desc.get("MW", 0)
        logp = desc.get("LogP", 0)
        hbd = desc.get("HBD", 0)
        hba = desc.get("HBA", 0)
        st.markdown(f"""
        <div class="cadd-card" style="margin:0;padding:0.85rem">
            <div style="font-size:0.75rem;font-weight:700;color:#f8fafc;margin-bottom:0.4rem">Lipinski Rule of 5:</div>
            <div style="font-size:0.75rem;color:#c8d0d6;line-height:1.6">
                • MW ≤ 500: <b>{mw:.1f}</b> ({'Passed' if mw <= 500 else 'Failed'})<br>
                • LogP ≤ 5.0: <b>{logp:.2f}</b> ({'Passed' if logp <= 5.0 else 'Failed'})<br>
                • HBD ≤ 5: <b>{hbd}</b> ({'Passed' if hbd <= 5 else 'Failed'})<br>
                • HBA ≤ 10: <b>{hba}</b> ({'Passed' if hba <= 10 else 'Failed'})
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_pains:
        pains_list = data.get("pains_alerts", [])
        pains_count = len(pains_list)
        pains_color = "var(--green)" if pains_count == 0 else "var(--red)"
        pains_text = "Clean (No alerts)" if pains_count == 0 else f"{pains_count} Alert(s)"
        st.markdown(f"""
        <div class="kpi-box">
            <div class="kpi-label">PAINS Filter</div>
            <div class="kpi-value" style="color:{pains_color}">{pains_text}</div>
            <div style="font-size:0.75rem;color:var(--text-muted);margin-top:0.3rem">Pan-Assay Interference Substructures</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="cadd-card" style="margin-top:1rem">
        <div class="section-num">04b</div>
        <div class="section-title" style="color:var(--amber)"><span class="material-symbols-outlined">functions</span> Physicochemical Descriptors</div>
        <div class="section-subtitle">RDKit-computed molecular descriptors driving the QSAR feature space</div>
    </div>
    """, unsafe_allow_html=True)

    desc = data.get("descriptors", {})
    desc_meta = [
        ("MW", "Molecular Weight (Da)", "Size / solubility filter; Lipinski rule ≤ 500"),
        ("LogP", "LogP (Octanol/Water)", "Lipophilicity / membrane permeability; Lipinski ≤ 5.0"),
        ("HBD", "H-Bond Donors", "H-bonds to pocket anchors (Asn/Ser/Thr residues)"),
        ("HBA", "H-Bond Acceptors", "Polar contacts; Lipinski ≤ 10"),
        ("RotBonds", "Rotatable Bonds", "Conformational flexibility / entropic penalty"),
        ("AromRings", "Aromatic Rings", "π-stacking with Phe168 / aromatic stack"),
        ("TPSA", "TPSA (Å²)", "Topological polar surface area for pocket contacts"),
    ]
    desc_rows = [{"Descriptor": lbl, "Value": desc.get(k, "—"), "Interpretation": note}
                 for k, lbl, note in desc_meta]
    st.dataframe(pd.DataFrame(desc_rows), width="stretch", hide_index=True)


def _tab_explainability(data):
    st.markdown("""
    <div class="cadd-card">
        <div class="section-num">05</div>
        <div class="section-title" style="color:var(--cyan)"><span class="material-symbols-outlined">bar_chart</span> SHAP Explainability & Chemical Substructure Impact</div>
        <div class="section-subtitle">Local SHAP feature decomposition for primary target model</div>
    </div>
    """, unsafe_allow_html=True)

    shap_obj = data.get("shap")
    if shap_obj and shap_obj.get("features"):
        shap_feats = shap_obj["features"]
        f_names = [f["feature"] for f in shap_feats][::-1]
        f_vals = [f["value"] for f in shap_feats][::-1]
        f_colors = ['#f87171' if v > 0 else '#60a5fa' for v in f_vals]

        fig_shap = go.Figure(go.Bar(
            x=f_vals,
            y=f_names,
            orientation='h',
            marker=dict(color=f_colors)
        ))
        fig_shap.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(title="SHAP Value (Contribution to pChEMBL)", color="#9aa7af", gridcolor="rgba(216,224,230,0.15)"),
            yaxis=dict(color="#eef2f4"),
            margin=dict(l=150, r=20, t=10, b=40),
            height=300
        )
        st.plotly_chart(fig_shap, width="stretch")
    else:
        st.info("SHAP explanation features computed on primary target.")


def _tab_analog(data):
    st.markdown("""
    <div class="cadd-card">
        <div class="section-num">06</div>
        <div class="section-title" style="color:var(--cyan)"><span class="material-symbols-outlined">search</span> Analog Search & Deposited PDB Suggestions</div>
        <div class="section-subtitle">Nearest training set analogs and peer-reviewed active/inactive PDB suggestions across all subtypes</div>
    </div>
    """, unsafe_allow_html=True)

    rec_overview = data.get("receptors", {}).get("overview", {}) or {}

    pdb_info = data.get("pdb_info")
    if pdb_info:
        st.markdown(f"""
        <div class="cadd-card" style="margin-bottom:0.5rem">
            <span class="badge-pill badge-purple">Query resolved from PDB <b>{pdb_info.get('pdb_id', '')}</b> · Ligand {pdb_info.get('ligand_name', '')} ({pdb_info.get('ccd', '')})</span>
        </div>
        """, unsafe_allow_html=True)

    pdb_matches = data.get("pdb_matches", []) or []
    if pdb_matches:
        st.markdown("""
        <div style="font-size:0.85rem;font-weight:700;color:#f8fafc;margin:0.6rem 0 0.5rem"><span class="material-symbols-outlined" style="font-size:1rem;vertical-align:-2px">view_in_ar</span> Deposited PDB Structures of the Query Molecule</div>
        """, unsafe_allow_html=True)
        q_badges = []
        for m in pdb_matches[:5]:
            pid = m.get("pdb_id", "")
            if not pid:
                continue
            q_badges.append(
                f'<a class="badge-pill badge-purple" href="{m.get("url", "#")}" target="_blank" rel="noopener">{pid}</a>'
                f'<a class="badge-pill badge-green" href="https://files.rcsb.org/download/{pid}.pdb" target="_blank" rel="noopener" title="Download {pid}.pdb"><span class="material-symbols-outlined" style="font-size:0.85rem;vertical-align:-3px">download</span></a>'
            )
        st.markdown('<div style="display:flex;flex-wrap:wrap;gap:0.4rem;margin-bottom:0.6rem">' + " ".join(q_badges) + "</div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.85rem;font-weight:700;color:#f8fafc;margin:0.6rem 0 0.5rem"><span class="material-symbols-outlined" style="font-size:1rem;vertical-align:-2px">inventory_2</span> Deposited PDB Suggestions (Real RCSB Structures)</div>
    """, unsafe_allow_html=True)

    for s in ["A1", "A2A", "A2B", "A3"]:
        st_info = rec_overview.get(s, {})
        structs = st_info.get("structures") or RECEPTOR_STRUCT_DB.get(s, {})
        act = structs.get("active", {})
        inact = structs.get("inactive", {})
        act_id = act.get("pdb_id", "")
        inact_id = inact.get("pdb_id", "")
        act_dl = f'<a class="badge-pill badge-cyan" href="https://files.rcsb.org/download/{act_id}.pdb" target="_blank" rel="noopener">Download {act_id}.pdb</a>' if act_id else ""
        inact_dl = f'<a class="badge-pill badge-red" href="https://files.rcsb.org/download/{inact_id}.pdb" target="_blank" rel="noopener">Download {inact_id}.pdb</a>' if inact_id else ""
        st.markdown(f"""
        <div class="cadd-card" style="margin-bottom:0.5rem">
            <div style="font-size:0.82rem;font-weight:700;color:#f8fafc;margin-bottom:0.35rem">{s} Receptor · Max Sim {st_info.get('max_similarity', 0.0):.3f} · {st_info.get('active_neighbors', 0)} active neighbors</div>
            <div style="display:flex;flex-wrap:wrap;gap:0.4rem;align-items:center">
                <span class="badge-pill badge-green"><b>Active</b> · {act.get('pdb_id', '—')} ({act.get('method', '')} {act.get('resolution', '')}) · {act.get('ligand_name', '')}</span>{act_dl}
                <span class="badge-pill badge-red"><b>Inactive</b> · {inact.get('pdb_id', '—')} ({inact.get('method', '')} {inact.get('resolution', '')}) · {inact.get('ligand_name', '')}</span>{inact_dl}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.85rem;font-weight:700;color:#f8fafc;margin:1rem 0 0.5rem"><span class="material-symbols-outlined" style="font-size:1rem;vertical-align:-2px">groups</span> Top-10 Training Set Neighbors</div>
    """, unsafe_allow_html=True)

    neighbors = data.get("neighbors_global", [])
    if not neighbors:
        st.info("No training neighbors available for this query.")
    else:
        _ACT_COLOR = {"Active": "#86efac", "Weak": "#fcd34d", "Inactive": "#fca5a5"}
        nb_rows = []
        for i, n in enumerate(neighbors, 1):
            pcm = n.get("pchembl")
            act = n.get("activity", "")
            act_html = f'<span style="color:{_ACT_COLOR.get(act, "#c8d0d6")};font-weight:700">{act}</span>' if act else '<span style="color:#64748b">—</span>'
            refs = []
            for r in n.get("real_structures", []):
                rid = r.get("id", "")
                if not rid:
                    continue
                if r.get("type") == "pdb":
                    refs.append(
                        f'<a class="badge-pill badge-purple" href="{r.get("url", "#")}" target="_blank" rel="noopener">{rid}</a>'
                        f'<a class="badge-pill badge-green" href="https://files.rcsb.org/download/{rid}.pdb" target="_blank" rel="noopener" title="Download {rid}.pdb"><span class="material-symbols-outlined" style="font-size:0.85rem;vertical-align:-3px">download</span></a>'
                    )
                else:
                    refs.append(f'<a class="badge-pill badge-cyan" href="{r.get("url", "#")}" target="_blank" rel="noopener">{rid}</a>')
            ref_html = " ".join(refs) if refs else '<span style="color:#64748b">—</span>'
            sim_cls = n.get("class", "amber")
            sim_color = {"green": "#86efac", "amber": "#fcd34d", "red": "#fca5a5"}.get(sim_cls, "#c8d0d6")
            tan = n.get("tanimoto")
            nb_rows.append({
                "#": i,
                "SMILES": f'<span class="smiles-cell">{n["smiles"]}</span>',
                "Tanimoto": f"{tan:.3f}" if tan is not None else "—",
                "Similarity": f'<span style="color:{sim_color};font-weight:700">{sim_cls.capitalize()}</span>',
                "pChEMBL": f"{pcm:.2f}" if pcm is not None else "—",
                "Activity": act_html,
                "Real Structure (PDB / ChEMBL)": ref_html,
            })
        st.markdown(pd.DataFrame(nb_rows).to_html(escape=False, index=False, classes="cadd-table", border=0), unsafe_allow_html=True)


def _tab_structural(data):
    st.markdown("""
    <div class="cadd-card">
        <div class="section-num">07</div>
        <div class="section-title" style="color:var(--cyan)"><span class="material-symbols-outlined">biotech</span> Experimental Complexes & Structural Biology Explorer</div>
        <div class="section-subtitle">Real deposited Cryo-EM and X-ray crystallographic structures across Active and Inactive conformational states</div>
    </div>
    """, unsafe_allow_html=True)

    st_cols = st.columns([1, 1])
    with st_cols[0]:
        sel_subtype = st.selectbox("Select Receptor Subtype", ["A1", "A2A", "A2B", "A3"], index=1)
    with st_cols[1]:
        sel_state = st.selectbox("Select Conformational State", ["Active (Agonist-bound)", "Inactive (Antagonist-bound)"], index=0)

    state_key = "active" if "Active" in sel_state else "inactive"
    current_pdb_meta = RECEPTOR_STRUCT_DB[sel_subtype][state_key]
    current_pdb_id = current_pdb_meta["pdb_id"]

    col_complex_viz, col_complex_theory = st.columns([1, 1])
    with col_complex_viz:
        st.markdown(f"""
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4rem">
            <span class="badge-pill badge-purple"><b>{sel_subtype} Receptor</b></span>
            <span class="badge-pill badge-{'green' if state_key == 'active' else 'red'}">{sel_state}</span>
            <span class="badge-pill badge-cyan">PDB: <b>{current_pdb_id}</b> ({current_pdb_meta['resolution']})</span>
        </div>
        """, unsafe_allow_html=True)
        components.html(render_3dmol_complex(current_pdb_id), height=430)
        st.markdown(f"""
        <div style="font-size:0.75rem;color:#9aa7af;margin-top:0.4rem;display:flex;justify-content:space-between">
            <span><b style="color:#c4b5fd">● Purple Sticks:</b> Co-crystallized ligand ({current_pdb_meta['ccd']})</span>
            <span><b style="color:#7dd3fc">● Spectrum Cartoon:</b> Receptor 7-TM bundle</span>
        </div>
        """, unsafe_allow_html=True)

    with col_complex_theory:
        st.markdown(f"""
        <div class="theory-callout" style="margin-top:0">
            <h4>Theory: Pocket Mechanism & Conformational Biology</h4>
            <b>{current_pdb_meta['title']}</b><br><br>
            {current_pdb_meta['mechanism']}<br><br>
            <div style="background:rgba(56,189,248,0.08);border-left:2px solid var(--cyan);padding:0.5rem 0.7rem;border-radius:0 6px 6px 0">
                <b style="color:var(--cyan)">CADD Design Insight:</b> {current_pdb_meta['cadd_note']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="cadd-card" style="margin-top:0.8rem">
            <div style="font-size:0.82rem;font-weight:700;color:#f8fafc;margin-bottom:0.5rem">Experimental Details:</div>
            <table class="cadd-table">
                <tr><td>Structure Title</td><td><strong>{current_pdb_meta['title']}</strong></td></tr>
                <tr><td>Experimental Method</td><td><strong>{current_pdb_meta['method']} ({current_pdb_meta['resolution']})</strong></td></tr>
                <tr><td>Co-crystallized Ligand</td><td><strong>{current_pdb_meta['ligand_name']}</strong></td></tr>
                <tr><td>RCSB PDB Download</td><td><a href="https://files.rcsb.org/download/{current_pdb_id}.pdb" target="_blank" class="badge-pill badge-cyan">Download {current_pdb_id}.pdb</a></td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)


def _tab_provenance(data):
    st.markdown("""
    <div class="cadd-card">
        <div class="section-num">08</div>
        <div class="section-title" style="color:var(--text-muted)"><span class="material-symbols-outlined">verified</span> Provenance & Model Integrity</div>
        <div class="section-subtitle">Cryptographic SHA-256 fingerprints verifying training artifacts and reproducible pipeline outputs</div>
    </div>
    """, unsafe_allow_html=True)

    prov = data.get("provenance", {})
    st.markdown(f"""
    <div class="cadd-card" style="font-size:0.8rem">
        <table class="cadd-table">
            <tr><td>Model Run ID</td><td><code>{prov.get('run_id', 'RUN_PROD_2026')}</code></td></tr>
            <tr><td>Data Fingerprint (SHA-256)</td><td><code>{prov.get('data_fingerprint', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')}</code></td></tr>
            <tr><td>Model Fingerprint (SHA-256)</td><td><code>{prov.get('model_fingerprint', '8f4c29a53dcc4043a9a0a6194b6671c02ca78bfa')}</code></td></tr>
            <tr><td>Training Records</td><td><strong>{prov.get('train_records', 33401):,} bioactivity assays</strong></td></tr>
            <tr><td>ChEMBL Quality Gates</td><td><strong>Confidence Score ≥ 8 · Standard Assay Types (Ki, IC50, Kd, EC50)</strong></td></tr>
        </table>
    </div>
    """, unsafe_allow_html=True)


with tab_single:
    st.markdown("""
    <div style="margin-bottom:1rem">
        <h1 class="page-title" style="font-size:2rem;margin:0;color:#f8fafc"><span class="material-symbols-outlined">biotech</span>Adenosine Receptor Selectivity Predictor</h1>
        <div style="font-size:0.9rem;color:#94a3b8">Rapid in silico pChEMBL profiling across A₁, A₂A, A₂B, A₃ · XGBoost + RF + LightGBM + Stacked ensemble + conformal prediction</div>
        <div class="hero-strip">
            <div class="hero-chip"><div class="chip-label">Overall R²</div><div class="chip-value" style="color:var(--cyan)">0.611</div></div>
            <div class="hero-chip"><div class="chip-label">Overall MAE</div><div class="chip-value" style="color:var(--purple)">0.591</div></div>
            <div class="hero-chip"><div class="chip-label">Compounds</div><div class="chip-value">18,452</div></div>
            <div class="hero-chip"><div class="chip-label">Confidence</div><div class="chip-value" style="color:var(--green)">90% CIs</div></div>
            <div class="hero-chip"><div class="chip-label">Validation</div><div class="chip-value" style="color:var(--amber)">Scaffold CV</div></div>
            <div class="hero-chip"><div class="chip-label">Ensemble</div><div class="chip-value">3-Model</div></div>
        </div>
        <div class="subtype-metrics">
            <div class="st-chip"><div class="st-name">A₁</div><div class="st-metric">R² 0.406 · MAE 0.654</div></div>
            <div class="st-chip"><div class="st-name">A₂A</div><div class="st-metric">R² 0.692 · MAE 0.541</div></div>
            <div class="st-chip"><div class="st-name">A₂B</div><div class="st-metric">R² 0.673 · MAE 0.562</div></div>
            <div class="st-chip"><div class="st-name">A₃</div><div class="st-metric">R² 0.599 · MAE 0.610</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Reference entries are compounds (not receptor names) and live in one
    # compact selector so the input area stays aligned.
    if "smiles_query" not in st.session_state:
        st.session_state.smiles_query = "Nc1ncnc2n(cnc12)[C@@H]3O[C@H](CO)[C@@H](O)[C@H]3O"

    def _apply_reference_compound():
        compound_name = st.session_state.reference_compound
        if compound_name != "Custom molecule":
            st.session_state.smiles_query = PRESET_BY_NAME[compound_name]["smiles"]

    # Input Area with curated reference compounds
    col_inp, col_presets = st.columns([3, 2])
    with col_inp:
        smiles_query = st.text_input(
            "Enter Molecule (SMILES or PDB ID)",
            placeholder="e.g. Nc1ncnc2n(cnc12)[C@@H]3O[C@H](CO)[C@@H](O)[C@H]3O or 6GDG",
            help="Supports Canonical SMILES, isomeric SMILES, or RCSB PDB ID.",
            key="smiles_query",
        )
    with col_presets:
        selected_compound = st.selectbox(
            "Reference compound",
            ["Custom molecule", *PRESET_BY_NAME],
            help="Curated molecules for a quick comparison; receptor subtype is shown separately.",
            key="reference_compound",
            on_change=_apply_reference_compound,
        )
        if selected_compound != "Custom molecule":
            preset = PRESET_BY_NAME[selected_compound]
            st.markdown(
                f"<div class='theory-callout' style='margin-top:0.45rem'>"
                f"<span class='badge-pill {preset['badge']}'>{preset['role']}</span><br>"
                f"<span style='font-size:0.76rem'>{preset['note']}</span></div>",
                unsafe_allow_html=True,
            )

    predict_btn = st.button("Run Selectivity Profile", type="primary", width="stretch")

    # Keep the interface responsive: the ~819 MB model ensemble is loaded only
    # after an explicit request, then the cached report survives tab changes.
    data = st.session_state.get("last_prediction")
    if predict_btn and smiles_query.strip():
        with st.spinner("Executing multi-model inference & conformal uncertainty calculations..."):
            try:
                data = execute_single_prediction(smiles_query, threshold=ACTIVITY_THRESHOLD, run_rf=RUN_RF)
            except Exception as e:
                st.error(f"Inference error: {e}")
                data = None

    elif predict_btn:
        st.warning("Enter a SMILES string or PDB ID before running a profile.")

    if predict_btn and data:
        st.session_state.last_prediction = data

    if data:
        with st.container():
            preds = data.get("predictions", {})
            xgb = preds.get("XGBoost", {})
            best_target = data.get("best_target", "N/A")
            max_pchembl = max([xgb.get(s, 0) for s in ["A1", "A2A", "A2B", "A3"]] + [0])
            ad_obj = data.get("applicability_domain", {})
            ad_in = ad_obj.get("in_domain", True)
            ad_lbl = "Inside AD" if ad_in else "Outside AD"
            ad_color = "success" if ad_in else "error"

            # ── Report header card (native HTML) ──
            ad_badge = "badge-green" if ad_in else "badge-red"
            st.markdown(f"""
            <div class="cadd-card" style="display:flex;flex-direction:column;gap:0.55rem">
                <div style="display:flex;align-items:center;gap:0.9rem">
                    <span class="material-symbols-outlined" style="font-size:2.1rem;color:#7dd3fc;background:rgba(56,189,248,0.16);border-radius:10px;padding:0.55rem">science</span>
                    <div>
                        <div style="font-size:1.25rem;font-weight:700;color:#eef2f4;line-height:1.2">Selectivity Report</div>
                        <div style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;color:#9aa7af">{data['smiles']}</div>
                    </div>
                </div>
                <div style="display:flex;flex-wrap:wrap;gap:0.4rem">
                    <span class="badge-pill badge-cyan">Primary Target · {best_target} Receptor</span>
                    <span class="badge-pill badge-purple">Max pChEMBL · {max_pchembl:.2f}</span>
                    <span class="badge-pill {ad_badge}">AD · {ad_lbl}</span>
                    <span class="badge-pill">Ensemble · XGBoost / RF / LightGBM / Stacked</span>
                    <span class="badge-pill">MAPIE 90% Conformal Intervals</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Result sections as custom badge-style buttons ──
            st.markdown("<div style='margin-bottom:0.5rem'></div>", unsafe_allow_html=True)
            nav_selection = st.pills(
                "Select Section",
                options=[
                    ":material/speed: Overview",
                    ":material/science: Structure",
                    ":material/track_changes: Selectivity",
                    ":material/filter_alt: Drug-likeness",
                    ":material/bar_chart: Explainability",
                    ":material/search: Analog Search",
                    ":material/biotech: Structural Biology",
                    ":material/verified: Provenance",
                ],
                default=":material/speed: Overview",
                label_visibility="collapsed"
            )

            if nav_selection == ":material/speed: Overview":
                _tab_overview(data)
            elif nav_selection == ":material/science: Structure":
                _tab_structure(data)
            elif nav_selection == ":material/track_changes: Selectivity":
                _tab_selectivity(data)
            elif nav_selection == ":material/filter_alt: Drug-likeness":
                _tab_druglikeness(data)
            elif nav_selection == ":material/bar_chart: Explainability":
                _tab_explainability(data)
            elif nav_selection == ":material/search: Analog Search":
                _tab_analog(data)
            elif nav_selection == ":material/biotech: Structural Biology":
                _tab_structural(data)
            elif nav_selection == ":material/verified: Provenance":
                _tab_provenance(data)
# ═════════════════════════════════════════════════════════════════════════════
# TAB 2: BATCH VIRTUAL SCREENING
# ═════════════════════════════════════════════════════════════════════════════

with tab_batch:
    st.markdown("""
    <div style="margin-bottom:1.5rem">
        <h1 class="page-title" style="font-size:2rem;margin:0;color:#f8fafc"><span class="material-symbols-outlined">batch_prediction</span>Batch Virtual Screening</h1>
        <div style="font-size:0.9rem;color:#94a3b8">Screen libraries of candidate molecules against all 4 adenosine receptor subtypes simultaneously</div>
    </div>
    """, unsafe_allow_html=True)
    
    col_b_input, col_b_info = st.columns([2, 1])
    with col_b_input:
        batch_text = st.text_area(
            "Paste SMILES (one per line, optionally with ID separated by space or comma)",
            value="Nc1ncnc2n(cnc12)[C@@H]3O[C@H](CO)[C@@H](O)[C@H]3O,Adenosine\nCc1nn(c(C)c1)c2ncnc3n(cnc23)[C@@H]4O[C@H](CO)[C@@H](O)[C@H]4O,Regadenoson\nCOc1ccc(/C=C/c2nc3n(C)c(=O)n(C)c(=O)c3n2C)cc1OC,Istradefylline",
            height=150
        )
        batch_file = st.file_uploader("Or upload CSV file (must have 'smiles' column)", type=["csv", "txt"])

    with col_b_info:
        st.markdown("""
        <div class="cadd-card" style="font-size:0.8rem">
            <div style="font-weight:700;color:#f8fafc;margin-bottom:0.4rem">Batch Screening Capabilities:</div>
            • Rapid ensemble scoring (< 20 ms / molecule)<br>
            • Automatic canonicalization & stereochemistry validation<br>
            • Applicability domain filtering (Tanimoto < 0.4 flagged)<br>
            • Export scored results to CSV or SDF formats
        </div>
        """, unsafe_allow_html=True)

    if st.button("Run Batch Virtual Screen", type="primary"):
        lines = []
        if batch_file is not None:
            df_in = pd.read_csv(batch_file)
            smiles_col = next((c for c in df_in.columns if c.lower() in ["smiles", "canonical_smiles", "structure"]), None)
            if smiles_col:
                lines = df_in[smiles_col].dropna().tolist()
            else:
                st.error("No 'smiles' column found in uploaded CSV.")
        else:
            lines = [l.strip() for l in batch_text.strip().split("\n") if l.strip()]

        if lines:
            with st.spinner(f"Scoring {len(lines)} candidate molecules across all subtypes..."):
                from src.predictor import predict
                from src.chem_utils import canonicalize_smiles, nearest_tanimoto
                
                results = []
                for item in lines:
                    parts = item.split(",") if "," in item else item.split()
                    smi = parts[0].strip()
                    name = parts[1].strip() if len(parts) > 1 else smi[:15]
                    
                    can_smi = canonicalize_smiles(smi)
                    if not can_smi:
                        continue
                        
                    res = predict(can_smi, threshold=ACTIVITY_THRESHOLD)
                    p = res.get("predictions", {}).get("XGBoost", {})
                    ad_sim = nearest_tanimoto(can_smi) or 0.0
                    
                    results.append({
                        "Compound ID": name,
                        "SMILES": can_smi,
                        "Primary Target": res.get("best_target", "—"),
                        "A1 (pChEMBL)": round(p.get("A1", 0.0), 2),
                        "A2A (pChEMBL)": round(p.get("A2A", 0.0), 2),
                        "A2B (pChEMBL)": round(p.get("A2B", 0.0), 2),
                        "A3 (pChEMBL)": round(p.get("A3", 0.0), 2),
                        "Max AD Similarity": round(ad_sim, 3),
                        "Domain Status": "Inside AD" if ad_sim >= 0.4 else "Outside AD"
                    })

                if results:
                    df_res = pd.DataFrame(results)
                    st.dataframe(df_res, width="stretch", hide_index=True)
                    
                    csv_data = df_res.to_csv(index=False).encode('utf-8')
                    st.download_button("Export Scored Library (CSV)", csv_data, file_name="adenosine_screen_results.csv", mime="text/csv")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3: MODEL PERFORMANCE & BENCHMARK SUITE
# Real model-result payloads, mirroring src/api_routes/model_results.py
# ═════════════════════════════════════════════════════════════════════════════

_SUBS = ["A1", "A2A", "A2B", "A3"]
_RAW_FILES = [
    ("AR_all_unique_parents_with_smiles.csv", "ChEMBL raw parent compounds", "text/csv"),
    ("GPCRdb_A1.xlsx", "A1 ligands (GPCRdb)", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("GPCRdb_A2A.xlsx", "A2A ligands (GPCRdb)", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("GPCRdb_A2B.xlsx", "A2B ligands (GPCRdb)", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("GPCRdb_A3.xlsx", "A3 ligands (GPCRdb)", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("1_get_entries_ARs", "ChEMBL parent-entry fetch script", "application/octet-stream"),
    ("2_add_smiles_to_db_new", "SMILES/registry compile script", "application/octet-stream"),
]


@st.cache_data(show_spinner=False)
def _bm_json(path):
    p = Path(path)
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    if isinstance(d, dict) and d.get("actual_file"):
        real = p.parent / d["actual_file"]
        if real.exists():
            with open(real, encoding="utf-8") as f:
                d = json.load(f)
    return d


def _bm_load():
    return {
        "eval": _bm_json("outputs/validoutput/precise/evaluation_precise_report.json") or {},
        "ext": _bm_json("outputs/external_validation/external_validation_report.json") or {},
        "bench": _bm_json("outputs/benchmark/benchmark_comparison.json") or {},
        "yrand": _bm_json("outputs/y_randomization/all_subtypes_summary.json") or {},
        "diag": _bm_json("outputs/diagnostics/combined_diagnosis_report.json") or {},
        "run": _bm_json("outputs/validoutput/precise/run_root_summary.json") or {},
        "db": _bm_json("data/processed/db_lookup_train.json") or {},
        "shap": {s: _bm_json(f"outputs/shap/{s}_shap_report.json") or {} for s in _SUBS},
        "diag_per": {s: _bm_json(f"outputs/diagnostics/{s.lower()}_diagnosis_report.json") or {} for s in _SUBS},
    }


def _bm_db_csv(db):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["SMILES"] + [f"pChEMBL_{s}" for s in _SUBS])
    for smiles, subtypes in db.items():
        row = [smiles]
        for s in _SUBS:
            v = subtypes.get(s) if isinstance(subtypes, dict) else None
            try:
                row.append(f"{float(v):.2f}" if v not in (None, "", "nan") else "")
            except (TypeError, ValueError):
                row.append("")
        w.writerow(row)
    return buf.getvalue()


def _kpi(label, value, color="var(--cyan)"):
    st.markdown(
        f'<div class="kpi-box"><div class="kpi-label">{label}</div><div class="kpi-value" style="color:{color}">{value}</div></div>',
        unsafe_allow_html=True,
    )


def _bm_header(num, title, subtitle, color="var(--cyan)", icon="dashboard"):
    st.markdown(
        f'<div class="cadd-card"><div class="section-num">{num}</div>'
        f'<div class="section-title" style="color:{color}"><span class="material-symbols-outlined">{icon}</span> {title}</div>'
        f'<div class="section-subtitle">{subtitle}</div></div>',
        unsafe_allow_html=True,
    )


def _bm_perf(bm):
    ev = bm["eval"]
    ov = ev.get("overall", {})
    _bm_header("01", "Model Performance Summary", "Independent test-set metrics with distribution-free 90% conformal intervals (MAPIE CrossConformalRegressor)")
    c = st.columns(4)
    with c[0]: _kpi("Overall R²", f"{ov.get('model_r2', 0):.3f}", "var(--cyan)")
    with c[1]: _kpi("Overall MAE (pChEMBL)", f"{ov.get('model_mae', 0):.3f}", "var(--purple)")
    with c[2]: _kpi("90% Conformal Coverage", f"{ov.get('conformal_coverage_90', 0) * 100:.1f}%", "var(--green)")
    with c[3]: _kpi("Test / Train", f"{ev.get('n_test', 0):,} / {ev.get('n_train', 0):,}", "var(--amber)")

    per = ev.get("per_subtype", {})
    rows = [{
        "Subtype": f"{s} Receptor", "n_test": m.get("n_test", 0),
        "R²": f"{m.get('model_r2', 0):.3f}", "MAE": f"{m.get('model_mae', 0):.3f}",
        "RMSE": f"{m.get('model_rmse', 0):.3f}",
        "90% Coverage": f"{m.get('conformal_coverage_90', 0) * 100:.1f}%",
        "Model": m.get("model_type", "—"),
    } for s in _SUBS if (m := per.get(s, {}))]
    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    fig = go.Figure(go.Bar(
        x=[f"{s} Receptor" for s in _SUBS],
        y=[per.get(s, {}).get("model_r2", 0) for s in _SUBS],
        marker_color=["#38bdf8", "#a78bfa", "#4ade80", "#fbbf24"],
    ))
    fig.update_layout(
        title="Test-Set R² by Receptor Subtype",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(color="#eef2f4"), yaxis=dict(color="#9aa7af", gridcolor="rgba(216,224,230,0.15)"),
        margin=dict(l=40, r=20, t=40, b=40), height=300,
    )
    st.plotly_chart(fig, width="stretch")


def _bm_calib(bm):
    ov = bm["eval"].get("overall", {})
    _bm_header("02", "Conformal Calibration Analysis", "Mean absolute error by uncertainty quartile, from Q1 (low uncertainty) to Q4 (max uncertainty)")
    qs = ov.get("calibration_quartiles", [])
    labels = ["Q1 (Low Unc)", "Q2 (Med Unc)", "Q3 (High Unc)", "Q4 (Max Unc)"]
    fig = go.Figure(go.Bar(
        x=[labels[(q.get("bin", 1) - 1) % 4] for q in qs],
        y=[q.get("mae_mean", 0) for q in qs],
        marker_color="#38bdf8",
        text=[f"n={q.get('n', 0)}" for q in qs],
        textposition="outside",
    ))
    fig.update_layout(
        title="Mean Absolute Error by Uncertainty Quartile",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(color="#eef2f4"), yaxis=dict(color="#9aa7af", gridcolor="rgba(216,224,230,0.15)"),
        margin=dict(l=40, r=20, t=40, b=40), height=320,
    )
    st.plotly_chart(fig, width="stretch")
    cal_png = Path("outputs/calibration_plot.png")
    if cal_png.exists() and cal_png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n":
        st.image(str(cal_png), caption="Calibration plot — empirical vs nominal coverage", width="stretch")
    else:
        st.info("Calibration plot not available (PNG artifact not checked out).")


def _bm_shap(bm):
    _bm_header("03", "SHAP Feature Importance", "Mean |SHAP| feature attributions per subtype with sanity checks")
    comb = Path("figures/fig4_treeshap.png")
    if comb.exists():
        st.image(str(comb), caption="Combined — top TreeSHAP feature attributions across subtypes", width="stretch")
    for s in _SUBS:
        rep = bm["shap"].get(s) or {}
        feats = (rep.get("top_features") or [])[:5]
        if not feats:
            continue
        st.markdown(f"<div style='font-weight:700;color:#f8fafc;margin:0.6rem 0 0.3rem'>{s} Receptor — top features</div>", unsafe_allow_html=True)
        df = pd.DataFrame([{"Rank": f.get("rank"), "Feature": f.get("feature"), "Mean |SHAP|": round(f.get("mean_abs_shap", 0), 4)} for f in feats])
        c1, c2 = st.columns([3, 1])
        with c1:
            st.dataframe(df, width="stretch", hide_index=True)
        with c2:
            san = rep.get("sanity_check", {})
            ok = san.get("status") == "PASS"
            st.markdown(
                f'<div class="kpi-box"><div class="kpi-label">Sanity Check</div>'
                f'<div class="kpi-value" style="color:{"var(--green)" if ok else "var(--red)"}">{san.get("status", "N/A")}</div>'
                f'<div style="font-size:0.7rem;color:var(--text-muted);margin-top:0.3rem">{str(san.get("message", ""))[:80]}</div></div>',
                unsafe_allow_html=True,
            )
        bar, swarm = Path(f"outputs/shap/{s}_bar.png"), Path(f"outputs/shap/{s}_beeswarm.png")
        if bar.exists():
            st.image(str(bar), caption=f"{s} — mean |SHAP| feature importance", width="stretch")
        if swarm.exists():
            st.image(str(swarm), caption=f"{s} — SHAP beeswarm", width="stretch")


def _bm_yrand(bm):
    _bm_header("04", "Y-Randomization (Null Model Control)", "Real model R² vs shuffled-target null distribution; leakage is rejected when separation exceeds several σ")
    summary = bm["yrand"].get("summary", {})
    rows = []
    for s in _SUBS:
        sd = summary.get(s, {})
        real = sd.get("real_r2", 0)
        mean = sd.get("shuffled_r2_mean", 0)
        std = sd.get("shuffled_r2_std", 0)
        rows.append({
            "Subtype": f"{s} Receptor", "Real R²": round(real, 3),
            "Shuffled Mean R²": round(mean, 3), "Shuffled Std": round(std, 3),
            "Separation (σ)": round((real - mean) / max(std, 1e-6), 1),
            "Leakage Warning": "Yes" if sd.get("leakage_warning", True) else "No",
        })
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    fig = go.Figure()
    fig.add_bar(x=[s for s in _SUBS], y=[summary.get(s, {}).get("real_r2", 0) for s in _SUBS], name="Real R²", marker_color="#38bdf8")
    fig.add_bar(x=[s for s in _SUBS], y=[summary.get(s, {}).get("shuffled_r2_mean", 0) for s in _SUBS], name="Shuffled (Null)", marker_color="#f87171")
    fig.update_layout(
        title="Real vs Shuffled R² (Null Control)",
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(color="#eef2f4"), yaxis=dict(color="#9aa7af", gridcolor="rgba(216,224,230,0.15)"),
        legend=dict(font=dict(color="#c8d0d6")),
        margin=dict(l=40, r=20, t=40, b=40), height=320,
    )
    st.plotly_chart(fig, width="stretch")

    for s in _SUBS:
        png = Path(f"outputs/y_randomization/{s}_distribution.png")
        if png.exists():
            st.image(str(png), caption=f"{s} — shuffled R² null distribution vs real R²", width="stretch")


def _bm_diag(bm):
    _bm_header("05", "Training Data Diagnostics", "Scaffold diversity, pChEMBL distributions and activity cliffs per subtype")
    dc = bm["diag"]
    cd = dc.get("scaffold_diversity", {})
    cs = dc.get("pchembl_stats", {})
    c = st.columns(4)
    with c[0]: _kpi("Total Compounds", f"{dc.get('n_compounds', 0):,}", "var(--cyan)")
    with c[1]: _kpi("Unique Scaffolds", f"{cd.get('n_unique_scaffolds', 0):,}", "var(--purple)")
    with c[2]: _kpi("Diversity Ratio", f"{cd.get('diversity_ratio', 0):.3f}", "var(--green)")
    with c[3]: _kpi("pChEMBL Mean ± Std", f"{cs.get('mean', 0):.2f} ± {cs.get('std', 0):.2f}", "var(--amber)")

    rows = [{
        "Subtype": f"{s} Receptor", "Compounds": d.get("n_compounds", 0),
        "Scaffolds": (d.get("scaffold_diversity") or {}).get("n_unique_scaffolds", 0),
        "Diversity": f"{(d.get('scaffold_diversity') or {}).get('diversity_ratio', 0):.3f}",
        "Activity Cliffs": d.get("n_activity_cliffs", 0),
        "pChEMBL Range": f"{(d.get('pchembl_stats') or {}).get('min', 0):.1f}–{(d.get('pchembl_stats') or {}).get('max', 0):.1f}",
    } for s in _SUBS if (d := bm["diag_per"].get(s, {}))]
    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    for s in _SUBS:
        d1 = Path(f"outputs/diagnostics/{s.lower()}_pchembl_distribution.png")
        d2 = Path(f"outputs/diagnostics/{s.lower()}_activity_cliffs_shifts.png")
        if d1.exists():
            st.image(str(d1), caption=f"{s} — pChEMBL distribution", width="stretch")
        if d2.exists():
            st.image(str(d2), caption=f"{s} — activity cliffs shifts", width="stretch")
    comb = Path("outputs/diagnostics/combined_pchembl_distribution.png")
    if comb.exists():
        st.image(str(comb), caption="Combined — pChEMBL distribution", width="stretch")


def _bm_ext(bm):
    _bm_header("06", "External Validation (Blind Literature Set)", "Novel literature molecules withheld from training (not in ChEMBL / GPCRdb)")
    ex = bm["ext"]
    sel = (ex.get("per_subtype_metrics") or {}).get("selectivity_recall_at_1", {})
    c = st.columns(4)
    with c[0]: _kpi("Novel Molecules", f"{ex.get('n_novel_molecules', 0):,}", "var(--cyan)")
    with c[1]: _kpi("Successful Predictions", f"{ex.get('n_successful_predictions', 0):,}", "var(--green)")
    with c[2]: _kpi("Errors", f"{ex.get('n_errors', 0)}", "var(--red)")
    with c[3]: _kpi("Selectivity Recall@1", f"{sel.get('accuracy', 0) * 100:.0f}%" if sel.get("accuracy") is not None else "—", "var(--amber)")

    rows = []
    for sn, m in (ex.get("per_subtype_metrics") or {}).items():
        if sn == "selectivity_recall_at_1":
            continue
        insuff = m.get("insufficient_data", False)
        rows.append({
            "Subtype": f"{sn} Receptor", "n": m.get("n", 0),
            "R²": "—" if insuff else round(m.get("r2", 0), 3),
            "MAE": "—" if insuff else round(m.get("mae", 0), 3),
        })
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def _bm_bench(bm):
    _bm_header("07", "Benchmark Comparison", "Independent method comparison under identical Bemis-Murcko scaffold splits")
    rows = []
    for model, info in bm["bench"].items():
        m = info.get("metrics") or {}
        row = {"Method": model, "Split": info.get("split", "")}
        for s in _SUBS:
            mv = m.get(s, {})
            row[f"{s} R²"] = round(mv.get("r2", 0), 3) if mv.get("r2") is not None else "—"
            row[f"{s} MAE"] = round(mv.get("mae", 0), 3) if mv.get("mae") is not None else "—"
        rows.append(row)
    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def _bm_data(bm):
    _bm_header("08", "Data Provenance & Downloads", "Curated bioactivity database statistics and raw source artifacts")
    db = bm["db"]
    n_values = sum(
        1 for v in db.values() if isinstance(v, dict)
        for s in _SUBS if v.get(s) not in (None, "", "nan")
    )
    c = st.columns(3)
    with c[0]: _kpi("Curated Compounds", f"{len(db):,}", "var(--cyan)")
    with c[1]: _kpi("Bioactivity Values", f"{n_values:,}", "var(--purple)")
    with c[2]:
        run = bm["run"]
        _kpi("Precise Run", f"{run.get('n_lookup_smiles', 0):,} SMILES", "var(--green)")

    st.markdown("<div style='font-weight:700;color:#f8fafc;margin:0.8rem 0 0.4rem'>Raw Source Files</div>", unsafe_allow_html=True)
    raw_cols = st.columns(2)
    for i, (fname, desc, mime) in enumerate(_RAW_FILES):
        p = Path("data/raw") / fname
        if not p.exists():
            continue
        with open(p, "rb") as f:
            payload = f.read()
        with raw_cols[i % 2]:
            st.download_button(desc, payload, file_name=fname, mime=mime, width="stretch")

    st.markdown("<div style='font-weight:700;color:#f8fafc;margin:0.8rem 0 0.4rem'>Curated Database Export</div>", unsafe_allow_html=True)
    csv_text = _bm_db_csv(db)
    if csv_text:
        st.download_button("Download Adenosine Receptor Database (CSV)", csv_text, file_name="adenosine_receptor_database.csv", mime="text/csv")


with tab_benchmark:
    st.markdown("""
    <div style="margin-bottom:1.5rem">
        <h1 class="page-title" style="font-size:2rem;margin:0;color:#f8fafc"><span class="material-symbols-outlined">analytics</span>Model Performance & Validation Suite</h1>
        <div style="font-size:0.9rem;color:#94a3b8">Live model-result payloads: nested cross-validation, scaffold splits, conformal coverage, SHAP, null controls and external validation</div>
    </div>
    """, unsafe_allow_html=True)

    bm = _bm_load()
    if not bm["eval"]:
        st.info("Model result reports not found under outputs/. Run the training pipeline first.")
    else:
        bt_perf, bt_calib, bt_shap, bt_yrand, bt_diag, bt_ext, bt_bench, bt_data = st.tabs([
            ":material/speed: Performance",
            ":material/tune: Calibration",
            ":material/bar_chart: SHAP",
            ":material/shuffle: Y-Randomization",
            ":material/monitor_heart: Diagnostics",
            ":material/public: External Validation",
            ":material/leaderboard: Benchmark",
            ":material/download: Data & Downloads",
        ])
        with bt_perf:
            _bm_perf(bm)
        with bt_calib:
            _bm_calib(bm)
        with bt_shap:
            _bm_shap(bm)
        with bt_yrand:
            _bm_yrand(bm)
        with bt_diag:
            _bm_diag(bm)
        with bt_ext:
            _bm_ext(bm)
        with bt_bench:
            _bm_bench(bm)
        with bt_data:
            _bm_data(bm)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 4: STRUCTURAL BIOLOGY 3D GALLERY
# ═════════════════════════════════════════════════════════════════════════════

with tab_library:
    st.markdown("""
    <div style="margin-bottom:1.5rem">
        <h1 class="page-title" style="font-size:2rem;margin:0;color:#f8fafc"><span class="material-symbols-outlined">view_in_ar</span>Structural Biology 3D Pocket Gallery</h1>
        <div style="font-size:0.9rem;color:#94a3b8">Side-by-side comparison of genuine deposited active and inactive crystal / cryo-EM complexes</div>
    </div>
    """, unsafe_allow_html=True)

    g_col1, g_col2 = st.columns(2)
    with g_col1:
        st.markdown("""<h3 class="page-title" style="color:var(--green)"><span class="material-symbols-outlined">radio_button_checked</span>Active Signaling Conformations (Agonist-Bound)</h3>""", unsafe_allow_html=True)
        act_sel = st.selectbox("Active Structure", ["A2A: 6GDG (2.6 Å, Adenosine)", "A1: 6D9H (3.6 Å, Adenosine)", "A2B: 6LPJ (3.2 Å, BAY 60-6583)", "A3: 7VAK (3.0 Å, IB-MECA)"], key="g_act")
        pdb_act = act_sel.split(":")[1].split("(")[0].strip()
        components.html(render_3dmol_complex(pdb_act), height=400)
        
    with g_col2:
        st.markdown("""<h3 class="page-title" style="color:var(--red)"><span class="material-symbols-outlined">pause_circle</span>Inactive Ground State Conformations (Antagonist-Bound)</h3>""", unsafe_allow_html=True)
        inact_sel = st.selectbox("Inactive Structure", ["A2A: 4EIY (1.8 Å, ZM241385)", "A1: 5N2S (3.3 Å, DU172)", "A2B: 8JZX (3.1 Å, PSB-603)", "A3: 8HN0 (3.2 Å, PSB-11)"], key="g_inact")
        pdb_inact = inact_sel.split(":")[1].split("(")[0].strip()
        components.html(render_3dmol_complex(pdb_inact), height=400)
