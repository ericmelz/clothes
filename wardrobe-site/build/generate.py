#!/usr/bin/env python3
# Batch generator: converts HEIC/JPG/PNG to WebP, creates thumbnails, and builds data/items.json.
# Usage:
#   python build/generate.py --src ./source_photos --out .
#   (Run from the site root.)

import argparse, json, os, pathlib, sys, datetime
from typing import List, Dict

# Dependencies:
#   pip install pillow pillow-heif
from PIL import Image
try:
    import pillow_heif
except Exception:
    pillow_heif = None

SUPPORTED_EXTS = {".heic", ".heif", ".jpg", ".jpeg", ".png", ".webp"}

def ensure_heif():
    if pillow_heif is None:
        print("WARNING: pillow-heif not installed. HEIC/HEIF will not decode. Install with 'pip install pillow-heif'.", file=sys.stderr)
    else:
        pillow_heif.register_heif_opener()

def walk_images(src_root: pathlib.Path):
    for root, _, files in os.walk(src_root):
        root_p = pathlib.Path(root)
        rel_dir = root_p.relative_to(src_root)
        category = rel_dir.parts[0] if rel_dir.parts else None
        for name in files:
            ext = pathlib.Path(name).suffix.lower()
            if ext in SUPPORTED_EXTS:
                yield category, root_p / name

def slugify(s: str) -> str:
    import re
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+","-", s).strip("-")
    return s

def convert_and_resize(img_path: pathlib.Path, out_full: pathlib.Path, out_thumb: pathlib.Path, max_full=1600, max_thumb=360):
    out_full.parent.mkdir(parents=True, exist_ok=True)
    out_thumb.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(img_path) as im:
        im = im.convert("RGB")
        # full
        f = im.copy()
        f.thumbnail((max_full, max_full))
        f.save(out_full, "WEBP", quality=85, method=6)
        # thumb
        t = im.copy()
        t.thumbnail((max_thumb, max_thumb))
        t.save(out_thumb, "WEBP", quality=80, method=6)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="Folder with source photos (e.g., source_photos)")
    ap.add_argument("--out", default=".", help="Site root (where index.html lives)")
    ap.add_argument("--metadata", default=None, help="Optional path to metadata.json or CSV with columns: category,filename,title,notes")
    args = ap.parse_args()

    site_root = pathlib.Path(args.out).resolve()
    src_root = pathlib.Path(args.src).resolve()

    images_root = site_root / "images"
    thumbs_root = site_root / "thumbs"
    data_path = site_root / "data" / "items.json"

    ensure_heif()

    # Load existing metadata
    meta_map: Dict[str, Dict[str,str]] = {}
    if args.metadata:
        mpath = pathlib.Path(args.metadata)
        if mpath.suffix.lower() == ".json":
            arr = json.loads(mpath.read_text(encoding="utf-8"))
            meta_map = { (slugify(f"{m.get('category','')}-{m.get('filename','')}")): m for m in arr }
        elif mpath.suffix.lower() in (".csv", ".tsv"):
            import csv
            delim = "," if mpath.suffix.lower()==".csv" else "\t"
            with mpath.open(newline="", encoding="utf-8") as f:
                r = csv.DictReader(f, delimiter=delim)
                for row in r:
                    row = {k:(v or "").strip() for k,v in row.items()}
                    key = slugify(f"{row.get('category','')}-{row.get('filename','')}")
                    meta_map[key] = row
        else:
            print("Unsupported metadata file format.", file=sys.stderr)

    items: List[Dict] = []
    for category, path in walk_images(src_root):
        if not category:
            # skip files directly in root without category folder
            continue
        stem = path.stem
        slug = slugify(f"{category}-{stem}")
        rel_dir = pathlib.Path(category)
        out_full = images_root / rel_dir / f"{stem}.webp"
        out_thumb = thumbs_root / rel_dir / f"{stem}.webp"

        try:
            convert_and_resize(path, out_full, out_thumb)
        except Exception as e:
            print(f"Failed to convert {path}: {e}", file=sys.stderr)
            continue

        meta = meta_map.get(slug, {})
        title = meta.get("title", "")
        notes = meta.get("notes", "")

        items.append({
            "id": slug,
            "category": category,
            "filename": f"{stem}.webp",
            "src": str(out_full.relative_to(site_root)).replace("\\","/"),
            "thumb": str(out_thumb.relative_to(site_root)).replace("\\","/"),
            "title": title or stem,
            "notes": notes
        })

    items.sort(key=lambda x: (x.get("category",""), (x.get("title") or "").lower()))
    payload = {"generatedAt": datetime.datetime.utcnow().replace(microsecond=0).isoformat()+"Z", "items": items}
    (site_root / "data").mkdir(parents=True, exist_ok=True)
    data_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {data_path} with {len(items)} items.")

if __name__ == "__main__":
    main()
