#!/usr/bin/env python3
"""
Wardrobe Site Generator

This script scans the source_photos directory, processes images,
creates thumbnails, and generates a JSON file with clothing item metadata.
"""

import shutil
import json
import os
from pathlib import Path

from PIL import Image
from pillow_heif import register_heif_opener
import re
from typing import Dict, List, Any, Tuple
from datetime import datetime

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Expected base headers (row 1), produced by the writer script
BASE_HEADERS = [
    "ID",
    "Title",
    "Category",
    "Filename",
    "Slug",
    "Thumbnail",
    "Image",
    "Notes",
    "Created (UTC ISO8601)",
]


# OAuth read-only scopes
OAUTH_READONLY_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


# Register HEIF/HEIC support
register_heif_opener()

class WardrobeGenerator:
    def __init__(self, source_dir: str = "source_data", output_dir: str = "output",
                 site_template_dir: str = "site_template", skip_image_processing=False,
                 parent_folder_id="1d1KFAo3jcomqzm05vpY5S_Vmbrh5_lyw",
                 readwrite_token_path="../token.json",
                 readonly_token_path="../token_readonly.json",
                 creds_path="../credentials.json",
                 metadata_sheetname=None):
        self.source_dir = Path(source_dir)
        self.photos_dir = self.source_dir / "photos"
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.thumbs_dir = self.images_dir / "thumbs"
        self.full_dir = self.images_dir / "full"
        self.site_template_dir = Path(site_template_dir)
        self.skip_image_processing = skip_image_processing
        self.parent_folder_id = parent_folder_id
        self.readwrite_token_path = readwrite_token_path
        self.readonly_token_path = readonly_token_path
        self.creds_path = creds_path
        self.metadata_sheetname = metadata_sheetname
        
        # Create output directories
        self.output_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        self.thumbs_dir.mkdir(exist_ok=True)
        self.full_dir.mkdir(exist_ok=True)
        
        self.items = []

    # -------- Auth / Clients --------
    def get_readonly_google_services(self):
        """
        Returns authorized Sheets and Drive service clients.
        Expects credentials.json in the working directory on first run.
        """
        creds = None

        if os.path.exists(self.readonly_token_path):
            creds = Credentials.from_authorized_user_file(self.readonly_token_path, OAUTH_READONLY_SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.creds_path):
                    raise FileNotFoundError(
                        "credentials.json not found. Download it from Google Cloud Console "
                        "(OAuth 2.0 Client IDs -> Desktop App) and place it next to this script."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(self.creds_path, OAUTH_READONLY_SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self.readonly_token_path, "w") as f:
                f.write(creds.to_json())

        sheets = build("sheets", "v4", credentials=creds)
        drive = build("drive", "v3", credentials=creds)
        return sheets, drive


    # -------- Drive helpers --------
    def find_sheet_in_folder(self, drive, folder_id: str, filename: str) -> str:
        """
        Return the spreadsheet file ID for a file named `filename` within `folder_id`.
        Raises FileNotFoundError if not found.
        """
        q = (
            f"name = '{filename}' and "
            f"'{folder_id}' in parents and "
            f"mimeType = 'application/vnd.google-apps.spreadsheet' and "
            f"trashed = false"
        )
        resp = drive.files().list(
            q=q,
            spaces="drive",
            fields="files(id, name)",
            pageSize=10,
        ).execute()
        files = resp.get("files", [])
        if not files:
            raise FileNotFoundError(
                f"Sheet named '{filename}' not found in folder {folder_id}."
            )
        # If multiple, take the first
        return files[0]["id"]

    # -------- Sheets helpers --------
    def get_first_sheet_title(self, sheets, spreadsheet_id: str) -> str:
        meta = sheets.spreadsheets().get(
            spreadsheetId=spreadsheet_id,
            fields="sheets(properties(title))",
        ).execute()
        sheet_props = meta.get("sheets", [])
        if not sheet_props:
            raise RuntimeError("Spreadsheet has no sheets.")
        return sheet_props[0]["properties"]["title"]
    
    def read_all_values(self, sheets, spreadsheet_id: str, sheet_title: str) -> List[List[str]]:
        """
        Read all values from the first sheet. We read a generous range.
        """
        # A very wide range to capture all columns/rows that might have data
        rng = f"'{sheet_title}'!A1:ZZ100000"
        resp = sheets.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=rng,
            majorDimension="ROWS",
        ).execute()
        return resp.get("values", [])

    # -------- Parsing helpers --------
    def locate_tag_block(self, header_row1: List[str], header_row2: List[str]) -> Tuple[int, List[str]]:
        """
        Using the two-row header:
          - Row 1 contains base_headers and 'Tags' in the first tag column (others blank).
          - Row 2 contains blanks then per-tag-type headers.
        Returns (tag_start_index, tag_type_headers)
        """
        # Find "Tags" cell in row 1; if not present, assume no tag block.
        tag_start = None
        for i, v in enumerate(header_row1):
            if (v or "").strip().lower() == "tags":
                tag_start = i
                break

        if tag_start is None:
            # No "Tags" label; assume no tags -> tag_start at end of base headers
            tag_start = len(header_row2)

        tag_type_headers = header_row2[tag_start:] if tag_start < len(header_row2) else []
        return tag_start, tag_type_headers

    def map_base_columns(self, header_row1: List[str]) -> Dict[str, int]:
        """
        Map expected base headers (exact match) to their indices, if present.
        """
        name_to_idx = {}
        for idx, name in enumerate(header_row1):
            if name in BASE_HEADERS:
                name_to_idx[name] = idx
        return name_to_idx

    def parse_iso_to_epoch(self, iso_str: str) -> int:
        """
        Convert an ISO-8601 string (with 'Z' or offset) to epoch seconds (int).
        Returns 0 if empty or unparsable.
        """
        if not iso_str:
            return 0
        s = iso_str.strip()
        try:
            # Support trailing 'Z'
            if s.endswith("Z"):
                dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(s)
            return int(dt.timestamp())
        except Exception:
            return 0

    def assemble_tags_from_row(self, row: List[str], tag_start: int, tag_types: List[str]) -> List[str]:
        """
        Given a data row and tag columns definition, return a list of tag strings:
          - For type 'color' and cell 'red, blue' -> ['color:red', 'color:blue']
          - For type '----' and cell 'Shirt, Cotton' -> ['Shirt', 'Cotton']
        """
        tags: List[str] = []
        for offset, tag_type in enumerate(tag_types):
            col_idx = tag_start + offset
            cell = row[col_idx].strip() if col_idx < len(row) and row[col_idx] is not None else ""
            if not cell:
                continue
            # Split on commas, keep order
            parts = [p.strip() for p in cell.split(",") if p.strip()]
            if tag_type == "----":
                tags.extend(parts)
            else:
                for p in parts:
                    tags.append(f"{tag_type}:{p}")
        return tags

    def row_to_item(
            self,
            row: List[str],
            base_idx: Dict[str, int],
            tag_start: int,
            tag_types: List[str],
    ) -> Dict:
        """
        Convert one sheet row into an 'item' dict in the original JSON shape.
        """
        def get(name: str) -> str:
            i = base_idx.get(name, -1)
            return (row[i] if (i >= 0 and i < len(row)) else "").strip()

        created_iso = get("Created (UTC ISO8601)")
        created_epoch = self.parse_iso_to_epoch(created_iso)

        item = {
            "id": get("ID"),
            "title": get("Title"),
            "category": get("Category"),
            "filename": get("Filename"),
            "slug": get("Slug"),
            "thumbnail": get("Thumbnail"),
            "image": get("Image"),
            "notes": get("Notes"),
            "created_date": created_epoch,
            "tags": self.assemble_tags_from_row(row, tag_start, tag_types),
        }
        return item

    def sheet_to_items(self, values: List[List[str]]) -> List[Dict]:
        """
        Convert a 2D array from Sheets into a list of items matching the
        original writer script's JSON schema.
        """
        if len(values) < 2:
            return []

        # Two-row header
        row1 = values[0]
        row2 = values[1]

        tag_start, tag_types = self.locate_tag_block(row1, row2)
        base_idx = self.map_base_columns(row1)

        items: List[Dict] = []
        for row in values[2:]:
            # skip entirely blank rows
            if not any((cell or "").strip() for cell in row):
                continue
            it = self.row_to_item(row, base_idx, tag_start, tag_types)
            items.append(it)

        return items

    def read_json_data_from_google_sheet(self) -> Dict[str, Any]:
        sheets, drive = self.get_readonly_google_services()

        filename = self.metadata_sheetname
        print(f"Looking for '{filename}' in folder {self.parent_folder_id}...")
        spreadsheet_id = self.find_sheet_in_folder(drive, self.parent_folder_id, filename)

        sheet_title = self.get_first_sheet_title(sheets, spreadsheet_id)
        values = self.read_all_values(sheets, spreadsheet_id, sheet_title)

        items = self.sheet_to_items(values)
        id_to_items = {}
        for item in items:
            id_to_items[item['id']] = item
        return id_to_items


    # Base metadata and image processing
    def generate_slug_from_filename(self, filename: str) -> str:
        """Generate a URL-friendly slug from filename"""
        # Remove file extension and convert to lowercase
        slug = Path(filename).stem.lower()
        # Replace non-alphanumeric characters with hyphens
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        return slug

    def process_image(self, image_path: Path, category: str) -> Dict[str, Any]:
        """Process a single image file"""
        print(f"Processing {image_path.name}")
        
        try:
            # Open and convert image
            with Image.open(image_path) as img:
                # Convert HEIC to RGB if needed
                if not self.skip_image_processing:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                
                # Generate filename without HEIC extension
                base_name = image_path.stem
                slug = self.generate_slug_from_filename(image_path.name)
                
                # Create thumbnail (300x300, maintain aspect ratio)
                if not self.skip_image_processing:
                    thumb = img.copy()
                    thumb.thumbnail((300, 300), Image.Resampling.LANCZOS)
                    thumb_path = self.thumbs_dir / f"{base_name}.jpg"
                    thumb.save(thumb_path, "JPEG", quality=85)
                
                # Create full-size web image (max 1200px width, maintain aspect ratio)
                if not self.skip_image_processing:
                    full = img.copy()
                    if full.width > 1200:
                        ratio = 1200 / full.width
                        new_height = int(full.height * ratio)
                        full = full.resize((1200, new_height), Image.Resampling.LANCZOS)
                
                full_path = self.full_dir / f"{base_name}.jpg"
                if not self.skip_image_processing:
                    full.save(full_path, "JPEG", quality=90)
                
                # Create item record
                item = {
                    "id": slug,
                    "filename": image_path.name,
                    "slug": slug,
                    "title": self.generate_title_from_filename(base_name),
                    "category": category.lower(),
                    "thumbnail": f"images/thumbs/{base_name}.jpg",
                    "image": f"images/full/{base_name}.jpg",
                    "tags": [category],
                    "notes": "",
                    "created_date": image_path.stat().st_mtime
                }
                
                return item
                
        except Exception as e:
            print(f"Error processing {image_path.name}: {e}")
            return None

    def generate_title_from_filename(self, filename: str) -> str:
        """Generate a human-readable title from filename"""
        # For now, just use the filename as title
        # This can be enhanced later to be more descriptive
        title = filename.replace('_', ' ').replace('-', ' ')
        return title

    def scan_source_photos(self):
        """Scan the source_photos directory and process all images"""
        if not self.photos_dir.exists():
            print(f"Source directory {self.photos_dir} not found!")
            return

        # Supported image extensions
        image_extensions = {'.heic', '.jpg', '.jpeg', '.png', '.webp'}
        
        for category_dir in self.photos_dir.iterdir():
            if not category_dir.is_dir():
                continue
                
            category_name = category_dir.name
            print(f"\nProcessing category: {category_name}")
            
            for image_file in category_dir.iterdir():
                if image_file.suffix.lower() in image_extensions:
                    item = self.process_image(image_file, category_name)
                    if item:
                        self.items.append(item)

    def read_json_data(self) -> Dict[str, Any]:
        json_path = self.source_dir / "wardrobe_data.json"
        with open (json_path) as f:
            data = json.load(f)
        id_to_items = {}
        for item in data['items']:
            id_to_items[item['id']] = item
        return id_to_items

    def generate_json_data(self):
        """Generate the JSON data file"""
        items = []

        # TODO: replace this with reading from Google Sheet
        # TODO: detect category conflicts
