"""
page_import.py - Import fichiers ODT/DOCX ou JSON
"""

import io
import json
import re
import streamlit as st
import pandas as pd


def _extraire_texte_docx(octets):
    from docx import Document as D
    doc = D(io.BytesIO(octets))
    return "\n".join(p.text.strip() for p in doc.paragraphs if p.text.strip())


def _extraire_texte_odt(octets):
    from odf.opendocument import load
    from odf.text import P
    doc = load(io.BytesIO(octets))
    paras = doc.text.getElementsByType(P)
    return "\n".join(str(p).strip() for p in paras if str(p).strip())


def _extraire(octets, nom):
    if nom.lower().endswith(".odt"):
        return _extraire_texte_odt(octets)
    return _extraire_texte_docx(octets)


def _detecter_id(nom):
    n = nom.replace(".docx","").replace(".odt","").strip().upper()
    if re.match(r"^E\d{1,2}$", n):
        return n
    m = re.search(r"ENSEIGNANT[_\s\-]*(\d{1,2})", n)
    if m:
        return "E" + m.group(1)
    m = re.search(r"E[_\s]?(\d{1,2})", n)
    if m:
        return "E" + m.group(1)
    return "E1"


def _init_session():
    if "data_aalc" not in st.session_state:
        st.session_state["data_aalc"] = {"enseignants": {}}
    elif not isinstance(st.session_state["data_aalc"], dict):
        st.session_state["data_aalc"] = {"enseignants": {}}
    elif "enseignants" not in st.session_state["data_aalc"]:
        st.session_state["data_aalc"]["enseignants"] = {}


def render():
    _init_session()

    st.markdown("# Accueil & Import des donnees")
    st.info("Hypothese 2 : Le dispositif a distance expose les apprenants-enseignants a une rupture de configuration des perspectives d'enseignement.")
    st.markdown("---")

    st.markdown("### Importer les fichiers de transcription (.odt ou .docx)")
    st.markdown("1. Deposez vos fichiers  \n2. Verifiez identifiant et groupe  \n3. Cliquez **Charger tous les fichiers**")

    fichiers = st.file_uploader(
        "Deposer les fichiers",
        type=["docx","odt"],
        accept_multiple_files=True,
        key="upload_fichiers",
    )

    if fichiers:
        ids_dispo = ["E"+str(i) for i in range(1,11)]
        configs = {}
        st.markdown("#### Verifiez les identifiants :")
        for f in fichiers:
            id_suggere = _detecter_id(f.name)
            c1,c2,c3 = st.columns([3,2,2])
            with c1:
                st.markdown("**" + f.name + "**")
            with c2:
                idx = ids_dispo.index(id_suggere) if id_suggere in ids_dispo else 0
                id_e = st.selectbox("ID", ids_dispo, index=idx, key="id_"+f.name, label_visibility="collapsed")
            with c3:
                grp = st.selectbox("Groupe", ["Hybride","Traditionnel"], key="grp_"+f.name, label_visibility="collapsed")
            configs[f.name] = {"id_e": id_e, "groupe": grp, "fichier": f}

        if st.button("Charger tous les fichiers (" + str(len(fichiers)) + ")", type="primary", use_container_width=True):
            nb_ok = 0
            for nom, cfg in configs.items():
                try:
                    octets = cfg["fichier"].read()
                    texte = _extraire(octets, nom)
                    paras = [p for p in texte.split("\n") if p.strip()]
                    id_e = cfg["id_e"]
                    anciens_segs = st.session_state["data_aalc"]["enseignants"].get(id_e, {}).get("segments", [])
                    st.session_state["data_aalc"]["enseignants"][id_e] = {
                        "id": id_e,
                        "profil": {
                            "groupe": cfg["groupe"],
                            "anciennete": "1-3 ans",
                            "type_formation": "TP ECSR",
                            "niveau_num": "Debutant",
                            "phase": "En cours de formation",
                            "organisme": "",
                            "genre": "Non renseigne",
                            "age_approx": "",
                            "notes": "",
                        },
                        "verbatim": texte,
                        "segments": anciens_segs,
                    }
                    nb_ok += 1
                except Exception as e:
                    st.error("Erreur " + nom + " : " + str(e))
            if nb_ok:
                st.success(str(nb_ok) + " fichier(s) charge(s). Allez dans Traitement individuel.")
            st.rerun()

    st.markdown("---")
    st.markdown("### Ou importer un fichier JSON")
    fj = st.file_uploader("Fichier JSON", type=["json"], key="upload_json")
    if fj:
        try:
            raw = json.loads(fj.read().decode("utf-8"))
            if "enseignants" in raw:
                data = raw
            elif "codages" in raw:
                data = {"enseignants": {}}
                for id_ens, segs in raw.get("codages",{}).items():
                    p = raw.get("profils",{}).get(id_ens,{})
                    data["enseignants"][id_ens] = {
                        "id": id_ens,
                        "profil": {
                            "groupe": p.get("groupe","?"),
                            "anciennete": p.get("anciennete","?"),
                            "type_formation": p.get("type_formation","TP ECSR"),
                            "niveau_num": p.get("niveau_num","?"),
                            "phase": p.get("phase_entretien", p.get("phase","?")),
                            "organisme": p.get("organisme",""),
                            "genre": p.get("genre","Non renseigne"),
                            "age_approx": p.get("age_approx",""),
                            "notes": p.get("notes",""),
                        },
                        "verbatim": raw.get("verbatims",{}).get(id_ens,{}).get("texte",""),
                        "segments": segs,
                    }
            else:
                data = {"enseignants": {}}
            nb = len(data["enseignants"])
            if nb == 0:
                st.error("Aucun enseignant trouve.")
            else:
                st.session_state["data_aalc"] = data
                st.success(str(nb) + " enseignant(s) charges.")
                st.rerun()
        except Exception as e:
            st.error("Erreur : " + str(e))

    st.markdown("---")
    ens = st.session_state["data_aalc"]["enseignants"]
    if ens:
        st.markdown("### Enseignants en session")
        lignes = []
        for id_e, d in sorted(ens.items()):
            p = d.get("profil",{})
            segs = d.get("segments",[])
            nb_para = len([l for l in d.get("verbatim","").split("\n") if l.strip()])
            lignes.append({
                "ID": id_e,
                "Groupe": p.get("groupe","?"),
                "Paragraphes": nb_para,
                "Segments": len(segs),
            })
        st.dataframe(pd.DataFrame(lignes).set_index("ID"), use_container_width=True)
        c1,c2,c3 = st.columns(3)
        c1.metric("Enseignants", len(ens))
        c2.metric("Hybride", sum(1 for d in ens.values() if d.get("profil",{}).get("groupe")=="Hybride"))
        c3.metric("Traditionnel", sum(1 for d in ens.values() if d.get("profil",{}).get("groupe")=="Traditionnel"))
        if st.button("Vider la session"):
            st.session_state["data_aalc"] = {"enseignants": {}}
            st.rerun()
    else:
        st.info("Aucun enseignant charge pour l'instant.")
