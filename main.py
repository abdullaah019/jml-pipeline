import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from detector import detect_changes, load_google_sheet, load_snapshot
from joiner import handle_joiner
from leaver import handle_leaver
from mover import handle_mover

HANDLERS = {
    "joiner": handle_joiner,
    "mover": handle_mover,
    "leaver": handle_leaver,
}

SNAPSHOT_PATH = Path(__file__).parent / "state" / "snapshot.json"


def save_snapshot(employees: dict) -> None:
    snapshot = {
        "run_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "employees": employees,
    }
    SNAPSHOT_PATH.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(f"Snapshot updated at {snapshot['run_timestamp']}")


def main() -> None:
    print("=== JML Pipeline ===\n")

    current = load_google_sheet()
    previous = load_snapshot(SNAPSHOT_PATH)

    changes = detect_changes(current, previous)

    if not changes:
        print("No changes detected — snapshot is up to date.\n")
    else:
        print(f"Detected {len(changes)} change(s):\n")
        for change in changes:
            HANDLERS[change["type"]](change["employee"])

    save_snapshot(current)
    print("\nDone.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("\n=== PIPELINE ERROR ===", flush=True)
        traceback.print_exc()
        print(f"\n{type(exc).__name__}: {exc}", flush=True)
        sys.exit(1)
