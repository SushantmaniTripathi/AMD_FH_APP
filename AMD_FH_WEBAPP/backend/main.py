"""
StayHeal — FastAPI Application Entry Point (Consolidated)

Run locally:
    uvicorn main:app --reload

Cloud Run uses the Dockerfile which calls:
    uvicorn main:app --host 0.0.0.0 --port 8080
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Annotated, Any, Literal, Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── App creation ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="StayHeal API",
    description=(
        "Intelligent health recommendation engine for the StayHeal "
        "food-ordering interface. Provides personalised menu ranking, "
        "behavioural nudges, and weekly nutritional insights."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# MODELS
# ==============================================================================

class MenuItem(BaseModel):
    id: str
    name: str
    calories: float = Field(..., ge=0, description="Total calories")
    protein: float  = Field(..., ge=0, description="Protein in grams")
    sugar:   float  = Field(..., ge=0, description="Sugar in grams")
    image_url: Optional[str]  = None
    price:     Optional[float] = None
    restaurant: Optional[str] = None
    tags: list[str] = Field(default_factory=list)

class ScoredItem(MenuItem):
    health_score: float
    badge: Literal["green", "yellow", "red"]
    is_top_pick: bool = False

class OrderedItem(BaseModel):
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

class ContextPayload(BaseModel):
    hour: Optional[int]   = Field(None, ge=0, le=23)
    weather: Optional[str] = None
    goal: Optional[str]   = None

class RecommendRequest(BaseModel):
    user_id: str
    menu_items: list[MenuItem]
    context: ContextPayload = Field(default_factory=ContextPayload)

class RecommendResponse(BaseModel):
    ranked_items: list[ScoredItem]

class NudgeRequest(BaseModel):
    user_history: Annotated[list[Order], Field(max_length=5)]

class NudgeResponse(BaseModel):
    message: str

class DayData(BaseModel):
    date: str
    items_ordered: list[OrderedItem]

class SummaryRequest(BaseModel):
    weekly_data: Annotated[list[DayData], Field(max_length=7)]
    user_id: Optional[str] = None

class SummaryResponse(BaseModel):
    insights: list[str]


# ==============================================================================
# DB MOCK
# ==============================================================================

_users: dict[str, dict] = {}
_orders: list[dict] = []
_preferences: dict[str, dict] = {}

async def get_user(user_id: str) -> Optional[dict]:
    return _users.get(user_id)

async def upsert_user(user_id: str, data: dict) -> None:
    if user_id not in _users:
        _users[user_id] = {}
    _users[user_id].update(data)
    _users[user_id]["user_id"] = user_id

async def get_last_n_orders(user_id: str, n: int = 5) -> list[dict]:
    try:
        user_orders = [o for o in _orders if o.get("user_id") == user_id]
        user_orders.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return user_orders[:n]
    except Exception as exc:
        logger.error("get_last_n_orders failed for %s: %s", user_id, exc)
        return []

async def save_order(order_data: dict) -> str:
    order_id = f"order_{len(_orders) + 1}"
    _orders.append(order_data)
    return order_id

async def get_preferences(user_id: str) -> Optional[dict]:
    return _preferences.get(user_id)

async def upsert_preferences(user_id: str, data: dict) -> None:
    if user_id not in _preferences:
        _preferences[user_id] = {}
    _preferences[user_id].update(data)


# ==============================================================================
# CONTEXT ENGINE
# ==============================================================================

WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
WEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5/weather"
DEFAULT_CITY: str = os.getenv("DEFAULT_CITY", "Bengaluru")

async def get_current_hour() -> int:
    return datetime.now().hour

async def get_weather_condition(city: str = DEFAULT_CITY) -> Optional[str]:
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
            main_condition: str = data["weather"][0]["main"]
            logger.info("Weather for %s: %s", city, main_condition)
            return main_condition
    except httpx.HTTPStatusError as exc:
        logger.error("Weather API HTTP error: %s", exc)
    except Exception as exc:
        logger.error("Weather fetch failed: %s", exc)

    return None

async def get_last5_order_ids(user_id: str) -> set[str]:
    try:
        orders = await get_last_n_orders(user_id, n=5)
        ids: set[str] = set()
        for order in orders:
            for item in order.get("items", []):
                if "id" in item:
                    ids.add(item["id"])
        return ids
    except Exception as exc:
        logger.error("Failed to fetch order history for %s: %s", user_id, exc)
        return set()

async def build_context(user_id: str, city: str = DEFAULT_CITY) -> dict:
    hour    = await get_current_hour()
    weather = await get_weather_condition(city)
    last5   = await get_last5_order_ids(user_id)
    return {
        "hour":    hour,
        "weather": weather,
        "last5_ids": last5,
    }


# ==============================================================================
# SCORING ENGINE
# ==============================================================================

_HEAVY_KCAL:    float = 600.0
_HEALTHY_SCORE: float = 60.0
_COMFORT_SUGAR: float = 15.0

_GREEN_THRESHOLD:  float = 70.0
_YELLOW_THRESHOLD: float = 40.0

_RAIN_KEYWORDS = {"rain", "drizzle", "thunderstorm", "shower"}

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
    return max(0.0, min(100.0, score))

def _junk_ratio(last5_ids: set[str], item_map: dict[str, MenuItem]) -> float:
    if not last5_ids or not item_map:
        return 0.0
    junk = sum(1 for iid in last5_ids if iid in item_map and _base_score(item_map[iid], set()) < 50)
    return junk / len(last5_ids)

def score_items(
    items: list[MenuItem],
    context: ContextPayload,
    last5_ids: set[str],
) -> list[ScoredItem]:
    item_map: dict[str, MenuItem] = {it.id: it for it in items}
    rain     = _is_raining(context.weather)
    hour     = context.hour
    j_ratio  = _junk_ratio(last5_ids, item_map)

    scored: list[tuple[float, MenuItem]] = []

    for item in items:
        score = _base_score(item, last5_ids)

        if hour is not None:
            is_late_night = (hour >= 21) or (hour <= 5)
            if is_late_night and item.calories >= _HEAVY_KCAL:
                score -= 20.0

        if j_ratio > 0.6 and score >= _HEALTHY_SCORE:
            score += 15.0

        if rain and item.sugar >= _COMFORT_SUGAR:
            score += 5.0

        score = max(0.0, min(100.0, score))
        scored.append((score, item))

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


# ==============================================================================
# API ROUTES
# ==============================================================================

@app.post("/recommend", response_model=RecommendResponse, tags=["AI"])
async def recommend(payload: RecommendRequest) -> RecommendResponse:
    if not payload.menu_items:
        raise HTTPException(status_code=400, detail="menu_items cannot be empty")

    server_ctx: dict[str, Any] = await build_context(payload.user_id)

    hour    = payload.context.hour    if payload.context.hour    is not None else server_ctx["hour"]
    weather = payload.context.weather if payload.context.weather is not None else server_ctx["weather"]
    last5   = server_ctx["last5_ids"]

    ctx = ContextPayload(hour=hour, weather=weather, goal=payload.context.goal)

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

@app.post("/nudge", response_model=NudgeResponse, tags=["AI"])
async def nudge(payload: NudgeRequest) -> NudgeResponse:
    if not payload.user_history:
        return NudgeResponse(message="Start your health journey — place your first order!")

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

@app.post("/summary", response_model=SummaryResponse, tags=["AI"])
async def summary(payload: SummaryRequest) -> SummaryResponse:
    if not payload.weekly_data:
        return SummaryResponse(insights=["No data available for the selected period."])

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
    active_days = sum(1 for d in day_tallies if d > 0)

    insights: list[str] = []

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if gemini_api_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_api_key)
            prompt = f"""
            You are an advanced health and nutrition AI assistant for a premium food ordering app called StayHeal.
            Based on the user's weekly food ordering data, generate 3 short, personalized, and encouraging nutritional insights.
            
            Data Summary:
            - Average Calories per meal: {avg_cal:.0f} kcal
            - Average Protein per meal: {avg_prot:.1f} g
            - Average Sugar per meal: {avg_sugar:.1f} g
            - Days tracked: {active_days}/7
            - Total items ordered: {total_items}
            
            Format your response as exactly 3 bullet points (starting with "-"), without any introductory or concluding text. Be concise, actionable, and friendly.
            """
            
            response = client.models.generate_content(
                model='gemini-2.5-pro',
                contents=prompt,
            )
            
            if response.text:
                ai_insights = [line.strip().lstrip('-').lstrip('*').strip() for line in response.text.split('\n') if line.strip() and (line.strip().startswith('-') or line.strip().startswith('*'))]
                if not ai_insights:
                   ai_insights = [line.strip() for line in response.text.split('\n') if line.strip()]
                return SummaryResponse(insights=ai_insights[:3])
        except Exception as exc:
            logger.error("Gemini API generation failed: %s", exc)

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

    if avg_prot >= 25:
        insights.append(
            f"Excellent protein discipline — {avg_prot:.1f}g per meal on average is great for muscle maintenance and satiety."
        )
    elif avg_prot < 15:
        insights.append(
            f"Your protein intake averaged only {avg_prot:.1f}g per meal. "
            "Adding a protein source (egg, paneer, legumes) to each meal will help meet your goals."
        )

    if avg_sugar > 20:
        insights.append(
            f"Watch out — your average sugar intake was {avg_sugar:.1f}g per meal this week. "
            "Try to bring it under 10g by swapping sweetened drinks and dessert items."
        )

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

    unique_ratio = len(set(all_names)) / total_items if total_items else 0
    if unique_ratio < 0.4:
        insights.append(
            "Your meals this week lacked variety. Rotating proteins, grains, and vegetables improves "
            "micronutrient coverage significantly."
        )

    return SummaryResponse(insights=insights)


# ==============================================================================
# LIFECYCLE & HEALTH
# ==============================================================================

@app.get("/health", tags=["Infra"])
async def health() -> dict:
    return {"status": "ok", "service": "stayheal-api"}

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

@app.on_event("startup")
async def on_startup() -> None:
    logger.info("StayHeal API starting up …")

@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("StayHeal API shutting down.")
