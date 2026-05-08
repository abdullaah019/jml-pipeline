import secrets

from auth import DOMAIN, get_directory_service


def _department_group(department: str) -> str:
    return f"{department.lower()}@{DOMAIN}"


def handle_joiner(employee: dict) -> None:
    print(f"  [JOINER] Provisioning {employee['name']} ({employee['employee_id']})")

    service = get_directory_service()

    first, _, last = employee["name"].partition(" ")

    user_body = {
        "primaryEmail": employee["email"],
        "name": {"givenName": first, "familyName": last},
        "password": secrets.token_urlsafe(16),
        "changePasswordAtNextLogin": True,
        "orgUnitPath": f"/{employee['department']}",
        "organizations": [
            {
                "title": employee["role"],
                "department": employee["department"],
                "primary": True,
            }
        ],
    }

    if employee.get("manager_email"):
        user_body["relations"] = [
            {"value": employee["manager_email"], "type": "manager"}
        ]

    service.users().insert(body=user_body).execute()
    print(f"    Created Google Workspace account: {employee['email']}")

    group_email = _department_group(employee["department"])
    service.members().insert(
        groupKey=group_email,
        body={"email": employee["email"], "role": "MEMBER"},
    ).execute()
    print(f"    Added to group: {group_email}")

    print(f"  Done — account created for {employee['email']}\n")
