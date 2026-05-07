import os

import requests
from googleapiclient.errors import HttpError

from auth import DOMAIN, get_directory_service

TEAMS_WEBHOOK_URL = os.environ.get(
    "TEAMS_WEBHOOK_URL",
    "https://placeholder.webhook.office.com/webhookb2/placeholder",
)


def handle_leaver(employee: dict) -> None:
    print(f"  [LEAVER] Offboarding {employee['name']} ({employee['employee_id']})")

    service = get_directory_service()

    service.users().patch(
        userKey=employee["email"],
        body={"suspended": True},
    ).execute()
    print(f"    Suspended account: {employee['email']}")

    current_groups = (
        service.groups()
        .list(userKey=employee["email"], domain=DOMAIN)
        .execute()
        .get("groups", [])
    )

    for group in current_groups:
        try:
            service.members().delete(
                groupKey=group["email"], memberKey=employee["email"]
            ).execute()
            print(f"    Removed from group: {group['email']}")
        except HttpError as e:
            if e.resp.status != 404:
                raise

    _notify_manager_via_teams(employee)

    print(f"  Done — {employee['email']} fully offboarded\n")


def _notify_manager_via_teams(employee: dict) -> None:
    if not employee.get("manager_email"):
        print("    [TEAMS] No manager on record — skipping notification")
        return

    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "type": "AdaptiveCard",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": f"Offboarding Notice: {employee['name']}",
                            "weight": "Bolder",
                            "size": "Medium",
                        },
                        {
                            "type": "FactSet",
                            "facts": [
                                {"title": "Employee", "value": employee["name"]},
                                {"title": "ID", "value": employee["employee_id"]},
                                {"title": "Role", "value": employee["role"]},
                                {"title": "Department", "value": employee["department"]},
                                {"title": "Email", "value": employee["email"]},
                            ],
                        },
                        {
                            "type": "TextBlock",
                            "text": "The account has been suspended and all group memberships removed. Please arrange asset retrieval and access handover.",
                            "wrap": True,
                        },
                    ],
                },
            }
        ],
    }

    response = requests.post(TEAMS_WEBHOOK_URL, json=payload, timeout=10)
    response.raise_for_status()
    print(f"    [TEAMS] Notified manager: {employee['manager_email']}")
