"""Jeu de données DÉMO d'Azul AGADIR.

Toutes les lignes sont fictives, marquées `is_demo = True`, et utilisent des
prix et horaires de démonstration. Aucune donnée réelle de client, aucun avis
réel et aucun tarif réel ne sont présents. La base démo est distincte de la
base de production.
"""
from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta

from sqlalchemy import select

from src.config import ADMIN_EMAIL, ADMIN_PASSWORD, CANCELLATION_POLICY
from src.services.security import (
    encrypt_text,
    hash_identifier,
    hash_password,
    new_public_reference,
    sign_ticket_payload,
)
from .base import utcnow
from .models import (
    AccommodationDetail,
    ActivityDetail,
    Anomaly,
    AuditLog,
    AvailabilitySlot,
    AIConversation,
    AIMessage,
    Booking,
    BookingItem,
    BookingStatusHistory,
    CatalogItem,
    CatalogMedia,
    Customer,
    Consent,
    Driver,
    Favorite,
    Itinerary,
    ItineraryDay,
    ItineraryItem,
    LegalDocument,
    MessageTemplate,
    OutboxMessage,
    Payment,
    Provider,
    ProviderCommission,
    RatingSnapshot,
    RestaurantDetail,
    Review,
    ReviewInvitation,
    ReviewSummary,
    Setting,
    SpotDetail,
    Ticket,
    TransportAssignment,
    TransportDetail,
    TransportRun,
    User,
    Variant,
    Vehicle,
)
from .session import session_scope

random.seed(20261019)

VIBES = {
    "aventure": {"fr": "Aventure", "en": "Adventure", "ar": "مغامرة", "es": "Aventura"},
    "famille": {"fr": "Famille", "en": "Family", "ar": "عائلة", "es": "Familia"},
    "culture": {"fr": "Culture et artisanat", "en": "Culture & crafts", "ar": "ثقافة وحرف", "es": "Cultura y artesanía"},
    "nature": {"fr": "Nature et animaux", "en": "Nature & animals", "ar": "طبيعة وحيوانات", "es": "Naturaleza y animales"},
    "mer": {"fr": "Mer", "en": "Sea", "ar": "البحر", "es": "Mar"},
    "gastronomie": {"fr": "Gastronomie", "en": "Food", "ar": "مأكولات", "es": "Gastronomía"},
    "detente": {"fr": "Détente", "en": "Relaxation", "ar": "استرخاء", "es": "Descanso"},
    "jeux": {"fr": "Jeux et loisirs", "en": "Games & leisure", "ar": "ألعاب وترفيه", "es": "Juegos y ocio"},
}


def T(fr: str, en: str | None = None, ar: str | None = None, es: str | None = None) -> dict:
    """Traduction courte avec repli français."""
    return {"fr": fr, "en": en or fr, "ar": ar or en or fr, "es": es or en or fr}


def _catalog(
    kind: str,
    slug: str,
    name: dict,
    tagline: str,
    short: str,
    long: str,
    vibes: list[str],
    lat: float,
    lng: float,
    distance: float,
    price: float | None,
    price_unit: str,
    capacity: int,
    provider_id: int,
    district: str = "Agadir",
    zone: str = "Agadir",
    booking_mode: str = "request",
    tags: list[str] | None = None,
) -> CatalogItem:
    return CatalogItem(
        kind=kind,
        slug=slug,
        name=name,
        tagline=T(tagline, tagline, tagline, tagline),
        short_description=T(short),
        long_description=T(long),
        vibes=vibes,
        tags=tags or [],
        address=f"{district}, {zone} — adresse de démonstration",
        district=district,
        zone=zone,
        lat=lat,
        lng=lng,
        distance_center_km=distance,
        languages=["fr", "en", "ar", "es"],
        capacity=capacity,
        price_from=price,
        price_unit=price_unit,
        price_status="demo" if price is not None else "missing",
        price_source="Donnée fictive de démonstration" if price is not None else None,
        price_updated_at=utcnow() if price is not None else None,
        booking_mode=booking_mode,
        provider_id=provider_id,
        status="published",
        is_demo=True,
    )


def _media(session, item: CatalogItem, captions: list[str]):
    for i, caption in enumerate(captions):
        session.add(CatalogMedia(
            catalog_id=item.id,
            kind="image",
            caption=T(caption),
            credit="Visuel abstrait généré pour la démonstration Azul AGADIR",
            rights_basis="demo",
            license_name="Démonstration — ne pas utiliser en production",
            sort_order=i,
            is_cover=(i == 0),
            is_demo=True,
        ))


def _slot(session, variant: Variant, start: datetime, duration: int, capacity: int | None = None):
    session.add(AvailabilitySlot(
        variant_id=variant.id,
        start_at=start,
        end_at=start + timedelta(minutes=duration),
        capacity=capacity or variant.capacity_max or 10,
        booked_count=0,
        status="open",
        languages=["fr", "en", "ar"],
        source="demo",
        is_demo=True,
    ))


def _ensure_admin(session):
    existing = session.scalar(select(User).where(User.email_hash == hash_identifier(ADMIN_EMAIL)))
    if existing:
        return existing
    admin = User(
        email_hash=hash_identifier(ADMIN_EMAIL),
        email_enc=encrypt_text(ADMIN_EMAIL),
        password_hash=hash_password(ADMIN_PASSWORD),
        full_name="Administrateur Azul",
        role="admin",
        locale="fr",
        is_demo=True,
    )
    session.add(admin)
    session.flush()
    return admin


def seed_if_empty():
    with session_scope() as session:
        if session.scalar(select(CatalogItem.id).limit(1)):
            return
        _seed_all(session)


