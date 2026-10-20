# ==========================================
# 🚀 AZUL AGADIR - PUSH TO GITHUB SCRIPT
# ==========================================
# Ce script pousse votre application sur GitHub en une seule commande
# Exécutez-le dans PowerShell dans le dossier azul-agadir/

Write-Host "╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🌊 AZUL AGADIR - GITHUB PUSH SCRIPT                            ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Couleurs
$Success = "Green"
$Warning = "Yellow"
$Error = "Red"
$Info = "Cyan"

# ==========================================
# ÉTAPE 1 : Vérifier Git
# ==========================================
Write-Host "📋 ÉTAPE 1 : Vérifier l'installation de Git..." -ForegroundColor $Info
try {
    $gitVersion = git --version
    Write-Host "✅ Git trouvé : $gitVersion" -ForegroundColor $Success
} catch {
    Write-Host "❌ ERREUR : Git n'est pas installé !" -ForegroundColor $Error
    Write-Host "   Téléchargez Git : https://git-scm.com/download/win" -ForegroundColor $Warning
    exit 1
}
Write-Host ""

# ==========================================
# ÉTAPE 2 : Initialiser Git (si nécessaire)
# ==========================================
Write-Host "📋 ÉTAPE 2 : Initialiser Git..." -ForegroundColor $Info
if (Test-Path ".git") {
    Write-Host "✅ Repository Git déjà initialisé" -ForegroundColor $Success
} else {
    Write-Host "🔧 Initialisation du repository..." -ForegroundColor $Info
    git init
    Write-Host "✅ Repository initialisé" -ForegroundColor $Success
}
Write-Host ""

# ==========================================
# ÉTAPE 3 : Configurer Git
# ==========================================
Write-Host "📋 ÉTAPE 3 : Configurer Git..." -ForegroundColor $Info
Write-Host "🔧 Configuration user.name..." -ForegroundColor $Info
git config user.name "AgadirGO"
Write-Host "✅ user.name configuré" -ForegroundColor $Success

Write-Host "🔧 Configuration user.email..." -ForegroundColor $Info
git config user.email "dev@azulagadir.ma"
Write-Host "✅ user.email configuré" -ForegroundColor $Success
Write-Host ""

# ==========================================
# ÉTAPE 4 : Vérifier les fichiers
# ==========================================
Write-Host "📋 ÉTAPE 4 : Vérifier les fichiers..." -ForegroundColor $Info
Write-Host "🔍 Fichiers non versionné :" -ForegroundColor $Info
git status -s
Write-Host ""

# ==========================================
# ÉTAPE 5 : Ajouter les fichiers
# ==========================================
Write-Host "📋 ÉTAPE 5 : Ajouter les fichiers..." -ForegroundColor $Info
Write-Host "🔧 Ajout de tous les fichiers avec 'git add .'..." -ForegroundColor $Info
git add .
Write-Host "✅ Fichiers ajoutés" -ForegroundColor $Success
Write-Host ""

# ==========================================
# ÉTAPE 6 : Vérifier .env n'est pas inclus
# ==========================================
Write-Host "📋 ÉTAPE 6 : Vérifier la sécurité..." -ForegroundColor $Info
$status = git status --porcelain
if ($status -match "\.env") {
    Write-Host "⚠️  ATTENTION : .env risque d'être commité !" -ForegroundColor $Warning
    Write-Host "   Assurez-vous que .env est dans .gitignore" -ForegroundColor $Warning
} else {
    Write-Host "✅ .env n'est pas versionné (sécurité OK)" -ForegroundColor $Success
}

if ($status -match "\.db") {
    Write-Host "⚠️  ATTENTION : *.db risque d'être commité !" -ForegroundColor $Warning
} else {
    Write-Host "✅ *.db n'est pas versionné (sécurité OK)" -ForegroundColor $Success
}
Write-Host ""

# ==========================================
# ÉTAPE 7 : Premier commit
# ==========================================
Write-Host "📋 ÉTAPE 7 : Créer le premier commit..." -ForegroundColor $Info
Write-Host "🔧 Commit en cours..." -ForegroundColor $Info
git commit -m "Initial commit: AZUL AGADIR - Application touristique premium pour Agadir et Taghazout"
Write-Host "✅ Commit créé" -ForegroundColor $Success
Write-Host ""

# ==========================================
# ÉTAPE 8 : Ajouter remote
# ==========================================
Write-Host "📋 ÉTAPE 8 : Ajouter le repository GitHub..." -ForegroundColor $Info

