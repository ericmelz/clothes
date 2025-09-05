"""Google Sheets reading functionality."""

from typing import Dict, List, Tuple, Any
from datetime import datetime

from .auth import GoogleSheetsAuth
from .sheet_utils import SheetUtils


# Expected base headers (row 1), produced by the writer script
BASE_HEADERS = [
    "ID",
    "Title", 
    "Category",
    "Filename",
    "Slug",
    "Thumbnail",
    "Image",
    "Notes",
    "Created (UTC ISO8601)",
]


class SheetsReader:
    """Handles reading data from Google Sheets."""
    
    def __init__(self, auth: GoogleSheetsAuth):
        """Initialize with authentication manager."""
        self.auth = auth


    def get_first_sheet_title(self, sheets, spreadsheet_id: str) -> str:
        """Get the title of the first sheet in a spreadsheet."""
        meta = sheets.spreadsheets().get(
            spreadsheetId=spreadsheet_id,
            fields="sheets(properties(title))",
        ).execute()
        sheet_props = meta.get("sheets", [])
        if not sheet_props:
            raise RuntimeError("Spreadsheet has no sheets.")
        return sheet_props[0]["properties"]["title"]
    
    def read_all_values(self, sheets, spreadsheet_id: str, sheet_title: str) -> List[List[str]]:
        """
        Read all values from the first sheet. We read a generous range.
        """
        # A very wide range to capture all columns/rows that might have data
        rng = f"'{sheet_title}'!A1:ZZ100000"
        resp = sheets.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=rng,
            majorDimension="ROWS",
        ).execute()
        return resp.get("values", [])

    def locate_tag_block(self, header_row1: List[str], header_row2: List[str]) -> Tuple[int, List[str]]:
        """
        Using the two-row header:
          - Row 1 contains base_headers and 'Tags' in the first tag column (others blank).
          - Row 2 contains blanks then per-tag-type headers.
        Returns (tag_start_index, tag_type_headers)
        """
        # Find "Tags" cell in row 1; if not present, assume no tag block.
        tag_start = None
        for i, v in enumerate(header_row1):
            if (v or "").strip().lower() == "tags":
                tag_start = i
                break

        if tag_start is None:
            # No "Tags" label; assume no tags -> tag_start at end of base headers
            tag_start = len(header_row2)

        tag_type_headers = header_row2[tag_start:] if tag_start < len(header_row2) else []
        return tag_start, tag_type_headers

    def map_base_columns(self, header_row1: List[str]) -> Dict[str, int]:
        """
        Map expected base headers (exact match) to their indices, if present.
        """
        name_to_idx = {}
        for idx, name in enumerate(header_row1):
            if name in BASE_HEADERS:
                name_to_idx[name] = idx
        return name_to_idx

    def parse_iso_to_epoch(self, iso_str: str) -> int:
        """
        Convert an ISO-8601 string (with 'Z' or offset) to epoch seconds (int).
        Returns 0 if empty or unparsable.
        """
        if not iso_str:
            return 0
        s = iso_str.strip()
        try:
            # Support trailing 'Z'
            if s.endswith("Z"):
                dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(s)
            return int(dt.timestamp())
        except Exception:
            return 0

    def assemble_tags_from_row(self, row: List[str], tag_start: int, tag_types: List[str]) -> List[str]:
        """
        Given a data row and tag columns definition, return a list of tag strings:
          - For type 'color' and cell 'red, blue' -> ['color:red', 'color:blue']
          - For type '----' and cell 'Shirt, Cotton' -> ['Shirt', 'Cotton']
        """
        tags: List[str] = []
        for offset, tag_type in enumerate(tag_types):
            col_idx = tag_start + offset
            cell = row[col_idx].strip() if col_idx < len(row) and row[col_idx] is not None else ""
            if not cell:
                continue
            # Split on commas, keep order
            parts = [p.strip() for p in cell.split(",") if p.strip()]
            if tag_type == "----":
                tags.extend(parts)
            else:
                for p in parts:
                    tags.append(f"{tag_type}:{p}")
        return tags

    def row_to_item(
            self,
            row: List[str],
            base_idx: Dict[str, int],
            tag_start: int,
            tag_types: List[str],
    ) -> Dict:
        """
        Convert one sheet row into an 'item' dict in the original JSON shape.
        """
        def get(name: str) -> str:
            i = base_idx.get(name, -1)
            return (row[i] if (i >= 0 and i < len(row)) else "").strip()

        created_iso = get("Created (UTC ISO8601)")
        created_epoch = self.parse_iso_to_epoch(created_iso)

        item = {
            "id": get("ID"),
            "title": get("Title"),
            "category": get("Category"),
            "filename": get("Filename"),
            "slug": get("Slug"),
            "thumbnail": get("Thumbnail"),
            "image": get("Image"),
            "notes": get("Notes"),
            "created_date": created_epoch,
            "tags": self.assemble_tags_from_row(row, tag_start, tag_types),
        }
        return item

    def sheet_to_items(self, values: List[List[str]]) -> List[Dict]:
        """
        Convert a 2D array from Sheets into a list of items matching the
        original writer script's JSON schema.
        """
        if len(values) < 2:
            return []

        # Two-row header
        row1 = values[0]
        row2 = values[1]

        tag_start, tag_types = self.locate_tag_block(row1, row2)
        base_idx = self.map_base_columns(row1)

        items: List[Dict] = []
        for row in values[2:]:
            # skip entirely blank rows
            if not any((cell or "").strip() for cell in row):
                continue
            it = self.row_to_item(row, base_idx, tag_start, tag_types)
            items.append(it)

        return items

    def read_sheet_data(self, parent_folder_id: str, sheet_name: str) -> Dict[str, Any]:
        """
        Read data from a Google Sheet and return as item dictionary.
        
        Args:
            parent_folder_id: Google Drive folder ID containing the sheet
            sheet_name: Name of the spreadsheet file
            
        Returns:
            Dictionary mapping item IDs to item data
        """
        sheets, drive = self.auth.get_readonly_services()

        print(f"Looking for '{sheet_name}' in folder {parent_folder_id}...")
        spreadsheet_id = SheetUtils.find_sheet_in_folder(drive, parent_folder_id, sheet_name)

        sheet_title = self.get_first_sheet_title(sheets, spreadsheet_id)
        values = self.read_all_values(sheets, spreadsheet_id, sheet_title)

        items = self.sheet_to_items(values)
        id_to_items = {}
        for item in items:
            id_to_items[item['id']] = item
        return id_to_items