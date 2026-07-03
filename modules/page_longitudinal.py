"""
page_longitudinal.py
Analyse longitudinale : évolution du discours de chaque enseignant
à travers les 5 nœuds du référentiel — texte rédigé de type thèse.
"""

import streamlit as st
from modules.llm import appel_llm, segments_vers_texte, stats_segments

PERES = ["CONTEXTE_INITIAL","VECU_DISPOSITIF","ALIGNEMENT_THEORIQUE","TRANSFORMATION_PRATIQUE","BILAN_REFLEXIF"]
PERE_COL = {"CONTEXTE_INITIAL":"#1B3A5C","VECU_DISPOSITIF":"#C0392B","ALIGNEMENT_THEORIQUE":"#7D3C98","TRANSFORMATION_PRATIQUE":"#E8A020","BILAN_REFLEXIF":"#27AE60"}


def _prompt_longitudinal(id_e: str, p: dict, segs: list, stats: dict) -> str:
    # Organiser les segments par nœud père
    par_pere = {pere: [s for s in segs if s.get("code_pere")==pere] for pere in PERES}
    detail = "\n\n".join(
        f"=== {pere} ({len(par_pere[pere])} segments) ===\n" + segments_vers_texte(par_pere[pere])
        for pere in PERES if par_pere[pere]
    )
    return f"""Rédige l'ANALYSE LONGITUDINALE de l'enseignant {id_e} pour une thèse de doctorat en Sciences de l'Éducation.

L'analyse longitudinale reconstitue l'évolution du discours de {id_e} depuis ses dispositions initiales jusqu'à son bilan réflexif final, en passant par les transformations induites par le dispositif hybride.

PROFIL : {p.get('groupe','?')} | {p.get('anciennete','?')} | Phase entretien : {p.get('phase','?')}
STATISTIQUES GLOBALES : {stats['n']} segments — {stats['nR']} ruptures ({stats['pct_r']}%) — {stats['nC']} continuités

SEGMENTS PAR NŒUD :
{detail}

STRUCTURE DE L'ANALYSE LONGITUDINALE :

### 1. Les perspectives d'enseignement initiales de {id_e}
Partir du CONTEXTE_INITIAL pour caractériser les perspectives d'enseignement de {id_e} avant/en début de formation (Pratt, 1998 : Transmission, Apprentissage, Développement, Soutien, Réforme Sociale). Analyser son rapport initial au numérique et à la distance.

### 2. L'entrée dans le dispositif hybride : premiers effets
À partir de VECU_DISPOSITIF, analyser comment {id_e} a vécu l'entrée dans la FOAD. Identifier les freins initiaux, les situations de développement (Vygotski, 1934), les premiers effets sur l'autonomie. Repérer les premiers signaux de rupture ou de continuité.

### 3. La distance transactionnelle vécue
À partir de ALIGNEMENT_THEORIQUE, analyser la distance transactionnelle (Moore, 1997) perçue par {id_e} : dialogue pédagogique, structure du dispositif, degré d'autonomie requis. Lien avec la relation pédagogique.

### 4. Les transformations des pratiques et des postures
À partir de TRANSFORMATION_PRATIQUE, analyser les reconfigurations observées : décentration pédagogique, instrumentation (Rabardel, 1995), transfert vers la pratique, et surtout les glissements de posture (Bucheton & Soulé, 2009) entre les pôles Contrôleur, Transmetteur et Accompagnateur.

### 5. Bilan longitudinal : rupture ou continuité des perspectives ?
À partir de BILAN_REFLEXIF et en synthétisant l'ensemble du parcours, conclure sur la trajectoire longitudinale de {id_e} : le dispositif a-t-il produit une reconfiguration de ses perspectives d'enseignement (Hypothèse 2) ? Argumenter à partir des données.

CONSIGNES :
- Citations systématiques entre « guillemets français »
- Références APA 7 intégrées (Moore, 1997 ; Vygotski, 1934 ; Bruner, 1983 ; Bucheton & Soulé, 2009 ; Pratt, 1998 ; Rabardel, 1995 ; Schön, 1983)
- 4 à 6 paragraphes par partie
- Transitions argumentées entre les parties qui reconstituent la dynamique temporelle
- Conclure sur le rapport de {id_e} à l'Hypothèse 2"""


