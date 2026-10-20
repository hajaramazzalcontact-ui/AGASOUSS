# ============================================================================
# 🚀 AZUL AGADIR - REPOUSSER SUR GITHUB - CORRIGER LE PROBLÈME
# ============================================================================
# Le premier push n'a pas marché. Ce script réessaie.

Write-Host ""
Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🚀 AZUL AGADIR - RE-PUSH GITHUB                             ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "⚠️  Le premier push n'a pas marché. On recommence !" -ForegroundColor Yellow
Write-Host ""

# ============================================================================
# VÉRIFIER GIT
# ============================================================================
Write-Host "🔍 Vérification de Git..." -ForegroundColor Cyan
try {
    git --version | Out-Null
    Write-Host "✅ Git trouvé" -ForegroundColor Green
} catch {
    Write-Host "❌ Git n'est pas installé !" -ForegroundColor Red
    exit 1
}
Write-Host ""

# ============================================================================
# VÉRIFIER L'ÉTAT
# ============================================================================
Write-Host "🔍 État du repository..." -ForegroundColor Cyan
Write-Host ""
git status
Write-Host ""

# ============================================================================
# AJOUTER TOUS LES FICHIERS
# ============================================================================
Write-Host "📋 Ajouter les fichiers..." -ForegroundColor Cyan
git add .
Write-Host "✅ Fichiers ajoutés" -ForegroundColor Green
Write-Host ""

# ============================================================================
# VÉRIFIER S'IL Y A QUELQUE CHOSE À COMMITER
# ============================================================================
$hasChanges = git status --porcelain
if ([string]::IsNullOrEmpty($hasChanges)) {
    Write-Host "ℹ️  Aucun changement à commiter (tout est déjà synchro)" -ForegroundColor Yellow
} else {
    Write-Host "📋 Créer un commit..." -ForegroundColor Cyan
    git commit -m "Fix: Re-push all files to GitHub"
    Write-Host "✅ Commit créé" -ForegroundColor Green
    Write-Host ""
}

# ============================================================================
# VÉRIFIER LE REMOTE
# ============================================================================
Write-Host "🌐 Vérifier le remote GitHub..." -ForegroundColor Cyan
$remote = git remote -v
if ([string]::IsNullOrEmpty($remote)) {
    Write-Host "⚠️  Aucun remote trouvé ! Ajouter le remote..." -ForegroundColor Yellow
    git remote add origin https://github.com/hajaramazzalcontact-ui/AZUL-AGADIR.git
    Write-Host "✅ Remote ajoutée" -ForegroundColor Green
} else {
    Write-Host "✅ Remote trouvée :" -ForegroundColor Green
    Write-Host $remote
}
Write-Host ""

# ============================================================================
# REPOUSSER VERS GITHUB
# ============================================================================
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host "🚀 RE-PUSH VERS GITHUB (LA PARTIE CRITIQUE)" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
Write-Host ""
Write-Host "⏳ Cela peut prendre 30 secondes..." -ForegroundColor Yellow
Write-Host ""

git push -u origin main --force

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║  ✅ SUCCÈS ! FICHIERS REPOUSSÉS SUR GITHUB !                  ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 VÉRIFICATION :" -ForegroundColor Green
    Write-Host ""
    git remote -v
    Write-Host ""
    Write-Host "PROCHAINE ÉTAPE :" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1️⃣  Aller sur Streamlit Cloud : https://streamlit.io/cloud" -ForegroundColor White
    Write-Host "2️⃣  Cliquer sur votre app AZUL AGADIR" -ForegroundColor White
    Write-Host "3️⃣  Cliquer sur les 3 points ⋮ → 'Reboot app'" -ForegroundColor White
    Write-Host "4️⃣  OU cliquer 'Deploy' pour redéployer" -ForegroundColor White
    Write-Host "5️⃣  Attendre 2-3 minutes" -ForegroundColor White
    Write-Host "6️⃣  ✅ App devrait démarrer !" -ForegroundColor White
    Write-Host ""
    Write-Host "🌊 URL : https://azul-agadir.streamlit.app" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ ERREUR LORS DU PUSH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Solutions :" -ForegroundColor Yellow
    Write-Host "1. Vérifier la connexion internet" -ForegroundColor Yellow
    Write-Host "2. Utiliser un Personal Access Token (pas le password)" -ForegroundColor Yellow
    Write-Host "   → https://github.com/settings/tokens" -ForegroundColor Yellow
    Write-Host "3. Essayer : git push -u origin main --force" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Ou contactez le support." -ForegroundColor Yellow
}

Write-Host ""
