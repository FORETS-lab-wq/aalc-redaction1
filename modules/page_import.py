"""
page_import.py
Accueil et import du fichier JSON exporté depuis AALC.
Gère deux formats : export AALC natif et export APPEC-Verbatims.
"""

import json
import streamlit as st
import pandas as pd


PERE_ORDRE = [
    "CONTEXTE_INITIAL", "VECU_DISPOSITIF",
    "ALIGNEMENT_THEORIQUE", "TRANSFORMATION_PRATIQUE", "BILAN_REFLEXIF",
]
PERE_COL = {
    "CONTEXTE_INITIAL": "#1B3A5C",
    "VECU_DISPOSITIF": "#C0392B",
    "ALIGNEMENT_THEORIQUE": "#7D3C98",
    "TRANSFORMATION_PRATIQUE": "#E8A020",
    "BILAN_REFLEXIF": "#27AE60",
}


def _normaliser_depuis_appec(raw: dict) -> dict:
    """
    Convertit un export APPEC-Verbatims (format de la session Claude)
    vers le format interne AALC-Rédaction.
    """
    enseignants = {}
    codages   = raw.get("codages", {})
    profils   = raw.get("profils", {})
    verbatims = raw.get("verbatims", {})

    for id_ens, segs in codages.items():
        p = profils.get(id_ens, {})
        enseignants[id_ens] = {
            "id": id_ens,
            "profil": {
                "groupe":         p.get("groupe", "?"),
                "anciennete":     p.get("anciennete", "?"),
                "type_formation": p.get("type_formation", "TP ECSR"),
                "niveau_num":     p.get("niveau_num", "?"),
                "phase":          p.get("phase_entretien", p.get("phase", "?")),
                "organisme":      p.get("organisme", ""),
                "genre":          p.get("genre", "Non renseigné"),
                "age_approx":     p.get("age_approx", ""),
                "notes":          p.get("notes", ""),
            },
            "verbatim": verbatims.get(id_ens, {}).get("texte", ""),
            "segments": segs,
        }
    return {"enseignants": enseignants}


def _normaliser_depuis_aalc(raw: dict) -> dict:
    """
    Tente de normaliser un export natif AALC (format Streamlit Cloud).
    Structure variable selon la version de AALC — on essaie plusieurs clés.
    """
    # Format 1 : {enseignants: {E1: {profil, segments, verbatim}}}
    if "enseignants" in raw:
        return raw

    # Format 2 : {codages: ..., profils: ..., verbatims: ...} — même que APPEC
    if "codages" in raw:
        return _normaliser_depuis_appec(raw)

    # Format 3 : liste plate de segments avec id_ens
    if isinstance(raw, list):
        ens = {}
        for seg in raw:
            id_e = seg.get("id_ens", seg.get("enseignant", "?"))
            if id_e not in ens:
                ens[id_e] = {"id": id_e, "profil": {}, "verbatim": "", "segments": []}
            ens[id_e]["segments"].append(seg)
        return {"enseignants": ens}

    return {"enseignants": {}}


def render():
    st.markdown("# 🏠 Accueil & Import des données")
    st.markdown(
        "Importez le fichier JSON exporté depuis **AALC** (ou depuis APPEC-Verbatims). "
        "Toutes vos données codées seront immédiatement disponibles."
    )

    # ── Hypothèse ─────────────────────────────────────────────────────────────
    st.info(
        "**Hypothèse 2 :** *Le dispositif suivi à distance expose les apprenants-enseignants "
        "à une rupture de configuration des perspectives d'enseignement.*"
    )

    st.markdown("---")
    st.markdown("### 📂 Import du fichier JSON")

    col1, col2 = st.columns([2, 1])
    with col1:
        fichier = st.file_uploader(
            "Déposez votre fichier JSON (export AALC ou APPEC-Verbatims)",
            type=["json"],
            help="Fichier exporté via 'Sauvegarde JSON' depuis AALC ou APPEC-Verbatims",
        )

    with col2:
        st.markdown("#### Format attendu")
        st.markdown("""
Le fichier JSON doit provenir de :
- **AALC** (Streamlit Cloud) → Export JSON
- **APPEC-Verbatims** → Sauvegarde JSON

Les deux formats sont reconnus automatiquement.
""")

    if fichier:
        try:
            raw = json.loads(fichier.read().decode("utf-8"))
            data = _normaliser_depuis_aalc(raw)
            nb = len(data.get("enseignants", {}))
            if nb == 0:
                st.error("Aucun enseignant trouvé dans ce fichier. Vérifiez le format.")
            else:
                st.session_state["data_aalc"] = data
                st.success(f"✅ {nb} enseignant(s) chargé(s) avec succès.")
                _afficher_apercu(data)
        except Exception as e:
            st.error(f"Erreur lors de la lecture : {e}")

    # ── Saisie manuelle si pas de fichier ─────────────────────────────────────
    st.markdown("---")
    st.markdown("### ✏️ Ou saisir manuellement un enseignant")
    with st.expander("Ajouter un enseignant manuellement"):
        _formulaire_manuel()

    # ── Affichage si données déjà chargées ────────────────────────────────────
    if st.session_state.get("data_aalc"):
        st.markdown("---")
        _afficher_apercu(st.session_state["data_aalc"])


