"""
Modèles SQLAlchemy pour AZUL AGADIR
"""

from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, Date, JSON, 
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

# ==================== ACTIVITÉS ====================
class Activity(Base):
    __tablename__ = "activities"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    
    # Noms multilingues
    name_fr = Column(String(255), nullable=False)
    name_en = Column(String(255))
    name_ar = Column(String(255))
    name_es = Column(String(255))
    
    # Descriptions
    category = Column(String(50))  # Karting, Golf, Médina, etc.
    description_short_fr = Column(Text)
    description_long_fr = Column(Text)
    
    # Détails pratiques
    duration_minutes = Column(Integer)
    location = Column(String(255))
    distance_from_center_km = Column(Float)
    public_type = Column(String(50))  # famille, enfants, adultes, tous
    effort_level = Column(String(50))  # facile, moyen, difficile
    what_to_bring = Column(Text)
    weather_conditions = Column(String(255))
    best_season = Column(String(50))
    languages_spoken = Column(String(255))
    capacity = Column(Integer)
    
    # Médias
    cover_photo_url = Column(String(500))
    cover_photo_credit = Column(String(255))
    gallery_urls = Column(JSON)  # [{url, credit}, ...]
    videos_urls = Column(JSON)  # [url1, url2, ...]
    
    # Avis et prix
    avg_rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    price_mad = Column(Integer)  # En MAD, peut être NULL
    
    # Flags
    is_demo = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation
    reviews = relationship("Review", back_populates="activity", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_category', 'category'),
        Index('idx_is_demo', 'is_demo'),
    )

# ==================== RESTAURANTS ====================
class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    quarter = Column(String(100))
    cuisine_types = Column(JSON)  # ["marocaine", "fruits_de_mer", ...]
    price_range = Column(String(20))  # €, €€, €€€, €€€€
    ambiance = Column(String(100))
    opening_hours = Column(Text)  # À renseigner
    signature_dishes = Column(JSON)  # ["Tagine", "Couscous", ...]
    options = Column(JSON)  # {terrasse, sea_view, children, halal, vegetarian, ...}
    capacity = Column(Integer)
    
    # Médias
    cover_photo_url = Column(String(500))
    cover_photo_credit = Column(String(255))
    gallery_urls = Column(JSON)  # [{url, credit}, ...]
    
    # Avis
    avg_rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    
    # Contact
    phone = Column(String(20))
    email = Column(String(100))
    website = Column(String(255))
    
    # Flags
    is_demo = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation
    reviews = relationship("Review", back_populates="restaurant", cascade="all, delete-orphan")
    table_reservations = relationship("TableReservation", back_populates="restaurant", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_quarter', 'quarter'),
        Index('idx_is_demo', 'is_demo'),
    )

# ==================== HÉBERGEMENTS ====================
class Accommodation(Base):
    __tablename__ = "accommodations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    zone = Column(String(50))  # Agadir, Taghazout, Tamraght, etc.
    type = Column(String(50))  # Hôtel, Riad, Auberge, Maison d'hôtes
    price_range = Column(String(20))  # €, €€, €€€, €€€€
    description = Column(Text)
    services = Column(JSON)  # ["wifi", "pool", "restaurant", ...]
    rooms_count = Column(Integer)
    
    # Médias
    photo_url = Column(String(500))
    photo_credit = Column(String(255))
    gallery_urls = Column(JSON)  # [{url, credit}, ...]
    
    # Localisation
    gps_lat = Column(Float)
    gps_lon = Column(Float)
    
    # Avis
    avg_rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    
    # Contact
    phone = Column(String(20))
    email = Column(String(100))
    website = Column(String(255))
    
    # Flags
    is_demo = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    reviews = relationship("Review", back_populates="accommodation", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_zone', 'zone'),
        Index('idx_type', 'type'),
    )

# ==================== TRANSPORTS ====================
class Transport(Base):
    __tablename__ = "transports"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    type = Column(String(50))  # Taxi, Minibus, Tour, Transfer, etc.
    departure_location = Column(String(255))
    arrival_location = Column(String(255))
    duration_minutes = Column(Integer)
    capacity = Column(Integer)
    baggage_info = Column(Text)
    driver_languages = Column(String(255))
    price_mad = Column(Integer)  # Par personne ou par véhicule
    price_unit = Column(String(20))  # person, vehicle
    departure_times = Column(JSON)  # ["08:00", "14:00", ...]
    cancellation_policy = Column(Text)
    
    # Flags
    is_demo = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_type', 'type'),
    )

# ==================== SPOTS ET PLAGES ====================
class Spot(Base):
    __tablename__ = "spots"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    location = Column(String(255))
    description = Column(Text)
    ambiance = Column(String(100))
    activities_possible = Column(JSON)  # ["baignade", "surf", "pique-nique", ...]
    distance_from_agadir_km = Column(Float)
    access_info = Column(Text)
    parking_available = Column(Boolean)
    services = Column(JSON)  # ["toilettes", "bar", ...]
    safety_advice = Column(Text)
    best_time = Column(String(100))
    
    # Médias
    photo_url = Column(String(500))
    photo_credit = Column(String(255))
    gallery_urls = Column(JSON)
    
    # Localisation
    gps_lat = Column(Float)
    gps_lon = Column(Float)
    
    # Flags
    is_demo = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_location', 'location'),
    )

