"""
AI Chatbot for Stock Predictions
Intelligent conversational assistant for stock market queries
"""
import os
import json
import re
from typing import List, Dict, Optional, Tuple
import pandas as pd
from datetime import datetime


class StockChatbot:
    """AI-powered conversational chatbot for stock market queries"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Auto-detect data directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.data_dir = os.path.join(os.path.dirname(current_dir), "data")
        else:
            self.data_dir = data_dir
        self.predictions = []
        self.news = []
        self.conversation_history = []
        self.load_data()
    
    def load_data(self):
        """Load predictions and news data"""
        try:
            pred_file = os.path.join(self.data_dir, "predictions.csv")
            if os.path.exists(pred_file):
                df = pd.read_csv(pred_file)
                self.predictions = df.to_dict('records')
            
            news_file = os.path.join(self.data_dir, "news_analyzed.csv")
            if os.path.exists(news_file):
                df = pd.read_csv(news_file)
                self.news = df.to_dict('records')
            
            print(f"✅ Loaded {len(self.predictions)} predictions, {len(self.news)} news articles")
        except Exception as e:
            print(f"⚠️ Error loading data: {e}")
    
    def get_stock_info(self, ticker: str) -> Optional[Dict]:
        """Get prediction info for a specific stock"""
        ticker = ticker.upper()
        for pred in self.predictions:
            if pred.get('ticker') == ticker:
                return pred
        return None
    
    def get_stock_news(self, ticker: str) -> List[Dict]:
        """Get news articles for a specific stock"""
        ticker = ticker.upper()
        return [n for n in self.news if n.get('ticker') == ticker]
    
    def get_top_recommendations(self, count: int = 5) -> List[Dict]:
        """Get top buy recommendations"""
        buy_stocks = [p for p in self.predictions 
                     if p.get('recommendation') in ['STRONG BUY', 'BUY']]
        return sorted(buy_stocks, key=lambda x: x.get('prediction_score', 0), reverse=True)[:count]
    
    def get_market_sentiment(self) -> Dict:
        """Get overall market sentiment"""
        if not self.news:
            return {"positive": 0, "neutral": 0, "negative": 0}
        
        positive = sum(1 for n in self.news if n.get('sentiment_compound', 0) > 0.05)
        negative = sum(1 for n in self.news if n.get('sentiment_compound', 0) < -0.05)
        neutral = len(self.news) - positive - negative
        
        return {
            "positive": positive,
            "neutral": neutral,
            "negative": negative,
            "total": len(self.news)
        }
    
    def extract_ticker(self, text: str) -> Optional[str]:
        """Extract ticker symbol from text - only if clearly mentioned"""
        text_upper = text.upper()
        words = text_upper.split()
        
        # Only match if it's a clear ticker mention (2-5 chars, all caps in original)
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word)
            # Must be 2-5 characters and exist in our data
            if 2 <= len(clean_word) <= 5 and clean_word.isupper() and self.get_stock_info(clean_word):
                return clean_word
        
        # Check for explicit ticker mentions like "ticker AAPL" or "stock AAPL"
        ticker_pattern = r'\b([A-Z]{2,5})\b'
        matches = re.findall(ticker_pattern, text)
        for match in matches:
            if self.get_stock_info(match):
                return match
        
        return None
    
    def find_similar_stocks(self, query: str) -> List[Dict]:
        """Find stocks matching a query"""
        query = query.lower()
        matches = []
        
        for pred in self.predictions:
            ticker = pred.get('ticker', '').lower()
            company = pred.get('company_name', '').lower()
            
            if query in ticker or query in company:
                matches.append(pred)
        
        return matches[:5]
    
    def get_stocks_by_recommendation(self, rec_type: str) -> List[Dict]:
        """Get stocks by recommendation type"""
        rec_type = rec_type.upper()
        return [p for p in self.predictions if rec_type in p.get('recommendation', '')]
    
    def compare_stocks(self, ticker1: str, ticker2: str) -> str:
        """Compare two stocks"""
        stock1 = self.get_stock_info(ticker1)
        stock2 = self.get_stock_info(ticker2)
        
        if not stock1 or not stock2:
            return f"Sorry, I couldn't find data for both {ticker1} and {ticker2}."
        
        return f"""
