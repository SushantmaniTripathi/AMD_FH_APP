"""
StayHeal — Firestore Client + Helpers
Initializes the Firebase Admin SDK from GOOGLE_APPLICATION_CREDENTIALS
and provides async-friendly wrappers for the three collections:

  users/       → { user_id, name, dietary_prefs, health_goals }
  orders/      → { user_id, items[], timestamp, total_health_score }
  preferences/ → { user_id, disliked_ingredients[], preferred_cuisine }

NOTE: google-cloud-firestore is synchronous; we run it in the default
      thread-pool executor so FastAPI's event loop stays non-blocking.
"""

from __future__ import annotations

import asyncio
import logging
import os
from functools import partial
from typing import Any, Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Firebase initialisation ───────────────────────────────────────────────────

_db: Any = None  # Will hold the firestore.Client once initialized

def _init_firebase() -> Any:
    """Initialize Firebase Admin SDK (idempotent)."""
    import firebase_admin
    from firebase_admin import credentials, firestore

    if not firebase_admin._apps:
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./serviceAccount.json")
        project   = os.getenv("FIRESTORE_PROJECT_ID")

        if not os.path.exists(cred_path):
            raise FileNotFoundError(
                f"Firebase service account not found at '{cred_path}'. "
                "Set GOOGLE_APPLICATION_CREDENTIALS in backend/.env"
            )

        kwargs: dict = {"credential": credentials.Certificate(cred_path)}
        if project:
            kwargs["project"] = project

        firebase_admin.initialize_app(**kwargs)
        logger.info("Firebase Admin SDK initialized (project=%s)", project or "default")

    return firestore.client()


def get_db() -> Any:
    """Return the (cached) Firestore client, initializing on first call."""
    global _db
    if _db is None:
        _db = _init_firebase()
    return _db


# ── Generic async helpers ─────────────────────────────────────────────────────

async def _run_sync(fn, *args, **kwargs):
    """Run a blocking Firestore call in a thread-pool executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(fn, *args, **kwargs))


# ── users/ ────────────────────────────────────────────────────────────────────

async def get_user(user_id: str) -> Optional[dict]:
    """Fetch a user document by user_id field."""
    def _fetch():
        db = get_db()
        docs = db.collection("users").where("user_id", "==", user_id).limit(1).stream()
        for doc in docs:
            return doc.to_dict()
        return None

    return await _run_sync(_fetch)


async def upsert_user(user_id: str, data: dict) -> None:
    """Create or merge-update a user document."""
    def _write():
        db = get_db()
        db.collection("users").document(user_id).set(data, merge=True)

    await _run_sync(_write)


# ── orders/ ───────────────────────────────────────────────────────────────────

async def get_last_n_orders(user_id: str, n: int = 5) -> list[dict]:
    """Return the last ``n`` order documents for a user, newest first."""
    def _fetch():
        db = get_db()
        query = (
            db.collection("orders")
            .where("user_id", "==", user_id)
            .order_by("timestamp", direction="DESCENDING")
            .limit(n)
        )
        return [doc.to_dict() for doc in query.stream()]

    try:
        return await _run_sync(_fetch)
    except Exception as exc:  # noqa: BLE001
        logger.error("get_last_n_orders failed for %s: %s", user_id, exc)
        return []


async def save_order(order_data: dict) -> str:
    """Persist an order document. Returns the new document ID."""
    def _write():
        db = get_db()
        _, ref = db.collection("orders").add(order_data)
        return ref.id

    return await _run_sync(_write)


# ── preferences/ ─────────────────────────────────────────────────────────────

async def get_preferences(user_id: str) -> Optional[dict]:
    """Fetch the preferences document for a user."""
    def _fetch():
        db = get_db()
        doc = db.collection("preferences").document(user_id).get()
        return doc.to_dict() if doc.exists else None

    return await _run_sync(_fetch)


async def upsert_preferences(user_id: str, data: dict) -> None:
    """Create or merge-update a preferences document."""
    def _write():
        db = get_db()
        db.collection("preferences").document(user_id).set(data, merge=True)

    await _run_sync(_write)
