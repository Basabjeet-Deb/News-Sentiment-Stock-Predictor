"""
Chat API endpoints (runs on the main FastAPI backend).

This replaces the old separate chatbot service on port 8001.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict

from app.services.prediction_service import PredictionService
from app.services.news_service import NewsService
from app.core.dependencies import get_prediction_service, get_news_service


router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


def _format_top_picks(predictions: List[Dict], n: int = 5) -> str:
    picks = [
        p for p in predictions
        if str(p.get("recommendation", "")).upper() in ("STRONG BUY", "BUY")
    ]
    picks = sorted(picks, key=lambda x: x.get("prediction_score", 0), reverse=True)[:n]
    if not picks:
        return "No BUY candidates available yet. Run the pipeline to generate fresh predictions."
    lines = ["Top picks:"]
    for i, p in enumerate(picks, 1):
        lines.append(
            f"{i}. {p.get('ticker')} — {p.get('recommendation')} "
            f"(score {p.get('prediction_score')}, conf {round(float(p.get('confidence',0))*100,0)}%)"
        )
    return "\n".join(lines)


@router.get("/health")
async def chat_health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@router.post("/")
async def chat(
    req: ChatRequest,
    prediction_service: PredictionService = Depends(get_prediction_service),
    news_service: NewsService = Depends(get_news_service),
):
    msg = req.message.strip()
    msg_l = msg.lower()

    preds = prediction_service.get_cached_predictions() or prediction_service.load_from_csv()
    news = news_service.get_cached_news() or news_service.load_from_csv()

    # Simple intent handling (fast + deterministic)
    if any(k in msg_l for k in ["top", "best", "buy", "recommend", "picks"]):
        response = _format_top_picks(preds, n=5)
        return {"response": response, "timestamp": datetime.now().isoformat()}

    # Ticker lookup
    token = "".join([c for c in msg.upper() if c.isalnum() or c in ".-"])
    ticker = token[:10]
    if 2 <= len(ticker) <= 10:
        for p in preds:
            if str(p.get("ticker", "")).upper() == ticker:
                related = [n for n in news if str(n.get("ticker", "")).upper() == ticker][:3]
                headlines = "\n".join([f"- {n.get('title','')}" for n in related]) if related else "- (no headlines yet)"
                response = (
                    f"{ticker} — {p.get('company_name', ticker)}\n"
                    f"Recommendation: {p.get('recommendation')} (score {p.get('prediction_score')})\n"
                    f"Confidence: {round(float(p.get('confidence',0))*100,0)}%\n"
                    f"News count: {p.get('news_count')}\n\n"
                    f"Recent headlines:\n{headlines}"
                )
                return {"response": response, "timestamp": datetime.now().isoformat()}

    return {
        "response": "Ask me for 'top picks' or a ticker like 'AAPL'.",
        "timestamp": datetime.now().isoformat(),
    }

