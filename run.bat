@echo off
REM Script de lancement d'AZUL AGADIR pour Windows

echo 🌊 Lancement d'AZUL AGADIR...

REM Installer les dépendances
pip install -r requirements.txt

REM Initialiser la base
python scripts/init_db.py

REM Lancer Streamlit
streamlit run app.py --server.port=8501

pause
