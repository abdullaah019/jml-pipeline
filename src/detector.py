import json
import os
from pathlib import Path

import gspread
import google.auth
import google.auth.transport.requests

_SHEET_SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def load_google_sheet() -> dict:
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise ValueError("GOOGLE_SHEET_ID environment variable is not set")

    creds, _ = google.auth.default(scopes=_SHEET_SCOPES)
    client = gspread.Client(auth=creds)
    client.session = google.auth.transport.requests.AuthorizedSession(creds)
    sheet = client.open_by_key(sheet_id).sheet1
    rows = sheet.get_all_records()

    return {row["employee_id"]: {k: str(v) for k, v in row.items()} for row in rows}


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
