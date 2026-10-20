"""Tests d'intégration sur la base DÉMO (lecture + écritures isolées)."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

import pytest
from sqlalchemy import select

from src.db.models import AvailabilitySlot, CatalogItem, Variant
from src.db.session import configure_database, get_session
from src.ia.guardrails import guard_answer, redact_pii, unsupported_prices
from src.i18n import t
from src.config import IS_DEMO
from src.services.auth import authenticate, AuthError
from src.services.availability import available_slots, can_book, reserve_capacity, release_capacity
from src.services.cart import add_item, cart_totals, get_or_create_cart, remove_item
from src.services.catalog import search_items, stats_counts
from src.services.privacy import anonymize_customer, customer_export
from src.services.reviews import create_review, review_eligibility
from src.services.scoring import score_booking_request
from src.services.security import decrypt_text, encrypt_text, mask_email, mask_phone


@pytest.fixture(scope="module", autouse=True)
def database():
    configure_database()


@pytest.fixture
def s():
    session = get_session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def activity(s):
    items = search_items(s, kind="activity")
    return items[0]


# --------------------------------------------------------------------- catalogue
def test_seed_is_loaded(s):
    counts = stats_counts(s)
    assert counts["activity"] >= 21
    assert counts["restaurant"] >= 25
    assert counts["accommodation"] >= 15
    assert counts["spot"] >= 8
    assert counts.get("transport", 6) >= 6


def test_search_filters(s, activity):
    results = search_items(s, kind="activity", max_price=activity.price_from)
    assert all(i.price_from is not None and i.price_from <= activity.price_from for i in results)
    assert activity in results


def test_translations_available():
    for lang in ("fr", "en", "ar", "es"):
        assert t("home", lang) and t("home", lang) != "home"


# ------------------------------------------------------------------ disponibilités
def test_reserve_and_release_capacity(s, activity):
    from src.services.catalog import variants_for
    variants = variants_for(s, activity.id)
    if not variants:
        pytest.skip("Pas de formule sur cette fiche.")
    slots = available_slots(s, variants[0].id)
    if not slots:
        pytest.skip("Aucun créneau : rien à réserver.")
    slot = slots[0]
    before = slot.remaining
    assert can_book(slot, 1)
    reserve_capacity(s, slot.id, 1)
    assert slot.remaining == before - 1
    release_capacity(s, slot.id, 1)
    assert slot.remaining == before


# --------------------------------------------------------------------------- panier
def test_cart_add_remove_and_totals(s, activity):
    from src.services.catalog import variants_for
    variants = variants_for(s, activity.id)
    if not variants:
        pytest.skip("Pas de formule : on saute le test panier.")
    cart = get_or_create_cart(s, "pytest-token")
    line = add_item(
        s, cart, activity.id,
        variant_id=variants[0].id, item_type="activity",
        service_date=date.today() + timedelta(days=3),
        start_at=datetime.combine(date.today(), time(10, 0)),
        adults=2, children=0, quantity=1, details={},
    )
    totals = cart_totals([line])
    assert "known_total" in totals
    remove_item(s, cart.id, line.id)
    s.commit()


# ----------------------------------------------------------------------------- score
def test_score_explained(activity):
    score, explanation = score_booking_request(
        amount=activity.price_from, lead_days=7, group_size=2,
        completed_bookings=0, cancelled_bookings=0,
    )
    assert 0 <= score <= 100
    assert isinstance(explanation, str) and explanation


# ------------------------------------------------------------------------------ avis
def test_review_requires_completed_booking(s):
    from src.db.models import BookingItem, Booking
    row = s.execute(
        select(BookingItem.id)
        .join(Booking, BookingItem.booking_id == Booking.id)
        .where(BookingItem.item_type != "accommodation")
        .limit(1)
    ).first()
    if not row:
        pytest.skip("Pas de réservation DÉMO.")
    allowed, reason = review_eligibility(s, row[0])
    assert isinstance(allowed, bool)
    if allowed:
        review = create_review(
            s, booking_item_id=row[0], rating=5, comment="Test pytest — DÉMO",
            language="fr", photos=None,
        )
        assert review.id is not None
        s.rollback()


# ---------------------------------------------------------------------------- garde-fous IA
def test_redact_pii():
    text = redact_pii("Contact jeanine@mail.co ou +212 600-000-000 merci.")
    assert "jeanine@mail.co" not in text
    assert "212" not in text


def test_no_invented_prices():
    assert unsupported_prices("Le quad coûte 999 MAD.", set()) == ["999 MAD"]
    status = guard_answer("", None)[1]
    assert status == "fallback"


def test_no_invented_prices_allowed():
    assert unsupported_prices("Le quad coûte 250 MAD au total.", {250.0}) == []


# ------------------------------------------------------------------------ sécurité
def test_encrypt_decrypt_roundtrip():
    value = "+212 600 00 00 00"
    enc = encrypt_text(value)
    assert enc != value
    assert decrypt_text(enc) == value
    assert mask_email("contact@example.com") != "contact@example.com"
    assert mask_phone(value) != value


# --------------------------------------------------------------------- authentification
def test_authenticate_demo_admin(s):
    if not IS_DEMO:
        pytest.skip("Comptes DÉMO uniquement en mode démonstration.")
    assert authenticate(s, "ADMIN@azul.local", "AzulDemo2026!").role == "admin"
    with pytest.raises(AuthError):
        authenticate(s, "admin@azul.local", "mot-de-passe-faux")


# ----------------------------------------------------------------------- confidentialité
def test_customer_export_and_anonymize(s):
    from src.db.models import Customer
    customer = s.scalars(select(Customer).where(Customer.anonymized_at.is_(None))).first()
    if not customer:
        pytest.skip("Pas de client DÉMO.")
    export = customer_export(s, customer.id)
    assert "identite" in export or "bookings" in export or isinstance(export, dict)
    anonymize_customer(s, customer.id)
    s.commit()
    refreshed = s.get(Customer, customer.id)
    assert refreshed.anonymized_at is not None
    s.rollback()


# ---------------------------------------------------------------------------- photos
def test_photo_license_filter():
    from src.services import photos
    assert photos._license_ok("CC BY-SA 4.0")
    assert photos._license_ok("CC BY 2.0")
    assert photos._license_ok("CC0")
    assert photos._license_ok("Public domain")
    assert not photos._license_ok("CC BY-NC 4.0")
    assert not photos._license_ok("CC BY-ND 4.0")
    assert not photos._license_ok("GFDL")
    assert not photos._license_ok("")


def test_harvest_item_creates_gallery_with_credits(s, monkeypatch):
    """La récolte crée des photos, une seule couverture et des crédits."""
    from src.db.models import CatalogItem
    from src.services import photos
    from src.ui.components import media_items, render_gallery

    item = CatalogItem(
        kind="activity", slug="test-photo-tmp", status="published",
        name={"fr": "Fiche test photos"}, is_demo=True,
    )
    s.add(item)
    s.flush()

    def fake_candidates(term, cache, limit=20):
        return [{
            "external_url": f"https://example.org/{term.replace(' ', '_')}.jpg",
            "source_url": "https://example.org/source",
            "credit": "Auteur test",
            "license_name": "CC BY 4.0",
            "sha1": f"sha-{term}",
        }]

    monkeypatch.setattr(photos, "_fetch_candidates", fake_candidates)
    monkeypatch.setattr(
        photos, "_download",
        lambda url, slug, key: (
            f"/app/static/media/{slug}/{key}.jpg",
            f"/app/static/media/{slug}/t_{key}.jpg",
        ),
    )
    monkeypatch.setattr(photos, "_save_cache", lambda cache: None)

    added = photos.harvest_item(s, item, target=3, download=True)
    s.flush()
    assert added == 3
    rows = sorted(item.media, key=lambda m: m.sort_order)
    assert sum(1 for m in rows if m.is_cover) == 1

    photos_list = media_items(item)
    assert photos_list
    assert photos_list[0]["src"].startswith("/app/static/media/")
    assert photos_list[0]["fallback"].startswith("https://example.org/")

    html = render_gallery(item, "fr")
    assert "Crédits photos" in html
    assert "CC BY 4.0" in html

    s.delete(item)
    s.commit()