def _afficher_apercu(data: dict):
    """Tableau récapitulatif des enseignants chargés."""
    ens = data.get("enseignants", {})
    if not ens:
        return
    st.markdown("### Données chargées")
    lignes = []
    for id_e, d in sorted(ens.items()):
        p = d.get("profil", {})
        segs = d.get("segments", [])
        nR = sum(1 for s in segs if s.get("polarite") == "RUPTURE")
        nC = sum(1 for s in segs if s.get("polarite") == "CONTINUITE")
        lignes.append({
            "ID":          id_e,
            "Groupe":      p.get("groupe", "—"),
            "Ancienneté":  p.get("anciennete", "—"),
            "Formation":   p.get("type_formation", "—"),
            "Segments":    len(segs),
            "🔴 Rupture":  nR,
            "🟢 Continuité": nC,
            "% Rupture":   f"{round(nR/len(segs)*100,1)}%" if segs else "—",
        })
    df = pd.DataFrame(lignes).set_index("ID")

    def color_groupe(val):
        if val == "Hybride":
            return "background-color:#D6EAF8;color:#1B3A5C;font-weight:bold"
        elif val == "Traditionnel":
            return "background-color:#D5F5E3;color:#1E8449;font-weight:bold"
        return ""

    st.dataframe(
        df.style.applymap(color_groupe, subset=["Groupe"]),
        use_container_width=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    total_segs = sum(len(d.get("segments",[])) for d in ens.values())
    total_R = sum(sum(1 for s in d.get("segments",[]) if s.get("polarite")=="RUPTURE") for d in ens.values())
    nb_H = sum(1 for d in ens.values() if d.get("profil",{}).get("groupe")=="Hybride")
    nb_T = sum(1 for d in ens.values() if d.get("profil",{}).get("groupe")=="Traditionnel")
    c1.metric("Enseignants", len(ens))
    c2.metric("Segments total", total_segs)
    c3.metric("Groupe Hybride", nb_H)
    c4.metric("Groupe Traditionnel", nb_T)


def _formulaire_manuel():
    """Permet d'ajouter un enseignant sans fichier JSON."""
    id_e = st.selectbox("Identifiant", [f"E{i}" for i in range(1, 11)])
    col1, col2 = st.columns(2)
    with col1:
        groupe = st.selectbox("Groupe", ["Hybride", "Traditionnel"])
        anciennete = st.selectbox("Ancienneté", ["< 1 an", "1-3 ans", "3-5 ans", "> 5 ans"])
        niveau_num = st.selectbox("Niveau numérique", ["Débutant", "Intermédiaire", "Avancé"])
    with col2:
        phase = st.selectbox("Phase entretien", ["Avant la formation", "En cours", "Après la formation"])
        organisme = st.text_input("Organisme", placeholder="ECF CERCA")
        age = st.text_input("Tranche d'âge", placeholder="30-35 ans")

    verbatim = st.text_area("Verbatim (texte brut)", height=120)
    segments_raw = st.text_area(
        "Segments codés (JSON — optionnel)",
        height=80,
        placeholder='[{"code_pere":"VECU_DISPOSITIF","code_fils":"AUTONOMIE_APPRENANT","polarite":"RUPTURE","extrait":"...","justification":"..."}]',
    )

    if st.button("Ajouter cet enseignant"):
        segs = []
        if segments_raw.strip():
            try:
                segs = json.loads(segments_raw)
            except Exception:
                st.warning("JSON des segments invalide — enseignant ajouté sans segments.")

        data = st.session_state.setdefault("data_aalc", {"enseignants": {}})
        data["enseignants"][id_e] = {
            "id": id_e,
            "profil": {
                "groupe": groupe, "anciennete": anciennete,
                "type_formation": "TP ECSR", "niveau_num": niveau_num,
                "phase": phase, "organisme": organisme,
                "age_approx": age, "genre": "Non renseigné", "notes": "",
            },
            "verbatim": verbatim,
            "segments": segs,
        }
        st.success(f"✅ {id_e} ajouté ({len(segs)} segments).")
        st.rerun()
