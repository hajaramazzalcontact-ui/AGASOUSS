"""Pages parcours : séjour, panier, espace client, assistant, avis, pages légales."""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from io import BytesIO

import streamlit as st
from sqlalchemy import select

from src.config import CANCELLATION_POLICY, IS_DEMO, UPLOAD_DIR
from src.db.models import Booking, CatalogItem, Customer, LegalDocument, Review, ReviewPhoto
from src.db.session import get_session
from src.i18n import t
from src.ia.assistant import answer as ai_answer, is_available
from src.ia.guardrails import no_information
from src.ia.planner import build_plan, save_plan
from src.services.booking import (
    BookingError,
    bookings_for_customer,
    create_booking_from_cart,
    get_booking_by_reference,
    upsert_customer,
)
from src.services.cart import add_item, cart_totals, get_or_create_cart, remove_item
from src.services.catalog import all_items, localized, money
from src.services.privacy import anonymize_customer, customer_export
from src.services.ratings import calculate_rating, rating_distribution_percent
from src.services.reviews import create_review, review_eligibility
from src.services.security import decrypt_text, new_cart_token
from src.services.tickets import qr_png, ticket_pdf
from .common import (
    accommodation_options,
    back_link,
    current_cart_token,
    demo_note,
    get_cart,
    get_customer,
    item_small_line,
    page_heading,
    selected_slot_datetime,
)
from .components import (
    art_svg,
    confetti,
    empty_state,
    esc,
    fmt_date,
    item_card,
    item_grid,
    page_link,
    rating_summary,
    review_card,
    section_head,
    show_html,
    stars,
    status_badge,
)

VIBE_LABELS = {
    "aventure": "Aventure", "famille": "Famille", "culture": "Culture & artisanat",
    "nature": "Nature & animaux", "mer": "Mer", "gastronomie": "Gastronomie",
    "detente": "Détente", "jeux": "Jeux & loisirs",
}


def _recalculate_plan(plan: dict) -> None:
    total = 0.0
    unknown = 0
    for day in plan["days"]:
        for item in day["items"]:
            if item.get("price") is None:
                unknown += 1
            else:
                pax = max(1, plan["adults"] + plan["children"])
                total += float(item["price"]) * pax
    plan["total_known"] = round(total, 2)
    plan["unknown_prices"] = unknown


