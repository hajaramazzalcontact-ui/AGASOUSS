"""Thème premium clair / sombre et injection CSS."""
from __future__ import annotations

import streamlit as st

BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Manrope:wght@400;500;600;700;800&family=Noto+Kufi+Arabic:wght@400;600;700&display=swap');

:root {
  --azul-bg: #FBF8F2;
  --azul-surface: #FFFFFF;
  --azul-surface-2: #F6F0E4;
  --azul-ink: #1B2433;
  --azul-night: #0B1F3A;
  --azul-muted: #667085;
  --azul-line: rgba(11,31,58,.10);
  --azul-ocean: #0E6BA8;
  --azul-turquoise: #14B8A6;
  --azul-sand: #F4E4C1;
  --azul-terracotta: #D9663A;
  --azul-argan: #4C7A4A;
  --azul-gold: #F5B700;
  --azul-shadow: 0 16px 48px rgba(11,31,58,.10);
  --azul-shadow-soft: 0 8px 24px rgba(11,31,58,.07);
  --azul-radius: 24px;
}
html[data-azul-theme="dark"], body.azul-dark {
  --azul-bg: #0E1523;
  --azul-surface: #172033;
  --azul-surface-2: #1D2940;
  --azul-ink: #E8EEF8;
  --azul-night: #F5F8FD;
  --azul-muted: #A6B2C8;
  --azul-line: rgba(232,238,248,.12);
  --azul-sand: #3A3326;
  --azul-shadow: 0 16px 48px rgba(0,0,0,.35);
  --azul-shadow-soft: 0 8px 24px rgba(0,0,0,.25);
}

html, body, [class*="css"] {
  font-family: 'Manrope', system-ui, -apple-system, sans-serif;
}
body { background: var(--azul-bg); color: var(--azul-ink); }
.stApp {
  background:
    radial-gradient(circle at 8% 4%, rgba(20,184,166,.08), transparent 28rem),
    radial-gradient(circle at 92% 0%, rgba(217,102,58,.08), transparent 24rem),
    var(--azul-bg);
  color: var(--azul-ink);
}
header[data-testid="stHeader"] { background: transparent; height: 0; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 1240px; padding-top: 1.1rem; padding-bottom: 4rem; }
h1, h2, h3, .az-display {
  font-family: 'Cormorant Garamond', Georgia, serif;
  color: var(--azul-night);
  letter-spacing: -.02em;
}
h1 { font-size: clamp(2.4rem, 5vw, 4.4rem); line-height: .98; }
h2 { font-size: clamp(1.9rem, 3.4vw, 2.8rem); }
h3 { font-size: clamp(1.35rem, 2vw, 1.8rem); }
p, li, label, .stMarkdown { color: var(--azul-ink); }
a { color: var(--azul-ocean); text-decoration: none; }
a:hover { color: var(--azul-turquoise); }
[data-testid="stSidebar"] { display: none; }
[data-testid="stMetric"] {
  background: var(--azul-surface);
  border: 1px solid var(--azul-line);
  border-radius: 20px;
  padding: 16px 18px;
  box-shadow: var(--azul-shadow-soft);
}
[data-testid="stMetricLabel"] { color: var(--azul-muted); font-weight: 600; }
[data-testid="stMetricValue"] { color: var(--azul-night); font-family: 'Cormorant Garamond', serif; }
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  border-radius: 999px;
  border: 0;
  background: linear-gradient(135deg, var(--azul-ocean), var(--azul-turquoise));
  color: #fff;
  font-weight: 700;
  padding: .6rem 1.15rem;
  box-shadow: 0 10px 22px rgba(14,107,168,.22);
  transition: transform .18s ease, box-shadow .18s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(14,107,168,.30);
  color: #fff;
}
.stButton > button[kind="secondary"], .stDownloadButton > button[kind="secondary"] {
  background: var(--azul-surface);
  color: var(--azul-night);
  border: 1px solid var(--azul-line);
  box-shadow: none;
}
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input, [data-testid="stTextArea"] textarea,
[data-baseweb="select"] > div, [data-baseweb="input"] > div {
  border-radius: 14px !important;
  background: var(--azul-surface) !important;
  color: var(--azul-ink) !important;
  border-color: var(--azul-line) !important;
}
[data-testid="stExpander"] {
  background: var(--azul-surface);
  border: 1px solid var(--azul-line);
  border-radius: 18px;
  overflow: hidden;
}
[data-testid="stTabs"] button { font-weight: 700; }
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { background: var(--azul-turquoise); }
.stAlert { border-radius: 16px; }
hr { border-color: var(--azul-line); }

