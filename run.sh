#!/bin/bash
# Script de lancement d'AZUL AGADIR

echo "🌊 Lancement d'AZUL AGADIR..."

# Vérifier les dépendances
pip install -r requirements.txt > /dev/null 2>&1

# Initialiser la base
python scripts/init_db.py

# Lancer Streamlit
streamlit run app.py --server.port=8501 --server.address=localhost
