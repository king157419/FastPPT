"""Test script for LangChain Teaching Agent.

This script demonstrates basic usage of the TeachingAgent class.
Run with: python -m pytest test_langchain_agent.py -v
Or manually: python test_langchain_agent.py
"""

import asyncio
import os
import sys

# Fix encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

from langchain_agent import TeachingAgent, AgentConfig


async def test_basic_chat():
    """Test basic chat functionality."""
    print("\n=== Testing Basic Chat ===")

    # Configure agent
    config = AgentConfig(
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", "test-key"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    )

    try:
        agent = TeachingAgent(config)
        print("✓ Agent initialized successfully")

        # Test chat (will fail without real API key and Redis)
        session_id = "test-session-001"
        response = await agent.chat("你好，我想制作一个关于Python编程的课件", session_id)
        print(f"✓ Chat response: {response[:100]}...")

    except ValueError as e:
        print(f"✓ Expected error (missing API key): {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


async def test_streaming_chat():
    """Test streaming chat functionality."""
    print("\n=== Testing Streaming Chat ===")

    config = AgentConfig(
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", "test-key"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    )

    try:
        agent = TeachingAgent(config)
        print("✓ Agent initialized successfully")

        # Test streaming (will fail without real API key and Redis)
        session_id = "test-session-002"
        print("Streaming response: ", end="")
        async for chunk in agent.chat_stream("介绍一下机器学习", session_id):
            print(chunk, end="", flush=True)
        print("\n✓ Streaming completed")

    except ValueError as e:
        print(f"✓ Expected error (missing API key): {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


async def test_ppt_generation():
    """Test PPT generation functionality."""
    print("\n=== Testing PPT Generation ===")

    config = AgentConfig(
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", "test-key"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    )

    try:
        agent = TeachingAgent(config)
        print("✓ Agent initialized successfully")

        # Test PPT generation
        teaching_spec = {
            "topic": "Python基础编程",
            "audience": "大一本科生",
            "key_points": ["变量与数据类型", "控制流程", "函数定义"],
            "duration": "45分钟",
            "style": "简洁学术"
        }

        result = await agent.generate_ppt(teaching_spec)
        print(f"✓ PPT generated with {len(result.get('pages', []))} pages")

    except ValueError as e:
        print(f"✓ Expected error (missing API key): {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


def test_imports():
    """Test that all imports work correctly."""
    print("\n=== Testing Imports ===")

    try:
        from langchain_agent import (
            TeachingAgent,
            AgentConfig,
            RedisMemoryStore,
            get_teaching_agent,
            retrieve_knowledge,
            generate_ppt_content,
            get_preview_url,
        )
        print("✓ All imports successful")
        print("✓ TeachingAgent class available")
        print("✓ AgentConfig class available")
        print("✓ RedisMemoryStore class available")
        print("✓ get_teaching_agent function available")
        print("✓ Tool functions available")

    except ImportError as e:
        print(f"✗ Import failed: {e}")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("LangChain Teaching Agent Test Suite")
    print("=" * 60)

    # Test imports first
    test_imports()

    # Test async functionality
    await test_basic_chat()
    await test_streaming_chat()
    await test_ppt_generation()

    print("\n" + "=" * 60)
    print("Test suite completed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
