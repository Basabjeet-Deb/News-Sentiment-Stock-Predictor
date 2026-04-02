"""Test the chatbot with various questions"""
from chatbot import StockChatbot

bot = StockChatbot()

test_questions = [
    ("Should I buy AAPL?", "Investment advice"),
    ("What is the weather today?", "Out of context"),
    ("Hello", "Greeting"),
    ("Compare AAPL vs MSFT", "Comparison"),
    ("What are the top recommendations?", "Top picks"),
    ("Tell me about Tesla", "Company search"),
    ("Show me the biggest losers", "Market movers"),
    ("What's the market sentiment?", "Market analysis"),
]

print("=" * 70)
print("🤖 CHATBOT TEST SUITE")
print("=" * 70)

for question, test_type in test_questions:
    print(f"\n📝 Test: {test_type}")
    print(f"❓ Question: {question}")
    print(f"💬 Answer:\n{bot.answer_question(question)}")
    print("-" * 70)
