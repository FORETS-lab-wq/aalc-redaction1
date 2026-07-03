import streamlit as st

st.set_page_config(
    page_title="AALC-Redaction | These TP ECSR",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

import modules.page_import as page_import
import modules.page_individuel as page_individuel
import modules.page_longitudinal as page_longitudinal
import modules.page_transversal as page_transversal
import modules.page_synthese as page_synthese
import modules.page_export as page_export

PAGES = {
    "Accueil & Import":       page_import,
    "Traitement individuel":  page_individuel,
    "Analyse longitudinale":  page_longitudinal,
    "Analyse transversale":   page_transversal,
    "Synthese & Hypothese 2": page_synthese,
    "Export Word":            page_export,
}

for k, v in {
    "data_aalc": {},
    "textes_rediges": {},
    "api_key": "",
    "rapport_genere": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

with st.sidebar:
    st.markdown("## AALC-Redaction")
    st.markdown("---")
    choix = st.radio("Navigation", list(PAGES.keys()), label_visibility="collapsed")
    st.markdown("---")
    nb_ens = len(st.session_state.get("data_aalc", {}).get("enseignants", {}))
    nb_seg = sum(
        len(v.get("segments", []))
        for v in st.session_state.get("data_aalc", {}).get("enseignants", {}).values()
    )
    st.markdown(f"**Enseignants :** {nb_ens}/10")
    st.markdown(f"**Segments :** {nb_seg}")
    st.markdown(f"**Textes rediges :** {len(st.session_state.get('textes_rediges', {}))}")
    st.markdown("---")
    st.session_state["api_key"] = st.text_input(
        "Cle API Anthropic",
        value=st.session_state.get("api_key", ""),
        type="password",
    )

PAGES[choix].render()
