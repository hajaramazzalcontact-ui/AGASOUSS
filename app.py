"""Point d'entrée Streamlit d'AZUL AGADIR (édité par AgadirGO).

Configure l'application, initialise la base, injecte le thème puis route
entre les pages visiteurs et le back-office protégé. La page courante est
portée par les paramètres d'URL (?page=...) afin que chaque vue reste
partageable par un lien.
"""
from __future__ import annotations

import logging
import os

from collections.abc import Callable

import streamlit as st
from sqlalchemy import func, select

from src.config import APP_EDITOR, APP_NAME, IS_DEMO
from src.db.models import Cart, CartItem
from src.db.session import configure_database, get_session, init_database
from src.i18n import LANGUAGES, direction, locale_name, t
from src.ui.components import esc, page_link
from src.ui.theme import inject_theme

from src.ui.pages_catalog import (
    render_accommodations,
    render_discover,
    render_home,
    render_map,
    render_restaurants,
    render_transport,
)
from src.ui.pages_journey import (
    render_account,
    render_assistant,
    render_cart,
    render_itinerary,
    render_legal,
    render_reviews,
)
from src.ui.pages_admin import render_admin

LOG = logging.getLogger(__name__)

# Pages visiteurs : clé d'URL -> (libellé, fonction de rendu).
VISITOR_PAGES: dict[str, tuple[str, Callable]] = {
    "accueil": (t("home", "fr"), render_home),
    "decouvrir": (t("discover", "fr"), render_discover),
    "restaurants": (t("restaurants", "fr"), render_restaurants),
    "hebergements": (t("accommodations", "fr"), render_accommodations),
    "transport": (t("transport", "fr"), render_transport),
    "carte": (t("map", "fr"), render_map),
    "sejour": (t("itinerary", "fr"), render_itinerary),
    "panier": (t("cart", "fr"), render_cart),
    "espace": (t("account", "fr"), render_account),
    "assistant": (t("assistant", "fr"), render_assistant),
    "avis": (t("latest_reviews", "fr"), render_reviews),
    "legal": ("Mentions légales", render_legal),
}