# Vérifier si remote existe
$remoteExists = git remote | Select-String "origin"
if ($remoteExists) {
    Write-Host "⚠️  Remote 'origin' existe déjà..." -ForegroundColor $Warning
    Write-Host "🔧 Suppression de l'ancienne remote..." -ForegroundColor $Info
    git remote remove origin
    Write-Host "✅ Ancienne remote supprimée" -ForegroundColor $Success
}

Write-Host "🔧 Ajout de la nouvelle remote..." -ForegroundColor $Info
git remote add origin https://github.com/hajaramazzalcontact-ui/AZUL-AGADIR.git
Write-Host "✅ Remote ajoutée : https://github.com/hajaramazzalcontact-ui/AZUL-AGADIR.git" -ForegroundColor $Success
Write-Host ""

# ==========================================
# ÉTAPE 9 : Renommer branche en main
# ==========================================
Write-Host "📋 ÉTAPE 9 : Renommer la branche..." -ForegroundColor $Info
Write-Host "🔧 Renommage en 'main'..." -ForegroundColor $Info
git branch -M main
Write-Host "✅ Branche renommée en 'main'" -ForegroundColor $Success
Write-Host ""

# ==========================================
# ÉTAPE 10 : Pousser vers GitHub
# ==========================================
Write-Host "📋 ÉTAPE 10 : Pousser vers GitHub..." -ForegroundColor $Info
Write-Host "🚀 PUSH EN COURS (cela peut prendre quelques secondes)..." -ForegroundColor $Warning
Write-Host ""

try {
    git push -u origin main
    Write-Host ""
    Write-Host "✅ SUCCÈS ! Code poussé sur GitHub !" -ForegroundColor $Success
} catch {
    Write-Host ""
    Write-Host "❌ ERREUR lors du push" -ForegroundColor $Error
    Write-Host "   Cela peut être un problème d'authentification" -ForegroundColor $Warning
    Write-Host ""
    Write-Host "Solutions :" -ForegroundColor $Info
    Write-Host "1. Utiliser un Personal Access Token au lieu du password" -ForegroundColor $Info
    Write-Host "   → GitHub Settings → Developer settings → Personal access tokens" -ForegroundColor $Info
    Write-Host "   → Générer token avec 'repo' et 'user:email'" -ForegroundColor $Info
    Write-Host ""
    Write-Host "2. Utiliser SSH au lieu de HTTPS" -ForegroundColor $Info
    Write-Host "   → Ajouter clé SSH à GitHub" -ForegroundColor $Info
    Write-Host ""
    exit 1
}
Write-Host ""

# ==========================================
# ÉTAPE 11 : Vérifier
# ==========================================
Write-Host "📋 ÉTAPE 11 : Vérifier le résultat..." -ForegroundColor $Info
Write-Host "🔍 Remote configurée :" -ForegroundColor $Info
git remote -v
Write-Host ""
Write-Host "🔍 Branches :" -ForegroundColor $Info
git branch -a
Write-Host ""

# ==========================================
# RÉSULTAT FINAL
# ==========================================
Write-Host "╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor $Success
Write-Host "║  ✅ BRAVO ! VOTRE CODE EST SUR GITHUB !                          ║" -ForegroundColor $Success
Write-Host "╚═══════════════════════════════════════════════════════════════════╝" -ForegroundColor $Success
Write-Host ""
Write-Host "🔗 Repository GitHub :" -ForegroundColor $Success
Write-Host "   https://github.com/hajaramazzalcontact-ui/AZUL-AGADIR" -ForegroundColor $Info
Write-Host ""
Write-Host "📊 Étapes suivantes :" -ForegroundColor $Success
Write-Host "   1. Ouvrir : https://streamlit.io/cloud" -ForegroundColor $Info
Write-Host "   2. Sign in with GitHub" -ForegroundColor $Info
Write-Host "   3. Create app" -ForegroundColor $Info
Write-Host "   4. Repository : hajaramazzalcontact-ui/AZUL-AGADIR" -ForegroundColor $Info
Write-Host "   5. Branch : main" -ForegroundColor $Info
Write-Host "   6. Main file : app.py" -ForegroundColor $Info
Write-Host "   7. Deploy" -ForegroundColor $Info
Write-Host "   8. Ajouter ANTHROPIC_API_KEY dans Secrets" -ForegroundColor $Info
Write-Host ""
Write-Host "🌊 Votre app sera en ligne sur :" -ForegroundColor $Success
Write-Host "   https://azul-agadir.streamlit.app" -ForegroundColor $Info
Write-Host ""
Write-Host "✨ Créé avec ❤️ par AgadirGO" -ForegroundColor $Success
Write-Host ""
