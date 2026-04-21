#!/usr/bin/env python
"""Test agent streaming directly (bypass FastAPI)"""
import os
import asyncio

# Set environment variables
os.environ["DEEPSEEK_API_KEY"] = "sk-f6a3e145bcdf477a8b07d964fadf9220"
os.environ["REDIS_URL"] = ""

async def test_streaming():
    print("Testing agent streaming directly...")

    try:
        from integrations.langchain_agent import get_teaching_agent

        print("1. Getting agent...")
        agent = get_teaching_agent()
        print(f"   Success! Agent type: {type(agent)}")

        print("\n2. Starting streaming chat...")
        session_id = "test-direct-001"
        message = "你好"

        chunk_count = 0
        async for chunk in agent.chat_stream(message=message, session_id=session_id):
            chunk_count += 1
            print(chunk, end='', flush=True)

        print(f"\n\n3. Streaming completed! Total chunks: {chunk_count}")

    except Exception as e:
        print(f"\nFailed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_streaming())
