"""
page_individuel.py
Traitement individuel : codage automatique via LLM + redaction profil + analyse.
"""

import streamlit as st
from modules.llm import appel_llm, stats_segments
import json
import re

PERE_COL = {
    "CONTEXTE_INITIAL": "#1B3A5C",
    "VECU_DISPOSITIF": "#C0392B",
    "ALIGNEMENT_THEORIQUE": "#7D3C98",
    "TRANSFORMATION_PRATIQUE": "#E8A020",
    "BILAN_REFLEXIF": "#27AE60",
}
POL_EMOJI = {"RUPTURE": "🔴", "CONTINUITE": "🟢", "AMBIGU": "⚪"}
CODES_FILS_VALIDES = [
    "EXP_PROF","FAMILIARITE_HYB","REPRESENTATION_NUM","AFFORDANCE_CULTURELLE",
    "VECU_ALTERNANCE","AUTONOMIE_APPRENANT","FREINS_INITIAUX","SIT_DEVELOPPEMENT",
    "DISTANCE_TRANSACTIONNELLE","LIEN_RELATION",
    "DECENTRATION_PEDAG","INSTRUMENTATION","TRANSFERT_PRATIQUE","GLISSEMENT_POSTURE",
    "APPORT_HYBRIDE","LIMITES_HYBRIDE",
]
PERE_MAP = {
    "EXP_PROF":"CONTEXTE_INITIAL","FAMILIARITE_HYB":"CONTEXTE_INITIAL",
    "REPRESENTATION_NUM":"CONTEXTE_INITIAL","AFFORDANCE_CULTURELLE":"CONTEXTE_INITIAL",
    "VECU_ALTERNANCE":"VECU_DISPOSITIF","AUTONOMIE_APPRENANT":"VECU_DISPOSITIF",
    "FREINS_INITIAUX":"VECU_DISPOSITIF","SIT_DEVELOPPEMENT":"VECU_DISPOSITIF",
    "DISTANCE_TRANSACTIONNELLE":"ALIGNEMENT_THEORIQUE","LIEN_RELATION":"ALIGNEMENT_THEORIQUE",
    "DECENTRATION_PEDAG":"TRANSFORMATION_PRATIQUE","INSTRUMENTATION":"TRANSFORMATION_PRATIQUE",
    "TRANSFERT_PRATIQUE":"TRANSFORMATION_PRATIQUE","GLISSEMENT_POSTURE":"TRANSFORMATION_PRATIQUE",
    "APPORT_HYBRIDE":"BILAN_REFLEXIF","LIMITES_HYBRIDE":"BILAN_REFLEXIF",
}


def _prompt_codage(id_e, verbatim):
    return """Tu es expert en Sciences de l'Education. Analyse ce verbatim d'entretien semi-directif selon la grille de codage suivante.

HYPOTHESE 2 : Le dispositif a distance expose les apprenants-enseignants a une RUPTURE de configuration des perspectives d'enseignement.

GRILLE DE CODAGE :
- CONTEXTE_INITIAL : EXP_PROF, FAMILIARITE_HYB, REPRESENTATION_NUM, AFFORDANCE_CULTURELLE
- VECU_DISPOSITIF : VECU_ALTERNANCE, AUTONOMIE_APPRENANT, FREINS_INITIAUX, SIT_DEVELOPPEMENT
- ALIGNEMENT_THEORIQUE : DISTANCE_TRANSACTIONNELLE, LIEN_RELATION
- TRANSFORMATION_PRATIQUE : DECENTRATION_PEDAG, INSTRUMENTATION, TRANSFERT_PRATIQUE, GLISSEMENT_POSTURE
- BILAN_REFLEXIF : APPORT_HYBRIDE, LIMITES_HYBRIDE

POLARITE : RUPTURE (reconfiguration des perspectives) | CONTINUITE | AMBIGU

VERBATIM de """ + id_e + """ :
""" + verbatim[:5000] + """

Retourne UNIQUEMENT ce JSON sans texte avant ou apres :
{"segments":[{"extrait":"citation exacte max 200 caracteres","code_fils":"CODE","code_pere":"PERE","polarite":"RUPTURE|CONTINUITE|AMBIGU","justification":"1 phrase de justification theorique"}]}"""


