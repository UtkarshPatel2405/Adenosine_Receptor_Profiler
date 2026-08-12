# src/app/css.py
"""Theme = the site's real style.css (loaded verbatim) + Streamlit widget theming.

The static webapp's full design system (src/static/css/style.css) is reused as-is so the
Streamlit app renders with the exact same fonts, colors, cards, animations and glow effects.
A Streamlit override block then maps Streamlit's native widgets (tabs, buttons, inputs,
file uploader, dataframes, expanders, metrics) onto that design system.
"""
from pathlib import Path

_STATIC_CSS = Path(__file__).resolve().parent.parent / "static" / "css" / "style.css"

# Extra classes used by the Streamlit pages that are NOT part of the static site CSS.
_PAGE_UTILS = """
/* ═══════════════════════════════════════════
   Streamlit page utility classes
   ═══════════════════════════════════════════ */
.badge-slate { background: #475569; }
.badge-row { display: flex; flex-wrap: wrap; align-items: center; gap: .4rem; }
.anim-in-d1 { animation: fadeInUp .55s var(--ease) .08s both; }
.anim-in-d2 { animation: fadeInUp .55s var(--ease) .16s both; }
.anim-in-d3 { animation: fadeInUp .55s var(--ease) .24s both; }
.anim-in-d4 { animation: fadeInUp .55s var(--ease) .32s both; }

.pb { background: rgba(255,255,255,.08); border-radius: 999px; overflow: hidden; }
.pb .f { height: 100%; border-radius: 999px; transition: width .8s cubic-bezier(.22,1,.36,1); }

.hi { display: flex; align-items: center; justify-content: space-between; gap: .4rem;
      padding: .3rem .5rem; border-radius: 8px; background: rgba(15,23,42,.6);
      border: 1px solid rgba(255,255,255,.06); margin-bottom: .3rem; font-size: .68rem; color: #cbd5e1; }
.tag { font-size: .58rem; font-weight: 700; padding: .08rem .45rem; border-radius: 999px; color: #fff; }
.tag.tg { background: #15803d; }
.tag.ta { background: #b45309; }
.tag.tr { background: #b91c1c; }

.sd { height: 1rem; }

.affinity-row { display: flex; justify-content: space-between; align-items: center;
    gap: .4rem; padding: .45rem .65rem; margin-bottom: .35rem; background: rgba(15,23,42,.8);
    border: 1px solid rgba(56,189,248,.1); border-radius: 8px; transition: all .25s var(--ease); }
.affinity-row:hover { background: rgba(30,41,59,.85); border-color: rgba(56,189,248,.25); transform: translateX(3px); }
.affinity-row b, .affinity-row span { font-size: .78rem; }

.ad-warning-box-oi { background: rgba(127,29,29,.4); border: 1px solid rgba(153,27,27,.6);
    border-radius: 10px; padding: .7rem .9rem; margin-bottom: .9rem; animation: pulseRed 2s ease-in-out infinite; }

.card-glow { position: relative; overflow: hidden; }
.card-glow::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, rgba(56,189,248,.45), transparent);
    animation: streamSweep 2.4s linear infinite; pointer-events: none; }

.ct { font-family: var(--font-display); font-weight: 800; font-size: 1.1rem; margin-bottom: .6rem; color: var(--ink); }

.flow-svg { width: 100%; display: block; }
"""

