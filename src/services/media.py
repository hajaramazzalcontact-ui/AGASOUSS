"""Téléversement et droits des médias."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image
from sqlalchemy.orm import Session

from src.config import BASE_DIR
from src.db.base import utcnow
from src.db.models import CatalogMedia


class MediaError(ValueError):
    pass


def validate_rights(rights_basis: str, credit: str, source_url: str = "") -> None:
    if rights_basis not in {"owner", "written_consent", "license", "demo"}:
        raise MediaError("La source et les droits du média sont obligatoires.")
    if not (credit or "").strip():
        raise MediaError("Le crédit du média est obligatoire.")
    if rights_basis in {"written_consent", "license"} and not source_url.strip():
        raise MediaError("La référence de l'accord ou de la licence est obligatoire.")


def save_image(
    file_bytes: bytes,
    original_name: str,
    *,
    catalog_id: int,
    rights_basis: str,
    credit: str,
    source_url: str = "",
    caption: str = "",
    sort_order: int = 0,
    is_cover: bool = False,
) -> Path:
    validate_rights(rights_basis, credit, source_url)
    if not file_bytes:
        raise MediaError("Fichier vide.")
    try:
        image = Image.open(BytesIO(file_bytes))
        image.verify()
        image = Image.open(BytesIO(file_bytes)).convert("RGB")
    except Exception as exc:
        raise MediaError("Format d'image non reconnu.") from exc

    # Miniature compressée et version d'affichage raisonnable.
    max_side = 1600
    image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    # Dossier servi par Streamlit sur /app/static/media/... : affichage rapide.
    folder = BASE_DIR / "static" / "media" / "uploads" / str(catalog_id)
    folder.mkdir(parents=True, exist_ok=True)
    suffix = ".jpg"
    base = f"{utcnow().strftime('%Y%m%d%H%M%S')}-{sort_order}"
    full_path = folder / f"{base}{suffix}"
    thumb_path = folder / f"{base}-thumb{suffix}"
    image.save(full_path, format="JPEG", quality=84, optimize=True)
    thumb = image.copy()
    thumb.thumbnail((520, 520), Image.Resampling.LANCZOS)
    thumb.save(thumb_path, format="JPEG", quality=76, optimize=True)
    return full_path
