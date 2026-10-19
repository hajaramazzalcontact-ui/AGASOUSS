"""Schéma relationnel d'Azul AGADIR.

Le catalogue repose sur un socle commun (`catalog_items`) et des tables de
détail. Les médias, disponibilités, avis et réservations pointent ainsi vers
un identifiant unique, ce qui simplifie la carte, la recherche et le panier.
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .base import Base, utcnow


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email_hash = Column(String(64), unique=True, nullable=False, index=True)
    email_enc = Column(Text, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(160), nullable=False)
    role = Column(String(30), nullable=False, default="manager")  # admin, manager, provider, driver
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    locale = Column(String(5), default="fr")
    is_active = Column(Boolean, default=True)
    failed_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)


class Provider(Base):
    __tablename__ = "providers"
    id = Column(Integer, primary_key=True)
    name = Column(String(180), nullable=False)
    kind = Column(String(40), default="activité")
    contact_name = Column(String(160))
    phone_enc = Column(Text)
    email_enc = Column(Text)
    commission_rate = Column(Float, default=15.0)
    contract_ref = Column(String(80))
    is_verified = Column(Boolean, default=False)
    notes = Column(Text)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    items = relationship("CatalogItem", back_populates="provider")
    commissions = relationship("ProviderCommission", back_populates="provider")


class Driver(Base):
    __tablename__ = "drivers"
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("providers.id"))
    full_name = Column(String(160), nullable=False)
    phone_enc = Column(Text)
    languages = Column(JSON, default=list)
    license_ref_enc = Column(Text)
    rating_avg = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_demo = Column(Boolean, default=False)


class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("providers.id"))
    label = Column(String(120), nullable=False)
    plate = Column(String(30))
    capacity = Column(Integer, default=6)
    luggage = Column(Integer, default=4)
    vehicle_type = Column(String(40), default="van")
    is_active = Column(Boolean, default=True)
    is_demo = Column(Boolean, default=False)


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email_enc = Column(Text)
    email_hash = Column(String(64), index=True)
    phone_enc = Column(Text)
    phone_hash = Column(String(64), index=True)
    country = Column(String(80))
    locale = Column(String(5), default="fr")
    stay_start = Column(Date)
    stay_end = Column(Date)
    adults = Column(Integer, default=1)
    children = Column(JSON, default=list)
    accommodation_id = Column(Integer, ForeignKey("catalog_items.id"))
    interests = Column(JSON, default=list)
    budget_min = Column(Float)
    budget_max = Column(Float)
    source = Column(String(80))
    special_requests_enc = Column(Text)
    marketing_opt_in = Column(Boolean, default=False)
    notes = Column(Text)
    anonymized_at = Column(DateTime)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    bookings = relationship("Booking", back_populates="customer")
    consents = relationship("Consent", back_populates="customer")


class Consent(Base):
    __tablename__ = "customer_consents"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    purpose = Column(String(80), nullable=False)
    granted = Column(Boolean, default=False)
    policy_version = Column(String(30), default="2026-01")
    source = Column(String(80), default="formulaire web")
    granted_at = Column(DateTime)
    revoked_at = Column(DateTime)

    customer = relationship("Customer", back_populates="consents")


class LegalDocument(Base):
    __tablename__ = "legal_documents"
    id = Column(Integer, primary_key=True)
    doc_type = Column(String(30), nullable=False)  # cgu, privacy, cookies
    locale = Column(String(5), default="fr")
    version = Column(String(30), nullable=False)
    title = Column(String(180), nullable=False)
    content = Column(Text, nullable=False)
    published_at = Column(DateTime, default=utcnow)


class CatalogItem(Base):
    __tablename__ = "catalog_items"
    id = Column(Integer, primary_key=True)
    kind = Column(String(20), nullable=False, index=True)  # activity, restaurant, accommodation, spot, transport
    slug = Column(String(140), unique=True, nullable=False)
    provider_id = Column(Integer, ForeignKey("providers.id"))
    status = Column(String(20), default="published", index=True)
    name = Column(JSON, nullable=False)
    tagline = Column(JSON, default=dict)
    short_description = Column(JSON, default=dict)
    long_description = Column(JSON, default=dict)
    vibes = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    address = Column(String(240))
    district = Column(String(120))
    zone = Column(String(120))
    lat = Column(Float)
    lng = Column(Float)
    distance_center_km = Column(Float)
    languages = Column(JSON, default=list)
    capacity = Column(Integer)
    price_from = Column(Float)
    price_unit = Column(String(30), default="personne")
    price_status = Column(String(20), default="missing")  # missing, demo, confirmed
    price_source = Column(String(160))
    price_updated_at = Column(DateTime)
    booking_mode = Column(String(20), default="request")  # instant, request, info
    rating_avg = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)
    is_demo = Column(Boolean, default=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    provider = relationship("Provider", back_populates="items")
    variants = relationship("Variant", back_populates="catalog", cascade="all, delete-orphan")
    media = relationship("CatalogMedia", back_populates="catalog", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="catalog")


class ActivityDetail(Base):
    __tablename__ = "activities"
    catalog_id = Column(Integer, ForeignKey("catalog_items.id"), primary_key=True)
    duration_minutes = Column(Integer)
    audience = Column(JSON, default=list)
    effort_level = Column(String(30))
    what_to_bring = Column(JSON, default=list)
    weather_notes = Column(JSON, default=dict)
    best_season = Column(JSON, default=list)
    safety_notes = Column(JSON, default=dict)
    includes = Column(JSON, default=list)


class RestaurantDetail(Base):
    __tablename__ = "restaurants"
    catalog_id = Column(Integer, ForeignKey("catalog_items.id"), primary_key=True)
    cuisines = Column(JSON, default=list)
    price_band = Column(String(20))
    ambiance = Column(JSON, default=list)
    opening_hours = Column(JSON, default=dict)
    hours_status = Column(String(20), default="missing")  # missing, demo, confirmed
    signature_dishes = Column(JSON, default=list)
    options = Column(JSON, default=list)
    max_covers = Column(Integer)


class AccommodationDetail(Base):
    __tablename__ = "accommodations"
    catalog_id = Column(Integer, ForeignKey("catalog_items.id"), primary_key=True)
    accommodation_type = Column(String(40))
    price_band = Column(String(20))
    amenities = Column(JSON, default=list)
    checkin_time = Column(String(10))
    checkout_time = Column(String(10))
    rooms_count = Column(Integer)


class SpotDetail(Base):
    __tablename__ = "spots"
    catalog_id = Column(Integer, ForeignKey("catalog_items.id"), primary_key=True)
    spot_type = Column(String(40), default="plage")
    possible_activities = Column(JSON, default=list)
    access = Column(JSON, default=dict)
    parking = Column(JSON, default=dict)
    services = Column(JSON, default=list)
    safety_advice = Column(JSON, default=dict)
    best_time = Column(JSON, default=dict)
    sea_exposure = Column(String(40))


class TransportDetail(Base):
    __tablename__ = "transports"
    catalog_id = Column(Integer, ForeignKey("catalog_items.id"), primary_key=True)
    mode = Column(String(40))  # tour, taxi, transfer, shuttle
    origin = Column(String(160))
    destination = Column(String(160))
    duration_minutes = Column(Integer)
    departure_times = Column(JSON, default=list)
    frequency = Column(String(120))
    luggage = Column(String(120))
    driver_languages = Column(JSON, default=list)
    cancellation_policy = Column(JSON, default=dict)


class Variant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (UniqueConstraint("catalog_id", "code", name="uq_variant_code"),)
    id = Column(Integer, primary_key=True)
    catalog_id = Column(Integer, ForeignKey("catalog_items.id"), nullable=False)
    code = Column(String(60), nullable=False)
    name = Column(JSON, default=dict)
    capacity_min = Column(Integer, default=1)
    capacity_max = Column(Integer, default=10)
    duration_minutes = Column(Integer)
    price = Column(Float)
    price_status = Column(String(20), default="missing")
    details = Column(JSON, default=dict)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    catalog = relationship("CatalogItem", back_populates="variants")
    slots = relationship("AvailabilitySlot", back_populates="variant", cascade="all, delete-orphan")


class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"
    __table_args__ = (UniqueConstraint("variant_id", "start_at", name="uq_slot_variant_start"),)
    id = Column(Integer, primary_key=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=False)
    start_at = Column(DateTime, nullable=False, index=True)
    end_at = Column(DateTime, nullable=False)
    capacity = Column(Integer, default=10)
    booked_count = Column(Integer, default=0)
    status = Column(String(20), default="open")  # open, closed, full
    price_override = Column(Float)
    languages = Column(JSON, default=list)
    source = Column(String(40), default="manager")
    notes = Column(Text)
    is_demo = Column(Boolean, default=False)

    variant = relationship("Variant", back_populates="slots")

    @property
    def remaining(self) -> int:
        return max(0, (self.capacity or 0) - (self.booked_count or 0))


class TransportRun(Base):
    __tablename__ = "transport_runs"
    id = Column(Integer, primary_key=True)
    catalog_id = Column(Integer, ForeignKey("catalog_items.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id"))
    departure_at = Column(DateTime, nullable=False, index=True)
    return_at = Column(DateTime)
    capacity = Column(Integer, default=8)
    booked_count = Column(Integer, default=0)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    status = Column(String(20), default="planned")
    route_plan = Column(JSON, default=dict)
    delay_minutes = Column(Integer, default=0)
    notes = Column(Text)
    is_demo = Column(Boolean, default=False)


class CatalogMedia(Base):
    __tablename__ = "catalog_media"
    id = Column(Integer, primary_key=True)
    catalog_id = Column(Integer, ForeignKey("catalog_items.id"), nullable=False)
    kind = Column(String(20), default="image")  # image, video
    storage_path = Column(String(400))
    thumbnail_path = Column(String(400))
    external_url = Column(String(600))
    caption = Column(JSON, default=dict)
    credit = Column(String(180))
    source_url = Column(String(500))
    rights_basis = Column(String(40))  # owner, written_consent, license
    license_name = Column(String(120))
    rights_expires_at = Column(Date)
    consent_at = Column(DateTime)
    sort_order = Column(Integer, default=0)
    is_cover = Column(Boolean, default=False)
    is_demo = Column(Boolean, default=False)

    catalog = relationship("CatalogItem", back_populates="media")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("booking_item_id", name="uq_review_booking_item"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating"),
    )
    id = Column(Integer, primary_key=True)
    booking_item_id = Column(Integer, ForeignKey("booking_items.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    catalog_item_id = Column(Integer, ForeignKey("catalog_items.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    language = Column(String(5), default="fr")
    experience_date = Column(Date)
    status = Column(String(20), default="published")  # published, hidden
    verified = Column(Boolean, default=True)
    manager_response = Column(Text)
    response_by = Column(Integer, ForeignKey("users.id"))
    response_at = Column(DateTime)
    moderation_reason = Column(Text)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    catalog = relationship("CatalogItem", back_populates="reviews")
    customer = relationship("Customer")
    photos = relationship("ReviewPhoto", back_populates="review", cascade="all, delete-orphan")


class ReviewPhoto(Base):
    __tablename__ = "review_photos"
    id = Column(Integer, primary_key=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    storage_path = Column(String(400), nullable=False)
    consent = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    review = relationship("Review", back_populates="photos")


class ReviewInvitation(Base):
    __tablename__ = "review_invitations"
    id = Column(Integer, primary_key=True)
    booking_item_id = Column(Integer, ForeignKey("booking_items.id"), unique=True, nullable=False)
    channel = Column(String(20), default="email")
    scheduled_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime)
    reminder_sent_at = Column(DateTime)
    token = Column(String(120), unique=True)
    status = Column(String(20), default="scheduled")  # scheduled, queued, sent, reviewed, expired
    is_demo = Column(Boolean, default=False)


class ReviewReport(Base):
    __tablename__ = "review_reports"
    id = Column(Integer, primary_key=True)
    review_id = Column(Integer, ForeignKey("reviews.id"), nullable=False)
    reporter = Column(String(160))
    reason = Column(Text)
    status = Column(String(20), default="open")
    resolution = Column(Text)
    created_at = Column(DateTime, default=utcnow)


class RatingSnapshot(Base):
    __tablename__ = "rating_snapshots"
    id = Column(Integer, primary_key=True)
    catalog_item_id = Column(Integer, ForeignKey("catalog_items.id"), nullable=False)
    month = Column(String(7), nullable=False)  # YYYY-MM
    rating_avg = Column(Float)
    review_count = Column(Integer)
    distribution = Column(JSON, default=dict)


class VisitorPhoto(Base):
    __tablename__ = "visitor_photos"
    id = Column(Integer, primary_key=True)
    catalog_item_id = Column(Integer, ForeignKey("catalog_items.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    storage_path = Column(String(400), nullable=False)
    caption = Column(Text)
    consent = Column(Boolean, default=False)
    withdrawn_at = Column(DateTime)
    moderation_status = Column(String(20), default="pending")
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)


class Cart(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True)
    token = Column(String(80), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    status = Column(String(20), default="open")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    catalog_item_id = Column(Integer, ForeignKey("catalog_items.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id"))
    slot_id = Column(Integer, ForeignKey("availability_slots.id"))
    item_type = Column(String(30), default="activity")
    service_date = Column(Date)
    start_at = Column(DateTime)
    adults = Column(Integer, default=1)
    children = Column(Integer, default=0)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float)
    price_status = Column(String(20), default="missing")
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utcnow)

    cart = relationship("Cart", back_populates="items")
    catalog = relationship("CatalogItem")
    variant = relationship("Variant")
    slot = relationship("AvailabilitySlot")


class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    reference = Column(String(30), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(String(30), default="pending", index=True)
    total_amount = Column(Float)
    deposit_amount = Column(Float)
    currency = Column(String(5), default="MAD")
    score = Column(Integer, default=0)
    score_explanation = Column(Text)
    source = Column(String(80), default="site")
    special_requests = Column(Text)
    consent_version = Column(String(30))
    cancellation_policy = Column(Text)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    confirmed_at = Column(DateTime)
    completed_at = Column(DateTime)
    cancelled_at = Column(DateTime)

    customer = relationship("Customer", back_populates="bookings")
    items = relationship("BookingItem", back_populates="booking", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="booking")
    history = relationship("BookingStatusHistory", back_populates="booking")
    tickets = relationship("Ticket", back_populates="booking")


class BookingItem(Base):
    __tablename__ = "booking_items"
    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    catalog_item_id = Column(Integer, ForeignKey("catalog_items.id"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.id"))
    slot_id = Column(Integer, ForeignKey("availability_slots.id"))
    item_type = Column(String(30), nullable=False)
    service_date = Column(Date)
    start_at = Column(DateTime)
    end_at = Column(DateTime)
    adults = Column(Integer, default=1)
    children = Column(Integer, default=0)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float)
    line_total = Column(Float)
    price_status = Column(String(20), default="missing")
    pickup_catalog_id = Column(Integer, ForeignKey("catalog_items.id"))
    pickup_time = Column(DateTime)
    return_required = Column(Boolean, default=False)
    details = Column(JSON, default=dict)
    status = Column(String(20), default="pending")
    is_demo = Column(Boolean, default=False)

    booking = relationship("Booking", back_populates="items")
    catalog = relationship("CatalogItem", foreign_keys=[catalog_item_id])
    variant = relationship("Variant")
    slot = relationship("AvailabilitySlot")


class BookingStatusHistory(Base):
    __tablename__ = "booking_status_history"
    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    from_status = Column(String(30))
    to_status = Column(String(30), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"))
    note = Column(Text)
    created_at = Column(DateTime, default=utcnow)
    booking = relationship("Booking", back_populates="history")


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    payment_type = Column(String(30), default="deposit")
    amount = Column(Float)
    status = Column(String(20), default="pending")  # pending, received, refunded, failed
    method = Column(String(40), default="manual")
    due_at = Column(DateTime)
    received_at = Column(DateTime)
    reference = Column(String(100))
    recorded_by = Column(Integer, ForeignKey("users.id"))
    note = Column(Text)
    booking = relationship("Booking", back_populates="payments")


class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False)
    reference = Column(String(40), unique=True, nullable=False)
    qr_payload = Column(Text, nullable=False)
    qr_token_hash = Column(String(64))
    pdf_path = Column(String(400))
    issued_at = Column(DateTime, default=utcnow)
    scanned_at = Column(DateTime)
    status = Column(String(20), default="issued")
    booking = relationship("Booking", back_populates="tickets")


class TransportAssignment(Base):
    __tablename__ = "transport_assignments"
    id = Column(Integer, primary_key=True)
    booking_item_id = Column(Integer, ForeignKey("booking_items.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"))
    driver_id = Column(Integer, ForeignKey("drivers.id"))
    pickup_at = Column(DateTime)
    route_plan = Column(JSON, default=dict)
    status = Column(String(30), default="assigned")
    delay_minutes = Column(Integer, default=0)
    driver_rating = Column(Integer)
    notes = Column(Text)
    completed_at = Column(DateTime)


class Itinerary(Base):
    __tablename__ = "itineraries"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    title = Column(String(180))
    start_date = Column(Date)
    duration_days = Column(Integer, default=3)
    budget = Column(Float)
    group_json = Column(JSON, default=dict)
    interests = Column(JSON, default=list)
    locale = Column(String(5), default="fr")
    status = Column(String(20), default="draft")
    ai_model = Column(String(80))
    prompt_version = Column(String(20))
    notes = Column(Text)
    generated_at = Column(DateTime, default=utcnow)
    is_demo = Column(Boolean, default=False)

    days = relationship("ItineraryDay", back_populates="itinerary", cascade="all, delete-orphan")


class ItineraryDay(Base):
    __tablename__ = "itinerary_days"
    id = Column(Integer, primary_key=True)
    itinerary_id = Column(Integer, ForeignKey("itineraries.id"), nullable=False)
    day_number = Column(Integer, nullable=False)
    day_date = Column(Date)
    weather_snapshot = Column(JSON, default=dict)
    backup_plan = Column(Text)
    notes = Column(Text)
    itinerary = relationship("Itinerary", back_populates="days")
    items = relationship("ItineraryItem", back_populates="day", cascade="all, delete-orphan")


class ItineraryItem(Base):
    __tablename__ = "itinerary_items"
    id = Column(Integer, primary_key=True)
    day_id = Column(Integer, ForeignKey("itinerary_days.id"), nullable=False)
    catalog_item_id = Column(Integer, ForeignKey("catalog_items.id"))
    variant_id = Column(Integer, ForeignKey("product_variants.id"))
    start_time = Column(String(10))
    end_time = Column(String(10))
    transport_service_id = Column(Integer, ForeignKey("catalog_items.id"))
    estimated_price = Column(Float)
    price_status = Column(String(20), default="missing")
    notes = Column(Text)
    is_booked = Column(Boolean, default=False)
    day = relationship("ItineraryDay", back_populates="items")
    catalog = relationship("CatalogItem", foreign_keys=[catalog_item_id])


class AIConversation(Base):
    __tablename__ = "ai_conversations"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    locale = Column(String(5), default="fr")
    title = Column(String(180))
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    messages = relationship("AIMessage", back_populates="conversation", cascade="all, delete-orphan")


class AIMessage(Base):
    __tablename__ = "ai_messages"
    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("ai_conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    sources = Column(JSON, default=list)
    model = Column(String(80))
    guardrail_status = Column(String(30), default="ok")
    created_at = Column(DateTime, default=utcnow)
    conversation = relationship("AIConversation", back_populates="messages")


class MessageTemplate(Base):
    __tablename__ = "message_templates"
    id = Column(Integer, primary_key=True)
    code = Column(String(60), nullable=False)
    channel = Column(String(20), default="email")
    locale = Column(String(5), default="fr")
    subject = Column(String(240))
    body = Column(Text, nullable=False)
    is_approved = Column(Boolean, default=False)
    approved_by = Column(Integer, ForeignKey("users.id"))
    version = Column(Integer, default=1)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    __table_args__ = (UniqueConstraint("code", "channel", "locale", name="uq_template_code"),)


class OutboxMessage(Base):
    __tablename__ = "outbox_messages"
    id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    customer_id = Column(Integer, ForeignKey("customers.id"))
    template_code = Column(String(60))
    channel = Column(String(20), default="email")
    recipient_enc = Column(Text)
    subject = Column(String(240))
    body = Column(Text, nullable=False)
    status = Column(String(20), default="draft")  # draft, approved, sent, failed
    scheduled_at = Column(DateTime)
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    sent_at = Column(DateTime)
    error = Column(Text)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)


class ReviewSummary(Base):
    __tablename__ = "review_summaries"
    id = Column(Integer, primary_key=True)
    catalog_item_id = Column(Integer, ForeignKey("catalog_items.id"), nullable=False)
    period = Column(String(20), default="30d")
    strengths = Column(Text)
    improvements = Column(Text)
    source_review_ids = Column(JSON, default=list)
    model = Column(String(80))
    validated_by = Column(Integer, ForeignKey("users.id"))
    validated_at = Column(DateTime)
    generated_at = Column(DateTime, default=utcnow)


class Anomaly(Base):
    __tablename__ = "anomalies"
    id = Column(Integer, primary_key=True)
    anomaly_type = Column(String(60), nullable=False)
    severity = Column(String(20), default="info")
    entity_type = Column(String(40))
    entity_id = Column(Integer)
    details = Column(JSON, default=dict)
    status = Column(String(20), default="open")
    detected_at = Column(DateTime, default=utcnow)
    resolved_by = Column(Integer, ForeignKey("users.id"))
    resolved_at = Column(DateTime)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(80), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    details = Column(JSON, default=dict)
    ip_hash = Column(String(64))
    created_at = Column(DateTime, default=utcnow, index=True)


class Setting(Base):
    __tablename__ = "settings"
    key = Column(String(80), primary_key=True)
    value = Column(JSON)
    updated_by = Column(Integer, ForeignKey("users.id"))
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class BackupLog(Base):
    __tablename__ = "backup_logs"
    id = Column(Integer, primary_key=True)
    path = Column(String(500), nullable=False)
    size_bytes = Column(Integer)
    created_at = Column(DateTime, default=utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))


class ProviderCommission(Base):
    __tablename__ = "provider_commissions"
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False)
    booking_item_id = Column(Integer, ForeignKey("booking_items.id"))
    gross_amount = Column(Float)
    rate = Column(Float)
    commission_amount = Column(Float)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=utcnow)
    provider = relationship("Provider", back_populates="commissions")


class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    session_token = Column(String(80))
    catalog_item_id = Column(Integer, ForeignKey("catalog_items.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow)
    __table_args__ = (UniqueConstraint("customer_id", "session_token", "catalog_item_id", name="uq_favorite"),)
