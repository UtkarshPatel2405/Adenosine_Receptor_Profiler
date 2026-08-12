import sys
import numpy as np
from pathlib import Path

# Explicit imports so unpickling resolves LightGBM, XGBoost, and MAPIE models
try:
    import lightgbm as lgb
    import lightgbm.sklearn
except ModuleNotFoundError:
    lgb = None

try:
    import xgboost as xgb
except ModuleNotFoundError:
    xgb = None

try:
    import mapie
except ModuleNotFoundError:
    mapie = None


class AverageEnsemble:
    """Equal-weight average ensemble model wrapper for stacked prediction."""
    def predict(self, X):
        return np.mean(X, axis=1)


setattr(sys.modules['__main__'], 'AverageEnsemble', AverageEnsemble)

# Add project root to sys.path first
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Force matplotlib backend and initialize early to avoid circular import issues in Streamlit
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import streamlit as st
import pandas as pd
from src.config import SUBTYPES
from src.app.css import _CSS
from src.app.pages.single_predict import render_single_predict
from src.app.components.batch_predict import render_batch_predict
from src.app.pages.model_results import render_model_results
from src.app.components.model_reports import _load_json


# ─────────────────────────────────────────────────────────────
# Site shell: background layers + navbar + hero + footer
# (transplanted verbatim from src/static/index.html)
# ─────────────────────────────────────────────────────────────

_BACKGROUND = """
<div class="bg-orbs">
  <div class="bg-orb bg-orb-1"></div>
  <div class="bg-orb bg-orb-2"></div>
  <div class="bg-orb bg-orb-3"></div>
</div>
<svg class="neural-paths" viewBox="0 0 1400 900" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
  <path class="neural-line neural-line-1" d="M0,200 C300,180 400,350 700,300 S1100,150 1400,220" stroke="url(#nGrad1)" stroke-width="1" fill="none"/>
  <path class="neural-line neural-line-2" d="M0,500 C250,480 500,600 750,520 S1050,400 1400,480" stroke="url(#nGrad2)" stroke-width="1" fill="none"/>
  <path class="neural-line neural-line-3" d="M0,750 C350,720 600,850 850,780 S1200,680 1400,740" stroke="url(#nGrad3)" stroke-width="1" fill="none"/>
  <defs>
    <linearGradient id="nGrad1" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stop-color="rgba(56,189,248,0)"/><stop offset="50%" stop-color="rgba(56,189,248,0.15)"/><stop offset="100%" stop-color="rgba(167,139,250,0)"/></linearGradient>
    <linearGradient id="nGrad2" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stop-color="rgba(74,222,128,0)"/><stop offset="50%" stop-color="rgba(74,222,128,0.12)"/><stop offset="100%" stop-color="rgba(56,189,248,0)"/></linearGradient>
    <linearGradient id="nGrad3" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" stop-color="rgba(167,139,250,0)"/><stop offset="50%" stop-color="rgba(167,139,250,0.10)"/><stop offset="100%" stop-color="rgba(74,222,128,0)"/></linearGradient>
  </defs>
  <circle class="neural-pulse neural-pulse-1" r="3" fill="#38bdf8" opacity="0.6"><animateMotion dur="8s" repeatCount="indefinite" path="M0,200 C300,180 400,350 700,300 S1100,150 1400,220"/></circle>
  <circle class="neural-pulse neural-pulse-2" r="2.5" fill="#4ade80" opacity="0.5"><animateMotion dur="10s" repeatCount="indefinite" path="M0,500 C250,480 500,600 750,520 S1050,400 1400,480"/></circle>
  <circle class="neural-pulse neural-pulse-3" r="2" fill="#a78bfa" opacity="0.4"><animateMotion dur="12s" repeatCount="indefinite" path="M0,750 C350,720 600,850 850,780 S1200,680 1400,740"/></circle>
</svg>
<div class="dot-grid"></div>
<canvas id="particle-canvas"></canvas>
<script>
(function(){
  var c=document.getElementById('particle-canvas');
  if(!c||c.dataset.initialized)return;
  c.dataset.initialized='1';
  if(window.__pLoop) cancelAnimationFrame(window.__pLoop);
  var ctx=c.getContext('2d'),W,H,pts=[],LINK=140;
  function resize(){W=c.width=window.innerWidth;H=c.height=window.innerHeight;}
  window.addEventListener('resize',resize);resize();
  for(var i=0;i<55;i++)pts.push({x:Math.random()*W,y:Math.random()*H,
    vx:(Math.random()-0.5)*0.2,vy:(Math.random()-0.5)*0.2,r:Math.random()*1.8+0.6,p:Math.random()*Math.PI});
  function draw(){
    ctx.clearRect(0,0,W,H);
    for(var i=0;i<pts.length;i++)for(var j=i+1;j<pts.length;j++){
      var dx=pts[i].x-pts[j].x,dy=pts[i].y-pts[j].y,d2=dx*dx+dy*dy;
      if(d2<LINK*LINK){var a=(1-d2/(LINK*LINK))*0.45;
        ctx.strokeStyle='rgba(148,163,184,'+a+')';ctx.lineWidth=1;
        ctx.beginPath();ctx.moveTo(pts[i].x,pts[i].y);ctx.lineTo(pts[j].x,pts[j].y);ctx.stroke();}}
    for(var k=0;k<pts.length;k++){
      var p=pts[k];p.x+=p.vx;p.y+=p.vy;p.p+=0.002;
      if(p.x<-10)p.x=W+10;else if(p.x>W+10)p.x=-10;
      if(p.y<-10)p.y=H+10;else if(p.y>H+10)p.y=-10;
      ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      var g=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,p.r*4);
      g.addColorStop(0,'rgba(56,189,248,'+(0.35+0.15*Math.sin(p.p))+')');
      g.addColorStop(1,'rgba(56,189,248,0)');ctx.fillStyle=g;ctx.fill();}
    window.__pLoop=requestAnimationFrame(draw);
  }
  draw();
})();
</script>
"""

