# 🌊 AZUL AGADIR - Application Touristique Premium

**Bienvenue dans AZUL AGADIR**, la porte d'entrée unique du tourisme à Agadir, Taghazout et alentours.

## 🎯 Fonctionnalités Principales

### Pour les Touristes (10 onglets)
1. **🏠 Accueil** - Météo, compteurs animés, coups de cœur
2. **🔍 Découvrir** - Catalogue filtrable d'activités
3. **🍽️ Restaurants** - Annuaire et réservation de tables
4. **🏨 Hébergements** - Hôtels, riads, auberges
5. **🚕 Transport** - Taxis, forfaits, transferts
6. **🗺️ Carte** - Interactive avec trajets et trajets
7. **📅 Mon séjour** - Planificateur IA jour par jour
8. **🛒 Panier** - Réservation en un clic
9. **👤 Mon espace** - Billets, avis, réservations
10. **🤖 Assistant IA** - Chat multilingue (FR, EN, AR, ES)

### Pour les Gestionnaires (Back-office protégé)
1. **📊 Tableau de bord** - KPIs, graphiques, réservations du jour
2. **📚 Catalogue** - CRUD activités, restaurants, hébergements, spots, transports
3. **📋 Réservations** - Statuts, confirmations, relances
4. **👥 Clients** - Fiches, historique, segments
5. **🤝 Prestataires** - Partenaires, commissions, accès limité
6. **⭐ Avis** - Avis vérifiés, modération, réponses du gérant
7. **📈 Analyses** - Fréquentation, satisfaction, nationalités
8. **💬 Messages** - Modèles de confirmation, rappels, demande d'avis
9. **⚙️ Réglages** - Société, utilisateurs, langues, politique

## 🛠️ Installation

### Prérequis
- Python 3.11+
- pip ou conda
- Une clé API Anthropic (Claude) gratuite

### Étapes

```bash
# 1. Cloner ou télécharger le projet
cd azul-agadir

# 2. Créer un environnement virtuel (recommandé)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Édite .env et ajoute ta clé ANTHROPIC_API_KEY

# 5. Initialiser la base de données
python -m scripts.init_db

# 6. Lancer l'application
streamlit run app.py
```

L'app s'ouvre automatiquement sur **http://localhost:8501**

---

## 📁 Structure du Projet

```
azul-agadir/
├── app.py                    # Point d'entrée Streamlit
├── requirements.txt          # Dépendances Python
├── README.md                 # Ce fichier
├── .env.example              # Variables d'environnement
│
├── data/
│   ├── __init__.py
│   ├── database.py           # Initialisation SQLite + SQLAlchemy
│   ├── models.py             # Modèles ORM
│   └── demo_data.py          # Données fictives DÉMO
│
├── services/
│   ├── __init__.py
│   ├── activity_service.py   # CRUD activités
│   ├── restaurant_service.py # CRUD restaurants
│   ├── accommodation_service.py
│   ├── transport_service.py
│   ├── booking_service.py    # Gestion panier et réservations
│   ├── review_service.py     # Avis vérifiés
│   └── user_service.py       # Authentification et profils
│
├── ia/
│   ├── __init__.py
│   ├── planner.py            # Planificateur de séjour
│   ├── assistant.py          # Chat multilingue
│   ├── scorer.py             # Scoring des réservations
│   └── message_generator.py  # Génération messages
│
├── ui/
│   ├── __init__.py
│   ├── pages/
│   │   ├── home.py
│   │   ├── discover.py
│   │   ├── restaurants.py
│   │   ├── accommodations.py
│   │   ├── transport.py
│   │   ├── map.py
│   │   ├── trip_planner.py
│   │   ├── cart_checkout.py
│   │   ├── my_space.py
│   │   └── ai_assistant.py
│   │
│   ├── admin/
│   │   ├── dashboard.py
│   │   ├── catalog_mgmt.py
│   │   ├── booking_mgmt.py
│   │   ├── client_mgmt.py
│   │   ├── provider_mgmt.py
│   │   ├── review_mgmt.py
│   │   ├── analytics.py
│   │   ├── messaging.py
│   │   └── settings.py
│   │
│   ├── components/
│   │   ├── activity_card.py
│   │   ├── restaurant_card.py
│   │   ├── accommodation_card.py
│   │   ├── review_badge.py
│   │   ├── weather_widget.py
│   │   └── navbar.py
│   │
│   └── styles.py             # Palette couleurs, CSS
│
├── tests/
│   ├── test_scorer.py
│   ├── test_availability.py
│   ├── test_booking.py
│   └── test_reviews.py
│
├── assets/
│   └── data/
│       ├── activities_demo.json
│       ├── restaurants_demo.json
│       ├── accommodations_demo.json
│       ├── transport_demo.json
│       ├── spots_demo.json
│       └── reviews_demo.json
│
└── scripts/
    └── init_db.py            # Initialiser la base
```

---

## 🎨 Design et Identité Visuelle

