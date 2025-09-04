#!/usr/bin/env python3
"""
Legacy write_sheet.py - now imports from new modular structure.
This file is kept for backwards compatibility.
"""

import json

from wardrobe.google_sheets import GoogleSheetsAuth, SheetsWriter


def load_items(json_path):
    """Load items from JSON file."""
    with open(json_path, "r") as f:
        data = json.load(f)
    return data.get("items", [])


def main():
    """Main function using new modular structure."""
    # Configuration from original script
    DATA_PATH = "source_data/erics-clothes/wardrobe_data.json"
    SHEET_TITLE = "Wardrobe Inventory (Tags grouped)"
    SHARE_WITH_EMAIL = "eric@emelz.com"
    PARENT_FOLDER_ID = "1d1KFAo3jcomqzm05vpY5S_Vmbrh5_lyw"
    
    # Initialize components
    auth = GoogleSheetsAuth()
    writer = SheetsWriter(auth)
    
    # Load and write data
    items = load_items(DATA_PATH)
    spreadsheet_id = writer.write_items_to_sheet(
        items=items,
        sheet_title=SHEET_TITLE,
        parent_folder_id=PARENT_FOLDER_ID,
        share_with_email=SHARE_WITH_EMAIL
    )
    print(f"Created: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")


if __name__ == "__main__":
    main()