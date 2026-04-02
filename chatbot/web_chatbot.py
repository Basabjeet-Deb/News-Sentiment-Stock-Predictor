"""
Web-based Chatbot API
FastAPI endpoint for chatbot integration
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chatbot import StockChatbot

app = FastAPI(title="Stock Chatbot API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize chatbot
bot = StockChatbot()


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str
    timestamp: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint"""
    try:
        answer = bot.answer_question(request.question)
        return ChatResponse(
            answer=answer,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "predictions_loaded": len(bot.predictions),
        "news_loaded": len(bot.news)
    }


if __name__ == "__main__":
    import uvicorn
    from datetime import datetime
    
    print("🤖 Starting Stock Chatbot API on http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
