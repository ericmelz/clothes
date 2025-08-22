# Wardrobe Static Site

This is a static, data-driven website for browsing your clothing photos.

## Quick Start

1. Put your source photos under a folder structure like:

```
source_photos/
  Shirts/
    IMG_7053.HEIC
  Pants/
    IMG_7063.HEIC
```

2. From the site root, install generator deps:

```
uv add pillow pillow-heif
```

3. Run the generator to convert images to WebP, create thumbnails, and build the data file:

```
uv run python build/generate.py --src ./source_photos --out .
```

4. Open `index.html` in a browser.

## Editing Titles & Notes

- Permanent: edit `data/items.json` after generation (or provide a `--metadata` CSV/JSON when running the generator).
- Temporary (per-browser): on the item page, expand “Edit notes”, save, then “Export My Notes” to download a JSON with your changes. Merge these back into `data/items.json` to make them permanent.

## Why WebP instead of HEIC?

HEIC support in browsers is inconsistent. The generator converts everything to WebP, which is widely supported and efficient.

## Sample Data

A sample item has been included in `data/items.json` using your “Flower Jamaican Shirt”. Update/replace once you generate your own data.

Generated: 2025-08-22T20:27:33Z
