from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..agent_core import answer_question
from ..config import settings
from ..llm.formatter import format_distribution
from ..observability import configure_logging, new_correlation_id
from ..services import get_fraktion_distribution

configure_logging()

app = FastAPI(title="DIP Fraktionsverteilung", version="0.1.0")

# allow react app running locally to call APIs without CORS issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "groq_configured": bool(settings.groq_api_key)}


@app.get("/api/distribution/{wahlperiode}")
def distribution(wahlperiode: int) -> dict:
    new_correlation_id()
    if not (1 <= wahlperiode <= 30):
        raise HTTPException(status_code=400, detail="wahlperiode out of range")
    try:
        result = get_fraktion_distribution(wahlperiode)
        summary = format_distribution(result)
    except Exception as exc:
        # Most likely an expired/invalid DIP key -> 401 upstream.
        raise HTTPException(status_code=502, detail=f"DIP request failed: {exc}")
    return {"data": result.as_dict(), "summary": summary}


@app.post("/api/chat")
async def chat(req: ChatRequest) -> dict:
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="empty message")
    return await answer_question(req.message, req.history)


# Serve the built React app (after `npm run build`) if present, so the whole
# thing runs from a single process in a demo.
_FRONTEND_DIST = Path(__file__).resolve().parents[3] / "frontend" / "dist"
if _FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")
