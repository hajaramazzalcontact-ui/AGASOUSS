# ============================================================================
# 🚀 AZUL AGADIR - PUSH VERS LE NOUVEAU REPOSITORY
# ============================================================================
# Nouveau repo : hajaramazzalcontact-ui/AzulAgadir
# Ces 3 commandes vont être exécutées

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🚀 AZUL AGADIR - PUSH VERS NOUVEAU REPO                     ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# VÉRIFIER GIT
# ============================================================================
Write-Host "🔍 Vérification de Git..." -ForegroundColor Yellow
try {
    git --version | Out-Null
    Write-Host "✅ Git trouvé" -ForegroundColor Green
} catch {
    Write-Host "❌ Git n'est pas installé !" -ForegroundColor Red
    Write-Host "   Téléchargez : https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# ============================================================================
# VÉRIFIER/INITIALISER LE REPOSITORY LOCAL
# ============================================================================
Write-Host "📋 Vérification du repository local..." -ForegroundColor Yellow
if (-not (Test-Path ".git")) {
    Write-Host "🔧 Initialisation de Git..." -ForegroundColor Cyan
    git init | Out-Null
    git config user.name "AgadirGO"
    git config user.email "dev@azulagadir.ma"
    Write-Host "✅ Repository initialisé" -ForegroundColor Green
} else {
    Write-Host "✅ Repository Git déjà présent" -ForegroundColor Green
}
Write-Host ""

# ============================================================================
# AJOUTER LES FICHIERS
# ============================================================================
Write-Host "📋 Ajouter tous les fichiers..." -ForegroundColor Yellow
git add . | Out-Null
Write-Host "✅ Fichiers ajoutés" -ForegroundColor Green
Write-Host ""

# ============================================================================
# VÉRIFIER/CRÉER LE COMMIT
# ============================================================================
Write-Host "📋 Vérification des changements..." -ForegroundColor Yellow
$hasChanges = git status --porcelain
if ([string]::IsNullOrEmpty($hasChanges)) {
    Write-Host "ℹ️  Aucun changement à commiter (tout est synchro)" -ForegroundColor Cyan
} else {
    Write-Host "🔧 Création du commit..." -ForegroundColor Cyan
    git commit -m "Initial commit: AZUL AGADIR - Application touristique premium pour Agadir et Taghazout" | Out-Null
    Write-Host "✅ Commit créé" -ForegroundColor Green
}
Write-Host ""

# ============================================================================
# COMMANDE 1 : git remote add origin
# ============================================================================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📋 COMMANDE 1 : Ajouter le remote GitHub" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "Exécution :" -ForegroundColor Yellow
Write-Host "git remote add origin https://github.com/hajaramazzalcontact-ui/AzulAgadir.git" -ForegroundColor White
Write-Host ""

# Vérifier si origin existe déjà
$remoteExists = git remote | Select-String "origin"
if ($remoteExists) {
    Write-Host "⚠️  Remote 'origin' existe déjà, suppression..." -ForegroundColor Yellow
    git remote remove origin | Out-Null
}

git remote add origin https://github.com/hajaramazzalcontact-ui/AzulAgadir.git
Write-Host "✅ Remote ajoutée avec succès" -ForegroundColor Green
Write-Host ""

# ============================================================================
# COMMANDE 2 : git branch -M main
# ============================================================================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📋 COMMANDE 2 : Renommer la branche en 'main'" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "Exécution :" -ForegroundColor Yellow
Write-Host "git branch -M main" -ForegroundColor White
Write-Host ""

git branch -M main
Write-Host "✅ Branche renommée en 'main'" -ForegroundColor Green
Write-Host ""

# ============================================================================
# COMMANDE 3 : git push -u origin main (LA PLUS IMPORTANTE)
# ============================================================================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📋 COMMANDE 3 : POUSSER VERS GITHUB (IMPORTANTE !)" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "Exécution :" -ForegroundColor Yellow
Write-Host "git push -u origin main" -ForegroundColor White
Write-Host ""
Write-Host "⏳ ATTENDRE... (Git demandera vos identifiants)" -ForegroundColor Yellow
Write-Host ""

git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  ✅ SUCCÈS ! CODE POUSSÉ SUR GITHUB !                         ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔗 Repository GitHub :" -ForegroundColor Green
    Write-Host "   https://github.com/hajaramazzalcontact-ui/AzulAgadir" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📊 VÉRIFICATION :" -ForegroundColor Green
    Write-Host ""
    git remote -v
    Write-Host ""
    Write-Host "🔍 Branches :" -ForegroundColor Green
    git branch -a
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host "📊 PROCHAINES ÉTAPES :" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
    Write-Host ""
    Write-Host "1️⃣  Ouvrir : https://streamlit.io/cloud" -ForegroundColor White
    Write-Host "2️⃣  'Sign in with GitHub'" -ForegroundColor White
    Write-Host "3️⃣  'Create app'" -ForegroundColor White
    Write-Host "4️⃣  Repository : hajaramazzalcontact-ui/AzulAgadir" -ForegroundColor White
    Write-Host "5️⃣  Branch : main" -ForegroundColor White
    Write-Host "6️⃣  Main file path : app.py" -ForegroundColor White
    Write-Host "7️⃣  Click 'Deploy'" -ForegroundColor White
    Write-Host "8️⃣  Attendre 2-3 minutes" -ForegroundColor White
    Write-Host "9️⃣  Settings → Secrets → ANTHROPIC_API_KEY" -ForegroundColor White
    Write-Host "🔟 App en ligne !" -ForegroundColor White
    Write-Host ""
    Write-Host "🌊 URL de l'app :" -ForegroundColor Green
    Write-Host "   https://azul-agadir.streamlit.app" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "✨ Créé avec ❤️ par AgadirGO" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ ERREUR lors du push" -ForegroundColor Red
    Write-Host ""
    Write-Host "Solutions :" -ForegroundColor Yellow
    Write-Host "1. Vérifier votre connexion internet" -ForegroundColor Yellow
    Write-Host "2. Utiliser un Personal Access Token (pas le password GitHub) :" -ForegroundColor Yellow
    Write-Host "   → https://github.com/settings/tokens" -ForegroundColor Yellow
    Write-Host "   → 'Generate new token'" -ForegroundColor Yellow
    Write-Host "   → Cocher 'repo' + 'user:email'" -ForegroundColor Yellow
    Write-Host "   → Copier et utiliser comme password" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "3. Vérifier que le repository existe sur GitHub :" -ForegroundColor Yellow
    Write-Host "   → https://github.com/hajaramazzalcontact-ui/AzulAgadir" -ForegroundColor Yellow
}

Write-Host ""
