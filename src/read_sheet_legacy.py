# TODO get rid of this
#!/usr/bin/env python3
"""
Legacy read_sheet.py - now imports from new modular structure.
This file is kept for backwards compatibility.
"""

import json
from pathlib import Path

from wardrobe.google_sheets import GoogleSheetsAuth, SheetsReader


def main():
    """Main function using new modular structure."""
    # Configuration from original script
    PARENT_FOLDER_ID = "1d1KFAo3jcomqzm05vpY5S_Vmbrh5_lyw"
    PEOPLE = ["eric", "randi"]
    OUTPUT_ROOT = Path("output")
    
    # Initialize components
    auth = GoogleSheetsAuth()
    reader = SheetsReader(auth)
    
    for person in PEOPLE:
        try:
            filename = f"{person}-wardrobe"
            items_dict = reader.read_sheet_data(PARENT_FOLDER_ID, filename)
            
            # Convert back to list format for compatibility
            items = list(items_dict.values())
            
            out_dir = OUTPUT_ROOT / f"{person}s-clothes"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / "wardrobe_data2.json"

            with open(out_path, "w") as f:
                json.dump({"items": items}, f, indent=2)

            print(f"Wrote {out_path}  ({len(items)} items)")
            
        except FileNotFoundError as e:
            print(f"[WARN] {e}")
        except Exception as e:
            print(f"[ERROR] Failed for {person}: {e}")


if __name__ == "__main__":
    main()