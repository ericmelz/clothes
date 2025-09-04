"""Tests for Google Sheets reader functionality."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from wardrobe.google_sheets.reader import SheetsReader
from wardrobe.google_sheets.auth import GoogleSheetsAuth


class TestSheetsReader:
    """Test SheetsReader functionality."""
    
    def test_parse_iso_to_epoch(self):
        """Test ISO date parsing."""
        auth = Mock()
        reader = SheetsReader(auth)
        
        # Test valid ISO date with Z
        result = reader.parse_iso_to_epoch("2009-02-13T23:31:30Z")
        assert result == 1234567890
        
        # Test empty string
        assert reader.parse_iso_to_epoch("") == 0
        
        # Test invalid date
        assert reader.parse_iso_to_epoch("invalid") == 0

    def test_generate_slug_from_filename(self):
        """Test slug generation from filename."""
        from wardrobe.core.image_processor import ImageProcessor
        from pathlib import Path
        
        processor = ImageProcessor(Path("/tmp"), Path("/tmp"), skip_processing=True)
        
        # Test basic filename
        assert processor.generate_slug_from_filename("Test_File.jpg") == "test-file"
        
        # Test with spaces and special chars
        assert processor.generate_slug_from_filename("My Great Photo!.heic") == "my-great-photo"
        
        # Test with multiple underscores/hyphens
        assert processor.generate_slug_from_filename("test__file--name.png") == "test-file-name"

    def test_locate_tag_block(self):
        """Test tag block location in headers."""
        auth = Mock()
        reader = SheetsReader(auth)
        
        header_row1 = ["ID", "Title", "Category", "Tags", "", ""]
        header_row2 = ["", "", "", "color", "size", "----"]
        
        tag_start, tag_types = reader.locate_tag_block(header_row1, header_row2)
        
        assert tag_start == 3
        assert tag_types == ["color", "size", "----"]

    def test_locate_tag_block_no_tags(self):
        """Test tag block location when no tags column exists."""
        auth = Mock()
        reader = SheetsReader(auth)
        
        header_row1 = ["ID", "Title", "Category"]
        header_row2 = ["", "", ""]
        
        tag_start, tag_types = reader.locate_tag_block(header_row1, header_row2)
        
        assert tag_start == 3
        assert tag_types == []

    def test_assemble_tags_from_row(self):
        """Test assembling tags from a data row."""
        auth = Mock()
        reader = SheetsReader(auth)
        
        row = ["id1", "title", "category", "red, blue", "large", "Cotton, Soft"]
        tag_start = 3
        tag_types = ["color", "size", "----"]
        
        result = reader.assemble_tags_from_row(row, tag_start, tag_types)
        expected = ["color:red", "color:blue", "size:large", "Cotton", "Soft"]
        
        assert result == expected

    def test_sheet_to_items(self, sample_sheet_values):
        """Test converting sheet values to items."""
        auth = Mock()
        reader = SheetsReader(auth)
        
        items = reader.sheet_to_items(sample_sheet_values)
        
        assert len(items) == 1
        item = items[0]
        assert item["id"] == "test-shirt"
        assert item["title"] == "Test Shirt"
        assert item["category"] == "shirts"
        assert item["created_date"] == 1234567890
        assert "color:blue" in item["tags"]
        assert "size:medium" in item["tags"]
        assert "Cotton" in item["tags"]

    def test_sheet_to_items_empty(self):
        """Test converting empty sheet values."""
        auth = Mock()
        reader = SheetsReader(auth)
        
        # Test with no data
        assert reader.sheet_to_items([]) == []
        
        # Test with only one row (no header)
        assert reader.sheet_to_items([["ID", "Title"]]) == []