"""
Quick demo of the chatbot capabilities
"""
from chatbot import StockChatbot

def demo():
    print("=" * 70)
    print("🤖 STOCK AI CHATBOT - DEMO")
    print("=" * 70)
    print()
    
    bot = StockChatbot()
    
    demo_questions = [
        "Hello!",
        "What are the top buy recommendations?",
        "Should I buy AAPL?",
        "Tell me about Tesla",
        "Compare AAPL vs MSFT",
        "What's the market sentiment?",
        "Show me the biggest losers",
        "What is the weather today?",  # Out of context test
    ]
    
    for i, question in enumerate(demo_questions, 1):
        print(f"\n{'='*70}")
        print(f"Question {i}: {question}")
        print(f"{'='*70}")
        answer = bot.answer_question(question)
        print(answer)
        print()
    
    print("=" * 70)
    print("✅ Demo complete! Try the interactive chat with: python chatbot.py")
    print("=" * 70)


if __name__ == "__main__":
    demo()
