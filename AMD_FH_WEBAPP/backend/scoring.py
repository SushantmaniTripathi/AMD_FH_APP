"""
StayHeal — Health Scoring Engine
Computes health_score for each menu item and applies contextual modifiers.

Formula (base):
    health_score = (100 - calories_weight) + protein_bonus - sugar_penalty - repeat_penalty

    calories_weight = calories / 10
    protein_bonus   = protein  * 0.5
    sugar_penalty   = sugar    * 0.8
    repeat_penalty  = 10  if item was in last 5 orders, else 0

Contextual modifiers (applied after base score):
    hour >= 21 or hour <= 5  → heavy_food_score  -= 20  (heavy = calories >= 600)
    junk_order_ratio > 0.6   → healthy_item_score += 15  (healthy = base_score >= 60)
    raining                  → comfort_food_score += 5   (comfort = sugar >= 15)
"""

from __future__ import annotations

from typing import Literal

from models import ContextPayload, MenuItem, ScoredItem


# ─── Thresholds ───────────────────────────────────────────────────────────────

_HEAVY_KCAL:    float = 600.0
_HEALTHY_SCORE: float = 60.0
_COMFORT_SUGAR: float = 15.0

_GREEN_THRESHOLD:  float = 70.0
_YELLOW_THRESHOLD: float = 40.0

_RAIN_KEYWORDS = {"rain", "drizzle", "thunderstorm", "shower"}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _badge(score: float) -> Literal["green", "yellow", "red"]:
    if score >= _GREEN_THRESHOLD:
        return "green"
    if score >= _YELLOW_THRESHOLD:
        return "yellow"
    return "red"


def _is_raining(weather: str | None) -> bool:
    if not weather:
        return False
    return any(kw in weather.lower() for kw in _RAIN_KEYWORDS)


def _base_score(item: MenuItem, last5_ids: set[str]) -> float:
    calories_weight = item.calories / 10.0
    protein_bonus   = item.protein  * 0.5
    sugar_penalty   = item.sugar    * 0.8
    repeat_penalty  = 10.0 if item.id in last5_ids else 0.0

    score = (100.0 - calories_weight) + protein_bonus - sugar_penalty - repeat_penalty
    # Clamp to [0, 100]
    return max(0.0, min(100.0, score))


def _junk_ratio(last5_ids: set[str], item_map: dict[str, MenuItem]) -> float:
    """Ratio of last-5 orders that are 'junky' (base_score < 50 vs a dummy map)."""
    if not last5_ids or not item_map:
        return 0.0
    junk = sum(1 for iid in last5_ids if iid in item_map and _base_score(item_map[iid], set()) < 50)
    return junk / len(last5_ids)


# ─── Public API ───────────────────────────────────────────────────────────────

def score_items(
    items: list[MenuItem],
    context: ContextPayload,
    last5_ids: set[str],
) -> list[ScoredItem]:
    """
    Score and rank all menu items, applying contextual modifiers.

    Parameters
    ----------
    items:      Full menu items sent by the client.
    context:    Current time / weather context.
    last5_ids:  IDs of items ordered in the last 5 orders.

    Returns
    -------
    Ranked list of ScoredItem (highest score first).
    """
    item_map: dict[str, MenuItem] = {it.id: it for it in items}
    rain     = _is_raining(context.weather)
    hour     = context.hour
    j_ratio  = _junk_ratio(last5_ids, item_map)

    scored: list[tuple[float, MenuItem]] = []

    for item in items:
        score = _base_score(item, last5_ids)

        # ── Contextual modifier 1: late-night heavy food penalty ──────────────
        if hour is not None:
            is_late_night = (hour >= 21) or (hour <= 5)
            if is_late_night and item.calories >= _HEAVY_KCAL:
                score -= 20.0

        # ── Contextual modifier 2: junk streak → healthy items bonus ─────────
        if j_ratio > 0.6 and score >= _HEALTHY_SCORE:
            score += 15.0

        # ── Contextual modifier 3: rain → comfort food bonus ─────────────────
        if rain and item.sugar >= _COMFORT_SUGAR:
            score += 5.0

        # Final clamp
        score = max(0.0, min(100.0, score))
        scored.append((score, item))

    # Sort descending
    scored.sort(key=lambda x: x[0], reverse=True)

    result: list[ScoredItem] = []
    for idx, (score, item) in enumerate(scored):
        result.append(
            ScoredItem(
                **item.model_dump(),
                health_score=round(score, 2),
                badge=_badge(score),
                is_top_pick=(idx == 0),
            )
        )

    return result
