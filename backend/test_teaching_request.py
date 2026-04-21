#!/usr/bin/env python
"""Test teaching request"""
import requests
import json

url = "http://localhost:8000/api/chat"
data = {
    "messages": [{"role": "user", "content": "我想生成一份关于光合作用的初中生物课件"}],
    "stream": False,
    "use_agent": False
}

print("Testing teaching request...")
response = requests.post(url, json=data, timeout=30)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"Intent ready: {result.get('intent_ready')}")
    print(f"Reply length: {len(result.get('reply', ''))}")
    if result.get('intent_ready'):
        print(f"Teaching spec: {json.dumps(result.get('teaching_spec', {}), ensure_ascii=False, indent=2)}")
else:
    print(f"Error: {response.text[:200]}")
