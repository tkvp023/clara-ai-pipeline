"""
tracker.py - Log pipeline results to Google Sheets (free)

Setup:
1. Go to console.cloud.google.com
2. Create a project → Enable Google Sheets API
3. Create a Service Account → Download JSON key
4. Share your Google Sheet with the service account email
5. Set GOOGLE_SHEET_ID and GOOGLE_SERVICE_ACCOUNT_JSON in .env

If you skip Google Sheets, results are still saved to tracker.json locally.
"""

import os
import json
from pathlib import Path
from datetime import datetime

# Only import gspread if available
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSHEETS_AVAILABLE = True
except ImportError:
    GSHEETS_AVAILABLE = False


def get_sheet_client():
    """Initialize Google Sheets client from service account JSON in env."""
    if not GSHEETS_AVAILABLE:
        return None

    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")

    if not creds_json or not sheet_id:
        return None

    try:
        creds_data = json.loads(creds_json)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_data, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_key(sheet_id)
    except Exception as e:
        print(f"  ⚠️  Google Sheets connection failed: {e}")
        return None


def ensure_sheet_headers(sheet):
    """Make sure the tracker sheet has the right headers."""
    try:
        ws = sheet.worksheet("Pipeline Tracker")
    except gspread.WorksheetNotFound:
        ws = sheet.add_worksheet("Pipeline Tracker", rows=1000, cols=10)

    headers = ws.row_values(1)
    if not headers:
        ws.append_row([
            "Account ID", "Company Name", "Pipeline",
            "Version", "Status", "Changes",
            "Transcript File", "Output Dir", "Processed At"
        ])
    return ws


def log_to_sheets(account_id: str, company_name: str, pipeline: str,
                  version: str, status: str, changes: int = 0,
                  transcript_file: str = "", output_dir: str = ""):
    """
    Log a pipeline result to Google Sheets.
    Falls back gracefully to local JSON if Sheets not configured.
    """
    record = {
        "account_id": account_id,
        "company_name": company_name,
        "pipeline": pipeline,
        "version": version,
        "status": status,
        "changes": changes,
        "transcript_file": transcript_file,
        "output_dir": output_dir,
        "processed_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }

    # Try Google Sheets first
    sheet = get_sheet_client()
    if sheet:
        try:
            ws = ensure_sheet_headers(sheet)
            ws.append_row([
                record["account_id"],
                record["company_name"],
                record["pipeline"],
                record["version"],
                record["status"],
                record["changes"],
                record["transcript_file"],
                record["output_dir"],
                record["processed_at"]
            ])
            print(f"  📊 Logged to Google Sheets: {account_id}")
        except Exception as e:
            print(f"  ⚠️  Sheets write failed: {e}")
            _log_locally(record)
    else:
        _log_locally(record)

    return record


def _log_locally(record: dict):
    """Fallback: append to a local JSONL log file."""
    log_path = Path(__file__).parent.parent / "outputs" / "pipeline_log.jsonl"
    log_path.parent.mkdir(exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(record) + "\n")
    print(f"  📝 Logged locally: {log_path.name}")
