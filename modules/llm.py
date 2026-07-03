"""
llm.py — Appels API Anthropic partagés entre tous les modules.
"""

import anthropic
import streamlit as st

SYSTEM_THESE = """Tu es un expert en Sciences de l'Éducation et Formation, spécialisé dans la rédaction académique de thèses de doctorat.

Tu travailles sur une thèse portant sur la formation des enseignants de la conduite automobile (TP ECSR).

HYPOTHÈSE 2 (focus de cette application) :
"Le dispositif suivi à distance expose les apprenants-enseignants à une rupture de configuration des perspectives d'enseignement."

CADRE THÉORIQUE OBLIGATOIRE À MOBILISER :
- Perspectives d'enseignement (Pratt, 1998) : Transmission, Apprentissage, Développement, Soutien, Réforme
- Distance transactionnelle (Moore, 1997) : dialogue, structure, autonomie
- Étayage et ZPD (Vygotski, 1934 ; Bruner, 1983)
- Postures d'étayage : Contrôleur / Transmetteur / Accompagnateur (Bucheton & Soulé, 2009)
- Praticien réflexif (Schön, 1983)
- Genèse instrumentale (Rabardel, 1995)
- REMC 2013 : référentiel de compétences de l'enseignant de la conduite

RÉFÉRENTIEL DE CODAGE :
- CONTEXTE_INITIAL → EXP_PROF, FAMILIARITE_HYB, REPRESENTATION_NUM, AFFORDANCE_CULTURELLE
- VECU_DISPOSITIF → VECU_ALTERNANCE, AUTONOMIE_APPRENANT, FREINS_INITIAUX, SIT_DEVELOPPEMENT
- ALIGNEMENT_THEORIQUE → DISTANCE_TRANSACTIONNELLE, LIEN_RELATION
- TRANSFORMATION_PRATIQUE → DECENTRATION_PEDAG, INSTRUMENTATION, TRANSFERT_PRATIQUE, GLISSEMENT_POSTURE
- BILAN_REFLEXIF → APPORT_HYBRIDE, LIMITES_HYBRIDE

POLARITÉ : RUPTURE (reconfiguration des perspectives) | CONTINUITÉ | AMBIGU

RÈGLES DE RÉDACTION :
- Style académique soutenu, 3e personne
- Références bibliographiques au format APA 7 intégrées dans le texte
- Citations du verbatim entre guillemets français (« »), en italique
- Paragraphes denses, argumentation serrée
- Transitions entre paragraphes explicites
- Ne jamais inventer de données non présentes
- Rédiger en français académique exclusivement
"""


def appel_llm(prompt: str, max_tokens: int = 3000) -> str:
    """Appel simple à l'API Anthropic. Retourne le texte généré."""
    api_key = st.session_state.get("api_key", "")
    if not api_key:
        raise ValueError("Clé API Anthropic non renseignée.")
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=SYSTEM_THESE,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def segments_vers_texte(segments: list[dict]) -> str:
    """Formate les segments codés pour inclusion dans un prompt."""
    lignes = []
    for s in segments:
        pol = s.get("polarite", "AMBIGU")
        emoji = {"RUPTURE": "🔴", "CONTINUITE": "🟢", "AMBIGU": "⚪"}.get(pol, "⚪")
        lignes.append(
            f"[{s.get('code_pere','?')} › {s.get('code_fils','?')}] {emoji} {pol}\n"
            f"  Extrait : « {s.get('extrait','')[:200]} »\n"
            f"  Justification : {s.get('justification','—')}"
        )
    return "\n\n".join(lignes)


def stats_segments(segments: list[dict]) -> dict:
    """Calcule les statistiques de base sur un ensemble de segments."""
    n = len(segments)
    nR = sum(1 for s in segments if s.get("polarite") == "RUPTURE")
    nC = sum(1 for s in segments if s.get("polarite") == "CONTINUITE")
    nA = n - nR - nC
    pct_r = round(nR / n * 100, 1) if n else 0
    peres = {}
    for s in segments:
        p = s.get("code_pere", "?")
        peres[p] = peres.get(p, 0) + 1
    return {"n": n, "nR": nR, "nC": nC, "nA": nA, "pct_r": pct_r, "peres": peres}