# Streamlit native-widget theming on top of the site design system.
_STREAM_OVERRIDES = """
/* ═══════════════════════════════════════════
   Streamlit widget theming (maps native widgets onto the site skin)
   ═══════════════════════════════════════════ */
html, body { background: var(--bg-page) !important; }

[data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stApp"] {
    background:
        radial-gradient(1200px 700px at 85% -10%, rgba(56,189,248,.08), transparent 55%),
        radial-gradient(900px 600px at -10% 15%, rgba(167,139,250,.07), transparent 55%),
        radial-gradient(1000px 700px at 50% 110%, rgba(74,222,128,.05), transparent 55%),
        var(--bg-page) !important;
    color: var(--ink) !important;
    font-family: var(--font-body);
}

/* remove Streamlit chrome */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stStatusWidget"] {
    visibility: hidden; height: 0;
}
header[data-testid="stHeader"] { background: transparent !important; }

/* main content column widths match the site's .app-container */
.block-container { max-width: 1400px; padding-top: 1.2rem; padding-bottom: 4rem; }

/* Typography */
h1, h2, h3, h4, h5, h6 { color: #f8fafc !important; font-family: var(--font-display) !important; }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span, [data-testid="stMarkdownContainer"] div { color: var(--ink-soft); }
[data-testid="stMarkdownContainer"] strong { color: var(--ink); }
code { font-family: var(--font-mono) !important; color: #7dd3fc !important;
       background: rgba(56,189,248,.15) !important; border: none; }

/* ── Tabs → site nav-tabs (dark pill bar, indigo gradient active) ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #232b30; padding: .32rem; border-radius: 12px;
    border: 1px solid var(--border); gap: .35rem;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    padding: .5rem 1rem; font-size: .8rem; font-weight: 600; color: var(--ink-soft);
    background: transparent; border: 1px solid transparent; border-radius: 9px;
    font-family: var(--font-body); transition: all var(--dur) var(--ease);
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover { color: var(--ink); background: rgba(79,70,229,.14); }
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
    color: #fff; background: linear-gradient(135deg,#4F46E5,#2563EB);
    border-color: rgba(79,70,229,.6); box-shadow: 0 6px 18px rgba(79,70,229,.4);
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-border"],
[data-testid="stTabs"] [data-baseweb="tab-list"] [role="presentation"] {
    background: transparent !important;
}
[data-testid="stTabs"] [data-baseweb="tab-list"] [data-testid="stTabs"] { gap: .35rem; }

/* ── Buttons → .btn ── */
.stButton > button, [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-primary"],
[data-testid="stDownloadButton"], [data-testid="stFormSubmitButton"] button {
    background: linear-gradient(135deg,#4F46E5,#2563EB) !important;
    color: #fff !important; border: 1px solid rgba(79,70,229,.4) !important;
    border-radius: 10px !important; font-weight: 700 !important; font-size: .84rem !important;
    font-family: var(--font-body) !important; padding: .5rem 1rem !important;
    box-shadow: 0 6px 18px rgba(79,70,229,.35) !important;
    transition: background var(--dur) var(--ease), transform var(--dur) var(--ease), box-shadow var(--dur) var(--ease) !important;
}
.stButton > button:hover, [data-testid="stBaseButton-secondary"]:hover,
[data-testid="stBaseButton-primary"]:hover, [data-testid="stDownloadButton"]:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 10px 26px rgba(79,70,229,.45) !important;
}
.stButton > button:active { transform: scale(.98); box-shadow: 0 4px 12px rgba(79,70,229,.3) !important; }

/* ── Text input → .input-field ── */
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-testid="stNumberInput"] input {
    background: rgba(15,23,42,.6) !important; color: var(--ink) !important;
    font-family: var(--font-mono) !important; font-size: .85rem !important;
    border: 1px solid rgba(255,255,255,.1) !important; border-radius: 10px !important;
}
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus {
    border-color: var(--accent-cyan) !important;
    box-shadow: 0 0 0 3px rgba(56,189,248,.2) !important;
}
[data-testid="stTextInput"] label, [data-testid="stTextArea"] label,
[data-testid="stNumberInput"] label, [data-testid="stSelectbox"] label,
[data-testid="stFileUploader"] label, [data-testid="stExpander"] label {
    color: var(--ink-soft) !important; font-size: .78rem !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background: rgba(15,23,42,.6) !important; color: var(--ink) !important;
    border: 1px solid rgba(255,255,255,.1) !important; border-radius: 10px !important;
}
[data-testid="stSelectbox"] ul, [data-testid="stSelectbox"] li {
    background: #232b30 !important; color: var(--ink) !important;
}
[data-testid="stSelectbox"] li[aria-selected="true"] { background: rgba(79,70,229,.4) !important; }

/* ── File uploader → dropzone ── */
[data-testid="stFileUploaderDropzone"] {
    border: 2px dashed var(--border-strong) !important; border-radius: var(--radius) !important;
    background: rgba(255,255,255,.05) !important; padding: 2.4rem 1.5rem !important; text-align: center !important;
    transition: all .3s var(--ease) !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--accent-cyan) !important; background: rgba(56,189,248,.1) !important;
}
[data-testid="stFileUploaderDropzone"] button {
    background: linear-gradient(135deg,#4F46E5,#2563EB) !important; color: #fff !important;
    border-radius: 8px !important; border: 1px solid rgba(79,70,229,.4) !important;
    font-weight: 600 !important;
}
[data-testid="stFileUploaderDropzone"] small, [data-testid="stFileUploaderDropzone"] span { color: var(--ink-muted) !important; }

/* ── Dataframe / tables → table-wrap ── */
[data-testid="stDataFrame"], [data-testid="stTable"] {
    border: 1px solid rgba(255,255,255,.06) !important;
    border-radius: 12px !important; overflow: hidden !important;
    background: rgba(15,23,42,.5) !important;
}
[data-testid="stDataFrame"] [data-testid="stElementContainer"] { background: transparent; }
[data-testid="stDataFrame"] canvas { color-scheme: dark; }

/* ── Expander → card ── */
[data-testid="stExpander"] {
    background: var(--glass-bg) !important; border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius) !important; box-shadow: var(--shadow-1) !important;
    overflow: hidden !important; margin-bottom: 1rem !important;
}
[data-testid="stExpander"] details, [data-testid="stExpander"] summary,
[data-testid="stExpander"] [data-testid="stExpander"] summary {
    background: transparent !important; color: var(--ink) !important;
}
[data-testid="stExpander"] summary { font-weight: 700 !important; padding: .6rem 1rem; }

/* ── Metrics → metric-box ── */
[data-testid="stMetric"] {
    background: rgba(255,255,255,.06) !important; border: 1px solid rgba(255,255,255,.14) !important;
    border-radius: 12px !important; padding: .9rem 1rem !important; text-align: center !important;
    transition: transform .3s var(--ease), border-color .3s var(--ease) !important;
}
[data-testid="stMetric"]:hover { transform: translateY(-4px); border-color: var(--border-strong); }
[data-testid="stMetricValue"] {
    font-family: var(--font-display) !important; font-weight: 800 !important;
    font-size: 1.45rem !important; color: var(--ink) !important;
}
[data-testid="stMetricLabel"] {
    color: var(--ink-soft) !important; font-size: .62rem !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: .09em !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: rgba(35,43,48,.92) !important; border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--ink-soft); }

/* ── Spinner ── */
[data-testid="stSpinner"] > div { color: var(--accent-cyan) !important; }
[data-testid="stSpinner"] > div::before { border-top-color: var(--accent-cyan) !important; }

/* ── Captions / info / warnings tinted for dark skin ── */
[data-testid="stCaptionContainer"] { color: var(--ink-muted) !important; }
[data-testid="stInfo"], [data-testid="stSuccess"], [data-testid="stWarning"], [data-testid="stError"] {
    background: rgba(15,23,42,.75) !important; border: 1px solid var(--border) !important;
    border-radius: 12px !important; color: var(--ink-soft) !important;
}
[data-testid="stInfo"] svg { fill: var(--accent-cyan) !important; }
[data-testid="stWarning"] svg { fill: var(--accent-amber) !important; }
[data-testid="stError"] svg { fill: var(--accent-red) !important; }

/* ── Dot-grid overlay (matches site body::before) ── */
.dot-grid {
    position: fixed; inset: 0; z-index: -1; pointer-events: none;
    background-image: radial-gradient(rgba(148,163,184,.10) 1px, transparent 1px);
    background-size: 26px 26px;
}

/* Fixed background layers: keep behind Streamlit content, particles above */
.bg-orbs, .neural-paths { z-index: -1 !important; }
#particle-canvas { z-index: 2; }
[data-testid="stMain"] .block-container { position: relative; z-index: 1; }

/* Navbar brand ring icon */
.brand-ring { filter: drop-shadow(0 0 8px rgba(2,132,199,.5)); }
"""


def _load() -> str:
    try:
        if _STATIC_CSS.exists():
            return _STATIC_CSS.read_text(encoding="utf-8")
    except Exception:
        pass
    return ""


_CSS = _load() + _PAGE_UTILS + _STREAM_OVERRIDES