def _seed_all(session):
    admin = _ensure_admin(session)
    now = utcnow()
    today = date.today()

    # ---------------------------------------------------------------- acteurs
    providers = []
    provider_specs = [
        ("Agadir Aventure DÉMO", "activité", 15),
        ("Ocean Experiences DÉMO", "mer", 18),
        ("Médina & Saveurs DÉMO", "restaurant", 12),
        ("Taghazout Surf Collective DÉMO", "hébergement", 10),
        ("Atlas Transferts DÉMO", "transport", 20),
        ("Argan Nature DÉMO", "nature", 15),
        ("Atelier Maghribi DÉMO", "culture", 12),
        ("Souss Hôtellerie DÉMO", "hébergement", 10),
    ]
    for name, kind, commission in provider_specs:
        p = Provider(
            name=name, kind=kind, contact_name="Contact démo",
            phone_enc=encrypt_text("+212600000000"), email_enc=encrypt_text("partenaire@example.test"),
            commission_rate=commission, contract_ref=f"DEMO-{len(providers)+1:02d}",
            is_verified=True, is_demo=True,
        )
        session.add(p)
        providers.append(p)
    session.flush()

    for name, email, role, provider in [
        ("Gestionnaire Azul", "manager@azul.local", "manager", None),
        ("Prestataire Aventure", "provider@azul.local", "provider", providers[0]),
    ]:
        session.add(User(
            email_hash=hash_identifier(email), email_enc=encrypt_text(email),
            password_hash=hash_password(ADMIN_PASSWORD), full_name=name,
            role=role, provider_id=provider.id if provider else None, is_demo=True,
        ))

    drivers = []
    vehicles = []
    for i in range(6):
        d = Driver(
            provider_id=providers[4].id, full_name=f"Chauffeur Démo {i+1}",
            phone_enc=encrypt_text(f"+21260000010{i}"),
            languages=["fr", "en"] + (["ar"] if i % 2 == 0 else []),
            license_ref_enc=encrypt_text(f"PERMIS-DEMO-{i+1}"),
            rating_avg=round(4.3 + (i % 5) * 0.12, 1), rating_count=8 + i,
            is_demo=True,
        )
        v = Vehicle(
            provider_id=providers[4].id, label=f"Van Azul Démo {i+1}",
            plate=f"DEMO-{100+i}", capacity=6 if i < 3 else 15,
            luggage=4 if i < 3 else 10, vehicle_type="van" if i < 3 else "minibus", is_demo=True,
        )
        session.add_all([d, v])
        drivers.append(d)
        vehicles.append(v)
    session.flush()

    # --------------------------------------------------------------- clients
    first_names = ["Yasmine", "Lucas", "Sofia", "Omar", "Emma", "Noah", "Amina", "Liam", "Clara", "Youssef",
                   "Marta", "Hugo", "Nora", "Elias", "Lina", "Adam", "Chloé", "Rayan", "Inès", "Tom",
                   "Salma", "David"]
    last_names = ["El Amrani", "Martin", "García", "Benali", "Dubois", "Wilson", "El Idrissi", "Brown", "Moreau", "Alaoui",
                  "López", "Bernard", "Haddad", "Meyer", "Rossi", "Bennani", "Petit", "Saidi", "Leroy", "Jensen",
                  "Amrani", "Cohen"]
    countries = [("Maroc", "MA"), ("France", "FR"), ("Espagne", "ES"), ("Royaume-Uni", "UK"), ("Allemagne", "DE"),
                 ("Belgique", "BE"), ("États-Unis", "US"), ("Italie", "IT")]
    customers = []
    for i, (fn, ln) in enumerate(zip(first_names, last_names)):
        country = countries[i % len(countries)][0]
        c = Customer(
            first_name=fn, last_name=ln,
            email_enc=encrypt_text(f"{fn.lower()}.{ln.split()[0].lower().replace(' ', '')}@example.test"),
            email_hash=hash_identifier(f"{fn.lower()}.{i}@example.test"),
            phone_enc=encrypt_text(f"+2126001{i:05d}"),
            phone_hash=hash_identifier(f"+2126001{i:05d}"),
            country=country, locale=["fr", "en", "es", "ar"][i % 4],
            stay_start=today - timedelta(days=20 - (i % 8)),
            stay_end=today + timedelta(days=5 + (i % 12)),
            adults=1 + (i % 3), children=[8, 11] if i % 5 == 0 else [],
            interests=random.sample(list(VIBES.keys()), 3),
            budget_min=500, budget_max=8000,
            source=["Instagram", "Hôtel partenaire", "Bouche à oreille", "Google", "Office de tourisme"][i % 5],
            marketing_opt_in=(i % 3 == 0),
            notes="Profil fictif de démonstration",
            is_demo=True,
        )
        session.add(c)
        customers.append(c)
    session.flush()
    for c in customers:
        session.add(Consent(
            customer_id=c.id, purpose="réservation", granted=True,
            granted_at=now - timedelta(days=12), policy_version="2026-01", source="formulaire démo",
        ))
        if c.marketing_opt_in:
            session.add(Consent(
                customer_id=c.id, purpose="marketing", granted=True,
                granted_at=now - timedelta(days=12), policy_version="2026-01", source="formulaire démo",
            ))

    # --------------------------------------------------------------- activités
    activities = [
        ("karting", "Karting Agadir", T("Karting Agadir", "Agadir Karting", "كارتينغ أكادير", "Karting Agadir"),
         "Adrénaline sur piste", "Une piste de karting pour petits et grands.",
         "Sensations fortes, briefing sécurité et sessions encadrées. Durée, niveau et équipement à confirmer par le gestionnaire.",
         ["aventure", "famille", "jeux"], 30.3998, -9.5440, 8.5, 350, "personne", 24, 0,
         "Route de l'aéroport", "Agadir"),
        ("golf", "Golf Les Dunes", T("Golf Les Dunes", "Les Dunes Golf", "غولف الكثبان", "Golf Les Dunes"),
         "Un parcours face à l'océan", "Golf et panorama dans un cadre verdoyant.",
         "Parcours de démonstration, location de matériel et cours possibles. Les horaires et tarifs réels sont à renseigner.",
         ["detente", "aventure"], 30.3850, -9.5700, 12.0, 650, "personne", 30, 1,
         "Founty", "Agadir"),
        ("agadir-oufella", "Agadir Oufella", T("Agadir Oufella", "Agadir Oufella", "أكادير أوفلا", "Agadir Oufella"),
         "La kasbah et la baie", "Panorama historique au-dessus d'Agadir.",
         "Montée vers la kasbah et point de vue sur la baie. Téléphérique, accès et horaires exacts à confirmer.",
         ["culture", "detente", "famille"], 30.4383, -9.6108, 2.1, 180, "personne", 40, 2,
         "Oufella", "Agadir"),
        ("medina", "Médina d'Agadir", T("Médina d'Agadir", "Agadir Medina", "مدينة أكادير", "Medina de Agadir"),
         "Artisanat et ruelles", "Balade dans les ruelles et ateliers de la médina.",
         "Parcours culturel dans une médina reconstituée. Les boutiques et animations varient selon la saison.",
         ["culture", "famille", "gastronomie"], 30.4015, -9.5580, 5.0, 50, "personne", 50, 2,
         "Médina", "Agadir"),
        ("dauphins", "Sortie dauphins", T("Sortie dauphins", "Dolphin watching", "رحلة الدلافين", "Avistamiento de delfines"),
         "Rencontre au large", "Sortie en mer à la rencontre des dauphins.",
         "Sortie en mer dépendante de la météo et des observations. Aucun sighting garanti. Conditions de sécurité à valider par l'opérateur.",
         ["mer", "nature", "famille"], 30.4185, -9.6010, 1.5, 350, "personne", 18, 1,
         "Port d'Agadir", "Agadir"),
        ("live-it-maghribi", "Live it Maghribi", T("Live it Maghribi", "Live it Maghribi", "عش المغرب", "Live it Maghribi"),
         "Ateliers d'artisanat", "Poterie, broderie, crochet et zellige.",
         "Ateliers de découverte des savoir-faire marocains. Contenu, durée et matériaux à confirmer avec l'atelier.",
         ["culture", "famille", "detente"], 30.4140, -9.5730, 3.4, 280, "personne", 12, 6,
         "Centre-ville", "Agadir"),
        ("quad", "Quad dans les dunes", T("Quad dans les dunes", "Dune quad ride", "كواد في الكثبان", "Quad en las dunas"),
         "Poussière et grands espaces", "Balade encadrée dans les dunes.",
         "Sortie tout-terrain avec briefing et équipement. Niveau et parcours adaptés aux débutants, à valider par l'opérateur.",
         ["aventure", "nature", "jeux"], 30.3530, -9.5460, 15.0, 450, "personne", 16, 0,
         "Tifnit", "Agadir"),
        ("cheval-dromadaire", "Cheval & dromadaire", T("Balade cheval & dromadaire", "Horse & camel ride", "جولة بالحصان والجمل", "Paseo a caballo y camello"),
         "Le long de la plage", "Deux façons de découvrir la côte.",
         "Balade accompagnée sur la plage. Poids, âge et conditions de sécurité à confirmer.",
         ["famille", "nature", "detente"], 30.4210, -9.6250, 4.2, 300, "personne", 14, 5,
         "Baie d'Agadir", "Agadir"),
        ("bowling", "Bowling Agadir", T("Bowling Agadir", "Agadir Bowling", "بولينغ أكادير", "Bolera Agadir"),
         "Soirée en famille", "Quelques pistes pour prolonger la journée.",
         "Bowling et espace détente. Horaires réels et formules groupes à renseigner.",
         ["jeux", "famille", "detente"], 30.4166, -9.5900, 2.0, 120, "personne", 30, 3,
         "Centre-ville", "Agadir"),
        ("timlaline", "Sand surfing Timlaline", T("Sand surfing Timlaline", "Timlaline sandboarding", "ساند سيرفينغ تيملالين", "Sandboard en Timlaline"),
         "Glisser sur les dunes", "Session de sandboard dans un décor désertique.",
         "Session encadrée, matériel fourni selon l'opérateur. Retour et niveau d'effort à confirmer.",
         ["aventure", "famille", "nature"], 30.3530, -9.5650, 20.0, 400, "personne", 14, 0,
         "Timlaline", "Agadir"),
        ("crocoparc", "Crocoparc", T("Crocoparc", "Crocoparc", "كروكوبارك", "Crocoparc"),
         "Nature et animaux", "Parc botanique et crocodiles.",
         "Visite libre du parc. Horaires d'ouverture et nourrissages à vérifier avant la visite.",
         ["nature", "famille", "detente"], 30.3450, -9.5590, 25.0, 160, "personne", 100, 5,
         "Drarga", "Agadir"),
        ("villa-taelaimoun", "Domaine Villa Taelaimoun", T("Domaine Villa Taelaimoun", "Villa Taelaimoun estate", "ضيعة فيلا تاليعمون", "Finca Villa Taelaimoun"),
         "Une parenthèse arganière", "Domaine et nature aux portes d'Agadir.",
         "Visite du domaine et activités nature. Contenu exact, accès et tarifs à confirmer.",
         ["nature", "detente", "gastronomie"], 30.4600, -9.4900, 18.0, 250, "personne", 20, 5,
         "Drarga", "Agadir"),
        ("pique-nique", "Pique-nique au bord de l'eau", T("Pique-nique au bord de l'eau", "Seaside picnic", "نزهة على البحر", "Pícnic junto al mar"),
         "Une pause simple", "Panier et couverture face à l'océan.",
         "Formule pique-nique de démonstration. Contenu du panier et point de rendez-vous à renseigner.",
         ["detente", "famille", "mer"], 30.4240, -9.6280, 3.0, 100, "personne", 12, 5,
         "Baie d'Agadir", "Agadir"),
        ("sortie-plage", "Sortie plage & jeux", T("Sortie plage & jeux", "Beach day & games", "يوم على الشاطئ", "Día de playa y juegos"),
         "Sable, jeux et océan", "Une demi-journée les pieds dans le sable.",
         "Animation de plage avec jeux. Activités soumises à la météo et au drapeau de baignade.",
         ["famille", "mer", "jeux"], 30.4240, -9.6300, 2.5, 80, "personne", 30, 5,
         "Baie d'Agadir", "Agadir"),
        ("art-studio", "Art Studio peinture", T("Art Studio peinture", "Art Studio painting", "استوديو الرسم", "Estudio de pintura"),
         "Créer face à la lumière", "Atelier de peinture guidé.",
         "Atelier créatif pour débutants. Matériel et durée à confirmer avec l'atelier.",
         ["culture", "detente", "famille"], 30.4180, -9.5790, 3.0, 220, "personne", 10, 6,
         "Centre-ville", "Agadir"),
        ("musee-agadir", "Musée d'Agadir", T("Musée d'Agadir", "Agadir Museum", "متحف أكادير", "Museo de Agadir"),
         "Mémoire du Souss", "Collections et histoire régionale.",
         "Parcours muséal. Horaires, tarifs et disponibilité des langues à vérifier auprès du musée.",
         ["culture", "famille", "detente"], 30.4220, -9.5950, 2.0, 60, "personne", 40, 2,
         "Centre-ville", "Agadir"),
        ("aghroud", "Aghroud, village coloré", T("Aghroud, village coloré", "Aghroud, colourful village", "أغروض القرية الملونة", "Aghroud, pueblo colorido"),
         "Couleurs et lagune", "Échappée vers le village et la côte.",
         "Excursion d'une demi-journée. Le programme et les arrêts sont adaptés à la météo.",
         ["culture", "mer", "nature"], 30.5330, -9.7000, 35.0, 200, "personne", 18, 4,
         "Aghroud", "Aghroud"),
        ("anza-dinosaures", "Anza Les Dinosaures", T("Anza Les Dinosaures", "Anza Dinosaurs", "أنزا الديناصورات", "Anza Dinosaurios"),
         "Une halte étonnante", "Restaurant et univers de dinosaures à Anza.",
         "Halte familiale et restauration. Les horaires et le menu sont à confirmer auprès de l'établissement.",
         ["famille", "gastronomie", "jeux"], 30.4630, -9.6470, 12.0, 180, "personne", 40, 2,
         "Anza", "Agadir"),
        ("escape-zone", "Escape Zone", T("Escape Zone", "Escape Zone", "إسكيب زون", "Escape Zone"),
         "Une heure pour s'échapper", "Salle d'escape game en équipe.",
         "Session d'escape game. Scénarios, âge minimum et horaires à confirmer.",
         ["jeux", "famille", "aventure"], 30.4150, -9.5900, 3.0, 150, "personne", 6, 3,
         "Centre-ville", "Agadir"),
        ("sortie-bateau", "Sortie en bateau", T("Sortie en bateau", "Boat trip", "رحلة بالقارب", "Paseo en barco"),
         "Agadir vue du large", "Balade en mer et pause au large.",
         "Sortie dépendante de la météo et des conditions maritimes. Consignes de sécurité fournies par l'opérateur.",
         ["mer", "nature", "detente"], 30.4185, -9.6020, 1.8, 400, "personne", 24, 1,
         "Marina", "Agadir"),
        ("excursions-alentours", "Excursions alentours", T("Excursions Taghazout, Tamraght, Imsouane", "Taghazout, Tamraght & Imsouane tours", "رحلات تاغازوت وتمراكت وإمسوان", "Excursiones Taghazout, Tamraght e Imsouane"),
         "La côte autrement", "Une journée entre villages et spots de surf.",
         "Tournée d'une journée avec arrêts. Programme, repas et temps libres à personnaliser avec le gestionnaire.",
         ["aventure", "mer", "nature"], 30.5450, -9.7100, 40.0, 550, "personne", 16, 4,
         "Taghazout", "Taghazout"),
    ]
    activity_items = []
    for idx, spec in enumerate(activities):
        slug, fr_name, name, tagline, short, long, vibes, lat, lng, dist, price, unit, cap, prov_i, district, zone = spec
        item = _catalog("activity", slug, name, tagline, short, long, vibes, lat, lng, dist,
                        price, unit, cap, providers[prov_i].id, district, zone, "request")
        session.add(item)
        session.flush()
        session.add(ActivityDetail(
            catalog_id=item.id, duration_minutes=[60, 90, 120, 180, 240, 480][idx % 6],
            audience=["famille", "adultes"] if idx % 2 else ["famille", "enfants", "adultes"],
            effort_level=["doux", "modéré", "sportif"][idx % 3],
            what_to_bring=T("Chaussures fermées, eau, protection solaire"),
            weather_notes=T("Sous réserve de météo favorable. Consignes confirmées par le prestataire."),
            best_season=T("Toute l'année, à confirmer selon la saison."),
            safety_notes=T("Briefing et consignes de sécurité fournis par l'opérateur avant le départ."),
            includes=["encadrement", "équipement selon formule"],
        ))
        var = Variant(
            catalog_id=item.id, code="standard", name=T("Formule standard"),
            capacity_min=1, capacity_max=max(2, cap // 2), duration_minutes=[60, 90, 120, 180, 240, 480][idx % 6],
            price=price, price_status="demo", details={"demo": True}, sort_order=0,
        )
        session.add(var)
        session.flush()
        activity_items.append((item, var))
        _media(session, item, ["Vue d'ensemble (DÉMO)", "Ambiance (DÉMO)", "Détail de l'expérience (DÉMO)"])

    # ------------------------------------------------------------- restaurants
    restaurant_specs = [
        ("Le Riad des Saveurs", "Centre-ville", ["marocaine"], "€€", ["terrasse", "halal", "famille"], ["Tajine", "Pastilla"], 120),
        ("La Terrasse du Port", "Port", ["fruits de mer", "internationale"], "€€€", ["vue mer", "terrasse", "halal"], ["Poisson grillé", "Crevettes"], 180),
        ("Café Argan", "Founty", ["café", "internationale"], "€", ["terrasse", "végétarien", "famille"], ["Petit-déjeuner", "Smoothies"], 90),
        ("Dar Agadir", "Médina", ["marocaine"], "€€", ["terrasse", "halal", "enfants"], ["Couscous", "Tajine"], 140),
        ("L'Olivier Vert", "Centre-ville", ["végétarienne", "internationale"], "€€", ["végétarien", "terrasse"], ["Buddha bowl", "Salades"], 110),
        ("Le Bistrot de l'Océan", "Corniche", ["internationale", "fruits de mer"], "€€€", ["vue mer", "terrasse"], ["Risotto", "Tartare"], 220),
        ("Bab Marrakech", "Talborjt", ["marocaine"], "€", ["halal", "famille"], ["Harira", "Brochettes"], 70),
        ("Sunset Taghazout", "Taghazout", ["café", "internationale"], "€€", ["vue mer", "terrasse", "végétarien"], ["Brunch", "Poke bowl"], 160),
        ("Imsouane Blue", "Imsouane", ["fruits de mer", "marocaine"], "€€", ["vue mer", "terrasse"], ["Poisson du jour", "Salade"], 130),
        ("Tamraght Bio Café", "Tamraght", ["végétarienne", "café"], "€", ["végétarien", "terrasse"], ["Bowls", "Jus frais"], 80),
        ("Aghroud Sunset", "Aghroud", ["marocaine", "fruits de mer"], "€€", ["vue mer", "terrasse"], ["Grillades", "Salade"], 150),
        ("La Corniche", "Corniche", ["internationale"], "€€", ["vue mer", "famille"], ["Pâtes", "Burger"], 140),
        ("Le Jardin d'Épices", "Centre-ville", ["marocaine", "végétarienne"], "€€", ["terrasse", "végétarien", "halal"], ["Tajine végétarien"], 100),
        ("Anza Dino Grill", "Anza", ["marocaine", "internationale"], "€€", ["famille", "enfants", "terrasse"], ["Grillades", "Pizza"], 120),
        ("Le Petit Souk", "Médina", ["marocaine", "café"], "€", ["terrasse", "famille"], ["Msemen", "Thé"], 50),
        ("Ocean 30", "Founty", ["fruits de mer"], "€€€", ["vue mer", "terrasse", "halal"], ["Plateau de mer", "Calamars"], 230),
        ("Riad Yasmine", "Centre-ville", ["marocaine"], "€€€", ["terrasse", "halal"], ["Pastilla", "Agneau"], 200),
        ("Le Comptoir Souss", "Talborjt", ["marocaine", "internationale"], "€€", ["famille", "halal"], ["Tajine", "Couscous"], 110),
        ("Surf & Coffee", "Taghazout", ["café"], "€", ["terrasse", "végétarien"], ["Café", "Cookies"], 40),
        ("La Paella Bleue", "Marina", ["espagnole", "fruits de mer"], "€€€", ["vue mer", "terrasse"], ["Paella", "Tapas"], 210),
        ("Nomad Kitchen", "Tamraght", ["internationale", "végétarienne"], "€€", ["végétarien", "terrasse"], ["Curry", "Salade"], 90),
        ("Aghroud Family Table", "Aghroud", ["marocaine"], "€", ["famille", "enfants"], ["Tajine", "Pizza"], 75),
        ("Imsouane Sunset Café", "Imsouane", ["café", "internationale"], "€", ["vue mer", "terrasse"], ["Petit-déjeuner", "Jus"], 55),
        ("L'Arganier", "Founty", ["marocaine", "végétarienne"], "€€", ["végétarien", "terrasse"], ["Couscous", "Légumes"], 95),
        ("Marina Grill", "Marina", ["fruits de mer", "marocaine"], "€€€", ["vue mer", "halal", "terrasse"], ["Gambas", "Dorade"], 240),
    ]
    restaurant_items = []
    for i, (name, district, cuisines, band, options, dishes, cap) in enumerate(restaurant_specs):
        zone = district if district in {"Taghazout", "Tamraght", "Imsouane", "Aghroud", "Anza"} else "Agadir"
        item = _catalog(
            "restaurant", f"restaurant-{i+1:02d}", T(name, name, name, name),
            f"{', '.join(cuisines).title()} — {district}", f"Une table de démonstration à {district}.",
            "Fiche fictive de démonstration. Les horaires, menus, capacités et prix réels doivent être saisis par le gérant.",
            ["gastronomie", "detente"] + (["famille"] if "famille" in options else []),
            30.42 + random.uniform(-0.06, 0.08), -9.59 + random.uniform(-0.09, 0.04),
            random.choice([1.2, 2.5, 4.0, 6.0, 12.0, 18.0, 35.0]),
            random.choice([80, 120, 180, 250]), "personne", cap, providers[2].id,
            district, zone, "request",
        )
        session.add(item)
        session.flush()
        session.add(RestaurantDetail(
            catalog_id=item.id, cuisines=cuisines, price_band=band,
            ambiance=T("Chaleureuse et conviviale"),
            opening_hours={"demo": "horaires fictifs à confirmer", "lunch": "12:00–15:00", "dinner": "19:00–23:00"},
            hours_status="demo", signature_dishes=dishes, options=options, max_covers=cap,
        ))
        var = Variant(
            catalog_id=item.id, code="table", name=T("Réservation de table"),
            capacity_min=1, capacity_max=8, price=None, price_status="missing",
            details={"demo": True}, sort_order=0,
        )
        session.add(var)
        session.flush()
        restaurant_items.append((item, var))
        _media(session, item, ["Salle (DÉMO)", "Assiette signature (DÉMO)", "Terrasse (DÉMO)"])

    # ------------------------------------------------------------ hébergements
    acc_specs = [
        ("Riad Azul DÉMO", "Agadir", "riad", "€€", ["petit-déjeuner", "terrasse", "wifi"]),
        ("Atlas Bay Hotel DÉMO", "Agadir", "hôtel", "€€€", ["piscine", "spa", "wifi", "petit-déjeuner"]),
        ("Surf House Taghazout DÉMO", "Taghazout", "maison d'hôtes", "€", ["wifi", "cours de surf", "terrasse"]),
        ("Tamraght Ocean Lodge DÉMO", "Tamraght", "auberge", "€", ["wifi", "cuisine", "terrasse"]),
        ("Imsouane Blue House DÉMO", "Imsouane", "maison d'hôtes", "€€", ["vue mer", "wifi", "petit-déjeuner"]),
        ("Aghroud Beach Camp DÉMO", "Aghroud", "camp", "€", ["terrasse", "vue mer", "wifi"]),
        ("Founty Sunset Hôtel DÉMO", "Agadir", "hôtel", "€€€", ["piscine", "vue mer", "spa", "wifi"]),
        ("Médina Riad DÉMO", "Agadir", "riad", "€€", ["terrasse", "petit-déjeuner", "wifi"]),
        ("Taghazout Bay Lodge DÉMO", "Taghazout", "hôtel", "€€€", ["piscine", "vue mer", "spa", "wifi"]),
        ("Tamraght Surf Villa DÉMO", "Tamraght", "villa", "€€", ["piscine", "cours de surf", "wifi"]),
        ("Imsouane Surf Camp DÉMO", "Imsouane", "auberge", "€", ["cours de surf", "terrasse", "wifi"]),
        ("Aghroud Village Rooms DÉMO", "Aghroud", "maison d'hôtes", "€€", ["vue mer", "terrasse", "wifi"]),
        ("Agadir Central Hôtel DÉMO", "Agadir", "hôtel", "€€", ["wifi", "petit-déjeuner", "famille"]),
        ("Souss Garden Riad DÉMO", "Agadir", "riad", "€€", ["jardin", "terrasse", "wifi"]),
        ("Corniche Beach Hôtel DÉMO", "Agadir", "hôtel", "€€€", ["piscine", "vue mer", "wifi", "spa"]),
    ]
    accommodation_items = []
    for i, (name, zone, typ, band, amenities) in enumerate(acc_specs):
        item = _catalog(
            "accommodation", f"hebergement-{i+1:02d}", T(name, name, name, name),
            f"{typ.title()} — {zone}", f"Un hébergement de démonstration à {zone}.",
            "Fiche fictive. Disponibilité, tarifs et services réels à renseigner par le gestionnaire.",
            ["detente", "famille"] + (["mer"] if zone != "Agadir" else []),
            30.43 + random.uniform(-0.12, 0.12), -9.60 + random.uniform(-0.18, 0.08),
            random.choice([1.5, 3.0, 8.0, 20.0, 35.0]),
            random.choice([450, 650, 900, 1200, 1800]), "nuit", 30,
            providers[3].id if zone != "Agadir" else providers[7].id,
            zone, zone, "request",
        )
        session.add(item)
        session.flush()
        session.add(AccommodationDetail(
            catalog_id=item.id, accommodation_type=typ, price_band=band,
            amenities=amenities, checkin_time="15:00", checkout_time="11:00", rooms_count=12,
        ))
        variants = []
        for j, (code, label, cap, price) in enumerate([
            ("double", "Chambre double", 2, random.choice([550, 750, 950])),
            ("family", "Chambre familiale", 4, random.choice([850, 1100, 1450])),
        ]):
            var = Variant(
                catalog_id=item.id, code=code, name=T(label), capacity_min=1, capacity_max=cap,
                price=price, price_status="demo", details={"demo": True}, sort_order=j,
            )
            session.add(var)
            variants.append(var)
        session.flush()
        accommodation_items.append((item, variants))
        _media(session, item, ["Chambre (DÉMO)", "Espace commun (DÉMO)", "Vue (DÉMO)"])

    # ------------------------------------------------------------ spots/plages
    spot_specs = [
        ("Baie d'Agadir", "Agadir", 30.4240, -9.6300, 2.5, "baignade, promenade, sports nautiques"),
        ("Taghazout Beach", "Taghazout", 30.5450, -9.7100, 35.0, "surf, baignade, promenade"),
        ("Aghroud Beach", "Aghroud", 30.5330, -9.7000, 35.0, "baignade, pique-nique, balade"),
        ("Tamraght Beach", "Tamraght", 30.5050, -9.6800, 22.0, "surf, balade, coucher de soleil"),
        ("Imsouane Bay", "Imsouane", 30.8430, -9.8200, 80.0, "surf, baignade, pêche"),
        ("Tifnit Beach", "Tifnit", 30.2100, -9.6500, 40.0, "pêche, promenade, nature"),
        ("Anza Beach", "Anza", 30.4630, -9.6470, 12.0, "balade, pique-nique, observation"),
        ("Imourane Beach", "Tamraght", 30.4900, -9.6750, 18.0, "surf, plage, détente"),
    ]
    spot_items = []
    for name, zone, lat, lng, dist, acts in spot_specs:
        item = _catalog(
            "spot", f"spot-{len(spot_items)+1:02d}", T(name, name, name, name),
            f"Spot & plage — {zone}", f"Un spot de démonstration à {zone}.",
            "Fiche informative fictive. Les conditions de baignade et de sécurité doivent être vérifiées sur place.",
            ["mer", "nature", "detente"], lat, lng, dist, None, "—", 0, None,
            zone, zone, "info",
        )
        session.add(item)
        session.flush()
        session.add(SpotDetail(
            catalog_id=item.id, spot_type="plage",
            possible_activities=acts.split(", "),
            access=T("Accès routier de démonstration, à confirmer."),
            parking=T("Parking à confirmer sur place."),
            services=["surveillance à confirmer", "douches à confirmer", "location de matériel selon saison"],
            safety_advice=T("Respecter les drapeaux, les consignes locales et ne pas se baigner seul. Donnée informative, sans garantie de sécurité."),
            best_time=T("Tôt le matin ou en fin de journée ; à adapter à la marée et à la météo."),
            sea_exposure="atlantique",
        ))
        spot_items.append(item)
        _media(session, item, ["Vue de la plage (DÉMO)", "Ambiance (DÉMO)", "Accès (DÉMO)"])

    # --------------------------------------------------------------- transport
    transport_specs = [
        ("tour-groupe-taghazout", "Tournée Taghazout en groupe", "tour", "Agadir", "Taghazout", 45, 8, 350, "personne", ["fr", "en", "ar"]),
        ("tour-prive-imsouane", "Tournée privée Imsouane", "tour", "Agadir", "Imsouane", 90, 6, 1200, "véhicule", ["fr", "en", "es"]),
        ("taxi-demande", "Taxi à la demande", "taxi", "Agadir", "Agadir et alentours", 20, 4, 120, "course", ["fr", "ar"]),
        ("taxi-demi-journee", "Taxi — forfait demi-journée", "taxi", "Agadir", "Agadir et alentours", 240, 4, 450, "véhicule", ["fr", "ar", "en"]),
        ("taxi-journee", "Taxi — forfait journée", "taxi", "Agadir", "Agadir et alentours", 480, 4, 750, "véhicule", ["fr", "ar", "en"]),
        ("transfert-aeroport", "Transfert aéroport", "transfer", "Aéroport Agadir", "Hôtel ou riad", 35, 6, 300, "véhicule", ["fr", "en", "ar"]),
    ]
    transport_items = []
    for slug, name, mode, origin, dest, duration, cap, price, unit, langs in transport_specs:
        item = _catalog(
            "transport", slug, T(name, name, name, name), f"{origin} → {dest}",
            "Transport de démonstration, prix et horaires fictifs.",
            "Prestation fictive. Le gérant doit renseigner les horaires, le prix définitif, les bagages et les conditions d'annulation.",
            ["aventure", "detente"], 30.4278, -9.5981, 0, price, unit, cap, providers[4].id,
            "Agadir", "Agadir", "request",
        )
        session.add(item)
        session.flush()
        session.add(TransportDetail(
            catalog_id=item.id, mode=mode, origin=origin, destination=dest,
            duration_minutes=duration, departure_times=["09:00", "14:00"],
            frequency="Selon planning — horaires fictifs de démonstration",
            luggage="1 bagage par personne (à confirmer)",
            driver_languages=langs,
            cancellation_policy=T(CANCELLATION_POLICY),
        ))
        var = Variant(
            catalog_id=item.id, code="standard", name=T("Formule standard"),
            capacity_min=1, capacity_max=cap, duration_minutes=duration,
            price=price, price_status="demo", details={"demo": True},
        )
        session.add(var)
        session.flush()
        transport_items.append((item, var))
        _media(session, item, ["Véhicule (DÉMO)", "Itinéraire (DÉMO)", "Confort (DÉMO)"])

    # -------------------------------------------------------------- créneaux
    start_day = today - timedelta(days=45)
    for item, var in activity_items:
        for d in range(75):
            day = start_day + timedelta(days=d)
            for h in (9, 14):
                _slot(session, var, datetime.combine(day, time(h, 0)), var.duration_minutes or 120)
    for item, var in restaurant_items:
        for d in range(21):
            day = today + timedelta(days=d)
            for h in (12, 19):
                _slot(session, var, datetime.combine(day, time(h, 0)), 120, capacity=item.capacity or 40)
    for item, variants in accommodation_items:
        for var in variants:
            for d in range(30):
                day = today + timedelta(days=d)
                _slot(session, var, datetime.combine(day, time(15, 0)), 20 * 60, capacity=4)
    for item, var in transport_items:
        for d in range(21):
            day = today + timedelta(days=d)
            for h in (9, 14):
                session.add(TransportRun(
                    catalog_id=item.id, variant_id=var.id,
                    departure_at=datetime.combine(day, time(h, 0)),
                    return_at=datetime.combine(day, time(h, 0)) + timedelta(minutes=var.duration_minutes or 90),
                    capacity=var.capacity_max or 6, booked_count=0,
                    vehicle_id=vehicles[(item.id + h) % len(vehicles)].id,
                    driver_id=drivers[(item.id + h) % len(drivers)].id,
                    status="planned", route_plan={"demo": True, "stops": [item.district or "Agadir"]},
                    is_demo=True,
                ))
    session.flush()

    # ------------------------------------------------------------- réservations
    statuses = ["completed"] * 30 + ["confirmed"] * 5 + ["deposit_received"] * 3 + ["cancelled"] * 2
    review_ratings = [5, 5, 4, 5, 4, 5, 3, 4, 5, 5, 2, 5, 4, 5, 4, 5, 5, 4, 3, 5,
                      5, 4, 5, 4, 5, 5, 4, 5, 3, 5, 4, 5, 5, 4, 5, 2, 5, 4, 5, 5,
                      4, 5, 5, 4, 3, 5, 5, 4, 5, 4, 5, 5, 4, 5, 5, 4, 5, 2, 5, 5]
    review_comments = [
        "Très belle experience, guide attentionne et paysages magnifiques.",
        "Nous avons adore la sortie en famille. Tout etait bien explique.",
        "Super moment, a refaire. Le timing etait respecte.",
        "Belle decouverte, dommage que le vent se soit leve en fin de journee.",
        "Accueil chaleureux et equipe professionnelle.",
        "Un peu d'attente au depart, mais l'activite valait le detour.",
        "Les enfants ont adore. Nous recommandons.",
        "Prix correct et organisation claire. Merci Azul.",
        "Très bon souvenir, malgré une météo capricieuse.",
        "Excellente activite, guide passionne.",
        "Nous avons trouve le rythme un peu lent, mais le site est superbe.",
        "Service impeccable et paysages inoubliables.",
        "Bonne experience dans l'ensemble, quelques informations a ameliorer.",
        "Le coucher de soleil etait magnifique. Equipe au top.",
        "Reservation simple et confirmation rapide.",
        "Activite sympa mais un peu trop de monde ce jour-la.",
        "Parfait pour notre premier sejour a Agadir.",
        "Le transfert etait ponctuel et le chauffeur tres aimable.",
        "Une tres belle journee, avec une pause repas delicieuse.",
        "Nous reviendrons avec plaisir.",
    ]
    completed_items_for_reviews = []
    bookings = []
    for b_i, status in enumerate(statuses):
        customer = customers[b_i % len(customers)]
        is_past = status in {"completed", "cancelled"} and b_i < 34
        service_day = today - timedelta(days=5 + b_i) if status == "completed" else today + timedelta(days=2 + (b_i % 14))
        if status == "cancelled":
            service_day = today - timedelta(days=12)
        created = datetime.combine(service_day - timedelta(days=7), time(10, 30))
        items_for_booking = []
        if status in {"completed", "confirmed", "deposit_received"}:
            act = activity_items[b_i % len(activity_items)]
            rest = restaurant_items[(b_i * 3) % len(restaurant_items)]
            items_for_booking = [act, rest]
        elif status == "cancelled":
            items_for_booking = [transport_items[b_i % len(transport_items)]]
        total = 0.0
        booking = Booking(
            reference=f"DEMO-2026-{b_i+1:04d}",
            customer_id=customer.id, status=status,
            total_amount=None, deposit_amount=None, currency="MAD",
            source=["site", "hotel", "WhatsApp", "conseil"][b_i % 4],
            special_requests="Demande fictive de démonstration." if b_i % 4 == 0 else None,
            consent_version="2026-01",
            cancellation_policy=CANCELLATION_POLICY,
            is_demo=True, created_at=created,
        )
        if status == "completed":
            booking.confirmed_at = created + timedelta(hours=4)
            booking.completed_at = datetime.combine(service_day, time(18, 0))
        elif status == "confirmed":
            booking.confirmed_at = now - timedelta(days=1)
        elif status == "deposit_received":
            booking.confirmed_at = now - timedelta(days=2)
        elif status == "cancelled":
            booking.cancelled_at = created + timedelta(days=1)
        session.add(booking)
        session.flush()

        for idx, (item, var) in enumerate(items_for_booking):
            price = var.price or 0
            qty = customer.adults + len(customer.children or [])
            line_total = price * max(1, qty if item.kind != "restaurant" else customer.adults)
            total += line_total
            bi = BookingItem(
                booking_id=booking.id, catalog_item_id=item.id, variant_id=var.id,
                item_type=item.kind, service_date=service_day,
                start_at=datetime.combine(service_day, time(9 if idx == 0 else 19, 0)),
                end_at=datetime.combine(service_day, time(11 if idx == 0 else 21, 0)),
                adults=customer.adults, children=len(customer.children or []),
                quantity=1, unit_price=price, line_total=line_total,
                price_status="demo", status=booking.status,
                details={"demo": True, "note": "Ligne fictive de démonstration"},
                is_demo=True,
            )
            session.add(bi)
            session.flush()
            if status == "completed":
                completed_items_for_reviews.append(bi)
        booking.total_amount = total
        booking.deposit_amount = round(total * 0.2, 2)
        if status in {"completed", "confirmed", "deposit_received"}:
            session.add(Payment(
                booking_id=booking.id, payment_type="deposit",
                amount=booking.deposit_amount,
                status="received" if status in {"completed", "deposit_received"} else "pending",
                method="manual", due_at=created + timedelta(days=2),
                received_at=created + timedelta(days=1) if status in {"completed", "deposit_received"} else None,
                reference=f"PAY-DEMO-{b_i+1:03d}",
                note="Paiement fictif de démonstration",
            ))
        if status in {"completed", "confirmed"}:
            ticket_ref = f"TKT-{booking.reference}"
            session.add(Ticket(
                booking_id=booking.id, reference=ticket_ref,
                qr_payload=sign_ticket_payload(booking.reference),
                qr_token_hash=hash_identifier(ticket_ref),
                status="issued",
            ))
        session.add(BookingStatusHistory(
            booking_id=booking.id, from_status=None, to_status=status,
            note="Statut fictif de démonstration", created_at=created,
        ))
        # Score de démonstration, calculé par la règle métier réelle plus bas.
        bookings.append(booking)

    # scoring déterministe
    from src.services.scoring import score_booking_request
    for b in bookings:
        hist = sum(1 for x in bookings if x.customer_id == b.customer_id and x.status == "completed")
        lead = max(0, (b.created_at.date() - today).days) if b.created_at else 3
        score, explanation = score_booking_request(b.total_amount or 0, lead, b.customer_id and (2 + b.id % 4) or 1, hist, 0)
        b.score = score
        b.score_explanation = explanation

    # ---------------------------------------------------------------- avis
    comment_languages = ["fr", "en", "fr", "es", "fr", "en"]
    for idx, bi in enumerate(completed_items_for_reviews[:60]):
        rating = review_ratings[idx % len(review_ratings)]
        comment = review_comments[idx % len(review_comments)]
        review = Review(
            booking_item_id=bi.id, customer_id=bi.booking.customer_id,
            catalog_item_id=bi.catalog_item_id, rating=rating, comment=comment,
            language=comment_languages[idx % len(comment_languages)],
            experience_date=bi.service_date, status="published", verified=True,
            is_demo=True, created_at=datetime.combine(bi.service_date or today, time(12, 0)) + timedelta(days=1, hours=idx % 8),
        )
        if idx % 5 != 0:
            review.manager_response = "Merci pour votre retour, il nous aide à améliorer l'expérience Azul."
            review.response_at = (review.created_at or now) + timedelta(hours=18)
            review.response_by = admin.id
        session.add(review)
        session.flush()
        session.add(ReviewInvitation(
            booking_item_id=bi.id, channel=["email", "whatsapp"][idx % 2],
            scheduled_at=(bi.service_date and datetime.combine(bi.service_date, time(18, 0))) or now,
            sent_at=(bi.service_date and datetime.combine(bi.service_date, time(19, 0))) or now,
            reminder_sent_at=(bi.service_date and datetime.combine(bi.service_date + timedelta(days=1), time(19, 0))) if idx % 4 == 0 else None,
            token=f"review-demo-{idx+1}", status="reviewed", is_demo=True,
        ))

    # cache des notes + snapshots
    all_catalog_items = (
        [x[0] for x in activity_items + restaurant_items + accommodation_items + transport_items]
        + list(spot_items)
    )
    for item in all_catalog_items:
        item_reviews = [r for r in session.scalars(select(Review).where(Review.catalog_item_id == item.id)).all() if r.status == "published"]
        if item_reviews:
            item.rating_avg = round(sum(r.rating for r in item_reviews) / len(item_reviews), 2)
            item.review_count = len(item_reviews)
            dist = {str(k): sum(1 for r in item_reviews if r.rating == k) for k in range(1, 6)}
            session.add(RatingSnapshot(
                catalog_item_id=item.id, month=(today - timedelta(days=15)).strftime("%Y-%m"),
                rating_avg=item.rating_avg, review_count=item.review_count, distribution=dist,
            ))

    # ------------------------------------------------ paniers / itinéraires / messages
    itinerary = Itinerary(
        customer_id=customers[0].id, title="3 jours entre océan et artisanat (DÉMO)",
        start_date=today + timedelta(days=7), duration_days=3, budget=3500,
        group_json={"adults": 2, "children": 0}, interests=["mer", "culture", "gastronomie"],
        locale="fr", status="draft", ai_model="moteur local de démonstration",
        prompt_version="demo-1", is_demo=True,
    )
    session.add(itinerary)
    session.flush()
    for day_i in range(3):
        day = ItineraryDay(
            itinerary_id=itinerary.id, day_number=day_i + 1,
            day_date=today + timedelta(days=7 + day_i),
            weather_snapshot={"demo": True, "summary": "Météo à confirmer"},
            backup_plan="Plan B météo : atelier culturel ou café couvert, à confirmer.",
        )
        session.add(day)
        session.flush()
        item, var = activity_items[(day_i * 4) % len(activity_items)]
        session.add(ItineraryItem(
            day_id=day.id, catalog_item_id=item.id, variant_id=var.id,
            start_time="09:30", end_time="12:00", estimated_price=var.price,
            price_status="demo", notes="Proposition de démonstration",
        ))
        rest, _ = restaurant_items[(day_i * 3) % len(restaurant_items)]
        session.add(ItineraryItem(
            day_id=day.id, catalog_item_id=rest.id, start_time="19:00",
            end_time="20:30", notes="Dîner proposé — réservation à confirmer",
        ))

    template_specs = [
        ("confirmation", "email", "Votre demande Azul AGADIR {reference}"),
        ("rappel", "whatsapp", "Rappel : votre expérience demain"),
        ("demande_avis", "email", "Votre avis compte pour Azul AGADIR"),
        ("relance_acompte", "email", "Votre acompte pour la réservation {reference}"),
        ("confirmation", "whatsapp", "Confirmation de votre demande"),
    ]
    for code, channel, subject in template_specs:
        session.add(MessageTemplate(
            code=code, channel=channel, locale="fr", subject=subject,
            body="Bonjour {prenom},\n\n{message}\n\nMerci,\nL'équipe Azul AGADIR",
            is_approved=(code != "relance_acompte"), approved_by=admin.id,
        ))
    for i, b in enumerate(bookings[:8]):
        session.add(OutboxMessage(
            booking_id=b.id, customer_id=b.customer_id, template_code="confirmation",
            channel="email", recipient_enc=encrypt_text("client@example.test"),
            subject=f"Confirmation de démonstration — {b.reference}",
            body="Message fictif de démonstration. Aucun envoi réel n'a été effectué. Validation humaine requise.",
            status="draft", is_demo=True,
        ))

    session.add_all([
        Anomaly(anomaly_type="coordonnees_manquantes", severity="warning", entity_type="customer", entity_id=customers[7].id,
                details={"demo": True, "missing": "email"}, status="open"),
        Anomaly(anomaly_type="creneau_surcharge", severity="warning", entity_type="activity", entity_id=activity_items[0][0].id,
                details={"demo": True, "remaining": 0}, status="open"),
        Anomaly(anomaly_type="doublon_potentiel", severity="info", entity_type="customer", entity_id=customers[9].id,
                details={"demo": True, "similar_to": customers[10].id}, status="open"),
        Anomaly(anomaly_type="acompte_non_paye", severity="high", entity_type="booking", entity_id=bookings[36].id,
                details={"demo": True, "age_hours": 26}, status="open"),
    ])

    for p in providers:
        session.add(ProviderCommission(
            provider_id=p.id, gross_amount=random.choice([1200, 2500, 4300]),
            rate=p.commission_rate,
            commission_amount=round(random.choice([1200, 2500, 4300]) * p.commission_rate / 100, 2),
            status="pending",
        ))

    session.add_all([
        Setting(key="company_name", value="AgadirGO / Azul AGADIR", updated_by=admin.id),
        Setting(key="default_locale", value="fr", updated_by=admin.id),
        Setting(key="cancellation_policy", value=CANCELLATION_POLICY, updated_by=admin.id),
        Setting(key="auto_confirm_demo", value=True, updated_by=admin.id),
        Setting(key="ai_model", value="claude-sonnet-4-6", updated_by=admin.id),
        Setting(key="review_window_hours", value=24, updated_by=admin.id),
    ])

    legal_fr = {
        "cgu": "Conditions générales d'utilisation — démonstration. Les conditions réelles doivent être validées par AgadirGO.",
        "privacy": (
            "Politique de confidentialité — démonstration. Azul AGADIR collecte uniquement les données nécessaires "
            "à la réservation. Consentement explicite, droit d'accès, de rectification et de suppression. "
            "Conformité loi marocaine 09-08 et recommandations CNDP. Aucune donnée personnelle n'est envoyée "
            "à un modèle de langage."
        ),
        "cookies": "Politique cookies — démonstration. Aucun traceur publicitaire n'est activé par défaut.",
    }
    for doc_type, content in legal_fr.items():
        session.add(LegalDocument(
            doc_type=doc_type, locale="fr", version="2026-01",
            title=doc_type.upper(), content=content,
        ))

    # conversation de démonstration (contenu local, sans PII)
    conv = AIConversation(customer_id=customers[0].id, locale="fr", title="Idées pour un séjour à Agadir")
    session.add(conv)
    session.flush()
    session.add(AIMessage(
        conversation_id=conv.id, role="assistant",
        content="Azul ! Je peux vous aider à composer un séjour à partir du catalogue Azul AGADIR. "
                "Les prix et horaires affichés en mode démo sont fictifs.",
        sources=["catalogue DÉMO"], model="moteur local", guardrail_status="ok",
    ))

    # favoris + audit
    session.add_all([
        Favorite(customer_id=customers[0].id, catalog_item_id=activity_items[0][0].id),
        Favorite(customer_id=customers[0].id, catalog_item_id=restaurant_items[0][0].id),
        AuditLog(actor_id=admin.id, action="seed_demo", entity_type="database", entity_id=1,
                 details={"demo": True, "note": "Jeu de démonstration initialisé"}),
    ])

    session.flush()