def render_itinerary(locale: str) -> None:
    s = get_session()
    try:
        customer = get_customer(s, st.session_state.get("customer_id"))
        page_heading(
            "Planificateur Azul", t("plan_title", locale),
            "Durée, budget, groupe et centres d'intérêt : Azul assemble un programme jour par jour, avec transport, repas et plan B météo.",
            locale,
        )
        demo_note(locale)
        with st.form("itinerary_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                days = st.number_input(t("plan_days", locale), 1, 7, 3)
            with c2:
                start = st.date_input("Arrivée", value=date.today() + timedelta(days=7))
            with c3:
                budget = st.number_input(t("plan_budget", locale), 0, 50000, 3500, step=250)
            c4, c5, c6 = st.columns(3)
            with c4:
                adults = st.number_input(t("adults", locale), 1, 12, 2)
            with c5:
                children = st.number_input(t("kids", locale), 0, 8, 0)
            with c6:
                level = st.selectbox("Rythme", ["Équilibré", "Tranquille", "Intense"])
            interests = st.multiselect(
                t("interests", locale), list(VIBE_LABELS), default=["mer", "culture", "gastronomie"],
                format_func=lambda x: VIBE_LABELS[x],
            )
            submitted = st.form_submit_button(t("generate_plan", locale), type="primary", use_container_width=True)
        if submitted:
            plan = build_plan(
                s, days=int(days), budget=float(budget), adults=int(adults), children=int(children),
                interests=interests or ["mer", "culture"], start_date=start, locale=locale,
            )
            save_plan(s, plan, customer.id if customer else None, locale)
            s.commit()
            st.session_state.plan = plan
            st.toast("Programme généré à partir du catalogue.", icon="✦")

        plan = st.session_state.get("plan")
        if not plan:
            st.markdown(f"""
            <div class="az-trust">
              <div><b>1 · Profil</b>Durée, budget, adultes et enfants : le programme s'adapte.</div>
              <div><b>2 · Terrain</b>Distances, créneaux et météo sont pris en compte.</div>
              <div><b>3 · Plan B</b>Chaque journée propose une alternative en cas de vent ou de pluie.</div>
            </div>
            """, unsafe_allow_html=True)
            return

        _recalculate_plan(plan)
        st.markdown(section_head(
            "Proposition", f"Votre programme de {plan['duration_days']} jours",
            f"Modèle : {plan.get('model', 'local')} · les prix et horaires à confirmer sont signalés.",
        ), unsafe_allow_html=True)
        st.markdown(f"""
        <div class="az-note" style="margin-bottom:14px">
          <b>Résumé.</b> {esc(plan.get('summary', ''))}<br>
          <b>Total connu (DÉMO) :</b> {money(plan.get('total_known'))} ·
          <b>Prix à confirmer :</b> {plan.get('unknown_prices', 0)} ·
          <b>Météo :</b> {esc(plan.get('weather', {}).get('summary', 'à confirmer'))}
        </div>
        """, unsafe_allow_html=True)
        if plan.get("budget_note"):
            st.warning(plan["budget_note"])

        for day_index, day in enumerate(plan["days"]):
            items_html = []
            for item in day["items"]:
                cat = item["item"]
                price_txt = money(item.get("price")) if item.get("price") is not None else "Prix à confirmer"
                if cat.kind == "activity" and item.get("price") is not None:
                    price_txt += " / pers. (DÉMO)"
                items_html.append(f"""
                <div class="az-day-item">
                  <div class="az-day-time">{esc(item.get('start_time', '—'))}</div>
                  <div style="flex:1">
                    <b><a target="_self" href="{page_link('decouvrir' if cat.kind == 'activity' else ('restaurants' if cat.kind == 'restaurant' else 'transport'), item=cat.slug)}">{esc(localized(cat.name, locale))}</a></b>
                    <small>{esc(item.get('end_time', ''))} · {esc(price_txt)}</small>
                  </div>
                </div>
                """)
            st.markdown(f"""
            <div class="az-day">
              <div class="az-day-head"><h3>Jour {day['day']} · {fmt_date(day['date'], locale)}</h3>
                <span class="az-badge verified">☼ {esc(day.get('weather', 'Météo à confirmer'))}</span></div>
              {''.join(items_html)}
              <div class="az-note" style="margin-top:10px"><b>{t('backup_plan', locale)}</b><br>{esc(day.get('backup', ''))}</div>
            </div>
            """, unsafe_allow_html=True)
            # Modification simple : retirer un élément du programme.
            remove_options = {f"{i}": f"{item['item'].slug} — {localized(item['item'].name, locale)}" for i, item in enumerate(day["items"])}
            if remove_options:
                with st.expander(f"Ajuster le jour {day['day']}"):
                    to_remove = st.multiselect("Éléments à retirer", list(remove_options), format_func=lambda x: remove_options[x], key=f"remove_plan_{day_index}")
                    if st.button("Mettre à jour", key=f"update_plan_{day_index}"):
                        day["items"] = [item for i, item in enumerate(day["items"]) if str(i) not in to_remove]
                        _recalculate_plan(plan)
                        st.session_state.plan = plan
                        st.rerun()

        st.markdown(f"""
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin:12px 0 4px">
          <a target="_self" class="az-btn primary" href="{page_link('cart')}">Voir le panier</a>
          <a target="_self" class="az-chip" href="{page_link('decouvrir')}">Ajouter une activité</a>
        </div>
        """, unsafe_allow_html=True)
        if st.button(t("book_plan", locale), type="primary", use_container_width=True):
            cart = get_cart(s)
            count = 0
            for day in plan["days"]:
                for item in day["items"]:
                    cat = item["item"]
                    variant = item.get("variant")
                    slot = item.get("slot")
                    try:
                        add_item(
                            s, cart, cat.id,
                            variant_id=variant.id if variant else None,
                            slot_id=slot.id if slot else None,
                            item_type=cat.kind,
                            service_date=(slot.start_at.date() if slot else day["date"]),
                            start_at=(slot.start_at if slot else datetime.combine(day["date"], datetime.min.time())),
                            adults=plan["adults"], children=plan["children"], quantity=1,
                            details={"from_plan": True, "arrival": str(plan["start_date"])},
                        )
                        count += 1
                    except Exception:
                        continue
            s.commit()
            if count:
                st.session_state.page = "cart"
                st.query_params["page"] = "cart"
                st.rerun()
            else:
                st.warning("Aucun élément n'a pu être ajouté. Vérifiez les disponibilités.")
    finally:
        s.close()


def _cart_line_html(line, locale: str) -> str:
    item = line.catalog
    variant = localized(line.variant.name, locale) if line.variant else ""
    when = ""
    if line.start_at:
        when = line.start_at.strftime("%d/%m/%Y · %H:%M")
    elif line.service_date:
        when = fmt_date(line.service_date, locale)
    pax = f"{line.adults} adulte(s)" + (f" · {line.children} enfant(s)" if line.children else "")
    if line.item_type == "accommodation":
        pax = f"{line.details.get('nights', 1)} nuit(s) · {line.quantity} chambre(s)"
    price = money(line.unit_price) if line.unit_price is not None else "Prix à confirmer"
    return f"""
    <div style="display:flex;gap:14px;align-items:center;background:var(--azul-surface);border:1px solid var(--azul-line);border-radius:20px;padding:12px;margin-bottom:9px">
      <div style="width:112px;height:86px;border-radius:14px;overflow:hidden;flex:0 0 auto">{art_svg(item, 1)}</div>
      <div style="flex:1;min-width:0">
        <div class="az-card-kind">{esc(line.item_type)} · {esc(variant)}</div>
        <div style="font-family:'Cormorant Garamond',serif;font-size:1.3rem;line-height:1.05">{esc(localized(item.name, locale))}</div>
        <div class="az-lesstext">{esc(when)} · {esc(pax)} · <b>{esc(price)}</b></div>
      </div>
    </div>
    """


def _show_booking_confirmation(s, booking: Booking, locale: str) -> None:
    confetti()
    st.success(f"{t('thank_you', locale)}")
    st.markdown(f"""
    <div class="az-detail-copy" style="margin-top:12px">
      <span class="az-kicker">{t('reference', locale)}</span>
      <h1 style="font-size:2.7rem;margin:0">{esc(booking.reference)}</h1>
      {status_badge(booking.status)}
      <p class="lead">Total connu : <b>{money(booking.total_amount)}</b> · acompte : <b>{money(booking.deposit_amount)}</b> (aucun paiement en ligne en V1).</p>
      <div class="az-note"><b>{t('score', locale)} : {booking.score}/100</b><br>{esc(booking.score_explanation)}</div>
      <p style="color:var(--azul-muted);font-size:.8rem">
        {"Mode DÉMO : la confirmation immédiate est activée pour la visite. En production, un humain valide la demande, les prix et les horaires." if booking.is_demo else "Un humain confirme les prix et horaires avant l'émission du billet."}
      </p>
    </div>
    """, unsafe_allow_html=True)
    ticket = booking.tickets[0] if booking.tickets else None
    if ticket:
        st.markdown(f"### {t('ticket', locale)}")
        c1, c2 = st.columns([1, 2])
        with c1:
            st.image(qr_png(ticket.qr_payload), caption="QR billet — DÉMO", width=210)
        with c2:
            st.caption("Présentez ce billet au prestataire. Le QR ne contient pas de donnée personnelle.")
            try:
                pdf = ticket_pdf(booking, locale)
                st.download_button(t("download_ticket", locale), pdf, file_name=f"{booking.reference}.pdf",
                                   mime="application/pdf", use_container_width=True)
            except Exception as exc:
                st.warning("Le PDF n'a pas pu être généré. Le QR reste valable.")
    else:
        st.info("Le billet sera émis après confirmation humaine de la réservation.")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'<a target="_self" class="az-btn primary" href="{page_link("account")}">Voir mon espace →</a>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<a target="_self" class="az-chip" href="{page_link("decouvrir")}">Continuer à explorer</a>', unsafe_allow_html=True)
    with c3:
        if st.button("Nouveau panier", use_container_width=True):
            st.session_state.last_booking_id = None
            st.rerun()