/* ------------------------------------------------------------- top bar */
.az-topbar {
  display: flex; align-items: center; justify-content: space-between; gap: 18px;
  padding: 10px 0 4px 0;
}
.az-brand { display: inline-flex; align-items: baseline; gap: 9px; white-space: nowrap; }
.az-brand .mark {
  font-family: 'Cormorant Garamond', serif; font-size: 1.85rem; font-weight: 700;
  color: var(--azul-night); letter-spacing: .02em; line-height: 1;
}
.az-brand .sub {
  font-size: .61rem; letter-spacing: .30em; font-weight: 800; color: var(--azul-ocean);
  text-transform: uppercase;
}
.az-brand .by { font-size: .59rem; letter-spacing: .12em; color: var(--azul-muted); text-transform: uppercase; }
.az-utility { display: flex; align-items: center; gap: 7px; flex-wrap: wrap; justify-content: flex-end; }
.az-chip {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 10px; border-radius: 999px; border: 1px solid var(--azul-line);
  background: color-mix(in srgb, var(--azul-surface) 88%, transparent);
  color: var(--azul-ink); font-size: .72rem; font-weight: 700;
}
.az-chip:hover { border-color: var(--azul-turquoise); color: var(--azul-ocean); }
.az-chip.active { background: var(--azul-night); color: var(--azul-surface); border-color: var(--azul-night); }
.az-chip .cart-count {
  display: inline-grid; place-items: center; min-width: 19px; height: 19px; padding: 0 5px;
  border-radius: 999px; background: var(--azul-terracotta); color: #fff; font-size: .66rem;
}
.az-nav {
  display: flex; gap: 5px; overflow-x: auto; scrollbar-width: none;
  padding: 10px 0 16px 0; margin-bottom: 8px; border-bottom: 1px solid var(--azul-line);
}
.az-nav::-webkit-scrollbar { display: none; }
.az-nav a {
  flex: 0 0 auto; padding: 8px 12px; border-radius: 999px; color: var(--azul-muted);
  font-size: .78rem; font-weight: 700; white-space: nowrap;
}
.az-nav a:hover { background: var(--azul-surface-2); color: var(--azul-night); }
.az-nav a.active { background: var(--azul-night); color: var(--azul-surface); }
.az-pro { border: 1px solid var(--azul-line); }

