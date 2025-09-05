"""Google Sheets utility functions."""


class SheetUtils:
    """Utility functions for working with Google Sheets."""

    @staticmethod
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