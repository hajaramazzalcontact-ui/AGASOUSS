# ============================================================================
# 🚀 AZUL AGADIR - PUSH TO GITHUB - RUN NOW !
# ============================================================================
# Ce script exécute les 3 commandes pour pousser votre code sur GitHub
# Exécutez simplement : .\RUN_NOW.ps1

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🌊 AZUL AGADIR - GITHUB PUSH - RUNNING NOW                  ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Vérifier Git
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

# Vérifier que nous sommes dans le bon dossier
if (-not (Test-Path ".git")) {
    Write-Host "⚠️  Initialisation de Git..." -ForegroundColor Yellow
    git init | Out-Null
    git config user.name "AgadirGO"
    git config user.email "dev@azulagadir.ma"
    git add . | Out-Null
    git commit -m "Initial commit: AZUL AGADIR" | Out-Null
    Write-Host "✅ Git initialisé et premier commit créé" -ForegroundColor Green
} else {
    Write-Host "✅ Repository Git déjà initialisé" -ForegroundColor Green
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
Write-Host "git remote add origin https://github.com/hajaramazzalcontact-ui/AZUL-AGADIR.git" -ForegroundColor White
Write-Host ""

# Vérifier si origin existe déjà
$remoteExists = git remote | Select-String "origin"
if ($remoteExists) {
    Write-Host "⚠️  Remote 'origin' existe déjà, suppression..." -ForegroundColor Yellow
    git remote remove origin | Out-Null
}

git remote add origin https://github.com/hajaramazzalcontact-ui/AZUL-AGADIR.git
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
# COMMANDE 3 : git push -u origin main
# ============================================================================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "📋 COMMANDE 3 : Pousser le code sur GitHub (LA PLUS IMPORTANTE)" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "Exécution :" -ForegroundColor Yellow
Write-Host "git push -u origin main" -ForegroundColor White
Write-Host ""
Write-Host "⏳ ATTENDRE... (Git demandera votre identifiant)" -ForegroundColor Yellow
Write-Host ""

git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  ✅ SUCCÈS ! VOTRE CODE EST SUR GITHUB !                      ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔗 Repository : https://github.com/hajaramazzalcontact-ui/AZUL-AGADIR" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 PROCHAINES ÉTAPES :" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1️⃣  Ouvrir : https://streamlit.io/cloud" -ForegroundColor White
    Write-Host "2️⃣  Se connecter avec GitHub" -ForegroundColor White
    Write-Host "3️⃣  Créer une nouvelle app" -ForegroundColor White
    Write-Host "4️⃣  Repository : hajaramazzalcontact-ui/AZUL-AGADIR" -ForegroundColor White
    Write-Host "5️⃣  Branch : main" -ForegroundColor White
    Write-Host "6️⃣  Main file : app.py" -ForegroundColor White
    Write-Host "7️⃣  Cliquer 'Deploy'" -ForegroundColor White
    Write-Host "8️⃣  Attendre 2-3 minutes" -ForegroundColor White
    Write-Host "9️⃣  Settings → Secrets → ANTHROPIC_API_KEY" -ForegroundColor White
    Write-Host "🔟 Votre app sera en ligne !" -ForegroundColor White
    Write-Host ""
    Write-Host "🌊 URL de l'app : https://azul-agadir.streamlit.app" -ForegroundColor Green
    Write-Host ""
    Write-Host "✨ Créé avec ❤️ par AgadirGO" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ ERREUR lors du push" -ForegroundColor Red
    Write-Host ""
    Write-Host "Solutions :" -ForegroundColor Yellow
    Write-Host "1. Vérifier votre connexion internet" -ForegroundColor Yellow
    Write-Host "2. Vérifier votre username GitHub (hajaramazzalcontact-ui)" -ForegroundColor Yellow
    Write-Host "3. Utiliser un Personal Access Token au lieu du password :" -ForegroundColor Yellow
    Write-Host "   → https://github.com/settings/tokens" -ForegroundColor Yellow
    Write-Host "   → 'Generate new token'" -ForegroundColor Yellow
    Write-Host "   → Cocher 'repo' + 'user:email'" -ForegroundColor Yellow
    Write-Host "   → Copier le token et utiliser comme password" -ForegroundColor Yellow
}

Write-Host ""
