"""
StayHeal — Pydantic v2 Models
Defines all request/response shapes used across the API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field


# ─── Shared primitives ────────────────────────────────────────────────────────

class MenuItem(BaseModel):
    id: str
    name: str
    calories: float = Field(..., ge=0, description="Total calories")
    protein: float  = Field(..., ge=0, description="Protein in grams")
    sugar:   float  = Field(..., ge=0, description="Sugar in grams")
    # Optional extras that the UI may send
    image_url: Optional[str]  = None
    price:     Optional[float] = None
    restaurant: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class ScoredItem(MenuItem):
    health_score: float
    badge: Literal["green", "yellow", "red"]
    is_top_pick: bool = False


class OrderedItem(BaseModel):
    """A lightweight representation of a previously ordered item."""
    id: str
    name: str
    calories: Optional[float] = None
    protein:  Optional[float] = None
    sugar:    Optional[float] = None


class Order(BaseModel):
    user_id: str
    items: list[OrderedItem]
    timestamp: datetime
    total_health_score: Optional[float] = None


# ─── Context payload (sent by frontend) ───────────────────────────────────────

class ContextPayload(BaseModel):
    hour: Optional[int]   = Field(None, ge=0, le=23)
    weather: Optional[str] = None          # e.g. "Rain", "Clear"
    goal: Optional[str]   = None           # e.g. "Workout Fuel"


# ─── /recommend ───────────────────────────────────────────────────────────────

class RecommendRequest(BaseModel):
    user_id: str
    menu_items: list[MenuItem]
    context: ContextPayload = Field(default_factory=ContextPayload)


class RecommendResponse(BaseModel):
    ranked_items: list[ScoredItem]


# ─── /nudge ───────────────────────────────────────────────────────────────────

class NudgeRequest(BaseModel):
    user_history: Annotated[list[Order], Field(max_length=5)]


class NudgeResponse(BaseModel):
    message: str


# ─── /summary ─────────────────────────────────────────────────────────────────

class DayData(BaseModel):
    date: str                        # ISO-8601 date string
    items_ordered: list[OrderedItem]


class SummaryRequest(BaseModel):
    weekly_data: Annotated[list[DayData], Field(max_length=7)]
    user_id: Optional[str] = None


class SummaryResponse(BaseModel):
    insights: list[str]
