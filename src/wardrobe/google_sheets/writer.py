"""Google Sheets writing functionality."""

from collections import defaultdict, OrderedDict
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from .auth import GoogleSheetsAuth


class SheetsWriter:
    """Handles writing data to Google Sheets."""
    
    def __init__(self, auth: GoogleSheetsAuth):
        """Initialize with authentication manager."""
        self.auth = auth
    
    def discover_tag_types(self, items: List[Dict[str, Any]]) -> OrderedDict:
        """Discover all tag types from items."""
        type_key_to_display = OrderedDict()
        saw_untyped = False
        for it in items:
            tags = it.get("tags", [])
            if not isinstance(tags, list):
                continue
            for t in tags:
                if not isinstance(t, str):
                    continue
                if ":" in t:
                    tag_type, _ = t.split(":", 1)
                    key = tag_type.strip().lower()
                    if key not in type_key_to_display:
                        type_key_to_display[key] = tag_type.strip()
                else:
                    saw_untyped = True
        if saw_untyped and "----" not in type_key_to_display:
            type_key_to_display["----"] = "----"
        return type_key_to_display

    def item_tag_values_by_type(self, item: Dict[str, Any], type_key_to_display: OrderedDict) -> Dict[str, List[str]]:
        """Get tag values grouped by type for a single item."""
        values = defaultdict(list)
        tags = item.get("tags", [])
        if isinstance(tags, list):
            for t in tags:
                if not isinstance(t, str):
                    continue
                if ":" in t:
                    tag_type, tag_val = t.split(":", 1)
                    key = tag_type.strip().lower()
                    if key in type_key_to_display:
                        v = tag_val.strip()
                        if v:
                            values[key].append(v)
                else:
                    if "----" in type_key_to_display:
                        v = t.strip()
                        if v:
                            values["----"].append(v)
        return values

    def build_headers(self, type_key_to_display: OrderedDict) -> tuple:
        """
        Two-row header where:
          - Row 1: blanks under base columns; 'Tags' over the tag block (merged horizontally)
          - Row 2: base headers + each tag-type name
        """
        base_headers = [
            "ID", "Title", "Category", "Filename", "Slug",
            "Thumbnail", "Image", "Notes", "Created (UTC ISO8601)"
        ]
        tag_type_headers = [type_key_to_display[k] for k in type_key_to_display]

        # Row 1: base headers, then 'Tags' plus blanks to fill merge width
        row1 = base_headers[:]
        if tag_type_headers:
            row1 += ["Tags"] + [""] * (len(tag_type_headers) - 1)

        # Row 2: empty cells for base columns, then tag-type labels
        row2 = [""] * len(base_headers) + tag_type_headers

        return base_headers, tag_type_headers, [row1, row2]

    def items_to_rows(self, items: List[Dict[str, Any]], base_headers: List[str], type_key_to_display: OrderedDict) -> List[List[str]]:
        """Convert items to spreadsheet rows."""
        rows = []
        for it in items:
            created_ts = it.get("created_date")
            if isinstance(created_ts, (int, float)):
                created_dt = datetime.fromtimestamp(created_ts, tz=timezone.utc)
                created_iso = created_dt.isoformat().replace("+00:00", "Z")
            else:
                created_iso = ""

            base_vals = [
                it.get("id", ""),
                it.get("title", ""),
                it.get("category", ""),
                it.get("filename", ""),
                it.get("slug", ""),
                it.get("thumbnail", ""),
                it.get("image", ""),
                it.get("notes", ""),
                created_iso,
            ]

            per_type = self.item_tag_values_by_type(it, type_key_to_display)
            tag_cols = []
            for key in type_key_to_display.keys():
                vals = per_type.get(key, [])
                tag_cols.append(", ".join(vals) if vals else "")

            rows.append(base_vals + tag_cols)
        return rows

    def create_sheet_and_write_data(self, sheets, drive, title: str, header_rows: List[List[str]], 
                                  data_rows: List[List[str]], num_base_cols: int,
                                  num_tag_cols: int, parent_folder_id: Optional[str] = None) -> str:
        """Create a new sheet and write data to it."""
        file_metadata = {
            "name": title,
            "mimeType": "application/vnd.google-apps.spreadsheet",
        }
        if parent_folder_id:
            file_metadata["parents"] = [parent_folder_id]

        created = drive.files().create(body=file_metadata, fields="id").execute()

        spreadsheet_id = created["id"]

        # Write header rows + data
        values = header_rows + data_rows
        sheets.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range="Sheet1!A1",
            valueInputOption="RAW",
            body={"values": values}
        ).execute()

        total_cols = num_base_cols + num_tag_cols

        requests = []

        # Freeze first 2 rows
        requests.append({
            "updateSheetProperties": {
                "properties": {"sheetId": 0, "gridProperties": {"frozenRowCount": 2}},
                "fields": "gridProperties.frozenRowCount"
            }
        })

        # Auto-size columns
        requests.append({
            "autoResizeDimensions": {
                "dimensions": {"sheetId": 0, "dimension": "COLUMNS", "startIndex": 0, "endIndex": total_cols}
            }
        })

        # Bold both header rows
        requests.append({
            "repeatCell": {
                "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 2, "startColumnIndex": 0, "endColumnIndex": total_cols},
                "cell": {"userEnteredFormat": {"textFormat": {"bold": True}}},
                "fields": "userEnteredFormat.textFormat.bold"
            }
        })

        # Center align row 1
        requests.append({
            "repeatCell": {
                "range": {"sheetId": 0, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": total_cols},
                "cell": {"userEnteredFormat": {"horizontalAlignment": "CENTER"}},
                "fields": "userEnteredFormat.horizontalAlignment"
            }
        })

        # 1) Merge each base column vertically across rows 1–2 (index 0..2)
        for col in range(num_base_cols):
            requests.append({
                "mergeCells": {
                    "range": {
                        "sheetId": 0,
                        "startRowIndex": 0,   # row 1 (index 0)
                        "endRowIndex": 2,     # through row 2 (exclusive)
                        "startColumnIndex": col,
                        "endColumnIndex": col + 1
                    },
                    "mergeType": "MERGE_ALL"
                }
            })

        # 2) Merge the "Tags" header across tag-type columns in Row 1 (index 0)
        if num_tag_cols > 0:
            start_col = num_base_cols
            end_col = num_base_cols + num_tag_cols
            requests.append({
                "mergeCells": {
                    "range": {
                        "sheetId": 0,
                        "startRowIndex": 0,
                        "endRowIndex": 1,     # only the first row
                        "startColumnIndex": start_col,
                        "endColumnIndex": end_col
                    },
                    "mergeType": "MERGE_ALL"
                }
            })

        sheets.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests}
        ).execute()

        return spreadsheet_id

    def share_file(self, drive, file_id: str, email: str):
        """Share a file with a user."""
        if not email:
            return
        drive.permissions().create(
            fileId=file_id,
            body={"type": "user", "role": "writer", "emailAddress": email},
            sendNotificationEmail=True
        ).execute()

    def write_items_to_sheet(self, items: List[Dict[str, Any]], sheet_title: str,
                           parent_folder_id: str, share_with_email: Optional[str] = None) -> str:
        """
        Write items to a new Google Sheet.
        
        Args:
            items: List of item dictionaries to write
            sheet_title: Title for the new sheet
            parent_folder_id: Google Drive folder ID to create sheet in
            share_with_email: Email to share sheet with (optional)
            
        Returns:
            Spreadsheet ID of created sheet
        """
        sheets, drive = self.auth.get_readwrite_services()

        type_key_to_display = self.discover_tag_types(items)
        base_headers, tag_type_headers, two_row_header = self.build_headers(type_key_to_display)
        data_rows = self.items_to_rows(items, base_headers, type_key_to_display)

        spreadsheet_id = self.create_sheet_and_write_data(
            sheets=sheets,
            drive=drive,
            title=sheet_title,
            header_rows=two_row_header,
            data_rows=data_rows,
            num_base_cols=len(base_headers),
            num_tag_cols=len(tag_type_headers),
            parent_folder_id=parent_folder_id
        )
        
        if share_with_email:
            self.share_file(drive, spreadsheet_id, share_with_email)
        
        return spreadsheet_id