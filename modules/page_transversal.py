"""
page_transversal.py
Analyse transversale : comparaison Hybride vs Traditionnel.
Texte académique structuré pour la thèse.
"""

import streamlit as st
import plotly.express as px
import pandas as pd
from modules.llm import appel_llm, segments_vers_texte, stats_segments

PERES = ["CONTEXTE_INITIAL","VECU_DISPOSITIF","ALIGNEMENT_THEORIQUE","TRANSFORMATION_PRATIQUE","BILAN_REFLEXIF"]
PERE_COL = {"CONTEXTE_INITIAL":"#1B3A5C","VECU_DISPOSITIF":"#C0392B","ALIGNEMENT_THEORIQUE":"#7D3C98","TRANSFORMATION_PRATIQUE":"#E8A020","BILAN_REFLEXIF":"#27AE60"}


def _stats_groupe(ens_dict: dict, groupe: str) -> dict:
    membres = {id_e: d for id_e, d in ens_dict.items() if d.get("profil",{}).get("groupe")==groupe}
    all_segs = []
    for d in membres.values():
        all_segs.extend(d.get("segments", []))
    st = stats_segments(all_segs)
    st["membres"] = list(membres.keys())
    st["segs_par_ens"] = {id_e: d.get("segments",[]) for id_e, d in membres.items()}
    return st


def _prompt_transversal(ens_dict: dict, stats_H: dict, stats_T: dict) -> str:
    # Extraits représentatifs de rupture pour le groupe Hybride
    segs_R_H = [s for id_e in stats_H["membres"] for s in ens_dict[id_e].get("segments",[]) if s.get("polarite")=="RUPTURE"][:8]
    segs_R_T = [s for id_e in stats_T["membres"] for s in ens_dict[id_e].get("segments",[]) if s.get("polarite")=="RUPTURE"][:4]
    # Extraits par nœud pour comparaison
    detail_H = {}
    detail_T = {}
    for pere in PERES:
        detail_H[pere] = [s for id_e in stats_H["membres"] for s in ens_dict[id_e].get("segments",[]) if s.get("code_pere")==pere][:3]
        detail_T[pere] = [s for id_e in stats_T["membres"] for s in ens_dict[id_e].get("segments",[]) if s.get("code_pere")==pere][:3]

    def fmt(segs): return segments_vers_texte(segs) if segs else "Aucun segment disponible."

    return f"""Rédige l'ANALYSE TRANSVERSALE comparative pour une thèse de doctorat en Sciences de l'Éducation.

HYPOTHÈSE 2 : "Le dispositif suivi à distance expose les apprenants-enseignants à une rupture de configuration des perspectives d'enseignement."

GROUPE HYBRIDE (n={len(stats_H['membres'])}) : {', '.join(stats_H['membres'])}
- {stats_H['n']} segments total — {stats_H['nR']} ruptures ({stats_H['pct_r']}%) — {stats_H['nC']} continuités
- Distribution : {stats_H['peres']}

GROUPE TRADITIONNEL (n={len(stats_T['membres'])}) : {', '.join(stats_T['membres'])}
- {stats_T['n']} segments total — {stats_T['nR']} ruptures ({stats_T['pct_r']}%) — {stats_T['nC']} continuités
- Distribution : {stats_T['peres']}

EXTRAITS DE RUPTURE — GROUPE HYBRIDE :
{fmt(segs_R_H)}

EXTRAITS DE RUPTURE — GROUPE TRADITIONNEL :
{fmt(segs_R_T)}

COMPARAISON NŒUD PAR NŒUD :

CONTEXTE_INITIAL :
Hybride : {fmt(detail_H['CONTEXTE_INITIAL'])}
Traditionnel : {fmt(detail_T['CONTEXTE_INITIAL'])}

VECU_DISPOSITIF :
Hybride : {fmt(detail_H['VECU_DISPOSITIF'])}
Traditionnel : {fmt(detail_T['VECU_DISPOSITIF'])}

ALIGNEMENT_THEORIQUE :
Hybride : {fmt(detail_H['ALIGNEMENT_THEORIQUE'])}
Traditionnel : {fmt(detail_T['ALIGNEMENT_THEORIQUE'])}

TRANSFORMATION_PRATIQUE :
Hybride : {fmt(detail_H['TRANSFORMATION_PRATIQUE'])}
Traditionnel : {fmt(detail_T['TRANSFORMATION_PRATIQUE'])}

BILAN_REFLEXIF :
Hybride : {fmt(detail_H['BILAN_REFLEXIF'])}
Traditionnel : {fmt(detail_T['BILAN_REFLEXIF'])}

STRUCTURE ATTENDUE DE L'ANALYSE TRANSVERSALE :

### 1. Introduction comparative : deux groupes, deux expériences
Présenter les deux groupes et leur différence fondamentale (exposition à la FOAD vs présentiel exclusif). Poser l'enjeu comparatif vis-à-vis de l'Hypothèse 2.

### 2. Comparaison des contextes initiaux et des perspectives d'enseignement de départ
Comparer les perspectives d'enseignement initiales (Pratt, 1998) des deux groupes. Différences et similitudes dans le rapport au numérique, la familiarité avec l'hybride.

### 3. Spécificité du vécu de la distance pour le groupe Hybride
Analyser ce que le groupe Hybride a vécu de spécifique dans la FOAD. Comparer avec le groupe Traditionnel : distance transactionnelle (Moore, 1997), autonomie, freins. Identifier les marqueurs de rupture propres au groupe Hybride.

### 4. Différenciations dans les transformations des pratiques et postures
Comparer les transformations des postures d'étayage (Bucheton & Soulé, 2009) entre les deux groupes. Le groupe Hybride présente-t-il des glissements plus marqués ? L'instrumentation (Rabardel, 1995) est-elle différentielle ?

### 5. Bilans réflexifs comparés
Comparer les bilans des deux groupes. Le groupe Hybride fait-il état d'une reconfiguration plus profonde de ses perspectives ?

### 6. Discussion et réponse à l'Hypothèse 2
Synthétiser les résultats comparatifs. Argumenter la réponse à l'Hypothèse 2 : le dispositif à distance produit-il effectivement une rupture spécifique ? Nuancer si nécessaire. Articuler avec le cadre de Moore (1997), Vygotski et Schön (1983).

CONSIGNES :
- Comparaisons systématiques Hybride/Traditionnel dans chaque partie
- Citations des verbatims entre « guillemets français »
- Références APA 7 intégrées
- 5 à 7 paragraphes par partie
- Conclure fermement sur la validité/invalidité/nuance de l'Hypothèse 2"""


