# 🤖 AI Stock Chatbot - Features & Capabilities

## ✅ What It Can Do

### 1. Investment Advice
Ask natural questions and get AI-powered recommendations:
- "Should I buy AAPL?"
- "Is TSLA a good investment?"
- "Worth buying NVDA?"

**Response includes:**
- Current price
- AI recommendation (BUY/HOLD/SELL)
- Confidence level
- News sentiment
- Contextual advice

### 2. Stock Information
Get detailed info about any stock:
- "Tell me about Apple"
- "What's the price of TSLA?"
- "How is Microsoft doing?"
- "Info on Tesla"

**Response includes:**
- Current price and change %
- AI recommendation with confidence
- News sentiment score
- Number of articles analyzed
- Contextual interpretation

### 3. Stock Comparisons
Compare two stocks side-by-side:
- "Compare AAPL vs MSFT"
- "TSLA or NVDA?"
- "Which is better: AMD vs INTC?"

**Response includes:**
- Price comparison
- Recommendation comparison
- Sentiment comparison
- AI's better pick

### 4. Top Recommendations
Get the best AI picks:
- "What are the top buy recommendations?"
- "Show me the best stocks"
- "What should I buy?"
- "Top picks today"

**Response includes:**
- Top 5 stocks ranked by AI score
- Price, confidence, sentiment
- Number of news articles
- Disclaimer about doing own research

### 5. Market Movers
Track gainers and losers:
- "What are the top gainers?"
- "Show me the biggest losers"
- "Which stocks are rising?"
- "What's falling today?"

**Response includes:**
- Top 5 gainers or losers
- Price and change %
- Company names

### 6. Market Sentiment
Understand overall market mood:
- "What's the market sentiment?"
- "Is the market bullish or bearish?"
- "How's the market looking today?"

**Response includes:**
- Overall market mood (Bullish/Bearish/Neutral)
- Positive/Neutral/Negative article counts
- Percentages
- Actionable advice

### 7. News Analysis
Get news for specific stocks:
- "Show news for AAPL"
- "What's the latest on Tesla?"
- "Any news about Microsoft?"

**Response includes:**
- Overall sentiment summary
- Top 5 recent articles
- Source, impact level, sentiment score
- Article count

### 8. Sector Analysis
Analyze performance by sector:
- "Show me sector analysis"
- "Which sectors are performing well?"

**Response includes:**
- Top 5 sectors by stock count
- Average sentiment per sector
- Buy recommendation count

### 9. Statistics
Get system stats:
- "How many stocks are you tracking?"
- "How many news articles?"

**Response includes:**
- Total counts
- Coverage details

## 🎯 Natural Language Understanding

The chatbot understands:
- **Company names**: "Tesla" → TSLA, "Apple" → AAPL
- **Natural questions**: "Should I buy..." "Is it good to..."
- **Comparisons**: "vs", "versus", "or"
- **Casual language**: "What's hot?", "Show me the best"
- **Greetings**: "Hi", "Hello", "Hey"

## 🛡️ Out-of-Context Handling

When asked non-stock questions:
- **Greetings**: Friendly welcome message
- **Help requests**: Shows capabilities
- **Non-stock topics**: Politely redirects to stock topics
- **Unclear questions**: Provides examples

Examples:
- "What is the weather?" → Redirects to stock topics
- "Hello" → Friendly greeting
- "Who are you?" → Explains capabilities
- "Thank you" → Acknowledges and offers more help

## 🎨 User Experience

### Conversational Tone
- Friendly and approachable
- Uses emojis for visual clarity
- Provides context and advice
- Includes disclaimers when appropriate

### Smart Responses
- Adapts based on recommendation type
- Provides actionable insights
- Explains confidence levels
- Suggests next steps

### Error Handling
- Graceful fallbacks for missing data
- Helpful suggestions when stock not found
- Clear error messages

## 🚀 Usage Options

### 1. Command Line
```bash
cd chatbot
python chatbot.py
```
Interactive terminal chat

### 2. Web Interface
```bash
cd chatbot
python web_chatbot.py
```
Then open `http://localhost:8002/chat_ui.html`

### 3. One-Click Start
```bash
cd chatbot
start_chatbot.bat    # Windows
./start_chatbot.sh   # Linux/Mac
```

### 4. API Integration
```python
from chatbot import StockChatbot

bot = StockChatbot()
answer = bot.answer_question("Should I buy AAPL?")
print(answer)
```

## 📊 Data Sources

- **Predictions**: `../data/predictions.csv`
- **News**: `../data/news_analyzed.csv`

Auto-loads on startup, supports 550+ stocks and 1000+ news articles.

## 🎨 Design

- Glassmorphism UI matching main dashboard
- Frosted glass effects
- Smooth animations
- Typing indicators
- Message bubbles with avatars
- Responsive design

## 💡 Example Conversations

**User**: "Hello!"
**Bot**: "👋 Hello! I'm your AI stock advisor..."

**User**: "What are the top buy recommendations?"
**Bot**: "🚀 Here are my top 5 AI-powered buy recommendations: 1. BMY..."

**User**: "Should I buy AAPL?"
**Bot**: "⚖️ AAPL is neutral right now. My AI recommends HOLD..."

**User**: "Compare AAPL vs MSFT"
**Bot**: "📊 Comparison: AAPL vs MSFT..."

**User**: "What is the weather?"
**Bot**: "I appreciate the question, but I'm specialized in stock market analysis!..."

## 🔧 Technical Details

- **Language**: Python 3.8+
- **Dependencies**: pandas, fastapi, uvicorn
- **Pattern Matching**: Regex-based with fuzzy matching
- **Response Generation**: Template-based with dynamic data
- **Context Handling**: Conversation history tracking
- **Error Recovery**: Graceful fallbacks

## 🎯 Future Enhancements

Potential additions:
- [ ] Multi-turn conversations with context
- [ ] Portfolio tracking and advice
- [ ] Price alerts and notifications
- [ ] Technical analysis explanations
- [ ] Earnings calendar integration
- [ ] Voice interface
- [ ] Multi-language support

## ✨ Key Differentiators

1. **Natural Language**: Understands casual questions
2. **Contextual**: Provides advice, not just data
3. **Intelligent**: Handles out-of-context gracefully
4. **Comprehensive**: Covers all aspects of stock analysis
5. **User-Friendly**: Emojis, formatting, clear language
6. **Accurate**: Based on real data and AI predictions

---

**Built with intelligence and care for better investment decisions! 📈**
