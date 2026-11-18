"""
auth.py — Firebase ID-token verification dependency for the RiskLens API.

Usage
-----
Add ``token: dict = Depends(verify_token)`` to any endpoint that requires an
authenticated Firebase user.  The dependency reads the ``Authorization`` header,
strips the ``Bearer `` prefix, and calls ``firebase_admin.auth.verify_id_token``
which validates the token's signature, expiry, and audience against your Firebase
project.

Environment variables
---------------------
FIREBASE_SERVICE_ACCOUNT_JSON
    The full contents of a Firebase service-account JSON key file as a single
    string.  Obtain this from:
        Firebase Console → Project Settings → Service Accounts → Generate new key

    On Render, set this as a secret environment variable (not committed to git).

FIREBASE_SERVICE_ACCOUNT_FILE
    Alternative for local development: a path to the service-account JSON key
    file on disk.  Checked only when FIREBASE_SERVICE_ACCOUNT_JSON is unset.
    Keep the key file outside the repo (it is git-ignored either way).

ALLOW_DEMO_AUTH
    Local development opt-in (default off).  When set to 1/true/yes, requests
    without an Authorization header are accepted as a demo session even if the
    Admin SDK is configured — useful when the web frontend runs in demo mode
    (no NEXT_PUBLIC_FIREBASE_* config) and therefore cannot send a real token.
    Never set this in production.

If the variable is absent the app still starts, but every protected endpoint
treats requests as a local demo session (uid "local-demo-user") instead of
verifying a Firebase ID token.  This lets local development — where the web
frontend runs in demo mode and cannot send a real token — continue end to end.
Production deployments always set the service account, in which case tokens
are verified strictly and missing/invalid credentials return HTTP 401.
"""

from __future__ import annotations

import json
import logging
import os

import firebase_admin
from firebase_admin import auth as fb_auth, credentials
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger("risklens.auth")

# ---------------------------------------------------------------------------
# Firebase Admin SDK — initialise once at module import time
# ---------------------------------------------------------------------------
_firebase_app: firebase_admin.App | None = None
_init_error: str | None = None

_SERVICE_ACCOUNT_JSON = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "")
_SERVICE_ACCOUNT_FILE = os.environ.get("FIREBASE_SERVICE_ACCOUNT_FILE", "")

if not _SERVICE_ACCOUNT_JSON and _SERVICE_ACCOUNT_FILE:
    try:
        with open(_SERVICE_ACCOUNT_FILE, encoding="utf-8") as fh:
            _SERVICE_ACCOUNT_JSON = fh.read()
    except OSError as exc:
        _init_error = f"Could not read FIREBASE_SERVICE_ACCOUNT_FILE: {exc}"
        logger.error(_init_error)

if _SERVICE_ACCOUNT_JSON:
    try:
        _cred = credentials.Certificate(json.loads(_SERVICE_ACCOUNT_JSON))
        _firebase_app = firebase_admin.initialize_app(_cred)
        logger.info("Firebase Admin SDK initialised successfully.")
    except Exception as exc:
        _init_error = f"Firebase Admin SDK failed to initialise: {exc}"
        logger.error(_init_error)
else:
    _init_error = _init_error or (
        "Neither FIREBASE_SERVICE_ACCOUNT_JSON nor FIREBASE_SERVICE_ACCOUNT_FILE "
        "is set — protected endpoints will return HTTP 503."
    )
    logger.warning(_init_error)

# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
# auto_error=False so a missing header reaches verify_token: when the Admin SDK
# is unconfigured (local dev) we issue a demo session instead of an opaque 403.
_bearer = HTTPBearer(auto_error=False)

# Principal handed out while the SDK is unconfigured (local development with
# the web app in demo mode). Endpoints only read token.get("uid") for logging.
_DEMO_PRINCIPAL = {
    "uid": "local-demo-user",
    "email": "local-demo@risklens.local",
    "name": "Local Demo User",
    "firebase": {"sign_in_provider": "local-demo"},
}

# Local-dev opt-in: accept headerless requests as demo sessions even when the
# Admin SDK is configured (frontend demo mode cannot produce a real token).
_ALLOW_DEMO_AUTH = os.environ.get("ALLOW_DEMO_AUTH", "").strip().lower() in (
    "1", "true", "yes",
)


async def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    """FastAPI dependency: verify a Firebase ID token.

    Returns the decoded token payload (uid, email, etc.) on success.
    Headerless requests run as a demo session when the Admin SDK is
    unconfigured, or when ALLOW_DEMO_AUTH is opted in (local dev only).
    A configured SDK without ALLOW_DEMO_AUTH gives strict verification:
    missing credentials → HTTP 401, invalid/expired token → HTTP 401.
    """
    if credentials is None:
        # No Authorization header. Local development (SDK unconfigured, or
        # ALLOW_DEMO_AUTH opted in) runs as a demo session; production keeps
        # strict authentication.
        if _firebase_app is None or _ALLOW_DEMO_AUTH:
            return _DEMO_PRINCIPAL
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Missing Authorization header.",
        )

    if _firebase_app is None:
        # A token was supplied but there is no Admin SDK to verify it against.
        # Keep local development moving; production never reaches this branch.
        return _DEMO_PRINCIPAL

    try:
        decoded = fb_auth.verify_id_token(credentials.credentials, app=_firebase_app)
        logger.debug("Verified token for uid=%s", decoded.get("uid"))
        return decoded
    except fb_auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase ID token has expired. Please sign in again.",
        )
    except fb_auth.InvalidIdTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Firebase ID token: {exc}",
        )
    except Exception as exc:
        logger.exception("Unexpected error during token verification")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token verification failed.",
        ) from exc
