#!/usr/bin/env python
"""Test agent streaming"""
import requests
import json

url = "http://localhost:8000/api/chat"
data = {
    "messages": [{"role": "user", "content": "你好，我想生成一份关于光合作用的初中生物课件"}],
    "stream": True,
    "use_agent": True,
    "session_id": "test-session-001"
}

print("Testing agent streaming...")
print(f"URL: {url}")
print(f"Session ID: {data['session_id']}")
print("\nStreaming response:")
print("-" * 50)

try:
    response = requests.post(url, json=data, stream=True, timeout=60)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
    else:
        chunk_count = 0
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    chunk_count += 1
                    data_str = line_str[6:]  # Remove 'data: ' prefix
                    try:
                        chunk_data = json.loads(data_str)
                        if 'chunk' in chunk_data:
                            print(chunk_data['chunk'], end='', flush=True)
                        elif 'done' in chunk_data:
                            print(f"\n\n{'='*50}")
                            print(f"Stream completed!")
                            print(f"Total chunks: {chunk_count}")
                            print(f"Intent ready: {chunk_data.get('intent_ready')}")
                            if chunk_data.get('intent_ready'):
                                print(f"Teaching spec keys: {list(chunk_data.get('teaching_spec', {}).keys())}")
                    except json.JSONDecodeError:
                        print(f"\n[Invalid JSON: {data_str[:50]}...]")

        if chunk_count == 0:
            print("No chunks received!")

except Exception as e:
    print(f"\nException: {e}")
    import traceback
    traceback.print_exc()
