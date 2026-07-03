"""
page_import.py
Accueil et import : fichiers Word (.docx) ou JSON exporté depuis AALC.
"""

import io
import json
import re
import streamlit as st
import pandas as pd
from docx import Document as DocxDocument


PERE_COL = {
    "CONTEXTE_INITIAL": "#1B3A5C",
    "VECU_DISPOSITIF": "#C0392B",
    "ALIGNEMENT_THEORIQUE": "#7D3C98",
    "TRANSFORMATION_PRATIQUE": "#E8A020",
    "BILAN_REFLEXIF": "#27AE60",
}


def _extraire_texte_docx(octets: bytes) -> str:
    doc = DocxDocument(io.BytesIO(octets))
    return "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())


def _detecter_id(nom_fichier: str) -> str:
    nom = nom_fichier.replace(".docx", "").strip().upper()
    if re.match(r"^E\d{1,2}$", nom):
        return nom
    m = re.search(r"E(\d{1,2})", nom)
    return f"E{m.group(1)}" if m else "E1"


def _normaliser_depuis_appec(raw: dict) -> dict:
    enseignants = {}
    for id_ens, segs in raw.get("codages", {}).items():
        p = raw.get("profils", {}).get(id_ens, {})
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
            "verbatim": raw.get("verbatims", {}).get(id_ens, {}).get("texte", ""),
            "segments": segs,
        }
    return {"enseignants": enseignants}


def _normaliser_depuis_aalc(raw: dict) -> dict:
    if "enseignants" in raw:
        return raw
    if "codages" in raw:
        return _normaliser_depuis_appec(raw)
    if isinstance(raw, list):
        ens = {}
        for seg in raw:
            id_e = seg.get("id_ens", "?")
            if id_e not in ens:
                ens[id_e] = {"id": id_e, "profil": {}, "verbatim": "", "segments": []}
            ens[id_e]["segments"].append(seg)
        return {"enseignants": ens}
    return {"enseignants": {}}


def render():
    st.markdown("# 🏠 Accueil & Import des données")

    st.info(
        "**Hypothèse 2 :** *Le dispositif suivi à distance expose les apprenants-enseignants "
        "à une rupture de configuration des perspectives d'enseignement.*"
    )

    st.markdown("---")

    st.markdown("### 📝 Importer les fichiers Word (.docx)")
    st.markdown(
        "Déposez vos 10 fichiers Word en une seule fois. "
        "Nommez-les `E1.docx` … `E10.docx` pour que l'identifiant soit détecté automatiquement."
    )

    fichiers = st.file_uploader(
        "Déposer les fichiers .docx",
        type=["docx"],
        accept_multiple_files=True,
        key="upload_docx",
    )

    if fichiers:
        ids_dispo = [f"E{i}" for i in range(1, 11)]
        for f in fichiers:
            id_suggere = _detecter_id(f.name)
            st.markdown(f"**{f.name}**")
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                id_e = st.selectbox(
                    "Identifiant",
                    ids_dispo,
                    index=ids_dispo.index(id_suggere) if id_suggere in ids_dispo else 0,
                    key=f"id_{f.name}",
                    label_visibility="collapsed",
                )
            with c2:
                groupe = st.selectbox(
                    "Groupe",
                    ["Hybride", "Traditionnel"],
                    key=f"grp_{f.name}",
                    label_visibility="collapsed",
                )
            with c3:
                if st.button("✅ Charger", key=f"btn_{f.name}"):
                    octets = f.read()
                    texte  = _extraire_texte_docx(octets)
                    paras  = [p for p in texte.split("\n") if p.strip()]
                    data   = st.session_state.setdefault("data_aalc", {"enseignants": {}})
                    data["enseignants"][id_e] = {
                        "id": id_e,
                        "profil": {
                            "groupe": groupe, "anciennete": "1-3 ans",
                            "type_formation": "TP ECSR", "niveau_num": "Débutant",
                            "phase": "En cours de formation", "organisme": "",
                            "genre": "Non renseigné", "age_approx": "", "notes": "",
                        },
                        "verbatim": texte,
                        "segments": [],
                    }
                    st.success(f"✅ {id_e} chargé — {len(paras)} paragraphes")
                    st.rerun()

    st.markdown("---")

    st.markdown("### 📂 Ou importer un fichier JSON (données déjà codées dans AALC)")

    fichier_json = st.file_uploader(
        "Déposer le fichier JSON",
        type=["json"],
        key="upload_json",
    )

    if fichier_json:
        try:
            raw  = json.loads(fichier_json.read().decode("utf-8"))
            data = _normaliser_depuis_aalc(raw)
            nb   = len(data.get("enseignants", {}))
            if nb == 0:
                st.error("Aucun enseignant trouvé dans ce fichier.")
            else:
                st.session_state["data_aalc"] = data
                st.success(f"✅ {nb} enseignant(s) chargé(s).")
                st.rerun()
        except Exception as e:
            st.error(f"Erreur : {e}")

    st.markdown("---")

    with st.expander("✏️ Ajouter un enseignant manuellement"):
        _formulaire_manuel()

    if st.session_state.get("data_aalc"):
        st.markdown("---")
        _afficher_apercu(st.session_state["data_aalc"])


