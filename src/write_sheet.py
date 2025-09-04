import json
import os
from collections import defaultdict, OrderedDict
from datetime import datetime, timezone

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ----------------------------
# CONFIG — edit these as needed
# ----------------------------
DATA_PATH = "source_data/erics-clothes/wardrobe_data.json"   # path to your JSON file
SHEET_TITLE = "Wardrobe Inventory (Tags grouped)"
SHARE_WITH_EMAIL = "eric@emelz.com"  # set to None to skip sharing
PARENT_FOLDER_ID = "1d1KFAo3jcomqzm05vpY5S_Vmbrh5_lyw"


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]

def get_google_services():
    creds = None
    token_path = "../token.json"
    creds_path = "../credentials.json"

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                raise FileNotFoundError(
                    "credentials.json not found. Download it from Google Cloud Console "
                    "(OAuth 2.0 Client IDs -> Desktop App) and place it next to this script."
                )
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as f:
            f.write(creds.to_json())

    sheets = build("sheets", "v4", credentials=creds)
    drive = build("drive", "v3", credentials=creds)
    return sheets, drive

def load_items(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)
    return data.get("items", [])

def discover_tag_types(items):
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

def item_tag_values_by_type(item, type_key_to_display):
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

def build_headers(type_key_to_display):
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

def items_to_rows(items, base_headers, type_key_to_display):
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

        per_type = item_tag_values_by_type(it, type_key_to_display)
        tag_cols = []
        for key in type_key_to_display.keys():
            vals = per_type.get(key, [])
            tag_cols.append(", ".join(vals) if vals else "")

        rows.append(base_vals + tag_cols)
    return rows

def create_sheet_and_write_data(sheets, drive, title, header_rows, data_rows, num_base_cols,
                                num_tag_cols, parent_folder_id=None):
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

def optionally_share_file(drive, file_id, email):
    if not email:
        return
    drive.permissions().create(
        fileId=file_id,
        body={"type": "user", "role": "writer", "emailAddress": email},
        sendNotificationEmail=True
    ).execute()

def main():
    sheets, drive = get_google_services()
    items = load_items(DATA_PATH)

    type_key_to_display = discover_tag_types(items)
    base_headers, tag_type_headers, two_row_header = build_headers(type_key_to_display)
    data_rows = items_to_rows(items, base_headers, type_key_to_display)

    parent_folder_id = PARENT_FOLDER_ID
    spreadsheet_id = create_sheet_and_write_data(
        sheets=sheets,
        drive=drive,
        title=SHEET_TITLE,
        header_rows=two_row_header,
        data_rows=data_rows,
        num_base_cols=len(base_headers),
        num_tag_cols=len(tag_type_headers),
        parent_folder_id=PARENT_FOLDER_ID
    )
    optionally_share_file(drive, spreadsheet_id, SHARE_WITH_EMAIL)
    print(f"Created: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")

if __name__ == "__main__":
    main()
