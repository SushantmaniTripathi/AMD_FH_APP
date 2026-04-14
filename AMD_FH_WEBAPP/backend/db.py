"""
StayHeal — In-Memory Database (Mock)
Replaces Firestore with an in-memory data store for local development and testing without Firebase.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# --- In-Memory Stores ---
_users: dict[str, dict] = {}
_orders: list[dict] = []
_preferences: dict[str, dict] = {}

# ── users/ ────────────────────────────────────────────────────────────────────

async def get_user(user_id: str) -> Optional[dict]:
    """Fetch a user document by user_id field."""
    return _users.get(user_id)

async def upsert_user(user_id: str, data: dict) -> None:
    """Create or merge-update a user document."""
    if user_id not in _users:
        _users[user_id] = {}
    _users[user_id].update(data)
    # Ensure user_id is in the data
    _users[user_id]["user_id"] = user_id

# ── orders/ ───────────────────────────────────────────────────────────────────

async def get_last_n_orders(user_id: str, n: int = 5) -> list[dict]:
    """Return the last ``n`` order documents for a user, newest first."""
    try:
        user_orders = [o for o in _orders if o.get("user_id") == user_id]
        # Sort by timestamp descending
        user_orders.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return user_orders[:n]
    except Exception as exc:
        logger.error("get_last_n_orders failed for %s: %s", user_id, exc)
        return []

async def save_order(order_data: dict) -> str:
    """Persist an order document. Returns the new document ID."""
    order_id = f"order_{len(_orders) + 1}"
    _orders.append(order_data)
    return order_id

# ── preferences/ ─────────────────────────────────────────────────────────────

async def get_preferences(user_id: str) -> Optional[dict]:
    """Fetch the preferences document for a user."""
    return _preferences.get(user_id)

async def upsert_preferences(user_id: str, data: dict) -> None:
    """Create or merge-update a preferences document."""
    if user_id not in _preferences:
        _preferences[user_id] = {}
    _preferences[user_id].update(data)
