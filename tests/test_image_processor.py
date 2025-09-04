"""Tests for image processing functionality."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from wardrobe.core.image_processor import ImageProcessor


class TestImageProcessor:
    """Test ImageProcessor functionality."""
    
    def test_generate_slug_from_filename(self, temp_dir):
        """Test slug generation from filename."""
        processor = ImageProcessor(temp_dir, temp_dir, skip_processing=True)
        
        # Test basic filename
        assert processor.generate_slug_from_filename("Test_File.jpg") == "test-file"
        
        # Test with spaces and special chars
        assert processor.generate_slug_from_filename("My Great Photo!.heic") == "my-great-photo"
        
        # Test with multiple underscores/hyphens
        assert processor.generate_slug_from_filename("test__file--name.png") == "test-file-name"
        
        # Test edge cases
        assert processor.generate_slug_from_filename("123.jpg") == "123"
        assert processor.generate_slug_from_filename("   test   .png") == "test"

    def test_generate_title_from_filename(self, temp_dir):
        """Test title generation from filename."""
        processor = ImageProcessor(temp_dir, temp_dir, skip_processing=True)
        
        assert processor.generate_title_from_filename("test_file") == "test file"
        assert processor.generate_title_from_filename("my-great-photo") == "my great photo"
        assert processor.generate_title_from_filename("simple") == "simple"

    def test_init_creates_directories(self, temp_dir):
        """Test that initialization creates output directories."""
        thumbs_dir = temp_dir / "thumbs"
        full_dir = temp_dir / "full"
        
        processor = ImageProcessor(thumbs_dir, full_dir, skip_processing=True)
        
        assert thumbs_dir.exists()
        assert full_dir.exists()

    @patch('wardrobe.core.image_processor.Image')
    def test_process_image_skip_processing(self, mock_image, temp_dir):
        """Test processing image with skip_processing=True."""
        # Setup
        thumbs_dir = temp_dir / "thumbs"
        full_dir = temp_dir / "full"
        processor = ImageProcessor(thumbs_dir, full_dir, skip_processing=True)
        
        # Create a fake image file
        image_path = temp_dir / "test_image.jpg"
        image_path.touch()
        
        # Mock PIL Image
        mock_img = MagicMock()
        mock_img.mode = 'RGB'
        mock_image.open.return_value.__enter__.return_value = mock_img
        
        # Process image
        result = processor.process_image(image_path, "test_category")
        
        # Verify result
        assert result is not None
        assert result["id"] == "test-image"
        assert result["filename"] == "test_image.jpg"
        assert result["category"] == "test_category"
        assert result["tags"] == ["test_category"]
        
        # Verify PIL wasn't called for actual processing since skip_processing=True
        mock_img.save.assert_not_called()

    def test_scan_photos_directory_nonexistent(self, temp_dir):
        """Test scanning a non-existent photos directory."""
        processor = ImageProcessor(temp_dir, temp_dir, skip_processing=True)
        nonexistent_dir = temp_dir / "nonexistent"
        
        result = processor.scan_photos_directory(nonexistent_dir)
        assert result == []

    @patch('wardrobe.core.image_processor.Image')
    def test_scan_photos_directory(self, mock_image, temp_dir):
        """Test scanning photos directory with images."""
        # Setup processor
        thumbs_dir = temp_dir / "thumbs"
        full_dir = temp_dir / "full"
        processor = ImageProcessor(thumbs_dir, full_dir, skip_processing=True)
        
        # Create directory structure
        photos_dir = temp_dir / "photos"
        category_dir = photos_dir / "shirts"
        category_dir.mkdir(parents=True)
        
        # Create test images
        (category_dir / "shirt1.jpg").touch()
        (category_dir / "shirt2.heic").touch()
        (category_dir / "readme.txt").touch()  # Should be ignored
        
        # Mock PIL Image
        mock_img = MagicMock()
        mock_img.mode = 'RGB'
        mock_image.open.return_value.__enter__.return_value = mock_img
        
        # Scan directory
        items = processor.scan_photos_directory(photos_dir)
        
        # Verify results
        assert len(items) == 2
        assert all(item["category"] == "shirts" for item in items)
        assert {item["filename"] for item in items} == {"shirt1.jpg", "shirt2.heic"}