def _afficher_apercu(data: dict):
    ens = data.get("enseignants", {})
    if not ens:
        return
    st.markdown("### Enseignants chargés")
    lignes = []
    for id_e, d in sorted(ens.items()):
        p    = d.get("profil", {})
        segs = d.get("segments", [])
        nR   = sum(1 for s in segs if s.get("polarite") == "RUPTURE")
        nC   = sum(1 for s in segs if s.get("polarite") == "CONTINUITE")
        nb_para = len([l for l in d.get("verbatim","").split("\n") if l.strip()])
        lignes.append({
            "ID":            id_e,
            "Groupe":        p.get("groupe", "—"),
            "Ancienneté":    p.get("anciennete", "—"),
            "Paragraphes":   nb_para,
            "Segments":      len(segs),
            "🔴 Rupture":    nR,
            "🟢 Continuité": nC,
        })
    df = pd.DataFrame(lignes).set_index("ID")

    def col_groupe(val):
        if val == "Hybride":
            return "background-color:#D6EAF8;color:#1B3A5C;font-weight:bold"
        elif val == "Traditionnel":
            return "background-color:#D5F5E3;color:#1E8449;font-weight:bold"
        return ""

    st.dataframe(df.style.applymap(col_groupe, subset=["Groupe"]), use_container_width=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Enseignants", len(ens))
    c2.metric("Segments total", sum(len(d.get("segments",[])) for d in ens.values()))
    c3.metric("Groupe Hybride", sum(1 for d in ens.values() if d.get("profil",{}).get("groupe")=="Hybride"))
    c4.metric("Groupe Traditionnel", sum(1 for d in ens.values() if d.get("profil",{}).get("groupe")=="Traditionnel"))

    if st.button("🗑️ Vider la session"):
        st.session_state["data_aalc"] = {}
        st.rerun()


def _formulaire_manuel():
    id_e     = st.selectbox("Identifiant", [f"E{i}" for i in range(1, 11)], key="man_id")
    groupe   = st.selectbox("Groupe", ["Hybride", "Traditionnel"], key="man_grp")
    verbatim = st.text_area("Texte du verbatim", height=100, key="man_verb")
    if st.button("Ajouter", key="man_btn") and verbatim:
        data = st.session_state.setdefault("data_aalc", {"enseignants": {}})
        data["enseignants"][id_e] = {
            "id": id_e,
            "profil": {"groupe": groupe, "anciennete": "1-3 ans", "type_formation": "TP ECSR",
                       "niveau_num": "Débutant", "phase": "En cours de formation",
                       "organisme": "", "genre": "Non renseigné", "age_approx": "", "notes": ""},
            "verbatim": verbatim,
            "segments": [],
        }
        st.success(f"✅ {id_e} ajouté.")
        st.rerun()
