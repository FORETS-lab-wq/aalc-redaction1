"""
page_synthese.py
Synthèse globale et réponse à l'Hypothèse 2 — section finale de la thèse.
"""

import streamlit as st
from modules.llm import appel_llm, stats_segments


def _prompt_synthese(ens_dict: dict, textes: dict) -> str:
    # Résumés des analyses individuelles
    resumes = []
    for id_e in sorted(ens_dict.keys()):
        p = ens_dict[id_e].get("profil", {})
        segs = ens_dict[id_e].get("segments", [])
        st_e = stats_segments(segs)
        t_ind = textes.get(f"individuel_{id_e}", "")
        # Extraire les 300 derniers caractères (bilan) de l'analyse individuelle
        extrait_bilan = t_ind[-400:] if t_ind else "Non généré."
        resumes.append(
            f"{id_e} ({p.get('groupe','?')}, {p.get('anciennete','?')}) — "
            f"{st_e['nR']}/{st_e['n']} ruptures ({st_e['pct_r']}%)\n"
            f"Bilan individuel (extrait) : {extrait_bilan}"
        )

    # Résumé transversal
    trans = textes.get("transversal", "")
    extrait_trans = trans[-600:] if trans else "Non généré."

    # Stats globales
    all_segs = [s for d in ens_dict.values() for s in d.get("segments", [])]
    st_glob = stats_segments(all_segs)
    nb_H = sum(1 for d in ens_dict.values() if d.get("profil",{}).get("groupe")=="Hybride")
    nb_T = sum(1 for d in ens_dict.values() if d.get("profil",{}).get("groupe")=="Traditionnel")

    return f"""Rédige la SYNTHÈSE GLOBALE et la RÉPONSE À L'HYPOTHÈSE 2 pour une thèse de doctorat en Sciences de l'Éducation portant sur la formation des enseignants de la conduite automobile (TP ECSR).

Cette synthèse constitue la section conclusive de l'analyse empirique de la thèse.

HYPOTHÈSE 2 : "Le dispositif suivi à distance expose les apprenants-enseignants à une rupture de configuration des perspectives d'enseignement."

DONNÉES GLOBALES :
- N = {len(ens_dict)} enseignants (Hybride : {nb_H}, Traditionnel : {nb_T})
- Total segments codés : {st_glob['n']}
- Ruptures globales : {st_glob['nR']} ({st_glob['pct_r']}%)
- Continuités : {st_glob['nC']}
- Distribution par nœud : {st_glob['peres']}

BILANS INDIVIDUELS (résumés) :
{chr(10).join(resumes)}

EXTRAIT DE L'ANALYSE TRANSVERSALE :
{extrait_trans}

STRUCTURE ATTENDUE DE LA SYNTHÈSE (section de thèse de 8 à 12 pages) :

### 1. Rappel de la problématique et de l'Hypothèse 2
Resituer brièvement l'Hypothèse 2 dans la problématique générale de la thèse : le dispositif hybride en formation initiale des ECSR, les enjeux de reconfiguration des perspectives d'enseignement (Pratt, 1998) et des postures d'étayage (Bucheton & Soulé, 2009).

### 2. Convergences et divergences entre les cas individuels
Identifier les tendances communes aux 10 enseignants : quels nœuds concentrent le plus de ruptures ? Quels profils sont les plus touchés par la reconfiguration ? Y a-t-il des facteurs modérateurs (ancienneté, niveau numérique, genre) ?

### 3. La rupture comme processus différentiel : entre exposition et réception
Analyser pourquoi certains enseignants du groupe Hybride montrent plus de rupture que d'autres. Mobiliser la notion de distance transactionnelle (Moore, 1997) et de zone proximale de développement (Vygotski, 1934) pour expliquer ces différences.

### 4. Reconfigurations des postures d'étayage : du Contrôleur à l'Accompagnateur ?
Synthétiser les glissements de postures observés (Bucheton & Soulé, 2009) dans l'ensemble du corpus. La FOAD favorise-t-elle un déplacement vers des postures plus accompagnatrices ? Nuancer selon les cas.

### 5. Réponse à l'Hypothèse 2
Formuler une réponse argumentée, nuancée et étayée à l'Hypothèse 2. Trois positions possibles à articuler :
- Confirmation : la FOAD produit bien une rupture des perspectives chez le groupe Hybride
- Nuance : rupture partielle, conditionnelle, ou différentielle selon les profils
- Complexification : la rupture n'est pas uniforme — elle dépend de l'intensité de la distance transactionnelle et du degré d'autonomie de l'apprenant

### 6. Implications pour la formation et la recherche
Tirer les implications pratiques (ingénierie de la formation des ECSR, REMC 2013) et théoriques (contribution à la littérature sur la FOAD en formation professionnelle).

### 7. Limites et perspectives
Reconnaître les limites de l'étude (N=10, design qualitatif, biais de désirabilité) et ouvrir sur des perspectives de recherche.

CONSIGNES :
- Section de thèse complète, style doctoral soutenu
- Références APA 7 systématiques (Moore, 1997 ; Pratt, 1998 ; Vygotski, 1934 ; Bruner, 1983 ; Bucheton & Soulé, 2009 ; Schön, 1983 ; Rabardel, 1995 ; Hernja ; Mayen ; Boccara)
- Citations des verbatims entre « guillemets français » pour illustrer
- 6 à 10 paragraphes par partie
- Ton conclusif mais nuancé — ne pas sur-affirmer
- Longueur visée : équivalent 8 à 12 pages Word"""


