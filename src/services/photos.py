"""Photos d'illustration pour toutes les fiches Azul AGADIR.

Objectif : chaque activité, restaurant, hébergement, spot et service de
transport possède une photo de couverture et une galerie (5 à 8 visuels),
téléchargées localement pour un affichage rapide, avec crédit, licence et
page source conservés en base.

Règles de fiabilité respectées :
- Sources exclusivement libres : Wikimedia Commons, licences CC BY,
  CC BY-SA, CC0 ou domaine public. Les licences NC/ND et GNU sont écartées.
- Aucune photo présentée comme celle du lieu exact : la légende indique
  « Photo d'illustration (DÉMO) » et le crédit complet est affiché.
- Idempotent : une fiche déjà illustrée n'est pas dupliquée.
- Un manifeste (`assets/media_manifest.json`) permet de réinstaller les
  mêmes visuels sans dépendre du réseau au démarrage.
- Hors ligne : tout échec réseau est silencieux, les visuels SVG générés
  prennent le relais dans l'interface.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from html import unescape
from io import BytesIO
from pathlib import Path
from typing import Any, Iterable

import requests
from sqlalchemy import select

from src.config import ASSETS_DIR, BASE_DIR
from src.db.models import CatalogItem, CatalogMedia

LOG = logging.getLogger(__name__)

API_URL = "https://commons.wikimedia.org/w/api.php"
API_TIMEOUT = 15
HEADERS = {
    "User-Agent": "AzulAgadirDemo/1.0 (local demonstration; contact: privacy@agadirgo.example)"
}
THROTTLE_SECONDS = 0.12

CACHE_PATH = ASSETS_DIR / "media_cache.json"
MANIFEST_PATH = ASSETS_DIR / "media_manifest.json"
STATIC_MEDIA_DIR = BASE_DIR / "static" / "media"
STATIC_WEB_PREFIX = "/app/static/media"

# Requêtes précises par fiche : c'est ici que se joue la pertinence.
ITEM_QUERIES: dict[str, list[str]] = {
    # --- Activités ---------------------------------------------------------
    "karting": ["kart racing", "go kart circuit", "karting track", "kart driver"],
    "golf": ["golf course green", "golfer swing", "golf bunker", "golf course Morocco"],
    "agadir-oufella": ["Agadir Oufella", "Agadir kasbah", "Agadir panorama", "Agadir hill view"],
    "medina": ["Agadir medina", "Moroccan medina alley", "Moroccan crafts market", "medina Morocco"],
    "dauphins": ["dolphin watching boat", "bottlenose dolphin", "dolphins ocean", "dolphin pod sea"],
    "live-it-maghribi": [
        "Moroccan pottery", "Moroccan embroidery", "zellige tiles", "Moroccan mosaic",
        "Moroccan handicraft", "potter hands wheel",
    ],
    "quad": ["quad bike desert", "ATV dune", "quad biking Morocco", "off road quad"],
    "cheval-dromadaire": [
        "camel ride beach", "dromedary Morocco", "horse riding beach", "camel caravan Morocco",
    ],
    "bowling": ["bowling alley", "bowling pins", "bowling lane", "ten pin bowling"],
    "timlaline": ["sandboarding dune", "sandboard desert", "sand surfing", "dune sand board"],
    "crocoparc": [
        "Nile crocodile", "crocodile zoo", "crocodile feeding", "crocodile Morocco",
        "Crocodylus niloticus", "crocodile close up",
    ],
    "villa-taelaimoun": ["Moroccan garden", "olive grove Morocco", "villa garden", "Moroccan courtyard garden"],
    "pique-nique": ["beach picnic", "picnic basket beach", "picnic blanket family", "picnic outdoors"],
    "sortie-plage": ["beach games family", "beach volleyball", "sandcastle children", "Agadir beach"],
    "art-studio": ["painting studio", "canvas painting workshop", "art class painting", "paint palette brushes"],
    "musee-agadir": ["museum interior", "Agadir museum", "Moroccan heritage museum", "museum exhibition"],
    "aghroud": ["Aghroud Morocco", "Moroccan coastal village", "colorful village Morocco", "fishing village Morocco"],
    "anza-dinosaures": ["dinosaur statue", "dinosaur park", "Anza Morocco", "T-Rex sculpture"],
    "escape-zone": ["escape room", "escape room puzzle", "team puzzle game", "padlock puzzle"],
    "sortie-bateau": ["boat trip coast", "motorboat sea", "sailboat Morocco", "boat deck ocean"],
    "excursions-alentours": ["Taghazout Morocco", "Imsouane bay", "Tamraght Morocco", "coastal road Morocco"],
    # --- Restaurants -------------------------------------------------------
    "restaurant-01": ["Moroccan tagine", "Moroccan riad restaurant", "Moroccan mint tea", "couscous Morocco"],
    "restaurant-02": ["seafood harbour", "grilled fish plate", "port restaurant", "seafood platter"],
    "restaurant-03": ["Moroccan mint tea", "coffee cup cafe", "Moroccan cafe", "argan oil Morocco"],
    "restaurant-04": ["Moroccan mezze", "Moroccan salad", "tagine table", "Moroccan bread"],
    "restaurant-05": ["olive salad", "mediterranean salad", "olive oil olives", "vegetarian plate"],
    "restaurant-06": ["seafood platter", "oysters plate", "ocean restaurant", "fish dish"],
    "restaurant-07": ["couscous Morocco", "Moroccan couscous vegetables", "Moroccan restaurant interior", "harira soup"],
    "restaurant-08": ["seafood sunset", "terrace restaurant sea", "Taghazout restaurant", "fish grill"],
    "restaurant-09": ["fish tagine", "Imsouane Morocco", "seafood Morocco", "fisherman boat"],
    "restaurant-10": ["healthy bowl food", "vegetarian cafe", "breakfast brunch", "smoothie bowl"],
    "restaurant-11": ["grilled fish", "beach restaurant sunset", "Moroccan grill", "seafood barbecue"],
    "restaurant-12": ["pizza restaurant", "pasta dish", "corniche Agadir", "italian restaurant"],
    "restaurant-13": ["Moroccan spices market", "ras el hanout", "spice shop Morocco", "spices bowls"],
    "restaurant-14": ["barbecue grill", "grilled meat", "grill restaurant", "dinosaur statue"],
    "restaurant-15": ["Moroccan street food", "souk food stall", "Moroccan pastry", "street market food"],
    "restaurant-16": ["seafood restaurant", "ocean view table", "grilled prawns", "Agadir restaurant"],
    "restaurant-17": ["pastilla Morocco", "Moroccan pastry", "riad restaurant", "Moroccan dessert"],
    "restaurant-18": ["Moroccan table", "Souss Morocco", "Moroccan salad plate", "restaurant terrace Morocco"],
    "restaurant-19": ["surf cafe", "coffee breakfast", "brunch plate", "coffee shop interior"],
    "restaurant-20": ["paella seafood", "paella pan", "spanish restaurant", "seafood rice dish"],
    "restaurant-21": ["vegetarian platter", "vegan bowl", "nomad food", "vegetables dish"],
    "restaurant-22": ["family meal table", "Moroccan family restaurant", "shared meal", "grilled fish family"],
    "restaurant-23": ["coffee sunset cafe", "Imsouane surf", "cafe sea view", "sunset coffee"],
    "restaurant-24": ["argan oil food", "argan nuts", "Moroccan breakfast", "argan tree"],
    "restaurant-25": ["marina restaurant", "grilled meat platter", "Agadir marina", "restaurant grill"],
    # --- Hébergements ------------------------------------------------------
    "hebergement-01": ["Moroccan riad courtyard", "riad Morocco interior", "riad patio fountain", "riad pool"],
    "hebergement-02": ["hotel pool", "hotel room modern", "hotel lobby Morocco", "hotel sea view"],
    "hebergement-03": ["surf house", "surfboards rack", "surf hostel", "Taghazout surf"],
    "hebergement-04": ["beach lodge ocean", "terrace sea view", "Tamraght Morocco", "coastal guesthouse"],
    "hebergement-05": ["Imsouane Morocco", "blue house Morocco", "guesthouse Morocco", "Imsouane bay"],
    "hebergement-06": ["beach camp tents", "glamping tent beach", "camping coast Morocco", "tent sunset sea"],
    "hebergement-07": ["Founty Agadir", "hotel Agadir", "hotel room suite", "sunset hotel"],
    "hebergement-08": ["Marrakech riad", "riad garden courtyard", "Moroccan riad door", "riad bedroom"],
    "hebergement-09": ["Taghazout bay", "lodge Morocco coast", "hotel Taghazout", "sea view lodge"],
    "hebergement-10": ["surf villa", "villa swimming pool", "villa terrace Morocco", "Tamraght surf"],
    "hebergement-11": ["surf camp", "surf school beach", "surf hostel dorm", "surfboards beach"],
    "hebergement-12": ["Aghroud Morocco", "village rooms Morocco", "guest room Morocco", "coastal village house"],
    "hebergement-13": ["Agadir city hotel", "hotel Agadir centre", "hotel facade Morocco", "city hotel room"],
    "hebergement-14": ["garden riad Morocco", "Souss garden", "riad courtyard plants", "Moroccan garden riad"],
    "hebergement-15": ["Agadir corniche", "beach hotel Morocco", "hotel pool sea", "beachfront hotel"],
    # --- Spots et plages ---------------------------------------------------
    "spot-01": ["Agadir beach", "Agadir bay", "Agadir promenade", "Agadir beach sunset"],
    "spot-02": ["Taghazout beach", "Taghazout Morocco", "Taghazout surf", "Taghazout sunset"],
    "spot-03": ["Aghroud beach", "Aghroud Morocco", "beach Morocco coast", "Atlantic beach Morocco"],
    "spot-04": ["Tamraght beach", "Tamraght Morocco", "surf beach Morocco", "Morocco surf spot"],
    "spot-05": ["Imsouane bay", "Imsouane Morocco", "Imsouane surf", "Imsouane beach"],
    "spot-06": ["Tifnit Morocco", "Tifnit beach", "fishing village beach Morocco", "Atlantic coast Morocco"],
    "spot-07": ["Anza Morocco", "Anza beach", "Agadir harbour", "fishing port Morocco"],
    "spot-08": ["Imourane beach", "Imourane Morocco", "Taghazout bay beach", "beach dunes Morocco"],
    # --- Transport ---------------------------------------------------------
    "tour-groupe-taghazout": ["minibus Morocco", "tour van Morocco", "coastal road Morocco", "tour group travel"],
    "tour-prive-imsouane": ["minivan road Morocco", "Imsouane road", "4x4 Morocco coast", "private tour car"],
    "taxi-demande": ["taxi Morocco", "petit taxi Morocco", "taxi street Morocco", "taxi cab"],
    "taxi-demi-journee": ["driver car Morocco", "chauffeur car", "car interior Morocco", "car driving coast"],
    "taxi-journee": ["Toyota Land Cruiser Morocco", "4x4 Morocco road", "car trip Morocco", "driver tour"],
    "transfert-aeroport": ["Agadir airport", "airport shuttle van", "luggage car", "airport terminal"],
}

# Pools de secours par type, pour compléter une galerie.
KIND_QUERIES: dict[str, list[str]] = {
    "activity": [
        "Morocco landscape", "Agadir Morocco", "Atlantic coast Morocco", "Moroccan culture",
        "Souss Massa", "dunes Morocco", "beach activity Morocco", "outdoor Morocco",
    ],
    "restaurant": [
        "Moroccan tagine", "Moroccan food", "Moroccan mint tea", "seafood Morocco",
        "Moroccan pastry", "restaurant Morocco", "Moroccan bread", "coffee Morocco",
    ],
    "accommodation": [
        "Moroccan riad", "hotel pool", "guesthouse Morocco", "hotel room",
        "Moroccan architecture", "riad courtyard", "hotel terrace", "Morocco hotel",
    ],
    "spot": [
        "Agadir beach", "Morocco beach", "Atlantic coast Morocco", "Taghazout",
        "Agadir bay", "Morocco coast sunset", "beach Morocco", "sea Morocco",
    ],
    "transport": [
        "Morocco road", "minivan Morocco", "Agadir Morocco street", "car Morocco",
        "bus Morocco", "coastal road", "airport Morocco", "vehicle interior",
    ],
}

# Traductions de légende.
CAPTION = {
    "photo": {
        "fr": "Photo d'illustration (DÉMO)",
        "en": "Illustrative photo (DEMO)",
        "ar": "صورة توضيحية (تجريبي)",
        "es": "Foto ilustrativa (DEMO)",
    }
}

_session_cache: dict[str, list[dict[str, Any]]] | None = None


# --------------------------------------------------------------------------
# Utilitaires JSON et licences
# --------------------------------------------------------------------------
def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_json(path: Path, data: dict) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception as exc:
        LOG.debug("Manifeste non écrit (%s): %s", path, exc)


def _cache() -> dict[str, list[dict[str, Any]]]:
    global _session_cache
    if _session_cache is None:
        _session_cache = _load_json(CACHE_PATH) or {}
    return _session_cache


def _license_ok(short: str) -> bool:
    low = (short or "").lower()
    if not low:
        return False
    banned = ("nc", "nd", "gfdl", "gnu", "non commercial", "noncommercial")
    if any(b in low for b in banned):
        return False
    accepted = ("cc by", "cc-by", "cc0", "public domain", "domaine public", "pd-", "pdm")
    return any(a in low for a in accepted)


def _clean_author(meta: dict) -> str:
    raw = (meta.get("Artist", {}) or {}).get("value") or ""
    return re.sub(r"<[^>]+>", "", unescape(raw)).strip()[:80]


def _slug_of(item: CatalogItem) -> str:
    return str(item.slug or f"item-{item.id}")


def _title(item: CatalogItem) -> str:
    if isinstance(item.name, dict):
        return item.name.get("fr") or item.name.get("en") or _slug_of(item)
    return str(item.name or _slug_of(item))


# --------------------------------------------------------------------------
# Wikimedia Commons
# --------------------------------------------------------------------------
def _fetch_candidates(term: str, cache: dict, limit: int = 20) -> list[dict[str, Any]]:
    """Candidats libres pour un terme, avec mise en cache disque."""
    if term in cache:
        return cache[term]
    results: list[dict[str, Any]] = []
    try:
        response = requests.get(
            API_URL,
            params={
                "action": "query", "format": "json",
                "generator": "search", "gsrsearch": f"{term} filetype:bitmap",
                "gsrnamespace": 6, "gsrlimit": str(limit),
                "prop": "imageinfo",
                "iiprop": "url|mime|size|extmetadata|sha1",
                "iiurlwidth": "1400",
            },
            headers=HEADERS,
            timeout=API_TIMEOUT,
        )
        response.raise_for_status()
        pages = (response.json().get("query") or {}).get("pages") or {}
        for page in sorted(pages.values(), key=lambda p: p.get("index", 99)):
            info = (page.get("imageinfo") or [None])[0]
            if not info:
                continue
            if info.get("mime") not in {"image/jpeg", "image/png", "image/webp"}:
                continue
            if int(info.get("width") or 0) < 900:
                continue
            meta = info.get("extmetadata") or {}
            license_name = ((meta.get("LicenseShortName", {}) or {}).get("value") or "").strip()
            if not _license_ok(license_name):
                continue
            url = info.get("thumburl") or info.get("url")
            if not url:
                continue
            results.append({
                "external_url": url,
                "origin_url": info.get("url"),
                "source_url": info.get("descriptionurl") or "https://commons.wikimedia.org",
                "credit": f"{unescape(page.get('title', '').replace('File:', ''))} — {_clean_author(meta) or 'Auteur inconnu'}",
                "license_name": license_name,
                "sha1": info.get("sha1") or hashlib.sha1(url.encode()).hexdigest(),
                "title": page.get("title", ""),
                "width": int(info.get("width") or 0),
                "height": int(info.get("height") or 0),
            })
    except Exception as exc:
        LOG.debug("Commons indisponible pour '%s': %s", term, exc)
    cache[term] = results
    return results


def _save_cache(cache: dict) -> None:
    _save_json(CACHE_PATH, cache)


# --------------------------------------------------------------------------
# Téléchargement local servi par Streamlit (`static/media`)
# --------------------------------------------------------------------------
def _download(url: str, slug: str, key: str) -> tuple[str, str] | None:
    """Télécharge et redimensionne une image. Retourne (chemin complet, miniature)."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=API_TIMEOUT)
        response.raise_for_status()
        from PIL import Image

        image = Image.open(BytesIO(response.content))
        if image.mode in ("RGBA", "LA", "P"):
            rgba = image.convert("RGBA")
            background = Image.new("RGB", rgba.size, (251, 248, 242))
            background.paste(rgba, mask=rgba.split()[-1])
            image = background
        else:
            image = image.convert("RGB")

        folder = STATIC_MEDIA_DIR / slug
        folder.mkdir(parents=True, exist_ok=True)
        full = image.copy()
        full.thumbnail((1400, 1400))
        thumb = image.copy()
        thumb.thumbnail((680, 680))
        full_name = f"{key}.jpg"
        thumb_name = f"t_{key}.jpg"
        full.save(folder / full_name, "JPEG", quality=84, optimize=True)
        thumb.save(folder / thumb_name, "JPEG", quality=80, optimize=True)
        return (
            f"{STATIC_WEB_PREFIX}/{slug}/{full_name}",
            f"{STATIC_WEB_PREFIX}/{slug}/{thumb_name}",
        )
    except Exception as exc:
        LOG.debug("Téléchargement impossible (%s): %s", url, exc)
        return None


