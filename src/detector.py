import json
import os
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build

_SHEET_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def _sa_credentials(scopes: list) -> service_account.Credentials:
    key_json = os.environ.get("GCP_SA_KEY")
    if not key_json:
        raise ValueError("GCP_SA_KEY environment variable is not set")
    return service_account.Credentials.from_service_account_info(
        json.loads(key_json), scopes=scopes
    )


def load_google_sheet() -> dict:
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise ValueError("GOOGLE_SHEET_ID environment variable is not set")

    service = build("sheets", "v4", credentials=_sa_credentials(_SHEET_SCOPES), cache_discovery=False)
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=sheet_id, range="Sheet1")
        .execute()
    )
    values = result.get("values", [])
    if not values:
        return {}
    headers = values[0]
    rows = [dict(zip(headers, row + [""] * (len(headers) - len(row)))) for row in values[1:]]
    return {row["employee_id"]: {k: str(v) for k, v in row.items()} for row in rows if row.get("employee_id")}


def load_snapshot(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["employees"]


def detect_changes(current: dict, previous: dict) -> list:
    changes = []

    for emp_id, emp in current.items():
        if emp_id not in previous:
            changes.append({"type": "joiner", "employee": emp})
            continue

        prev_status = previous[emp_id]["status"]
        curr_status = emp["status"]

        if prev_status == curr_status:
            continue

        if curr_status == "terminated":
            changes.append({"type": "leaver", "employee": emp})
        elif curr_status == "mover":
            changes.append({"type": "mover", "employee": emp})

    for emp_id, emp in previous.items():
        if emp_id not in current:
            changes.append({"type": "leaver", "employee": emp})

    return changes


def main():
    root = Path(__file__).parent.parent
    current = load_google_sheet()
    previous = load_snapshot(root / "state" / "snapshot.json")

    changes = detect_changes(current, previous)

    print(f"Detected {len(changes)} change(s):\n")
    for change in changes:
        emp = change["employee"]
        print(f"  [{change['type'].upper()}] {emp['name']} ({emp['employee_id']})")
        print(f"    Role:       {emp['role']}")
        print(f"    Department: {emp['department']}")
        print(f"    Status:     {emp['status']}")
        print(f"    Email:      {emp['email']}")
        print()

    return changes


if __name__ == "__main__":
    main()
