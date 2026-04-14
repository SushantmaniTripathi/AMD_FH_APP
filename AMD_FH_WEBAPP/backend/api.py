"""
StayHeal — Route Definitions
All business-logic endpoints live here and are registered
onto the FastAPI `router`, which is then included in main.py.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException

from context import build_context
from models import (
    NudgeRequest,
    NudgeResponse,
    RecommendRequest,
    RecommendResponse,
    ScoredItem,
    SummaryRequest,
    SummaryResponse,
)
from scoring import score_items

router = APIRouter()
logger = logging.getLogger(__name__)


# ─── POST /recommend ──────────────────────────────────────────────────────────

@router.post("/recommend", response_model=RecommendResponse, tags=["AI"])
async def recommend(payload: RecommendRequest) -> RecommendResponse:
    """
    Rank menu items by health score and apply contextual modifiers.

    The client may supply a partial ``context`` (e.g. just the hour).
    Missing fields are auto-fetched from the server (weather API + Firestore).
    """
    if not payload.menu_items:
        raise HTTPException(status_code=400, detail="menu_items cannot be empty")

    # 1. Build context — server fills what the client didn't provide
    server_ctx: dict[str, Any] = await build_context(payload.user_id)

    hour    = payload.context.hour    if payload.context.hour    is not None else server_ctx["hour"]
    weather = payload.context.weather if payload.context.weather is not None else server_ctx["weather"]
    last5   = server_ctx["last5_ids"]

    # Merge client context with server defaults
    from models import ContextPayload
    ctx = ContextPayload(hour=hour, weather=weather, goal=payload.context.goal)

    # 2. Score + rank
    ranked: list[ScoredItem] = score_items(
        items=payload.menu_items,
        context=ctx,
        last5_ids=last5,
    )

    logger.info(
        "/recommend user=%s items=%d top='%s' score=%.1f",
        payload.user_id,
        len(ranked),
        ranked[0].name if ranked else "-",
        ranked[0].health_score if ranked else 0,
    )

    return RecommendResponse(ranked_items=ranked)


# ─── POST /nudge ──────────────────────────────────────────────────────────────

@router.post("/nudge", response_model=NudgeResponse, tags=["AI"])
async def nudge(payload: NudgeRequest) -> NudgeResponse:
    """
    Analyse the last N orders and return a personalised nudge message.

    Logic (rule-based, no external LLM required):
    - Count how many of the orders are "junk" (avg health_score < 50
      or we fall back to a sugar/calorie heuristic).
    - Build a message based on the repeat pattern.
    """
    if not payload.user_history:
        return NudgeResponse(message="Start your health journey — place your first order!")

    # Collect item level signals
    total_items = 0
    junk_items  = 0
    all_names: list[str] = []
    repeat_map: dict[str, int] = {}

    for order in payload.user_history:
        for item in order.items:
            total_items += 1
            name = item.name
            all_names.append(name)
            repeat_map[name] = repeat_map.get(name, 0) + 1

            cal   = item.calories or 0
            sugar = item.sugar    or 0
            if cal > 700 or sugar > 25:
                junk_items += 1

    junk_ratio = junk_items / total_items if total_items else 0
    most_repeated = max(repeat_map, key=lambda k: repeat_map[k]) if repeat_map else None
    repeat_count  = repeat_map.get(most_repeated, 0) if most_repeated else 0

    # Build message
    if junk_ratio > 0.6:
        msg = (
            f"You've had quite a few indulgent meals lately — "
            f"{round(junk_ratio * 100)}% of your recent orders were high-calorie or sugary. "
            "How about a protein-rich bowl tonight to reset?"
        )
    elif most_repeated and repeat_count >= 3:
        msg = (
            f"You've ordered '{most_repeated}' {repeat_count}× in your last 5 orders. "
            "Variety is the spice of life — and nutrition! Want to explore something new?"
        )
    elif junk_ratio > 0.3:
        msg = (
            "You're doing okay, but there's room to boost your weekly health score. "
            "Try swapping one meal for a high-protein, low-sugar option."
        )
    else:
        msg = (
            "Great streak! Your recent orders show solid nutritional choices. "
            "Keep it up and you'll hit your weekly health goal."
        )

    return NudgeResponse(message=msg)


# ─── POST /summary ────────────────────────────────────────────────────────────

@router.post("/summary", response_model=SummaryResponse, tags=["AI"])
async def summary(payload: SummaryRequest) -> SummaryResponse:
    """
    Generate week-level textual insights from 7 days of order data.
    """
    if not payload.weekly_data:
        return SummaryResponse(insights=["No data available for the selected period."])

    # Aggregate signals
    total_cal:   float = 0.0
    total_prot:  float = 0.0
    total_sugar: float = 0.0
    total_items: int   = 0
    day_tallies: list[int] = []
    all_names: list[str] = []

    for day in payload.weekly_data:
        day_count = len(day.items_ordered)
        day_tallies.append(day_count)
        for item in day.items_ordered:
            total_items += 1
            all_names.append(item.name)
            total_cal   += item.calories or 0
            total_prot  += item.protein  or 0
            total_sugar += item.sugar    or 0

    avg_cal   = total_cal   / total_items if total_items else 0
    avg_prot  = total_prot  / total_items if total_items else 0
    avg_sugar = total_sugar / total_items if total_items else 0

    insights: list[str] = []

    # Insight 1 — Calorie snapshot
    if avg_cal > 700:
        insights.append(
            f"Your average meal carried {avg_cal:.0f} kcal this week — above the recommended single-meal ceiling. "
            "Consider portion control or lower-density options."
        )
    elif avg_cal < 350:
        insights.append(
            f"Your meals averaged only {avg_cal:.0f} kcal — make sure you're eating enough to fuel your day!"
        )
    else:
        insights.append(
            f"Solid week: average meal calorie count was {avg_cal:.0f} kcal — right in the healthy range."
        )

    # Insight 2 — Protein feedback
    if avg_prot >= 25:
        insights.append(
            f"Excellent protein discipline — {avg_prot:.1f}g per meal on average is great for muscle maintenance and satiety."
        )
    elif avg_prot < 15:
        insights.append(
            f"Your protein intake averaged only {avg_prot:.1f}g per meal. "
            "Adding a protein source (egg, paneer, legumes) to each meal will help meet your goals."
        )

    # Insight 3 — Sugar warning
    if avg_sugar > 20:
        insights.append(
            f"Watch out — your average sugar intake was {avg_sugar:.1f}g per meal this week. "
            "Try to bring it under 10g by swapping sweetened drinks and dessert items."
        )

    # Insight 4 — Consistency
    active_days = sum(1 for d in day_tallies if d > 0)
    if active_days < 4:
        insights.append(
            f"You only tracked meals on {active_days}/7 days. "
            "Consistent tracking is the #1 driver of healthy eating outcomes."
        )
    else:
        insights.append(
            f"You stayed consistent — meals tracked on {active_days} out of 7 days. Fantastic discipline!"
        )

    # Insight 5 — Variety
    unique_ratio = len(set(all_names)) / total_items if total_items else 0
    if unique_ratio < 0.4:
        insights.append(
            "Your meals this week lacked variety. Rotating proteins, grains, and vegetables improves "
            "micronutrient coverage significantly."
        )

    return SummaryResponse(insights=insights)
