"""Composants visuels réutilisables : art génératif, cartes, avis, hero."""
from __future__ import annotations

import html
import random
from datetime import date, datetime
from urllib.parse import urlencode

import streamlit as st
import streamlit.components.v1 as components

from src.services.catalog import localized, money, price_unit_label
from src.services.ratings import rating_distribution_percent
from src.i18n import t

PAGE_FOR_KIND = {
    "activity": "decouvrir",
    "restaurant": "restaurants",
    "accommodation": "hebergements",
    "spot": "decouvrir",
    "transport": "transport",
}
KIND_ICON = {"activity": "✦", "restaurant": "◌", "accommodation": "⌂", "spot": "≈", "transport": "→"}
KIND_WORD = {
    "activity": {"fr": "Activité", "en": "Activity", "ar": "نشاط", "es": "Actividad"},
    "restaurant": {"fr": "Table", "en": "Table", "ar": "مطعم", "es": "Mesa"},
    "accommodation": {"fr": "Séjour", "en": "Stay", "ar": "إقامة", "es": "Estancia"},
    "spot": {"fr": "Spot", "en": "Spot", "ar": "موقع", "es": "Lugar"},
    "transport": {"fr": "Transport", "en": "Transport", "ar": "نقل", "es": "Transporte"},
}
PALETTES = {
    "activity": [("#0E6BA8", "#14B8A6", "#F4E4C1"), ("#D9663A", "#F5B700", "#FBF8F2"), ("#4C7A4A", "#14B8A6", "#F4E4C1")],
    "restaurant": [("#D9663A", "#F5B700", "#FBF8F2"), ("#0B1F3A", "#0E6BA8", "#F4E4C1"), ("#4C7A4A", "#D9663A", "#FBF8F2")],
    "accommodation": [("#0B1F3A", "#0E6BA8", "#F4E4C1"), ("#4C7A4A", "#14B8A6", "#FBF8F2"), ("#D9663A", "#F4E4C1", "#FBF8F2")],
    "spot": [("#0E6BA8", "#14B8A6", "#FBF8F2"), ("#0B1F3A", "#14B8A6", "#F4E4C1"), ("#0E6BA8", "#F5B700", "#FBF8F2")],
    "transport": [("#0B1F3A", "#D9663A", "#F4E4C1"), ("#0E6BA8", "#F5B700", "#FBF8F2"), ("#4C7A4A", "#0E6BA8", "#F4E4C1")],
}
MONTHS_FR = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


def esc(value) -> str:
    return html.escape(str(value or ""))


def page_link(page: str, **params) -> str:
    query = {"page": page, **{k: v for k, v in params.items() if v is not None}}
    return "?" + urlencode(query)


def item_link(item) -> str:
    return page_link(PAGE_FOR_KIND.get(item.kind, "decouvrir"), item=item.slug)


def fmt_date(value, locale: str = "fr") -> str:
    if not value:
        return "—"
    if isinstance(value, datetime):
        value = value.date()
    if not isinstance(value, date):
        return str(value)
    if locale == "fr":
        return f"{value.day} {MONTHS_FR[value.month - 1]} {value.year}"
    return value.strftime("%d %b %Y")


def stars(rating: float | None, max_stars: int = 5) -> str:
    value = float(rating or 0)
    full = int(round(value))
    return "".join(
        f'<span class="{"empty" if i >= full else ""}">★</span>' for i in range(max_stars)
    )


def _svm(seed: int, variant: int = 0, kind: str = "activity"):
    palette = PALETTES.get(kind, PALETTES["activity"])
    return palette[(seed + variant) % len(palette)]


