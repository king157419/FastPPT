#!/usr/bin/env python
"""Test Claude API connection"""
import os
import anthropic

# Set environment variables explicitly
os.environ["ANTHROPIC_API_KEY"] = "B003MH0H-6TY8-2N5X-90Z2-EWXQ2JKKFNBC"
os.environ["ANTHROPIC_BASE_URL"] = "https://yunyi.cfd/claude"

print("Testing Claude API...")
print(f"API Key: {os.environ['ANTHROPIC_API_KEY'][:20]}...")
print(f"Base URL: {os.environ['ANTHROPIC_BASE_URL']}")

try:
    client = anthropic.Anthropic(
        api_key=os.environ["ANTHROPIC_API_KEY"],
        base_url=os.environ["ANTHROPIC_BASE_URL"]
    )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=[{"role": "user", "content": "Hello"}]
    )

    print("\nSuccess!")
    print(f"Response: {response.content[0].text}")

except Exception as e:
    print(f"\nFailed: {e}")
    import traceback
    traceback.print_exc()