📊 Comparison: {ticker1} vs {ticker2}

{ticker1} ({stock1.get('company_name', ticker1)}):
  💰 Price: ${stock1.get('current_price', 0):.2f}
  📈 Change: {stock1.get('price_change_percent', 0):+.2f}%
  🎯 Recommendation: {stock1.get('recommendation', 'N/A')}
  📊 Confidence: {stock1.get('confidence', 0)*100:.0f}%
  💭 Sentiment: {stock1.get('avg_sentiment', 0)*100:.0f}%

{ticker2} ({stock2.get('company_name', ticker2)}):
  💰 Price: ${stock2.get('current_price', 0):.2f}
  📈 Change: {stock2.get('price_change_percent', 0):+.2f}%
  🎯 Recommendation: {stock2.get('recommendation', 'N/A')}
  📊 Confidence: {stock2.get('confidence', 0)*100:.0f}%
  💭 Sentiment: {stock2.get('avg_sentiment', 0)*100:.0f}%

💡 Better Pick: {ticker1 if stock1.get('prediction_score', 0) > stock2.get('prediction_score', 0) else ticker2}
"""
    
    def get_sector_analysis(self) -> str:
        """Analyze stocks by sector"""
        sectors = {}
        for pred in self.predictions:
            sector = pred.get('sector', 'Unknown')
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(pred)
        
        result = "🏢 Sector Analysis:\n\n"
        for sector, stocks in sorted(sectors.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
            avg_sentiment = sum(s.get('avg_sentiment', 0) for s in stocks) / len(stocks) if stocks else 0
            buy_count = sum(1 for s in stocks if 'BUY' in s.get('recommendation', ''))
            
            sentiment_emoji = "🟢" if avg_sentiment > 0.1 else "🔴" if avg_sentiment < -0.1 else "⚪"
            result += f"{sentiment_emoji} {sector}: {len(stocks)} stocks | {buy_count} buys | Sentiment: {avg_sentiment*100:.0f}%\n"
        
        return result
    
    def answer_question(self, question: str) -> str:
        """Answer user questions intelligently"""
        question_lower = question.lower().strip()
        
        # Store in conversation history
        self.conversation_history.append({"role": "user", "content": question})
        
        # Extract tickers mentioned
        ticker = self.extract_ticker(question)
        
        # Pattern matching with intelligent responses
        
        # Comparison queries
        if " vs " in question_lower or " versus " in question_lower or " or " in question_lower:
            tickers = [self.extract_ticker(part) for part in re.split(r' vs | versus | or ', question, flags=re.IGNORECASE)]
            tickers = [t for t in tickers if t]
            if len(tickers) >= 2:
                return self.compare_stocks(tickers[0], tickers[1])
        
        # Should I buy/invest queries
        if ticker and any(word in question_lower for word in ["should i buy", "should i invest", "good to buy", "worth buying", "is it good"]):
            info = self.get_stock_info(ticker)
            if info:
                rec = info.get('recommendation', '')
                conf = info.get('confidence', 0) * 100
                sentiment = info.get('avg_sentiment', 0) * 100
                
                if 'BUY' in rec:
                    return f"✅ Yes, {ticker} looks promising! My AI recommends {rec} with {conf:.0f}% confidence. Sentiment is {sentiment:+.0f}% based on {info.get('news_count', 0)} news articles. Current price: ${info.get('current_price', 0):.2f}"
                elif 'SELL' in rec:
                    return f"⚠️ I'd be cautious with {ticker}. My AI recommends {rec} with {conf:.0f}% confidence. Sentiment is {sentiment:+.0f}%. Current price: ${info.get('current_price', 0):.2f}"
                else:
                    return f"⚖️ {ticker} is neutral right now. My AI recommends {rec}. Sentiment is {sentiment:+.0f}%. You might want to wait for a clearer signal. Current price: ${info.get('current_price', 0):.2f}"
        
        # Price prediction queries
        if ticker and any(word in question_lower for word in ["will it go up", "will it rise", "will it fall", "will it drop", "price prediction", "forecast"]):
            info = self.get_stock_info(ticker)
            if info:
                rec = info.get('recommendation', '')
                change = info.get('price_change_percent', 0)
                sentiment = info.get('avg_sentiment', 0)
                
                if 'BUY' in rec and sentiment > 0:
                    return f"📈 Based on my analysis, {ticker} is likely to go UP. Current momentum is {change:+.2f}%, sentiment is positive ({sentiment*100:.0f}%), and I recommend {rec}. But remember, this is not financial advice!"
                elif 'SELL' in rec and sentiment < 0:
                    return f"📉 Based on my analysis, {ticker} might go DOWN. Current momentum is {change:+.2f}%, sentiment is negative ({sentiment*100:.0f}%), and I recommend {rec}. But remember, this is not financial advice!"
                else:
                    return f"⚖️ {ticker} is showing mixed signals. Current change: {change:+.2f}%, sentiment: {sentiment*100:.0f}%. I recommend {rec}. It's hard to predict short-term movements."
        
        # Top recommendations - more flexible matching
        if ("top" in question_lower or "best" in question_lower or "good" in question_lower) and \
           ("recommendation" in question_lower or "stock" in question_lower or "pick" in question_lower or "buy" in question_lower or "investment" in question_lower):
            return self._format_top_recommendations()
        
        if "what should i buy" in question_lower or "what to buy" in question_lower or "what to invest" in question_lower:
            return self._format_top_recommendations()
        
        # Worst/sell recommendations
        if (any(word in question_lower for word in ["worst", "avoid", "sell", "bad", "risky"]) and 
            "stock" in question_lower) or "what to sell" in question_lower:
            return self._format_worst_stocks()
        
        # Specific stock info - check ticker first, then company name
        if ticker and any(word in question_lower for word in ["price", "info", "about", "tell me", "what is", "how is", "status", "doing"]):
            return self._format_stock_info(ticker)
        
        # Company name search (e.g., "Tell me about Tesla")
        if any(phrase in question_lower for phrase in ["tell me about", "what about", "how about", "info on", "information on"]):
            # Try to find company by name
            search_term = question_lower
            for phrase in ["tell me about", "what about", "how about", "info on", "information on"]:
                search_term = search_term.replace(phrase, "").strip()
            
            matches = self.find_similar_stocks(search_term)
            if matches:
                return self._format_stock_info(matches[0].get('ticker'))
        
        # Stock news
        if ticker and "news" in question_lower:
            return self._format_stock_news(ticker)
        
        # Market sentiment
        if any(phrase in question_lower for phrase in ["market sentiment", "market mood", "how is the market", "market looking", "bullish", "bearish", "market today"]):
            return self._format_market_sentiment()
        
        # Sector analysis
        if "sector" in question_lower:
            return self.get_sector_analysis()
        
        # Statistics
        if "how many" in question_lower:
            if "stock" in question_lower:
                return f"I'm currently tracking {len(self.predictions)} stocks with AI-powered predictions. These include major companies across all sectors like tech, finance, energy, healthcare, and more."
            elif "news" in question_lower:
                return f"I've analyzed {len(self.news)} news articles from multiple financial sources. These articles cover market news, company announcements, earnings reports, and economic indicators."
        
        # Gainers/losers
        if any(word in question_lower for word in ["gainer", "rising", "going up", "performing well"]):
            return self._format_top_gainers()
        
        if any(word in question_lower for word in ["loser", "falling", "going down", "performing badly"]):
            return self._format_top_losers()
        
        # Search by company name or partial match
        if len(question_lower) > 2 and not any(word in question_lower for word in ["what", "how", "why", "when", "where"]):
            matches = self.find_similar_stocks(question_lower)
            if matches:
                if len(matches) == 1:
                    return self._format_stock_info(matches[0].get('ticker'))
                else:
                    result = f"I found {len(matches)} stocks matching '{question}':\n\n"
                    for stock in matches:
                        result += f"• {stock.get('ticker')} - {stock.get('company_name', 'N/A')} | ${stock.get('current_price', 0):.2f} | {stock.get('recommendation', 'N/A')}\n"
                    result += "\nAsk me about any specific ticker for more details!"
                    return result
        
        # Out of context - redirect to stock topics
        return self._handle_out_of_context(question)
    
    def _format_stock_info(self, ticker: str) -> str:
        """Format stock information"""
        info = self.get_stock_info(ticker)
        if not info:
            return f"Sorry, I don't have data for {ticker}. Try asking about popular stocks like AAPL, TSLA, MSFT, or GOOGL."
        
        change_emoji = "📈" if info.get('price_change_percent', 0) >= 0 else "📉"
        rec_emoji = "🚀" if "BUY" in info.get('recommendation', '') else "⚠️" if "SELL" in info.get('recommendation', '') else "⚖️"
        
        # Add context based on recommendation
        context = ""
        rec = info.get('recommendation', '')
        conf = info.get('confidence', 0) * 100
        
        if 'STRONG BUY' in rec:
            context = f"\n💡 This is a strong buy signal with {conf:.0f}% confidence. The AI sees significant upside potential based on positive news sentiment."
        elif 'BUY' in rec:
            context = f"\n💡 This looks like a good buying opportunity with {conf:.0f}% confidence. Positive sentiment detected in recent news."
        elif 'SELL' in rec:
            context = f"\n⚠️ Caution advised. The AI recommends selling with {conf:.0f}% confidence due to negative sentiment or weak momentum."
        else:
            context = f"\n⚖️ Neutral signal. The AI recommends holding with {conf:.0f}% confidence. Wait for clearer signals."
        
        return f"""
{rec_emoji} {ticker} - {info.get('company_name', ticker)}

