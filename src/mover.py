import json
import os

import requests


def handle_mover(employee: dict) -> None:
    print(f"  [MOVER] Updating {employee['name']} ({employee['employee_id']})")

    webhook_url = os.environ.get("APPS_SCRIPT_WEBHOOK_URL")
    payload = {"action": "mover", "employee": employee}

    if not webhook_url:
        print(f"    [DRY RUN] Would POST to Apps Script webhook:")
        print(f"    {json.dumps(payload, indent=6)}")
        print(f"  Done — skipped (APPS_SCRIPT_WEBHOOK_URL not set)\n")
        return

    response = requests.post(webhook_url, json=payload, timeout=30)
    response.raise_for_status()
    print(f"    Webhook response: {response.status_code}")
    print(f"  Done — mover webhook fired for {employee['email']}\n")
