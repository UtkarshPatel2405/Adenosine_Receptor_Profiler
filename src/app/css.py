_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ═══════════════════════════════════════════════════════════
   Publication-Grade Scientific Platform Theme
   Glassmorphism, High-Contrast Neon Accents & Motion Physics
   ═══════════════════════════════════════════════════════════ */

/* ── Hardware Accelerated Animations & Keyframes ─────────── */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(14px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes pulseGlow {
    0%, 100% {
        box-shadow: 0 0 8px rgba(56, 189, 248, 0.25), inset 0 0 6px rgba(56, 189, 248, 0.1);
        border-color: rgba(56, 189, 248, 0.3);
    }
    50% {
        box-shadow: 0 0 22px rgba(56, 189, 248, 0.6), inset 0 0 12px rgba(56, 189, 248, 0.25);
        border-color: rgba(56, 189, 248, 0.65);
    }
}

@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

@keyframes floatIcon {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-4px) rotate(2deg); }
}

@keyframes spinSlow {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

@keyframes badgePulse {
    0%, 100% { opacity: 0.92; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.04); }
}

/* ── Base App Layout ─────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at 50% 0%, #0d172a 0%, #060b14 100%) !important;
    color: #f1f5f9 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

[data-testid="stHeader"] {
    background: rgba(6, 11, 20, 0.85) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    border-bottom: 1px solid rgba(56, 189, 248, 0.15) !important;
}

[data-testid="stSidebar"] {
    background: rgba(4, 8, 16, 0.95) !important;
    backdrop-filter: blur(16px) !important;
    border-right: 1px solid rgba(56, 189, 248, 0.15) !important;
}

/* ── Typography ─────────────────────────────────────────── */
h1, h2, h3, h4 {
    color: #f8fafc !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em !important;
}
h1 { font-size: 1.65rem !important; }
h2 { font-size: 1.3rem !important; }
h3 { font-size: 1.05rem !important; }
p, span, label, div, li, td, th { color: #e2e8f0 !important; }
.stMarkdown p { color: #cbd5e1 !important; line-height: 1.65 !important; }
code {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important;
    color: #38bdf8 !important;
    background: rgba(15, 23, 42, 0.8) !important;
    padding: 0.15rem 0.4rem !important;
    border-radius: 4px !important;
    border: 1px solid rgba(56, 189, 248, 0.2) !important;
}

/* ── Entrance Animation Utilities ────────────────────────── */
.anim-in { animation: fadeInUp 0.45s cubic-bezier(0.16, 1, 0.3, 1) both; }
.anim-in-d1 { animation: fadeInUp 0.45s cubic-bezier(0.16, 1, 0.3, 1) 0.08s both; }
.anim-in-d2 { animation: fadeInUp 0.45s cubic-bezier(0.16, 1, 0.3, 1) 0.16s both; }
.anim-in-d3 { animation: fadeInUp 0.45s cubic-bezier(0.16, 1, 0.3, 1) 0.24s both; }
.anim-in-d4 { animation: fadeInUp 0.45s cubic-bezier(0.16, 1, 0.3, 1) 0.32s both; }

/* ── Glassmorphic Container Cards ───────────────────────── */
.card {
    background: rgba(15, 23, 42, 0.75) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(56, 189, 248, 0.18) !important;
    border-radius: 12px !important;
    padding: 1.0rem 1.25rem !important;
    margin-bottom: 0.9rem !important;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.35) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.card:hover {
    transform: translateY(-3px) !important;
    border-color: rgba(56, 189, 248, 0.4) !important;
    box-shadow: 0 12px 28px -6px rgba(0, 0, 0, 0.5), 0 0 20px rgba(56, 189, 248, 0.15) !important;
}

/* ── Motion Icons & Badges ──────────────────────────────── */
.motion-icon {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    vertical-align: middle !important;
    transition: all 0.3s ease !important;
}
.icon-spin { animation: spinSlow 12s linear indefinite !important; }
.icon-pulse { animation: badgePulse 2s ease-in-out infinite !important; }
.icon-float { animation: floatIcon 3.5s ease-in-out infinite !important; }
.icon-glow { filter: drop-shadow(0 0 6px rgba(56, 189, 248, 0.6)) !important; }

/* ── Scientific Badges ──────────────────────────────────── */
.badge {
    display: inline-flex !important;
    align-items: center !important;
    gap: 0.3rem !important;
    padding: 0.22rem 0.6rem !important;
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    letter-spacing: 0.025em !important;
    white-space: nowrap !important;
    transition: all 0.25s ease !important;
}
.badge:hover {
    transform: scale(1.05) !important;
}
.badge-blue {
    background: rgba(56, 189, 248, 0.15) !important;
    color: #38bdf8 !important;
    border: 1px solid rgba(56, 189, 248, 0.35) !important;
}
.badge-green {
    background: rgba(34, 197, 94, 0.15) !important;
    color: #4ade80 !important;
    border: 1px solid rgba(34, 197, 94, 0.35) !important;
}
.badge-amber {
    background: rgba(234, 179, 8, 0.15) !important;
    color: #facc15 !important;
    border: 1px solid rgba(234, 179, 8, 0.35) !important;
}
.badge-red {
    background: rgba(239, 68, 68, 0.15) !important;
    color: #f87171 !important;
    border: 1px solid rgba(239, 68, 68, 0.35) !important;
}
.badge-purple {
    background: rgba(168, 85, 247, 0.15) !important;
    color: #c084fc !important;
    border: 1px solid rgba(168, 85, 247, 0.35) !important;
}
.badge-cyan {
    background: rgba(20, 184, 166, 0.15) !important;
    color: #2dd4bf !important;
    border: 1px solid rgba(20, 184, 166, 0.35) !important;
}
.badge-slate {
    background: rgba(148, 163, 184, 0.15) !important;
    color: #cbd5e1 !important;
    border: 1px solid rgba(148, 163, 184, 0.3) !important;
}

.badge-row {
    display: flex !important;
    flex-wrap: wrap !important;
    align-items: center !important;
    gap: 0.4rem !important;
}

/* ── Section Headers ────────────────────────────────────── */
.section-header {
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    color: #f8fafc !important;
    text-transform: uppercase !important;
    letter-spacing: 0.09em !important;
    margin-top: 0.6rem !important;
    margin-bottom: 0.75rem !important;
    padding-bottom: 0.45rem !important;
    border-bottom: 1px solid rgba(56, 189, 248, 0.2) !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.55rem !important;
}

/* ── Hero Banner Section ────────────────────────────────── */
.hero {
    padding: 1.4rem 1.8rem !important;
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.8) 100%) !important;
    backdrop-filter: blur(16px) !important;
    border: 1px solid rgba(56, 189, 248, 0.25) !important;
    border-radius: 14px !important;
    margin-bottom: 1.2rem !important;
    box-shadow: 0 8px 32px -4px rgba(0, 0, 0, 0.45), 0 0 24px rgba(56, 189, 248, 0.12) !important;
    animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}