def render():
    st.markdown("# 📋 Synthèse globale & Hypothèse 2")
    st.markdown(
        "Génère la section conclusive de l'analyse empirique : synthèse des 10 cas "
        "et réponse argumentée à l'Hypothèse 2."
    )

    data     = st.session_state.get("data_aalc", {})
    ens_dict = data.get("enseignants", {})
    textes   = st.session_state.get("textes_rediges", {})
    api_key  = st.session_state.get("api_key", "")

    if not ens_dict:
        st.warning("⚠️ Aucune donnée chargée.")
        return

    # ── Vérification des pré-requis ───────────────────────────────────────────
    nb_ind  = sum(1 for id_e in ens_dict if f"individuel_{id_e}" in textes)
    nb_long = sum(1 for id_e in ens_dict if f"longitudinal_{id_e}" in textes)
    has_trans = "transversal" in textes

    st.markdown("### Avancement des analyses")
    col1, col2, col3 = st.columns(3)
    col1.metric("Analyses individuelles", f"{nb_ind}/{len(ens_dict)}")
    col2.metric("Analyses longitudinales", f"{nb_long}/{len(ens_dict)}")
    col3.metric("Analyse transversale", "✅" if has_trans else "⬜ non générée")

    if nb_ind < len(ens_dict):
        st.warning(
            f"⚠️ {len(ens_dict) - nb_ind} analyse(s) individuelle(s) manquante(s). "
            "La synthèse sera moins précise sans elles — vous pouvez quand même la générer."
        )

    st.markdown("---")

    # ── Génération ───────────────────────────────────────────────────────────
    cle = "synthese"
    if cle in textes:
        st.markdown("#### Synthèse globale rédigée")
        texte = textes[cle]
        # Affichage structuré
        for ligne in texte.split("\n"):
            if ligne.startswith("### "):
                st.markdown(f"**{ligne[4:]}**")
            elif ligne.strip():
                st.markdown(
                    f'<div class="these-block" style="font-family:Georgia,serif;line-height:1.9">'
                    f'{ligne}</div>',
                    unsafe_allow_html=True,
                )

        col_a, col_b, col_c = st.columns([1, 1, 4])
        with col_a:
            if st.button("🔄 Regénérer"):
                del st.session_state["textes_rediges"][cle]
                st.rerun()
        with col_b:
            st.download_button(
                "⬇️ .txt",
                data=texte.encode("utf-8"),
                file_name="synthese_hypothese2.txt",
                mime="text/plain",
            )
    else:
        st.markdown(
            "La synthèse mobilise l'ensemble des analyses générées "
            "(individuelles + longitudinales + transversale) pour produire "
            "une réponse argumentée à l'Hypothèse 2."
        )
        if st.button(
            "✍️ Générer la synthèse globale",
            disabled=not api_key,
            type="primary",
        ):
            with st.spinner("Rédaction de la synthèse globale (60-120s)…"):
                try:
                    texte = appel_llm(
                        _prompt_synthese(ens_dict, textes),
                        max_tokens=8000,
                    )
                    st.session_state["textes_rediges"][cle] = texte
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")