### Palette Couleurs
- 🌊 **Bleu océan** : #0E6BA8 (primaire)
- 🌿 **Turquoise** : #14B8A6 (accents)
- 🏜️ **Sable** : #F4E4C1 (fond clair)
- 🧡 **Terracotta** : #D9663A (secondaire)
- 🌿 **Vert argan** : #4C7A4A (nature)
- 🌙 **Bleu nuit** : #0B1F3A (titres)
- ⭐ **Or** : #F5B700 (avis)

### Style
- Cartes arrondies avec ombres douces
- Photos grand format (16:9)
- Animations fluides
- Mode clair et sombre
- Responsive mobile-first
- Accessibilité (WCAG AA)

---

## 🚀 Lancement Rapide

```bash
# Démarrage simple
streamlit run app.py

# Avec rechargement automatique
streamlit run app.py --logger.level=debug

# Accès externe (VPS, serveur)
streamlit run app.py --server.address=0.0.0.0
```

---

## 🔐 Données de Démonstration

L'application démarre avec **données fictives clairement marquées "DÉMO"** :
- 21 activités exemple
- 25 restaurants exemple
- 15 hébergements exemple
- 6 services de transport
- 8 spots et plages
- 40 réservations exemple
- 60 avis vérifiés exemple

**⚠️ Mode Démo** : interface entièrement fonctionnelle mais avec données de test.

Pour passer à des données réelles, édite les fichiers JSON dans `assets/data/` ou crée des enregistrements via le back-office.

---

## 🔐 Identifiants par défaut (Démo)

### Administrateur
- Email : `admin@azulagadir.ma`
- Mot de passe : `admin123` (à changer en production)

### Gestionnaire
- Email : `manager@azulagadir.ma`
- Mot de passe : `manager123`

### Prestataire (exemple)
- Email : `provider@azulagadir.ma`
- Mot de passe : `provider123`

---

## 🌐 Multilingue

L'app supporte 4 langues avec sélecteur intégré :
- 🇫🇷 Français (défaut)
- 🇬🇧 English
- 🇲🇦 العربية (Arabe)
- 🇪🇸 Español

Les données multilingues sont stockées dans la base (`name_fr`, `name_en`, `name_ar`, `name_es`).

---

## 📸 Photos Réelles

Toutes les photos proviennent de sources libres de droits avec crédits :
- **Unsplash** (domaine public)
- **Pixabay** (CC0)
- **Pexels** (CC0)
- **Wikimedia Commons** (vérifié)

Les crédits s'affichent sous chaque image dans l'app.

---

## 🤖 Intelligence Artificielle

### Planificateur de Séjour
- Entrées : profil, durée, budget, météo, distances
- Sorties : programme jour par jour avec transport et repas
- Plan B en cas de mauvais temps

### Assistant Conversationnel
- Chat multilingue 24/7
- Réponses basées uniquement sur le catalogue
- Recommandations personnalisées
- Vente complémentaire intelligente

### Scoring des Réservations
- Note 0-100 basée sur : montant, délai, groupe, historique
- Priorise les confirmations et relances

### Génération de Messages
- Confirmation, rappel, demande d'avis
- Validés par l'humain avant envoi

---

## ✅ Qualité et Conformité

### Tests
```bash
# Exécuter tous les tests
pytest tests/

# Test spécifique
pytest tests/test_scorer.py
```

### Sécurité
- ✅ Mots de passe hachés (bcrypt)
- ✅ Rôles et permissions (RBAC)
- ✅ Journal des accès
- ✅ Chiffrement données sensibles
- ✅ Aucune donnée personnelle envoyée à l'IA

### Conformité
- ✅ RGPD (politique de confidentialité incluse)
- ✅ Loi marocaine 09-08 (données personnelles)
- ✅ Conditions générales intégrées
- ✅ Consentement explicite (cookies, marketing)
- ✅ Droit d'accès, modification, suppression

---

## 🔮 Évolutions Futures

- ✅ Intégration WhatsApp (confirmations, rappels, avis)
- ✅ Email (confirmation, reçu, facture)
- ✅ SMS (rappels critiques)
- ✅ Paiement en ligne (Stripe, Maroc Telecom)
- ✅ Application mobile (React Native, Flutter)
- ✅ Programme de fidélité (points, réductions)
- ✅ Blog et SEO (articles, itinéraires, rich snippets)
- ✅ Analytics avancées (Google Analytics, Hotjar)
- ✅ Connexion hôtels (sync réservations clients)
- ✅ Dashboard public pour prestataires

---

## 📞 Support et Contact

**AgadirGO - Équipe AZUL AGADIR**
- 📧 Email : support@azulagadir.ma
- 📱 WhatsApp : +212 XXXXX
- 🌐 Site : www.azulagadir.ma
- 📍 Agadir, Maroc

---

## 📄 Licence

Copyright © 2024 AgadirGO. Tous droits réservés.

Cette application est propriétaire. Reproduction interdite sans permission écrite.

---

## 🙏 Remerciements

- 📸 Photos : Unsplash, Pixabay, Pexels, Wikimedia Commons
- 🤖 IA : Anthropic (Claude Sonnet 3.5)
- 🗺️ Cartes : Folium, OpenStreetMap
- 🌤️ Météo : Open-Meteo

---

**Créé avec ❤️ pour les touristes et les amoureux d'Agadir** 🌊

Dernière mise à jour : Octobre 2024
