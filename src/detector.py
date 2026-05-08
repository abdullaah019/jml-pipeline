import csv
import io
import json
import os
from pathlib import Path

import requests


def load_google_sheet() -> dict:
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise ValueError("GOOGLE_SHEET_ID environment variable is not set")

    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    reader = csv.DictReader(io.StringIO(response.text))
    return {
        row["employee_id"]: {k: str(v) for k, v in row.items()}
        for row in reader
        if row.get("employee_id")
    }


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