💰 Current Price: ${info.get('current_price', 0):.2f}
{change_emoji} Today's Change: {info.get('price_change_percent', 0):+.2f}%
🎯 AI Recommendation: {rec}
📊 Confidence Level: {conf:.0f}%
💭 News Sentiment: {info.get('avg_sentiment', 0)*100:+.0f}%
📰 Articles Analyzed: {info.get('news_count', 0)}
{context}
"""
    
    def _format_stock_news(self, ticker: str) -> str:
        """Format news for a stock"""
        news = self.get_stock_news(ticker)
        if not news:
            return f"I don't have any recent news for {ticker}. This could mean the stock hasn't been in the headlines lately, which might indicate stable, quiet trading."
        
        # Calculate overall sentiment
        avg_sentiment = sum(n.get('sentiment_compound', 0) for n in news) / len(news)
        sentiment_desc = "very positive" if avg_sentiment > 0.3 else "positive" if avg_sentiment > 0.05 else "very negative" if avg_sentiment < -0.3 else "negative" if avg_sentiment < -0.05 else "neutral"
        
        result = f"📰 Latest news for {ticker} ({len(news)} articles)\n"
        result += f"Overall sentiment: {sentiment_desc} ({avg_sentiment*100:+.0f}%)\n\n"
        
        for i, article in enumerate(news[:5], 1):
            sentiment = "🟢" if article.get('sentiment_compound', 0) > 0.05 else "🔴" if article.get('sentiment_compound', 0) < -0.05 else "⚪"
            result += f"{i}. {sentiment} {article.get('title', 'No title')}\n"
            result += f"   {article.get('source', 'Unknown')} | Impact: {article.get('impact_level', 'N/A')} | Sentiment: {article.get('sentiment_compound', 0)*100:+.0f}%\n\n"
        
        if len(news) > 5:
            result += f"...and {len(news) - 5} more articles.\n"
        
        return result
    
    def _format_top_recommendations(self) -> str:
        """Format top recommendations"""
        top = self.get_top_recommendations(5)
        if not top:
            return "I don't have any buy recommendations right now. The market might be showing weak signals, or you may need to run the pipeline to get fresh data."
        
        result = "🚀 Here are my top 5 AI-powered buy recommendations:\n\n"
        for i, stock in enumerate(top, 1):
            emoji = "🔥" if i == 1 else "⭐" if i <= 3 else "✨"
            result += f"{emoji} {i}. {stock.get('ticker')} - {stock.get('company_name', stock.get('ticker'))}\n"
            result += f"   💰 ${stock.get('current_price', 0):.2f} | "
            result += f"📊 {stock.get('recommendation')} ({stock.get('confidence', 0)*100:.0f}% confidence) | "
            result += f"📰 {stock.get('news_count', 0)} articles\n"
            result += f"   💭 Sentiment: {stock.get('avg_sentiment', 0)*100:+.0f}%\n\n"
        
        result += "💡 Remember: These are AI predictions based on news sentiment. Always do your own research before investing!"
        return result
    
    def _format_market_sentiment(self) -> str:
        """Format market sentiment"""
        sentiment = self.get_market_sentiment()
        total = sentiment['total']
        
        if total == 0:
            return "I don't have market data loaded yet. Please run the pipeline first to analyze news and generate predictions."
        
        pos_pct = (sentiment['positive'] / total) * 100
        neu_pct = (sentiment['neutral'] / total) * 100
        neg_pct = (sentiment['negative'] / total) * 100
        
        # Determine overall mood
        if pos_pct > 60:
            overall = "Very Bullish 🚀"
            advice = "The market is showing strong positive sentiment. This could be a good time to look for buying opportunities."
        elif pos_pct > 50:
            overall = "Bullish 🟢"
            advice = "The market sentiment is positive. Consider the top recommendations for potential investments."
        elif neg_pct > 60:
            overall = "Very Bearish 📉"
            advice = "The market is showing strong negative sentiment. Be cautious and consider defensive positions."
        elif neg_pct > 50:
            overall = "Bearish 🔴"
            advice = "The market sentiment is negative. This might be a good time to review your portfolio and consider risk management."
        else:
            overall = "Neutral ⚖️"
            advice = "The market is showing mixed signals. Wait for clearer trends before making major moves."
        
        return f"""
