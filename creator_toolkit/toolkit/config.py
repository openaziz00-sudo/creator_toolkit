"""All configuration comes from environment variables / a .env file."""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE = Path(os.getenv("TOOLKIT_HOME", str(Path.home() / ".creator_toolkit")))
BASE.mkdir(parents=True, exist_ok=True)

DB_PATH = BASE / "toolkit.db"
TOKENS_PATH = BASE / "tokens.json"
YT_TOKEN_PATH = BASE / "youtube_token.json"

TZ = os.getenv("TOOLKIT_TZ", "Asia/Muscat")

TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
TIKTOK_REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI", "")
TIKTOK_MODE = os.getenv("TIKTOK_MODE", "direct")  # direct | inbox
TIKTOK_PRIVACY = os.getenv("TIKTOK_PRIVACY", "SELF_ONLY")

YT_CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET", "client_secret.json")
YT_PRIVACY = os.getenv("YT_PRIVACY", "private")

IG_USER_ID = os.getenv("IG_USER_ID", "")
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")
IG_API_VERSION = os.getenv("IG_API_VERSION", "v23.0")


def load_tokens() -> dict:
    if TOKENS_PATH.exists():
        return json.loads(TOKENS_PATH.read_text())
    return {}


def save_tokens(tokens: dict) -> None:
    TOKENS_PATH.write_text(json.dumps(tokens))
    try:
        TOKENS_PATH.chmod(0o600)
    except OSError:
        pass
