from googleapiclient.errors import HttpError

from auth import DOMAIN, get_directory_service


def _department_group(department: str) -> str:
    return f"{department.lower()}@{DOMAIN}"


def handle_mover(employee: dict) -> None:
    print(f"  [MOVER] Updating {employee['name']} ({employee['employee_id']})")

    service = get_directory_service()
    new_group = _department_group(employee["department"])

    if service is None:
        print(f"    [DRY RUN] Would update profile: role={employee['role']}, dept={employee['department']}")
        print(f"    [DRY RUN] Would update group membership to: {new_group}")
        print(f"  Done — skipped (GCP_SA_KEY not set)\n")
        return

    patch_body = {
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
        patch_body["relations"] = [
            {"value": employee["manager_email"], "type": "manager"}
        ]

    service.users().patch(userKey=employee["email"], body=patch_body).execute()
    print(f"    Updated profile: role={employee['role']}, dept={employee['department']}")

    current_groups = (
        service.groups()
        .list(userKey=employee["email"], domain=DOMAIN)
        .execute()
        .get("groups", [])
    )

    for group in current_groups:
        if group["email"] == new_group:
            continue
        try:
            service.members().delete(
                groupKey=group["email"], memberKey=employee["email"]
            ).execute()
            print(f"    Removed from group: {group['email']}")
        except HttpError as e:
            if e.resp.status != 404:
                raise

    try:
        service.members().insert(
            groupKey=new_group,
            body={"email": employee["email"], "role": "MEMBER"},
        ).execute()
        print(f"    Added to group: {new_group}")
    except HttpError as e:
        if e.resp.status == 409:
            print(f"    Already a member of: {new_group}")
        else:
            raise

    print(f"  Done — profile updated for {employee['email']}\n")
