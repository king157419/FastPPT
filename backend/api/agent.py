"""FastAPI routes for LangChain Teaching Agent.

This module provides REST API endpoints for the teaching agent:
- POST /api/agent/chat - Synchronous chat
- POST /api/agent/chat/stream - Streaming chat (SSE)
- POST /api/agent/generate - Generate PPT
- DELETE /api/agent/session/{session_id} - Clear session
"""

from __future__ import annotations

import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="User message")
    session_id: str = Field(..., description="Unique session identifier")


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session identifier")


class GenerateRequest(BaseModel):
    """PPT generation request model."""
    teaching_spec: dict = Field(
        ...,
        description="Teaching specification with topic, audience, key_points, duration, style"
    )


class GenerateResponse(BaseModel):
    """PPT generation response model."""
    slides_json: dict = Field(..., description="Generated PPT content")
    page_count: int = Field(..., description="Number of pages")


class ClearSessionResponse(BaseModel):
    """Clear session response model."""
    success: bool = Field(..., description="Whether session was cleared")
    session_id: str = Field(..., description="Session identifier")


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/agent/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """Synchronous chat endpoint.

    Args:
        req: Chat request with message and session_id

    Returns:
        Chat response with agent's reply

    Raises:
        HTTPException: If chat fails
    """
    try:
        from integrations.langchain_agent import get_teaching_agent

        agent = get_teaching_agent()
        response = await agent.chat(req.message, req.session_id)

        logger.info(f"Chat completed for session {req.session_id}")
        return ChatResponse(response=response, session_id=req.session_id)

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/agent/chat/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    """Streaming chat endpoint using Server-Sent Events (SSE).

    Args:
        req: Chat request with message and session_id

    Returns:
        StreamingResponse with SSE events

    Raises:
        HTTPException: If streaming fails
    """
    try:
        from integrations.langchain_agent import get_teaching_agent

        agent = get_teaching_agent()

        async def event_generator() -> AsyncGenerator[str, None]:
            """Generate SSE events from agent stream."""
            try:
                async for chunk in agent.chat_stream(req.message, req.session_id):
                    # Format as SSE event
                    yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"

                # Send completion event
                yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

                logger.info(f"Streaming completed for session {req.session_id}")

            except Exception as e:
                logger.error(f"Streaming error: {e}")
                error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
                yield f"data: {error_data}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
                "Connection": "keep-alive",
            },
        )

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/agent/generate", response_model=GenerateResponse)
async def generate(req: GenerateRequest) -> GenerateResponse:
    """Generate PPT content from teaching specification.

    Args:
        req: Generation request with teaching_spec

    Returns:
        Generated PPT content with page count

    Raises:
        HTTPException: If generation fails
    """
    try:
        from integrations.langchain_agent import get_teaching_agent

        agent = get_teaching_agent()
        result = await agent.generate_ppt(req.teaching_spec)

        page_count = len(result.get("pages", []))
        logger.info(f"Generated PPT with {page_count} pages")

        return GenerateResponse(slides_json=result, page_count=page_count)

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/agent/session/{session_id}", response_model=ClearSessionResponse)
async def clear_session(session_id: str) -> ClearSessionResponse:
    """Clear conversation history for a session.

    Args:
        session_id: Session identifier to clear

    Returns:
        Success status

    Raises:
        HTTPException: If clearing fails
    """
    try:
        from integrations.langchain_agent import get_teaching_agent

        agent = get_teaching_agent()
        success = await agent.clear_session(session_id)

        logger.info(f"Session {session_id} cleared: {success}")
        return ClearSessionResponse(success=success, session_id=session_id)

    except Exception as e:
        logger.error(f"Session clear failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agent/health")
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        Health status
    """
    try:
        from integrations.langchain_agent import get_teaching_agent

        # Try to get agent instance
        agent = get_teaching_agent()

        return {
            "status": "healthy",
            "agent": "initialized",
            "model": agent.config.model_name,
        }

    except ValueError as e:
        return {
            "status": "unhealthy",
            "error": "Configuration error",
            "detail": str(e),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": "Initialization error",
            "detail": str(e),
        }
