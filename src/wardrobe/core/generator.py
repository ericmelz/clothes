"""Main wardrobe site generator."""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from ..google_sheets import GoogleSheetsAuth, SheetsReader
from .image_processor import ImageProcessor


def create_favicon(output_dir: Path):
    """Create a simple SVG favicon."""
    favicon_content = '''<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
    <rect width="32" height="32" fill="#3498db"/>
    <text x="16" y="20" text-anchor="middle" fill="white" font-family="Arial" font-size="16" font-weight="bold">W</text>
</svg>'''
        
    favicon_path = output_dir / "favicon.svg"
    with open(favicon_path, 'w') as f:
        f.write(favicon_content)
    print(f"Created favicon at {favicon_path}")


class WardrobeGenerator:
    """Main class for generating wardrobe sites."""
    
    def __init__(self, 
                 source_dir: str = "source_data", 
                 output_dir: str = "output",
                 site_template_dir: str = "site_template", 
                 skip_image_processing: bool = False,
                 parent_folder_id: str = "1d1KFAo3jcomqzm05vpY5S_Vmbrh5_lyw",
                 readwrite_token_path: str = "../token.json",
                 readonly_token_path: str = "../token_readonly.json",
                 creds_path: str = "../credentials.json",
                 metadata_sheetname: Optional[str] = None):
        """
        Initialize wardrobe generator.
        
        Args:
            source_dir: Source data directory
            output_dir: Output directory for generated site
            site_template_dir: Template directory for site files
            skip_image_processing: Skip image processing (useful for testing)
            parent_folder_id: Google Drive folder ID
            readwrite_token_path: Path to read/write token
            readonly_token_path: Path to readonly token
            creds_path: Path to OAuth credentials
            metadata_sheetname: Name of metadata spreadsheet
        """
        self.source_dir = Path(source_dir)
        self.photos_dir = self.source_dir / "photos"
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.thumbs_dir = self.images_dir / "thumbs"
        self.full_dir = self.images_dir / "full"
        self.site_template_dir = Path(site_template_dir)
        self.parent_folder_id = parent_folder_id
        self.metadata_sheetname = metadata_sheetname
        
        # Create output directories
        self.output_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.auth = GoogleSheetsAuth(
            credentials_path=creds_path,
            readonly_token_path=readonly_token_path,
            readwrite_token_path=readwrite_token_path
        )
        self.sheets_reader = SheetsReader(self.auth)
        self.image_processor = ImageProcessor(
            thumbs_dir=self.thumbs_dir,
            full_dir=self.full_dir,
            skip_processing=skip_image_processing
        )
        
        self.items = []

    def read_json_data_from_google_sheet(self) -> Dict[str, Any]:
        """Read data from Google Sheet and return as item dictionary."""
        if not self.metadata_sheetname:
            return {}
            
        return self.sheets_reader.read_sheet_data(
            parent_folder_id=self.parent_folder_id,
            sheet_name=self.metadata_sheetname
        )

    def read_json_data(self) -> Dict[str, Any]:
        """Read data from local JSON file."""
        json_path = self.source_dir / "wardrobe_data.json"
        if not json_path.exists():
            return {}
            
        with open(json_path) as f:
            data = json.load(f)
        id_to_items = {}
        for item in data['items']:
            id_to_items[item['id']] = item
        return id_to_items

    def scan_source_photos(self):
        """Scan the source_photos directory and process all images."""
        self.items = self.image_processor.scan_photos_directory(self.photos_dir)

    def generate_json_data(self):
        """Generate the JSON data file."""
        items = []

        # Try to get data from Google Sheets first, fall back to local JSON
        try:
            id_to_items = self.read_json_data_from_google_sheet()
        except Exception as e:
            print(f"Warning: Could not read from Google Sheets: {e}")
            id_to_items = self.read_json_data()
        
        changed_categories = []
        for item in self.items:
            if item['id'] in id_to_items:
                replacement_item = id_to_items[item['id']]
                if replacement_item['category'] != item['category']:
                    changed_categories.append((item['id'], item['category'], replacement_item['category']))
                items.append(replacement_item)
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

        if len(changed_categories) > 0:
            print("\n*** WARNING: The Following categories have been changed on the spreadsheet:")
            for id, original, new in changed_categories:
                print(f"  {id=} {original=} {new=}")

    def generate_static_site(self):
        """Copy files to create a static website that can be served directly by nginx."""
        # copy index.html
        source = self.site_template_dir / "per_person_assets"
        dest = self.output_dir 
        if source.exists():
            shutil.copytree(source, dest, dirs_exist_ok=True)
            print("Static website created!")
        else:
            print(f"Warning: Template directory {source} not found")

    def generate(self):
        """Main generation method."""
        print("Starting wardrobe site generation...")
        start = datetime.now()
        self.generate_static_site()
        self.scan_source_photos()
        self.generate_json_data()
        end = datetime.now()
        print(f"Generation complete! {(end - start).seconds} seconds elapsed.")


def generate_wardrobe_sites(people: List[str] = None, 
                          output_base: str = "output",
                          site_template_dir: str = "site_template"):
    """
    Generate wardrobe sites for multiple people.
    
    Args:
        people: List of people to generate sites for
        output_base: Base output directory
        site_template_dir: Template directory
    """
    if people is None:
        people = ['eric', 'randi']
    
    output_dir = Path(output_base)
    site_template_dir = Path(site_template_dir)

    # Clean output directory
    try:
        shutil.rmtree(output_dir)
    except FileNotFoundError:
        pass
    
    output_dir.mkdir(exist_ok=True)

    # Create favicon
    create_favicon(output_dir)

    # Copy shared files
    for file in ['index.html', 'styles.css']:
        source = site_template_dir / file
        dest = output_dir / file
        if source.exists():
            shutil.copy2(source, dest)
            print(f"Copied {source} to {dest}")
        else:
            print(f"Warning: Template file {source} not found")

    # Generate sites for each person
    for person in people:
        source_path = f'source_data/{person}s-clothes'
        output_path = f'{output_dir}/{person}s-clothes'
        site_template_path = str(site_template_dir)
        
        generator = WardrobeGenerator(
            source_dir=source_path, 
            output_dir=output_path,
            site_template_dir=site_template_path,
            metadata_sheetname=f"{person}-wardrobe"
        )
        generator.generate()