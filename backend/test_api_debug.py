#!/usr/bin/env python
"""Test API with detailed error tracking"""
import requests
import json

url = "http://localhost:8000/api/chat"
data = {
    "messages": [{"role": "user", "content": "你好"}],
    "stream": False,  # Non-streaming first
    "use_agent": True,
    "session_id": "test-debug-001"
}

print("Testing non-streaming agent mode...")
print(f"URL: {url}")
print(f"Request: {json.dumps(data, ensure_ascii=False)}")
print("\nResponse:")
print("-" * 50)

try:
    response = requests.post(url, json=data, timeout=30)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"Reply: {result.get('reply', '')[:100]}...")
        print(f"Agent mode: {result.get('agent_mode')}")
        print(f"Fallback mode: {result.get('fallback_mode')}")
    else:
        print(f"Error response: {response.text}")

except Exception as e:
    print(f"Exception: {e}")
