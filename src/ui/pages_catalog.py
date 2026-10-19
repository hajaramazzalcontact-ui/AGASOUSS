"""Pages catalogue : accueil, découvrir, restaurants, hébergements, transport, carte."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta

import pandas as pd
import streamlit as st
from sqlalchemy import select

from src.config import CENTER_LAT, CENTER_LNG
from src.db.models import AvailabilitySlot, CatalogItem, Customer, Review
from src.db.session import get_session
from src.i18n import t
from src.ia.assistant import is_available
from src.ia.client import complete as ai_complete
from src.ia.recommendations import cross_sell, recommend
from src.services.analytics import nationality_breakdown, top_activities
from src.services.catalog import (
    all_items,
    detail_for,
    display_price,
    get_by_slug,
    item_reviews,
    kind_label,
    localized,
    money,
    price_unit_label,
    recent_reviews,
    search_items,
    slots_for,
    stats_counts,
    variants_for,
)
from src.services.routing import distance_from_center, travel_minutes
from src.services.weather import get_weather_sea
from .common import (
    accommodation_options,
    add_to_cart_and_go,
    back_link,
    current_cart_token,
    demo_note,
    get_cart,
    get_customer,
    item_small_line,
    page_heading,
    pickup_select,
    render_slot_choice,
    slot_label,
)
from .components import (
    animated_counters,
    art_svg,
    empty_state,
    esc,
    gallery,
    hero,
    item_card,
    item_grid,
    page_link,
    rating_summary,
    review_card,
    section_head,
    stars,
    vibe_tiles,
)


def _personalized_greeting(customer, weather: dict, locale: str) -> str | None:
    if not customer:
        return None
    key = f"azul_greeting_{customer.id}_{locale}"
    if key in st.session_state:
        return st.session_state[key]
    local = {
        "fr": f"Azul {customer.first_name}. {weather.get('summary', 'Belle journée')} sur la baie — votre prochaine expérience commence ici.",
        "en": f"Azul {customer.first_name}. {weather.get('summary', 'A beautiful day')} over the bay — your next experience starts here.",
        "ar": f"أزول {customer.first_name}. {weather.get('summary', 'يوم جميل')} على الخليج — تجربتك القادمة تبدأ هنا.",
        "es": f"Azul {customer.first_name}. {weather.get('summary', 'Un día precioso')} en la bahía — tu próxima experiencia empieza aquí.",
    }.get(locale, "")
    if is_available():
        generated = ai_complete(
            "Tu écris une seule phrase d'accueil chaleureuse pour Azul AGADIR. "
            "Tu ne cites aucun prix, horaire ou disponibilité. Maximum 22 mots.",
            f"Langue: {locale}. Client: {customer.first_name}. Météo: {weather.get('summary')}. "
            f"Intérêts: {', '.join(customer.interests or [])}. "
            "Écris la phrase, sans guillemets.",
            max_tokens=80,
        )
        if generated:
            local = generated.strip().replace('"', "")
    st.session_state[key] = local
    return local


def _weekly_favorites(s, limit: int = 6) -> list[CatalogItem]:
    since = datetime.now() - timedelta(days=45)
    reviews = list(s.scalars(select(Review).where(
        Review.status == "published", Review.verified.is_(True), Review.created_at >= since
    )).all())
    scores: dict[int, float] = {}
    for review in reviews:
        scores[review.catalog_item_id] = scores.get(review.catalog_item_id, 0) + (review.rating / 5) + 0.15
    ids = [item_id for item_id, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)][:limit]
    items = [s.get(CatalogItem, item_id) for item_id in ids]
    items = [item for item in items if item and item.status == "published"]
    if len(items) < limit:
        filled = sorted(
            [i for i in all_items(s) if i.kind in {"activity", "restaurant", "accommodation"}],
            key=lambda i: (i.rating_avg or 0, i.review_count or 0), reverse=True,
        )
        for item in filled:
            if item not in items:
                items.append(item)
            if len(items) >= limit:
                break
    return items[:limit]


def render_home(locale: str) -> None:
    s = get_session()
    try:
        customer = get_customer(s, st.session_state.get("customer_id"))
        counts = stats_counts(s)
        weather = get_weather_sea()
        greeting = _personalized_greeting(customer, weather, locale)
        st.markdown(hero(locale, customer.first_name if customer else None, weather, counts), unsafe_allow_html=True)
        animated_counters(counts, locale)
        st.caption(
            f"Météo et mer : {weather.get('source')} · mise à jour {weather.get('updated_at')} · "
            "données indicatives, consignes de sécurité à vérifier sur place."
        )

        st.markdown(section_head(
            "Choisir une ambiance", t("vibes", locale),
            "Huit portes d'entrée pour trouver l'expérience qui vous ressemble.",
        ), unsafe_allow_html=True)
        st.markdown(vibe_tiles(locale), unsafe_allow_html=True)

        st.markdown(section_head(
            "Sélection Azul", t("favorites_week", locale),
            "Classement fondé sur les avis vérifiés récents — contenus et notes de démonstration.",
            t("see", locale), page_link("decouvrir"),
        ), unsafe_allow_html=True)
        favorites = _weekly_favorites(s, 6)
        if favorites:
            st.markdown(
                '<div class="az-grid">' + "".join(item_card(i, locale) for i in favorites) + "</div>",
                unsafe_allow_html=True,
            )
        else:
            empty_state("✦", t("no_results", locale))

        reviews = recent_reviews(s, 6)
        st.markdown(section_head(
            "Avis vérifiés", t("latest_reviews", locale),
            "Seuls les clients ayant une prestation terminée reçoivent une invitation. Les critiques sont visibles.",
            t("see_all", locale), page_link("avis"),
        ), unsafe_allow_html=True)
        if reviews:
            cols_html = "".join(
                f'<div>{review_card(r, locale, show_item=True)}</div>' for r in reviews[:6]
            )
            st.markdown(f'<div class="az-grid">{cols_html}</div>', unsafe_allow_html=True)

        st.markdown(section_head(
            "Votre séjour", "Un programme qui respire",
            "Durée, budget, envies et météo : Azul assemble les jours et prévoit un plan B.",
            t("plan", locale), page_link("itinerary"),
        ), unsafe_allow_html=True)
        st.markdown(f"""
        <div class="az-detail-copy" style="display:grid;grid-template-columns:1.3fr .7fr;gap:18px;align-items:center">
          <div>
            <span class="az-kicker">Planificateur Azul</span>
            <h2 style="margin:4px 0 6px">Trois jours entre océan, artisanat et tables du Souss.</h2>
            <p class="lead" style="color:var(--azul-muted)">
              Un exemple de programme de démonstration. Aucun prix, horaire ou disponibilité
              n'est inventé : ce qui manque est marqué « à confirmer ».
            </p>
            <a class="az-btn primary" href="{page_link('itinerary')}">Composer mon séjour →</a>
          </div>
          <div style="border-radius:22px;overflow:hidden;min-height:220px">{art_svg(type('X', (), {'kind':'spot','id':7})(), 1, tall=True)}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="az-trust">
          <div><b>Paiement expliqué</b>Aucun paiement en ligne en V1. Acompte suivi manuellement, sans prélèvement automatique.</div>
          <div><b>Prestataires vérifiés</b>Chaque partenaire dispose d'une fiche, d'un contrat et d'un accès limité à ses réservations.</div>
          <div><b>Avis intègres</b>Impossible de créer ou modifier un avis. Seule la modération motivée peut masquer un contenu illégal.</div>
        </div>
        """, unsafe_allow_html=True)
    finally:
        s.close()


def _render_activity_booking(s, item, locale: str) -> None:
    variants = variants_for(s, item.id)
    if not variants:
        st.info("Aucune formule réservable n'est encore renseignée. Contactez l'équipe.")
        return
    with st.form(f"book_activity_{item.id}"):
        st.markdown(f"#### {t('request', locale)}")
        labels = {v.id: localized(v.name, locale) for v in variants}
        variant_id = st.selectbox("Formule", list(labels), format_func=lambda x: labels[x])
        variant = s.get(type(variants[0]), variant_id)
        slots = slots_for(s, variant.id, days=75)
        slot_id = None
        if slots:
            options = {sl.id: slot_label(sl, locale) for sl in slots[:80]}
            slot_id = st.selectbox(t("choose_time", locale), list(options), format_func=lambda x: options[x])
        else:
            st.info(t("no_slot", locale))
        c1, c2 = st.columns(2)
        with c1:
            adults = st.number_input(t("adults", locale), 1, 20, 2)
        with c2:
            children = st.number_input(t("kids", locale), 0, 10, 0)
        pickup_id = pickup_select(s, locale, f"pickup_act_{item.id}")
        st.caption(f"Prix indicatif : {display_price(item, locale)}. Le prix final est confirmé par l'équipe.")
        submitted = st.form_submit_button(t("add_cart", locale), use_container_width=True, type="primary")
        if submitted:
            slot = s.get(AvailabilitySlot, slot_id) if slot_id else None
            add_to_cart_and_go(
                s, item, variant_id=variant.id, slot_id=slot_id, item_type="activity",
                service_date=slot.start_at.date() if slot else None,
                start_at=slot.start_at if slot else None,
                adults=int(adults), children=int(children), quantity=1,
                details={"pickup_catalog_id": pickup_id or None}, locale=locale,
            )


def _render_activity_detail(s, item, locale: str) -> None:
    detail = detail_for(s, item)
    back_link("decouvrir", "Retour au catalogue")
    st.markdown(f'<div class="az-gallery">{gallery(item, locale)}</div>', unsafe_allow_html=True)
    rating_line = f'<span class="az-stars">{stars(item.rating_avg)}</span> <b>{item.rating_avg or 0:.1f}</b> · {item.review_count or 0} {t("reviews", locale)}'
    facts = [
        ("Durée", f"{detail.duration_minutes} min" if detail and detail.duration_minutes else "À confirmer"),
        ("Distance", f"{item.distance_center_km:.0f} km" if item.distance_center_km is not None else "—"),
        ("Capacité", str(item.capacity or "À confirmer")),
        ("Langues", " · ".join((item.languages or [])[:4]).upper() or "À confirmer"),
        ("Public", " · ".join(detail.audience or []) if detail else "À confirmer"),
        ("Effort", (detail.effort_level or "À confirmer").title() if detail else "À confirmer"),
    ]
    facts_html = "".join(f'<div class="az-fact"><span>{esc(k)}</span><b>{esc(v)}</b></div>' for k, v in facts)
    st.markdown(f"""
    <div class="az-detail-hero">
      <div class="az-detail-art">{art_svg(item, 1, tall=True)}</div>
      <div class="az-detail-copy">
        <div class="az-chip-row"><span class="az-badge demo">DÉMO</span><span class="az-badge verified">✓ Avis vérifiés</span></div>
        <div class="az-card-kind">{esc(localized(kind_label(item.kind, locale), locale))} · {esc(item.zone or item.district or 'Agadir')}</div>
        <h1>{esc(localized(item.name, locale))}</h1>
        <div class="lead">{esc(localized(item.short_description, locale))}</div>
        <div class="az-rating-line">{rating_line}</div>
        <div class="az-price" style="font-size:1.05rem">{esc(display_price(item, locale))}</div>
        {facts_html}
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f'<div class="az-prose">{esc(localized(item.long_description, locale))}</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<div class="az-note"><b>À apporter</b><br>{esc(localized(detail.what_to_bring, locale) if detail else "À confirmer")}</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="az-note"><b>Météo</b><br>{esc(localized(detail.weather_notes, locale) if detail else "À confirmer")}</div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="az-note"><b>Sécurité</b><br>{esc(localized(detail.safety_notes, locale) if detail else "À confirmer")}</div>', unsafe_allow_html=True)

    st.markdown(section_head("Réservation", "Choisissez votre moment", "Les créneaux affichés viennent de la base de démonstration."), unsafe_allow_html=True)
    _render_activity_booking(s, item, locale)

    st.markdown(section_head("Avis", "Ce que disent les voyageurs", "Avis vérifiés de démonstration, affichés sans filtrage de note."), unsafe_allow_html=True)
    with st.expander(t("see_all", locale), expanded=True):
        from .common import item_reviews_block
        item_reviews_block(s, item, locale)

    related = cross_sell(s, item, 3)
    if related:
        st.markdown(section_head("Après l'activité", "À combiner avec Azul"), unsafe_allow_html=True)
        st.markdown('<div class="az-grid">' + "".join(item_card(i, locale) for i in related) + "</div>", unsafe_allow_html=True)