def art_svg(item, variant: int = 0, tall: bool = False) -> str:
    """Visuel abstrait généré : aucun droit photo externe, aucun faux lieu."""
    kind = getattr(item, "kind", "activity")
    seed = int(getattr(item, "id", 1) or 1)
    c1, c2, c3 = _svm(seed, variant, kind)
    grad = f"ag{seed}{variant}"
    glow = f"gl{seed}{variant}"
    w, h = 800, 560 if tall else 500
    rnd = random.Random(seed * 97 + variant * 13)
    sun_x = 190 + (seed * 37 + variant * 19) % 520
    sun_y = 100 + (seed * 23) % 90
    sun_r = 34 + (seed % 3) * 8
    if kind == "restaurant":
        shapes = f"""
        <circle cx="270" cy="315" r="100" fill="rgba(255,255,255,.17)"/>
        <circle cx="270" cy="315" r="66" fill="rgba(255,255,255,.13)"/>
        <circle cx="560" cy="280" r="76" fill="rgba(255,255,255,.12)"/>
        <path d="M80 390 Q250 340 400 390 T740 380" stroke="rgba(255,255,255,.35)" stroke-width="4" fill="none"/>
        <rect x="100" y="420" width="600" height="10" rx="5" fill="rgba(255,255,255,.16)"/>
        <path d="M260 240 q10 -28 20 0" stroke="rgba(255,255,255,.5)" stroke-width="3" fill="none"/>
        """
    elif kind == "accommodation":
        shapes = f"""
        <path d="M120 440 L120 250 Q120 180 200 180 Q280 180 280 250 L280 440 Z" fill="rgba(255,255,255,.13)"/>
        <path d="M330 440 L330 220 Q330 150 410 150 Q490 150 490 220 L490 440 Z" fill="rgba(255,255,255,.10)"/>
        <path d="M540 440 L540 270 Q540 210 600 210 Q660 210 660 270 L660 440 Z" fill="rgba(255,255,255,.09)"/>
        <circle cx="200" cy="290" r="26" fill="rgba(245,183,0,.22)"/>
        <circle cx="410" cy="260" r="26" fill="rgba(245,183,0,.20)"/>
        <path d="M80 440 H720" stroke="rgba(255,255,255,.20)" stroke-width="3"/>
        """
    elif kind == "spot":
        shapes = f"""
        <path d="M0 300 Q100 260 200 300 T400 300 T600 300 T800 300 V560 H0Z" fill="rgba(255,255,255,.15)"/>
        <path d="M0 345 Q120 300 240 345 T480 345 T720 345 T960 345 V560 H0Z" fill="rgba(255,255,255,.12)"/>
        <path d="M0 395 Q100 355 200 395 T400 395 T600 395 T800 395 V560 H0Z" fill="rgba(255,255,255,.10)"/>
        <path d="M620 160 q30 -45 60 0" stroke="rgba(255,255,255,.55)" stroke-width="3" fill="none"/>
        <path d="M680 190 q22 -32 44 0" stroke="rgba(255,255,255,.35)" stroke-width="2" fill="none"/>
        """
    elif kind == "transport":
        shapes = f"""
        <path d="M-40 520 C160 380 250 470 390 330 S600 300 840 150" stroke="rgba(255,255,255,.22)" stroke-width="78" fill="none" stroke-linecap="round"/>
        <path d="M-40 520 C160 380 250 470 390 330 S600 300 840 150" stroke="rgba(255,255,255,.40)" stroke-width="4" fill="none" stroke-dasharray="14 18"/>
        <circle cx="610" cy="170" r="18" fill="rgba(255,255,255,.28)"/>
        """
    else:
        shapes = f"""
        <path d="M0 340 L180 280 L360 330 L520 300 L800 370 V560 H0Z" fill="rgba(255,255,255,.10)"/>
        <path d="M0 390 L170 330 L330 380 L520 350 L800 420 V560 H0Z" fill="rgba(255,255,255,.09)"/>
        <path d="M650 370 q-15 -85 -42 -105 q35 15 56 70 q15 -50 42 -70 q-20 45 -20 105" fill="rgba(255,255,255,.18)"/>
        """
    return f"""
    <svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Visuel abstrait de démonstration">
      <defs>
        <linearGradient id="{grad}" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="{c1}"/>
          <stop offset="58%" stop-color="{c2}"/>
          <stop offset="100%" stop-color="{c3}"/>
        </linearGradient>
        <radialGradient id="{glow}" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="rgba(255,255,255,.75)"/>
          <stop offset="100%" stop-color="rgba(255,255,255,0)"/>
        </radialGradient>
      </defs>
      <rect width="{w}" height="{h}" fill="url(#{grad})"/>
      <circle cx="{sun_x}" cy="{sun_y}" r="{sun_r * 3.2}" fill="url(#{glow})" opacity=".55"/>
      <circle cx="{sun_x}" cy="{sun_y}" r="{sun_r}" fill="rgba(255,255,255,.62)"/>
      {shapes}
      <g opacity=".48" fill="none" stroke="rgba(255,255,255,.42)" stroke-width="1.4">
        <path d="M60 90 q35 -18 70 0 q-35 -8 -70 0"/>
        <path d="M690 110 q28 -14 56 0 q-28 -6 -56 0"/>
      </g>
      <text x="42" y="470" font-family="Georgia, serif" font-size="29" fill="rgba(255,255,255,.70)">{KIND_ICON.get(kind, '✦')}</text>
    </svg>
    """


