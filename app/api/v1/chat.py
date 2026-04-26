"""
Chat API endpoints with LM Studio Gemma 4 E4B integration.

Connects to LM Studio local server for AI-powered stock chat.
"""

import os
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict
import asyncio

from app.services.prediction_service import PredictionService
from app.services.news_service import NewsService
from app.core.dependencies import get_prediction_service, get_news_service


router = APIRouter()

# LM Studio Configuration - Load from environment variables
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://127.0.0.1:1234/v1/chat/completions")
LM_STUDIO_TIMEOUT = float(os.getenv("LM_STUDIO_TIMEOUT", "10.0"))
MAX_TOKENS = int(os.getenv("LM_STUDIO_MAX_TOKENS", "45"))
TEMPERATURE = float(os.getenv("LM_STUDIO_TEMPERATURE", "0.2"))
TOP_P = float(os.getenv("LM_STUDIO_TOP_P", "0.8"))
MODEL_NAME = os.getenv("LM_STUDIO_MODEL", "google/gemma-4-e4b")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


class ChatResponse(BaseModel):
    response: str
    timestamp: str
    source: str = "lm_studio"


def _build_system_prompt(predictions: List[Dict], news: List[Dict]) -> str:
    """Build context-aware system prompt with stock data."""
    
    # Ensure predictions is a list
    if not isinstance(predictions, list):
        predictions = []
    
    # Ensure news is a list
    if not isinstance(news, list):
        news = []
    
    # Get top 5 buy recommendations
    top_picks = [
        p for p in predictions
        if isinstance(p, dict) and
        str(p.get("recommendation", "")).upper() in ("STRONG BUY", "BUY") and
        p.get("confidence", 0) > 0.4
    ]
    top_picks = sorted(top_picks, key=lambda x: x.get("prediction_score", 0), reverse=True)[:5]
    
    # Get recent high-impact news
    high_impact = [
        n for n in news
        if isinstance(n, dict) and n.get("impact_level") in ("high", "macro")
    ][:5]
    
    # Build context
    context = "You are a friendly stock market assistant. You can chat casually AND provide stock analysis.\n\n"
    context += "PERSONALITY:\n"
    context += "- Be conversational and friendly\n"
    context += "- Handle greetings naturally (hi, hello, how are you, etc.)\n"
    context += "- If asked non-stock questions, politely redirect to stocks\n"
    context += "- Keep ALL responses under 40 words\n\n"
    
    context += "STOCK ANALYSIS RULES:\n"
    context += "- Use format: 'Bullish/Bearish/Neutral on [TICKER]'\n"
    context += "- Include key metrics (confidence, sentiment)\n"
    context += "- If no data available, say 'Insufficient data'\n\n"
    
    if top_picks:
        context += "Top Stock Picks:\n"
        for p in top_picks:
            ticker = p.get("ticker", "")
            rec = p.get("recommendation", "")
            conf = round(float(p.get("confidence", 0)) * 100, 0)
            sent = round(float(p.get("avg_sentiment", 0)) * 100, 0)
            context += f"- {ticker}: {rec}, Confidence {conf}%, Sentiment {sent}%\n"
        context += "\n"
    
    if high_impact:
        context += "Recent High-Impact News:\n"
        for n in high_impact[:3]:
            ticker = n.get("ticker", "Market")
            title = n.get("title", "")[:60]
            sent = "Positive" if n.get("sentiment_compound", 0) > 0.05 else "Negative" if n.get("sentiment_compound", 0) < -0.05 else "Neutral"
            context += f"- {ticker}: {title}... ({sent})\n"
    
    return context


async def _call_lm_studio(
    user_message: str,
    system_prompt: str,
    timeout: float = LM_STUDIO_TIMEOUT
) -> str:
    """Call LM Studio API with timeout and error handling."""
    
    # Get API token from environment or use empty string
    api_token = os.getenv("LM_STUDIO_API_TOKEN", "")
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Add authorization header if token is provided
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "max_tokens": MAX_TOKENS,
        "stream": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(LM_STUDIO_URL, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract response from LM Studio format
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                content = message.get("content", "").strip()
                
                # Thinking models (Gemma 4 E4B, Qwen) use reasoning_content
                if not content:
                    reasoning = message.get("reasoning_content", "").strip()
                    if reasoning:
                        # Use the full reasoning as the response
                        # It contains the actual answer
                        content = reasoning
                
                return content if content else "Error: Empty response"
            
            return "Error: Invalid response format"
            
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="LM Studio timeout - response took too long"
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="LM Studio not available - ensure it's running on port 1234"
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=503,
                detail="LM Studio requires API token - set LM_STUDIO_API_TOKEN environment variable or disable authentication in LM Studio settings"
            )
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"LM Studio error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


