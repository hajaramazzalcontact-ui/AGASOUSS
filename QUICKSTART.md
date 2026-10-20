# 🚀 QUICK START - AZUL AGADIR

Mise en route en **5 minutes** 🚀

## Prérequis

- Python 3.11+
- pip ou conda
- Une clé API Anthropic (gratuite : https://console.anthropic.com)

## Installation Rapide

### 1️⃣ Cloner et entrer dans le dossier

```bash
cd azul-agadir
```

### 2️⃣ Créer un environnement virtuel

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3️⃣ Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4️⃣ Configurer les variables d'environnement

```bash
# Copier le template
cp .env.example .env

# Éditer .env et ajouter ta clé API Anthropic
# ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxx
```

### 5️⃣ Lancer l'application

#### Sur Windows
```bash
run.bat
```

#### Sur Linux/Mac
```bash
bash run.sh
```

#### Ou manuellement
```bash
python scripts/init_db.py
streamlit run app.py
```

---

## 🌐 L'app devrait s'ouvrir à

**http://localhost:8501**

---

## 🎮 Tester l'Application

### 1. Page Accueil
- Voir les activités populaires
- Vérifier la météo (placeholder)
- Affichage des compteurs

### 2. Découvrir
- Filtrer par catégorie, budget, note
- Rechercher une activité
- Ajouter au panier

### 3. Panier
- Voir les articles
- Remplir le formulaire de réservation
- Confirmer et générer un code de confirmation

### 4. Admin (Optionnel)
- Cliquer sur l'icône ⚙️ Admin
- Email : `admin@azulagadir.ma`
- Mot de passe : `admin123`

---

## 📁 Structure Rapide

```
azul-agadir/
├── app.py                 # Application principale
├── data/
│   ├── models.py         # Schéma base de données
│   ├── database.py       # Configuration SQLite
│   └── demo_data.py      # Données fictives DÉMO
├── services/
│   ├── activity_service.py
│   ├── booking_service.py
│   ├── user_service.py
├── ia/
│   ├── assistant.py      # Chat multilingue
│   └── planner.py        # Planificateur séjour
└── tests/               # Tests unitaires
```

---

## 🔧 Dépannage

### ❌ Erreur "ANTHROPIC_API_KEY not set"
→ Ajoute ta clé dans le fichier `.env`

### ❌ Port 8501 déjà utilisé
```bash
streamlit run app.py --server.port=8502
```

### ❌ Base de données vide
```bash
python scripts/init_db.py
```

### ❌ Dépendances manquantes
```bash
pip install -r requirements.txt --upgrade
```

---

## 🎨 Première personnalisation

### Changer la couleur primaire
Édite `styles.css` dans `app.py` :
```css
--ocean: #0E6BA8;  /* Bleu actuel */
--ocean: #FF6B35;  /* Nouveau : Orange */
```

### Changer les données démo
Édite `data/demo_data.py` et relance :
```bash
python scripts/init_db.py
```

### Ajouter une langue
Ajoute dans `LANGUAGES` dict dans `app.py` :
```python
"ar": {
    "title": "🌊 أزول أغادير",
    ...
}
```

---

## 📊 Accéder à la Base de Données

SQLite crée un fichier local `azul_agadir.db`

### Visualiser les données
```bash
# Installer un client SQLite GUI (optionnel)
# https://sqlitebrowser.org/

# Ou en ligne de commande
sqlite3 azul_agadir.db
> SELECT COUNT(*) FROM activities;
```

---

## 🚀 Prochaines Étapes

1. ✅ **L'app fonctionne** → Explore les pages
2. ✅ **Ajouter plus de données** → Édite `demo_data.py`
3. ✅ **Personnaliser le design** → Modifie `styles.css`
4. ✅ **Connecter WhatsApp** → Voir `DEPLOYMENT.md`
5. ✅ **Déployer en prod** → Voir `DEPLOYMENT.md`

---

## 📚 Documentation Complète

- 📖 **README.md** : Guide complet
- 📖 **DEPLOYMENT.md** : Mise en production
- 📖 **assets/data/README_SOURCES.md** : Crédits photos

---

## 🆘 Support

Email : support@azulagadir.ma
GitHub Issues : (si applicable)

---

**Bienvenue dans AZUL AGADIR !** 🌊✨

Bon développement ! 🚀