def demo_badge() -> str:
    return '<span class="az-badge demo">DÉMO</span>'


def item_card(item, locale: str = "fr", show_demo: bool = True) -> str:
    name = esc(localized(item.name, locale))
    desc = esc(localized(item.short_description, locale))
    kind = esc(localized(KIND_WORD.get(item.kind, {}), locale))
    price = esc(_price_label(item, locale))
    rating = float(item.rating_avg or 0)
    count = int(item.review_count or 0)
    badges = ""
    if show_demo:
        badges += demo_badge()
    if rating >= 4.5 and count >= 3:
        badges += '<span class="az-badge popular">Populaire</span>'
    if "famille" in (item.vibes or []):
        badges += '<span class="az-badge family">Idéal famille</span>'
    rating_html = (
        f'<div class="az-rating-line"><span class="az-stars">{stars(rating)}</span> '
        f'<b>{rating:.1f}</b><span>· {count} {t("reviews", locale)}</span></div>'
        if count else '<div class="az-rating-line"><span class="az-stars">★★★★★</span><span>Nouveau</span></div>'
    )
    return f"""
    <a class="az-card" href="{item_link(item)}">
      <div class="az-cover">
        {art_svg(item)}
        <div class="badge">{badges}</div>
      </div>
      <div class="az-card-body">
        <div class="az-card-kind">{kind} · {esc(item.district or item.zone or 'Agadir')}</div>
        <div class="az-card-title">{name}</div>
        <div class="az-card-desc">{desc}</div>
        {rating_html}
        <div class="az-card-foot">
          <div class="az-price">{price}</div>
          <span class="az-arrow">Découvrir →</span>
        </div>
      </div>
    </a>
    """


def _price_label(item, locale: str) -> str:
    if item.price_from is None:
        return {"fr": "Tarif à confirmer", "en": "Price on request", "ar": "السعر عند الطلب", "es": "Precio a confirmar"}.get(locale, "Tarif à confirmer")
    unit = price_unit_label(item.price_unit, locale)
    demo = " (DÉMO)" if item.price_status == "demo" else ""
    return f"dès {money(item.price_from)}{demo}<small>{unit}</small>"


def item_grid(items, locale: str = "fr", columns: int = 3) -> None:
    if not items:
        empty_state("🔎", t("no_results", locale), t("no_results", locale))
        return
    for index in range(0, len(items), columns):
        cols = st.columns(columns, gap="medium")
        for col, item in zip(cols, items[index:index + columns]):
            with col:
                st.markdown(item_card(item, locale), unsafe_allow_html=True)