# --------------------------------------------------------------------------
# Récolte
# --------------------------------------------------------------------------
def _existing_urls(item: CatalogItem) -> set[str]:
    return {
        getattr(m, "external_url", None)
        for m in (item.media or [])
        if getattr(m, "external_url", None)
    }


def _has_local(item: CatalogItem) -> bool:
    return any((getattr(m, "storage_path", "") or "").startswith("/app/static") for m in (item.media or []))


def _terms_for(item: CatalogItem) -> list[str]:
    slug = _slug_of(item)
    terms = list(ITEM_QUERIES.get(slug, []))
    if len(terms) < 4:
        pool = KIND_QUERIES.get(item.kind, KIND_QUERIES["activity"])
        offset = int(item.id or 0) % max(1, len(pool))
        terms += pool[offset:] + pool[:offset]
    return terms


def harvest_item(
    session,
    item: CatalogItem,
    target: int = 6,
    download: bool = True,
    used: set[str] | None = None,
) -> int:
    """Complète une fiche jusqu'à `target` photos. Retourne le nombre ajouté.

    Deux passes : d'abord des visuels uniques (variété maximale), puis, si la
    fiche reste incomplète, une seconde passe autorisant la réutilisation —
    jamais deux fois la même photo dans une même galerie.
    """
    existing = _existing_urls(item)

    def fill(strict: bool, seen_local: set[str]) -> int:
        added = 0
        cache = _cache()
        for term in _terms_for(item):
            if len(existing) + added >= target:
                break
            for candidate in _fetch_candidates(term, cache):
                if len(existing) + added >= target:
                    break
                key = candidate.get("sha1") or candidate["external_url"]
                if candidate["external_url"] in existing or key in seen_local:
                    continue
                if strict and used is not None and key in used:
                    continue
                storage = thumbnail = None
                if download:
                    saved = _download(candidate["external_url"], _slug_of(item), key[:12])
                    if saved:
                        storage, thumbnail = saved
                seen_local.add(key)
                if used is not None:
                    used.add(key)
                existing.add(candidate["external_url"])
                first = len(existing) == 1
                session.add(CatalogMedia(
                    catalog_id=item.id,
                    catalog=item,  # synchronise la collection item.media
                    kind="image",
                    storage_path=storage,
                    thumbnail_path=thumbnail,
                    external_url=candidate["external_url"],
                    caption=dict(CAPTION["photo"]),
                    credit=(candidate["credit"] or "")[:178],
                    source_url=(candidate.get("source_url") or "")[:500],
                    license_name=(candidate.get("license_name") or "")[:118],
                    rights_basis="license",
                    is_cover=first,
                    sort_order=added,
                    is_demo=False,
                ))
                added += 1
        _save_cache(cache)
        time.sleep(THROTTLE_SECONDS)
        return added

    added = fill(strict=True, seen_local=set())
    if len(existing) < target:
        added += fill(strict=False, seen_local=set())
    return added


