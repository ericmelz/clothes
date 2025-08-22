#!/usr/bin/env python3
"""
Wardrobe Site Generator

This script scans the source_photos directory, processes images,
creates thumbnails, and generates a JSON file with clothing item metadata.
"""

import json
import os
from pathlib import Path
from PIL import Image
from pillow_heif import register_heif_opener
import re
from typing import Dict, List, Any

# Register HEIF/HEIC support
register_heif_opener()

class WardrobeGenerator:
    def __init__(self, source_dir: str = "source_photos", output_dir: str = "output"):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.thumbs_dir = self.images_dir / "thumbs"
        self.full_dir = self.images_dir / "full"
        
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
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Generate filename without HEIC extension
                base_name = image_path.stem
                slug = self.generate_slug_from_filename(image_path.name)
                
                # Create thumbnail (300x300, maintain aspect ratio)
                thumb = img.copy()
                thumb.thumbnail((300, 300), Image.Resampling.LANCZOS)
                thumb_path = self.thumbs_dir / f"{base_name}.jpg"
                thumb.save(thumb_path, "JPEG", quality=85)
                
                # Create full-size web image (max 1200px width, maintain aspect ratio)
                full = img.copy()
                if full.width > 1200:
                    ratio = 1200 / full.width
                    new_height = int(full.height * ratio)
                    full = full.resize((1200, new_height), Image.Resampling.LANCZOS)
                
                full_path = self.full_dir / f"{base_name}.jpg"
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
        if not self.source_dir.exists():
            print(f"Source directory {self.source_dir} not found!")
            return

        # Supported image extensions
        image_extensions = {'.heic', '.jpg', '.jpeg', '.png', '.webp'}
        
        for category_dir in self.source_dir.iterdir():
            if not category_dir.is_dir():
                continue
                
            category_name = category_dir.name
            print(f"\nProcessing category: {category_name}")
            
            for image_file in category_dir.iterdir():
                if image_file.suffix.lower() in image_extensions:
                    item = self.process_image(image_file, category_name)
                    if item:
                        self.items.append(item)

    def generate_json_data(self):
        """Generate the JSON data file"""
        data = {
            "metadata": {
                "version": "1.0",
                "generated_at": "2025-08-22",
                "total_items": len(self.items)
            },
            "categories": list(set(item["category"] for item in self.items)),
            "items": self.items
        }
        
        json_path = self.output_dir / "wardrobe_data.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\nGenerated {json_path} with {len(self.items)} items")

    def generate_static_site(self):
        """Copy files to create a static website that can be served directly by nginx"""
        import shutil
        
        website_dir = self.output_dir / "website"
        
        # Copy JSON data to website directory
        json_source = self.output_dir / "wardrobe_data.json"
        json_dest = website_dir / "wardrobe_data.json"
        if json_source.exists():
            shutil.copy2(json_source, json_dest)
            print(f"Copied JSON data to {json_dest}")
        
        # Copy images to website directory
        images_source = self.output_dir / "images"
        images_dest = website_dir / "images"
        if images_source.exists():
            if images_dest.exists():
                shutil.rmtree(images_dest)
            shutil.copytree(images_source, images_dest)
            print(f"Copied images to {images_dest}")
        
        print("Static website structure created!")
        print(f"Website ready for deployment at: {website_dir}")
        print("You can now serve this directory with nginx or any web server.")

    def generate(self):
        """Main generation method"""
        print("Starting wardrobe site generation...")
        self.scan_source_photos()
        self.generate_json_data()
        self.generate_static_site()
        print("Generation complete!")

def main():
    generator = WardrobeGenerator()
    generator.generate()

if __name__ == "__main__":
    main()