💭 Market Sentiment Analysis

Overall Market Mood: {overall}

🟢 Positive News: {sentiment['positive']} articles ({pos_pct:.1f}%)
⚪ Neutral News: {sentiment['neutral']} articles ({neu_pct:.1f}%)
🔴 Negative News: {sentiment['negative']} articles ({neg_pct:.1f}%)

Total articles analyzed: {total}

💡 {advice}
"""
    
    def _format_top_gainers(self) -> str:
        """Format top gaining stocks"""
        gainers = sorted([p for p in self.predictions if p.get('price_change_percent', 0) > 0],
                        key=lambda x: x.get('price_change_percent', 0), reverse=True)[:5]
        
        if not gainers:
            return "No stocks are showing gains right now. The market might be in a downturn."
        
        result = "📈 Top 5 Gainers Today:\n\n"
        for i, stock in enumerate(gainers, 1):
            result += f"{i}. {stock.get('ticker')} - {stock.get('company_name', stock.get('ticker'))}\n"
            result += f"   💰 ${stock.get('current_price', 0):.2f} | 📈 +{stock.get('price_change_percent', 0):.2f}%\n\n"
        
        return result
    
    def _format_top_losers(self) -> str:
        """Format top losing stocks"""
        losers = sorted([p for p in self.predictions if p.get('price_change_percent', 0) < 0],
                       key=lambda x: x.get('price_change_percent', 0))[:5]
        
        if not losers:
            return "No stocks are showing losses right now. The market is doing well!"
        
        result = "📉 Top 5 Losers Today:\n\n"
        for i, stock in enumerate(losers, 1):
            result += f"{i}. {stock.get('ticker')} - {stock.get('company_name', stock.get('ticker'))}\n"
            result += f"   💰 ${stock.get('current_price', 0):.2f} | 📉 {stock.get('price_change_percent', 0):.2f}%\n\n"
        
        return result
    
    def _format_worst_stocks(self) -> str:
        """Format worst stocks to avoid"""
        worst = sorted([p for p in self.predictions if 'SELL' in p.get('recommendation', '')],
                      key=lambda x: x.get('prediction_score', 0))[:5]
        
        if not worst:
            return "Good news! I don't have any strong sell recommendations right now. The market is looking healthy."
        
        result = "⚠️ Stocks to Avoid (AI Sell Recommendations):\n\n"
        for i, stock in enumerate(worst, 1):
            result += f"{i}. {stock.get('ticker')} - {stock.get('recommendation')}\n"
            result += f"   💰 ${stock.get('current_price', 0):.2f} | "
            result += f"📊 Confidence: {stock.get('confidence', 0)*100:.0f}% | "
            result += f"💭 Sentiment: {stock.get('avg_sentiment', 0)*100:+.0f}%\n\n"
        
        return result
    
    def _handle_out_of_context(self, question: str) -> str:
        """Handle out-of-context questions gracefully"""
        question_lower = question.lower()
        
        # Check if it's a greeting
        greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "howdy"]
        if any(greeting == question_lower or question_lower.startswith(greeting + " ") for greeting in greetings):
            return "👋 Hello! I'm your AI stock advisor. I analyze 550+ stocks using news sentiment and provide buy/sell recommendations. What would you like to know about the stock market today?"
        
        # Check if asking about capabilities
        if any(word in question_lower for word in ["what can you", "what do you", "help me", "how do you work", "what do you do"]):
            return self._format_help()
        
        # Check if asking about the chatbot itself
        if any(word in question_lower for word in ["who are you", "what are you", "your name", "introduce yourself"]):
            return "I'm an AI-powered stock market assistant built to help investors make informed decisions. I analyze news sentiment from 1000+ articles daily, track 550+ stocks, and provide buy/sell recommendations with confidence scores. Think of me as your personal financial analyst! 📊"
        
        # Thank you
        if any(word in question_lower for word in ["thank", "thanks", "appreciate"]):
            return "You're welcome! Happy to help. Feel free to ask me anything else about stocks or the market. 😊"
        
        # Clearly non-stock related
        non_stock_keywords = ["weather", "food", "movie", "music", "sports", "game", "recipe", "travel", "politics", "religion"]
        if any(keyword in question_lower for keyword in non_stock_keywords):
            return f"""