def harvest_catalog(
    session,
    target: int = 6,
    download: bool = True,
    budget_seconds: float = 900.0,
    limit: int | None = None,
) -> int:
    """Illustre toutes les fiches publiées. Idempotent, borné dans le temps."""
    deadline = time.monotonic() + max(10.0, budget_seconds)
    added = 0
    reused_titles: set[str] = set()
    items = session.scalars(
        select(CatalogItem).where(CatalogItem.status == "published").order_by(CatalogItem.id)
    ).all()
    if limit:
        items = items[:limit]
    # Priorité aux fiches totalement nues : une couverture pour tout le
    # catalogue avant d'enrichir les galeries existantes au-delà de 3 photos.
    complete = [i for i in items if len(_existing_urls(i)) >= 3]
    naked = [i for i in items if not _existing_urls(i)]
    filling = [i for i in items if 0 < len(_existing_urls(i)) < 3]
    for item in naked + filling + complete:
        if time.monotonic() >= deadline:
            LOG.info("Budget de récolte photo atteint (%s visuels ajoutés).", added)
            break
        added += harvest_item(session, item, target=target, download=download, used=reused_titles)
        # Commit par fiche : libère le verrou SQLite entre deux fiches pour
        # ne pas bloquer les autres sessions (app en cours de rendu, tests).
        session.commit()
    normalize_covers(session)
    session.commit()
    write_manifest(session)
    return added


