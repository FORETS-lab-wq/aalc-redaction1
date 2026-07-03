"""
page_import.py
Accueil et import : fichiers Word (.docx), LibreOffice (.odt) ou JSON depuis AALC.
Les fichiers sont stockés en session_state AVANT de naviguer vers une autre page.
"""

import io
import json
import re
import streamlit as st
import pandas as pd


def _extraire_texte_docx(octets: bytes) -> str:
    from docx import Document as DocxDocument
    doc = DocxDocument(io.BytesIO(octets))
    return "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())


def _extraire_texte_odt(octets: bytes) -> str:
    from odf.opendocument import load
    from odf.text import P
    doc = load(io.BytesIO(octets))
    paras = doc.text.getElementsByType(P)
    return "\n".join(str(p).strip() for p in paras if str(p).strip())


def _extraire_texte(octets: bytes, nom: str) -> str:
    if nom.lower().endswith(".odt"):
        return _extraire_texte_odt(octets)
    else:
        return _extraire_texte_docx(octets)


def _detecter_id(nom_fichier: str) -> str:
    nom = nom_fichier.replace(".docx","").replace(".odt","").strip().upper()
    if re.match(r"^E\d{1,2}$", nom):
        return nom
    m = re.search(r"ENSEIGNANT[_\s\-]*(\d{1,2})", nom)
    if m:
        return f"E{m.group(1)}"
    m = re.search(r"E[_\s]?(\d{1,2})", nom)
    if m:
        return f"E{m.group(1)}"
    return "E1"


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

    # ── Initialisation session ────────────────────────────────────────────────
    if "data_aalc" not in st.session_state:
        st.session_state["data_aalc"] = {"enseignants": {}}

    st.markdown("---")

    # ── OPTION 1 : Fichiers .docx ou .odt ────────────────────────────────────
    st.markdown("### 📝 Importer les fichiers de transcription")
    st.markdown(
        "**1.** Déposez vos fichiers ci-dessous (.docx ou .odt)  \n"
        "**2.** Vérifiez l'identifiant et le groupe de chaque fichier  \n"
        "**3.** Cliquez **Charger tous les fichiers** pour les enregistrer en session"
    )

    fichiers = st.file_uploader(
        "Déposer les fichiers (.docx ou .odt)",
        type=["docx", "odt"],
        accept_multiple_files=True,
        key="upload_fichiers",
    )

    if fichiers:
        ids_dispo = [f"E{i}" for i in range(1, 11)]

        # Tableau de configuration
        configs = {}
        st.markdown("#### Vérifiez les identifiants et groupes :")
        for f in fichiers:
            id_suggere = _detecter_id(f.name)
            c1, c2, c3 = st.columns([3, 2, 2])
            with c1:
                st.markdown(f"📄 `{f.name}`")
            with c2:
                id_e = st.selectbox(
                    "ID",
                    ids_dispo,
                    index=ids_dispo.index(id_suggere) if id_suggere in ids_dispo else 0,
                    key=f"id_{f.name}",
                    label_visibility="collapsed",
                )
            with c3:
                groupe = st.selectbox(
                    "Groupe",
                    ["Hybride", "Traditionnel"],
                    key=f"grp_{f.name}",
                    label_visibility="collapsed",
                )
            configs[f.name] = {"id_e": id_e, "groupe": groupe, "fichier": f}

        st.markdown("")
        if st.button(
            f"✅ Charger tous les fichiers ({len(fichiers)})",
            type="primary",
            use_container_width=True,
        ):
            data = st.session_state["data_aalc"]
            nb_ok = 0
            nb_err = 0
            for nom, cfg in configs.items():
                try:
                    octets = cfg["fichier"].read()
                    texte  = _extraire_texte(octets, nom)
                    paras  = [p for p in texte.split("\n") if p.strip()]
                    id_e   = cfg["id_e"]
                    groupe = cfg["groupe"]
                    data["enseignants"][id_e] = {
                        "id": id_e,
                        "profil": {
                            "groupe": groupe,
                            "anciennete": "1-3 ans",
                            "type_formation": "TP ECSR",
                            "niveau_num": "Débutant",
                            "phase": "En cours de formation",
                            "organisme": "",
                            "genre": "Non renseigné",
                            "age_approx": "",
                            "notes": "",
                        },
                        "verbatim": texte,
                        "segments": data["enseignants"].get(id_e, {}).get("segments", []),
                    }
                    nb_ok += 1
                except Exception as e:
                    st.error(f"Erreur — {nom} : {e}")
                    nb_err += 1

            st.session_state["data_aalc"] = data
            if nb_ok:
                st.success(
                    f"✅ {nb_ok} fichier(s) chargé(s) en session. "
                    "Vous pouvez maintenant aller dans **Traitement individuel**."
                )
            if nb_err:
                st.warning(f"⚠️ {nb_err} fichier(s) en erreur.")
            st.rerun()

    st.markdown("---")

    # ── OPTION 2 : JSON ───────────────────────────────────────────────────────
    st.markdown("### 📂 Ou importer un fichier JSON (session précédente ou export AALC)")

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
                st.success(
                    f"✅ {nb} enseignant(s) chargé(s). "
                    "Vous pouvez maintenant aller dans **Traitement individuel**."
                )
                st.rerun()
        except Exception as e:
            st.error(f"Erreur : {e}")

    st.markdown("---")

    # ── Récapitulatif ─────────────────────────────────────────────────────────
    ens = st.session_state.get("data_aalc", {}).get("enseignants", {})
    if ens:
        _afficher_apercu(ens)
    else:
        st.info("Aucun enseignant chargé pour l'instant.")

    # ── Saisie manuelle ───────────────────────────────────────────────────────
    with st.expander("✏️ Ajouter un enseignant manuellement"):
        _formulaire_manuel()


def _afficher_apercu(ens: dict):
    st.markdown("### ✅ Enseignants en session")
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
    c3.metric("Groupe Hybride",
              sum(1 for d in ens.values() if d.get("profil",{}).get("groupe")=="Hybride"))
    c4.metric("Groupe Traditionnel",
              sum(1 for d in ens.values() if d.get("profil",{}).get("groupe")=="Traditionnel"))

    if st.button("🗑️ Vider la session"):
        st.session_state["data_aalc"] = {"enseignants": {}}
        st.rerun()


def _formulaire_manuel():
    id_e     = st.selectbox("Identifiant", [f"E{i}" for i in range(1, 11)], key="man_id")
    groupe   = st.selectbox("Groupe", ["Hybride", "Traditionnel"], key="man_grp")
    verbatim = st.text_area("Texte du verbatim", height=100, key="man_verb")
    if st.button("Ajouter", key="man_btn") and verbatim:
        data = st.session_state.setdefault("data_aalc", {"enseignants": {}})
        data["enseignants"][id_e] = {
            "id": id_e,
            "profil": {
                "groupe": groupe, "anciennete": "1-3 ans",
                "type_formation": "TP ECSR", "niveau_num": "Débutant",
                "phase": "En cours de formation", "organisme": "",
                "genre": "Non renseigné", "age_approx": "", "notes": "",
            },
            "verbatim": verbatim,
            "segments": [],
        }
        st.success(f"✅ {id_e} ajouté.")
        st.rerun()
