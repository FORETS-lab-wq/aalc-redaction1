# AALC-Rédaction

Application Streamlit de rédaction académique pour la thèse TP ECSR.  
Génère un rapport Word complet (40-50 pages) à partir des données codées dans AALC.

## Déploiement sur Streamlit Cloud

1. Forkez ce dépôt sur votre compte GitHub (`mathieuforets4`)
2. Allez sur [share.streamlit.io](https://share.streamlit.io)
3. **New app** → sélectionnez ce dépôt → `app.py` → **Deploy**

## Utilisation

1. **Accueil & Import** — importez le JSON exporté depuis AALC
2. **Traitement individuel** — générez profil + analyse pour chaque enseignant
3. **Analyse longitudinale** — générez l'analyse longitudinale par enseignant
4. **Analyse transversale** — comparez Hybride vs Traditionnel
5. **Synthèse & H2** — générez la réponse à l'Hypothèse 2
6. **Export Word** — téléchargez le rapport complet (.docx)

## Structure du rapport Word généré

- Partie 1 : Fiches profils (× 10)
- Partie 2 : Analyses individuelles (× 10)
- Partie 3 : Analyses longitudinales (× 10)
- Partie 4 : Analyse transversale Hybride vs Traditionnel
- Partie 5 : Synthèse globale et réponse à l'Hypothèse 2
- Annexe : Corpus de segments codés

## Clé API

Renseignez votre clé Anthropic dans la barre latérale. Créez-en une sur [console.anthropic.com](https://console.anthropic.com).