def review_card(review, locale: str = "fr", show_item: bool = False) -> str:
    customer = review.customer
    author = f"{customer.first_name} {customer.last_name[:1]}." if customer else "Voyageur"
    item_name = esc(localized(review.catalog.name, locale)) if getattr(review, "catalog", None) else ""
    date_txt = fmt_date(review.created_at, locale)
    verified = f'<span class="az-badge verified">✓ {t("verified", locale)}</span>'
    demo = '<span class="az-badge demo">DÉMO</span>' if review.is_demo else ""
    response = (
        f'<div class="response"><b>Réponse du gérant</b><br>{esc(review.manager_response)}</div>'
        if review.manager_response else ""
    )
    item_line = f'<div class="az-lesstext">{item_name}</div>' if show_item and item_name else ""
    return f"""
    <div class="az-review">
      <div class="az-review-head">
        <div><div class="az-review-author">{esc(author)}</div>{item_line}
          <div class="az-review-date">{date_txt}</div></div>
        <div class="az-chip-row">{verified}{demo}</div>
      </div>
      <div class="az-stars" aria-label="{review.rating} sur 5">{stars(review.rating)}</div>
      <p>{esc(review.comment)}</p>
      {response}
    </div>
    """


def rating_summary(reviews, locale: str = "fr") -> str:
    from src.services.ratings import calculate_rating
    stats = calculate_rating(reviews)
    if not stats["count"]:
        return f'<div class="az-note">Aucun avis vérifié publié pour le moment.</div>'
    pct = rating_distribution_percent(stats["distribution"])
    bars = "".join(
        f'<div class="az-dist"><span>{s}★</span><div class="bar"><span style="width:{pct[str(s)]}%"></span></div>'
        f'<span>{stats["distribution"][str(s)]}</span></div>'
        for s in (5, 4, 3, 2, 1)
    )
    return f"""
    <div class="az-review" style="display:grid;grid-template-columns:auto 1fr;gap:22px;align-items:center">
      <div class="az-rating-big" style="flex-direction:column;align-items:flex-start">
        <div class="value">{stats['average']}<span style="font-size:1.2rem;color:var(--azul-muted)">/5</span></div>
        <div class="az-stars" style="font-size:1rem">{stars(stats['average'])}</div>
        <div class="az-lesstext">{stats['count']} {t('reviews', locale)} · {t('verified', locale)}</div>
      </div>
      <div style="display:flex;flex-direction:column;gap:5px">{bars}</div>
    </div>
    """


def vibe_tiles(locale: str = "fr") -> str:
    icons = {
        "aventure": "◈", "famille": "⌂", "culture": "✺", "nature": "❧",
        "mer": "≈", "gastronomie": "◌", "detente": "☼", "jeux": "◇",
    }
    labels = {
        "aventure": ("Aventure", "Adventure", "مغامرة", "Aventura"),
        "famille": ("Famille", "Family", "عائلة", "Familia"),
        "culture": ("Culture & artisanat", "Culture & crafts", "ثقافة وحرف", "Cultura"),
        "nature": ("Nature & animaux", "Nature & animals", "طبيعة", "Naturaleza"),
        "mer": ("Mer", "Sea", "البحر", "Mar"),
        "gastronomie": ("Gastronomie", "Food", "مأكولات", "Gastronomía"),
        "detente": ("Détente", "Relax", "استرخاء", "Descanso"),
        "jeux": ("Jeux & loisirs", "Games", "ألعاب", "Juegos"),
    }
    sub = {"fr": "Trouver mon ambiance", "en": "Find my mood", "ar": "اختر مزاجك", "es": "Encuentra tu estilo"}
    idx = {"fr": 0, "en": 1, "ar": 2, "es": 3}.get(locale, 0)
    cells = []
    for key, icon in icons.items():
        label = labels[key][idx]
        cells.append(f'<a class="az-vibe" href="{page_link("decouvrir", vibe=key)}"><span class="ico">{icon}</span><b>{esc(label)}</b><span>{esc(sub.get(locale, ""))}</span></a>')
    return f'<div class="az-vibes">{"".join(cells)}</div>'