# --------------------------------------------------------------------------
# Nettoyage et couverture
# --------------------------------------------------------------------------
def reset_remote_only_media(session) -> int:
    """Supprime les anciens visuels distants non vérifiés, garde les locaux."""
    removed = 0
    rows = session.scalars(select(CatalogMedia)).all()
    for media in rows:
        if not media.external_url:
            continue
        local = (media.storage_path or "").startswith("/app/static")
        if local:
            continue
        session.delete(media)
        removed += 1
    session.flush()
    return removed


def normalize_covers(session) -> int:
    """Garantit une seule couverture par fiche, en privilégiant le local."""
    fixed = 0
    items = session.scalars(select(CatalogItem).where(CatalogItem.status == "published")).all()
    for item in items:
        rows = [
            m for m in (item.media or [])
            if getattr(m, "external_url", None) or (getattr(m, "storage_path", "") or "").startswith("/app/static")
        ]
        if not rows:
            continue
        rows.sort(key=lambda m: (
            not (getattr(m, "storage_path", "") or "").startswith("/app/static"),
            int(getattr(m, "sort_order", 0) or 0),
            int(getattr(m, "id", 0) or 0),
        ))
        best = rows[0]
        for media in (item.media or []):
            wanted = media is best
            if bool(media.is_cover) != wanted:
                media.is_cover = wanted
                fixed += 1
    session.flush()
    return fixed