def render():
    st.markdown("# 📈 Analyse longitudinale")
    st.markdown(
        "Génère pour chaque enseignant un texte académique reconstituant l'évolution "
        "de son discours à travers les 5 nœuds du référentiel."
    )

    data = st.session_state.get("data_aalc", {})
    ens_dict = data.get("enseignants", {})
    if not ens_dict:
        st.warning("⚠️ Aucune donnée chargée.")
        return

    api_key = st.session_state.get("api_key", "")

    # ── Sélection de l'enseignant ─────────────────────────────────────────────
    ids = sorted(ens_dict.keys())
    col_sel, col_meta = st.columns([1, 3])
    with col_sel:
        id_e = st.selectbox("Enseignant", ids, key="long_ens")
    
    d    = ens_dict[id_e]
    p    = d.get("profil", {})
    segs = d.get("segments", [])
    stats = stats_segments(segs)

    with col_meta:
        st.markdown(
            f"**Groupe :** `{p.get('groupe','—')}` | "
            f"**Ancienneté :** {p.get('anciennete','—')} | "
            f"**Phase :** {p.get('phase','—')} | "
            f"**Segments :** {stats['n']} (🔴{stats['nR']} 🟢{stats['nC']})"
        )

    # ── Visualisation rapide ──────────────────────────────────────────────────
    if segs:
        cols = st.columns(5)
        for j, pere in enumerate(PERES):
            n = stats["peres"].get(pere, 0)
            nR = sum(1 for s in segs if s.get("code_pere")==pere and s.get("polarite")=="RUPTURE")
            cols[j].markdown(
                f'<div class="stat-box"><div style="font-size:10px;color:{PERE_COL[pere]};font-weight:600">{pere.replace("_"," ")}</div>'
                f'<div style="font-size:18px;font-weight:500">{n}</div>'
                f'<div style="font-size:11px;color:#C0392B">🔴 {nR}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── Génération ───────────────────────────────────────────────────────────
    cle = f"longitudinal_{id_e}"
    if cle in st.session_state["textes_rediges"]:
        st.markdown("#### Analyse longitudinale rédigée")
        texte = st.session_state["textes_rediges"][cle]
        st.markdown(
            f'<div class="these-block" style="font-family:Georgia,serif;line-height:1.9">{texte.replace(chr(10),"<br>")}</div>',
            unsafe_allow_html=True,
        )
        col_a, col_b, col_c = st.columns([1, 1, 4])
        with col_a:
            if st.button("🔄 Regénérer", key=f"regen_l_{id_e}"):
                del st.session_state["textes_rediges"][cle]
                st.rerun()
        with col_b:
            st.download_button(
                "⬇️ .txt",
                data=texte.encode("utf-8"),
                file_name=f"longitudinal_{id_e}.txt",
                mime="text/plain",
                key=f"dl_l_{id_e}",
            )
    else:
        if not segs:
            st.info("Aucun segment codé pour cet enseignant.")
        else:
            st.markdown(f"*{stats['n']} segments disponibles pour l'analyse longitudinale de {id_e}.*")
            if st.button(
                f"✍️ Générer l'analyse longitudinale — {id_e}",
                key=f"gen_l_{id_e}",
                disabled=not api_key,
                type="primary",
            ):
                with st.spinner(f"Rédaction de l'analyse longitudinale de {id_e}… (30-60s)"):
                    try:
                        texte = appel_llm(
                            _prompt_longitudinal(id_e, p, segs, stats),
                            max_tokens=5000,
                        )
                        st.session_state["textes_rediges"][cle] = texte
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erreur : {e}")

    # ── Générer toutes ────────────────────────────────────────────────────────
    st.markdown("---")
    nb_deja = sum(1 for id_e in ids if f"longitudinal_{id_e}" in st.session_state["textes_rediges"])
    st.markdown(f"**Analyses longitudinales générées : {nb_deja}/{len(ids)}**")
    if st.button("🚀 Générer toutes les analyses longitudinales", disabled=not api_key):
        prog = st.progress(0)
        for i, id_e in enumerate(ids):
            cle = f"longitudinal_{id_e}"
            if cle in st.session_state["textes_rediges"]:
                prog.progress((i+1)/len(ids))
                continue
            d    = ens_dict[id_e]
            p    = d.get("profil", {})
            segs = d.get("segments", [])
            if not segs:
                prog.progress((i+1)/len(ids))
                continue
            stats = stats_segments(segs)
            with st.spinner(f"Analyse longitudinale {id_e}…"):
                try:
                    st.session_state["textes_rediges"][cle] = appel_llm(
                        _prompt_longitudinal(id_e, p, segs, stats), max_tokens=5000
                    )
                except Exception as e:
                    st.error(f"{id_e} : {e}")
            prog.progress((i+1)/len(ids))
        st.success("✅ Toutes les analyses longitudinales générées !")
        st.rerun()
