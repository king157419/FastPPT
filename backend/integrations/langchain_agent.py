"""LangChain-based Teaching Agent with multi-turn conversation and tool integration.

This module provides a production-ready teaching agent with:
- Multi-turn conversation with memory persistence
- Tool integration (RAG retrieval, PPT generation, preview)
- Streaming output support
- Redis-based memory storage
- Comprehensive error handling and logging
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from typing import Any, AsyncGenerator, Optional

import redis.asyncio as redis
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

class AgentConfig(BaseModel):
    """Configuration for Teaching Agent."""
    deepseek_api_key: str = Field(default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", ""))
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    model_name: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 4096
    redis_url: str = Field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    memory_ttl: int = 86400  # 24 hours


# ============================================================================
# Memory Management
# ============================================================================

class RedisMemoryStore:
    """Redis-based memory store for conversation persistence - DISABLED."""

    def __init__(self, redis_url: str, ttl: int = 86400):
        self.redis_url = redis_url
        self.ttl = ttl
        self._client: Optional[redis.Redis] = None
        self._memory_cache = {}  # 使用内存缓存替代Redis

    async def __aenter__(self):
        """Async context manager entry - Redis disabled, using in-memory cache."""
        # 不连接Redis，使用内存缓存
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass  # 无需关闭连接

    def _get_key(self, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"teaching_agent:memory:{session_id}"

    async def save_messages(self, session_id: str, messages: list[dict[str, Any]]) -> None:
        """Save conversation messages to in-memory cache (Redis disabled).

        Args:
            session_id: Unique session identifier
            messages: List of message dictionaries
        """
        key = self._get_key(session_id)
        self._memory_cache[key] = messages
        logger.info(f"Saved {len(messages)} messages for session {session_id} (in-memory)")

    async def load_messages(self, session_id: str) -> list[dict[str, Any]]:
        """Load conversation messages from in-memory cache (Redis disabled).

        Args:
            session_id: Unique session identifier

        Returns:
            List of message dictionaries
        """
        key = self._get_key(session_id)
        messages = self._memory_cache.get(key, [])
        logger.info(f"Loaded {len(messages)} messages for session {session_id} (in-memory)")
        return messages

    async def delete_session(self, session_id: str) -> bool:
        """Delete session from in-memory cache.

        Args:
            session_id: Unique session identifier

        Returns:
            True if deleted, False if not found
        """
        key = self._get_key(session_id)
        existed = key in self._memory_cache
        self._memory_cache.pop(key, None)
        logger.info(f"Deleted session {session_id}: {existed} (in-memory)")
        return existed


# ============================================================================
# Tools
# ============================================================================

@tool
def retrieve_knowledge(query: str, top_k: int = 3) -> str:
    """Retrieve relevant knowledge from RAGFlow knowledge base.

    Args:
        query: Search query for knowledge retrieval
        top_k: Number of top results to return (default: 3)

    Returns:
        Retrieved knowledge chunks as formatted string
    """
    try:
        from core import rag
        results = rag.search(query, top_k=top_k)
        if not results:
            return "未找到相关知识。"

        formatted = "\n\n".join([f"[知识片段 {i+1}]\n{chunk}" for i, chunk in enumerate(results)])
        logger.info(f"Retrieved {len(results)} chunks for query: {query}")
        return formatted

    except Exception as e:
        logger.error(f"Knowledge retrieval failed: {e}")
        return f"知识检索失败: {str(e)}"


@tool
def generate_ppt_content(teaching_spec: str) -> str:
    """Generate PPT content based on teaching specification.

    Args:
        teaching_spec: JSON string containing teaching specification with fields:
                      topic, audience, key_points, duration, style

    Returns:
        JSON string with generated PPT content or error message
    """
    try:
        from core.teaching_spec import compile_teaching_spec
        from core.llm import generate_slides_json
        from core import rag

        # Parse teaching spec
        spec_dict = json.loads(teaching_spec)
        spec = compile_teaching_spec(spec_dict)
        effective_intent = spec.to_intent()

        # Retrieve knowledge
        topic = effective_intent.get("topic", "")
        key_points = effective_intent.get("key_points", [])
        rag_chunks = []
        for kp in key_points:
            results = rag.search(f"{topic} {kp}", top_k=2)
            rag_chunks.extend(results)

        # Generate slides
        slides_json = generate_slides_json(effective_intent, rag_chunks)

        logger.info(f"Generated PPT with {len(slides_json.get('pages', []))} pages")
        return json.dumps(slides_json, ensure_ascii=False)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid teaching spec JSON: {e}")
        return json.dumps({"error": f"教学规格JSON格式错误: {str(e)}"}, ensure_ascii=False)
    except Exception as e:
        logger.error(f"PPT generation failed: {e}")
        return json.dumps({"error": f"PPT生成失败: {str(e)}"}, ensure_ascii=False)


@tool
def get_preview_url(job_id: str) -> str:
    """Get preview URL for generated PPT.

    Args:
        job_id: Job identifier for the generated PPT

    Returns:
        Preview URL or error message
    """
    try:
        # In production, this would query the job status and return actual URL
        base_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        preview_url = f"{base_url}/preview/{job_id}"
        logger.info(f"Generated preview URL for job {job_id}")
        return f"预览链接: {preview_url}"

    except Exception as e:
        logger.error(f"Preview URL generation failed: {e}")
        return f"预览链接生成失败: {str(e)}"


# ============================================================================
# Teaching Agent
# ============================================================================

class TeachingAgent:
    """LangChain-based teaching agent with conversation and tool capabilities."""

    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize teaching agent.

        Args:
            config: Agent configuration (uses defaults if not provided)
        """
        self.config = config or AgentConfig()
        self._validate_config()

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.config.model_name,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            openai_api_key=self.config.deepseek_api_key,
            openai_api_base=self.config.deepseek_base_url,
            streaming=True,
        )

        # Initialize tools
        self.tools = [
            retrieve_knowledge,
            generate_ppt_content,
            get_preview_url,
        ]

        # Initialize memory store
        self.memory_store = RedisMemoryStore(
            redis_url=self.config.redis_url,
            ttl=self.config.memory_ttl,
        )

        # Create agent
        self.agent = self._create_agent()

        logger.info("TeachingAgent initialized successfully")

    def _validate_config(self) -> None:
        """Validate configuration."""
        if not self.config.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY is required")

    def _create_agent(self) -> Any:
        """Create LangChain agent with tools.

        Returns:
            Configured agent
        """
        # System prompt
        system_message = """你是一位专业的教学设计助手，帮助教师设计课件。

你的职责：
1. 通过自然对话收集教学需求（主题、受众、知识点、课时、风格）
2. 使用工具检索相关知识
3. 生成高质量的PPT课件内容
4. 提供预览链接

对话风格：亲切、专业、简洁。每次只问一个问题或确认一项信息。

可用工具：
- retrieve_knowledge: 检索知识库中的相关内容
- generate_ppt_content: 根据教学规格生成PPT内容
- get_preview_url: 获取PPT预览链接

当收集到完整的教学需求后，使用 generate_ppt_content 工具生成课件。"""

        # Create agent using LangChain 1.0+ API
        # Explicitly use in-process checkpoint/store to avoid any implicit Redis dependency.
        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_message,
            checkpointer=InMemorySaver(),
            store=InMemoryStore(),
        )

        return agent

    async def chat(
        self,
        message: str,
        session_id: str,
    ) -> str:
        """Multi-turn conversation with the agent.

        Args:
            message: User message
            session_id: Unique session identifier for memory persistence

        Returns:
            Agent response

        Raises:
            RuntimeError: If chat fails
        """
        try:
            async with self.memory_store as store:
                # Load conversation history
                messages = await store.load_messages(session_id)

                # Convert to LangChain message format
                chat_history = []
                for msg in messages:
                    if msg["role"] == "user":
                        chat_history.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        chat_history.append(AIMessage(content=msg["content"]))

                # Prepare input with history
                input_data = {
                    "messages": chat_history + [HumanMessage(content=message)]
                }

                # Invoke agent
                result = await self.agent.ainvoke(input_data)

                # Extract response from the agent state
                if isinstance(result, dict) and "messages" in result:
                    # Get the last message from the agent
                    response = result["messages"][-1].content
                else:
                    response = str(result)

                # Save updated history
                messages.append({"role": "user", "content": message})
                messages.append({"role": "assistant", "content": response})
                await store.save_messages(session_id, messages)

                logger.info(f"Chat completed for session {session_id}")
                return response

        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise RuntimeError(f"对话失败: {str(e)}") from e

    async def chat_stream(
        self,
        message: str,
        session_id: str,
    ) -> AsyncGenerator[str, None]:
        """Streaming multi-turn conversation with the agent.

        Args:
            message: User message
            session_id: Unique session identifier for memory persistence

        Yields:
            Response chunks

        Raises:
            RuntimeError: If streaming fails
        """
        try:
            async with self.memory_store as store:
                # Load conversation history
                messages = await store.load_messages(session_id)

                # Convert to LangChain message format
                chat_history = []
                for msg in messages:
                    if msg["role"] == "user":
                        chat_history.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        chat_history.append(AIMessage(content=msg["content"]))

                # Prepare input with history
                input_data = {
                    "messages": chat_history + [HumanMessage(content=message)]
                }

                # Stream agent response
                full_response = ""
                async for event in self.agent.astream_events(input_data, version="v2"):
                    # Extract content from streaming events
                    if event["event"] == "on_chat_model_stream":
                        chunk = event["data"]["chunk"]
                        if hasattr(chunk, "content") and chunk.content:
                            full_response += chunk.content
                            yield chunk.content

                # Save updated history
                messages.append({"role": "user", "content": message})
                messages.append({"role": "assistant", "content": full_response})
                await store.save_messages(session_id, messages)

                logger.info(f"Streaming chat completed for session {session_id}")

        except Exception as e:
            logger.error(f"Streaming chat failed: {e}")
            raise RuntimeError(f"流式对话失败: {str(e)}") from e

    async def generate_ppt(self, teaching_spec: dict[str, Any]) -> dict[str, Any]:
        """Generate PPT directly from teaching specification.

        Args:
            teaching_spec: Teaching specification dictionary

        Returns:
            Generated PPT content

        Raises:
            RuntimeError: If generation fails
        """
        try:
            spec_json = json.dumps(teaching_spec, ensure_ascii=False)
            result_json = generate_ppt_content.invoke({"teaching_spec": spec_json})
            result = json.loads(result_json)

            if "error" in result:
                raise RuntimeError(result["error"])

            logger.info("PPT generated successfully")
            return result

        except Exception as e:
            logger.error(f"PPT generation failed: {e}")
            raise RuntimeError(f"PPT生成失败: {str(e)}") from e

    async def clear_session(self, session_id: str) -> bool:
        """Clear conversation history for a session.

        Args:
            session_id: Session identifier to clear

        Returns:
            True if cleared successfully
        """
        try:
            async with self.memory_store as store:
                result = await store.delete_session(session_id)
                logger.info(f"Session {session_id} cleared: {result}")
                return result

        except Exception as e:
            logger.error(f"Session clear failed: {e}")
            return False


# ============================================================================
# Singleton Instance
# ============================================================================

_agent_instance: Optional[TeachingAgent] = None


def get_teaching_agent(config: Optional[AgentConfig] = None) -> TeachingAgent:
    """Get or create teaching agent singleton.

    Args:
        config: Optional configuration (required on first call)

    Returns:
        TeachingAgent instance

    Raises:
        ValueError: If config not provided on first call
    """
    global _agent_instance

    if _agent_instance is None:
        _agent_instance = TeachingAgent(config)

    return _agent_instance
