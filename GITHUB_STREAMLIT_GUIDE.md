# 🚀 Guide Complet : GitHub + Streamlit Cloud

Ce guide vous montre comment pousser **AZUL AGADIR** sur GitHub et le déployer sur Streamlit Cloud.

---

## 📋 PRÉREQUIS

- ✅ Git installé ([télécharger](https://git-scm.com/download/win))
- ✅ Un compte GitHub ([github.com](https://github.com))
- ✅ Un compte Streamlit Cloud (gratuit, créé avec GitHub)
- ✅ L'application `azul-agadir` prête
- ✅ Fichier `.env` configuré (mais NON commité)

---

## 🔧 ÉTAPE 1 : Préparer le Repository Local

### 1.1 Ouvrir Git Bash ou PowerShell

**Sur Windows :**
- Ouvrir le dossier `azul-agadir`
- Clic droit → "Git Bash Here" (si installé)
- OU : PowerShell → `cd C:\Users\vams\Documents\Projet\ par\ défaut\azul-agadir`

### 1.2 Initialiser Git

```bash
cd azul-agadir
git init
```

**Résultat attendu :**
```
Initialized empty Git repository in C:\Users\...\azul-agadir\.git
```

### 1.3 Configurer votre identité Git

```bash
git config user.name "Votre Nom"
git config user.email "votre.email@example.com"
```

**Vérifier :**
```bash
git config --list
```

---

## 📁 ÉTAPE 2 : Vérifier le .gitignore

Le fichier `.gitignore` doit exclure les secrets et fichiers inutiles.

### 2.1 Vérifier le contenu de `.gitignore`

```bash
cat .gitignore
```

**Doit contenir :**
```
.env
.env.local
*.db
.streamlit/secrets.toml
__pycache__/
venv/
.vscode/
.idea/
```

### 2.2 Si `.gitignore` manque, le créer

```bash
# Créer le fichier
echo ".env
.env.local
*.db
.streamlit/
__pycache__/
venv/
.vscode/
.idea/
*.pyc
.DS_Store" > .gitignore

git add .gitignore
```

---

## 🎯 ÉTAPE 3 : Committer le Code Local

### 3.1 Vérifier les fichiers

```bash
git status
```

Vous devriez voir tous les fichiers Python, documentation, etc. (sauf `.env` et `*.db`)

### 3.2 Ajouter tous les fichiers

```bash
git add .
```

### 3.3 Vérifier avant de committer

```bash
git status
```

**Les fichiers sensibles (`.env`, `.db`) ne doivent PAS apparaître** ✓

### 3.4 Premier commit

```bash
git commit -m "Initial commit: AZUL AGADIR - Application touristique complète"
```

**Résultat attendu :**
```
[main (root-commit) abc123] Initial commit: AZUL AGADIR...
 XX files changed, XXXX insertions(+)
```

---

## 🌐 ÉTAPE 4 : Créer le Repository GitHub

### 4.1 Aller sur GitHub

1. Ouvrir https://github.com
2. Cliquer **"New"** (bouton vert) ou aller à https://github.com/new
3. **Repository name** : `AZUL-AGADIR`
4. **Description** : `Application touristique premium pour Agadir - Taghazout. Streamlit + SQLite + Claude IA`
5. **Public** ✓ (pour Streamlit Cloud)
6. ✅ **Initialize this repository with :** DÉCOCHER (ne pas créer README)
7. Cliquer **"Create repository"**

**URL : `https://github.com/votre-username/AZUL-AGADIR`**

---

## 📤 ÉTAPE 5 : Pousser le Code sur GitHub

### 5.1 Ajouter la remote

```bash
git remote add origin https://github.com/votre-username/AZUL-AGADIR.git
```

**Remplacer `votre-username` par votre vrai username GitHub**

### 5.2 Vérifier la remote

```bash
git remote -v
```

**Doit afficher :**
```
origin  https://github.com/votre-username/AZUL-AGADIR.git (fetch)
origin  https://github.com/votre-username/AZUL-AGADIR.git (push)
```

### 5.3 Renommer la branche en `main` (optionnel si déjà `main`)

```bash
git branch -M main
```

### 5.4 Pousser le code

```bash
git push -u origin main
```

**La première fois, Git vous demandera vos identifiants GitHub :**

#### ✅ Authentification HTTPS

```
Username for 'https://github.com': votre-username
Password for 'https://votre-username@github.com': [Votre token ou password]
```

**Recommandé : Utiliser un Token (Personal Access Token)**

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token"
3. Cocher : `repo`, `read:user`, `user:email`
4. Copier le token : `ghp_xxxxxxxxxxxx`
5. Coller comme password quand demandé
6. Sauvegarder le token ✓

**Résultat attendu :**
```
Enumerating objects: XX, done.
Counting objects: 100% (XX/XX)
Delta compression using up to 8 threads
Compressing objects: 100% (XX/XX)
Writing objects: 100% (XX/XX)
...
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

### 5.5 Vérifier sur GitHub

1. Ouvrir https://github.com/votre-username/AZUL-AGADIR
2. Vous devez voir tous vos fichiers ✓
3. Le `.env` ne doit PAS être visible ✓

---

## 🚀 ÉTAPE 6 : Déployer sur Streamlit Cloud

### 6.1 Créer un compte Streamlit Cloud

1. Ouvrir https://streamlit.io/cloud
2. Cliquer **"Sign up"**
3. Cliquer **"Sign in with GitHub"**
4. Autoriser Streamlit Cloud ✓
5. Connecté ! 🎉

### 6.2 Déployer l'application

1. Dans Streamlit Cloud, cliquer **"Create app"**
2. **Repository** : `votre-username/AZUL-AGADIR`
3. **Branch** : `main`
4. **Main file path** : `app.py`
5. Cliquer **"Deploy"** ✓

**L'app se déploiera automatiquement !** (2-3 minutes)

---

## 🔐 ÉTAPE 7 : Configurer les Secrets (Streamlit Cloud)

### 7.1 Ajouter votre clé API

1. Ouvrir votre app Streamlit Cloud
2. Cliquer ⚙️ **Settings** (coin supérieur droit)
3. Cliquer **"Secrets"**
4. Ajouter votre secret :

```toml
ANTHROPIC_API_KEY = "sk-ant-votre-cle-ici"
DATABASE_URL = "sqlite:///azul_agadir.db"
ENVIRONMENT = "production"
```

5. Cliquer **"Save"**
6. L'app redémarrera automatiquement ✓

**IMPORTANT : Vos secrets ne sont jamais visibles sur GitHub !** 🔒

---

## ✅ ÉTAPE 8 : Vérifier le Déploiement

### 8.1 URL de l'app

Votre app est maintenant accessible sur :
```
https://azul-agadir.streamlit.app
```

OU

```
https://votre-username-AZUL-AGADIR.streamlit.app
```

### 8.2 Tester l'app

1. Ouvrir l'URL
2. Cliquer "Découvrir"
3. Ajouter une activité au panier
4. Confirmer une réservation
5. Voir le code de confirmation ✓

---

## 📝 ÉTAPE 9 : Faire des Mises à Jour

Chaque fois que vous modifiez le code :

```bash
# 1. Vérifier les changements
git status

# 2. Ajouter les fichiers
git add .

# 3. Committer
git commit -m "Description de la modification"

# 4. Pousser
git push
```

**Streamlit Cloud redéploiera automatiquement en 1-2 minutes !** 🚀

---

## 🐛 TROUBLESHOOT

### Erreur : "fatal: origin already exists"

```bash
# Supprimer la remote existante
git remote remove origin

# Ajouter la nouvelle
git remote add origin https://github.com/votre-username/AZUL-AGADIR.git
```

### Erreur : ".env not found"

**C'est normal !** Le `.env` doit être créé localement.

**Sur Streamlit Cloud :**
1. Aller dans les Secrets (settings)
2. Ajouter `ANTHROPIC_API_KEY`

### Erreur : "Permission denied"

Utiliser un **Personal Access Token** au lieu du password GitHub

1. GitHub → Settings → Developer settings → Personal access tokens
2. Générer un token avec `repo` et `user:email`
3. Utiliser ce token comme password

### Erreur : "Module not found: streamlit"

Vérifier que `requirements.txt` est dans le dossier racine

```bash
# Vérifier
ls requirements.txt

# Doit afficher :
# requirements.txt
```

---

## 📊 Vérification Finale

| Étape | Fait ? |
|-------|--------|
| ✅ Repository local initialisé | [ ] |
| ✅ `.gitignore` créé | [ ] |
| ✅ Fichiers committés | [ ] |
| ✅ Repository GitHub créé | [ ] |
| ✅ Code poussé | [ ] |
| ✅ Streamlit Cloud connecté | [ ] |
| ✅ App déployée | [ ] |
| ✅ Secrets configurés | [ ] |
| ✅ App testée | [ ] |

---

## 🎯 Commandes Résumées

```bash
# 1. Initialiser
cd azul-agadir
git init
git config user.name "Votre Nom"
git config user.email "votre.email@example.com"

# 2. Committer
git add .
git commit -m "Initial commit: AZUL AGADIR"

# 3. Ajouter remote
git remote add origin https://github.com/votre-username/AZUL-AGADIR.git
git branch -M main

# 4. Pousser
git push -u origin main

# 5. Vérifier
git remote -v
git log
```

---

## 🌐 Résultat Final

✅ **Code sur GitHub** : https://github.com/votre-username/AZUL-AGADIR
✅ **App en ligne** : https://azul-agadir.streamlit.app
✅ **Secrets sécurisés** : Dans Streamlit Cloud
✅ **Mises à jour automatiques** : À chaque `git push`

---

## 📞 Support

- **Problème Git** ? → Lire le guide GitHub officiel
- **Problème Streamlit** ? → Voir la doc Streamlit Cloud
- **Problème de déploiement** ? → Vérifier les logs dans Streamlit Cloud

---

**Bon déploiement ! 🚀**

Votre application AZUL AGADIR est maintenant en ligne ! 🌊✨

À bientôt sur votre app : `https://azul-agadir.streamlit.app`