def _prompt_profil(id_e, p, verbatim, stats):
    return """Tu es chercheur en Sciences de l'Education et rediges une these de doctorat sur la formation des enseignants de la conduite (TP ECSR).

Redige le profil academique de l'enseignant """ + id_e + """ intégrable dans une these.

DONNEES :
- Groupe : """ + p.get("groupe","?") + """ (""" + ("expose a la FOAD" if p.get("groupe")=="Hybride" else "formation 100% presentielle") + """)
- Anciennete : """ + p.get("anciennete","?") + """
- Niveau numerique : """ + p.get("niveau_num","?") + """
- Phase entretien : """ + p.get("phase","?") + """
- Segments codes : """ + str(stats["n"]) + """ total, """ + str(stats["nR"]) + """ ruptures (""" + str(stats["pct_r"]) + """%)

DEBUT DU VERBATIM :
""" + verbatim[:2000] + """

Redige 3 paragraphes academiques :
1. Profil socioprofessionnel et parcours
2. Rapport initial au numerique et a la formation
3. Positionnement vis-a-vis de l'Hypothese 2 (rupture ou continuite attendue)

Style these de doctorat, 3e personne, references a Pratt (1998) pour les perspectives d'enseignement."""


def _prompt_analyse(id_e, p, segs, stats):
    detail = ""
    peres = ["CONTEXTE_INITIAL","VECU_DISPOSITIF","ALIGNEMENT_THEORIQUE","TRANSFORMATION_PRATIQUE","BILAN_REFLEXIF"]
    for pere in peres:
        sub = [s for s in segs if s.get("code_pere")==pere]
        if sub:
            detail += "\n" + pere + " :\n"
            for s in sub:
                detail += "  [" + s.get("code_fils","?") + "] " + s.get("polarite","?") + " : " + s.get("extrait","")[:120] + "\n"

    return """Tu es chercheur en Sciences de l'Education. Redige l'analyse individuelle complete de """ + id_e + """ pour une these de doctorat.

PROFIL : """ + p.get("groupe","?") + """ | """ + p.get("anciennete","?") + """ | Phase : """ + p.get("phase","?") + """
STATISTIQUES : """ + str(stats["n"]) + """ segments - """ + str(stats["nR"]) + """ ruptures (""" + str(stats["pct_r"]) + """%) - """ + str(stats["nC"]) + """ continuites

SEGMENTS CODES :
""" + detail + """

Redige une analyse structuree en 5 parties :
1. Contexte initial et perspectives d'enseignement (Pratt, 1998)
2. Vecu du dispositif hybride - marqueurs de rupture (Vygotski, Bruner)
3. Distance transactionnelle percue (Moore, 1997)
4. Transformation des pratiques et glissements de posture (Bucheton & Soule, 2009 ; Rabardel, 1995)
5. Bilan reflexif et reponse a l'Hypothese 2 (Schon, 1983)

- Citer les extraits du verbatim entre guillemets
- References APA 7 integrees
- 4 a 6 paragraphes par partie
- Style these de doctorat, 3e personne, francais academique"""


def _coder_verbatim(id_e, verbatim):
    """Appelle le LLM pour coder le verbatim et retourne les segments."""
    reponse = appel_llm(_prompt_codage(id_e, verbatim), max_tokens=3000)
    # Nettoyer la reponse
    reponse = reponse.strip()
    reponse = re.sub(r"```json|```", "", reponse).strip()
    data = json.loads(reponse)
    segs = []
    for s in data.get("segments", []):
        fils = s.get("code_fils","")
        if fils not in CODES_FILS_VALIDES:
            continue
        segs.append({
            "extrait": s.get("extrait","")[:300],
            "code_fils": fils,
            "code_pere": s.get("code_pere", PERE_MAP.get(fils,"?")),
            "polarite": s.get("polarite","AMBIGU").upper(),
            "justification": s.get("justification",""),
            "valide": True,
        })
    return segs