def render():
    st.markdown("# ⚖️ Analyse transversale")
    st.markdown(
        "Comparaison Hybride vs Traditionnel — génère le texte académique "
        "argumentant la réponse à l'Hypothèse 2."
    )

    data = st.session_state.get("data_aalc", {})
    ens_dict = data.get("enseignants", {})
    if not ens_dict:
        st.warning("⚠️ Aucune donnée chargée.")
        return

    api_key = st.session_state.get("api_key", "")

    stats_H = _stats_groupe(ens_dict, "Hybride")
    stats_T = _stats_groupe(ens_dict, "Traditionnel")

    # ── Métriques comparatives ────────────────────────────────────────────────
    st.markdown("### Comparaison quantitative")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"#### Groupe Hybride (n={len(stats_H['membres'])})")
        st.markdown(f"Membres : {', '.join(stats_H['membres']) or '—'}")
        c1,c2,c3 = st.columns(3)
        c1.metric("Segments", stats_H["n"])
        c2.metric("🔴 Rupture", f"{stats_H['nR']} ({stats_H['pct_r']}%)")
        c3.metric("🟢 Continuité", stats_H["nC"])

    with col2:
        st.markdown(f"#### Groupe Traditionnel (n={len(stats_T['membres'])})")
        st.markdown(f"Membres : {', '.join(stats_T['membres']) or '—'}")
        c1,c2,c3 = st.columns(3)
        c1.metric("Segments", stats_T["n"])
        c2.metric("🔴 Rupture", f"{stats_T['nR']} ({stats_T['pct_r']}%)")
        c3.metric("🟢 Continuité", stats_T["nC"])

    # ── Graphique comparatif ──────────────────────────────────────────────────
    if stats_H["n"] or stats_T["n"]:
        lignes = []
        for groupe, st_g in [("Hybride", stats_H), ("Traditionnel", stats_T)]:
            for pol, n in [("RUPTURE", st_g["nR"]), ("CONTINUITE", st_g["nC"]), ("AMBIGU", st_g["nA"])]:
                lignes.append({"Groupe": groupe, "Polarité": pol, "N": n})
        df = pd.DataFrame(lignes)
        fig = px.bar(
            df, x="Groupe", y="N", color="Polarité",
            color_discrete_map={"RUPTURE":"#C0392B","CONTINUITE":"#27AE60","AMBIGU":"#888"},
            barmode="group", template="plotly_white",
            title="Distribution des polarités par groupe",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Signal H2
        if stats_H["n"] and stats_T["n"]:
            if stats_H["pct_r"] > stats_T["pct_r"]:
                st.success(
                    f"✅ Le groupe Hybride présente un taux de rupture supérieur "
                    f"({stats_H['pct_r']}% vs {stats_T['pct_r']}%) — "
                    f"résultat congruent avec l'Hypothèse 2."
                )
            else:
                st.warning(
                    f"⚠️ Le groupe Traditionnel présente un taux de rupture comparable ou supérieur "
                    f"({stats_T['pct_r']}% vs {stats_H['pct_r']}%) — "
                    f"l'Hypothèse 2 devra être nuancée."
                )

    st.markdown("---")

    # ── Génération du texte ───────────────────────────────────────────────────
    cle = "transversal"
    if cle in st.session_state["textes_rediges"]:
        st.markdown("#### Analyse transversale rédigée")
        texte = st.session_state["textes_rediges"][cle]
        st.markdown(
            f'<div class="these-block" style="font-family:Georgia,serif;line-height:1.9">'
            f'{texte.replace(chr(10),"<br>")}</div>',
            unsafe_allow_html=True,
        )
        col_a, col_b, col_c = st.columns([1, 1, 4])
        with col_a:
            if st.button("🔄 Regénérer", key="regen_trans"):
                del st.session_state["textes_rediges"][cle]
                st.rerun()
        with col_b:
            st.download_button(
                "⬇️ .txt",
                data=texte.encode("utf-8"),
                file_name="analyse_transversale.txt",
                mime="text/plain",
            )
    else:
        if not (stats_H["membres"] or stats_T["membres"]):
            st.info("Aucun enseignant chargé avec groupe renseigné.")
        else:
            if st.button(
                "✍️ Générer l'analyse transversale",
                disabled=not api_key,
                type="primary",
            ):
                with st.spinner("Rédaction de l'analyse transversale (60-90s)…"):
                    try:
                        texte = appel_llm(
                            _prompt_transversal(ens_dict, stats_H, stats_T),
                            max_tokens=6000,
                        )
                        st.session_state["textes_rediges"][cle] = texte
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")
