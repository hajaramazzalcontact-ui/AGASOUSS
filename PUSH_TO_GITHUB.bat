@echo off
REM ==========================================
REM 🚀 AZUL AGADIR - PUSH TO GITHUB SCRIPT
REM ==========================================
REM Ce script pousse votre application sur GitHub

setlocal enabledelayedexpansion

echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║  🌊 AZUL AGADIR - GITHUB PUSH SCRIPT                            ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

REM ==========================================
REM ÉTAPE 1 : Vérifier Git
REM ==========================================
echo 📋 ÉTAPE 1 : Vérifier l'installation de Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERREUR : Git n'est pas installé !
    echo.
    echo Téléchargez Git : https://git-scm.com/download/win
    pause
    exit /b 1
)
echo ✅ Git trouvé
echo.

REM ==========================================
REM ÉTAPE 2 : Initialiser Git (si nécessaire)
REM ==========================================
echo 📋 ÉTAPE 2 : Initialiser Git...
if exist ".git" (
    echo ✅ Repository Git déjà initialisé
) else (
    echo 🔧 Initialisation du repository...
    git init
    echo ✅ Repository initialisé
)
echo.

REM ==========================================
REM ÉTAPE 3 : Configurer Git
REM ==========================================
echo 📋 ÉTAPE 3 : Configurer Git...
echo 🔧 Configuration user.name...
git config user.name "AgadirGO"
echo ✅ user.name configuré

echo 🔧 Configuration user.email...
git config user.email "dev@azulagadir.ma"
echo ✅ user.email configuré
echo.

REM ==========================================
REM ÉTAPE 4 : Vérifier les fichiers
REM ==========================================
echo 📋 ÉTAPE 4 : Vérifier les fichiers...
echo 🔍 État Git :
git status -s
echo.

REM ==========================================
REM ÉTAPE 5 : Ajouter les fichiers
REM ==========================================
echo 📋 ÉTAPE 5 : Ajouter les fichiers...
echo 🔧 Ajout de tous les fichiers...
git add .
echo ✅ Fichiers ajoutés
echo.

REM ==========================================
REM ÉTAPE 6 : Vérifier sécurité
REM ==========================================
echo 📋 ÉTAPE 6 : Vérifier la sécurité...
git status --porcelain | findstr ".env" >nul
if not errorlevel 1 (
    echo ⚠️  ATTENTION : .env risque d'être commité !
    echo    Assurez-vous que .env est dans .gitignore
) else (
    echo ✅ .env n'est pas versionné (sécurité OK)
)

git status --porcelain | findstr ".db" >nul
if not errorlevel 1 (
    echo ⚠️  ATTENTION : *.db risque d'être commité !
) else (
    echo ✅ *.db n'est pas versionné (sécurité OK)
)
echo.

REM ==========================================
REM ÉTAPE 7 : Créer le premier commit
REM ==========================================
echo 📋 ÉTAPE 7 : Créer le premier commit...
echo 🔧 Commit en cours...
git commit -m "Initial commit: AZUL AGADIR - Application touristique premium pour Agadir et Taghazout"
echo ✅ Commit créé
echo.

REM ==========================================
REM ÉTAPE 8 : Ajouter remote
REM ==========================================
echo 📋 ÉTAPE 8 : Ajouter le repository GitHub...
git remote | findstr "origin" >nul
if not errorlevel 1 (
    echo ⚠️  Remote 'origin' existe déjà...
    echo 🔧 Suppression de l'ancienne remote...
    git remote remove origin
    echo ✅ Ancienne remote supprimée
)

echo 🔧 Ajout de la nouvelle remote...
git remote add origin https://github.com/hajaramazzalcontact-ui/AZUL-AGADIR.git
echo ✅ Remote ajoutée : https://github.com/hajaramazzalcontact-ui/AZUL-AGADIR.git
echo.

REM ==========================================
REM ÉTAPE 9 : Renommer branche en main
REM ==========================================
echo 📋 ÉTAPE 9 : Renommer la branche...
echo 🔧 Renommage en 'main'...
git branch -M main
echo ✅ Branche renommée en 'main'
echo.

REM ==========================================
REM ÉTAPE 10 : Pousser vers GitHub
REM ==========================================
echo 📋 ÉTAPE 10 : Pousser vers GitHub...
echo 🚀 PUSH EN COURS (cela peut prendre quelques secondes)...
echo.

git push -u origin main
if errorlevel 1 (
    echo.
    echo ❌ ERREUR lors du push
    echo    Cela peut être un problème d'authentification
    echo.
    echo Solutions :
    echo 1. Utiliser un Personal Access Token au lieu du password
    echo    - GitHub Settings ^> Developer settings ^> Personal access tokens
    echo    - Générer token avec 'repo' et 'user:email'
    echo.
    echo 2. Utiliser SSH au lieu de HTTPS
    echo    - Ajouter clé SSH à GitHub
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ SUCCÈS ! Code poussé sur GitHub !
echo.

REM ==========================================
REM ÉTAPE 11 : Vérifier
REM ==========================================
echo 📋 ÉTAPE 11 : Vérifier le résultat...
echo 🔍 Remote configurée :
git remote -v
echo.
echo 🔍 Branches :
git branch -a
echo.

REM ==========================================
REM RÉSULTAT FINAL
REM ==========================================
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║  ✅ BRAVO ! VOTRE CODE EST SUR GITHUB !                          ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.
echo 🔗 Repository GitHub :
echo    https://github.com/hajaramazzalcontact-ui/AZUL-AGADIR
echo.
echo 📊 Étapes suivantes :
echo    1. Ouvrir : https://streamlit.io/cloud
echo    2. Sign in with GitHub
echo    3. Create app
echo    4. Repository : hajaramazzalcontact-ui/AZUL-AGADIR
echo    5. Branch : main
echo    6. Main file : app.py
echo    7. Deploy
echo    8. Ajouter ANTHROPIC_API_KEY dans Secrets
echo.
echo 🌊 Votre app sera en ligne sur :
echo    https://azul-agadir.streamlit.app
echo.
echo ✨ Créé avec coeur par AgadirGO
echo.
pause
