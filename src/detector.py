import csv
import json
from pathlib import Path


def load_csv(path: str) -> dict:
    employees = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            employees[row["employee_id"]] = row
    return employees


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
    current = load_csv(root / "data" / "employees.csv")
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
