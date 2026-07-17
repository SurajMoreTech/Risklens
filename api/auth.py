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

If the variable is absent the app still starts, but every protected endpoint
returns HTTP 503 ("Auth not configured") until the variable is set.  This lets
local development without credentials continue working on unprotected endpoints
while making the misconfiguration obvious at the protected ones.
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

if _SERVICE_ACCOUNT_JSON:
    try:
        _cred = credentials.Certificate(json.loads(_SERVICE_ACCOUNT_JSON))
        _firebase_app = firebase_admin.initialize_app(_cred)
        logger.info("Firebase Admin SDK initialised successfully.")
    except Exception as exc:
        _init_error = f"Firebase Admin SDK failed to initialise: {exc}"
        logger.error(_init_error)
else:
    _init_error = (
        "FIREBASE_SERVICE_ACCOUNT_JSON env var not set — "
        "protected endpoints will return HTTP 503."
    )
    logger.warning(_init_error)

# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
_bearer = HTTPBearer(auto_error=True)


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """FastAPI dependency: verify a Firebase ID token.

    Returns the decoded token payload (uid, email, etc.) on success.
    Raises HTTP 503 if the SDK is not configured, HTTP 401 for any invalid token.
    """
    if _firebase_app is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_init_error or "Firebase Auth is not configured on this server.",
        )

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
