"""Audit de couverture photo : 1 couverture minimum et galerie suffisante."""
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "data" / "azul_demo.db"
c = sqlite3.connect(DB)
c.row_factory = sqlite3.Row

rows = c.execute("""
    select i.id, i.kind, i.slug, i.name,
      (select count(*) from catalog_media m where m.catalog_id = i.id
         and (m.external_url is not null or m.storage_path like '/app/static%')) as photos,
      (select count(*) from catalog_media m where m.catalog_id = i.id and m.is_cover = 1
         and (m.external_url is not null or m.storage_path like '/app/static%')) as covers,
      (select count(*) from catalog_media m where m.catalog_id = i.id
         and m.storage_path like '/app/static%') as local
    from catalog_items i
    where i.status = 'published'
    order by i.kind, i.id
""").fetchall()

total = len(rows)
ok = [r for r in rows if r["photos"] >= 5 and r["covers"] == 1]
low = [r for r in rows if r["photos"] < 5 or r["covers"] != 1]
print(f"Fiches : {total} | conformes (>=5 photos, 1 couverture) : {len(ok)} | a corriger : {len(low)}")
if low:
    for r in low:
        print(f"  ! {r['slug']}: {r['photos']} photos, {r['covers']} couverture, {r['local']} locales")
print(f"Total photos : {sum(r['photos'] for r in rows)} | locales : {sum(r['local'] for r in rows)}")
by_kind: dict[str, list[int]] = {}
for r in rows:
    by_kind.setdefault(r["kind"], []).append(r["photos"])
for kind, values in by_kind.items():
    print(f"  {kind}: {len(values)} fiches, min {min(values)}, max {max(values)}")
sys.exit(1 if low else 0)
