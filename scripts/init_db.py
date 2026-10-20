"""
Script d'initialisation de la base de données
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import init_db
from data.demo_data import load_demo_data

def main():
    """Initialise la base et charge les données démo"""
    print("🔧 Initialisation de la base de données...")
    
    try:
        init_db()
        print("✅ Schéma créé avec succès")
        
        print("\n📊 Chargement des données de démonstration...")
        load_demo_data()
        print("✅ Données démo chargées")
        
        print("\n🎉 Base de données prête !")
        print("Lancez l'application avec : streamlit run app.py")
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
