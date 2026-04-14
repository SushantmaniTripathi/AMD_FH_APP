"""
StayHeal — Context Engine
Provides the three pillars of contextual data:
  1. Current local hour
  2. Weather condition (OpenWeatherMap)
  3. Last-5-order IDs from Firestore for a given user
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional

import httpx
from dotenv import load_dotenv

from db import get_last_n_orders

load_dotenv()

logger = logging.getLogger(__name__)

WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
WEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5/weather"

# Default city — can be overridden via env or per-request later
DEFAULT_CITY: str = os.getenv("DEFAULT_CITY", "Bengaluru")


async def get_current_hour() -> int:
    """Return the local server hour (0-23)."""
    return datetime.now().hour


async def get_weather_condition(city: str = DEFAULT_CITY) -> Optional[str]:
    """
    Fetch the current weather condition string from OpenWeatherMap.

    Returns the main condition label (e.g. "Rain", "Clear", "Clouds")
    or None if the API key is absent / request fails.
    """
    if not WEATHER_API_KEY:
        logger.warning("WEATHER_API_KEY not set — skipping weather fetch.")
        return None

    params = {
        "q": city,
        "appid": WEATHER_API_KEY,
        "units": "metric",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(WEATHER_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            # OWM response: {"weather": [{"main": "Rain", "description": "light rain"}, ...]}
            main_condition: str = data["weather"][0]["main"]
            logger.info("Weather for %s: %s", city, main_condition)
            return main_condition
    except httpx.HTTPStatusError as exc:
        logger.error("Weather API HTTP error: %s", exc)
    except Exception as exc:  # noqa: BLE001
        logger.error("Weather fetch failed: %s", exc)

    return None


async def get_last5_order_ids(user_id: str) -> set[str]:
    """
    Return the set of menu-item IDs from the last 5 orders for ``user_id``.
    Falls back to an empty set on any error.
    """
    try:
        orders = await get_last_n_orders(user_id, n=5)
        ids: set[str] = set()
        for order in orders:
            for item in order.get("items", []):
                if "id" in item:
                    ids.add(item["id"])
        return ids
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to fetch order history for %s: %s", user_id, exc)
        return set()


async def build_context(user_id: str, city: str = DEFAULT_CITY) -> dict:
    """
    Aggregate all three context signals and return a single dict.

    Used internally by the /recommend route.
    """
    hour    = await get_current_hour()
    weather = await get_weather_condition(city)
    last5   = await get_last5_order_ids(user_id)

    return {
        "hour":    hour,
        "weather": weather,
        "last5_ids": last5,
    }
