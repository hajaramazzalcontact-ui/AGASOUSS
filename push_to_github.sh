#!/bin/bash
# ==========================================
# 🚀 AZUL AGADIR - PUSH TO GITHUB SCRIPT
# ==========================================
# Ce script pousse votre application sur GitHub
# Usage: bash push_to_github.sh

set -e  # Exit on error

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║  🌊 AZUL AGADIR - GITHUB PUSH SCRIPT                            ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# ==========================================
# ÉTAPE 1 : Vérifier Git
# ==========================================
echo -e "${CYAN}📋 ÉTAPE 1 : Vérifier l'installation de Git...${NC}"
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ ERREUR : Git n'est pas installé !${NC}"
    echo -e "${YELLOW}   Installez Git : https://git-scm.com/download/linux${NC}"
    exit 1
fi
git_version=$(git --version)
echo -e "${GREEN}✅ Git trouvé : $git_version${NC}"
echo ""

# ==========================================
# ÉTAPE 2 : Initialiser Git (si nécessaire)
# ==========================================
echo -e "${CYAN}📋 ÉTAPE 2 : Initialiser Git...${NC}"
if [ -d ".git" ]; then
    echo -e "${GREEN}✅ Repository Git déjà initialisé${NC}"
else
    echo -e "${CYAN}🔧 Initialisation du repository...${NC}"
    git init
    echo -e "${GREEN}✅ Repository initialisé${NC}"
fi
echo ""

# ==========================================
# ÉTAPE 3 : Configurer Git
# ==========================================
echo -e "${CYAN}📋 ÉTAPE 3 : Configurer Git...${NC}"
echo -e "${CYAN}🔧 Configuration user.name...${NC}"
git config user.name "AgadirGO"
echo -e "${GREEN}✅ user.name configuré${NC}"

echo -e "${CYAN}🔧 Configuration user.email...${NC}"
git config user.email "dev@azulagadir.ma"
echo -e "${GREEN}✅ user.email configuré${NC}"
echo ""

# ==========================================
# ÉTAPE 4 : Vérifier les fichiers
# ==========================================
echo -e "${CYAN}📋 ÉTAPE 4 : Vérifier les fichiers...${NC}"
echo -e "${CYAN}🔍 Fichiers non versionné :${NC}"
git status -s || true
echo ""

# ==========================================
# ÉTAPE 5 : Ajouter les fichiers
# ==========================================
echo -e "${CYAN}📋 ÉTAPE 5 : Ajouter les fichiers...${NC}"
echo -e "${CYAN}🔧 Ajout de tous les fichiers...${NC}"
git add .
echo -e "${GREEN}✅ Fichiers ajoutés${NC}"
echo ""

# ==========================================
# ÉTAPE 6 : Vérifier sécurité
# ==========================================
echo -e "${CYAN}📋 ÉTAPE 6 : Vérifier la sécurité...${NC}"
if git status --porcelain | grep -q "\.env"; then
    echo -e "${YELLOW}⚠️  ATTENTION : .env risque d'être commité !${NC}"
    echo -e "${YELLOW}   Assurez-vous que .env est dans .gitignore${NC}"
else
    echo -e "${GREEN}✅ .env n'est pas versionné (sécurité OK)${NC}"
fi

if git status --porcelain | grep -q "\.db"; then
    echo -e "${YELLOW}⚠️  ATTENTION : *.db risque d'être commité !${NC}"
else
    echo -e "${GREEN}✅ *.db n'est pas versionné (sécurité OK)${NC}"
fi
echo ""

# ==========================================
# ÉTAPE 7 : Créer le premier commit
# ==========================================
echo -e "${CYAN}📋 ÉTAPE 7 : Créer le premier commit...${NC}"
echo -e "${CYAN}🔧 Commit en cours...${NC}"
git commit -m "Initial commit: AZUL AGADIR - Application touristique premium pour Agadir et Taghazout"
echo -e "${GREEN}✅ Commit créé${NC}"
echo ""

# ==========================================
# ÉTAPE 8 : Ajouter remote
# ==========================================
echo -e "${CYAN}📋 ÉTAPE 8 : Ajouter le repository GitHub...${NC}"