.hero h1 { font-size: 1.6rem !important; font-weight: 800 !important; margin: 0 !important; color: #f8fafc !important; }
.hero p { font-size: 0.85rem !important; color: #cbd5e1 !important; margin: 0.4rem 0 0.7rem 0 !important; }

/* ── Dashboard Metric Grid ──────────────────────────────── */
.dash-grid { display: flex !important; gap: 0.6rem !important; margin-top: 0.9rem !important; flex-wrap: wrap !important; }
.dash-card {
    background: rgba(30, 41, 59, 0.7) !important;
    backdrop-filter: blur(8px) !important;
    border: 1px solid rgba(56, 189, 248, 0.18) !important;
    border-radius: 10px !important;
    padding: 0.7rem 0.9rem !important;
    text-align: center !important;
    flex: 1 !important;
    min-width: 90px !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.dash-card:hover {
    transform: translateY(-4px) scale(1.02) !important;
    border-color: rgba(56, 189, 248, 0.45) !important;
    box-shadow: 0 8px 20px -4px rgba(0, 0, 0, 0.4), 0 0 16px rgba(56, 189, 248, 0.2) !important;
}
.dash-label { font-size: 0.62rem !important; font-weight: 700 !important; color: #94a3b8 !important; text-transform: uppercase !important; letter-spacing: 0.07em !important; margin-bottom: 0.2rem !important; }
.dash-value { font-size: 1.25rem !important; font-weight: 800 !important; color: #ffffff !important; text-shadow: 0 0 12px rgba(56, 189, 248, 0.3); }
.dash-sub { font-size: 0.62rem !important; color: #cbd5e1 !important; margin-top: 0.15rem !important; }

/* ── Inputs & Selectboxes ────────────────────────────────── */
.stTextInput > div > div > input {
    background: rgba(15, 23, 42, 0.9) !important;
    border: 1px solid rgba(56, 189, 248, 0.25) !important;
    border-radius: 8px !important;
    color: #f8fafc !important;
    padding: 0.55rem 0.85rem !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
    transition: all 0.25s ease !important;
}
.stTextInput > div > div > input:focus {
    border-color: #38bdf8 !important;
    box-shadow: 0 0 14px rgba(56, 189, 248, 0.35) !important;
}

div[data-baseweb="select"] input {
    caret-color: transparent !important;
}

/* ── Interactive Buttons ─────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(56, 189, 248, 0.35) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 0.45rem 0.95rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3) !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #38bdf8 0%, #0284c7 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(56, 189, 248, 0.45) !important;
    border-color: #38bdf8 !important;
}

/* ── Modern Animated Tabs ────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(15, 23, 42, 0.85) !important;
    border-radius: 10px !important;
    padding: 0.2rem !important;
    border: 1px solid rgba(56, 189, 248, 0.12) !important;
    gap: 0.2rem !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #94a3b8 !important;
    padding: 0.4rem 0.8rem !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    border-radius: 8px !important;
    border: none !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #f8fafc !important;
    background: rgba(56, 189, 248, 0.08) !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, rgba(56, 189, 248, 0.2) 0%, rgba(168, 85, 247, 0.15) 100%) !important;
    color: #38bdf8 !important;
    font-weight: 700 !important;
    border: 1px solid rgba(56, 189, 248, 0.3) !important;
    box-shadow: 0 4px 12px rgba(56, 189, 248, 0.15) !important;
}

/* ── Info / Tooltip Boxes ───────────────────────────────── */
.sci-box {
    background: rgba(56, 189, 248, 0.04) !important;
    border: 1px solid rgba(56, 189, 248, 0.15) !important;
    border-radius: 10px !important;
    padding: 0.85rem 1.0rem !important;
    font-size: 0.78rem !important;
    color: #cbd5e1 !important;
    line-height: 1.6 !important;
    margin-bottom: 0.7rem !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2) !important;
}

/* ── Subtype Affinity Pills ─────────────────────────────── */
.affinity-row {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    padding: 0.4rem 0.65rem !important;
    margin-bottom: 0.35rem !important;
    background: rgba(15, 23, 42, 0.8) !important;
    border: 1px solid rgba(56, 189, 248, 0.1) !important;
    border-radius: 8px !important;
    transition: all 0.25s ease !important;
}
.affinity-row:hover {
    background: rgba(30, 41, 59, 0.85) !important;
    border-color: rgba(56, 189, 248, 0.25) !important;
    transform: translateX(3px) !important;
}

/* ── Feature Importance Rows ────────────────────────────── */
.feat-row {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    padding: 0.22rem 0.45rem !important;
    font-size: 0.75rem !important;
    border-bottom: 1px solid rgba(56, 189, 248, 0.08) !important;
    transition: background 0.2s ease !important;
}
.feat-row:hover {
    background: rgba(56, 189, 248, 0.06) !important;
}

/* ── DataFrames & Tables ────────────────────────────────── */
div[data-testid="stDataFrame"] {
    border: 1px solid rgba(56, 189, 248, 0.15) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
}

/* ── Metric Containers ──────────────────────────────────── */
[data-testid="stMetricValue"] {
    color: #f8fafc !important;
    font-weight: 800 !important;
    text-shadow: 0 0 10px rgba(56, 189, 248, 0.25) !important;
}
[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
    font-size: 0.74rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}

</style>
"""
