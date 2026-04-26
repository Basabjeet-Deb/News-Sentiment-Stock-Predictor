"""
Test casual conversation handling in chatbot.
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1/chat/"

test_messages = [
    "hi",
    "hey",
    "how are you",
    "thanks",
    "what are the top picks?",
    "tell me about NVDA",
    "AAPL",
    "market sentiment",
    "what's the weather like?",  # Non-stock question
]

def test_chat(message):
    """Send a message to the chatbot and print response."""
    try:
        response = requests.post(
            BASE_URL,
            json={"message": message},
            timeout=15
        )
        
        if response.ok:
            data = response.json()
            print(f"\n👤 User: {message}")
            print(f"🤖 Bot: {data['response']}")
            print(f"   Source: {data['source']}")
        else:
            print(f"\n❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Casual Conversation Handling")
    print("=" * 60)
    
    for msg in test_messages:
        test_chat(msg)
    
    print("\n" + "=" * 60)
    print("✅ Test Complete")
    print("=" * 60)