def _generate_fallback_response(
    message: str,
    predictions: List[Dict],
    news: List[Dict]
) -> str:
    """Fast fallback response when LM Studio is unavailable."""
    
    # Ensure predictions is a list
    if not isinstance(predictions, list):
        predictions = []
    
    # Ensure news is a list
    if not isinstance(news, list):
        news = []
    
    msg_lower = message.lower()
    
    # Casual greetings and conversation
    greetings = ["hi", "hello", "hey", "howdy", "sup", "yo"]
    how_are_you = ["how are you", "how r u", "how are u", "what's up", "whats up", "wassup"]
    thanks = ["thank", "thanks", "thx", "appreciate"]
    
    if any(g == msg_lower.strip() for g in greetings):
        return "Hi! I'm your stock assistant. Ask me about top picks, specific tickers, or market sentiment."
    
    if any(phrase in msg_lower for phrase in how_are_you):
        return "I'm doing great, thanks! Ready to help with stock analysis. What would you like to know?"
    
    if any(t in msg_lower for t in thanks):
        return "You're welcome! Let me know if you need anything else."
    
    if msg_lower in ["bye", "goodbye", "see you", "later"]:
        return "Goodbye! Happy trading!"
    
    # Top picks request
    if any(k in msg_lower for k in ["top", "best", "buy", "recommend", "picks"]):
        top = [
            p for p in predictions
            if isinstance(p, dict) and str(p.get("recommendation", "")).upper() in ("STRONG BUY", "BUY")
        ]
        top = sorted(top, key=lambda x: x.get("prediction_score", 0), reverse=True)[:3]
        
        if not top:
            return "No strong buy signals currently. Market sentiment mixed."
        
        tickers = ", ".join([p.get("ticker", "") for p in top])
        return f"Bullish on: {tickers}. Strong buy signals with positive sentiment."
    
    # Market sentiment
    if any(k in msg_lower for k in ["market", "sentiment", "overall", "today"]):
        bullish = sum(1 for p in predictions if isinstance(p, dict) and "BUY" in str(p.get("recommendation", "")).upper())
        bearish = sum(1 for p in predictions if isinstance(p, dict) and "SELL" in str(p.get("recommendation", "")).upper())
        
        if bullish > bearish * 1.5:
            return f"Market sentiment: Bullish. {bullish} buy signals vs {bearish} sell signals."
        elif bearish > bullish * 1.5:
            return f"Market sentiment: Bearish. {bearish} sell signals vs {bullish} buy signals."
        else:
            return f"Market sentiment: Neutral. Mixed signals across sectors."
    
    # Ticker lookup - only check if message looks like it could be a ticker
    # (short, mostly uppercase, alphanumeric)
    words = message.strip().split()
    if len(words) <= 3:  # Only check short messages
        for word in words:
            ticker = "".join([c for c in word.upper() if c.isalnum()])
            if 2 <= len(ticker) <= 5 and ticker.isupper():
                for p in predictions:
                    if not isinstance(p, dict):
                        continue
                    if str(p.get("ticker", "")).upper() == ticker:
                        rec = p.get("recommendation", "HOLD")
                        conf = round(float(p.get("confidence", 0)) * 100, 0)
                        sent = "Bullish" if p.get("avg_sentiment", 0) > 0.1 else "Bearish" if p.get("avg_sentiment", 0) < -0.1 else "Neutral"
                        return f"{ticker}: {rec}. {sent} sentiment. Confidence {conf}%."
    
    # Default: guide user on what to ask
    return "I specialize in stock analysis. Try asking about top picks, specific tickers (like AAPL or TSLA), or market sentiment!"


@router.get("/health")
async def chat_health():
    """Health check for chat service."""
    return {
        "status": "ok",
        "lm_studio_url": LM_STUDIO_URL,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    prediction_service: PredictionService = Depends(get_prediction_service),
    news_service: NewsService = Depends(get_news_service),
):
    """
    Chat endpoint with LM Studio Qwen 4B integration.
    
    - Loads stock predictions and news context
    - Sends to LM Studio for AI response
    - Falls back to rule-based responses if LM Studio unavailable
    - Enforces 40-word limit and 10-second timeout
    """
    
    message = req.message.strip()
    
    # Load data
    predictions = prediction_service.get_cached_predictions() or prediction_service.load_from_csv()
    news = news_service.get_cached_news() or news_service.load_from_csv()
    
    # Build context-aware system prompt
    system_prompt = _build_system_prompt(predictions, news)
    
    try:
        # Try LM Studio first
        response_text = await _call_lm_studio(message, system_prompt)
        source = "lm_studio"
        print(f"[DEBUG] LM Studio response: {response_text[:100]}...")
        
    except HTTPException as e:
        # Fallback to rule-based response
        print(f"[DEBUG] LM Studio failed: {e.detail}")
        response_text = _generate_fallback_response(message, predictions, news)
        source = "fallback"
    
    return ChatResponse(
        response=response_text,
        timestamp=datetime.now().isoformat(),
        source=source
    )
