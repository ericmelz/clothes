# Wardrobe Management System

A modular Python package for managing clothing inventory with Google Sheets integration, image processing, and static website generation.

## 🚀 Quick Start

### Installation
```bash
# Install with development tools and Jupyter support
uv pip install -e ".[dev,jupyter]"
```

### Command Line Usage
```bash
# Generate wardrobe sites for all configured people
wardrobe generate

# Generate for a single person
wardrobe generate-single eric --source source_data/erics-clothes
```

### Jupyter Development
```bash
# Start Jupyter for experimentation
uv run jupyter notebook

# Open notebooks in notebooks/ directory
# Clean imports now available:
from wardrobe import WardrobeGenerator
from wardrobe.google_sheets import SheetsReader, SheetsWriter
```

### Deployment
```bash
src/deploy.sh
```

## 📁 Project Structure
- **`src/wardrobe/`** - Main package (formerly `claude/`)
- **`tests/`** - Comprehensive test suite  
- **`notebooks/`** - Jupyter notebooks for development
- **`source_data/`** - Your clothing photos and metadata
- **`scripts/`** - Development utilities

## 🛠️ Development
```bash
# Run tests
python scripts/run_tests.py

# Format code
black src/ tests/

# Type checking  
mypy src/
```

## 📖 Documentation
See `src/README.md` for complete documentation including:
- Detailed setup instructions
- API documentation  
- Google Sheets integration
- Testing and development workflows
- Troubleshooting guide

## ✨ What's New
This codebase has been refactored from a collection of scripts into a proper Python package:
- ✅ Modular, testable code structure
- ✅ Comprehensive test coverage
- ✅ Clean imports for Jupyter notebooks
- ✅ Command-line interface
- ✅ Developer-friendly tools and documentation