def hero_art() -> str:
    return """
    <svg viewBox="0 0 1400 700" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration abstraite de la baie d'Agadir">
      <defs>
        <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#0B1F3A"/><stop offset="50%" stop-color="#0E6BA8"/><stop offset="100%" stop-color="#14B8A6"/>
        </linearGradient>
        <linearGradient id="sea" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#14B8A6" stop-opacity=".9"/><stop offset="100%" stop-color="#0B1F3A" stop-opacity=".98"/>
        </linearGradient>
        <radialGradient id="sun" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#FFF5CF"/><stop offset="58%" stop-color="#F5B700"/><stop offset="100%" stop-color="#D9663A" stop-opacity=".1"/>
        </radialGradient>
      </defs>
      <rect width="1400" height="700" fill="url(#sky)"/>
      <circle cx="1010" cy="180" r="170" fill="url(#sun)" opacity=".38"/>
      <circle cx="1010" cy="180" r="76" fill="#FFE9A7" opacity=".95"/>
      <path d="M0 420 C240 380 400 430 620 400 S1000 360 1400 415 V700 H0Z" fill="url(#sea)"/>
      <path d="M0 470 Q180 440 360 470 T720 470 T1080 470 T1440 470 V700 H0Z" fill="rgba(255,255,255,.055)"/>
      <path d="M0 520 Q200 490 400 520 T800 520 T1200 520 T1600 520 V700 H0Z" fill="rgba(255,255,255,.045)"/>
      <g fill="#0B1F3A" opacity=".84">
        <path d="M90 430 L90 330 L130 330 L130 312 L206 312 L206 330 L248 330 L248 430 Z"/>
        <rect x="112" y="354" width="22" height="30" rx="10" fill="#0E6BA8" opacity=".65"/>
        <rect x="156" y="354" width="22" height="30" rx="10" fill="#0E6BA8" opacity=".65"/>
        <rect x="200" y="354" width="22" height="30" rx="10" fill="#0E6BA8" opacity=".65"/>
        <path d="M64 430 L290 430 L320 445 L40 445 Z"/>
      </g>
      <g opacity=".9">
        <path d="M1130 468 q-24 -140 -76 -184 q82 44 108 176" fill="#0B1F3A" opacity=".55"/>
        <path d="M1122 470 q22 -132 84 -172 q-46 84 -54 172" fill="#0B1F3A" opacity=".45"/>
        <path d="M1104 468 q-12 -78 -58 -100 q42 40 38 100" fill="#0B1F3A" opacity=".35"/>
      </g>
      <g fill="none" stroke="rgba(255,255,255,.35)" stroke-width="2">
        <path d="M390 210 q34 -20 68 0 q-34 -10 -68 0"/>
        <path d="M455 236 q24 -14 48 0 q-24 -7 -48 0"/>
        <path d="M1240 130 q38 -22 76 0 q-38 -11 -76 0"/>
      </g>
      <path d="M840 525 q35 -44 70 0 q-35 -16 -70 0" fill="rgba(255,255,255,.20)"/>
      <path d="M850 560 q28 -34 56 0 q-28 -13 -56 0" fill="rgba(255,255,255,.12)"/>
    </svg>
    """


def hero(locale: str, greeting_name: str | None, weather: dict, counts: dict) -> str:
    name = f", {esc(greeting_name)}" if greeting_name else ""
    temp = f"{weather.get('temperature'):.0f}°" if weather.get("temperature") is not None else "—"
    wind = f"{weather.get('wind'):.0f} km/h" if weather.get("wind") is not None else "—"
    wave = f"{weather.get('wave_height'):.1f} m" if weather.get("wave_height") is not None else "—"
    sea = weather.get("sea_state") or "—"
    sunrise = (weather.get("sunrise") or "")[-5:] or "—"
    sunset = (weather.get("sunset") or "")[-5:] or "—"
    return f"""
    <section class="az-hero">
      <div class="az-hero-art">{hero_art()}</div>
      <span class="az-demo-ribbon">DÉMO · CONTENUS FICTIFS</span>
      <div class="az-hero-copy">
        <div class="eyebrow">AZUL AGADIR · {esc("AGADIRGO")}</div>
        <h1>{esc(t("welcome", locale))}{name}</h1>
        <p>{esc(t("hero_sub", locale))}</p>
        <div class="az-hero-actions">
          <a class="az-btn primary" href="{page_link('decouvrir')}">{esc(t('explore', locale))} →</a>
          <a class="az-btn ghost" href="{page_link('itinerary')}">{esc(t('plan', locale))} ✦</a>
        </div>
        <div class="az-hero-weather">
          <div class="az-weather-pill"><span>{esc(t('weather', locale))}</span><b>{esc(weather.get('summary') or t('weather_unavailable', locale))}</b></div>
          <div class="az-weather-pill"><span>Température</span><b>{temp}</b></div>
          <div class="az-weather-pill"><span>Vent</span><b>{wind}</b></div>
          <div class="az-weather-pill"><span>Mer</span><b>{wave} · {esc(sea)}</b></div>
          <div class="az-weather-pill"><span>Lever / coucher</span><b>{sunrise} / {sunset}</b></div>
        </div>
      </div>
    </section>
    """


