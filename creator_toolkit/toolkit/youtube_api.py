"""YouTube Data API v3 – upload Shorts (vertical video, <= 3 min, #Shorts)."""
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from . import config

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def credentials() -> Credentials:
    creds = None
    if config.YT_TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(config.YT_TOKEN_PATH), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(config.YT_CLIENT_SECRET, SCOPES)
        # open_browser=False: prints a URL; open it in any browser (works on Termux too)
        creds = flow.run_local_server(port=8080, open_browser=False)
    config.YT_TOKEN_PATH.write_text(creds.to_json())
    return creds


def upload_short(path: str, title: str, caption: str, tags: list) -> str:
    youtube = build("youtube", "v3", credentials=credentials())
    description = caption if "#shorts" in caption.lower() else f"{caption}\n\n#Shorts"
    body = {
        "snippet": {"title": title[:100], "description": description,
                    "tags": tags[:15], "categoryId": "22"},
        "status": {"privacyStatus": config.YT_PRIVACY, "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(path, chunksize=8 * 1024 * 1024, resumable=True, mimetype="video/*")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _, response = request.next_chunk()
    return response["id"]