def render():
    st.markdown("# Traitement individuel")

    data = st.session_state.get("data_aalc", {})
    ens_dict = data.get("enseignants", {})
    if not ens_dict:
        st.warning("Aucun verbatim charge. Allez dans Accueil & Import.")
        return

    api_key = st.session_state.get("api_key","")
    if not api_key:
        st.warning("Cle API Anthropic manquante — renseignez-la dans la barre laterale.")

    ids = sorted(ens_dict.keys())
    onglets = st.tabs(ids)

    for i, id_e in enumerate(ids):
        with onglets[i]:
            d = ens_dict[id_e]
            p = d.get("profil",{})
            segs = d.get("segments",[])
            verbatim = d.get("verbatim","")
            stats = stats_segments(segs)

            # Metriques
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Groupe", p.get("groupe","—"))
            c2.metric("Segments", stats["n"])
            c3.metric("Rupture", str(stats["nR"]) + " (" + str(stats["pct_r"]) + "%)")
            c4.metric("Continuite", stats["nC"])

            # ETAPE 1 : Codage automatique
            st.markdown("---")
            st.markdown("#### Etape 1 — Codage automatique du verbatim")
            if segs:
                st.success(str(len(segs)) + " segments codes. Vous pouvez regenerer ou passer a l'etape 2.")
                with st.expander("Voir les segments codes"):
                    for s in segs:
                        pol = s.get("polarite","AMBIGU")
                        st.markdown(
                            POL_EMOJI.get(pol,"") + " **[" + s.get("code_fils","?") + "]** " + pol + "  \n" +
                            "*« " + s.get("extrait","")[:200] + " »*"
                        )
                col_a, col_b = st.columns([1,4])
                with col_a:
                    if st.button("Recoder", key="recod_"+id_e, disabled=not api_key):
                        with st.spinner("Codage de " + id_e + "..."):
                            try:
                                nouveaux = _coder_verbatim(id_e, verbatim)
                                st.session_state["data_aalc"]["enseignants"][id_e]["segments"] = nouveaux
                                st.success(str(len(nouveaux)) + " segments.")
                                st.rerun()
                            except Exception as e:
                                st.error("Erreur : " + str(e))
            else:
                if not verbatim:
                    st.info("Pas de verbatim charge pour " + id_e)
                else:
                    st.info("Verbatim charge (" + str(len(verbatim)) + " caracteres). Lancez le codage.")
                    if st.button("Coder le verbatim via LLM", key="cod_"+id_e, disabled=not api_key, type="primary"):
                        with st.spinner("Codage de " + id_e + " en cours..."):
                            try:
                                nouveaux = _coder_verbatim(id_e, verbatim)
                                st.session_state["data_aalc"]["enseignants"][id_e]["segments"] = nouveaux
                                st.success(str(len(nouveaux)) + " segments codes !")
                                st.rerun()
                            except Exception as e:
                                st.error("Erreur codage : " + str(e))

            # ETAPE 2 : Profil
            st.markdown("---")
            st.markdown("#### Etape 2 — Profil redige")
            cle_profil = "profil_" + id_e
            if cle_profil in st.session_state.get("textes_rediges",{}):
                st.markdown(st.session_state["textes_rediges"][cle_profil])
                if st.button("Regenerer le profil", key="regen_p_"+id_e, disabled=not api_key):
                    del st.session_state["textes_rediges"][cle_profil]
                    st.rerun()
            else:
                if st.button("Generer le profil de " + id_e, key="gen_p_"+id_e, disabled=not api_key):
                    with st.spinner("Redaction du profil de " + id_e + "..."):
                        try:
                            segs_actuels = st.session_state["data_aalc"]["enseignants"][id_e].get("segments",[])
                            stats_act = stats_segments(segs_actuels)
                            texte = appel_llm(_prompt_profil(id_e, p, verbatim, stats_act), max_tokens=1500)
                            st.session_state.setdefault("textes_rediges",{})[cle_profil] = texte
                            st.rerun()
                        except Exception as e:
                            st.error("Erreur : " + str(e))

            # ETAPE 3 : Analyse individuelle
            st.markdown("---")
            st.markdown("#### Etape 3 — Analyse individuelle complete")
            cle_analyse = "individuel_" + id_e
            segs_actuels = st.session_state["data_aalc"]["enseignants"][id_e].get("segments",[])
            if cle_analyse in st.session_state.get("textes_rediges",{}):
                texte = st.session_state["textes_rediges"][cle_analyse]
                for ligne in texte.split("\n"):
                    if ligne.strip():
                        st.markdown(ligne)
                col_a, col_b = st.columns([1,1])
                with col_a:
                    if st.button("Regenerer l'analyse", key="regen_a_"+id_e, disabled=not api_key):
                        del st.session_state["textes_rediges"][cle_analyse]
                        st.rerun()
                with col_b:
                    st.download_button(
                        "Telecharger .txt",
                        data=texte.encode("utf-8"),
                        file_name="analyse_"+id_e+".txt",
                        mime="text/plain",
                        key="dl_a_"+id_e,
                    )
            else:
                if not segs_actuels:
                    st.info("Codez d'abord le verbatim (Etape 1) pour generer l'analyse.")
                else:
                    if st.button("Generer l'analyse de " + id_e, key="gen_a_"+id_e, disabled=not api_key, type="primary"):
                        with st.spinner("Analyse de " + id_e + " (30-60s)..."):
                            try:
                                stats_act = stats_segments(segs_actuels)
                                texte = appel_llm(_prompt_analyse(id_e, p, segs_actuels, stats_act), max_tokens=4000)
                                st.session_state.setdefault("textes_rediges",{})[cle_analyse] = texte
                                st.rerun()
                            except Exception as e:
                                st.error("Erreur : " + str(e))

    # Generer tout
    st.markdown("---")
    st.markdown("### Generer toutes les analyses en une fois")
    col_btn, col_info = st.columns([1,3])
    with col_btn:
        if st.button("Tout generer (x10)", disabled=not api_key, type="primary"):
            prog = st.progress(0)
            for i, id_e in enumerate(ids):
                d = ens_dict[id_e]
                p = d.get("profil",{})
                verbatim = d.get("verbatim","")
                if not verbatim:
                    prog.progress((i+1)/len(ids))
                    continue
                # Codage
                segs = st.session_state["data_aalc"]["enseignants"][id_e].get("segments",[])
                if not segs:
                    with st.spinner("Codage " + id_e + "..."):
                        try:
                            segs = _coder_verbatim(id_e, verbatim)
                            st.session_state["data_aalc"]["enseignants"][id_e]["segments"] = segs
                        except Exception as e:
                            st.error(id_e + " codage : " + str(e))
                            prog.progress((i+1)/len(ids))
                            continue
                stats = stats_segments(segs)
                # Profil
                cle_p = "profil_" + id_e
                if cle_p not in st.session_state.get("textes_rediges",{}):
                    with st.spinner("Profil " + id_e + "..."):
                        try:
                            st.session_state.setdefault("textes_rediges",{})[cle_p] = appel_llm(
                                _prompt_profil(id_e, p, verbatim, stats), max_tokens=1500
                            )
                        except Exception as e:
                            st.error(id_e + " profil : " + str(e))
                # Analyse
                cle_a = "individuel_" + id_e
                if cle_a not in st.session_state.get("textes_rediges",{}):
                    with st.spinner("Analyse " + id_e + "..."):
                        try:
                            st.session_state.setdefault("textes_rediges",{})[cle_a] = appel_llm(
                                _prompt_analyse(id_e, p, segs, stats), max_tokens=4000
                            )
                        except Exception as e:
                            st.error(id_e + " analyse : " + str(e))
                prog.progress((i+1)/len(ids))
            st.success("Toutes les analyses generees !")
            st.rerun()
    with col_info:
        st.info("Code + profil + analyse pour les " + str(len(ids)) + " enseignants. Comptez 2-3 min par enseignant.")
