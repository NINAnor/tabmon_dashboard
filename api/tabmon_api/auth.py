"""Signed-cookie session auth for the team area."""

import base64
import hashlib
import hmac
import json
import secrets
import time

from fastapi import Depends, HTTPException, Request, Response

from .config import Settings, get_settings

COOKIE = "tabmon_session"


def _secret(settings: Settings) -> bytes:
    if not settings.session_secret:
        raise HTTPException(503, "SESSION_SECRET is not configured")
    return settings.session_secret.encode()


def _sign(payload: bytes, settings: Settings) -> str:
    return hmac.new(_secret(settings), payload, hashlib.sha256).hexdigest()


def issue(response: Response, username: str, settings: Settings) -> None:
    payload = json.dumps(
        {"u": username, "exp": int(time.time()) + settings.session_hours * 3600}
    ).encode()
    token = base64.urlsafe_b64encode(payload).decode() + "." + _sign(payload, settings)
    response.set_cookie(
        COOKIE,
        token,
        max_age=settings.session_hours * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def clear(response: Response) -> None:
    response.delete_cookie(COOKIE, path="/")


def check_credentials(username: str, password: str, settings: Settings) -> bool:
    if not settings.dashboard_password:
        return False
    ok_user = secrets.compare_digest(username, settings.dashboard_username)
    ok_pass = secrets.compare_digest(password, settings.dashboard_password)
    return ok_user and ok_pass


def current_user(
    request: Request, settings: Settings = Depends(get_settings)
) -> str | None:
    token = request.cookies.get(COOKIE)
    if not token or "." not in token or not settings.session_secret:
        return None
    encoded, signature = token.rsplit(".", 1)
    try:
        payload = base64.urlsafe_b64decode(encoded.encode())
    except ValueError:
        return None
    if not hmac.compare_digest(signature, _sign(payload, settings)):
        return None
    data = json.loads(payload)
    if data.get("exp", 0) < time.time():
        return None
    return data.get("u")


def require_user(user: str | None = Depends(current_user)) -> str:
    if user is None:
        raise HTTPException(401, "Login required")
    return user