def animated_counters(counts: dict, locale: str = "fr") -> None:
    labels = {
        "activity": ("Activités", "Activities", "أنشطة", "Actividades"),
        "restaurant": ("Restaurants", "Restaurants", "مطاعم", "Restaurantes"),
        "accommodation": ("Hébergements", "Stays", "إقامة", "Alojamientos"),
        "spot": ("Spots & plages", "Spots & beaches", "مواقع وشواطئ", "Lugares y playas"),
    }
    idx = {"fr": 0, "en": 1, "ar": 2, "es": 3}.get(locale, 0)
    cells = []
    for kind, value in counts.items():
        label = labels.get(kind, (kind, kind, kind, kind))[idx]
        cells.append(f"""
        <div class="count"><div class="num" data-target="{int(value)}">0</div><div class="lab">{esc(label)} <span>DÉMO</span></div></div>
        """)
    components.html(f"""
    <style>
      * {{ box-sizing: border-box; }}
      body {{ margin:0; background:transparent; font-family: Manrope, system-ui, sans-serif; }}
      .wrap {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; }}
      .count {{ background:rgba(255,255,255,.72); border:1px solid rgba(11,31,58,.09); border-radius:18px; padding:14px 16px; }}
      .num {{ font-family: Georgia, serif; font-size:2.1rem; line-height:1; color:#0B1F3A; font-weight:700; }}
      .lab {{ margin-top:5px; color:#667085; font-size:.63rem; font-weight:700; text-transform:uppercase; letter-spacing:.09em; }}
      .lab span {{ color:#D9663A; }}
      @media (max-width:620px) {{ .wrap {{ grid-template-columns:repeat(2,1fr); }} .num {{ font-size:1.8rem; }} }}
    </style>
    <div class="wrap">{''.join(cells)}</div>
    <script>
      document.querySelectorAll('.num').forEach((el) => {{
        const target = parseInt(el.dataset.target || '0', 10);
        const start = performance.now();
        const duration = 1100;
        function tick(now) {{
          const p = Math.min(1, (now - start) / duration);
          const eased = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(target * eased).toLocaleString('fr-FR');
          if (p < 1) requestAnimationFrame(tick);
        }}
        requestAnimationFrame(tick);
      }});
    </script>
    """, height=130, scrolling=False)


def section_head(kicker: str, title: str, subtitle: str = "", link_label: str = "", link_href: str = "") -> str:
    link = f'<a class="az-link" href="{link_href}">{esc(link_label)} →</a>' if link_label and link_href else ""
    return f"""
    <div class="az-section-head">
      <div><span class="az-kicker">{esc(kicker)}</span><h2>{esc(title)}</h2>{f'<p>{esc(subtitle)}</p>' if subtitle else ''}</div>
      {link}
    </div>
    """