def render_discover(locale: str) -> None:
    s = get_session()
    try:
        slug = st.query_params.get("item")
        if slug:
            item = get_by_slug(s, slug)
            if item:
                if item.kind != "activity":
                    st.warning("Cette fiche se consulte depuis sa rubrique dédiée.")
                _render_activity_detail(s, item, locale)
                return
        page_heading(
            "Catalogue Azul", "Des expériences à la mesure du Souss",
            "Filtrez par envie, budget, durée, distance ou note. Chaque fiche indique clairement ce qui reste à confirmer.",
            locale,
        )
        demo_note(locale)
        default_vibe = st.query_params.get("vibe")
        default_vibes = [default_vibe] if default_vibe else []
        with st.form("discover_filters"):
            st.markdown(f"#### {t('filters', locale)}")
            c1, c2 = st.columns([2, 1])
            with c1:
                query = st.text_input(t("search", locale), placeholder=t("search_placeholder", locale))
            with c2:
                sort_by = st.selectbox("Trier par", ["Recommandé", "Note", "Prix", "Distance"])
            vibes = st.multiselect(
                t("vibes", locale),
                options=["aventure", "famille", "culture", "nature", "mer", "gastronomie", "detente", "jeux"],
                default=default_vibes,
                format_func=lambda v: {
                    "aventure": "Aventure", "famille": "Famille", "culture": "Culture & artisanat",
                    "nature": "Nature & animaux", "mer": "Mer", "gastronomie": "Gastronomie",
                    "detente": "Détente", "jeux": "Jeux & loisirs",
                }[v],
            )
            c3, c4, c5 = st.columns(3)
            with c3:
                max_price = st.slider(t("budget", locale) + " (MAD)", 0, 2000, 2000, step=50)
            with c4:
                max_distance = st.slider(t("distance", locale) + " (km)", 0, 90, 90, step=5)
            with c5:
                min_rating = st.slider(t("rating", locale), 0.0, 5.0, 0.0, step=0.5)
            c6, c7 = st.columns(2)
            with c6:
                family = st.checkbox(t("children", locale))
            with c7:
                duration_choice = st.selectbox(t("duration", locale), [0, 60, 120, 180, 240, 480],
                                               format_func=lambda x: "Toutes" if x == 0 else f"≤ {x // 60} h")
            submitted = st.form_submit_button(t("apply", locale), type="primary", use_container_width=True)
        results = search_items(
            s, kind="activity", query=query, vibes=vibes,
            max_price=None if max_price >= 2000 else max_price,
            max_distance=None if max_distance >= 90 else max_distance,
            min_rating=min_rating or None, family=family,
            duration_max=duration_choice or None, locale=locale,
        )
        if sort_by == "Note":
            results.sort(key=lambda x: (x.rating_avg or 0, x.review_count or 0), reverse=True)
        elif sort_by == "Prix":
            results.sort(key=lambda x: (x.price_from is None, x.price_from or 0))
        elif sort_by == "Distance":
            results.sort(key=lambda x: x.distance_center_km or 999)
        else:
            results.sort(key=lambda x: ((x.rating_avg or 0) * 1.2) + (2 if "culture" in (x.vibes or []) else 0), reverse=True)
        st.markdown(f"**{len(results)} expérience(s)** · prix et horaires de démonstration")
        if results:
            st.markdown('<div class="az-grid">' + "".join(item_card(i, locale) for i in results) + "</div>", unsafe_allow_html=True)
        else:
            empty_state("✦", t("no_results", locale), "Élargissez le budget, la distance ou choisissez une autre ambiance.")
        st.markdown(f'<div style="margin-top:26px"><a class="az-chip" href="{page_link("carte")}">Voir tout sur la carte →</a></div>', unsafe_allow_html=True)
    finally:
        s.close()


