from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt

from app.core.config import get_settings


def load_github_private_key() -> str:
    settings = get_settings()
    key_path = Path(settings.github_private_key_path)

    if not key_path.exists():
        raise FileNotFoundError(
            f"GitHub private key file not found: {settings.github_private_key_path}"
        )

    return key_path.read_text(encoding="utf-8")


def generate_github_app_jwt() -> str:
    settings = get_settings()

    if not settings.github_app_enabled:
        raise ValueError("GitHub App credentials are not configured")

    now = datetime.now(UTC)

    payload = {
        "iat": int((now - timedelta(seconds=60)).timestamp()),
        "exp": int((now + timedelta(minutes=10)).timestamp()),
        "iss": settings.github_app_id,
    }

    private_key = load_github_private_key()

    encoded_jwt = jwt.encode(
        payload,
        private_key,
        algorithm="RS256",
    )

    return encoded_jwt