I appreciate the question, but I'm specialized in stock market analysis! 📈

I can't help with {question_lower.split()[0] if question_lower.split() else 'that'}, but I'm great at:

💰 Stock prices and predictions
📰 News sentiment analysis
🎯 Buy/sell recommendations
📊 Market trends and analysis

Want to know about any stocks? Try asking:
• "What are the top buy recommendations?"
• "Should I invest in tech stocks?"
• "What's the market sentiment today?"
"""
        
        # Generic unclear question
        return f"""
Hmm, I'm not sure I understand. I'm specialized in stock market analysis.

I can help you with:
📊 Stock prices and recommendations (e.g., "Tell me about AAPL")
📰 News sentiment analysis (e.g., "Show news for TSLA")
💭 Market trends (e.g., "What's the market sentiment?")
🎯 Investment advice (e.g., "Should I buy NVDA?")
📈 Top picks (e.g., "What are the best stocks?")

What would you like to know about the stock market?
"""
    
    def _format_help(self) -> str:
        """Format help message"""
        return """
🤖 I'm your AI Stock Assistant! Here's what I can help you with:

📊 Stock Information:
  • "Tell me about AAPL"
  • "What's the price of TSLA?"
  • "How is MSFT doing?"
  • "Should I buy NVDA?"

📰 News & Sentiment:
  • "Show news for AAPL"
  • "What's the latest on GOOGL?"
  • "Any news about Tesla?"