def render_restaurants(locale: str) -> None:
    s = get_session()
    try:
        slug = st.query_params.get("item")
        if slug:
            item = get_by_slug(s, slug)
            if item and item.kind == "restaurant":
                _render_restaurant_detail(s, item, locale)
                return
        page_heading(
            "Tables du Souss", t("restaurants_title", locale),
            "Marocain, fruits de mer, internationale ou végétarien : une sélection de démonstration à confirmer avec chaque établissement.",
            locale,
        )
        demo_note(locale)
        with st.form("restaurant_filters"):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                query = st.text_input(t("search", locale), placeholder="Tajine, poisson, café…")
            with c2:
                district = st.selectbox("Quartier", ["Tous", "Centre-ville", "Founty", "Corniche", "Médina", "Talborjt", "Port", "Marina", "Taghazout", "Tamraght", "Imsouane", "Aghroud", "Anza"])
            with c3:
                band = st.selectbox("Gamme", ["Toutes", "€", "€€", "€€€"])
            with c4:
                cuisine = st.selectbox("Cuisine", ["Toutes", "marocaine", "fruits de mer", "internationale", "végétarienne", "café", "espagnole"])
            st.form_submit_button(t("apply", locale), use_container_width=True, type="primary")
        items = search_items(s, kind="restaurant", query=query, locale=locale)
        filtered = []
        for item in items:
            detail = detail_for(s, item)
            if district != "Tous" and item.district != district:
                continue
            if band != "Toutes" and detail and detail.price_band != band:
                continue
            if cuisine != "Toutes" and detail and cuisine not in (detail.cuisines or []):
                continue
            filtered.append(item)
        filtered.sort(key=lambda x: (x.rating_avg or 0), reverse=True)
        st.markdown(f"**{len(filtered)} table(s)** · horaires et prix de démonstration")
        if filtered:
            st.markdown('<div class="az-grid">' + "".join(item_card(i, locale) for i in filtered) + "</div>", unsafe_allow_html=True)
        else:
            empty_state("◌", t("no_results", locale))
    finally:
        s.close()


