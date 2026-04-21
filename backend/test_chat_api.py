#!/usr/bin/env python
"""Test chat API with requests"""
import requests
import json

url = "http://localhost:8000/api/chat"
data = {
    "messages": [{"role": "user", "content": "hello"}],
    "stream": False,
    "use_agent": False
}

print("Testing POST /api/chat...")
print(f"URL: {url}")
print(f"Data: {json.dumps(data, indent=2)}")

try:
    response = requests.post(url, json=data, timeout=15)
    print(f"\nStatus: {response.status_code}")
    print(f"Response: {response.text[:500]}")

    if response.status_code == 200:
        result = response.json()
        print(f"\nSuccess! Reply: {result.get('reply', '')[:200]}")
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
