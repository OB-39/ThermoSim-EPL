# ThermoSim Pro 🌡️

**Simulateur Thermodynamique Moteur (Otto & Diesel)**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/)

Une application interactive développée pour l'**École Polytechnique de Lomé (EPL)** permettant de simuler, visualiser et comparer les cycles thermodynamiques des moteurs à combustion interne.

---

## 🚀 Fonctionnalités

*   **Cycles Modélisés** : Otto (Beau de Rochas) et Diesel.
*   **Modèles de Gaz** : Gaz Parfait et Gaz Réel (Van der Waals).
*   **Laboratoire Virtuel** :
    *   Diagrammes interactifs **P-V** (Clapeyron) et **T-S** (Entropique).
    *   Calcul temps réel du Rendement, Travail, Puissance et Couple.
*   **Outils Avancés** :
    *   📸 **Comparaison** : Superposition de courbes pour analyser l'impact du taux de compression.
    *   📈 **Analyse de Sensibilité** : Courbe de rendement en fonction de $\tau$.
*   **Export** : Téléchargement des données brutes en JSON.

## 🛠️ Installation

1.  Cloner le dépôt :
    ```bash
    git clone https://github.com/OB-39/ThermoSim-EPL.git
    cd ThermoSim-EPL
    ```
2.  Installer les dépendances :
    ```bash
    pip install -r requirements.txt
    ```
3.  Lancer l'application :
    ```bash
    streamlit run streamlit_app.py
    ```

## � Contexte Académique

Projet étudiant réalisé par **OB-39** (EPL).
L'objectif est d'appliquer les principes de thermodynamique et les méthodes numériques (Simpson, Newton-Raphson) dans une simulation concrète.

---
*Powered by Python, Streamlit & Plotly.*