def _init_session() -> None:
    """Valeurs par défaut de la session Streamlit."""
    defaults = {
        "lang": "fr",
        "dark_mode": False,
        "customer_id": None,
        "cart_token": None,
        "admin_user_id": None,
        "chat": [],
        "plan": None,
        "last_booking_id": None,
        "generated_message": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_resource(show_spinner="Préparation de la base…")
def _setup_database() -> None:
    """Garantit le schéma et, en mode DÉMO, les données fictives.

    Sur un déploiement neuf (Streamlit Community Cloud), la base locale
    n'est pas versionnée par Git : sans cette étape, les requêtes
    échouent avec « no such table ». Exécutée une seule fois par process.
    """
    configure_database()
    init_database()
    # Photos réelles (Wikimedia Commons, licences libres) : manifeste
    # d'abord (instantané, hors ligne), récolte réseau brève ensuite pour
    # les fiches encore sans photo. Idempotent ; désactivable via
    # AZUL_SKIP_STARTUP_PHOTOS=1.
    if IS_DEMO and os.getenv("AZUL_SKIP_STARTUP_PHOTOS", "").strip().lower() not in {"1", "true", "yes"}:
        try:
            from src.services.photos import apply_real_photos

            session = get_session()
            try:
                apply_real_photos(session, max_media_per_item=6, budget_seconds=60.0)
            finally:
                session.close()
        except Exception as exc:  # hors ligne : les visuels SVG prennent le relais
            LOG.warning("Pipeline photos ignorée (%s)", exc)


def _cart_count() -> int:
    """Nombre d'articles dans le panier courant, sans le créer."""
    token = st.session_state.get("cart_token")
    if not token:
        return 0
    session = get_session()
    try:
        count = session.scalar(
            select(func.count(CartItem.id))
            .join(Cart, CartItem.cart_id == Cart.id)
            .where(Cart.token == token, Cart.status == "open")
        )
        return int(count or 0)
    except Exception:
        return 0
    finally:
        session.close()


def _change_language(new_lang: str) -> None:
    st.session_state["lang"] = new_lang
    st.query_params["lang"] = new_lang
    st.rerun()


def _render_topbar(locale: str, rtl: bool) -> None:
    """Bandeau supérieur : marque, DÉMO, langue, thème, panier, espace pro."""
    c_logo, c_utils = st.columns([7, 5])
    with c_logo:
        st.markdown(
            f"""
            <div class="az-topbar">
              <div>
                <a class="az-brand" href="{page_link('accueil')}">
                  <span class="mark">AZUL</span><span class="sub">AGADIR</span><span class="by">par {APP_EDITOR}</span>
                </a>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if IS_DEMO:
            st.markdown(
                f'<div class="az-note" style="margin:0 0 6px 0">🧪 <b>DÉMO</b> — {esc(t("demo_banner", locale))}</div>',
                unsafe_allow_html=True,
            )
    with c_utils:
        uc1, uc2, uc3 = st.columns([2, 1, 2])
        with uc1:
            labels = {code: f"{info['flag']} {info['label']}" for code, info in LANGUAGES.items()}
            current = st.session_state.get("lang", "fr")
            chosen = st.selectbox(
                "Langue", list(labels),
                index=list(labels).index(current) if current in labels else 0,
                format_func=lambda x: labels[x],
                label_visibility="collapsed",
            )
            if chosen != current:
                _change_language(chosen)
        with uc2:
            if st.button("☀️" if st.session_state.get("dark_mode") else "🌙",
                         key="theme_toggle", help="Thème clair / sombre"):
                st.session_state["dark_mode"] = not bool(st.session_state.get("dark_mode"))
                st.rerun()
        with uc3:
            count = _cart_count()
            cart_badge = (
                f'<a class="az-chip" href="{page_link("panier")}">🛒'
                + (f'<span class="cart-count">{count}</span>' if count else "")
                + "</a>"
            )
            st.markdown(
                f"""
                <div class="az-utility" style="{'direction:rtl' if rtl else ''}">
                  <a class="az-chip" href="{page_link('admin')}">{t('admin', locale)}</a>
                  {cart_badge}
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_nav(locale: str, current_page: str) -> None:
    """Navigation principale par pastilles."""
    pills = "".join(
        f'<a class="az-chip{" active" if key == current_page else ""}" href="{page_link(key)}">{label}</a>'
        for key, (label, _) in VISITOR_PAGES.items()
    )
    st.markdown(f'<div class="az-nav">{pills}</div>', unsafe_allow_html=True)


def _render_footer(locale: str) -> None:
    st.markdown(
        f"""
        <div class="az-footer">
          <div>
            <span class="brand">AZUL AGADIR</span><br>
            Édité par {APP_EDITOR} · Agadir, Souss-Massa, Maroc<br>
            {esc("Application en mode démonstration." if IS_DEMO else "")}
          </div>
          <div>
            <a href="{page_link('legal', doc='privacy')}">Confidentialité</a> ·
            <a href="{page_link('legal', doc='cgu')}">CGU</a> ·
            <a href="{page_link('legal', doc='cookies')}">Cookies</a><br>
            Conforme loi marocaine 09-08 · démonstration sans données réelles.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(
        page_title=f"{APP_NAME} — {APP_EDITOR}",
        page_icon="✦",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _init_session()
    _setup_database()

    locale = st.session_state.get("lang", "fr")
    rtl = direction(locale) == "rtl"
    inject_theme(dark=bool(st.session_state.get("dark_mode")), rtl=rtl)

    # La langue reste lisible dans l'URL pour un partage simple.
    if st.query_params.get("lang") != locale:
        st.query_params["lang"] = locale

    page = st.query_params.get("page", "accueil")
    if page != "admin" and page not in VISITOR_PAGES:
        # La modification des query params déclenche déjà un rerun : inutile
        # d'en ajouter un second (source de clignotements et d'erreurs DOM).
        st.query_params["page"] = "accueil"
        page = "accueil"

    if page == "admin":
        render_admin(locale)
        return

    _render_topbar(locale, rtl)
    _render_nav(locale, page)

    _, render_page = VISITOR_PAGES[page]
    render_page(locale)

    _render_footer(locale)


if __name__ == "__main__":
    main()
