#!/usr/bin/env python
"""Test agent initialization"""
import os
import sys

# Set environment variables
os.environ.setdefault("DEEPSEEK_API_KEY", "sk-REPLACE_ME")  # 原硬编码密钥已移除
os.environ["REDIS_URL"] = ""

print("Testing agent initialization...")

try:
    from integrations.langchain_agent import get_teaching_agent

    print("Calling get_teaching_agent()...")
    agent = get_teaching_agent()

    print(f"Success! Agent type: {type(agent)}")
    print(f"Agent has _memory_cache: {hasattr(agent, '_memory_cache')}")

except Exception as e:
    print(f"Failed: {e}")
    import traceback
    traceback.print_exc()