# ==================== UTILISATEURS / CLIENTS ====================
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))  # WhatsApp
    email = Column(String(100), unique=True)
    country = Column(String(100))
    language = Column(String(5), default="fr")  # fr, en, ar, es
    
    # Dates de séjour
    stay_dates_from = Column(Date)
    stay_dates_to = Column(Date)
    
    # Composition du groupe
    adults_count = Column(Integer)
    children_count = Column(Integer)
    children_ages = Column(JSON)  # [3, 7, 10]
    
    # Préférences
    accommodation_id = Column(String, ForeignKey("accommodations.id"))
    interests = Column(JSON)  # ["Aventure", "Famille", ...]
    budget_mad = Column(Float)
    source = Column(String(100))  # Google, Instagram, Hotel, Friend, ...
    special_requests = Column(Text)
    
    # Consentements
    consent_privacy = Column(Boolean, default=False)
    consent_marketing = Column(Boolean, default=False)
    
    # Flags
    is_demo = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    bookings = relationship("Booking", back_populates="user", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_email', 'email'),
        Index('idx_phone', 'phone'),
    )

# ==================== ADMINISTRATEURS ====================
class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20))  # admin, manager, provider, driver
    provider_id = Column(String)  # Lien prestataire si applicable
    phone = Column(String(20))
    first_name = Column(String(100))
    last_name = Column(String(100))
    
    # Flags
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_email', 'email'),
        Index('idx_role', 'role'),
    )

# ==================== RÉSERVATIONS ====================
class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Statut et type
    status = Column(String(20), default="pending")  # pending, confirmed, deposit_received, cancelled, completed
    booking_type = Column(String(50))  # activity, restaurant, transport, package
    
    # Articles du panier
    booking_items = Column(JSON)  # [{type, item_id, quantity, price, ...}]
    
    # Tarification
    total_price_mad = Column(Float)
    deposit_paid_mad = Column(Float, default=0.0)
    currency_code = Column(String(5), default="MAD")
    
    # Dates et heures
    booking_date = Column(DateTime, default=datetime.utcnow)
    activity_date = Column(Date)
    activity_time = Column(String(5))  # HH:MM
    
    # Participants
    participant_count = Column(Integer)
    
    # Demandes spéciales
    special_requests = Column(Text)
    
    # Validation et scores
    confirmation_code = Column(String(20), unique=True)  # QR code reference
    ai_score = Column(Integer)  # 0-100
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation
    user = relationship("User", back_populates="bookings")
    reviews = relationship("Review", back_populates="booking", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_status', 'status'),
        Index('idx_confirmation_code', 'confirmation_code'),
    )

# ==================== RÉSERVATIONS DE TABLE ====================
class TableReservation(Base):
    __tablename__ = "table_reservations"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    restaurant_id = Column(String, ForeignKey("restaurants.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Date et heure
    reservation_date = Column(Date, nullable=False)
    reservation_time = Column(String(5), nullable=False)  # HH:MM
    
    # Participants
    guest_count = Column(Integer, nullable=False)
    special_requests = Column(Text)
    
    # Statut
    status = Column(String(20), default="pending")  # pending, confirmed, cancelled, completed
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    restaurant = relationship("Restaurant", back_populates="table_reservations")
    user = relationship("User")
    
    __table_args__ = (
        Index('idx_restaurant_id', 'restaurant_id'),
        Index('idx_user_id', 'user_id'),
        Index('idx_date', 'reservation_date'),
    )

# ==================== AVIS VÉRIFIÉS ====================
class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    booking_id = Column(String, ForeignKey("bookings.id"), unique=True)  # Lien unique avec réservation complétée
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Objet de l'avis
    item_type = Column(String(50))  # activity, restaurant, accommodation, transport
    activity_id = Column(String, ForeignKey("activities.id"))
    restaurant_id = Column(String, ForeignKey("restaurants.id"))
    accommodation_id = Column(String, ForeignKey("accommodations.id"))
    
    # Contenu
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text)
    photo_urls = Column(JSON)  # [url1, url2, ...]
    
    # Vérification
    verified_badge = Column(Boolean, default=True)
    experience_date = Column(Date)
    submission_date = Column(DateTime, default=datetime.utcnow)
    
    # Réponse du gérant
    manager_response = Column(Text)
    manager_response_date = Column(DateTime)
    
    # Modération
    is_moderated = Column(Boolean, default=False)
    moderation_reason = Column(String(255))
    
    # Flags
    is_demo = Column(Boolean, default=True)
    is_helpful = Column(Integer, default=0)  # Nombre de votes "utile"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    booking = relationship("Booking", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
    activity = relationship("Activity", back_populates="reviews")
    restaurant = relationship("Restaurant", back_populates="reviews")
    accommodation = relationship("Accommodation", back_populates="reviews")
    
    __table_args__ = (
        Index('idx_item_type', 'item_type'),
        Index('idx_rating', 'rating'),
    )

# ==================== PRESTATAIRES ====================
class Provider(Base):
    __tablename__ = "providers"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    type = Column(String(50))  # Activity, Restaurant, Accommodation, Transport
    contact_name = Column(String(255))
    phone = Column(String(20))
    email = Column(String(100))
    commission_rate = Column(Float)  # %
    is_verified = Column(Boolean, default=False)
    notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_type', 'type'),
    )

# ==================== MESSAGES GÉNÉRÉS ====================
class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    booking_id = Column(String, ForeignKey("bookings.id"))
    
    # Type et destinataire
    type = Column(String(50))  # confirmation, reminder, review_request, deposit_reminder
    recipient_phone = Column(String(20))
    recipient_email = Column(String(100))
    
    # Contenu
    template_name = Column(String(100))
    content = Column(Text)
    
    # Statut
    is_validated = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_booking_id', 'booking_id'),
        Index('idx_type', 'type'),
    )

# ==================== LOGS D'ACCÈS ====================
class AccessLog(Base):
    __tablename__ = "access_logs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String)
    action = Column(String(100))
    resource = Column(String(255))
    ip_address = Column(String(50))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_action', 'action'),
    )
