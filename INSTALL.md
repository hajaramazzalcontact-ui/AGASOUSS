# 📦 Installation AZUL AGADIR

Installation simple et rapide en 3 étapes ! 🚀

---

## 🎯 Étape 1 : Télécharger et Configurer

### Windows

```batch
REM 1. Ouvrir PowerShell / CMD
REM 2. Aller dans le dossier du projet
cd C:\Users\[ton-username]\azul-agadir

REM 3. Créer l'environnement virtuel
python -m venv venv
venv\Scripts\activate

REM 4. Installer les dépendances
pip install -r requirements.txt

REM 5. Configurer .env
copy .env.example .env
REM Édite .env et ajoute ta clé ANTHROPIC_API_KEY

REM 6. Lancer
python scripts/init_db.py
streamlit run app.py
```

### Linux / Mac

```bash
# 1. Terminal
cd ~/azul-agadir

# 2. Environnement virtuel
python3 -m venv venv
source venv/bin/activate

# 3. Dépendances
pip install -r requirements.txt

# 4. Configuration
cp .env.example .env
# Édite .env avec nano/vim

# 5. Lancer
python scripts/init_db.py
streamlit run app.py
```

---

## 🔑 Étape 2 : Obtenir la Clé API Anthropic

### Gratuit (vous avez $5 de crédits gratuits)

1. Aller à **https://console.anthropic.com/login**
2. Créer un compte (email + password)
3. Aller à **"API Keys"** dans le sidebar
4. Cliquer **"Create Key"**
5. Copier la clé générée : `sk-ant-...`
6. Coller dans le fichier `.env` :

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxx
```

---

## ✅ Étape 3 : Vérifier l'Installation

Après lancement, tu dois voir :

```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://[IP]:8501
```

### Ouvrir dans le navigateur

Clique sur **http://localhost:8501** ou ouvre manuellement ce lien

---

## 🎮 Tester l'Application

### ✅ Page d'Accueil
- [ ] Voir le titre "🌊 AZUL AGADIR"
- [ ] Voir les activités populaires
- [ ] Vérifier le sélecteur de langue (FR/EN)

### ✅ Découvrir Activités
- [ ] Filtrer par budget
- [ ] Rechercher "Dauphins"
- [ ] Ajouter une activité au panier

### ✅ Panier & Réservation
- [ ] Voir l'article ajouté
- [ ] Remplir le formulaire
- [ ] Confirmer la réservation
- [ ] Voir le code de confirmation

---

## ❌ Problèmes Courants

### "Erreur : ANTHROPIC_API_KEY not found"

**Solution :**
1. Ouvre `.env`
2. Vérifie que tu as écrit : `ANTHROPIC_API_KEY=sk-ant-...`
3. Relance : `streamlit run app.py`

### "Port 8501 already in use"

**Solution :**
```bash
streamlit run app.py --server.port=8502
```

### "ModuleNotFoundError: No module named 'streamlit'"

**Solution :**
```bash
# Vérifie que l'env virtuel est activé (tu dois voir (venv) dans le terminal)
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Puis réinstalle
pip install -r requirements.txt
```

### "Database error"

**Solution :**
```bash
# Réinitialiser la base
python scripts/init_db.py
streamlit run app.py
```

---

## 📁 Fichiers Importants

| Fichier | Rôle |
|---------|------|
| `app.py` | Application principale Streamlit |
| `.env` | Variables d'environnement (API keys) |
| `data/models.py` | Schéma base de données |
| `data/demo_data.py` | Données exemple |
| `azul_agadir.db` | Base SQLite (créée automatiquement) |

---

## 🔧 Commandes Utiles

```bash
# Réinitialiser la base
python scripts/init_db.py

# Lancer avec debug
streamlit run app.py --logger.level=debug

# Lancer sur tous les ports (pour accès réseau)
streamlit run app.py --server.address=0.0.0.0

# Afficher la version Streamlit
streamlit version
```

---

## 🌐 Prochaines Étapes

- ✅ **Installation = FAIT** ✓
- 📖 Lis `QUICKSTART.md` pour l'exploration
- 🚀 Lis `DEPLOYMENT.md` pour la production
- 📸 Lis `assets/data/README_SOURCES.md` pour les photos

---

## 💬 Besoin d'Aide ?

1. **Vérifier les logs** : console Streamlit
2. **Lire le README** : `README.md`
3. **Contacter** : support@azulagadir.ma

---

## ✨ Bravo !

Tu as réussi à installer **AZUL AGADIR** 🎉

L'app tourne maintenant sur **http://localhost:8501**

À bientôt ! 🌊

---

**Durée estimée** : 5-10 minutes
**Besoin d'aide ?** : support@azulagadir.ma