def render_cart(locale: str) -> None:
    s = get_session()
    try:
        if st.session_state.get("last_booking_id"):
            booking = s.get(Booking, st.session_state.last_booking_id)
            if booking:
                page_heading("Confirmation", "Votre demande est enregistrée", "Récapitulatif et billet numérique.", locale)
                _show_booking_confirmation(s, booking, locale)
                return
        cart = get_cart(s)
        page_heading("Panier unique", "Plusieurs services, une seule demande",
                     "Activités, tables, hébergements et transport réunis dans un récapitulatif unique.", locale)
        demo_note(locale)
        if not cart.items:
            empty_state("◌", t("cart_empty", locale), t("cart_empty_hint", locale), t("explore", locale), page_link("decouvrir"))
            return
        for line in list(cart.items):
            c1, c2 = st.columns([6, 1])
            with c1:
                show_html(_cart_line_html(line, locale))
            with c2:
                st.write("")
                if st.button("✕", key=f"remove_{line.id}", help=t("remove", locale)):
                    remove_item(s, cart.id, line.id)
                    s.commit()
                    st.rerun()
        totals = cart_totals(cart.items)
        st.markdown(f"""
        <div class="az-note" style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;font-size:.82rem">
          <div><b>{t('known_total', locale)}</b><br><span style="font-size:1.6rem;font-family:Georgia,serif">{money(totals['known_total'])}</span></div>
          <div><b>{t('unknown_prices', locale)}</b><br>{totals['unknown_count']} ligne(s) · confirmation humaine requise</div>
          <div><b>Paiement</b><br>Aucun paiement en ligne en V1</div>
        </div>
        """, unsafe_allow_html=True)
        if totals["unknown_count"]:
            st.warning("Certaines lignes n'ont pas de prix renseigné. Le total final sera confirmé par un humain ; aucun montant n'est inventé.")

        customer = get_customer(s, st.session_state.get("customer_id"))
        email = decrypt_text(customer.email_enc) if customer else ""
        phone = decrypt_text(customer.phone_enc) if customer else ""
        accs = accommodation_options(s, locale)
        acc_labels = {0: "— À préciser —", **{a.id: localized(a.name, locale) for a in accs}}
        st.markdown(section_head("Récapitulatif", t("your_details", locale), "Consentement explicite et données minimisées."), unsafe_allow_html=True)
        with st.form("checkout_form"):
            c1, c2 = st.columns(2)
            with c1:
                first_name = st.text_input(t("first_name", locale), value=customer.first_name if customer else "")
            with c2:
                last_name = st.text_input(t("last_name", locale), value=customer.last_name if customer else "")
            c3, c4 = st.columns(2)
            with c3:
                email_input = st.text_input(t("email", locale), value=email or "")
            with c4:
                phone_input = st.text_input(t("phone", locale), value=phone or "")
            c5, c6, c7 = st.columns(3)
            with c5:
                country = st.text_input(t("country", locale), value=customer.country if customer and customer.country else "Maroc")
            with c6:
                lang = st.selectbox("Langue", ["fr", "en", "ar", "es"], index=["fr", "en", "ar", "es"].index(locale))
            with c7:
                source = st.selectbox(t("source", locale), ["Site Azul", "Hôtel partenaire", "Instagram", "Google", "Bouche à oreille", "Office de tourisme"])
            c8, c9 = st.columns(2)
            with c8:
                stay_start = st.date_input(t("stay_dates", locale), value=customer.stay_start if customer and customer.stay_start else date.today())
            with c9:
                stay_end = st.date_input("Fin du séjour", value=customer.stay_end if customer and customer.stay_end else date.today() + timedelta(days=5))
            c10, c11, c12 = st.columns(3)
            with c10:
                adults = st.number_input(t("adults", locale), 1, 20, customer.adults if customer else 2)
            with c11:
                children = st.number_input(t("kids", locale), 0, 10, len(customer.children or []) if customer else 0)
            with c12:
                acc_id = st.selectbox(t("accommodation", locale), list(acc_labels), format_func=lambda x: acc_labels[x],
                                      index=list(acc_labels).index(customer.accommodation_id) if customer and customer.accommodation_id in acc_labels else 0)
            ages = st.text_input("Âges des enfants (ex. 6, 9)", value=", ".join(str(x) for x in (customer.children or [])) if customer else "")
            interests = st.multiselect(t("interests", locale), list(VIBE_LABELS), default=(customer.interests or []) if customer else ["mer", "culture"],
                                       format_func=lambda x: VIBE_LABELS[x])
            budget_max = st.number_input("Budget indicatif (MAD)", 0, 50000, int(customer.budget_max or 5000) if customer else 5000, step=250)
            special = st.text_area(t("requests", locale), value=decrypt_text(customer.special_requests_enc) if customer else "")
            marketing = st.checkbox("Je souhaite recevoir les idées et offres d'Azul AGADIR (facultatif).", value=bool(customer.marketing_opt_in) if customer else False)
            consent = st.checkbox(t("consent", locale), value=False)
            st.caption(f"{t('privacy_link', locale)} : données utilisées uniquement pour la réservation, accès/rectification/suppression sur demande. Loi 09-08.")
            submitted = st.form_submit_button(t("confirm_request", locale), type="primary", use_container_width=True)
        if submitted:
            if not consent:
                st.error("Le consentement explicite est obligatoire.")
                return
            if not (first_name.strip() and (email_input.strip() or phone_input.strip())):
                st.error("Renseignez au minimum votre prénom et un email ou un téléphone.")
                return
            try:
                ages_list = [int(x.strip()) for x in ages.split(",") if x.strip().isdigit()]
                customer_obj = upsert_customer(
                    s, first_name=first_name, last_name=last_name, email=email_input, phone=phone_input,
                    country=country, locale=lang, stay_start=stay_start, stay_end=stay_end,
                    adults=int(adults), children=ages_list, interests=interests,
                    accommodation_id=acc_id or None, budget_max=float(budget_max),
                    source=source, special_requests=special, marketing_opt_in=marketing, consent=consent,
                )
                booking = create_booking_from_cart(s, cart, customer_obj, special_requests=special)
                s.commit()
                st.session_state.customer_id = customer_obj.id
                st.session_state.last_booking_id = booking.id
                st.session_state.cart_token = new_cart_token()
                st.rerun()
            except (BookingError, ValueError) as exc:
                s.rollback()
                st.error(str(exc))
            except Exception as exc:
                s.rollback()
                st.error(f"La demande n'a pas pu être enregistrée : {exc}")
    finally:
        s.close()


