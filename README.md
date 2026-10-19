# AZUL AGADIR

Application touristique pour la ville d'Agadir (Souss-Massa, Maroc) — éditée par **AgadirGO**.

> **DÉMONSTRATION** — Tous les contenus, prix, horaires et avis affichés sont fictifs et marqués « DÉMO ». Aucune donnée réelle n'est stockée, aucun paiement ni envoi réel n'est déclenché.

## Contenu

- **Parcours visiteur** : Accueil, Découvrir, Restaurants, Hébergements, Transport, Carte, Mon séjour, Panier, Mon espace, Assistant IA, Avis, Mentions légales.
- **Back-office protégé** (qualifié par rôles : admin, manager, prestataire, chauffeur) : Tableau de bord, Catalogue, Réservations, Clients, Prestataires, Transport, Avis, Analyses, Messages, Réglages.
- **IA** : assistant conversationnel, recommandations, planificateur de séjour, résumé d'avis — ancrés sur le catalogue, sans aucun automatisme de sécurité (prix, horaire, disponibilité toujours confirmés par un humain).
- Multi-langues (fr, en, ar, es) · devise MAD · mobile-first.

## Lancement local

```bash
python -m venv .venv
.\.venv\Scripts\activate          # Windows
pip install -r requirements.txt
streamlit run app.py
```

## Lancement avec Streamlit Community Cloud

1. Poussez ce dépôt sur GitHub.
2. Sur https://share.streamlit.io, créez une app avec :
   - Repository : `hajaramazzalcontact-ui/AZUL-AGADIR`
   - Branch : `main`
   - Main file path : `app.py`

## Sécurité & confidentialité

- Mots de passe hachés, chiffrement Fernet des champs sensibles (email / téléphone), journal d'accès.
- Conformité loi marocaine 09-08 : consentement explicite, export, anonymisation.
- Avis uniquement vérifiés via une réservation terminée ; impossibilité de créer ou modifier un avis via l'UI.

## Comptes de démonstration

- Admin : `admin@azul.local` / `AzulDemo2026!`
- Manager : `manager@azul.local` / `AzulDemo2026!`
- Prestataire : `provider@azul.local` / `AzulDemo2026!`

## Configuration

Variables d'environnement (voir `.env.example`) :

| Variable | Rôle |
| --- | --- |
| `AZUL_MODE` | `demo` (par défaut) ou `production` |
| `ANTHROPIC_API_KEY` | Active Claude (sinon moteur local sans invention) |
| `ANTHROPIC_MODEL` | Défaut `claude-sonnet-4-6` |
| `AZUL_FERNET_KEY` | Clé de chiffrement des champs sensibles (production) |
| `AZUL_DATABASE_URL` | URL de la base SQL (défaut : SQLite locale) |

Ne committez jamais `.env`, `.streamlit/secrets.toml` ni la base `data/azul_demo.db` (déjà exclus par `.gitignore`).
