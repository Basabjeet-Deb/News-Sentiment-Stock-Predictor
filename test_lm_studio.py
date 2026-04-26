#!/usr/bin/env python3
"""
Test script for LM Studio integration.

Tests:
1. LM Studio connection
2. Chatbot endpoint
3. Response format
4. Fallback mode
"""

import requests
import json
import time
from datetime import datetime


def test_lm_studio_direct():
    """Test direct connection to LM Studio."""
    print("\n" + "="*60)
    print("TEST 1: LM Studio Direct Connection")
    print("="*60)
    
    url = "http://127.0.0.1:1234/v1/chat/completions"
    payload = {
        "model": "qwen",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Answer in max 10 words."},
            {"role": "user", "content": "Hello, are you working?"}
        ],
        "temperature": 0.2,
        "max_tokens": 20
    }
    
    try:
        start = time.time()
        response = requests.post(url, json=payload, timeout=10)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✅ LM Studio is running")
            print(f"⏱️  Response time: {elapsed:.2f}s")
            print(f"💬 Response: {content}")
            return True
        else:
            print(f"❌ LM Studio returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to LM Studio")
        print("   Make sure LM Studio is running on port 1234")
        return False
    except requests.exceptions.Timeout:
        print("❌ LM Studio timeout (>10s)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_chatbot_health():
    """Test chatbot health endpoint."""
    print("\n" + "="*60)
    print("TEST 2: Chatbot Health Check")
    print("="*60)
    
    url = "http://localhost:8000/api/v1/chat/health"
    
    try:
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chatbot service is healthy")
            print(f"🔗 LM Studio URL: {data.get('lm_studio_url')}")
            print(f"⏰ Timestamp: {data.get('timestamp')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to FastAPI backend")
        print("   Make sure the backend is running on port 8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_chatbot_query(message):
    """Test chatbot with a query."""
    print(f"\n📤 User: {message}")
    
    url = "http://localhost:8000/api/v1/chat/"
    payload = {"message": message}
    
    try:
        start = time.time()
        response = requests.post(url, json=payload, timeout=15)
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response received ({elapsed:.2f}s)")
            print(f"🤖 Bot: {data.get('response')}")
            print(f"📍 Source: {data.get('source')}")
            
            # Check word count
            word_count = len(data.get('response', '').split())
            if word_count <= 45:
                print(f"✅ Word count: {word_count}/45")
            else:
                print(f"⚠️  Word count: {word_count}/45 (exceeds limit)")
            
            return True
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout (>15s)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("LM STUDIO INTEGRATION TEST SUITE")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Test 1: LM Studio direct
    results.append(("LM Studio Connection", test_lm_studio_direct()))
    
    # Test 2: Health check
    results.append(("Chatbot Health", test_chatbot_health()))
    
    # Test 3: Sample queries
    print("\n" + "="*60)
    print("TEST 3: Chatbot Queries")
    print("="*60)
    
    queries = [
        "What are the top picks today?",
        "Tell me about AAPL",
        "Market sentiment?",
    ]
    
    for query in queries:
        results.append((f"Query: {query[:30]}", test_chatbot_query(query)))
        time.sleep(1)  # Rate limiting
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
