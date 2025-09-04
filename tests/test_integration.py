"""Integration tests for the wardrobe system."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from wardrobe.core.generator import WardrobeGenerator


class TestWardrobeGeneratorIntegration:
    """Integration tests for WardrobeGenerator."""
    
    def test_init_creates_directories(self, temp_dir):
        """Test that generator creates necessary directories."""
        source_dir = temp_dir / "source"
        output_dir = temp_dir / "output"
        
        generator = WardrobeGenerator(
            source_dir=str(source_dir),
            output_dir=str(output_dir),
            skip_image_processing=True
        )
        
        assert generator.output_dir.exists()
        assert generator.images_dir.exists()

    @patch('wardrobe.google_sheets.auth.GoogleSheetsAuth._get_credentials')
    def test_read_json_data_fallback(self, mock_get_creds, temp_dir):
        """Test that generator falls back to local JSON when sheets fail."""
        # Setup directories
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        
        # Create test JSON data
        json_data = {
            "items": [
                {"id": "test1", "title": "Test Item 1"},
                {"id": "test2", "title": "Test Item 2"}
            ]
        }
        json_path = source_dir / "wardrobe_data.json"
        with open(json_path, 'w') as f:
            json.dump(json_data, f)
        
        generator = WardrobeGenerator(
            source_dir=str(source_dir),
            output_dir=str(temp_dir / "output"),
            skip_image_processing=True
        )
        
        # Mock sheets failure
        mock_get_creds.side_effect = Exception("Sheets not available")
        
        # This should fall back to local JSON
        result = generator.read_json_data()
        
        assert len(result) == 2
        assert "test1" in result
        assert "test2" in result

    def test_generate_json_data_no_items(self, temp_dir):
        """Test generating JSON data with no items."""
        generator = WardrobeGenerator(
            source_dir=str(temp_dir / "source"),
            output_dir=str(temp_dir / "output"),
            skip_image_processing=True
        )
        
        generator.items = []  # No items
        generator.generate_json_data()
        
        json_path = generator.output_dir / "wardrobe_data.json"
        assert json_path.exists()
        
        with open(json_path) as f:
            data = json.load(f)
        
        assert data["items"] == []
        assert data["categories"] == []
        assert data["metadata"]["total_items"] == 0

    @patch('wardrobe.core.generator.shutil.copytree')
    def test_generate_static_site_missing_template(self, mock_copytree, temp_dir, capsys):
        """Test generating static site with missing template directory."""
        generator = WardrobeGenerator(
            source_dir=str(temp_dir / "source"),
            output_dir=str(temp_dir / "output"),
            site_template_dir=str(temp_dir / "nonexistent_template"),
            skip_image_processing=True
        )
        
        generator.generate_static_site()
        
        # Should print warning about missing template
        captured = capsys.readouterr()
        assert "Warning: Template directory" in captured.out
        
        # Should not have called copytree
        mock_copytree.assert_not_called()