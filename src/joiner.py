GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"


def _create_entra_user(employee: dict) -> str:
    """POST /users — create the Entra ID account. Returns the new user's object ID."""
    print(f"    [API] POST {GRAPH_API_BASE}/users")
    print(f"           displayName={employee['name']}, mail={employee['email']}")
    return "placeholder-object-id"


def _assign_license(object_id: str, employee: dict) -> None:
    """POST /users/{id}/assignLicense — assign an M365 license."""
    print(f"    [API] POST {GRAPH_API_BASE}/users/{object_id}/assignLicense")
    print(f"           skuId=placeholder-sku-id (M365 Business Standard)")


def _add_to_department_group(object_id: str, employee: dict) -> None:
    """POST /groups/{id}/members/$ref — add user to their department group."""
    print(f"    [API] POST {GRAPH_API_BASE}/groups/placeholder-{employee['department'].lower()}-group-id/members/$ref")
    print(f"           userId={object_id}")


def _set_manager(object_id: str, employee: dict) -> None:
    """PUT /users/{id}/manager/$ref — set the reporting manager."""
    if not employee.get("manager_email"):
        return
    print(f"    [API] PUT {GRAPH_API_BASE}/users/{object_id}/manager/$ref")
    print(f"           managerEmail={employee['manager_email']}")


def handle_joiner(employee: dict) -> None:
    print(f"  [JOINER] Provisioning {employee['name']} ({employee['employee_id']})")

    object_id = _create_entra_user(employee)
    _assign_license(object_id, employee)
    _add_to_department_group(object_id, employee)
    _set_manager(object_id, employee)

    print(f"  Done — account created for {employee['email']}\n")
