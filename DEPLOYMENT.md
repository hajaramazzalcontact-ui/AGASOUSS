# 🚀 DEPLOYMENT - Guide de Mise en Production

Guide complet pour déployer AZUL AGADIR en production.

---

## 📋 Checklist Pré-Déploiement

- [ ] Tests unitaires passent : `pytest tests/`
- [ ] Données réelles importées (pas de mode DÉMO)
- [ ] Clés API sécurisées (variables d'environnement)
- [ ] Base de données sauvegardée
- [ ] SSL/HTTPS configuré
- [ ] Rate limiting en place
- [ ] Monitoring configuré

---

## 🌍 Option 1 : Streamlit Cloud (Gratuit / Simple)

### Avantages
- ✅ Gratuit jusqu'à 3 apps
- ✅ Déploiement en 1 clic
- ✅ SSL automatique
- ✅ Idéal pour démonstration

### Inconvénients
- ❌ Ressources limitées
- ❌ Base de données en mémoire
- ❌ Pas de scaling

### Étapes

#### 1. Préparer le repository GitHub

```bash
git init
git add .
git commit -m "Initial commit: AZUL AGADIR"
git branch -M main
git remote add origin https://github.com/ton-username/azul-agadir.git
git push -u origin main
```

#### 2. Créer un `streamlit_secrets.toml`

Créer le fichier `.streamlit/secrets.toml` (ne pas committer) :

```toml
ANTHROPIC_API_KEY = "sk-ant-xxxxxxxx"
DATABASE_URL = "sqlite:///azul_agadir.db"
ENVIRONMENT = "production"
USE_DEMO_DATA = false
```

#### 3. Push vers GitHub (sans secrets !)

```bash
echo ".streamlit/secrets.toml" >> .gitignore
git add .gitignore
git commit -m "Add secrets to gitignore"
git push
```

#### 4. Déployer sur Streamlit Cloud

1. Aller à https://share.streamlit.io
2. Connecter GitHub
3. Sélectionner `azul-agadir` repo
4. Configurer les secrets dans l'interface
5. **Deploy** ✅

**URL finale** : `https://azul-agadir.streamlit.app`

---

## 🐳 Option 2 : Docker + VPS (Recommandé pour Production)

### Avantages
- ✅ Contrôle total
- ✅ Scaling horizontal
- ✅ Base de données persistent
- ✅ Monitoring complet

### Prérequis
- Docker installé
- VPS/Serveur (AWS, DigitalOcean, OVH, etc.)
- Domaine et SSL

### Étapes

#### 1. Créer Dockerfile

Créer `Dockerfile` à la racine :

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code applicatin
COPY . .

# Initialiser la base de données
RUN python scripts/init_db.py

# Exposer le port
EXPOSE 8501

# Lancer Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### 2. Créer docker-compose.yml

Créer `docker-compose.yml` :

```yaml
version: '3.8'

services:
  azul-agadir:
    build: .
    ports:
      - "8501:8501"
    environment:
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      DATABASE_URL: sqlite:///azul_agadir.db
      ENVIRONMENT: production
      STREAMLIT_SERVER_HEADLESS: true
    volumes:
      - ./azul_agadir.db:/app/azul_agadir.db
    restart: unless-stopped

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - azul-agadir
    restart: unless-stopped
```

#### 3. Configuration Nginx (Reverse Proxy)

Créer `nginx.conf` :

```nginx
events {
    worker_connections 1024;
}

http {
    upstream streamlit {
        server azul-agadir:8501;
    }

    server {
        listen 80;
        server_name azul-agadir.ma www.azul-agadir.ma;

        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name azul-agadir.ma www.azul-agadir.ma;

        ssl_certificate /etc/nginx/certs/cert.pem;
        ssl_certificate_key /etc/nginx/certs/key.pem;

        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        location / {
            proxy_pass http://streamlit;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Streamlit WebSocket
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Fichiers statiques
        location /static/ {
            alias /app/assets/;
            expires 30d;
        }
    }
}
```

#### 4. Déployer sur VPS

```bash
# SSH dans le serveur
ssh root@mon-vps.com

# Cloner le repo
git clone https://github.com/ton-username/azul-agadir.git
cd azul-agadir

# Créer .env
cat > .env << EOF
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx
DATABASE_URL=sqlite:///azul_agadir.db
ENVIRONMENT=production
EOF

# Obtenir SSL (Let's Encrypt)
sudo apt-get install certbot
certbot certonly -d azul-agadir.ma

# Copier certs dans dossier
mkdir certs
sudo cp /etc/letsencrypt/live/azul-agadir.ma/fullchain.pem certs/cert.pem
sudo cp /etc/letsencrypt/live/azul-agadir.ma/privkey.pem certs/key.pem

# Lancer Docker Compose
docker-compose up -d

# Vérifier
docker-compose logs -f azul-agadir
```

**URL finale** : `https://azul-agadir.ma`

---

## 🔐 Sécurité - Checklist

- [ ] Mots de passe hachés (bcrypt) ✅ (déjà fait)
- [ ] HTTPS/SSL configuré
- [ ] CORS configuré
- [ ] Rate limiting activé
- [ ] Variables d'env en secrets (jamais en Git)
- [ ] Firewall configuré
- [ ] Backups automatiques
- [ ] Logs surveillés
- [ ] Sanitization des données
- [ ] RGPD/Privacy policy appliquée

### Activer Rate Limiting (dans app.py)

```python
from streamlit.components.v1 import html
import time

MAX_REQUESTS_PER_MINUTE = 60

def rate_limit():
    if "request_times" not in st.session_state:
        st.session_state.request_times = []
    
    now = time.time()
    st.session_state.request_times = [
        t for t in st.session_state.request_times
        if now - t < 60
    ]
    
    if len(st.session_state.request_times) >= MAX_REQUESTS_PER_MINUTE:
        st.error("Rate limit dépassé. Attends 1 minute.")
        st.stop()
    
    st.session_state.request_times.append(now)
```

---

## 📊 Monitoring et Logging

### 1. Logs d'Application

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### 2. Monitoring (optionnel)

#### Datadog
```python
from datadog import initialize, api

options = {
    'api_key': 'xxx',
    'app_key': 'yyy'
}

initialize(**options)
```

#### Sentry (Error Tracking)
```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://xxx@sentry.io/yyy",
    environment="production"
)
```

---

## 📈 Performance Optimization

### 1. Caching

```python
import streamlit as st

@st.cache_data
def load_activities():
    db = SessionLocal()
    return ActivityService.get_all(db)

@st.cache_resource
def init_ai_client():
    return AIAssistant()
```

### 2. Database Optimization

```sql
-- Index sur colonnes fréquemment filtrées
CREATE INDEX idx_is_demo ON activities(is_demo);
CREATE INDEX idx_category ON activities(category);
CREATE INDEX idx_rating ON activities(avg_rating DESC);
CREATE INDEX idx_user_id ON bookings(user_id);
```

### 3. Image Optimization

- URLs externes optimisées (Unsplash avec paramètres `w=600&q=80`)
- Chargement lazy des images
- Compression WebP si possible

---

## 🔄 CI/CD (GitHub Actions)

Créer `.github/workflows/deploy.yml` :

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest
    
    - name: Run tests
      run: pytest tests/
    
    - name: Deploy to VPS
      run: |
        mkdir -p ~/.ssh
        echo "${{ secrets.SSH_KEY }}" > ~/.ssh/id_rsa
        chmod 600 ~/.ssh/id_rsa
        ssh -o StrictHostKeyChecking=no user@vps "cd azul-agadir && git pull && docker-compose restart"
```

---

## 🔄 Mise à Jour en Production

```bash
# Développement local
git add .
git commit -m "Update: feature X"
git push origin main

# Sur VPS (automatique avec CI/CD ou manuel)
cd azul-agadir
git pull
docker-compose restart azul-agadir
docker-compose logs -f azul-agadir
```

---

## 🆘 Troubleshooting

### ❌ Base de données corrompue
```bash
# Sauvegarde et réinitialisation
cp azul_agadir.db azul_agadir.db.backup
python scripts/init_db.py
```

### ❌ Memory leak
```bash
docker-compose restart azul-agadir
```

### ❌ Port en utilisation
```bash
# Trouver le processus
lsof -i :8501

# Terminer
kill -9 PID
```

---

## 📞 Support

- 📧 support@azulagadir.ma
- 📞 +212 XXXX XXXXX
- 🌐 www.azulagadir.ma

---

**Bon déploiement !** 🚀

Dernière mise à jour : Octobre 2024
