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
from typing import Dict, List, Any
from datetime import datetime

# Register HEIF/HEIC support
register_heif_opener()

class WardrobeGenerator:
    def __init__(self, source_dir: str = "source_data", output_dir: str = "output",
                 site_template_dir: str = "site_template", skip_image_processing=False):
        self.source_dir = Path(source_dir)
        self.photos_dir = self.source_dir / "photos"
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.thumbs_dir = self.images_dir / "thumbs"
        self.full_dir = self.images_dir / "full"
        self.site_template_dir = Path(site_template_dir)
        self.skip_image_processing = skip_image_processing
        
        # Create output directories
        self.output_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        self.thumbs_dir.mkdir(exist_ok=True)
        self.full_dir.mkdir(exist_ok=True)
        
        self.items = []

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
        id_to_items = self.read_json_data()
        for item in self.items:
            if item['id'] in id_to_items:
                items.append(id_to_items[item['id']])
            else:
                items.append(item)
            
        data = {
            "metadata": {
                "version": "1.0",
                "generated_at": "2025-08-22",
                "total_items": len(self.items)
            },
            "categories": list(set(item["category"] for item in self.items)),
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
                          site_template_dir=site_template_path).generate()



if __name__ == "__main__":
    main()
