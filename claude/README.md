# Wardrobe Collection Website

A static website generator and browser for your clothing collection. Takes photos from organized directories and creates a searchable, browsable website with thumbnails and detailed views.

## Features

- **Image Processing**: Converts HEIC photos to web-friendly JPEGs
- **Thumbnail Generation**: Creates optimized thumbnails for grid view
- **Search & Filter**: Search by title/tags and filter by category
- **Responsive Design**: Works on desktop and mobile devices
- **URL Routing**: Direct links to individual items
- **JSON Data Structure**: Easily editable metadata for customization

## Project Structure

```
source-data/
    source_photos/          # Original photos organized by category
        wardrobe_data.json  # Item metadata
        Shirts/             # Shirt photos (HEIC format)
        Pants/              # Pants photos (HEIC format)
        [Other Categories]/
output/                     # Generated website files - also copied to website/
    wardrobe_data.json      # Item metadata
    images/                 # Processed images
        thumbs/             # Thumbnail images (300x300)
        full/               # Full-size web images (max 1200px)
    website/                # Static website files
        index.html          # Main HTML page
        styles.css          # CSS styles
        src/
            App.js          # React application
generate_site.py            # Site generator script
serve_website.py            # Local development server
```

## Setup

1. **Install Dependencies**:
   ```bash
   uv sync
   ```

2. **Add Your Photos**:
   - Place photos in `source_photos/` organized by category
   - Supported formats: HEIC, JPG, JPEG, PNG, WebP
   - Categories are determined by directory names

3. **Generate Website**:
   ```bash
   uv run generate_site.py
   ```

4. **Serve Locally**:
   ```bash
   uv run serve_website.py
   ```
   
   Visit http://localhost:8000/website/ to view your wardrobe collection.

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

## Technology Stack

- **Backend**: Python with uv package management
- **Image Processing**: Pillow + pillow-heif for HEIC support
- **Frontend**: React.js (browser build, no compilation needed)
- **Styling**: Pure CSS with responsive design
- **Data**: JSON file for metadata storage

## Future Enhancements

The architecture supports easy extension to:
- Backend database integration
- User authentication
- Advanced tagging system
- Outfit planning features
- Image analysis for automatic tagging
- Shopping list integration

## Development

To modify the React application, edit `output/website/src/App.js`. The app uses:
- React Hooks for state management
- Browser history API for routing
- Fetch API for loading JSON data
- CSS Grid and Flexbox for layout

No build process is needed - the browser loads React and Babel directly for development simplicity.