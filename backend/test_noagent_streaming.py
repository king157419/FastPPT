#!/usr/bin/env python
"""Test non-agent streaming"""
import requests
import json

url = "http://localhost:8000/api/chat"
data = {
    "messages": [{"role": "user", "content": "你好"}],
    "stream": True,
    "use_agent": False,  # Explicitly disable agent
    "session_id": "test-noagent-001"
}

print("Testing non-agent streaming...")
print(f"URL: {url}")
print(f"Request: {json.dumps(data, ensure_ascii=False)}")
print("\nResponse:")
print("-" * 50)

try:
    response = requests.post(url, json=data, stream=True, timeout=30)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
    else:
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    try:
                        chunk_data = json.loads(data_str)
                        if 'error' in chunk_data:
                            print(f"\n[ERROR] {chunk_data['error']}")
                            break
                        elif 'chunk' in chunk_data:
                            print(chunk_data['chunk'], end='', flush=True)
                        elif 'done' in chunk_data:
                            print(f"\n\n[DONE] Intent ready: {chunk_data.get('intent_ready')}")
                    except json.JSONDecodeError as e:
                        print(f"\n[JSON Error: {e}]")

except Exception as e:
    print(f"\nException: {e}")