#        id_to_items = self.read_json_data()
        id_to_items = self.read_json_data_from_google_sheet()
        for item in self.items:
            if item['id'] in id_to_items:
                items.append(id_to_items[item['id']])
            else:
                items.append(item)
            
        data = {
            "metadata": {
                "version": "1.0",
                "generated_at": f"{datetime.now()}",
                "total_items": len(self.items)
            },
            "categories": sorted(list(set(item["category"] for item in self.items))),
            "items": items
        }
        
        json_path = self.output_dir / "wardrobe_data.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nGenerated {json_path} with {len(self.items)} items")


    def generate_static_site(self):
        """Copy files to create a static website that can be served directly by nginx"""
        # copy index.html
        source = self.site_template_dir / "per_person_assets"
        dest = self.output_dir 
        shutil.copytree(source, dest, dirs_exist_ok=True)

        print("Static website created!")


    def generate(self):
        """Main generation method"""
        print("Starting wardrobe site generation...")
        start = datetime.now()
        self.generate_static_site()
        self.scan_source_photos()
        self.generate_json_data()
        end = datetime.now()
        print(f"Generation complete! {(end - start).seconds} seconds elapsed.")



def create_favicon(output_dir: Path):
    """Create a simple SVG favicon"""
    favicon_content = '''<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
    <rect width="32" height="32" fill="#3498db"/>
    <text x="16" y="20" text-anchor="middle" fill="white" font-family="Arial" font-size="16" font-weight="bold">W</text>
</svg>'''
        
    website_dir = output_dir / "website"
    favicon_path = Path(output_dir) / "favicon.svg"
    with open(favicon_path, 'w') as f:
        f.write(favicon_content)
    print(f"Created favicon at {favicon_path}")


def main():
    output_dir = Path('output')
    site_template_dir = Path('site_template')

    try:
        shutil.rmtree(output_dir)
    except FileNotFoundError:
        pass
    
    output_dir.mkdir(exist_ok=True)

    # copy index.html, styles.css, favicon?
    create_favicon(output_dir)

    # Copy index.html and styles.css to website directory
    for file in ['index.html', 'styles.css']:
        source = site_template_dir / file
        dest = output_dir / file
        shutil.copy2(source, dest)
        print(f"Copied {source} to {dest}")

    people = ['eric', 'randi']
    for person in people:
        source_path = f'source_data/{person}s-clothes'
        output_path = f'{output_dir}/{person}s-clothes'
        site_template_path = f'site_template'
        WardrobeGenerator(source_dir=source_path, output_dir=output_path,
                          site_template_dir=site_template_path,
                          metadata_sheetname=f"{person}-wardrobe").generate()



if __name__ == "__main__":
    main()