if git remote | grep -q "origin"; then
    echo -e "${YELLOW}⚠️  Remote 'origin' existe déjà...${NC}"
    echo -e "${CYAN}🔧 Suppression de l'ancienne remote...${NC}"
    git remote remove origin
    echo -e "${GREEN}✅ Ancienne remote supprimée${NC}"
fi

echo -e "${CYAN}🔧 Ajout de la nouvelle remote...${NC}"
git remote add origin https://github.com/hajaramazzalcontact-ui/AZUL-AGADIR.git
echo -e "${GREEN}✅ Remote ajoutée : https://github.com/hajaramazzalcontact-ui/AZUL-AGADIR.git${NC}"
echo ""

# ==========================================
# ÉTAPE 9 : Renommer branche en main
# ==========================================
echo -e "${CYAN}📋 ÉTAPE 9 : Renommer la branche...${NC}"
echo -e "${CYAN}🔧 Renommage en 'main'...${NC}"
git branch -M main
echo -e "${GREEN}✅ Branche renommée en 'main'${NC}"
echo ""

# ==========================================
# ÉTAPE 10 : Pousser vers GitHub
# ==========================================
echo -e "${CYAN}📋 ÉTAPE 10 : Pousser vers GitHub...${NC}"
echo -e "${YELLOW}🚀 PUSH EN COURS (cela peut prendre quelques secondes)...${NC}"
echo ""

if git push -u origin main; then
    echo ""
    echo -e "${GREEN}✅ SUCCÈS ! Code poussé sur GitHub !${NC}"
else
    echo ""
    echo -e "${RED}❌ ERREUR lors du push${NC}"
    echo -e "${YELLOW}   Cela peut être un problème d'authentification${NC}"
    echo ""
    echo -e "${CYAN}Solutions :${NC}"
    echo -e "${CYAN}1. Utiliser un Personal Access Token au lieu du password${NC}"
    echo -e "   → GitHub Settings → Developer settings → Personal access tokens"
    echo -e "   → Générer token avec 'repo' et 'user:email'"
    echo ""
    echo -e "${CYAN}2. Utiliser SSH au lieu de HTTPS${NC}"
    echo -e "   → Ajouter clé SSH à GitHub"
    echo ""
    exit 1
fi
echo ""

# ==========================================
# ÉTAPE 11 : Vérifier
# ==========================================
echo -e "${CYAN}📋 ÉTAPE 11 : Vérifier le résultat...${NC}"
echo -e "${CYAN}🔍 Remote configurée :${NC}"
git remote -v
echo ""
echo -e "${CYAN}🔍 Branches :${NC}"
git branch -a
echo ""

# ==========================================
# RÉSULTAT FINAL
# ==========================================
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║  ✅ BRAVO ! VOTRE CODE EST SUR GITHUB !                          ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}🔗 Repository GitHub :${NC}"
echo -e "   ${CYAN}https://github.com/hajaramazzalcontact-ui/AZUL-AGADIR${NC}"
echo ""
echo -e "${GREEN}📊 Étapes suivantes :${NC}"
echo -e "   ${CYAN}1. Ouvrir : https://streamlit.io/cloud${NC}"
echo -e "   ${CYAN}2. Sign in with GitHub${NC}"
echo -e "   ${CYAN}3. Create app${NC}"
echo -e "   ${CYAN}4. Repository : hajaramazzalcontact-ui/AZUL-AGADIR${NC}"
echo -e "   ${CYAN}5. Branch : main${NC}"
echo -e "   ${CYAN}6. Main file : app.py${NC}"
echo -e "   ${CYAN}7. Deploy${NC}"
echo -e "   ${CYAN}8. Ajouter ANTHROPIC_API_KEY dans Secrets${NC}"
echo ""
echo -e "${GREEN}🌊 Votre app sera en ligne sur :${NC}"
echo -e "   ${CYAN}https://azul-agadir.streamlit.app${NC}"
echo ""
echo -e "${GREEN}✨ Créé avec ❤️  par AgadirGO${NC}"
echo ""
