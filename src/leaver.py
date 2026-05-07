GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"
TEAMS_WEBHOOK_URL = "https://placeholder.webhook.office.com/webhookb2/placeholder"


def _get_user_object_id(employee: dict) -> str:
    """GET /users/{email} — resolve email to Entra object ID."""
    print(f"    [API] GET {GRAPH_API_BASE}/users/{employee['email']}")
    return "placeholder-object-id"


def _disable_account(object_id: str, employee: dict) -> None:
    """PATCH /users/{id} — block sign-in immediately."""
    print(f"    [API] PATCH {GRAPH_API_BASE}/users/{object_id}")
    print(f"           accountEnabled=false")


def _revoke_sessions(object_id: str, employee: dict) -> None:
    """POST /users/{id}/revokeSignInSessions — invalidate all active tokens."""
    print(f"    [API] POST {GRAPH_API_BASE}/users/{object_id}/revokeSignInSessions")


def _remove_all_groups(object_id: str, employee: dict) -> None:
    """Remove user from all Entra group memberships."""
    print(f"    [API] GET {GRAPH_API_BASE}/users/{object_id}/memberOf (fetch all groups)")
    print(f"    [API] DELETE {GRAPH_API_BASE}/groups/*/members/{object_id}/$ref (for each group)")


def _remove_licenses(object_id: str, employee: dict) -> None:
    """POST /users/{id}/assignLicense — remove all assigned licenses."""
    print(f"    [API] POST {GRAPH_API_BASE}/users/{object_id}/assignLicense")
    print(f"           addLicenses=[], removeLicenses=[placeholder-sku-ids]")


def _hide_from_gal(object_id: str, employee: dict) -> None:
    """PATCH /users/{id} — hide the account from the Global Address List."""
    print(f"    [API] PATCH {GRAPH_API_BASE}/users/{object_id}")
    print(f"           showInAddressList=false")


def _notify_manager_via_teams(employee: dict) -> None:
    """POST to Teams incoming webhook — alert the manager about the offboarding."""
    if not employee.get("manager_email"):
        print(f"    [TEAMS] No manager on record — skipping notification")
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
                            "text": "The account has been disabled and all sessions revoked. Please ensure asset retrieval and access handover are completed.",
                            "wrap": True,
                        },
                    ],
                },
            }
        ],
    }

    print(f"    [TEAMS] POST {TEAMS_WEBHOOK_URL}")
    print(f"            Notifying manager: {employee['manager_email']}")
    print(f"            Payload: Adaptive Card for {employee['name']}")


def handle_leaver(employee: dict) -> None:
    print(f"  [LEAVER] Offboarding {employee['name']} ({employee['employee_id']})")

    object_id = _get_user_object_id(employee)
    _disable_account(object_id, employee)
    _revoke_sessions(object_id, employee)
    _remove_all_groups(object_id, employee)
    _remove_licenses(object_id, employee)
    _hide_from_gal(object_id, employee)
    _notify_manager_via_teams(employee)

    print(f"  Done — {employee['email']} fully offboarded\n")
