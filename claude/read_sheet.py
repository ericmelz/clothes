import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ----------------------------
# CONFIG — edit these as needed
# ----------------------------
PARENT_FOLDER_ID = "1d1KFAo3jcomqzm05vpY5S_Vmbrh5_lyw"
PEOPLE = ["eric", "randi"]

# Output root directory
OUTPUT_ROOT = Path("output")

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

# OAuth scopes (read-only)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


# -------- Auth / Clients --------
def get_google_services():
    """
    Returns authorized Sheets and Drive service clients.
    Expects credentials.json in the working directory on first run.
    """
    creds = None
    token_path = "../token_readonly.json"   # separate cache from your writer token if you like
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


# -------- Drive helpers --------
def find_sheet_in_folder(drive, folder_id: str, filename: str) -> str:
    """
    Return the spreadsheet file ID for a file named `filename` within `folder_id`.
    Raises FileNotFoundError if not found.
    """
    q = (
        f"name = '{filename}' and "
        f"'{folder_id}' in parents and "
        f"mimeType = 'application/vnd.google-apps.spreadsheet' and "
        f"trashed = false"
    )
    resp = drive.files().list(
        q=q,
        spaces="drive",
        fields="files(id, name)",
        pageSize=10,
    ).execute()
    files = resp.get("files", [])
    if not files:
        raise FileNotFoundError(
            f"Sheet named '{filename}' not found in folder {folder_id}."
        )
    # If multiple, take the first
    return files[0]["id"]


# -------- Sheets helpers --------
def get_first_sheet_title(sheets, spreadsheet_id: str) -> str:
    meta = sheets.spreadsheets().get(
        spreadsheetId=spreadsheet_id,
        fields="sheets(properties(title))",
    ).execute()
    sheet_props = meta.get("sheets", [])
    if not sheet_props:
        raise RuntimeError("Spreadsheet has no sheets.")
    return sheet_props[0]["properties"]["title"]


def read_all_values(sheets, spreadsheet_id: str, sheet_title: str) -> List[List[str]]:
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


# -------- Parsing helpers --------
def locate_tag_block(header_row1: List[str], header_row2: List[str]) -> Tuple[int, List[str]]:
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


def map_base_columns(header_row1: List[str]) -> Dict[str, int]:
    """
    Map expected base headers (exact match) to their indices, if present.
    """
    name_to_idx = {}
    for idx, name in enumerate(header_row1):
        if name in BASE_HEADERS:
            name_to_idx[name] = idx
    return name_to_idx


def parse_iso_to_epoch(iso_str: str) -> int:
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


def assemble_tags_from_row(row: List[str], tag_start: int, tag_types: List[str]) -> List[str]:
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
    created_epoch = parse_iso_to_epoch(created_iso)

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
        "tags": assemble_tags_from_row(row, tag_start, tag_types),
    }
    return item


def sheet_to_items(values: List[List[str]]) -> List[Dict]:
    """
    Convert a 2D array from Sheets into a list of items matching the
    original writer script's JSON schema.
    """
    if len(values) < 2:
        return []

    # Two-row header
    row1 = values[0]
    row2 = values[1]

    tag_start, tag_types = locate_tag_block(row1, row2)
    base_idx = map_base_columns(row1)

    items: List[Dict] = []
    for row in values[2:]:
        # skip entirely blank rows
        if not any((cell or "").strip() for cell in row):
            continue
        it = row_to_item(row, base_idx, tag_start, tag_types)
        items.append(it)

    return items


# -------- Main flow --------
def process_person(sheets, drive, person: str, parent_folder_id: str):
    filename = f"{person}-wardrobe"
    print(f"Looking for '{filename}' in folder {parent_folder_id}...")
    spreadsheet_id = find_sheet_in_folder(drive, parent_folder_id, filename)

    sheet_title = get_first_sheet_title(sheets, spreadsheet_id)
    values = read_all_values(sheets, spreadsheet_id, sheet_title)

    items = sheet_to_items(values)
    out_dir = OUTPUT_ROOT / f"{person}s-clothes"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "wardrobe_data2.json"

    with open(out_path, "w") as f:
        json.dump({"items": items}, f, indent=2)

    print(f"Wrote {out_path}  ({len(items)} items)")


def main():
    sheets, drive = get_google_services()
    for person in PEOPLE:
        try:
            process_person(sheets, drive, person, PARENT_FOLDER_ID)
        except FileNotFoundError as e:
            print(f"[WARN] {e}")
        except Exception as e:
            print(f"[ERROR] Failed for {person}: {e}")


if __name__ == "__main__":
    main()
