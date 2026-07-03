"""
page_individuel.py
Module de traitement individuel : génère pour chaque enseignant
1. Profil rédigé
2. Analyse de ses segments par nœud
3. Positionnement vis-à-vis de l'Hypothèse 2
"""

import streamlit as st
from modules.llm import appel_llm, segments_vers_texte, stats_segments

PERE_COL = {
    "CONTEXTE_INITIAL": "#1B3A5C",
    "VECU_DISPOSITIF": "#C0392B",
    "ALIGNEMENT_THEORIQUE": "#7D3C98",
    "TRANSFORMATION_PRATIQUE": "#E8A020",
    "BILAN_REFLEXIF": "#27AE60",
}
POL_EMOJI = {"RUPTURE": "🔴", "CONTINUITE": "🟢", "AMBIGU": "⚪"}


def _prompt_profil(id_e: str, p: dict, segs: list, stats: dict) -> str:
    extraits = segments_vers_texte(segs[:5])
    return f"""Rédige le profil académique de l'enseignant {id_e} pour une thèse de doctorat en Sciences de l'Éducation.

DONNÉES :
- Identifiant : {id_e}
- Groupe : {p.get('groupe','?')} ({"exposé à la FOAD" if p.get('groupe')=='Hybride' else "formation 100% présentielle"})
- Ancienneté : {p.get('anciennete','?')}
- Formation visée : {p.get('type_formation','TP ECSR')}
- Niveau numérique auto-déclaré : {p.get('niveau_num','?')}
- Genre : {p.get('genre','Non renseigné')}
- Tranche d'âge : {p.get('age_approx','Non renseignée')}
- Phase de l'entretien : {p.get('phase','?')}
- Organisme : {p.get('organisme','?')}
- Notes : {p.get('notes','—')}
- Segments codés : {stats['n']} total — {stats['nR']} ruptures ({stats['pct_r']}%), {stats['nC']} continuités

PREMIERS SEGMENTS :
{extraits}

CONSIGNES :
- 3 paragraphes denses : (1) profil socioprofessionnel, (2) rapport au numérique et à la formation, (3) positionnement initial vis-à-vis de l'Hypothèse 2
- Mobiliser Pratt (1998) pour les perspectives d'enseignement initiales
- Citer le groupe de formation et son implication théorique (Moore, 1997)
- Style thèse de doctorat, 3e personne, français académique"""


def _prompt_analyse_individuelle(id_e: str, p: dict, segs: list, stats: dict) -> str:
    seg_txt = segments_vers_texte(segs)
    return f"""Rédige l'analyse individuelle complète de l'enseignant {id_e} pour une thèse de doctorat.

PROFIL : {p.get('groupe','?')} | {p.get('anciennete','?')} | Phase : {p.get('phase','?')}
STATISTIQUES : {stats['n']} segments — {stats['nR']} ruptures ({stats['pct_r']}%) — {stats['nC']} continuités
DISTRIBUTION PAR NŒUD : {stats['peres']}

SEGMENTS CODÉS :
{seg_txt}

STRUCTURE ATTENDUE (5 parties correspondant aux 5 nœuds père) :

1. CONTEXTE INITIAL
   Présenter les perspectives d'enseignement initiales de {id_e} (Pratt, 1998).
   Analyser son rapport au numérique, sa familiarité avec l'hybride.

2. VÉCU DU DISPOSITIF
   Analyser comment {id_e} a vécu la FOAD : alternance, autonomie, freins, situations de développement.
   Mobiliser la ZPD (Vygotski) et l'étayage (Bruner).
   Identifier les premiers marqueurs de rupture ou de continuité.

3. ALIGNEMENT THÉORIQUE
   Analyser la distance transactionnelle (Moore, 1997) perçue.
   Évaluer la qualité du lien pédagogique à distance.

4. TRANSFORMATION DES PRATIQUES
   Analyser les glissements de posture (Bucheton & Soulé, 2009) : Contrôleur → Transmetteur → Accompagnateur.
   Évaluer la décentration pédagogique, l'instrumentation (Rabardel, 1995), le transfert.

5. BILAN RÉFLEXIF ET POSITIONNEMENT VIS-À-VIS DE L'HYPOTHÈSE 2
   Synthétiser les apports et limites perçus.
   Conclure sur le positionnement de {id_e} : la FOAD a-t-elle produit une rupture de ses perspectives d'enseignement ?
   Référencer l'Hypothèse 2 explicitement.

CONSIGNES :
- Citer systématiquement les extraits du verbatim entre « guillemets français »
- Références APA 7 intégrées dans le texte
- 6 à 8 paragraphes denses par partie
- Transitions argumentées entre les parties
- Conclure fermement sur la validité de l'H2 pour cet enseignant"""


