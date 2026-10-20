"""Helpers partagés par les pages visiteurs."""
from __future__ import annotations

from datetime import date, datetime

import streamlit as st
from sqlalchemy import func, select

from src.db.models import Cart, CartItem, CatalogItem, Customer, Review
from src.i18n import t
from src.services.cart import get_or_create_cart
from src.services.catalog import localized, slots_for
from src.services.security import decrypt_text, new_cart_token
from .components import esc, page_link, rating_summary, review_card, section_head, stars


def get_customer(s, customer_id: int | None) -> Customer | None:
    return s.get(Customer, customer_id) if customer_id else None


def current_cart_token() -> str:
    if not st.session_state.get("cart_token"):
        st.session_state.cart_token = new_cart_token()
    return st.session_state.cart_token


def get_cart(s):
    return get_or_create_cart(s, current_cart_token(), st.session_state.get("customer_id"))


def cart_item_count(s) -> int:
    token = st.session_state.get("cart_token")
    if not token:
        return 0
    return s.scalar(
        select(func.count(CartItem.id)).join(Cart, CartItem.cart_id == Cart.id)
        .where(Cart.token == token, Cart.status == "open")
    ) or 0


def page_heading(kicker: str, title: str, subtitle: str = "", locale: str = "fr") -> None:
    st.markdown(
        f"""
        <div style="margin:14px 0 18px 0">
          <span class="az-kicker">{esc(kicker)}</span>
          <h1 style="font-size:clamp(2.1rem,4.2vw,3.7rem);margin:2px 0 6px">{esc(title)}</h1>
          {f'<p style="color:var(--azul-muted);max-width:720px;font-size:.9rem;line-height:1.6">{esc(subtitle)}</p>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def demo_note(locale: str = "fr") -> None:
    st.markdown(
        f'<div class="az-note" style="margin:0 0 18px 0">🧪 <b>DÉMO</b> — {esc(t("demo_banner", locale))}</div>',
        unsafe_allow_html=True,
    )


def item_reviews_block(s, item, locale: str, limit: int | None = None) -> None:
    from src.services.catalog import item_reviews
    reviews = item_reviews(s, item.id, limit=limit)
    st.markdown(rating_summary(reviews, locale), unsafe_allow_html=True)
    if not reviews:
        return
    shown = reviews[:6]
    for index in range(0, len(shown), 2):
        cols = st.columns(2, gap="medium")
        for col, review in zip(cols, shown[index:index + 2]):
            with col:
                st.markdown(review_card(review, locale), unsafe_allow_html=True)
    if len(reviews) > 6:
        st.caption(f"{len(reviews)} avis vérifiés au total — les critiques sont affichées et peuvent recevoir une réponse.")


def accommodation_options(s, locale: str = "fr") -> list[CatalogItem]:
    return list(s.scalars(
        select(CatalogItem).where(CatalogItem.kind == "accommodation", CatalogItem.status == "published")
    ).all())


def pickup_select(s, locale: str, key: str):
    accs = accommodation_options(s, locale)
    labels = {0: "— Je ne sais pas encore —"}
    for acc in accs:
        labels[acc.id] = localized(acc.name, locale)
    return st.selectbox(
        "Hébergement / prise en charge" if locale == "fr" else {
            "en": "Pickup accommodation", "ar": "مكان الالتقاط", "es": "Alojamiento de recogida"
        }.get(locale, "Pickup"),
        options=list(labels.keys()), format_func=lambda x: labels[x], key=key,
    )


def slot_label(slot, locale: str = "fr") -> str:
    if locale == "fr":
        day = slot.start_at.strftime("%d/%m/%Y")
        return f"{day} · {slot.start_at.strftime('%H:%M')} · {slot.remaining} place(s)"
    return f"{slot.start_at.strftime('%d/%m/%Y %H:%M')} · {slot.remaining} left"


def render_slot_choice(s, variant_id: int, locale: str, key: str, days: int = 60):
    slots = slots_for(s, variant_id, days=days)
    if not slots:
        st.info(t("no_slot", locale))
        return None
    options = {slot.id: slot_label(slot, locale) for slot in slots[:60]}
    return st.selectbox(
        t("choose_time", locale), options=list(options.keys()),
        format_func=lambda x: options[x], key=key,
    )


def add_to_cart_and_go(s, item, *, variant_id=None, slot_id=None, item_type=None, service_date=None,
                       start_at=None, adults=1, children=0, quantity=1, details=None, locale="fr"):
    from src.services.cart import add_item
    cart = get_cart(s)
    try:
        add_item(
            s, cart, item.id, variant_id=variant_id, slot_id=slot_id,
            item_type=item_type or item.kind, service_date=service_date, start_at=start_at,
            adults=adults, children=children, quantity=quantity, details=details or {},
        )
        s.commit()
        st.toast(t("added", locale), icon="✓")
        st.rerun()
    except Exception as exc:
        st.error(str(exc))


def back_link(page: str, label: str) -> None:
    st.markdown(
        f'<div style="margin:6px 0 14px 0"><a target="_self" class="az-chip" href="{page_link(page)}">← {esc(label)}</a></div>',
        unsafe_allow_html=True,
    )


def selected_slot_datetime(s, slot_id):
    from src.db.models import AvailabilitySlot
    slot = s.get(AvailabilitySlot, slot_id) if slot_id else None
    return (slot.start_at if slot else None), (slot.start_at.date() if slot else None)


def item_small_line(item, locale: str, subtitle: str = "", price: str = "") -> str:
    from .components import art_svg
    return f"""
    <div style="display:flex;gap:12px;align-items:center;background:var(--azul-surface);border:1px solid var(--azul-line);border-radius:18px;padding:10px;margin-bottom:8px">
      <div style="width:76px;height:64px;border-radius:12px;overflow:hidden;flex:0 0 auto">{art_svg(item, 2)}</div>
      <div style="flex:1;min-width:0">
        <div style="font-size:.6rem;color:var(--azul-ocean);font-weight:800;text-transform:uppercase;letter-spacing:.1em">{esc(subtitle)}</div>
        <div style="font-family:'Cormorant Garamond',serif;font-size:1.12rem;line-height:1.1">{esc(localized(item.name, locale))}</div>
        {f'<div class="az-lesstext">{esc(price)}</div>' if price else ''}
      </div>
    </div>
    """
