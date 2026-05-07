GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"


def _get_user_object_id(employee: dict) -> str:
    """GET /users/{email} — resolve email to Entra object ID."""
    print(f"    [API] GET {GRAPH_API_BASE}/users/{employee['email']}")
    return "placeholder-object-id"


def _update_user_profile(object_id: str, employee: dict) -> None:
    """PATCH /users/{id} — update job title and department attributes."""
    print(f"    [API] PATCH {GRAPH_API_BASE}/users/{object_id}")
    print(f"           jobTitle={employee['role']}, department={employee['department']}")


def _update_manager(object_id: str, employee: dict) -> None:
    """PUT /users/{id}/manager/$ref — reassign reporting manager."""
    if not employee.get("manager_email"):
        return
    print(f"    [API] PUT {GRAPH_API_BASE}/users/{object_id}/manager/$ref")
    print(f"           managerEmail={employee['manager_email']}")


def _remove_from_old_groups(object_id: str, employee: dict) -> None:
    """DELETE /groups/{id}/members/{userId}/$ref — strip previous department group memberships."""
    print(f"    [API] GET {GRAPH_API_BASE}/users/{object_id}/memberOf (fetch current groups)")
    print(f"    [API] DELETE {GRAPH_API_BASE}/groups/placeholder-old-group-id/members/{object_id}/$ref")


def _add_to_new_group(object_id: str, employee: dict) -> None:
    """POST /groups/{id}/members/$ref — add to new department group."""
    print(f"    [API] POST {GRAPH_API_BASE}/groups/placeholder-{employee['department'].lower()}-group-id/members/$ref")
    print(f"           userId={object_id}")


def handle_mover(employee: dict) -> None:
    print(f"  [MOVER] Updating {employee['name']} ({employee['employee_id']})")

    object_id = _get_user_object_id(employee)
    _update_user_profile(object_id, employee)
    _update_manager(object_id, employee)
    _remove_from_old_groups(object_id, employee)
    _add_to_new_group(object_id, employee)

    print(f"  Done — profile updated for {employee['email']}\n")