🎯 Recommendations:
  • "What are the top buy recommendations?"
  • "Which stocks should I avoid?"
  • "Show me the best picks"

💭 Market Analysis:
  • "What's the market sentiment?"
  • "Is the market bullish or bearish?"
  • "How's the market looking?"

📈 Comparisons:
  • "Compare AAPL vs MSFT"
  • "TSLA or NVDA?"
  • "Which is better: AMD vs INTC?"

🏢 Sector Analysis:
  • "Show me sector analysis"
  • "Which sectors are performing well?"

📊 Market Movers:
  • "What are the top gainers?"
  • "Show me the biggest losers"

Just ask me naturally, and I'll help you navigate the stock market!
"""
    
    def chat(self):
        """Interactive chat loop"""
        print("=" * 60)
        print("🤖 Stock AI Assistant")
        print("=" * 60)
        print("Hi! I'm your personal AI stock advisor. I analyze news sentiment")
        print("and provide buy/sell recommendations for 550+ stocks.")
        print("\nAsk me anything about stocks, and I'll help you out!")
        print("Type 'quit' or 'exit' to end the conversation.\n")
        
        while True:
            try:
                question = input("You: ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                    print("\n👋 Thanks for chatting! Remember: Always do your own research before investing. Good luck! 📈")
                    break
                
                answer = self.answer_question(question)
                print(f"\n🤖 AI: {answer}\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Happy investing! 📈")
                break
            except Exception as e:
                print(f"\n❌ Oops, I encountered an error: {e}")
                print("Try rephrasing your question or ask me something else!\n")


if __name__ == "__main__":
    bot = StockChatbot()
    bot.chat()
