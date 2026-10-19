"""Billets numériques, QR signé et PDF."""
from __future__ import annotations

from io import BytesIO

import qrcode
from fpdf import FPDF

from src.db.models import Booking, Ticket
from src.services.catalog import localized
from src.services.security import sign_ticket_payload


def issue_ticket(session, booking: Booking, ticket_ref: str | None = None) -> Ticket:
    existing = session.query(Ticket).filter(Ticket.booking_id == booking.id).first()
    if existing:
        return existing
    ref = ticket_ref or f"TKT-{booking.reference}"
    payload = sign_ticket_payload(booking.reference)
    ticket = Ticket(booking_id=booking.id, reference=ref, qr_payload=payload, status="issued")
    session.add(ticket)
    session.flush()
    return ticket


def qr_png(payload: str) -> bytes:
    qr = qrcode.QRCode(version=None, box_size=8, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0B1F3A", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def ticket_pdf(booking: Booking, locale: str = "fr") -> bytes:
    """Génère un billet simple. Les données réelles sont relues depuis la base."""
    pdf = FPDF(unit="mm", format="A4")
    pdf.add_page()
    pdf.set_fill_color(14, 107, 168)
    pdf.rect(0, 0, 210, 38, style="F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_xy(18, 12)
    pdf.cell(0, 10, "AZUL AGADIR")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(18, 25)
    pdf.cell(0, 6, "Billet numerique - demonstration")
    pdf.set_text_color(11, 31, 58)
    pdf.set_xy(18, 50)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 8, f"Reservation {booking.reference}")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_xy(18, 62)
    customer = booking.customer
    pdf.cell(0, 6, f"Client : {customer.first_name} {customer.last_name}")
    pdf.set_xy(18, 69)
    pdf.cell(0, 6, f"Statut : {booking.status}  |  Total : {booking.total_amount or 'a confirmer'} MAD")
    pdf.set_xy(18, 76)
    pdf.cell(0, 6, f"Mode : {'DEMONSTRATION - donnees fictives' if booking.is_demo else 'production'}")
    pdf.set_xy(18, 90)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 7, "Prestations")
    pdf.set_font("Helvetica", "", 10)
    y = 100
    for item in booking.items:
        title = localized(item.catalog.name, locale)
        date = item.service_date.strftime("%d/%m/%Y") if item.service_date else "date a confirmer"
        pdf.set_xy(18, y)
        pdf.multi_cell(130, 5, f"- {title} | {date} | {item.line_total or 'a confirmer'} MAD")
        y += 11
        if y > 205:
            pdf.add_page()
            y = 20
    ticket = booking.tickets[0] if booking.tickets else None
    payload = ticket.qr_payload if ticket else sign_ticket_payload(booking.reference)
    qr_bytes = qr_png(payload)
    pdf.image(BytesIO(qr_bytes), x=145, y=210, w=45, h=45)
    pdf.set_xy(18, 245)
    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(120, 4, "QR de demonstration. Presentez ce billet au prestataire. "
                           "Les prix, horaires et conditions reels doivent etre confirmes par Azul AGADIR.")
    out = pdf.output()
    return bytes(out) if not isinstance(out, bytes) else out
