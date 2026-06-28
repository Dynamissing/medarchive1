from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


def verify_admin_credentials(username: str, password: str, settings: Settings | None = None) -> bool:
    resolved = settings or get_settings()
    return hmac.compare_digest(username, resolved.admin_username) and hmac.compare_digest(
        password,
        resolved.admin_password,
    )


def create_admin_token(settings: Settings | None = None, now: int | None = None) -> str:
    resolved = settings or get_settings()
    issued_at = int(now if now is not None else time.time())
    payload = {
        "sub": resolved.admin_username,
        "iat": issued_at,
        "exp": issued_at + resolved.admin_token_ttl_seconds,
    }
    payload_b64 = encode_json(payload)
    signature = sign_payload(payload_b64, resolved.admin_token_secret)
    return f"{payload_b64}.{signature}"


def validate_admin_token(token: str, settings: Settings | None = None, now: int | None = None) -> dict[str, Any]:
    resolved = settings or get_settings()
    try:
        payload_b64, signature = token.split(".", 1)
    except ValueError as exc:
        raise unauthorized("Invalid admin token") from exc
    expected = sign_payload(payload_b64, resolved.admin_token_secret)
    if not hmac.compare_digest(signature, expected):
        raise unauthorized("Invalid admin token")
    try:
        payload = json.loads(base64.urlsafe_b64decode(pad_base64(payload_b64)).decode("utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        raise unauthorized("Invalid admin token") from exc
    current_time = int(now if now is not None else time.time())
    if payload.get("sub") != resolved.admin_username:
        raise unauthorized("Invalid admin token subject")
    if int(payload.get("exp", 0)) < current_time:
        raise unauthorized("Admin token expired")
    return payload


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise unauthorized("Missing admin bearer token")
    return validate_admin_token(credentials.credentials)


def encode_json(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def sign_payload(payload_b64: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def pad_base64(value: str) -> bytes:
    return (value + "=" * (-len(value) % 4)).encode("ascii")


def unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )
