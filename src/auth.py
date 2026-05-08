import google.auth
from googleapiclient.discovery import build

DOMAIN = "yaseenconsulting.com"

SCOPES = [
    "https://www.googleapis.com/auth/admin.directory.user",
    "https://www.googleapis.com/auth/admin.directory.group",
]


def get_directory_service():
    creds, _ = google.auth.default(scopes=SCOPES)
    return build("admin", "directory_v1", credentials=creds, cache_discovery=False)