def _ticket_block(s, booking: Booking, locale: str) -> None:
    ticket = booking.tickets[0] if booking.tickets else None
    if not ticket:
        st.caption("Billet en attente de confirmation humaine.")
        return
    c1, c2 = st.columns([1, 2])
    with c1:
        st.image(qr_png(ticket.qr_payload), width=170, caption="QR — DÉMO")
    with c2:
        try:
            pdf = ticket_pdf(booking, locale)
            st.download_button("Télécharger le billet", pdf, file_name=f"{booking.reference}.pdf",
                               mime="application/pdf", key=f"pdf_{booking.id}")
        except Exception:
            st.caption("PDF indisponible, QR valable.")


def render_account(locale: str) -> None:
    s = get_session()
    try:
        page_heading("Mon espace", "Votre voyage, au même endroit", "Réservations, billets, rappels, avis et fidélité.", locale)
        demo_note(locale)
        if IS_DEMO:
            customers = list(s.scalars(select(Customer).order_by(Customer.id)).all())
            labels = {c.id: f"{c.first_name} {c.last_name} · {c.country}" for c in customers}
            current = st.session_state.get("customer_id") or (customers[0].id if customers else None)
            chosen = st.selectbox("Explorer un profil de démonstration", list(labels), index=list(labels).index(current) if current in labels else 0, format_func=lambda x: labels[x])
            if chosen != st.session_state.get("customer_id"):
                st.session_state.customer_id = chosen
                st.rerun()
        elif not st.session_state.get("customer_id"):
            st.info("Retrouvez vos réservations avec votre référence et l'email utilisé.")
            with st.form("lookup_booking"):
                ref = st.text_input(t("reference", locale))
                lookup_email = st.text_input(t("email", locale))
                if st.form_submit_button("Retrouver", type="primary"):
                    booking = get_booking_by_reference(s, ref)
                    if booking and booking.customer:
                        from src.services.security import hash_identifier
                        if booking.customer.email_hash == hash_identifier(lookup_email):
                            st.session_state.customer_id = booking.customer_id
                            st.rerun()
                    st.error("Référence ou email incorrect.")
            return

        customer = get_customer(s, st.session_state.get("customer_id"))
        if not customer:
            empty_state("⌂", "Aucun profil", "Votre profil apparaîtra après votre première demande.")
            return
        bookings = bookings_for_customer(s, customer.id)
        completed = [b for b in bookings if b.status == "completed"]
        reviews = list(s.scalars(select(Review).where(Review.customer_id == customer.id)).all())
        points = len(completed) * 100 + len(reviews) * 20
        tier = "Azul" if points < 300 else ("Océan" if points < 900 else "Argan")
        st.markdown(f"""
        <div class="az-detail-copy" style="margin-bottom:16px">
          <div class="az-chip-row"><span class="az-badge demo">DÉMO</span><span class="az-badge verified">Profil fictif</span></div>
          <h1 style="margin:0">{esc(customer.first_name)} {esc(customer.last_name)}</h1>
          <p class="lead">{esc(customer.country or '—')} · {esc(customer.locale.upper())} · séjour {fmt_date(customer.stay_start, locale)} → {fmt_date(customer.stay_end, locale)}</p>
          <div class="az-facts">
            <div class="az-fact"><span>Email</span><b>{esc(decrypt_text(customer.email_enc) or '—')}</b></div>
            <div class="az-fact"><span>Téléphone</span><b>{esc(decrypt_text(customer.phone_enc) or '—')}</b></div>
            <div class="az-fact"><span>Fidélité</span><b>{tier} · {points} pts</b></div>
            <div class="az-fact"><span>Réservations</span><b>{len(bookings)} · {len(completed)} terminée(s)</b></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        upcoming = [b for b in bookings if b.status in {"pending", "confirmed", "deposit_received"}]
        if upcoming:
            st.markdown(section_head("Rappels", "Vos prochains rendez-vous"), unsafe_allow_html=True)
            for booking in upcoming[:4]:
                items = " · ".join(localized(i.catalog.name, locale) for i in booking.items)
                st.markdown(f"""
                <div class="az-note" style="margin-bottom:8px">
                  {status_badge(booking.status)} <b>{esc(booking.reference)}</b> · {esc(items)}<br>
                  Ramassage / heure : à confirmer la veille · <a target="_self" href="{page_link('account')}">Voir le billet</a>
                </div>
                """, unsafe_allow_html=True)

        st.markdown(section_head("Historique", t("my_trips", locale)), unsafe_allow_html=True)
        if not bookings:
            empty_state("◌", t("no_bookings", locale))
        for booking in bookings:
            items_text = " · ".join(localized(i.catalog.name, locale) for i in booking.items)
            with st.expander(f"{booking.reference} · {items_text[:70]} · {booking.total_amount or 'à confirmer'} MAD", expanded=False):
                st.markdown(f"{status_badge(booking.status)} · créée le {fmt_date(booking.created_at, locale)}", unsafe_allow_html=True)
                for item in booking.items:
                    when = fmt_date(item.service_date, locale)
                    st.markdown(f"- **{localized(item.catalog.name, locale)}** · {when} · {money(item.line_total)}")
                if booking.status in {"confirmed", "completed", "deposit_received"}:
                    _ticket_block(s, booking, locale)
                if booking.status == "completed":
                    for item in booking.items:
                        existing = s.scalar(select(Review).where(Review.booking_item_id == item.id))
                        if existing:
                            st.markdown(review_card(existing, locale), unsafe_allow_html=True)
                        else:
                            allowed, _ = review_eligibility(s, item.id)
                            if allowed:
                                with st.form(f"review_form_{item.id}"):
                                    st.markdown(f"**{t('write_review', locale)} — {localized(item.catalog.name, locale)}**")
                                    rating = st.slider("Note", 1, 5, 5)
                                    comment = st.text_area("Commentaire")
                                    photo = st.file_uploader("Photo facultative", type=["jpg", "jpeg", "png"], key=f"photo_{item.id}")
                                    if st.form_submit_button("Publier mon avis vérifié", type="primary"):
                                        photo_path = None
                                        if photo:
                                            folder = UPLOAD_DIR / "reviews" / str(item.id)
                                            folder.mkdir(parents=True, exist_ok=True)
                                            photo_path = folder / f"{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                                            photo_path.write_bytes(photo.getvalue())
                                        review = create_review(
                                            s, booking_item_id=item.id, rating=int(rating), comment=comment,
                                            customer_id=customer.id, language=locale,
                                            photos=[str(photo_path)] if photo_path else None,
                                        )
                                        s.commit()
                                        st.rerun()

        with st.expander("Confidentialité et données"):
            export = customer_export(s, customer.id)
            st.download_button("Télécharger mes données (JSON)", json.dumps(export, ensure_ascii=False, indent=2),
                               file_name=f"azul-donnees-{customer.id}.json", mime="application/json")
            st.caption("Droit d'accès, de rectification et de suppression. La suppression est une anonymisation qui préserve les obligations comptables.")
            if st.checkbox("Je comprends que l'anonymisation est irréversible.", key=f"anon_ok_{customer.id}"):
                if st.button("Demander la suppression de mes données", type="secondary"):
                    anonymize_customer(s, customer.id)
                    s.commit()
                    st.session_state.customer_id = None
                    st.success("Les coordonnées ont été supprimées.")
                    st.rerun()
    finally:
        s.close()


def _assistant_process(s, prompt: str, locale: str) -> None:
    history = st.session_state.get("chat", [])
    history.append({"role": "user", "content": prompt})
    result = ai_answer(s, prompt, locale, history=history[-8:])
    history.append({
        "role": "assistant", "content": result["answer"], "model": result.get("model"),
        "guardrail": result.get("guardrail"),
        "sources": [
            {"id": item.id, "name": localized(item.name, locale), "slug": item.slug, "kind": item.kind}
            for item in result.get("items", [])
        ],
    })
    st.session_state.chat = history


def render_assistant(locale: str) -> None:
    s = get_session()
    try:
        page_heading("Assistant Azul", "Une conversation ancrée dans le catalogue",
                     "L'assistant répond uniquement à partir des fiches Azul. S'il ne sait pas, il le dit.", locale)
        demo_note(locale)
        if not is_available():
            st.info("Clé Claude non configurée : l'assistant utilise le moteur local, sans invention. Ajoutez ANTHROPIC_API_KEY pour activer Claude.", icon="✦")
        else:
            st.caption("Claude est activé. Les coordonnées personnelles sont masquées avant tout appel.")
        if "chat" not in st.session_state:
            st.session_state.chat = [{
                "role": "assistant",
                "content": t("ai_intro", locale),
                "sources": [], "model": "moteur local Azul", "guardrail": "ok",
            }]

        examples = [
            "Que faire à Agadir avec des enfants quand il y a du vent ?",
            "Quels restaurants ont une vue mer ?",
            "Comment aller de mon hôtel à Taghazout ?",
            "Propose-moi une journée culture et artisanat.",
        ]
        cols = st.columns(2)
        for i, example in enumerate(examples):
            with cols[i % 2]:
                if st.button(example, key=f"example_{i}", use_container_width=True):
                    _assistant_process(s, example, locale)
                    s.commit()
                    st.rerun()

        for message in st.session_state.chat:
            with st.chat_message(message["role"], avatar="✦" if message["role"] == "assistant" else "◉"):
                st.markdown(message["content"])
                if message.get("sources"):
                    source_html = "".join(
                        f'<a target="_self" class="az-chip" href="{page_link("decouvrir" if src["kind"] == "activity" else ("restaurants" if src["kind"] == "restaurant" else "transport"), item=src["slug"])}">{esc(src["name"])}</a>'
                        for src in message["sources"]
                    )
                    st.markdown(f'<div class="az-chip-row" style="margin-top:6px">{source_html}</div>', unsafe_allow_html=True)
                if message["role"] == "assistant":
                    st.caption(f"Modèle : {message.get('model', 'local')} · garde-fou : {message.get('guardrail', 'ok')}")

        prompt = st.chat_input(t("ask", locale))
        if prompt:
            _assistant_process(s, prompt, locale)
            s.commit()
            st.rerun()
        if len(st.session_state.chat) > 1 and st.button("Effacer la conversation", type="secondary"):
            st.session_state.chat = []
            st.rerun()
        st.caption("L'IA propose, l'humain valide. Aucune réservation, aucun prix et aucun envoi ne sont déclenchés automatiquement.")
    finally:
        s.close()


def render_reviews(locale: str) -> None:
    s = get_session()
    try:
        page_heading("Réputation", "Tous les avis vérifiés", "Les critiques sont visibles. Le gérant peut répondre publiquement ; la modération exige un motif.", locale)
        demo_note(locale)
        reviews = list(s.scalars(select(Review).where(Review.status == "published", Review.verified.is_(True)).order_by(Review.created_at.desc())).all())
        st.markdown(rating_summary(reviews, locale), unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            min_rating = st.selectbox("Filtrer par note", ["Toutes", 5, 4, 3, 2, 1])
        with c2:
            item_filter = st.selectbox("Filtrer par fiche", ["Toutes"] + sorted({localized(r.catalog.name, locale) for r in reviews if r.catalog}))
        filtered = [r for r in reviews if (min_rating == "Toutes" or r.rating == min_rating) and
                    (item_filter == "Toutes" or localized(r.catalog.name, locale) == item_filter)]
        st.markdown(f"**{len(filtered)} avis**")
        for index in range(0, len(filtered), 3):
            cols_html = "".join(f"<div>{review_card(r, locale, show_item=True)}</div>" for r in filtered[index:index + 3])
            st.markdown(f'<div class="az-grid">{cols_html}</div>', unsafe_allow_html=True)
    finally:
        s.close()


def render_legal(locale: str) -> None:
    s = get_session()
    try:
        doc_type = st.query_params.get("doc", "privacy")
        doc = s.scalar(select(LegalDocument).where(LegalDocument.doc_type == doc_type, LegalDocument.locale == locale))
        if not doc:
            doc = s.scalar(select(LegalDocument).where(LegalDocument.doc_type == doc_type, LegalDocument.locale == "fr"))
        page_heading("Transparence", doc.title if doc else "Informations légales",
                     "Documents de démonstration à faire valider par AgadirGO et un juriste avant production.", locale)
        demo_note(locale)
        tabs = st.tabs(["Confidentialité", "CGU", "Cookies"])
        mapping = ["privacy", "cgu", "cookies"]
        for tab, code in zip(tabs, mapping):
            with tab:
                row = s.scalar(select(LegalDocument).where(LegalDocument.doc_type == code, LegalDocument.locale == "fr"))
                st.markdown(f"### {row.title if row else code.upper()}")
                st.write(row.content if row else "Document à compléter.")
        st.markdown(f"""
        <div class="az-trust">
          <div><b>Données minimales</b>Nom, contact, séjour et préférences. Pas de données sensibles inutiles.</div>
          <div><b>Loi 09-08</b>Consentement explicite, accès, rectification et suppression. Contact : privacy@agadirgo.example.</div>
          <div><b>IA</b>Aucune coordonnée personnelle transmise au modèle. L'IA ne décide ni d'un prix ni d'une confirmation.</div>
        </div>
        """, unsafe_allow_html=True)
        st.info(f"Politique d'annulation : {CANCELLATION_POLICY}", icon="⚖️")
    finally:
        s.close()