def empty_state(icon: str, title: str, text: str = "", action: str = "", href: str = "") -> None:
    cta = f'<p style="margin-top:16px"><a class="az-btn primary" href="{href}">{esc(action)}</a></p>' if action and href else ""
    st.markdown(
        f'<div class="az-empty"><div class="ico">{icon}</div><h3>{esc(title)}</h3><p>{esc(text)}</p>{cta}</div>',
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    labels = {
        "pending": "En attente", "confirmed": "Confirmée", "deposit_received": "Acompte reçu",
        "completed": "Terminée", "cancelled": "Annulée", "draft": "Brouillon",
    }
    return f'<span class="az-status {esc(status)}">{esc(labels.get(status, status))}</span>'


def gallery(item, locale: str = "fr") -> str:
    variants = [art_svg(item, i) for i in range(5)]
    return f'<div class="az-gallery">{"".join(f"<div>{v}</div>" for v in variants)}</div>'


def confetti() -> None:
    palette = ["#0E6BA8", "#14B8A6", "#F4E4C1", "#D9663A", "#4C7A4A", "#F5B700"]
    pieces = "".join(
        f'<i style="left:{5 + (i * 7) % 92}%;background:{palette[i % len(palette)]};animation-delay:{(i % 9) * .08}s;transform:rotate({(i * 37) % 180}deg)"></i>'
        for i in range(38)
    )
    components.html(f"""
    <style>
      html,body {{ margin:0; background:transparent; overflow:hidden; height:120px; }}
      .stage {{ position:relative; height:120px; }}
      i {{ position:absolute; top:-14px; width:8px; height:14px; border-radius:2px; animation:drop 2.2s cubic-bezier(.2,.7,.4,1) forwards; }}
      @keyframes drop {{ 0% {{ transform:translateY(-20px) rotate(0deg); opacity:0; }} 10% {{ opacity:1; }} 100% {{ transform:translateY(130px) rotate(540deg); opacity:0; }} }}
    </style>
    <div class="stage">{pieces}</div>
    """, height=120, scrolling=False)


def render_footer(locale: str = "fr") -> None:
    st.markdown(f"""
    <div class="az-footer">
      <div><div class="brand">AZUL AGADIR</div><div>par AgadirGO · Porte d'entrée du tourisme à Agadir, Taghazout et alentours.</div>
      <div style="margin-top:6px">© 2026 AgadirGO — application de démonstration.</div></div>
      <div style="display:flex;gap:16px;flex-wrap:wrap">
        <a href="{page_link('legal', doc='cgu')}">Conditions générales</a>
        <a href="{page_link('legal', doc='privacy')}">Confidentialité (loi 09-08)</a>
        <a href="{page_link('legal', doc='cookies')}">Cookies</a>
        <a href="{page_link('admin')}">Espace pro</a>
      </div>
      <div style="max-width:360px">Aucun paiement en ligne n'est activé en V1. Les prix et horaires de démonstration sont fictifs et ne doivent pas être utilisés comme information réelle.</div>
    </div>
    """, unsafe_allow_html=True)


def show_onboarding() -> None:
    if st.session_state.get("onboarding_seen", False):
        return

    @st.dialog("Bienvenue dans Azul AGADIR", width="large")
    def _dialog():
        st.markdown(
            """
            <div style="text-align:center;padding:4px 0 10px">
              <div style="font-family:Georgia,serif;font-size:2.6rem;color:#0B1F3A;line-height:1">Azul.</div>
              <p style="color:#667085;margin-top:4px">Quatre repères pour composer votre séjour.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("#### 1 · Explorez")
        st.caption("Activités, tables, hébergements et spots : filtrez par envie, budget ou météo.")
        st.markdown("#### 2 · Composez")
        st.caption("Ajoutez plusieurs services dans un seul panier, avec un récapitulatif unique.")
        st.markdown("#### 3 · Réservez")
        st.caption("Un humain confirme les prix, horaires et détails. Aucune donnée sensible envoyée à l'IA.")
        st.markdown("#### 4 · Voyagez")
        st.caption("Billet numérique, QR code, rappels et espace personnel.")
        st.info("Mode démonstration : les contenus, prix, horaires et avis sont fictifs.", icon="🧪")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Explorer maintenant", use_container_width=True, type="primary"):
                st.session_state.onboarding_seen = True
                st.rerun()
        with c2:
            if st.button("Ne plus afficher", use_container_width=True):
                st.session_state.onboarding_seen = True
                st.rerun()

    _dialog()
