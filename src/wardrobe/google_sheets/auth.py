"""Google Sheets authentication utilities."""

import os
from pathlib import Path
from typing import List, Tuple

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


class GoogleSheetsAuth:
    """Handles Google Sheets authentication and service creation."""
    
    # OAuth scopes
    READONLY_SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    
    READWRITE_SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
        "https://www.googleapis.com/auth/drive",
    ]
    
    def __init__(self, 
                 credentials_path: str = "../credentials.json",
                 readonly_token_path: str = "../token_readonly.json",
                 readwrite_token_path: str = "../token.json"):
        """
        Initialize authentication manager.
        
        Args:
            credentials_path: Path to OAuth credentials JSON file
            readonly_token_path: Path to readonly token cache
            readwrite_token_path: Path to read/write token cache
        """
        self.credentials_path = Path(credentials_path).resolve()
        self.readonly_token_path = Path(readonly_token_path).resolve()
        self.readwrite_token_path = Path(readwrite_token_path).resolve()
    
    def _get_credentials(self, scopes: List[str], token_path: Path) -> Credentials:
        """Get or refresh Google credentials for given scopes."""
        creds = None
        
        # Load existing token
        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), scopes)
        
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_path}. "
                        "Download it from Google Cloud Console "
                        "(OAuth 2.0 Client IDs -> Desktop App)."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), scopes
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(token_path, "w") as f:
                f.write(creds.to_json())
        
        return creds
    
    def get_readonly_services(self) -> Tuple:
        """
        Get read-only Sheets and Drive service clients.
        
        Returns:
            Tuple of (sheets_service, drive_service)
        """
        creds = self._get_credentials(self.READONLY_SCOPES, self.readonly_token_path)
        sheets = build("sheets", "v4", credentials=creds)
        drive = build("drive", "v3", credentials=creds)
        return sheets, drive
    
    def get_readwrite_services(self) -> Tuple:
        """
        Get read/write Sheets and Drive service clients.
        
        Returns:
            Tuple of (sheets_service, drive_service)
        """
        creds = self._get_credentials(self.READWRITE_SCOPES, self.readwrite_token_path)
        sheets = build("sheets", "v4", credentials=creds)
        drive = build("drive", "v3", credentials=creds)
        return sheets, drive