def _render_restaurant_detail(s, item, locale: str) -> None:
    detail = detail_for(s, item)
    back_link("restaurants", "Retour aux restaurants")
    st.markdown(f'<div class="az-gallery">{gallery(item, locale)}</div>', unsafe_allow_html=True)
    facts = [
        ("Quartier", item.district or "—"),
        ("Cuisines", " · ".join(detail.cuisines or []) if detail else "—"),
        ("Gamme", detail.price_band if detail else "—"),
        ("Capacité", str(item.capacity or "—")),
        ("Options", " · ".join(detail.options or []) if detail else "—"),
        ("Distance", f"{item.distance_center_km:.0f} km" if item.distance_center_km is not None else "—"),
    ]
    st.markdown(f"""
    <div class="az-detail-hero">
      <div class="az-detail-art">{art_svg(item, 0, tall=True)}</div>
      <div class="az-detail-copy">
        <div class="az-chip-row"><span class="az-badge demo">DÉMO</span><span class="az-badge verified">✓ Avis vérifiés</span></div>
        <div class="az-card-kind">Restaurant · {esc(item.district or 'Agadir')}</div>
        <h1>{esc(localized(item.name, locale))}</h1>
        <div class="lead">{esc(localized(item.short_description, locale))}</div>
        <div class="az-rating-line"><span class="az-stars">{stars(item.rating_avg)}</span> <b>{item.rating_avg or 0:.1f}</b> · {item.review_count or 0} {t('reviews', locale)}</div>
        <div class="az-price" style="font-size:1.05rem">{esc(display_price(item, locale))}</div>
        <div class="az-facts">{"".join(f'<div class="az-fact"><span>{esc(k)}</span><b>{esc(v)}</b></div>' for k,v in facts)}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f'<div class="az-prose">{esc(localized(item.long_description, locale))}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f'<div class="az-note"><b>Horaires</b><br>{esc(_hours_text(detail, locale))}</div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="az-note"><b>Plats phares de démonstration</b><br>{esc(" · ".join(detail.signature_dishes or []))}</div>', unsafe_allow_html=True)

    st.markdown(section_head("Réservation de table", "Réservez votre table", "Choix de l'heure et du nombre de couverts."), unsafe_allow_html=True)
    variants = variants_for(s, item.id)
    if variants:
        variant = variants[0]
        slots = slots_for(s, variant.id, days=30)
        with st.form(f"restaurant_book_{item.id}"):
            c1, c2 = st.columns(2)
            with c1:
                covers = st.number_input(t("covers", locale), 1, 12, 2)
            with c2:
                if slots:
                    opts = {sl.id: slot_label(sl, locale) for sl in slots[:80]}
                    slot_id = st.selectbox(t("choose_time", locale), list(opts), format_func=lambda x: opts[x])
                else:
                    slot_id = None
                    st.info(t("no_slot", locale))
            pickup_id = pickup_select(s, locale, f"pickup_rest_{item.id}")
            st.caption("Les horaires réels et la disponibilité de la table sont confirmés par le restaurant.")
            submitted = st.form_submit_button(t("book", locale), use_container_width=True, type="primary")
            if submitted:
                slot = s.get(AvailabilitySlot, slot_id) if slot_id else None
                add_to_cart_and_go(
                    s, item, variant_id=variant.id, slot_id=slot_id, item_type="restaurant",
                    service_date=slot.start_at.date() if slot else None,
                    start_at=slot.start_at if slot else None,
                    adults=int(covers), children=0, quantity=1,
                    details={"pickup_catalog_id": pickup_id or None}, locale=locale,
                )

    st.markdown(section_head("Avis", "Les derniers avis", "Y compris les critiques."), unsafe_allow_html=True)
    from .common import item_reviews_block
    item_reviews_block(s, item, locale)


def _hours_text(detail, locale: str) -> str:
    if not detail or not detail.opening_hours:
        return "Horaires à confirmer."
    if detail.hours_status == "missing":
        return "Horaires à confirmer."
    hours = detail.opening_hours
    if isinstance(hours, dict):
        return "Déjeuner " + str(hours.get("lunch", "—")) + " · Dîner " + str(hours.get("dinner", "—")) + " (DÉMO)"
    return str(hours)


def render_accommodations(locale: str) -> None:
    s = get_session()
    try:
        slug = st.query_params.get("item")
        if slug:
            item = get_by_slug(s, slug)
            if item and item.kind == "accommodation":
                _render_accommodation_detail(s, item, locale)
                return
        page_heading(
            "Dormir", t("stays_title", locale),
            "Hôtels, riads, maisons d'hôtes et auberges à Agadir, Taghazout, Tamraght, Aghroud et Imsouane.",
            locale,
        )
        demo_note(locale)
        zones = sorted({i.zone for i in all_items(s, "accommodation") if i.zone})
        with st.form("acc_filters"):
            c1, c2, c3 = st.columns(3)
            with c1:
                zone = st.selectbox("Zone", ["Toutes"] + zones)
            with c2:
                typ = st.selectbox("Type", ["Tous", "hôtel", "riad", "maison d'hôtes", "auberge", "villa", "camp"])
            with c3:
                band = st.selectbox("Gamme", ["Toutes", "€", "€€", "€€€"])
            st.form_submit_button(t("apply", locale), use_container_width=True, type="primary")
        items = all_items(s, "accommodation")
        filtered = []
        for item in items:
            detail = detail_for(s, item)
            if zone != "Toutes" and item.zone != zone:
                continue
            if typ != "Tous" and detail and detail.accommodation_type != typ:
                continue
            if band != "Toutes" and detail and detail.price_band != band:
                continue
            filtered.append(item)
        filtered.sort(key=lambda x: (x.rating_avg or 0), reverse=True)
        st.markdown(f"**{len(filtered)} hébergement(s)** · tarifs de démonstration à confirmer")
        st.markdown('<div class="az-grid">' + "".join(item_card(i, locale) for i in filtered) + "</div>", unsafe_allow_html=True)
    finally:
        s.close()


def _render_accommodation_detail(s, item, locale: str) -> None:
    detail = detail_for(s, item)
    back_link("hebergements", "Retour aux hébergements")
    st.markdown(f'<div class="az-gallery">{gallery(item, locale)}</div>', unsafe_allow_html=True)
    facts = [
        ("Zone", item.zone or "—"), ("Type", detail.accommodation_type if detail else "—"),
        ("Gamme", detail.price_band if detail else "—"), ("Capacité", f"{item.capacity or '—'} personnes"),
        ("Arrivée", detail.checkin_time if detail else "À confirmer"),
        ("Départ", detail.checkout_time if detail else "À confirmer"),
    ]
    st.markdown(f"""
    <div class="az-detail-hero">
      <div class="az-detail-art">{art_svg(item, 1, tall=True)}</div>
      <div class="az-detail-copy">
        <div class="az-chip-row"><span class="az-badge demo">DÉMO</span><span class="az-badge verified">✓ Avis vérifiés</span></div>
        <div class="az-card-kind">Hébergement · {esc(item.zone or 'Agadir')}</div>
        <h1>{esc(localized(item.name, locale))}</h1>
        <div class="lead">{esc(localized(item.short_description, locale))}</div>
        <div class="az-rating-line"><span class="az-stars">{stars(item.rating_avg)}</span> <b>{item.rating_avg or 0:.1f}</b> · {item.review_count or 0} {t('reviews', locale)}</div>
        <div class="az-price" style="font-size:1.05rem">{esc(display_price(item, locale))}</div>
        <div class="az-facts">{"".join(f'<div class="az-fact"><span>{esc(k)}</span><b>{esc(v)}</b></div>' for k,v in facts)}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f'<div class="az-prose">{esc(localized(item.long_description, locale))}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="az-note"><b>Services</b><br>{esc(" · ".join(detail.amenities or [])) if detail else "À confirmer"}</div>', unsafe_allow_html=True)

    st.markdown(section_head("Réserver", "Composez votre nuitée", "Le tarif de démonstration est par chambre et par nuit."), unsafe_allow_html=True)
    variants = variants_for(s, item.id)
    if not variants:
        st.info("Aucune catégorie de chambre n'est disponible.")
        return
    with st.form(f"acc_book_{item.id}"):
        vlabels = {v.id: localized(v.name, locale) for v in variants}
        variant_id = st.selectbox("Catégorie", list(vlabels), format_func=lambda x: vlabels[x])
        variant = s.get(type(variants[0]), variant_id)
        slots = slots_for(s, variant.id, days=30)
        c1, c2 = st.columns(2)
        with c1:
            if slots:
                opts = {sl.id: slot_label(sl, locale) for sl in slots[:40]}
                slot_id = st.selectbox("Arrivée", list(opts), format_func=lambda x: opts[x])
                arrival = s.get(AvailabilitySlot, slot_id).start_at.date()
            else:
                slot_id = None
                arrival = st.date_input("Arrivée", value=date.today() + timedelta(days=7))
        with c2:
            departure = st.date_input("Départ", value=arrival + timedelta(days=2), min_value=arrival + timedelta(days=1))
        c3, c4, c5 = st.columns(3)
        with c3:
            rooms = st.number_input("Chambres", 1, max(1, int(variant.capacity_max or 1)), 1)
        with c4:
            adults = st.number_input(t("adults", locale), 1, 10, 2)
        with c5:
            children = st.number_input(t("kids", locale), 0, 6, 0)
        nights = max(1, (departure - arrival).days)
        st.caption(f"{nights} nuit(s) · {display_price(item, locale)} · disponibilité à confirmer")
        submitted = st.form_submit_button(t("add_cart", locale), use_container_width=True, type="primary")
        if submitted:
            add_to_cart_and_go(
                s, item, variant_id=variant.id, slot_id=slot_id, item_type="accommodation",
                service_date=arrival, start_at=datetime.combine(arrival, time(15, 0)),
                adults=int(adults), children=int(children), quantity=int(rooms),
                details={"nights": nights, "checkout": str(departure)}, locale=locale,
            )

    st.markdown(section_head("Avis", "La parole aux voyageurs"), unsafe_allow_html=True)
    from .common import item_reviews_block
    item_reviews_block(s, item, locale)


