"""
StayHeal — FastAPI Application Entry Point

Run locally:
    uvicorn main:app --reload

Cloud Run uses the Dockerfile which calls:
    uvicorn main:app --host 0.0.0.0 --port 8080
"""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import router

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

# ── CORS ──────────────────────────────────────────────────────────────────────
FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
app.include_router(router)


# ── Health-check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Infra"])
async def health() -> dict:
    """Lightweight liveness probe used by Cloud Run."""
    return {"status": "ok", "service": "stayheal-api"}


# ── Startup / shutdown events ─────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup() -> None:
    logger.info("StayHeal API starting up …")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("StayHeal API shutting down.")