# --------------------------------------------------------------------------
# Manifeste et application hors réseau
# --------------------------------------------------------------------------
def write_manifest(session) -> dict:
    """Écrit le manifeste des médias par slug (réinstallation rapide)."""
    items = session.scalars(select(CatalogItem).where(CatalogItem.status == "published")).all()
    payload: dict[str, Any] = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "items": {}}
    for item in items:
        rows = [
            m for m in (item.media or [])
            if getattr(m, "external_url", None) or (getattr(m, "storage_path", "") or "").startswith("/app/static")
        ]
        if not rows:
            continue
        payload["items"][_slug_of(item)] = [
            {
                "external_url": m.external_url,
                "storage_path": m.storage_path,
                "thumbnail_path": m.thumbnail_path,
                "caption": m.caption,
                "credit": m.credit,
                "source_url": m.source_url,
                "license_name": m.license_name,
                "is_cover": bool(m.is_cover),
                "sort_order": int(m.sort_order or 0),
            }
            for m in rows
        ]
    _save_json(MANIFEST_PATH, payload)
    return payload


def apply_manifest(session, target: int = 6) -> int:
    """Applique le manifeste local : instantané, sans réseau."""
    manifest = _load_json(MANIFEST_PATH)
    mapping = manifest.get("items") or {}
    if not mapping:
        return 0
    added = 0
    items = session.scalars(select(CatalogItem).where(CatalogItem.status == "published")).all()
    for item in items:
        rows = mapping.get(_slug_of(item)) or []
        if not rows:
            continue
        existing = _existing_urls(item)
        has_cover = any(getattr(m, "is_cover", False) for m in (item.media or []))
        for index, row in enumerate(rows):
            url = row.get("external_url") or row.get("storage_path")
            if not url or url in existing:
                continue
            if len(existing) >= target:
                break
            session.add(CatalogMedia(
                catalog_id=item.id,
                catalog=item,  # synchronise la collection item.media
                kind="image",
                storage_path=row.get("storage_path"),
                thumbnail_path=row.get("thumbnail_path"),
                external_url=row.get("external_url"),
                caption=row.get("caption") or dict(CAPTION["photo"]),
                credit=row.get("credit"),
                source_url=row.get("source_url"),
                license_name=row.get("license_name"),
                rights_basis="license",
                is_cover=(not has_cover and index == 0),
                sort_order=int(row.get("sort_order") or index),
                is_demo=False,
            ))
            existing.add(url)
            added += 1
    normalize_covers(session)
    session.flush()
    return added


def ensure_static_serving() -> None:
    """Garantit l'existence du dossier servi par Streamlit."""
    STATIC_MEDIA_DIR.mkdir(parents=True, exist_ok=True)


def apply_real_photos(session, max_media_per_item: int = 6, budget_seconds: float = 120.0) -> int:
    """Point d'entrée applicatif : manifeste d'abord, réseau ensuite.

    Le manifeste rend le démarrage instantané et fonctionne hors ligne.
    Si une fiche reste sans photo, on tente une récolte réseau brève.
    """
    ensure_static_serving()
    added = apply_manifest(session, target=max_media_per_item)
    session.commit()
    if added:
        return added
    return harvest_catalog(
        session,
        target=max_media_per_item,
        download=True,
        budget_seconds=budget_seconds,
    )
