"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
from unittest.mock import Mock


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory fixture."""
    return tmp_path


@pytest.fixture
def sample_image_data():
    """Sample image data for testing."""
    return {
        "id": "test-shirt",
        "title": "Test Shirt",
        "category": "shirts",
        "filename": "test_shirt.jpg",
        "slug": "test-shirt",
        "thumbnail": "images/thumbs/test_shirt.jpg",
        "image": "images/full/test_shirt.jpg",
        "tags": ["shirts", "color:blue", "size:medium"],
        "notes": "A test shirt",
        "created_date": 1234567890
    }


@pytest.fixture
def mock_google_services():
    """Mock Google Sheets and Drive services."""
    sheets_mock = Mock()
    drive_mock = Mock()
    return sheets_mock, drive_mock


@pytest.fixture
def sample_sheet_values():
    """Sample spreadsheet values for testing."""
    return [
        # Header rows
        ["ID", "Title", "Category", "Filename", "Slug", "Thumbnail", "Image", "Notes", "Created (UTC ISO8601)", "Tags", "", ""],
        ["", "", "", "", "", "", "", "", "", "color", "size", "----"],
        # Data rows
        ["test-shirt", "Test Shirt", "shirts", "test_shirt.jpg", "test-shirt", 
         "images/thumbs/test_shirt.jpg", "images/full/test_shirt.jpg", "A test shirt", 
         "2009-02-13T23:31:30Z", "blue", "medium", "Cotton"]
    ]