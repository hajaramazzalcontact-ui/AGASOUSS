"""Back-office protégé d'Azul AGADIR.

Le back-office est séparé du parcours visiteur et protégé par rôle. Les
opérations sensibles sont journalisées. Aucune donnée de carte bancaire n'est
stockée et aucun paiement n'est déclenché automatiquement.
"""
from __future__ import annotations

import json
from datetime import date, datetime, time, timedelta
from io import BytesIO

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import func, or_, select

from src.config import ADMIN_EMAIL, CANCELLATION_POLICY, IS_DEMO, UPLOAD_DIR
from src.db.base import utcnow
from src.db.models import (
    AuditLog,
    AvailabilitySlot,
    BackupLog,
    Booking,
    BookingItem,
    CatalogItem,
    CatalogMedia,
    Consent,
    Customer,
    Driver,
    LegalDocument,
    MessageTemplate,
    OutboxMessage,
    Payment,
    Provider,
    ProviderCommission,
    Review,
    ReviewSummary,
    Setting,
    TransportAssignment,
    TransportRun,
    User,
    Variant,
    Vehicle,
)
from src.db.session import get_session
from src.i18n import t
from src.ia.copywriter import generate_message
from src.ia.insights import daily_brief, detect_anomalies, summary_for_reviews
from src.services.analytics import (
    booking_funnel,
    dashboard_metrics,
    monthly_revenue,
    nationality_breakdown,
    provider_bookings,
    satisfaction_over_time,
    today_road_sheet,
    top_activities,
)
from src.services.auth import ROLE_LABELS, AuthError, authenticate, create_user, user_email
from src.services.booking import (
    cancel_booking,
    complete_booking,
    confirm_booking,
    mark_deposit_received,
)
from src.services.backups import create_backup
from src.services.catalog import all_items, detail_for, localized, money
from src.services.demo import reset_demo_database
from src.services.media import save_image
from src.services.messaging import approve_message, mark_sent, queue_message
from src.services.privacy import anonymize_customer, customer_export, withdraw_consent
from src.services.reviews import (
    manager_response_metrics,
    moderate_review,
    report_review,
    respond_to_review,
)
from src.services.security import (
    decrypt_text,
    encrypt_text,
    hash_identifier,
    mask_email,
    mask_phone,
)
from src.services.audit import log_action
from .common import page_heading
from .components import art_svg, empty_state, esc, fmt_date, money, page_link, rating_summary, status_badge

ADMIN_SECTIONS = [
    ("dashboard", "Tableau de bord"),
    ("catalogue", "Catalogue"),
    ("reservations", "Réservations"),
    ("clients", "Clients"),
    ("prestataires", "Prestataires"),
    ("transport", "Transport"),
    ("avis", "Avis"),
    ("analyses", "Analyses"),
    ("messages", "Messages"),
    ("reglages", "Réglages"),
]
PROVIDER_SECTIONS = {"dashboard", "catalogue", "reservations", "transport", "avis"}
DRIVER_SECTIONS = {"dashboard", "transport"}


def _session_user(s) -> User | None:
    uid = st.session_state.get("admin_user_id")
    user = s.get(User, uid) if uid else None
    if user and not user.is_active:
        return None
    return user


def _login(s, locale: str) -> None:
    st.markdown(f"""
    <div style="max-width:520px;margin:6vh auto 0 auto">
      <div class="az-brand"><span class="mark">AZUL</span><span class="sub">AGADIR</span></div>
      <div class="az-kicker" style="margin-top:20px">Espace professionnel</div>
      <h1 style="font-size:2.8rem;margin:0 0 6px">Reprendre la main.</h1>
      <p style="color:var(--azul-muted);font-size:.86rem">Tableau de bord, catalogue, réservations, avis et messages. Accès protégé et journalisé.</p>
    </div>
    """, unsafe_allow_html=True)
    with st.form("admin_login"):
        email = st.text_input(t("email", locale), placeholder="admin@azul.local")
        password = st.text_input(t("password", locale), type="password")
        submitted = st.form_submit_button(t("login", locale), type="primary", use_container_width=True)
        if submitted:
            try:
                user = authenticate(s, email, password)
                s.commit()
                st.session_state.admin_user_id = user.id
                st.session_state.page = "admin"
                st.rerun()
            except AuthError as exc:
                s.commit()
                st.error(str(exc))
    if IS_DEMO:
        st.info(t("demo_login", locale) + " · rôles : manager@azul.local, provider@azul.local, même mot de passe DÉMO.", icon="🔐")
    st.markdown(f'<p style="text-align:center;margin-top:18px"><a href="{page_link("accueil")}">← Retour au site visiteur</a></p>', unsafe_allow_html=True)


