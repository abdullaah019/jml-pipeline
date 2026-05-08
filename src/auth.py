import json
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build

DOMAIN = "yaseenconsulting.com"

SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.user",
    "https://www.googleapis.com/auth/admin.directory.group",
]


def get_directory_service():
    key_json = os.environ.get("GCP_SA_KEY")
    if not key_json:
        return None
    creds = service_account.Credentials.from_service_account_info(
        json.loads(key_json), scopes=SCOPES
    )
    return build("admin", "directory_v1", credentials=creds, cache_discovery=False)
