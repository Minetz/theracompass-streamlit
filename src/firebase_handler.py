"""Firebase utilities for authentication and user data storage.

This module provides minimal wrappers around Firebase services to support
future replacement of local storage with Firebase. Each user retains a single
JSON document stored in Cloud Firestore.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from time import time
from typing import Any

import requests
from dotenv import load_dotenv
from firebase_admin import auth, credentials
import logging

load_dotenv()
# Simple logger for debugging Firebase flows
logger = logging.getLogger("firebase")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "")

# Toggle between local filesystem and Firebase based on SAVE_MODE
SAVE_MODE = os.getenv("SAVE_MODE", "local").lower()

# Simple in-memory cache for verified tokens to avoid repeated calls to
# Firebase when the same token is reused. Cache entries expire either when
# the token's own expiry passes or after ``TOKEN_CACHE_TTL`` seconds.
TOKEN_CACHE_TTL = int(os.getenv("TOKEN_CACHE_TTL", "300"))
_TOKEN_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}

# Basic diagnostics (non-secret)
logger.debug(
    "firebase_handler loaded: SAVE_MODE=%s, FIREBASE_API_KEY_set=%s, TOKEN_CACHE_TTL=%s",
    SAVE_MODE,
    bool(FIREBASE_API_KEY),
    TOKEN_CACHE_TTL,
)


def init_firebase(
    credential_path: str | Path | None = None,
) -> None:
    """Initialise the Firebase app.

    Parameters
    ----------
    credential_path:
        Path to the service account credentials JSON file. If not provided,
        ``FIREBASE_CREDENTIALS`` environment variable is used.
    """
    import firebase_admin

    try:  # Avoid reinitialising if already set up
        firebase_admin.get_app()
        return
    except ValueError:
        pass

    cred_path = credential_path or os.getenv("FIREBASE_CREDENTIALS")
    project_id = os.getenv("FIREBASE_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT") or ""
    logger.debug(
        "init_firebase: project_id=%s, creds_path_set=%s",
        project_id or "(none)",
        bool(cred_path),
    )
    if cred_path:
        try:
            exists = Path(str(cred_path)).exists()
            logger.debug("init_firebase: credential_path=%s exists=%s", cred_path, exists)
        except Exception as e:
            logger.warning("init_firebase: could not stat credential_path=%s: %s", cred_path, e)

    try:
        cred: credentials.Base
        if cred_path:
            cred = credentials.Certificate(str(cred_path))
            firebase_admin.initialize_app(cred, {"projectId": project_id} if project_id else None)
        else:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {"projectId": project_id} if project_id else None)
        logger.debug("init_firebase: initialized app using %s", "service account" if cred_path else "ADC")
    except Exception as e:
        logger.exception("init_firebase failed: %s", e)
        print(f"init_firebase failed: {type(e).__name__}: {e}")
        raise


def create_user(email: str, password: str) -> str:
    """Register a new user in Firebase Authentication and initialise their data.

    Parameters
    ----------
    email:
        User's e-mail address.
    password:
        User's password.

    Returns
    -------
    str
        The created user's UID.
    """
    try:
        user = auth.create_user(email=email, password=password)
        save_user_json(
            user.uid,
            {
                "username": email,
                "email": email,
                "user_id": user.uid,
                "user_subscription": "free",
                "patient_dir": {},
            },
        )
        return user.uid
    except Exception as e:
        logger.exception("create_user failed for %s: %s", email, e)
        print(f"create_user failed for {email}: {type(e).__name__}: {e}")
        raise


def verify_id_token(id_token: str) -> dict[str, Any]:
    """Verify a Firebase ID token and return the decoded claims.

    To reduce the number of validation calls against Firebase, successful
    verifications are cached in memory for a short period. The cache honours
    the token's own ``exp`` claim and falls back to ``TOKEN_CACHE_TTL`` seconds
    if the claim is missing.
    """
    now = time()
    cached = _TOKEN_CACHE.get(id_token)
    if cached and cached[0] > now:
        return cached[1]

    import firebase_admin as _fb

    try:
        _fb.get_app()
    except ValueError:
        init_firebase()  # ensure default app exists
    try:
        decoded = auth.verify_id_token(id_token)
    except Exception as e:
        logger.exception("verify_id_token failed: %s", e)
        print(f"verify_id_token failed: {type(e).__name__}: {e}")
        raise
    

    exp = decoded.get("exp")
    ttl = exp - now if exp else TOKEN_CACHE_TTL
    # Ensure a positive TTL in case of clock skew or past expiry
    expires_at = now + max(ttl, 0)
    _TOKEN_CACHE[id_token] = (expires_at, decoded)
    return decoded


def sign_in_with_email_and_password(email: str, password: str) -> dict[str, Any]:
    """Authenticate a user using Firebase email/password flow.

    Parameters
    ----------
    email:
        User's e-mail address.
    password:
        User's password.

    Returns
    -------
    dict[str, Any]
        The Firebase response containing ID and refresh tokens.
    """
    url = (
        "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key="
        f"{FIREBASE_API_KEY}"
    )
    payload = {"email": email, "password": password, "returnSecureToken": True}
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        body = None
        try:
            body = e.response.text if getattr(e, "response", None) is not None else None
        except Exception:
            body = None
        logger.exception(
            "sign_in_with_email_and_password error for %s: %s; status=%s; body=%s",
            email,
            e,
            getattr(getattr(e, "response", None), "status_code", None),
            body,
        )
        print(
            f"sign_in_with_email_and_password failed for {email}: {type(e).__name__}: {e}; "
            f"status={getattr(getattr(e, 'response', None), 'status_code', None)}"
        )
        raise


def send_password_reset_email(email: str) -> None:
    """Send a password reset e-mail via Firebase Authentication.

    Parameters
    ----------
    email:
        The user's e-mail address.
    """
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_API_KEY}"
    payload = {"requestType": "PASSWORD_RESET", "email": email}
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        body = None
        try:
            body = e.response.text if getattr(e, "response", None) is not None else None
        except Exception:
            body = None
        logger.exception(
            "send_password_reset_email error for %s: %s; status=%s; body=%s",
            email,
            e,
            getattr(getattr(e, "response", None), "status_code", None),
            body,
        )
        print(
            f"send_password_reset_email failed for {email}: {type(e).__name__}: {e}; "
            f"status={getattr(getattr(e, 'response', None), 'status_code', None)}"
        )
        raise
    

def sign_in_with_google(id_token: str) -> dict[str, Any]:
    """Authenticate a user via Google OAuth token."""
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={FIREBASE_API_KEY}"
    payload = {
        "postBody": f"id_token={id_token}&providerId=google.com",
        "requestUri": "http://localhost",
        "returnSecureToken": True,
        "returnIdpCredential": True,
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.RequestException as e:
        body = None
        try:
            body = e.response.text if getattr(e, "response", None) is not None else None
        except Exception:
            body = None
        logger.exception(
            "sign_in_with_google error: %s; status=%s; body=%s",
            e,
            getattr(getattr(e, "response", None), "status_code", None),
            body,
        )
        print(
            f"sign_in_with_google failed: {type(e).__name__}: {e}; "
            f"status={getattr(getattr(e, 'response', None), 'status_code', None)}"
        )
        raise


def save_json(collection: str, item_id: str, data: dict[str, Any]) -> None:
    """Save a JSON-serialisable object either locally or to Firestore."""
    if SAVE_MODE == "firebase":
        import firebase_admin as _fb
        from firebase_admin import firestore

        try:
            _fb.get_app()
        except ValueError:
            init_firebase()  # ensure default app exists
        try:
            db = firestore.client()
            db.collection(collection).document(item_id).set(data)
        except Exception as e:
            logger.exception(
                "save_json failed: collection=%s id=%s err=%s", collection, item_id, e
            )
            print(
                f"save_json failed for {collection}/{item_id}: {type(e).__name__}: {e}"
            )
            raise
       
    else:
        path = Path("data") / collection
        path.mkdir(parents=True, exist_ok=True)
        with open(path / f"{item_id}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        

def load_json(collection: str, item_id: str) -> dict[str, Any] | None:
    """Retrieve a JSON object from the configured storage."""
    if SAVE_MODE == "firebase":
        import firebase_admin as _fb
        from firebase_admin import firestore

        try:
            _fb.get_app()
        except ValueError:
            init_firebase()  # ensure default app exists
        try:
            db = firestore.client()
            doc = db.collection(collection).document(item_id).get()
            if not doc.exists:
                return None
            return doc.to_dict()
        except Exception as e:
            logger.exception(
                "load_json failed: collection=%s id=%s err=%s", collection, item_id, e
            )
            print(
                f"load_json failed for {collection}/{item_id}: {type(e).__name__}: {e}"
            )
            raise

    path = Path("data") / collection / f"{item_id}.json"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def delete_json(collection: str, item_id: str) -> bool:
    """Delete a JSON object from the configured storage."""
    if SAVE_MODE == "firebase":
        import firebase_admin as _fb
        from firebase_admin import firestore

        try:
            _fb.get_app()
        except ValueError:
            init_firebase()  # ensure default app exists
        try:
            db = firestore.client()
            doc = db.collection(collection).document(item_id)
            if not doc.get().exists:
                return False
            doc.delete()
            return True
        except Exception as e:
            logger.exception(
                "delete_json failed: collection=%s id=%s err=%s", collection, item_id, e
            )
            print(
                f"delete_json failed for {collection}/{item_id}: {type(e).__name__}: {e}"
            )
            raise

    path = Path("data") / collection / f"{item_id}.json"
    if not path.exists():
        return False
    path.unlink()
    return True


def save_user_json(user_id: str, data: dict[str, Any]) -> None:
    """Upload the user's JSON data to Firestore."""
    save_json("users", user_id, data)


def load_user_json(user_id: str) -> dict[str, Any] | None:
    """Download a user's JSON data from Firestore."""
    return load_json("users", user_id)


def delete_user_json(user_id: str) -> bool:
    """Remove a user's JSON data from Firestore."""
    return delete_json("users", user_id)
