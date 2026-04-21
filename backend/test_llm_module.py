#!/usr/bin/env python
"""Test core.llm module"""
import os

# Set environment variables BEFORE importing core.llm
os.environ["ANTHROPIC_API_KEY"] = "B003MH0H-6TY8-2N5X-90Z2-EWXQ2JKKFNBC"
os.environ["ANTHROPIC_BASE_URL"] = "https://yunyi.cfd/claude"
os.environ["DEEPSEEK_API_KEY"] = ""
os.environ["DASHSCOPE_API_KEY"] = ""

print("Environment variables set:")
print(f"ANTHROPIC_API_KEY: {os.environ['ANTHROPIC_API_KEY'][:20]}...")
print(f"ANTHROPIC_BASE_URL: {os.environ['ANTHROPIC_BASE_URL']}")

# Now import core.llm
from core.llm import chat_with_claude

print("\nTesting chat_with_claude...")
try:
    messages = [{"role": "user", "content": "Hello, say hi in one sentence"}]
    response = chat_with_claude(messages)
    print(f"Success! Response: {response[:100]}...")
except Exception as e:
    print(f"Failed: {e}")
    import traceback
    traceback.print_exc()
