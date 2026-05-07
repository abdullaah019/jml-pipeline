import json
import os

import google.auth
from google.oauth2 import service_account
from googleapiclient.discovery import build

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@yaseenconsulting.com")
DOMAIN = "yaseenconsulting.com"

SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.user",
    "https://www.googleapis.com/auth/admin.directory.group",
]


def get_directory_service():
    """Return an Admin Directory API client using domain-wide delegation.

    Prefers a service account key file (GOOGLE_APPLICATION_CREDENTIALS pointing
    to a JSON key) which supports DWD via with_subject. Falls back to ADC for
    WIF/GCE environments where the SA itself has DWD enabled.
    """
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")

    if creds_path and os.path.exists(creds_path):
        with open(creds_path) as f:
            info = json.load(f)
        if info.get("type") == "service_account":
            creds = service_account.Credentials.from_service_account_info(
                info, scopes=SCOPES, subject=ADMIN_EMAIL
            )
            return build("admin", "directory_v1", credentials=creds, cache_discovery=False)

    creds, _ = google.auth.default(scopes=SCOPES)
    if hasattr(creds, "with_subject"):
        creds = creds.with_subject(ADMIN_EMAIL)
    return build("admin", "directory_v1", credentials=creds, cache_discovery=False)
