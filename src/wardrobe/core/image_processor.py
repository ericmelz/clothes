"""Image processing functionality for wardrobe items."""

import re
from pathlib import Path
from typing import Dict, Any, Optional

from PIL import Image
from pillow_heif import register_heif_opener

# Register HEIF/HEIC support
register_heif_opener()


class ImageProcessor:
    """Handles image processing for wardrobe items."""
    
    def __init__(self, thumbs_dir: Path, full_dir: Path, skip_processing: bool = False):
        """
        Initialize image processor.
        
        Args:
            thumbs_dir: Directory for thumbnail images
            full_dir: Directory for full-size images  
            skip_processing: Skip actual image processing (for testing)
        """
        self.thumbs_dir = thumbs_dir
        self.full_dir = full_dir
        self.skip_processing = skip_processing
        
        # Create output directories
        self.thumbs_dir.mkdir(parents=True, exist_ok=True)
        self.full_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_slug_from_filename(self, filename: str) -> str:
        """Generate a URL-friendly slug from filename."""
        # Remove file extension and convert to lowercase
        slug = Path(filename).stem.lower()
        # Replace non-alphanumeric characters with hyphens
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        return slug

    def generate_title_from_filename(self, filename: str) -> str:
        """Generate a human-readable title from filename."""
        # For now, just use the filename as title
        # This can be enhanced later to be more descriptive
        title = filename.replace('_', ' ').replace('-', ' ')
        return title

    def process_image(self, image_path: Path, category: str) -> Optional[Dict[str, Any]]:
        """
        Process a single image file.
        
        Args:
            image_path: Path to the source image
            category: Category name for the item
            
        Returns:
            Item dictionary or None if processing failed
        """
        print(f"Processing {image_path.name}")
        
        try:
            # Open and convert image
            with Image.open(image_path) as img:
                # Convert HEIC to RGB if needed
                if not self.skip_processing:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                
                # Generate filename without HEIC extension
                base_name = image_path.stem
                slug = self.generate_slug_from_filename(image_path.name)
                
                # Create thumbnail (300x300, maintain aspect ratio)
                if not self.skip_processing:
                    thumb = img.copy()
                    thumb.thumbnail((300, 300), Image.Resampling.LANCZOS)
                    thumb_path = self.thumbs_dir / f"{base_name}.jpg"
                    thumb.save(thumb_path, "JPEG", quality=85)
                
                # Create full-size web image (max 1200px width, maintain aspect ratio)
                if not self.skip_processing:
                    full = img.copy()
                    if full.width > 1200:
                        ratio = 1200 / full.width
                        new_height = int(full.height * ratio)
                        full = full.resize((1200, new_height), Image.Resampling.LANCZOS)
                
                full_path = self.full_dir / f"{base_name}.jpg"
                if not self.skip_processing:
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

    def scan_photos_directory(self, photos_dir: Path) -> list:
        """
        Scan the source_photos directory and process all images.
        
        Args:
            photos_dir: Directory containing category subdirectories with images
            
        Returns:
            List of processed item dictionaries
        """
        items = []
        
        if not photos_dir.exists():
            print(f"Source directory {photos_dir} not found!")
            return items

        # Supported image extensions
        image_extensions = {'.heic', '.jpg', '.jpeg', '.png', '.webp'}
        
        for category_dir in photos_dir.iterdir():
            if not category_dir.is_dir():
                continue
                
            category_name = category_dir.name
            print(f"\nProcessing category: {category_name}")
            
            for image_file in category_dir.iterdir():
                if image_file.suffix.lower() in image_extensions:
                    item = self.process_image(image_file, category_name)
                    if item:
                        items.append(item)
        
        return items