_NAVBAR = """
<header class="navbar anim-in">
  <div class="brand">
    <svg class="motion-icon icon-spin brand-ring" width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="4" stroke="#38bdf8" stroke-width="1.5"/>
      <circle cx="12" cy="4" r="2" fill="#a78bfa"/>
      <circle cx="20" cy="12" r="1.5" fill="#4ade80"/>
      <circle cx="12" cy="20" r="1.5" fill="#fbbf24"/>
    </svg>
    <div>
      <h1>Adenosine Selectivity Platform</h1>
      <p>Conformal Multi-Model ML &middot; GPCR Profiling across A<sub>1</sub>, A<sub>2A</sub>, A<sub>2B</sub>, A<sub>3</sub></p>
    </div>
  </div>
</header>
"""


def _hero(m) -> str:
    return f"""
<div class="hero-banner reveal" id="hero-banner">
  <div class="hero-inner">
    <div class="hero-text">
      <span class="hero-badge">&#128737; Conformal ML</span>
      <h2 class="hero-title">Predict Adenosine Receptor<br>Selectivity with Confidence</h2>
      <p class="hero-sub">Multi-model ensemble (XGBoost, LightGBM, RandomForest, Stacking) trained on {m['n']} pChEMBL records with MAPIE 90% conformal prediction intervals across A<sub>1</sub>, A<sub>2A</sub>, A<sub>2B</sub>, A<sub>3</sub>.</p>
      <div class="hero-stats">
        <div class="hero-stat"><span class="hero-stat-num" data-count="4">0</span><span class="hero-stat-label">Receptor Subtypes</span></div>
        <div class="hero-stat"><span class="hero-stat-num" data-count="33401">0</span><span class="hero-stat-label">Training Records</span></div>
        <div class="hero-stat"><span class="hero-stat-num" data-count="4">0</span><span class="hero-stat-label">ML Models</span></div>
        <div class="hero-stat"><span class="hero-stat-num" data-count="90">0</span><span class="hero-stat-label">% Conformal CI</span></div>
      </div>
    </div>
    <div class="hero-visual">
      <div class="hero-molecule-ring">
        <svg class="hero-ring-svg" viewBox="0 0 260 260" fill="none" xmlns="http://www.w3.org/2000/svg">
          <circle cx="130" cy="130" r="118" stroke="url(#heroGrad)" stroke-width="1.5" opacity="0.5"/>
          <circle cx="130" cy="130" r="95" stroke="url(#heroGrad2)" stroke-width="1" opacity="0.35"/>
          <circle cx="130" cy="130" r="72" stroke="rgba(56,189,248,0.15)" stroke-width="1" stroke-dasharray="6 8"/>
          <defs>
            <linearGradient id="heroGrad" x1="0" y1="0" x2="260" y2="260"><stop offset="0%" stop-color="#38bdf8"/><stop offset="100%" stop-color="#a78bfa"/></linearGradient>
            <linearGradient id="heroGrad2" x1="260" y1="0" x2="0" y2="260"><stop offset="0%" stop-color="#4ade80"/><stop offset="100%" stop-color="#38bdf8"/></linearGradient>
          </defs>
        </svg>
        <div class="hero-molecule-icon">
          <svg width="52" height="52" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="5" stroke="#38bdf8" stroke-width="1.5"/>
            <circle cx="12" cy="5" r="2.2" fill="#a78bfa"/>
            <circle cx="19" cy="12" r="1.8" fill="#4ade80"/>
            <circle cx="12" cy="19" r="1.8" fill="#fbbf24"/>
          </svg>
        </div>
        <div class="hero-orbit-dot hero-orbit-1"></div>
        <div class="hero-orbit-dot hero-orbit-2"></div>
        <div class="hero-orbit-dot hero-orbit-3"></div>
        <div class="hero-orbit-dot hero-orbit-4"></div>
      </div>
    </div>
  </div>
</div>
<script>
(function(){{
  var counters=document.querySelectorAll('.hero-stat-num[data-count]');
  if(!counters.length)return;
  if(window.__heroCounted){{counters.forEach(function(e){{e.textContent=(+e.getAttribute('data-count')).toLocaleString();}});return;}}
  window.__heroCounted=true;
  var obs=new IntersectionObserver(function(entries){{
    entries.forEach(function(entry){{
      if(!entry.isIntersecting)return;
      var el=entry.target,target=parseInt(el.getAttribute('data-count'),10);
      if(isNaN(target))return; obs.unobserve(el);
      var dur=1200,start=performance.now();
      (function tick(now){{
        var p=Math.min((now-start)/dur,1),ease=1-Math.pow(1-p,3);
        el.textContent=Math.round(ease*target).toLocaleString();
        if(p<1)requestAnimationFrame(tick);
      }})(start);
    }});
  }},{{threshold:0.3}});
  counters.forEach(function(c){{obs.observe(c);}});
}})();
</script>
"""

