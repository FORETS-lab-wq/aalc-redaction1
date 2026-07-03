"""
AALC-Rédaction — Application de rédaction thèse TP ECSR
Génère un rapport Word de 40-50 pages à partir des données codées dans AALC.
"""

import streamlit as st

st.set_page_config(
    page_title="AALC-Rédaction | Thèse TP ECSR",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
:root { --primary: #1B3A5C; --secondary: #2E7D9A; --accent: #E8A020; --rupture: #C0392B; --continuite: #27AE60; }
h1,h2,h3 { color: #1B3A5C; }
[data-testid="stSidebar"] { background-color: #1B3A5C; }
[data-testid="stSidebar"] * { color: #ECF0F1 !important; }
[data-testid="stSidebar"] hr { border-color: #2E4E6C; }
.these-block { background: #FAFAFA; border-left: 4px solid #2E7D9A; padding: 16px 20px; margin: 12px 0; border-radius: 0 8px 8px 0; font-family: Georgia, serif; line-height: 1.8; font-size: 14px; }
.these-block.rupture { border-left-color: #C0392B; }
.badge { display:inline-block; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600; color:white; }
.stat-box { background: white; border: 1px solid #E0E0E0; border-radius: 8px; padding: 12px; text-align:center; }
</style>
""", unsafe_allow_html=True)

import modules.page_import as page_import
import modules.page_individuel as page_individuel
import modules.page_longitudinal as page_longitudinal
import modules.page_transversal as page_transversal
import modules.page_synthese as page_synthese
import modules.page_export as page_export

PAGES = {
    "🏠 Accueil & Import":        page_import,
    "👤 Traitement individuel":   page_individuel,
    "📈 Analyse longitudinale":   page_longitudinal,
    "⚖️ Analyse transversale":    page_transversal,
    "📋 Synthèse & Hypothèse 2":  page_synthese,
    "📄 Export Word (.docx)":     page_export,
}

with st.sidebar:
    st.markdown("## 📝 AALC-Rédaction")
    st.markdown("*Thèse TP ECSR — Hypothèse 2*")
    st.markdown("---")
    choix = st.radio("Navigation", list(PAGES.keys()), label_visibility="collapsed")
    st.markdown("---")
    nb_ens = len(st.session_state.get("data_aalc", {}).get("enseignants", {}))
    nb_seg = sum(
        len(v.get("segments", []))
        for v in st.session_state.get("data_aalc", {}).get("enseignants", {}).values()
    )
    st.markdown(f"**Enseignants chargés :** {nb_ens}/10")
    st.markdown(f"**Segments codés :** {nb_seg}")
    nb_red = len(st.session_state.get("textes_rediges", {}))
    st.markdown(f"**Textes rédigés :** {nb_red}")
    st.markdown("---")
    st.session_state["api_key"] = st.text_input(
        "🔑 Clé API Anthropic",
        value=st.session_state.get("api_key", ""),
        type="password",
    )

# Initialisation session
for k, v in {
    "data_aalc": {},
    "textes_rediges": {},
    "api_key": "",
    "rapport_genere": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

PAGES[choix].render()
