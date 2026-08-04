# src/app/components/sidebar.py
import streamlit as st
import pandas as pd

def _tag(v, t=6.0):
    p = float(v) if v is not None else 0
    return ("tg", "Active") if p >= t else ("ta", "Weak") if p >= t - 1.5 else ("tr", "Inact")

def render_sidebar():
    with st.sidebar:
        st.markdown(f'<div style="font-size:.65rem;text-transform:uppercase;letter-spacing:.05em;color:#94a3b8;margin-bottom:.3rem">Session &middot; {len(st.session_state.history)} molecules</div>', unsafe_allow_html=True)
        if st.button("Clear", use_container_width=True):
            st.session_state.history = []
            st.session_state.history_df = pd.DataFrame()
            st.rerun()
            
        if st.session_state.history:
            for h in reversed(st.session_state.history[-8:]):
                sm = h["smiles"][:22] + ".." if len(h["smiles"]) > 22 else h["smiles"]
                c, _ = _tag(h["bv"])
                st.markdown(f'<div class="hi"><span>{sm}</span><span class="tag {c}">{h["bt"]}</span><span style="font-size:.5rem;color:#94a3b8">{h["t"]}</span></div>', unsafe_allow_html=True)
            
            if not st.session_state.history_df.empty:
                csv = st.session_state.history_df.to_csv(index=False).encode()
                st.download_button("Export CSV", csv, "ar_session.csv", use_container_width=True)
