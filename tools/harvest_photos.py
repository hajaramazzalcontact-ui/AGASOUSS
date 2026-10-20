"""Récolte complète des photos pour toutes les fiches DÉMO.

Usage : python tools/harvest_photos.py [target]
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402

from src.db.models import CatalogItem  # noqa: E402
from src.db.session import configure_database, get_session  # noqa: E402
from src.services.photos import (  # noqa: E402
    ensure_static_serving,
    harvest_catalog,
    normalize_covers,
    reset_remote_only_media,
    write_manifest,
)


def main() -> None:
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    configure_database()
    ensure_static_serving()
    session = get_session()
    try:
        removed = reset_remote_only_media(session)
        session.commit()
        print(f"Anciens visuels distants retirés : {removed}", flush=True)
        start = time.time()
        added = harvest_catalog(session, target=target, download=True, budget_seconds=2400)
        normalize_covers(session)
        session.commit()
        manifest = write_manifest(session)
        print(f"Photos ajoutées : {added} en {time.time() - start:.0f} s", flush=True)
        print(f"Fiches au manifeste : {len(manifest.get('items', {}))}", flush=True)
        rows = session.scalars(select(CatalogItem).where(CatalogItem.status == "published")).all()
        for item in rows:
            photos = [
                m for m in (item.media or [])
                if m.external_url or (m.storage_path or "").startswith("/app/static")
            ]
            cover = sum(1 for m in photos if m.is_cover)
            print(f"{item.slug}: {len(photos)} photos, {cover} couverture", flush=True)
    finally:
        session.close()


if __name__ == "__main__":
    main()