def render():
    st.markdown("# 👤 Traitement individuel")
    st.markdown(
        "Génère pour chaque enseignant un profil rédigé et une analyse complète "
        "structurée par les 5 nœuds du référentiel de codage."
    )

    data = st.session_state.get("data_aalc", {})
    ens_dict = data.get("enseignants", {})

    if not ens_dict:
        st.warning("⚠️ Aucune donnée chargée. Allez dans **Accueil & Import**.")
        return

    api_key = st.session_state.get("api_key", "")
    if not api_key:
        st.warning("⚠️ Clé API Anthropic manquante — renseignez-la dans la barre latérale.")

    ids = sorted(ens_dict.keys())
    onglets = st.tabs(ids)

    for i, id_e in enumerate(ids):
        with onglets[i]:
            d    = ens_dict[id_e]
            p    = d.get("profil", {})
            segs = d.get("segments", [])
            stats = stats_segments(segs)

            # ── Métriques ───────────────────────────────────────────────────
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Groupe", p.get("groupe", "—"))
            col2.metric("Segments", stats["n"])
            col3.metric("🔴 Rupture", f"{stats['nR']} ({stats['pct_r']}%)")
            col4.metric("🟢 Continuité", stats["nC"])

            # ── Distribution visuelle ────────────────────────────────────────
            if segs:
                st.markdown("#### Distribution par nœud père")
                for pere, col in PERE_COL.items():
                    n_pere = stats["peres"].get(pere, 0)
                    n_r = sum(1 for s in segs if s.get("code_pere")==pere and s.get("polarite")=="RUPTURE")
                    pct = round(n_pere / stats["n"] * 100) if stats["n"] else 0
                    st.markdown(
                        f'<div style="margin-bottom:6px">'
                        f'<span style="font-size:11px;color:{col};font-weight:600">{pere}</span>'
                        f'<span style="font-size:11px;color:#888;margin-left:8px">{n_pere} seg. — 🔴{n_r}</span>'
                        f'<div style="height:8px;background:#F0F0F0;border-radius:4px;margin-top:2px">'
                        f'<div style="width:{pct}%;height:100%;background:{col};border-radius:4px"></div></div></div>',
                        unsafe_allow_html=True,
                    )

            # ── Verbatims par nœud ───────────────────────────────────────────
            with st.expander("Segments codés", expanded=False):
                for pere, col in PERE_COL.items():
                    segs_pere = [s for s in segs if s.get("code_pere") == pere]
                    if not segs_pere:
                        continue
                    st.markdown(
                        f'<span style="font-weight:600;color:{col}">{pere}</span>',
                        unsafe_allow_html=True,
                    )
                    for s in segs_pere:
                        pol = s.get("polarite", "AMBIGU")
                        css = "rupture" if pol == "RUPTURE" else "continuite" if pol == "CONTINUITE" else ""
                        st.markdown(
                            f'<div class="these-block {css}">'
                            f'<strong>[{s.get("code_fils","?")}]</strong> {POL_EMOJI.get(pol,"")} {pol}<br>'
                            f'<em>« {s.get("extrait","")[:250]} »</em><br>'
                            f'<small style="color:#666">↳ {s.get("justification","")}</small>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

            st.markdown("---")

            # ── Génération du profil ─────────────────────────────────────────
            st.markdown("#### 1. Profil rédigé")
            cle_profil = f"profil_{id_e}"
            if cle_profil in st.session_state["textes_rediges"]:
                st.markdown(
                    f'<div class="these-block">{st.session_state["textes_rediges"][cle_profil]}</div>',
                    unsafe_allow_html=True,
                )
                col_a, col_b = st.columns([1, 4])
                with col_a:
                    if st.button("🔄 Regénérer", key=f"regen_p_{id_e}"):
                        del st.session_state["textes_rediges"][cle_profil]
                        st.rerun()
            else:
                if st.button(f"✍️ Générer le profil de {id_e}", key=f"gen_p_{id_e}", disabled=not api_key):
                    with st.spinner(f"Rédaction du profil de {id_e}…"):
                        try:
                            texte = appel_llm(_prompt_profil(id_e, p, segs, stats), max_tokens=1500)
                            st.session_state["textes_rediges"][cle_profil] = texte
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erreur : {e}")

            st.markdown("---")

            # ── Génération de l'analyse individuelle ─────────────────────────
            st.markdown("#### 2. Analyse individuelle complète")
            cle_analyse = f"individuel_{id_e}"
            if cle_analyse in st.session_state["textes_rediges"]:
                texte = st.session_state["textes_rediges"][cle_analyse]
                # Affichage avec mise en forme des titres
                for ligne in texte.split("\n"):
                    if ligne.strip().startswith("#"):
                        st.markdown(ligne)
                    elif ligne.strip():
                        st.markdown(
                            f'<div class="these-block">{ligne}</div>',
                            unsafe_allow_html=True,
                        )
                col_a, col_b = st.columns([1, 4])
                with col_a:
                    if st.button("🔄 Regénérer", key=f"regen_a_{id_e}"):
                        del st.session_state["textes_rediges"][cle_analyse]
                        st.rerun()
            else:
                if not segs:
                    st.info("Aucun segment codé pour cet enseignant.")
                else:
                    if st.button(
                        f"✍️ Générer l'analyse de {id_e}",
                        key=f"gen_a_{id_e}",
                        disabled=not api_key,
                        type="primary",
                    ):
                        with st.spinner(f"Analyse de {id_e} en cours (peut prendre 30-60s)…"):
                            try:
                                texte = appel_llm(
                                    _prompt_analyse_individuelle(id_e, p, segs, stats),
                                    max_tokens=4000,
                                )
                                st.session_state["textes_rediges"][cle_analyse] = texte
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")

    # ── Générer tous ──────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Générer toutes les analyses en une fois")
    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        if st.button("🚀 Tout générer (×10)", disabled=not api_key, type="primary"):
            progress = st.progress(0)
            for i, id_e in enumerate(ids):
                d    = ens_dict[id_e]
                p    = d.get("profil", {})
                segs = d.get("segments", [])
                if not segs:
                    continue
                stats = stats_segments(segs)
                # Profil
                cle_p = f"profil_{id_e}"
                if cle_p not in st.session_state["textes_rediges"]:
                    with st.spinner(f"Profil {id_e}…"):
                        try:
                            st.session_state["textes_rediges"][cle_p] = appel_llm(
                                _prompt_profil(id_e, p, segs, stats), max_tokens=1500
                            )
                        except Exception as e:
                            st.error(f"{id_e} profil : {e}")
                # Analyse
                cle_a = f"individuel_{id_e}"
                if cle_a not in st.session_state["textes_rediges"]:
                    with st.spinner(f"Analyse {id_e}…"):
                        try:
                            st.session_state["textes_rediges"][cle_a] = appel_llm(
                                _prompt_analyse_individuelle(id_e, p, segs, stats), max_tokens=4000
                            )
                        except Exception as e:
                            st.error(f"{id_e} analyse : {e}")
                progress.progress((i + 1) / len(ids))
            st.success("✅ Toutes les analyses individuelles générées !")
            st.rerun()
    with col_info:
        st.info(
            f"Génère profil + analyse pour les {len(ids)} enseignants chargés. "
            "Comptez environ 1-2 minutes par enseignant."
        )