/* --------------------------------------------------------------- hero */
.az-hero {
  position: relative; min-height: 510px; border-radius: 32px; overflow: hidden;
  box-shadow: var(--azul-shadow); isolation: isolate;
  background: linear-gradient(140deg, #0B1F3A, #0E6BA8 52%, #14B8A6);
  display: flex; align-items: flex-end;
}
.az-hero-art { position: absolute; inset: 0; z-index: -1; }
.az-hero-art svg { width: 100%; height: 100%; object-fit: cover; animation: azulKen 22s ease-in-out infinite alternate; }
.az-hero::after {
  content: ""; position: absolute; inset: 0; z-index: 0;
  background: linear-gradient(90deg, rgba(6,20,40,.80) 0%, rgba(6,20,40,.44) 48%, rgba(6,20,40,.06) 100%),
              linear-gradient(0deg, rgba(6,20,40,.55), transparent 45%);
}
.az-hero-copy { position: relative; z-index: 1; padding: clamp(28px, 6vw, 62px); max-width: 780px; color: #fff; }
.az-hero-copy .eyebrow {
  display: inline-flex; align-items: center; gap: 8px; font-size: .72rem; font-weight: 800;
  letter-spacing: .18em; text-transform: uppercase; color: #CFFAF1;
}
.az-hero-copy h1 { color: #fff; margin: 12px 0 12px 0; }
.az-hero-copy p { color: rgba(255,255,255,.88); font-size: clamp(.95rem, 1.4vw, 1.12rem); max-width: 620px; }
.az-hero-actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 22px; }
.az-btn {
  display: inline-flex; align-items: center; gap: 8px; padding: 12px 18px; border-radius: 999px;
  font-size: .82rem; font-weight: 800; transition: transform .2s ease, box-shadow .2s ease;
}
.az-btn:hover { transform: translateY(-2px); }
.az-btn.primary { background: #fff; color: #0B1F3A; box-shadow: 0 14px 30px rgba(0,0,0,.22); }
.az-btn.ghost { color: #fff; border: 1px solid rgba(255,255,255,.40); background: rgba(255,255,255,.08); backdrop-filter: blur(8px); }
.az-hero-weather {
  display: flex; gap: 8px; flex-wrap: wrap; margin-top: 24px;
}
.az-weather-pill {
  display: inline-flex; flex-direction: column; gap: 1px; padding: 9px 13px; border-radius: 14px;
  background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.16); color: #fff;
  backdrop-filter: blur(10px); min-width: 104px;
}
.az-weather-pill b { font-size: .9rem; }
.az-weather-pill span { font-size: .62rem; letter-spacing: .10em; text-transform: uppercase; opacity: .78; }
.az-demo-ribbon {
  position: absolute; top: 18px; right: 18px; z-index: 2;
  background: rgba(11,31,58,.72); border: 1px solid rgba(255,255,255,.22); color: #fff;
  padding: 5px 10px; border-radius: 999px; font-size: .62rem; font-weight: 800; letter-spacing: .12em;
  backdrop-filter: blur(8px);
}

/* -------------------------------------------------------------- section */
.az-section-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; margin: 48px 0 18px; }
.az-section-head h2 { margin: 0; }
.az-section-head p { margin: 4px 0 0; color: var(--azul-muted); font-size: .88rem; }
.az-kicker {
  display: inline-block; color: var(--azul-ocean); font-size: .66rem; font-weight: 800;
  letter-spacing: .18em; text-transform: uppercase; margin-bottom: 4px;
}
.az-link { font-size: .78rem; font-weight: 800; white-space: nowrap; }

/* --------------------------------------------------------------- cards */
.az-grid { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 18px; }
.az-grid.two { grid-template-columns: repeat(2, minmax(0,1fr)); }
.az-card {
  display: flex; flex-direction: column; background: var(--azul-surface); border: 1px solid var(--azul-line);
  border-radius: var(--azul-radius); overflow: hidden; box-shadow: var(--azul-shadow-soft);
  transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease;
  color: var(--azul-ink); min-height: 100%;
}
.az-card:hover { transform: translateY(-4px); box-shadow: var(--azul-shadow); border-color: rgba(20,184,166,.45); color: var(--azul-ink); }
.az-cover { position: relative; aspect-ratio: 16/10; overflow: hidden; background: var(--azul-surface-2); }
.az-cover svg { width: 100%; height: 100%; display: block; transition: transform .5s ease; }
.az-card:hover .az-cover svg { transform: scale(1.035); }
.az-cover .badge { position: absolute; top: 12px; left: 12px; display: flex; gap: 6px; flex-wrap: wrap; }
.az-badge {
  display: inline-flex; align-items: center; gap: 4px; padding: 5px 9px; border-radius: 999px;
  font-size: .62rem; font-weight: 800; letter-spacing: .02em; backdrop-filter: blur(8px);
}
.az-badge.demo { background: rgba(11,31,58,.68); color: #fff; border: 1px solid rgba(255,255,255,.25); }
.az-badge.popular { background: rgba(217,102,58,.92); color: #fff; }
.az-badge.family { background: rgba(76,122,74,.92); color: #fff; }
.az-badge.favorite { background: rgba(245,183,0,.95); color: #0B1F3A; }
.az-badge.verified { background: rgba(20,184,166,.14); color: var(--azul-ocean); border: 1px solid rgba(20,184,166,.28); }
.az-badge.status { background: var(--azul-surface-2); color: var(--azul-ink); }
.az-card-body { padding: 16px 17px 17px; display: flex; flex-direction: column; gap: 7px; flex: 1; }
.az-card-kind { color: var(--azul-ocean); font-size: .62rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }
.az-card-title { font-family: 'Cormorant Garamond', serif; font-size: 1.42rem; line-height: 1.08; color: var(--azul-night); }
.az-card-desc { color: var(--azul-muted); font-size: .78rem; line-height: 1.45; min-height: 2.2em; }
.az-meta { display: flex; gap: 10px; flex-wrap: wrap; color: var(--azul-muted); font-size: .69rem; }
.az-card-foot { margin-top: auto; padding-top: 8px; display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.az-price { font-size: .76rem; font-weight: 800; color: var(--azul-night); }
.az-price small { display: block; color: var(--azul-muted); font-weight: 500; font-size: .62rem; }
.az-arrow { color: var(--azul-turquoise); font-weight: 800; font-size: .9rem; }
.az-stars { color: var(--azul-gold); letter-spacing: .06em; font-size: .72rem; white-space: nowrap; }
.az-stars .empty { color: color-mix(in srgb, var(--azul-muted) 35%, transparent); }
.az-rating-line { display: flex; align-items: center; gap: 7px; color: var(--azul-muted); font-size: .7rem; }

/* ---------------------------------------------------------------- vibes */
.az-vibes { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 12px; }
.az-vibe {
  display: flex; flex-direction: column; gap: 8px; padding: 18px 16px; border-radius: 20px;
  background: var(--azul-surface); border: 1px solid var(--azul-line); color: var(--azul-ink);
  box-shadow: var(--azul-shadow-soft); transition: transform .2s ease, border-color .2s ease;
}
.az-vibe:hover { transform: translateY(-3px); border-color: var(--azul-turquoise); color: var(--azul-ink); }
.az-vibe .ico { font-size: 1.4rem; }
.az-vibe b { font-size: .83rem; }
.az-vibe span { color: var(--azul-muted); font-size: .62rem; }
.az-vibe:nth-child(8n+1) { background: linear-gradient(145deg, color-mix(in srgb, var(--azul-ocean) 10%, var(--azul-surface)), var(--azul-surface)); }
.az-vibe:nth-child(8n+2) { background: linear-gradient(145deg, color-mix(in srgb, var(--azul-sand) 55%, var(--azul-surface)), var(--azul-surface)); }
.az-vibe:nth-child(8n+3) { background: linear-gradient(145deg, color-mix(in srgb, var(--azul-terracotta) 10%, var(--azul-surface)), var(--azul-surface)); }
.az-vibe:nth-child(8n+4) { background: linear-gradient(145deg, color-mix(in srgb, var(--azul-argan) 10%, var(--azul-surface)), var(--azul-surface)); }

/* -------------------------------------------------------------- reviews */
.az-review {
  background: var(--azul-surface); border: 1px solid var(--azul-line); border-radius: 20px;
  padding: 18px; box-shadow: var(--azul-shadow-soft); height: 100%;
}
.az-review-head { display: flex; justify-content: space-between; gap: 10px; align-items: flex-start; }
.az-review-author { font-weight: 800; font-size: .8rem; }
.az-review-date { color: var(--azul-muted); font-size: .64rem; }
.az-review p { font-size: .82rem; line-height: 1.55; margin: 10px 0; }
.az-review .response {
  background: var(--azul-surface-2); border-left: 3px solid var(--azul-turquoise);
  border-radius: 0 12px 12px 0; padding: 9px 11px; font-size: .73rem; color: var(--azul-muted);
}
.az-rating-big { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.az-rating-big .value { font-family: 'Cormorant Garamond', serif; font-size: 3rem; line-height: 1; color: var(--azul-night); }
.az-dist { display: flex; gap: 7px; align-items: center; font-size: .65rem; color: var(--azul-muted); }
.az-dist .bar { flex: 1; height: 5px; background: var(--azul-line); border-radius: 999px; overflow: hidden; }
.az-dist .bar span { display: block; height: 100%; background: var(--azul-gold); border-radius: 999px; }

/* -------------------------------------------------------------- details */
.az-detail-hero {
  display: grid; grid-template-columns: 1.1fr .9fr; gap: 22px; align-items: stretch;
  margin-bottom: 26px;
}
.az-detail-art { min-height: 360px; border-radius: 30px; overflow: hidden; box-shadow: var(--azul-shadow); }
.az-detail-art svg { width: 100%; height: 100%; display: block; }
.az-detail-copy {
  background: var(--azul-surface); border: 1px solid var(--azul-line); border-radius: 30px;
  padding: 28px; box-shadow: var(--azul-shadow-soft); display: flex; flex-direction: column; gap: 10px;
}
.az-detail-copy h1 { font-size: clamp(2.2rem, 4vw, 3.4rem); margin: 2px 0 4px; }
.az-detail-copy .lead { color: var(--azul-muted); font-size: .9rem; line-height: 1.55; }
.az-facts { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 8px; margin-top: 8px; }
.az-fact { background: var(--azul-surface-2); border-radius: 14px; padding: 10px 12px; }
.az-fact span { display: block; color: var(--azul-muted); font-size: .59rem; text-transform: uppercase; letter-spacing: .10em; }
.az-fact b { font-size: .79rem; }
.az-gallery { display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 8px; margin: 10px 0 28px; }
.az-gallery div { border-radius: 16px; overflow: hidden; aspect-ratio: 16/9; }
.az-gallery div:first-child { grid-row: span 2; aspect-ratio: auto; }
.az-gallery svg { width: 100%; height: 100%; }
.az-prose { color: var(--azul-ink); font-size: .89rem; line-height: 1.65; }
.az-prose p { color: var(--azul-ink); }
.az-note { background: var(--azul-surface-2); border-radius: 16px; padding: 13px 15px; color: var(--azul-muted); font-size: .74rem; }
.az-chip-row { display: flex; gap: 6px; flex-wrap: wrap; }
.az-pill { background: var(--azul-surface-2); border: 1px solid var(--azul-line); border-radius: 999px; padding: 5px 9px; font-size: .65rem; font-weight: 700; }
.az-empty {
  text-align: center; padding: 60px 20px; border: 1px dashed var(--azul-line); border-radius: 26px;
  background: color-mix(in srgb, var(--azul-surface) 70%, transparent);
}
.az-empty .ico { font-size: 2.4rem; margin-bottom: 8px; }
.az-empty h3 { margin: 0 0 6px; }
.az-empty p { color: var(--azul-muted); font-size: .84rem; }

/* ------------------------------------------------------------- itinerary */
.az-day {
  background: var(--azul-surface); border: 1px solid var(--azul-line); border-radius: 24px;
  padding: 20px; margin-bottom: 14px; box-shadow: var(--azul-shadow-soft);
}
.az-day-head { display: flex; align-items: baseline; justify-content: space-between; gap: 10px; }
.az-day-head h3 { margin: 0; }
.az-day-item { display: flex; gap: 12px; align-items: flex-start; padding: 10px 0; border-bottom: 1px dashed var(--azul-line); }
.az-day-item:last-child { border-bottom: 0; }
.az-day-time { min-width: 54px; font-weight: 800; color: var(--azul-ocean); font-size: .72rem; }
.az-day-item b { font-size: .82rem; }
.az-day-item small { display: block; color: var(--azul-muted); font-size: .67rem; }

/* ---------------------------------------------------------------- misc */
.az-trust { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 14px; margin: 30px 0; }
.az-trust div { background: var(--azul-surface); border: 1px solid var(--azul-line); border-radius: 18px; padding: 16px; font-size: .74rem; color: var(--azul-muted); }
.az-trust b { display: block; color: var(--azul-night); font-size: .82rem; margin-bottom: 3px; }
.az-footer {
  margin-top: 54px; padding: 28px 0 10px; border-top: 1px solid var(--azul-line);
  display: flex; justify-content: space-between; gap: 20px; flex-wrap: wrap; color: var(--azul-muted); font-size: .69rem;
}
.az-footer .brand { font-family: 'Cormorant Garamond', serif; font-size: 1.2rem; color: var(--azul-night); }
.az-lesstext { font-size: .7rem; color: var(--azul-muted); }
.az-admin-head { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-bottom: 4px; }
.az-admin-nav { display: flex; gap: 6px; flex-wrap: wrap; padding-bottom: 12px; border-bottom: 1px solid var(--azul-line); margin-bottom: 18px; }
.az-admin-nav a { padding: 7px 11px; border-radius: 999px; font-size: .72rem; font-weight: 700; color: var(--azul-muted); background: var(--azul-surface); border: 1px solid var(--azul-line); }
.az-admin-nav a.active { background: var(--azul-night); color: var(--azul-surface); border-color: var(--azul-night); }
.az-status { display: inline-flex; padding: 4px 8px; border-radius: 999px; font-size: .62rem; font-weight: 800; }
.az-status.pending { background: #FFF3CD; color: #7A5A00; }
.az-status.confirmed { background: #D9F5EF; color: #0A6B5F; }
.az-status.deposit_received { background: #DDEBFF; color: #0E4C8A; }
.az-status.completed { background: #E4EEDC; color: #3C643A; }
.az-status.cancelled { background: #FBE1DB; color: #94351F; }

@keyframes azulKen { 0% { transform: scale(1) translate3d(0,0,0); } 100% { transform: scale(1.08) translate3d(-1.5%, -1%, 0); } }
@keyframes azulUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
.az-hero-copy, .az-card, .az-day { animation: azulUp .55s ease both; }
@media (prefers-reduced-motion: reduce) {
  .az-hero-art svg, .az-hero-copy, .az-card, .az-day { animation: none !important; transition: none !important; }
}

@media (max-width: 900px) {
  .az-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
  .az-vibes { grid-template-columns: repeat(2, minmax(0,1fr)); }
  .az-detail-hero { grid-template-columns: 1fr; }
  .az-detail-art { min-height: 280px; }
  .az-gallery { grid-template-columns: 1fr 1fr; }
  .az-gallery div:first-child { grid-row: auto; aspect-ratio: 16/9; }
  .az-trust { grid-template-columns: 1fr; }
}
@media (max-width: 620px) {
  .block-container { padding-left: .8rem; padding-right: .8rem; }
  .az-grid { grid-template-columns: 1fr; }
  .az-hero { min-height: 560px; border-radius: 24px; }
  .az-hero-copy { padding: 24px 20px 26px; }
  .az-hero-copy h1 { font-size: 2.5rem; }
  .az-facts { grid-template-columns: 1fr 1fr; }
  .az-detail-copy { padding: 20px; border-radius: 22px; }
  .az-topbar { align-items: flex-start; }
  .az-utility { justify-content: flex-start; }
  .az-nav { padding-bottom: 12px; }
  .az-section-head { align-items: flex-start; flex-direction: column; gap: 6px; }
  .az-footer { flex-direction: column; }
  .az-gallery { grid-template-columns: 1fr; }
}
html[dir="rtl"], html[dir="rtl"] body { font-family: 'Noto Kufi Arabic', 'Manrope', sans-serif; }
html[dir="rtl"] .az-hero-copy, html[dir="rtl"] .az-card-body, html[dir="rtl"] .az-detail-copy, html[dir="rtl"] .az-review { text-align: right; }
html[dir="rtl"] .az-hero::after { background: linear-gradient(270deg, rgba(6,20,40,.80), rgba(6,20,40,.06)); }
html[dir="rtl"] .az-nav { direction: rtl; }
html[dir="rtl"] .az-utility { direction: rtl; }
html[dir="rtl"] .az-price, html[dir="rtl"] .az-card-kind { direction: ltr; }

/* ------------------------------------------------------------- réelles */
.az-cover, .az-detail-art, .az-gallery div { position: relative; }
.az-media { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; z-index: 1; }
.az-gallery div { transition: transform .35s ease, box-shadow .35s ease; }
.az-gallery div:hover { transform: translateY(-2px); box-shadow: var(--azul-shadow-soft); }
.az-badge.photos { background: rgba(11, 31, 58, .78); color: #fff; }
.az-media-credits {
  margin: -14px 0 28px; padding: 10px 14px; border: 1px solid var(--azul-line);
  border-radius: 14px; background: var(--azul-surface); font-size: .68rem; color: var(--azul-muted);
}
.az-media-credits summary { cursor: pointer; font-weight: 700; color: var(--azul-night); }
.az-media-credits .hint { margin: 8px 0; }
.az-media-credits ul { margin: 6px 0 0; padding-left: 18px; display: grid; gap: 3px; }
.az-media-credits a { color: var(--azul-ocean); }
"""


def inject_theme(dark: bool = False, rtl: bool = False) -> None:
    theme = "dark" if dark else "light"
    st.markdown(
        f"""<style>
        html {{ --azul-mode: {theme}; }}
        {BASE_CSS}
        </style>""",
        unsafe_allow_html=True,
    )
    # Streamlit n'exécute pas les scripts intégrés : le thème et la direction
    # sont appliqués uniquement en CSS, sans attribut posé par script.
    if dark:
        st.markdown(
            """<style>
            :root {
              --azul-bg: #0E1523; --azul-surface: #172033; --azul-surface-2: #1D2940;
              --azul-ink: #E8EEF8; --azul-night: #F5F8FD; --azul-muted: #A6B2C8;
              --azul-line: rgba(232,238,248,.12); --azul-sand: #3A3326;
              --azul-shadow: 0 16px 48px rgba(0,0,0,.35); --azul-shadow-soft: 0 8px 24px rgba(0,0,0,.25);
            }
            .stApp { background: radial-gradient(circle at 8% 4%, rgba(20,184,166,.07), transparent 28rem), var(--azul-bg); }
            </style>""",
            unsafe_allow_html=True,
        )
    if rtl:
        st.markdown(
            """<style>
            html, body, .stApp { direction: rtl; }
            .az-topbar, .az-nav, .az-utility { direction: rtl; }
            .az-hero-copy, .az-card-body, .az-detail-copy, .az-review,
            .az-note, .az-day, .az-day-head, .az-section-head { text-align: right; }
            .az-price, .az-card-kind { direction: ltr; }
            </style>""",
            unsafe_allow_html=True,
        )