def _admin_header(user: User) -> None:
    sections = ADMIN_SECTIONS
    if user.role == "provider":
        sections = [s for s in sections if s[0] in PROVIDER_SECTIONS]
    elif user.role == "driver":
        sections = [s for s in sections if s[0] in DRIVER_SECTIONS]
    current = st.query_params.get("section", "dashboard")
    if current not in {s[0] for s in sections}:
        current = "dashboard"
    st.markdown(f"""
    <div class="az-admin-head">
      <div>
        <div class="az-brand"><span class="mark">AZUL</span><span class="sub">BACK OFFICE</span><span class="by">par AgadirGO</span></div>
        <div class="az-lesstext" style="margin-top:4px">{esc(user.full_name)} · {esc(ROLE_LABELS.get(user.role, user.role))} · {esc(user_email(user))}</div>
      </div>
      <div class="az-chip-row">
        <a class="az-chip" href="{page_link("accueil")}">← Site visiteur</a>
        <span class="az-chip active">DÉMO</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns([9, 1])
    with c2:
        if st.button("Déconnexion", use_container_width=True):
            st.session_state.admin_user_id = None
            st.session_state.page = "accueil"
            st.query_params["page"] = "accueil"
            st.rerun()
    nav = "".join(
        f'<a class="{"active" if key == current else ""}" href="{page_link("admin", section=key)}">{esc(label)}</a>'
        for key, label in sections
    )
    st.markdown(f'<div class="az-admin-nav">{nav}</div>', unsafe_allow_html=True)
    return current


def render_admin(locale: str) -> None:
    s = get_session()
    try:
        user = _session_user(s)
        if not user:
            _login(s, locale)
            return
        section = _admin_header(user)
        st.markdown(f'<div class="az-note" style="margin-bottom:16px">Mode démonstration : données fictives. Aucun envoi réel, aucun paiement réel, aucune donnée client réelle.</div>', unsafe_allow_html=True)
        dispatch = {
            "dashboard": _dashboard,
            "catalogue": _catalogue,
            "reservations": _reservations,
            "clients": _clients,
            "prestataires": _providers,
            "transport": _transport,
            "avis": _reviews,
            "analyses": _analytics,
            "messages": _messages,
            "reglages": _settings,
        }
        dispatch.get(section, _dashboard)(s, user, locale)
    finally:
        s.close()


def _metric(label: str, value: str, delta: str | None = None) -> None:
    st.metric(label, value, delta)


def _provider_item_ids(s, user: User) -> set[int]:
    if user.role != "provider" or not user.provider_id:
        return set()
    return {i.id for i in s.scalars(select(CatalogItem).where(CatalogItem.provider_id == user.provider_id)).all()}


def _provider_booking_ids(s, user: User) -> set[int]:
    if user.role != "provider" or not user.provider_id:
        return set()
    rows = s.execute(
        select(BookingItem.booking_id).join(CatalogItem, BookingItem.catalog_item_id == CatalogItem.id)
        .where(CatalogItem.provider_id == user.provider_id)
    ).all()
    return {row[0] for row in rows}


def _dashboard(s, user: User, locale: str) -> None:
    page_heading("Pilotage", "Bonjour, la ville est en mouvement.", "Réservations, revenus, satisfaction et points à traiter.", locale)
    metrics = dashboard_metrics(s)
    if user.role == "provider" and user.provider_id:
        own_items = list(provider_bookings(s, user.provider_id))
        own_bookings = {i.booking_id for i in own_items}
        revenue = sum((i.line_total or 0) for i in own_items)
        metrics = {**metrics, "confirmed": len(own_bookings), "revenue": round(revenue, 2), "average_basket": round(revenue / len(own_bookings), 2) if own_bookings else 0, "total_bookings": len(own_bookings)}
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _metric("Réservations aujourd'hui", str(metrics["today_bookings"]), "flux du jour")
    with c2:
        _metric("Revenu confirmé (DÉMO)", f"{metrics['revenue']:,.0f} MAD".replace(",", " "), "acomptes inclus")
    with c3:
        _metric("À traiter", str(metrics["pending"]), "demandes en attente")
    with c4:
        _metric("Note vérifiée", f"{metrics['rating']['average']}/5", f"{metrics['rating']['count']} avis")
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        _metric("Panier moyen", f"{metrics['average_basket']:,.0f} MAD".replace(",", " "))
    with c6:
        _metric("Acomptes à relancer", str(metrics["awaiting_deposit"]))
    with c7:
        _metric("Anomalies ouvertes", str(metrics["anomalies"]))
    with c8:
        _metric("Clients", str(len(s.scalars(select(Customer).where(Customer.anonymized_at.is_(None))).all())))

    st.markdown(f'<div class="az-note" style="margin:18px 0">✦ <b>Brief du jour.</b> {esc(daily_brief(s))}</div>', unsafe_allow_html=True)
    c1, c2 = st.columns([1.25, 1])
    with c1:
        st.markdown("### Réservations récentes")
        bookings = list(s.scalars(select(Booking).order_by(Booking.created_at.desc()).limit(8)).all())
        rows = [{
            "Référence": b.reference,
            "Client": f"{b.customer.first_name} {b.customer.last_name[:1]}." if b.customer else "—",
            "Statut": b.status,
            "Total": b.total_amount or 0,
            "Score": b.score or 0,
            "Créée": fmt_date(b.created_at, locale),
        } for b in bookings]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    with c2:
        st.markdown("### Activités les plus demandées")
        top = top_activities(s)
        if not top.empty:
            fig = px.bar(top.head(7), x="réservations", y="activité", orientation="h", color="type",
                         color_discrete_sequence=["#0E6BA8", "#14B8A6", "#D9663A", "#F5B700", "#4C7A4A"])
            fig.update_layout(height=270, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.caption("Pas encore de données.")

    st.markdown("### Chiffre d'affaires et flux")
    c1, c2 = st.columns(2)
    with c1:
        rev = monthly_revenue(s)
        if not rev.empty:
            fig = px.bar(rev, x="mois", y="montant", color_discrete_sequence=["#0E6BA8"])
            fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        funnel = booking_funnel(s)
        fig = px.bar(funnel, x="statut", y="nombre", color_discrete_sequence=["#14B8A6"])
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    anomalies = list(s.scalars(select(Anomaly).where(Anomaly.status == "open").order_by(Anomaly.detected_at.desc())).all()) if False else []
    # éviter un import inutile dans plusieurs pages : l'anomalie est affichée depuis les réglages/analyses.


def _catalogue(s, user: User, locale: str) -> None:
    page_heading("Catalogue", "Une fiche juste, un prix assumé.", "Créez, publiez et vérifiez les informations. Un prix manquant n'est jamais remplacé par une invention.", locale)
    own_ids = _provider_item_ids(s, user)
    tabs = st.tabs(["Fiches", "Nouvelle activité", "Disponibilités", "Médias"])
    with tabs[0]:
        kind = st.selectbox("Type de catalogue", ["activity", "restaurant", "accommodation", "spot", "transport"],
                            format_func=lambda k: {"activity": "Activités", "restaurant": "Restaurants", "accommodation": "Hébergements", "spot": "Spots", "transport": "Transport"}[k])
        items = [i for i in all_items(s, kind) if not own_ids or i.id in own_ids]
        st.caption(f"{len(items)} fiche(s) · statut et prix modifiables")
        if items:
            st.dataframe(pd.DataFrame([{
                "ID": i.id, "Nom": localized(i.name, "fr"), "Zone": i.zone or i.district or "—",
                "Prix": i.price_from, "Prix statut": i.price_status, "Réservation": i.booking_mode,
                "Note": i.rating_avg, "Avis": i.review_count, "Statut": i.status,
            } for i in items]), use_container_width=True, hide_index=True)
            item_id = st.selectbox("Modifier une fiche", [i.id for i in items], format_func=lambda x: next(f"{i.id} · {localized(i.name, 'fr')}" for i in items if i.id == x))
            item = s.get(CatalogItem, item_id)
            with st.form(f"edit_item_{item.id}"):
                c1, c2 = st.columns(2)
                with c1:
                    name_fr = st.text_input("Nom (FR)", value=localized(item.name, "fr"))
                    tagline = st.text_input("Accroche (FR)", value=localized(item.tagline, "fr"))
                    city = st.text_input("Quartier / zone", value=item.district or item.zone or "")
                    status = st.selectbox("Statut", ["published", "draft", "archived"], index=["published", "draft", "archived"].index(item.status) if item.status in ["published", "draft", "archived"] else 0)
                with c2:
                    price = st.number_input("Prix à partir de (MAD, 0 = non renseigné)", min_value=0.0, value=float(item.price_from or 0), step=50.0)
                    price_status = st.selectbox("Statut du prix", ["missing", "demo", "confirmed"], index=["missing", "demo", "confirmed"].index(item.price_status) if item.price_status in ["missing", "demo", "confirmed"] else 0)
                    price_unit = st.selectbox("Unité de prix", ["personne", "nuit", "véhicule", "course"], index=["personne", "nuit", "véhicule", "course"].index(item.price_unit) if item.price_unit in ["personne", "nuit", "véhicule", "course"] else 0)
                    booking_mode = st.selectbox("Mode de réservation", ["request", "instant", "info"], index=["request", "instant", "info"].index(item.booking_mode) if item.booking_mode in ["request", "instant", "info"] else 0)
                    capacity = st.number_input("Capacité", 0, 500, int(item.capacity or 0))
                short = st.text_area("Description courte (FR)", value=localized(item.short_description, "fr"))
                long = st.text_area("Description longue (FR)", value=localized(item.long_description, "fr"), height=100)
                vibes = st.multiselect("Ambiances", ["aventure", "famille", "culture", "nature", "mer", "gastronomie", "detente", "jeux"], default=item.vibes or [])
                c3, c4 = st.columns(2)
                with c3:
                    lat = st.number_input("Latitude", value=float(item.lat or 30.4278), format="%.5f")
                with c4:
                    lng = st.number_input("Longitude", value=float(item.lng or -9.5981), format="%.5f")
                submit = st.form_submit_button("Enregistrer la fiche", type="primary", use_container_width=True)
                if submit:
                    if booking_mode == "instant" and not price:
                        st.error("Un mode instantané exige un prix confirmé. La fiche n'a pas été modifiée.")
                    else:
                        names = dict(item.name or {})
                        names["fr"] = name_fr.strip()
                        item.name = names
                        item.tagline = {**(item.tagline or {}), "fr": tagline}
                        item.short_description = {**(item.short_description or {}), "fr": short}
                        item.long_description = {**(item.long_description or {}), "fr": long}
                        item.price_from = price or None
                        item.price_status = price_status if price else "missing"
                        item.price_unit = price_unit
                        item.booking_mode = booking_mode
                        item.capacity = capacity or None
                        item.status = status
                        item.district = city or item.district
                        item.zone = city or item.zone
                        item.lat = lat
                        item.lng = lng
                        item.vibes = vibes
                        item.price_updated_at = utcnow() if price else item.price_updated_at
                        item.is_demo = True
                        log_action(s, user.id, "edit_catalog_item", "catalog", item.id, {"price": price, "status": status})
                        s.commit()
                        st.success("Fiche enregistrée.")
                        st.rerun()
    with tabs[1]:
        if user.role == "provider":
            st.caption("La création est réservée à l'administration Azul.")
        else:
            with st.form("new_activity"):
                st.markdown("#### Nouvelle activité")
                c1, c2 = st.columns(2)
                with c1:
                    new_name = st.text_input("Nom (FR)")
                    new_slug = st.text_input("Identifiant URL", placeholder="mon-activite")
                with c2:
                    new_price = st.number_input("Prix DÉMO (MAD)", 0.0, 20000.0, 250.0, step=50.0)
                    new_capacity = st.number_input("Capacité", 1, 200, 10)
                    provider_ids = [p.id for p in s.scalars(select(Provider).order_by(Provider.name)).all()]
                    provider_id = st.selectbox("Prestataire", [None] + provider_ids,
                                               format_func=lambda x: "— Interne —" if x is None else s.get(Provider, x).name)
                new_short = st.text_input("Description courte")
                new_long = st.text_area("Description longue", height=80)
                submit_new = st.form_submit_button("Créer l'activité", type="primary", use_container_width=True)
                if submit_new:
                    if not new_name or not new_slug:
                        st.error("Nom et identifiant sont obligatoires.")
                    elif s.scalar(select(CatalogItem).where(CatalogItem.slug == new_slug)):
                        st.error("Cet identifiant existe déjà.")
                    else:
                        item = CatalogItem(
                            kind="activity", slug=new_slug.strip(), name={"fr": new_name.strip()},
                            tagline={"fr": new_short}, short_description={"fr": new_short},
                            long_description={"fr": new_long}, status="draft", provider_id=provider_id,
                            price_from=new_price or None, price_status="demo" if new_price else "missing",
                            price_unit="personne", booking_mode="request", capacity=new_capacity,
                            district="Agadir", zone="Agadir", lat=30.4278, lng=-9.5981,
                            languages=["fr", "en", "ar", "es"], is_demo=True, created_by=user.id,
                        )
                        s.add(item)
                        s.flush()
                        s.add(ActivityDetail(catalog_id=item.id, duration_minutes=120, audience=["famille", "adultes"],
                                             effort_level="modéré", what_to_bring={"fr": "À confirmer"},
                                             weather_notes={"fr": "À confirmer"}, safety_notes={"fr": "À confirmer"},
                                             best_season={"fr": "À confirmer"}, includes=[]))
                        s.add(Variant(catalog_id=item.id, code="standard", name={"fr": "Formule standard"},
                                      capacity_min=1, capacity_max=new_capacity, duration_minutes=120,
                                      price=new_price or None, price_status="demo" if new_price else "missing"))
                        log_action(s, user.id, "create_catalog_item", "catalog", item.id, {"name": new_name})
                        s.commit()
                        st.success("Activité créée en brouillon. Ajoutez les détails avant publication.")
                        st.rerun()
    with tabs[2]:
        st.markdown("#### Ajouter un créneau")
        all_kind_items = [i for i in all_items(s) if not own_ids or i.id in own_ids]
        if all_kind_items:
            item_id = st.selectbox("Fiche", [i.id for i in all_kind_items], format_func=lambda x: next(f"{localized(i.name, 'fr')} · {i.kind}" for i in all_kind_items if i.id == x), key="slot_item")
            variants = list(s.scalars(select(Variant).where(Variant.catalog_id == item_id)).all())
            if variants:
                with st.form("new_slot"):
                    variant_id = st.selectbox("Formule", [v.id for v in variants], format_func=lambda x: next(localized(v.name, "fr") for v in variants if v.id == x))
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        slot_date = st.date_input("Date", value=date.today() + timedelta(days=2))
                    with c2:
                        slot_time = st.time_input("Heure", value=time(10, 0))
                    with c3:
                        slot_capacity = st.number_input("Capacité", 1, 200, 10)
                    duration = st.number_input("Durée (minutes)", 15, 720, 120, step=15)
                    if st.form_submit_button("Créer le créneau", type="primary"):
                        start = datetime.combine(slot_date, slot_time)
                        if s.scalar(select(AvailabilitySlot).where(AvailabilitySlot.variant_id == variant_id, AvailabilitySlot.start_at == start)):
                            st.error("Ce créneau existe déjà.")
                        else:
                            s.add(AvailabilitySlot(variant_id=variant_id, start_at=start,
                                                   end_at=start + timedelta(minutes=int(duration)),
                                                   capacity=int(slot_capacity), booked_count=0, status="open",
                                                   source="manager", is_demo=True))
                            log_action(s, user.id, "create_slot", "slot", variant_id)
                            s.commit()
                            st.success("Créneau ajouté.")
                            st.rerun()
                soon = list(s.scalars(select(AvailabilitySlot).where(AvailabilitySlot.variant_id.in_([v.id for v in variants]), AvailabilitySlot.start_at >= datetime.now()).order_by(AvailabilitySlot.start_at).limit(20)).all())
                if soon:
                    st.dataframe(pd.DataFrame([{
                        "Date": sl.start_at.strftime("%d/%m/%Y %H:%M"), "Capacité": sl.capacity,
                        "Réservé": sl.booked_count, "Reste": sl.remaining, "Statut": sl.status,
                    } for sl in soon]), use_container_width=True, hide_index=True)
    with tabs[3]:
        st.markdown("#### Médias et droits")
        st.caption("La source, le crédit et la base de droits sont obligatoires. Un visuel sans droits ne peut pas être publié.")
        media_items = [i for i in all_items(s) if not own_ids or i.id in own_ids]
        if media_items:
            item_id = st.selectbox("Fiche", [i.id for i in media_items], format_func=lambda x: next(localized(i.name, "fr") for i in media_items if i.id == x), key="media_item")
            item = s.get(CatalogItem, item_id)
            st.markdown(f'<div style="max-width:340px;border-radius:18px;overflow:hidden">{art_svg(item, 1)}</div>', unsafe_allow_html=True)
            upload = st.file_uploader("Ajouter une image", type=["jpg", "jpeg", "png", "webp"])
            c1, c2 = st.columns(2)
            with c1:
                rights = st.selectbox("Base de droits", ["owner", "written_consent", "license", "demo"],
                                      format_func=lambda x: {"owner": "Photo possédée", "written_consent": "Autorisation écrite", "license": "Licence", "demo": "Visuel de démonstration"}[x])
                credit = st.text_input("Crédit obligatoire", value="Azul AGADIR")
                caption = st.text_input("Légende")
            with c2:
                source_url = st.text_input("Référence licence / autorisation")
                license_name = st.text_input("Nom de la licence", value="Démonstration")
                is_cover = st.checkbox("Image de couverture")
            if st.button("Téléverser et enregistrer", type="primary") and upload:
                try:
                    path = save_image(
                        upload.getvalue(), upload.name, catalog_id=item.id,
                        rights_basis=rights, credit=credit, source_url=source_url,
                        caption=caption, sort_order=len(item.media or []), is_cover=is_cover,
                    )
                    from src.config import BASE_DIR
                    rel = str(path.relative_to(BASE_DIR))
                    thumb = path.with_name(path.stem + "-thumb" + path.suffix)
                    s.add(CatalogMedia(
                        catalog_id=item.id, kind="image", storage_path=rel,
                        thumbnail_path=str(thumb.relative_to(BASE_DIR)),
                        caption={"fr": caption}, credit=credit, source_url=source_url,
                        rights_basis=rights, license_name=license_name,
                        consent_at=utcnow() if rights == "written_consent" else None,
                        is_cover=is_cover, is_demo=rights == "demo",
                    ))
                    log_action(s, user.id, "upload_media", "catalog", item.id, {"rights": rights})
                    s.commit()
                    st.success("Média enregistré avec ses droits.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))


def _reservations(s, user: User, locale: str) -> None:
    page_heading("Réservations", "Chaque demande a une histoire.", "File d'attente, confirmation humaine, acompte, prestation terminée et avis.", locale)
    allowed_ids = _provider_booking_ids(s, user)
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        status_filter = st.selectbox("Statut", ["Tous", "pending", "confirmed", "deposit_received", "completed", "cancelled"])
    with c2:
        search = st.text_input("Référence")
    with c3:
        st.caption("Le score de priorité est explicable et n'annule jamais la décision humaine.")
    stmt = select(Booking).order_by(Booking.created_at.desc())
    if status_filter != "Tous":
        stmt = stmt.where(Booking.status == status_filter)
    if search:
        stmt = stmt.where(Booking.reference.ilike(f"%{search}%"))
    bookings = list(s.scalars(stmt).all())
    if user.role == "provider":
        bookings = [b for b in bookings if b.id in allowed_ids]
    if not bookings:
        empty_state("◌", "Aucune réservation", "Modifiez les filtres.")
        return
    st.dataframe(pd.DataFrame([{
        "Référence": b.reference, "Client": f"{b.customer.first_name} {b.customer.last_name}" if b.customer else "—",
        "Statut": b.status, "Total": b.total_amount or 0, "Score": b.score or 0, "Créée": fmt_date(b.created_at, locale),
    } for b in bookings]), use_container_width=True, hide_index=True)
    booking_id = st.selectbox("Ouvrir une réservation", [b.id for b in bookings],
                              format_func=lambda x: next(f"{b.reference} · {b.customer.first_name if b.customer else '—'} · {b.status}" for b in bookings if b.id == x))
    booking = s.get(Booking, booking_id)
    if not booking:
        return
    st.markdown(f"### {booking.reference} · {status_badge(booking.status)}", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"**Client**  \n{booking.customer.first_name} {booking.customer.last_name}  \n{booking.customer.country or '—'}")
    with c2:
        st.markdown(f"**Total connu**  \n{money(booking.total_amount)}  \nAcompte : {money(booking.deposit_amount)}")
    with c3:
        st.markdown(f"**Score**  \n{booking.score}/100  \n{booking.source or '—'}")
    st.markdown(f'<div class="az-note">{esc(booking.score_explanation or "")}</div>', unsafe_allow_html=True)
    st.markdown("#### Prestations")
    st.dataframe(pd.DataFrame([{
        "Fiche": localized(i.catalog.name, "fr") if i.catalog else "—",
        "Date": fmt_date(i.service_date, locale), "Adultes": i.adults, "Enfants": i.children,
        "Prix unitaire": i.unit_price, "Total ligne": i.line_total, "Statut": i.status,
    } for i in booking.items]), use_container_width=True, hide_index=True)
    st.markdown("#### Actions humaines")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Confirmer la réservation", type="primary", use_container_width=True, key=f"confirm_{booking.id}"):
            try:
                confirm_booking(s, booking.id, user.id)
                s.commit()
                st.success("Réservation confirmée. Billet émis.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    with c2:
        if st.button("Marquer l'acompte reçu", use_container_width=True, key=f"deposit_{booking.id}"):
            try:
                mark_deposit_received(s, booking.id, user.id)
                s.commit()
                st.success("Acompte saisi manuellement.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    with c3:
        if st.button("Marquer la prestation terminée", use_container_width=True, key=f"complete_{booking.id}"):
            complete_booking(s, booking.id, user.id)
            s.commit()
            st.success("Prestation terminée. Invitation à laisser un avis programmée.")
            st.rerun()
    with st.expander("Annuler avec un motif"):
        reason = st.text_area("Motif d'annulation", key=f"cancel_reason_{booking.id}")
        if st.button("Annuler la réservation", type="secondary", key=f"cancel_{booking.id}"):
            if not reason.strip():
                st.error("Un motif est obligatoire.")
            else:
                cancel_booking(s, booking.id, reason, user.id)
                s.commit()
                st.success("Réservation annulée, capacité libérée.")
                st.rerun()
    with st.expander("Préparer un message (validation humaine obligatoire)"):
        kind = st.selectbox("Type", ["confirmation", "rappel", "demande_avis", "relance_acompte"], key=f"msg_kind_{booking.id}")
        if st.button("Générer un brouillon", key=f"gen_msg_{booking.id}"):
            from src.services.security import decrypt_text
            body = generate_message(kind, booking.customer, booking, locale)
            recipient = decrypt_text(booking.customer.email_enc) or decrypt_text(booking.customer.phone_enc)
            msg = queue_message(
                s, customer=booking.customer, channel="email" if kind != "rappel" else "whatsapp",
                subject=f"Azul AGADIR · {booking.reference}", body=body,
                booking_id=booking.id, template_code=kind,
            )
            log_action(s, user.id, "queue_message", "booking", booking.id, {"kind": kind})
            s.commit()
            st.success("Brouillon ajouté à la boîte d'envoi. Aucun envoi automatique.")
            st.text_area("Aperçu", body, height=120, key=f"preview_{booking.id}")
    with st.expander("Paiements et journal"):
        for payment in booking.payments:
            st.markdown(f"- {payment.payment_type} · {money(payment.amount)} · **{payment.status}** · {payment.method}")
        for history in booking.history:
            st.caption(f"{history.created_at} · {history.from_status or '—'} → {history.to_status} · {history.note or ''}")


def _clients(s, user: User, locale: str) -> None:
    if user.role not in {"admin", "manager"}:
        st.error("Accès réservé à l'administration et à la gestion.")
        return
    page_heading("Clients", "La confiance se cultive.", "Coordonnées chiffrées, consentements, export et anonymisation.", locale)
    customers = list(s.scalars(select(Customer).where(Customer.anonymized_at.is_(None)).order_by(Customer.created_at.desc())).all())
    st.dataframe(pd.DataFrame([{
        "ID": c.id, "Prénom": c.first_name, "Nom": c.last_name, "Pays": c.country or "—",
        "Email": mask_email(decrypt_text(c.email_enc)), "Téléphone": mask_phone(decrypt_text(c.phone_enc)),
        "Séjour": f"{c.stay_start or '—'} → {c.stay_end or '—'}", "Langue": c.locale,
    } for c in customers]), use_container_width=True, hide_index=True)
    if not customers:
        return
    cid = st.selectbox("Ouvrir un client", [c.id for c in customers], format_func=lambda x: next(f"{c.first_name} {c.last_name} · {c.country}" for c in customers if c.id == x))
    customer = s.get(Customer, cid)
    reveal = st.checkbox("Afficher les coordonnées complètes (action journalisée)")
    if reveal:
        log_action(s, user.id, "reveal_customer_contact", "customer", customer.id)
        s.commit()
        st.markdown(f"Email : **{decrypt_text(customer.email_enc) or '—'}** · Téléphone : **{decrypt_text(customer.phone_enc) or '—'}**")
    c1, c2, c3 = st.columns(3)
    with c1:
        _metric("Réservations", str(len(customer.bookings)))
    with c2:
        _metric("Avis", str(len(s.scalars(select(Review).where(Review.customer_id == customer.id)).all())))
    with c3:
        _metric("Langue", customer.locale.upper())
    consents = list(s.scalars(select(Consent).where(Consent.customer_id == customer.id)).all())
    st.markdown("#### Consentements")
    for consent in consents:
        st.caption(f"{consent.purpose} · accordé={consent.granted} · {consent.granted_at} · retiré={consent.revoked_at or '—'}")
        if consent.granted and not consent.revoked_at and st.button(f"Retirer le consentement {consent.purpose}", key=f"withdraw_{consent.id}"):
            withdraw_consent(s, customer.id, consent.purpose)
            log_action(s, user.id, "withdraw_consent", "customer", customer.id, {"purpose": consent.purpose})
            s.commit()
            st.rerun()
    export = customer_export(s, customer.id)
    st.download_button("Exporter les données (JSON)", json.dumps(export, ensure_ascii=False, indent=2),
                       file_name=f"azul-client-{customer.id}.json", mime="application/json")
    st.markdown("#### Réservations")
    for booking in customer.bookings:
        st.markdown(f"- **{booking.reference}** · {status_badge(booking.status)} · {money(booking.total_amount)}", unsafe_allow_html=True)
    st.markdown("#### Anonymisation (loi 09-08)")
    st.caption("L'anonymisation supprime les coordonnées et conserve les obligations comptables. Elle est irréversible.")
    confirm = st.checkbox("Je confirme la demande d'effacement.", key=f"anon_{customer.id}")
    if confirm and st.button("Anonymiser ce client", type="secondary"):
        anonymize_customer(s, customer.id, user.id)
        s.commit()
        st.success("Client anonymisé.")
        st.rerun()


def _providers(s, user: User, locale: str) -> None:
    if user.role not in {"admin", "manager"}:
        st.error("Accès réservé à l'administration et à la gestion.")
        return
    page_heading("Prestataires", "Des partenaires, pas des boîtes noires.", "Contrats, commissions, fiches et vérification.", locale)
    providers = list(s.scalars(select(Provider).order_by(Provider.name)).all())
    st.dataframe(pd.DataFrame([{
        "ID": p.id, "Nom": p.name, "Type": p.kind, "Commission %": p.commission_rate,
        "Contrat": p.contract_ref or "—", "Vérifié": "Oui" if p.is_verified else "Non",
        "Fiches": len(p.items),
    } for p in providers]), use_container_width=True, hide_index=True)
    if providers:
        pid = st.selectbox("Ouvrir un prestataire", [p.id for p in providers], format_func=lambda x: next(p.name for p in providers if p.id == x))
        provider = s.get(Provider, pid)
        with st.form(f"provider_{provider.id}"):
            c1, c2 = st.columns(2)
            with c1:
                commission = st.number_input("Commission (%)", 0.0, 60.0, float(provider.commission_rate or 0))
                contract = st.text_input("Référence contrat", value=provider.contract_ref or "")
            with c2:
                verified = st.checkbox("Prestataire vérifié", value=bool(provider.is_verified))
                notes = st.text_area("Notes internes", value=provider.notes or "")
            if st.form_submit_button("Enregistrer", type="primary"):
                provider.commission_rate = commission
                provider.contract_ref = contract
                provider.is_verified = verified
                provider.notes = notes
                log_action(s, user.id, "edit_provider", "provider", provider.id)
                s.commit()
                st.success("Prestataire mis à jour.")
                st.rerun()
        st.markdown("#### Portefeuille")
        st.dataframe(pd.DataFrame([{
            "Fiche": localized(i.name, "fr"), "Type": i.kind, "Prix": i.price_from,
            "Note": i.rating_avg, "Statut": i.status,
        } for i in provider.items]), use_container_width=True, hide_index=True)
    with st.expander("Créer un prestataire"):
        with st.form("new_provider"):
            name = st.text_input("Nom")
            kind = st.selectbox("Type", ["activité", "restaurant", "hébergement", "transport", "nature", "culture"])
            contact = st.text_input("Contact")
            email = st.text_input("Email")
            phone = st.text_input("Téléphone")
            commission = st.number_input("Commission %", 0.0, 60.0, 15.0)
            if st.form_submit_button("Créer", type="primary"):
                p = Provider(name=name, kind=kind, contact_name=contact, email_enc=encrypt_text(email),
                             phone_enc=encrypt_text(phone), commission_rate=commission, is_demo=True)
                s.add(p)
                s.flush()
                log_action(s, user.id, "create_provider", "provider", p.id)
                s.commit()
                st.success("Prestataire créé.")
                st.rerun()


def _reviews(s, user: User, locale: str) -> None:
    page_heading("Avis", "La note appartient aux voyageurs.", "Impossible de créer ou modifier un avis. Répondre oui, modérer seulement avec un motif.", locale)
    own_ids = _provider_item_ids(s, user)
    reviews = list(s.scalars(select(Review).order_by(Review.created_at.desc())).all())
    if user.role == "provider":
        reviews = [r for r in reviews if r.catalog_item_id in own_ids]
    c1, c2, c3 = st.columns(3)
    with c1:
        rating_filter = st.selectbox("Note", ["Toutes", 5, 4, 3, 2, 1])
    with c2:
        status_filter = st.selectbox("Statut", ["Tous", "published", "hidden"])
    with c3:
        response_filter = st.selectbox("Réponse", ["Toutes", "Sans réponse", "Avec réponse"])
    filtered = [r for r in reviews
                if (rating_filter == "Toutes" or r.rating == rating_filter)
                and (status_filter == "Tous" or r.status == status_filter)
                and (response_filter == "Toutes" or (response_filter == "Sans réponse" and not r.manager_response) or (response_filter == "Avec réponse" and r.manager_response))]
    st.markdown(rating_summary(filtered, locale), unsafe_allow_html=True)
    st.dataframe(pd.DataFrame([{
        "ID": r.id, "Fiche": localized(r.catalog.name, "fr") if r.catalog else "—",
        "Note": r.rating, "Avis": (r.comment or "")[:70], "Statut": r.status,
        "Réponse": "Oui" if r.manager_response else "Non", "Vérifié": "Oui" if r.verified else "Non",
    } for r in filtered]), use_container_width=True, hide_index=True)
    if not filtered:
        return
    rid = st.selectbox("Ouvrir un avis", [r.id for r in filtered], format_func=lambda x: next(f"{r.id} · {r.rating}/5 · {(r.comment or '')[:50]}" for r in filtered if r.id == x))
    review = s.get(Review, rid)
    st.markdown(f"### {review.rating}/5 · {localized(review.catalog.name, 'fr')} · {review.created_at}", unsafe_allow_html=True)
    st.markdown(f"> {review.comment}")
    c1, c2 = st.columns(2)
    with c1:
        st.caption(f"Langue : {review.language} · vérifié : {review.verified} · statut : {review.status} · démo : {review.is_demo}")
    with c2:
        st.caption(f"Réponse : {review.manager_response or '—'}")
    with st.form(f"response_{review.id}"):
        response = st.text_area("Réponse publique du gérant", value=review.manager_response or "")
        if st.form_submit_button("Publier la réponse", type="primary"):
            respond_to_review(s, review.id, response, user.id)
            s.commit()
            st.success("Réponse publiée.")
            st.rerun()
    with st.expander("Modération motivée"):
        st.caption("La note et le texte ne peuvent pas être modifiés. Masquer un avis exige un motif conservé au journal.")
        reason = st.text_area("Motif", key=f"mod_reason_{review.id}")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Masquer l'avis", type="secondary", key=f"hide_{review.id}"):
                try:
                    moderate_review(s, review.id, hidden=True, reason=reason, actor_id=user.id)
                    s.commit()
                    st.success("Avis masqué et motif journalisé.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
        with c2:
            if st.button("Republier", key=f"publish_{review.id}"):
                moderate_review(s, review.id, hidden=False, reason=reason or "Republication motivée", actor_id=user.id)
                s.commit()
                st.success("Avis republié.")
                st.rerun()
    with st.expander("Résumé d'aide à la lecture (IA, non publié automatiquement)"):
        if st.button("Générer un résumé ancré", key=f"summary_{review.id}"):
            text = summary_for_reviews(s, review.catalog_item_id)
            st.session_state[f"summary_text_{review.id}"] = text
        if st.session_state.get(f"summary_text_{review.id}"):
            st.info(st.session_state[f"summary_text_{review.id}"])
            st.caption("Résumé extractif à valider. Il ne modifie ni la note ni les avis.")


def _analytics(s, user: User, locale: str) -> None:
    if user.role not in {"admin", "manager"}:
        st.error("Accès réservé à l'administration et à la gestion.")
        return
    page_heading("Analyses", "Décider avec des faits.", "Volumes, revenus, nationalités, satisfaction et conversion. Données de démonstration.", locale)
    metrics = dashboard_metrics(s)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _metric("Total réservations", str(metrics["total_bookings"]))
    with c2:
        _metric("Revenu confirmé", f"{metrics['revenue']:,.0f} MAD".replace(",", " "))
    with c3:
        _metric("Panier moyen", f"{metrics['average_basket']:,.0f} MAD".replace(",", " "))
    with c4:
        _metric("Satisfaction", f"{metrics['rating']['average']}/5")
    c1, c2 = st.columns(2)
    with c1:
        rev = monthly_revenue(s)
        if not rev.empty:
            st.plotly_chart(px.line(rev, x="mois", y="montant", markers=True, color_discrete_sequence=["#0E6BA8"]).update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"), use_container_width=True)
    with c2:
        nat = nationality_breakdown(s)
        if not nat.empty:
            st.plotly_chart(px.pie(nat, names="pays", values="clients", color_discrete_sequence=px.colors.qualitative.Set2).update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)"), use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        sat = satisfaction_over_time(s)
        if not sat.empty:
            st.plotly_chart(px.bar(sat, x="mois", y="note", color_discrete_sequence=["#14B8A6"]).update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"), use_container_width=True)
    with c2:
        top = top_activities(s)
        if not top.empty:
            st.plotly_chart(px.bar(top, x="réservations", y="activité", orientation="h", color_discrete_sequence=["#D9663A"]).update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)"), use_container_width=True)
    st.markdown("#### Anomalies détectées")
    if st.button("Relancer les contrôles"):
        created = detect_anomalies(s)
        s.commit()
        st.success(f"{len(created)} nouvelle(s) anomalie(s).")
    from src.db.models import Anomaly
    anomalies = list(s.scalars(select(Anomaly).order_by(Anomaly.detected_at.desc()).limit(12)).all())
    if anomalies:
        st.dataframe(pd.DataFrame([{
            "Type": a.anomaly_type, "Gravité": a.severity, "Entité": f"{a.entity_type}:{a.entity_id}",
            "Statut": a.status, "Détectée": fmt_date(a.detected_at, locale),
        } for a in anomalies]), use_container_width=True, hide_index=True)


def _messages(s, user: User, locale: str) -> None:
    if user.role not in {"admin", "manager"}:
        st.error("Accès réservé à l'administration et à la gestion.")
        return
    page_heading("Messages", "Préparer, valider, envoyer.", "Aucun message ne part sans validation humaine. Aucun envoi réel n'est activé en démonstration.", locale)
    tabs = st.tabs(["Modèles", "Boîte d'envoi", "Générer"])
    with tabs[0]:
        templates = list(s.scalars(select(MessageTemplate).order_by(MessageTemplate.code)).all())
        if templates:
            tid = st.selectbox("Modèle", [x.id for x in templates], format_func=lambda x: next(f"{x.code} · {x.channel} · {x.locale}" for x in templates if x.id == x))
            template = s.get(MessageTemplate, tid)
            with st.form(f"template_{template.id}"):
                subject = st.text_input("Sujet", value=template.subject or "")
                body = st.text_area("Corps", value=template.body, height=180)
                approved = st.checkbox("Modèle validé pour préparation", value=bool(template.is_approved))
                if st.form_submit_button("Enregistrer", type="primary"):
                    template.subject = subject
                    template.body = body
                    template.is_approved = approved
                    template.approved_by = user.id if approved else None
                    log_action(s, user.id, "edit_template", "template", template.id)
                    s.commit()
                    st.success("Modèle enregistré.")
                    st.rerun()
    with tabs[1]:
        messages = list(s.scalars(select(OutboxMessage).order_by(OutboxMessage.created_at.desc())).all())
        st.dataframe(pd.DataFrame([{
            "ID": m.id, "Canal": m.channel, "Sujet": m.subject or "—", "Statut": m.status,
            "Client": m.customer_id, "Créé": fmt_date(m.created_at, locale),
        } for m in messages]), use_container_width=True, hide_index=True)
        if messages:
            mid = st.selectbox("Message", [m.id for m in messages], format_func=lambda x: next(f"{x.id} · {x.subject or x.template_code} · {x.status}" for x in messages if x.id == x))
            msg = s.get(OutboxMessage, mid)
            st.text_area("Aperçu", msg.body, height=180, disabled=True)
            st.caption(f"Destinataire : {mask_email(decrypt_text(msg.recipient_enc))} · statut : {msg.status}")
            c1, c2 = st.columns(2)
            with c1:
                if msg.status == "draft" and st.button("Valider ce message", type="primary"):
                    approve_message(s, msg.id, user.id)
                    s.commit()
                    st.success("Message validé. Aucun envoi réel n'a encore eu lieu.")
                    st.rerun()
            with c2:
                if msg.status == "approved" and st.button("Marquer comme envoyé (démo)"):
                    mark_sent(s, msg.id)
                    s.commit()
                    st.success("Statut passé à envoyé — adaptateur de démonstration, aucun réseau.")
                    st.rerun()
    with tabs[2]:
        bookings = list(s.scalars(select(Booking).order_by(Booking.created_at.desc()).limit(40)).all())
        if bookings:
            bid = st.selectbox("Réservation", [b.id for b in bookings], format_func=lambda x: next(f"{b.reference} · {b.customer.first_name}" for b in bookings if b.id == x))
            booking = s.get(Booking, bid)
            kind = st.selectbox("Type", ["confirmation", "rappel", "demande_avis", "relance_acompte"])
            if st.button("Générer un brouillon", type="primary"):
                st.session_state["generated_message"] = generate_message(kind, booking.customer, booking, locale)
            text = st.text_area("Brouillon", value=st.session_state.get("generated_message", ""), height=180)
            if st.button("Ajouter à la boîte d'envoi"):
                if not text.strip():
                    st.error("Le brouillon est vide.")
                else:
                    queue_message(s, customer=booking.customer, channel="email", subject=f"Azul AGADIR · {booking.reference}",
                                  body=text, booking_id=booking.id, template_code=kind)
                    log_action(s, user.id, "queue_message", "booking", booking.id, {"kind": kind})
                    s.commit()
                    st.success("Brouillon enregistré, en attente de validation.")
                    st.session_state["generated_message"] = ""


def _settings(s, user: User, locale: str) -> None:
    if user.role not in {"admin", "manager"}:
        st.error("Accès réservé à l'administration et à la gestion.")
        return
    page_heading("Réglages", "Les garde-fous, au centre.", "Société, politique, utilisateurs, sauvegardes et traçabilité.", locale)
    tabs = st.tabs(["Société", "Utilisateurs", "Sauvegardes", "Journal", "Démo"])
    with tabs[0]:
        keys = ["company_name", "default_locale", "cancellation_policy", "auto_confirm_demo", "review_window_hours", "ai_model"]
        values = {k: s.get(Setting, k).value if s.get(Setting, k) else None for k in keys}
        with st.form("settings_company"):
            company = st.text_input("Société", value=str(values["company_name"] or "AgadirGO / Azul AGADIR"))
            default_locale = st.selectbox("Langue par défaut", ["fr", "en", "ar", "es"], index=["fr", "en", "ar", "es"].index(str(values["default_locale"] or "fr")))
            auto_confirm = st.checkbox("Confirmation immédiate en mode démo", value=bool(values["auto_confirm_demo"]))
            review_window = st.number_input("Fenêtre d'invitation à l'avis (heures)", 1, 240, int(values["review_window_hours"] or 24))
            model = st.text_input("Modèle IA", value=str(values["ai_model"] or "claude-sonnet-4-6"))
            policy = st.text_area("Politique d'annulation", value=str(values["cancellation_policy"] or CANCELLATION_POLICY), height=120)
            if st.form_submit_button("Enregistrer les réglages", type="primary"):
                for key, value in {
                    "company_name": company, "default_locale": default_locale,
                    "cancellation_policy": policy, "auto_confirm_demo": auto_confirm,
                    "review_window_hours": review_window, "ai_model": model,
                }.items():
                    row = s.get(Setting, key)
                    if row:
                        row.value = value
                        row.updated_by = user.id
                    else:
                        s.add(Setting(key=key, value=value, updated_by=user.id))
                log_action(s, user.id, "edit_settings", "settings")
                s.commit()
                st.success("Réglages enregistrés.")
                st.rerun()
    with tabs[1]:
        if user.role != "admin":
            st.caption("Seul un administrateur peut créer des comptes.")
        users = list(s.scalars(select(User).order_by(User.full_name)).all())
        st.dataframe(pd.DataFrame([{
            "ID": u.id, "Nom": u.full_name, "Email": mask_email(user_email(u)),
            "Rôle": ROLE_LABELS.get(u.role, u.role), "Actif": "Oui" if u.is_active else "Non",
            "Dernière connexion": fmt_date(u.last_login_at, locale) if u.last_login_at else "—",
        } for u in users]), use_container_width=True, hide_index=True)
        if user.role == "admin":
            with st.form("new_user"):
                full_name = st.text_input("Nom complet")
                email = st.text_input("Email")
                password = st.text_input("Mot de passe temporaire", type="password")
                role = st.selectbox("Rôle", list(ROLE_LABELS), format_func=lambda r: ROLE_LABELS[r])
                providers = list(s.scalars(select(Provider).order_by(Provider.name)).all())
                provider_id = st.selectbox("Prestataire associé (si rôle prestataire)", [None] + [p.id for p in providers],
                                           format_func=lambda x: "—" if x is None else s.get(Provider, x).name)
                if st.form_submit_button("Créer le compte", type="primary"):
                    try:
                        create_user(s, email=email, password=password, full_name=full_name, role=role,
                                    provider_id=provider_id, locale=locale)
                        log_action(s, user.id, "create_user", "user")
                        s.commit()
                        st.success("Compte créé.")
                        st.rerun()
                    except Exception as exc:
                        s.rollback()
                        st.error(str(exc))
    with tabs[2]:
        logs = list(s.scalars(select(BackupLog).order_by(BackupLog.created_at.desc()).limit(10)).all())
        st.dataframe(pd.DataFrame([{"Date": fmt_date(b.created_at, locale), "Fichier": b.path, "Octets": b.size_bytes} for b in logs]), use_container_width=True, hide_index=True)
        if st.button("Créer une sauvegarde maintenant", type="primary"):
            try:
                path = create_backup(s, user.id)
                log_action(s, user.id, "create_backup", "database")
                s.commit()
                st.success(f"Sauvegarde créée : {path.name}")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
        st.caption("Sauvegarde locale SQLite. En production, copier aussi vers un stockage chiffré hors du serveur.")
        legal = list(s.scalars(select(LegalDocument).order_by(LegalDocument.doc_type, LegalDocument.locale)).all())
        st.markdown("#### Documents légaux")
        st.dataframe(pd.DataFrame([{"Type": d.doc_type, "Langue": d.locale, "Version": d.version, "Publié": fmt_date(d.published_at, locale)} for d in legal]), use_container_width=True, hide_index=True)
    with tabs[3]:
        logs = list(s.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(60)).all())
        st.dataframe(pd.DataFrame([{
            "Date": l.created_at.strftime("%d/%m/%Y %H:%M") if l.created_at else "—",
            "Acteur": l.actor_id, "Action": l.action, "Entité": f"{l.entity_type}:{l.entity_id}" if l.entity_type else "—",
        } for l in logs]), use_container_width=True, hide_index=True)
        st.caption("Le journal ne contient pas de coordonnée en clair. Les champs sensibles sont chiffrés.")
    with tabs[4]:
        st.warning("La remise à zéro supprime et recrée la base DÉMO. Aucune action en production.")
        confirm = st.checkbox("Je comprends que la base de démonstration sera effacée.")
        if confirm and st.button("Réinitialiser la base DÉMO", type="secondary"):
            try:
                lang = st.session_state.get("lang", "fr")
                dark = st.session_state.get("dark_mode", False)
                reset_demo_database()
                st.session_state.clear()
                st.session_state.lang = lang
                st.session_state.dark_mode = dark
                st.session_state.page = "admin"
                st.success("Base DÉMO réinitialisée. Reconnectez-vous.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def _transport(s, user: User, locale: str) -> None:
    page_heading("Transport", "Chaque trajet, une promesse tenue.", "Planning, chauffeurs, véhicules, retards et feuilles de route.", locale)
    page_heading  # noqa: F821
    today_sheet = today_road_sheet(s)
    st.markdown("#### Feuille de route du jour")
    if today_sheet:
        st.dataframe(pd.DataFrame(today_sheet), use_container_width=True, hide_index=True)
    else:
        st.caption("Aucune affectation de transport aujourd'hui.")
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("#### Affecter une réservation")
        items = list(s.scalars(select(BookingItem).where(BookingItem.item_type == "transport").order_by(BookingItem.service_date.desc()).limit(60)).all())
        drivers = list(s.scalars(select(Driver).where(Driver.is_active.is_(True))).all())
        vehicles = list(s.scalars(select(Vehicle).where(Vehicle.is_active.is_(True))).all())
        if items and drivers and vehicles:
            with st.form("assign_transport"):
                item_id = st.selectbox("Prestation", [i.id for i in items], format_func=lambda x: next(f"{i.booking.reference} · {localized(i.catalog.name, 'fr')} · {i.service_date}" for i in items if i.id == x))
                driver_id = st.selectbox("Chauffeur", [d.id for d in drivers], format_func=lambda x: next(d.full_name for d in drivers if d.id == x))
                vehicle_id = st.selectbox("Véhicule", [v.id for v in vehicles], format_func=lambda x: next(f"{v.label} · {v.capacity} pl." for v in vehicles if v.id == x))
                pickup_at = st.datetime_input("Prise en charge", value=datetime.combine(date.today(), time(9, 0)))
                route = st.text_input("Points d'arrêt", placeholder="Hôtel → Taghazout → retour")
                if st.form_submit_button("Affecter", type="primary"):
                    assignment = TransportAssignment(booking_item_id=item_id, driver_id=driver_id, vehicle_id=vehicle_id,
                                                     pickup_at=pickup_at, route_plan={"stops": route}, status="assigned")
                    s.add(assignment)
                    log_action(s, user.id, "assign_transport", "booking_item", item_id, {"driver": driver_id, "vehicle": vehicle_id})
                    s.commit()
                    st.success("Affectation enregistrée.")
                    st.rerun()
        else:
            st.caption("Ajoutez d'abord des chauffeurs et véhicules.")
    with c2:
        st.markdown("#### Planning des tournées")
        runs = list(s.scalars(select(TransportRun).where(TransportRun.departure_at >= datetime.now() - timedelta(days=1)).order_by(TransportRun.departure_at).limit(30)).all())
        if runs:
            run_id = st.selectbox("Tournée", [r.id for r in runs], format_func=lambda x: next(f"{x.departure_at.strftime('%d/%m %H:%M')} · {localized(x.catalog_id and s.get(CatalogItem, x.catalog_id).name or {}, 'fr')}" for x in runs if x.id == x))
            run = s.get(TransportRun, run_id)
            with st.form("edit_run"):
                delay = st.number_input("Retard (minutes)", 0, 240, int(run.delay_minutes or 0))
                status = st.selectbox("Statut", ["planned", "departed", "completed", "delayed", "cancelled"], index=["planned", "departed", "completed", "delayed", "cancelled"].index(run.status) if run.status in ["planned", "departed", "completed", "delayed", "cancelled"] else 0)
                note = st.text_input("Note", value=run.notes or "")
                if st.form_submit_button("Mettre à jour la tournée", type="primary"):
                    run.delay_minutes = delay
                    run.status = status
                    run.notes = note
                    log_action(s, user.id, "update_transport_run", "transport_run", run.id, {"status": status, "delay": delay})
                    s.commit()
                    st.success("Tournée mise à jour.")
                    st.rerun()
        else:
            st.caption("Pas de tournée planifiée.")
    st.markdown("#### Chauffeurs et véhicules")
    c1, c2 = st.columns(2)
    with c1:
        drivers = list(s.scalars(select(Driver).order_by(Driver.full_name)).all())
        st.dataframe(pd.DataFrame([{"Chauffeur": d.full_name, "Langues": ", ".join(d.languages or []),
                                    "Note": d.rating_avg, "Avis": d.rating_count, "Actif": d.is_active} for d in drivers]),
                     use_container_width=True, hide_index=True)
    with c2:
        vehicles = list(s.scalars(select(Vehicle).order_by(Vehicle.label)).all())
        st.dataframe(pd.DataFrame([{"Véhicule": v.label, "Type": v.vehicle_type, "Places": v.capacity,
                                    "Bagages": v.luggage, "Actif": v.is_active} for v in vehicles]),
                     use_container_width=True, hide_index=True)
    with st.expander("Noter un chauffeur après la course"):
        assignments = list(s.scalars(select(TransportAssignment).where(TransportAssignment.status != "cancelled").order_by(TransportAssignment.pickup_at.desc()).limit(30)).all())
        if assignments:
            aid = st.selectbox("Affectation", [a.id for a in assignments], format_func=lambda x: next(f"{x.id} · {x.pickup_at} · {x.status}" for x in assignments if x.id == x))
            assignment = s.get(TransportAssignment, aid)
            with st.form("rate_driver"):
                rating = st.slider("Note du chauffeur", 1, 5, 5)
                note = st.text_input("Commentaire interne")
                if st.form_submit_button("Enregistrer la note", type="primary"):
                    assignment.driver_rating = rating
                    assignment.notes = note
                    assignment.status = "completed"
                    assignment.completed_at = utcnow()
                    if assignment.driver_id:
                        driver = s.get(Driver, assignment.driver_id)
                        if driver:
                            old = (driver.rating_avg or 0) * (driver.rating_count or 0)
                            driver.rating_count = (driver.rating_count or 0) + 1
                            driver.rating_avg = round((old + rating) / driver.rating_count, 2)
                    log_action(s, user.id, "rate_driver", "assignment", assignment.id, {"rating": rating})
                    s.commit()
                    st.success("Note enregistrée.")
                    st.rerun()