def render_transport(locale: str) -> None:
    s = get_session()
    try:
        slug = st.query_params.get("item")
        if slug:
            item = get_by_slug(s, slug)
            if item and item.kind == "transport":
                _render_transport_detail(s, item, locale)
                return
        page_heading(
            "Transport", t("transport_title", locale),
            "Tournées, taxi à la demande, forfaits demi-journée ou journée et transferts aéroport. Ramassage à l'hébergement.",
            locale,
        )
        demo_note(locale)
        with st.form("transport_filters"):
            c1, c2 = st.columns(2)
            with c1:
                query = st.text_input(t("search", locale), placeholder="Taghazout, aéroport, journée…")
            with c2:
                mode = st.selectbox("Type", ["Tous", "tour", "taxi", "transfer", "shuttle"],
                                    format_func=lambda x: {"Tous": "Tous", "tour": "Tournée", "taxi": "Taxi", "transfer": "Transfert", "shuttle": "Navette"}.get(x, x))
            st.form_submit_button(t("apply", locale), use_container_width=True, type="primary")
        items = search_items(s, kind="transport", query=query, locale=locale)
        filtered = []
        for item in items:
            detail = detail_for(s, item)
            if mode != "Tous" and detail and detail.mode != mode:
                continue
            filtered.append(item)
        st.markdown(f"**{len(filtered)} service(s)** · prix et horaires de démonstration")
        st.markdown('<div class="az-grid">' + "".join(item_card(i, locale) for i in filtered) + "</div>", unsafe_allow_html=True)
    finally:
        s.close()


