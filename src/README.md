# Wardrobe Management System

A modular Python package for managing clothing inventory with Google Sheets integration, image processing, and static website generation. Perfect for organizing your wardrobe with photos, metadata, and searchable web interfaces.

## ✨ Features

- **📸 Image Processing**: Converts HEIC photos to web-friendly JPEGs with thumbnails
- **📊 Google Sheets Integration**: Read/write inventory data to collaborative spreadsheets
- **🔍 Search & Filter**: Searchable, browsable website with category filtering
- **📱 Responsive Design**: Works on desktop and mobile devices
- **🔗 URL Routing**: Direct links to individual items
- **🧪 Jupyter-Friendly**: Clean imports for notebook experimentation
- **🛠️ Developer Tools**: Comprehensive test suite, linting, and type checking

## 🏗️ Project Structure

```
src/wardrobe/               # Main package
├── core/                   # Core functionality
│   ├── generator.py        # Main site generator
│   └── image_processor.py  # Image processing
├── google_sheets/          # Google Sheets integration
│   ├── auth.py            # Authentication
│   ├── reader.py          # Read from sheets
│   └── writer.py          # Write to sheets
├── web/                   # Web server
└── cli.py                 # Command-line interface

tests/                     # Test suite
scripts/                   # Development scripts
source_data/              # Your data
├── photos/               # Original photos by category
└── wardrobe_data.json    # Item metadata (optional)
output/                   # Generated website files
site_template/            # HTML/CSS templates
```

## 🚀 Quick Start

### Installation
```bash
# Install with development tools
uv pip install -e ".[dev,jupyter]"

# Or just the basics
uv pip install -e .
```

### Command Line Usage
```bash
# Generate sites for all people (eric, randi)
wardrobe generate

# Generate for specific people
wardrobe generate --people alice bob

# Generate single person with custom paths
wardrobe generate-single eric --source my_data --output my_output --sheet "Eric's Closet"
```

### Python API
```python
from wardrobe import WardrobeGenerator

# Basic usage
generator = WardrobeGenerator(
    source_dir="source_data/erics-clothes",
    output_dir="output/erics-clothes",
    metadata_sheetname="eric-wardrobe"
)
generator.generate()

# For experimentation (skip slow image processing)
generator = WardrobeGenerator(skip_image_processing=True)
items = generator.image_processor.scan_photos_directory("photos")
```

### Jupyter Notebooks
```python
# Clean imports for experimentation
from wardrobe.google_sheets import SheetsReader, SheetsWriter
from wardrobe.core import ImageProcessor
from wardrobe import WardrobeGenerator

# Test sheet reading
auth = GoogleSheetsAuth()
reader = SheetsReader(auth)
data = reader.read_sheet_data("folder_id", "eric-wardrobe")
```

## Customization

### Adding Metadata

Edit `source_data/wardrobe_data.json` to customize:
- **titles**: Change from generic "IMG_7055" to "Blue Striped Shirt"
- **tags**: Add descriptive tags like "casual", "work", "summer"
- **notes**: Add detailed notes like "Great for beach parties"

Example item customization:
```json
{
  "id": "img-7055",
  "title": "Flower Jamaican Shirt",
  "category": "shirts",
  "tags": ["Jamaican", "Party", "Festive", "Medium"],
  "notes": "Good for Jamaican Party"
}
```

### Adding Categories

Simply create new directories in `source_photos/`:
- `source_photos/Jackets/`
- `source_photos/Shoes/`
- `source_photos/Accessories/`

### Styling

Modify `output/website/styles.css` to customize:
- Colors and fonts
- Grid layout
- Card designs
- Modal appearance

## 🛠️ Development Setup

### Prerequisites
- Python 3.12+
- uv package manager
- Google Cloud credentials (for Sheets integration)

### Development Installation
```bash
# Clone and setup
git clone <your-repo>
cd wardrobe
uv pip install -e ".[dev,jupyter]"
```

### Running Tests
```bash
# Run all tests with coverage
python scripts/run_tests.py

# Or use pytest directly
pytest tests/ -v

# Run specific test file
pytest tests/test_sheets_reader.py -v
```

### Code Quality
```bash
# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Lint
ruff check src/ tests/
```

### Google Sheets Setup
1. **Create Google Cloud Project**: Go to [Google Cloud Console](https://console.cloud.google.com/)
2. **Enable APIs**: Enable Google Sheets API and Google Drive API
3. **Create OAuth Credentials**: Create OAuth 2.0 Client ID for Desktop application
4. **Download credentials.json**: Place in project root
5. **First run**: Will open browser for authentication

### Testing Without Google Sheets
```python
# Use local JSON files for testing
generator = WardrobeGenerator(
    source_dir="test_data",
    output_dir="test_output", 
    skip_image_processing=True  # Faster for testing
)
# Will fall back to local JSON if sheets unavailable
```

## 📦 Architecture & Extension Points

### Modular Design
- **`core/`**: Image processing and site generation logic
- **`google_sheets/`**: Authentication and sheet I/O (easily replaceable)
- **`web/`**: Web server functionality
- **`cli.py`**: Command-line interface

### Adding New Features
```python
# Extend the generator
class CustomWardrobeGenerator(WardrobeGenerator):
    def custom_processing(self):
        # Add your custom logic
        pass

# Add new sheet operations  
class CustomSheetsReader(SheetsReader):
    def read_custom_data(self):
        # Custom sheet reading logic
        pass
```

### Testing Strategy
- **Unit tests**: Individual component testing
- **Integration tests**: End-to-end workflows  
- **Mocked services**: Google Sheets calls are mocked
- **Fixtures**: Reusable test data and directories

## 🔍 Troubleshooting

### Common Issues

**"credentials.json not found"**
```bash
# Download from Google Cloud Console and place in project root
ls credentials.json  # Should exist
```

**Tests failing**
```bash
# Install test dependencies
uv pip install -e ".[test]"

# Run with verbose output
pytest -v -s
```

**Import errors in notebooks**
```bash
# Install in development mode
uv pip install -e .

# Restart notebook kernel
```

**Image processing slow**
```bash
# Skip image processing for testing
wardrobe generate-single eric --skip-images
```

## 🚀 Technology Stack

- **Backend**: Python 3.12+ with uv package management
- **Image Processing**: Pillow + pillow-heif for HEIC support  
- **Google Integration**: Google Sheets API + Drive API
- **Testing**: pytest with coverage reporting
- **Code Quality**: black, isort, mypy, ruff
- **Frontend**: React.js (browser build, no compilation needed)
- **Data**: JSON + Google Sheets for metadata storage

## 🎯 Future Enhancements

The modular architecture supports easy extension:
- **Database backends**: Replace JSON with SQLite/PostgreSQL
- **Cloud storage**: S3/GCS integration for images
- **Advanced tagging**: ML-powered automatic tagging
- **Mobile app**: API-first design ready for mobile clients
- **Outfit planning**: Combination and recommendation features
- **Shopping integration**: Price tracking and purchase history