_FOOTER = """
<div class="app-footer">
  Adenosine Receptor Selectivity Platform &middot; Conformal Multi-Model ML &middot; 4 adenosine receptor subtypes
</div>
"""


def run_app():
    st.set_page_config(page_title="Adenosine Receptor Selectivity Predictor", layout="wide",
                       initial_sidebar_state="collapsed")

    # Initialize session state variables
    for k in ("history", "history_df", "pred"):
        if k not in st.session_state:
            st.session_state[k] = [] if k == "history" else pd.DataFrame() if k == "history_df" else None

    st.html(_CSS)
    st.html(_BACKGROUND)
    st.html(_NAVBAR)

    # Real model metrics when the evaluation report exists, else literature defaults
    rp = Path("outputs/validoutput/precise/evaluation_precise_report.json")
    m = {"r2": "0.620", "mae": "0.550", "n": "33,401",
         "A1": ["0.620", "0.580", "8,272"], "A2A": ["0.660", "0.510", "8,407"],
         "A2B": ["0.580", "0.550", "8,290"], "A3": ["0.640", "0.540", "8,432"]}
    if rp.exists():
        try:
            ed = _load_json(str(rp)) or {}
            ov = ed.get("overall", {})
            if ov.get("model_r2") is not None:
                m["r2"] = f"{ov['model_r2']:.3f}"
                m["mae"] = f"{ov['model_mae']:.3f}"
                m["n"] = f"{ed.get('n_train', 0) + ed.get('n_test', 0):,}"
            for s in SUBTYPES:
                sd = ed.get("per_subtype", {}).get(s, {})
                if sd:
                    m[s] = [f"{sd.get('model_r2', 0):.3f}", f"{sd.get('model_mae', 0):.3f}",
                            f"{sd.get('n_train', 0) + sd.get('n_test', 0):,}"]
        except Exception:
            pass

    st.html(_hero(m))

    t1, t2, t3 = st.tabs(["Single Molecule", "Batch CSV", "Model Results Hub"])
    with t1:
        render_single_predict()
    with t2:
        render_batch_predict()
    with t3:
        render_model_results()

    st.html(_FOOTER)


if __name__ == "__main__":
    run_app()