def _render_transport_detail(s, item, locale: str) -> None:
    detail = detail_for(s, item)
    back_link("transport", "Retour au transport")
    st.markdown(f'<div class="az-gallery">{gallery(item, locale)}</div>', unsafe_allow_html=True)
    facts = [
        ("Départ", detail.origin if detail else "—"),
        ("Arrivée", detail.destination if detail else "—"),
        ("Durée", f"{detail.duration_minutes} min" if detail and detail.duration_minutes else "À confirmer"),
        ("Capacité", f"{item.capacity or '—'} personnes"),
        ("Bagages", detail.luggage if detail else "À confirmer"),
        ("Langues", " · ".join((detail.driver_languages or []) if detail else []).upper() or "À confirmer"),
    ]
    st.markdown(f"""
    <div class="az-detail-hero">
      <div class="az-detail-art">{art_svg(item, 1, tall=True)}</div>
      <div class="az-detail-copy">
        <div class="az-chip-row"><span class="az-badge demo">DÉMO</span><span class="az-badge verified">✓ Prestataire vérifié</span></div>
        <div class="az-card-kind">Transport · {esc(detail.mode if detail else 'service')}</div>
        <h1>{esc(localized(item.name, locale))}</h1>
        <div class="lead">{esc(localized(item.short_description, locale))}</div>
        <div class="az-price" style="font-size:1.05rem">{esc(display_price(item, locale))}</div>
        <div class="az-facts">{"".join(f'<div class="az-fact"><span>{esc(k)}</span><b>{esc(v)}</b></div>' for k,v in facts)}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f'<div class="az-prose">{esc(localized(item.long_description, locale))}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="az-note"><b>Annulation</b><br>{esc(localized(detail.cancellation_policy, locale) if detail else "Conditions à confirmer")}</div>', unsafe_allow_html=True)

    st.markdown(section_head("Réserver", "Votre trajet, de bout en bout", "Ramassage à l'hébergement, retour et heure confirmée la veille."), unsafe_allow_html=True)
    variants = variants_for(s, item.id)
    if not variants:
        st.info("Aucun véhicule réservable n'est renseigné.")
        return
    with st.form(f"transport_book_{item.id}"):
        vlabels = {v.id: localized(v.name, locale) for v in variants}
        variant_id = st.selectbox("Formule", list(vlabels), format_func=lambda x: vlabels[x])
        variant = s.get(type(variants[0]), variant_id)
        c1, c2, c3 = st.columns(3)
        with c1:
            travel_date = st.date_input("Date", value=date.today() + timedelta(days=2))
        with c2:
            travel_time = st.time_input("Heure", value=time(9, 0))
        with c3:
            pax = st.number_input("Voyageurs", 1, max(1, int(variant.capacity_max or 6)), 2)
        pickup_id = pickup_select(s, locale, f"pickup_trans_{item.id}")
        c4, c5 = st.columns(2)
        with c4:
            return_required = st.checkbox(t("return_trip", locale))
        with c5:
            st.caption(f"Tarif : {display_price(item, locale)}")
        submitted = st.form_submit_button(t("add_cart", locale), use_container_width=True, type="primary")
        if submitted:
            quantity = int(pax) if item.price_unit == "personne" else 1
            add_to_cart_and_go(
                s, item, variant_id=variant.id, item_type="transport",
                service_date=travel_date, start_at=datetime.combine(travel_date, travel_time),
                adults=int(pax), children=0, quantity=quantity,
                details={"pickup_catalog_id": pickup_id or None, "return_required": bool(return_required)},
                locale=locale,
            )

    st.markdown(section_head("Avis", "Voyager avec Azul"), unsafe_allow_html=True)
    from .common import item_reviews_block
    item_reviews_block(s, item, locale)


def render_map(locale: str) -> None:
    s = get_session()
    try:
        page_heading("Carte interactive", t("map_title", locale), t("map_hint", locale), locale)
        demo_note(locale)
        kinds = st.multiselect(
            "Afficher", ["activity", "restaurant", "accommodation", "spot", "transport"],
            default=["activity", "restaurant", "accommodation", "spot"],
            format_func=lambda k: kind_label(k, locale),
        )
        items = [i for i in all_items(s) if i.kind in kinds and i.lat is not None and i.lng is not None]
        try:
            import folium
            from streamlit_folium import st_folium
            colors = {"activity": "#D9663A", "restaurant": "#F5B700", "accommodation": "#0E6BA8",
                      "spot": "#14B8A6", "transport": "#4C7A4A"}
            m = folium.Map(location=[CENTER_LAT, CENTER_LNG], zoom_start=11, tiles="OpenStreetMap",
                           control_scale=True)
            folium.Marker(
                [CENTER_LAT, CENTER_LNG],
                popup="Centre d'Agadir",
                tooltip="Centre d'Agadir",
                icon=folium.Icon(color="darkblue", icon="info-sign"),
            ).add_to(m)
            for item in items:
                name = localized(item.name, locale)
                popup_html = (
                    f'<div style="font-family:Arial;min-width:190px"><b>{esc(name)}</b><br>'
                    f'<span style="color:#667085;font-size:12px">{esc(kind_label(item.kind, locale))} · '
                    f'{esc(item.district or item.zone or "Agadir")}</span><br>'
                    f'<a href="{item_link(item)}" target="_self">Voir la fiche Azul</a></div>'
                )
                folium.CircleMarker(
                    location=[item.lat, item.lng], radius=7,
                    color=colors.get(item.kind, "#0E6BA8"), fill=True,
                    fill_color=colors.get(item.kind, "#0E6BA8"), fill_opacity=.82,
                    popup=folium.Popup(popup_html, max_width=280),
                    tooltip=name,
                ).add_to(m)
            st_folium(m, width=1120, height=540, returned_objects=[])
        except Exception as exc:
            st.error(f"La carte n'a pas pu être affichée : {exc}")
            items = []

        st.markdown(section_head("Depuis le centre", "Temps de trajet estimés", "Estimations routières hors trafic, à vérifier sur place."), unsafe_allow_html=True)
        rows = []
        for item in items:
            if item.kind not in {"spot", "accommodation", "activity"}:
                continue
            rows.append({
                "Lieu": localized(item.name, locale),
                "Type": kind_label(item.kind, locale),
                "Distance": f"{distance_from_center(item.lat, item.lng) or 0:.1f} km",
                "Temps estimé": f"{travel_minutes(CENTER_LAT, CENTER_LNG, item.lat, item.lng)} min",
            })
        rows.sort(key=lambda r: float(r["Distance"].replace(" km", "")))
        if rows:
            st.dataframe(pd.DataFrame(rows[:16]), use_container_width=True, hide_index=True)
        st.caption("Aucune donnée de trafic en temps réel. Les temps sont des estimations Azul, pas une promesse horaire.")
    finally:
        s.close()


# import local pour éviter un import circulaire au chargement du module
from .components import item_link  # noqa: E402
