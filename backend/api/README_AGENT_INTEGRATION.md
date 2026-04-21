# Chat API - LangChain Agent Integration

## Overview

The chat API now supports both traditional LLM calls and LangChain Agent mode with full backward compatibility.

## API Changes

### Request Parameters

```json
{
  "messages": [{"role": "user", "content": "..."}],
  "stream": false,           // Enable SSE streaming
  "use_agent": false,        // Enable LangChain Agent mode (NEW)
  "session_id": "optional"   // Session ID for conversation memory (NEW)
}
```

### Response Format

All responses now include:
- `session_id`: Session identifier for multi-turn conversations
- `agent_mode`: Boolean indicating if agent was used (only in agent mode)

## Usage Examples

### 1. Traditional Mode (Backward Compatible)

```python
# Non-streaming
response = requests.post("/api/chat", json={
    "messages": [{"role": "user", "content": "我想做一个关于Python的课件"}],
    "stream": False
})
# Returns: {"reply": "...", "intent_ready": false, "intent": null}
```

### 2. Traditional Mode with Streaming

```python
# Streaming
response = requests.post("/api/chat", json={
    "messages": [{"role": "user", "content": "我想做一个关于Python的课件"}],
    "stream": True
})
# Returns: SSE stream with chunks
```

### 3. Agent Mode (New)

```python
# Non-streaming with agent
response = requests.post("/api/chat", json={
    "messages": [{"role": "user", "content": "我想做一个关于Python的课件"}],
    "use_agent": True,
    "session_id": "user-123"  # Optional, auto-generated if not provided
})
# Returns: {"reply": "...", "session_id": "user-123", "agent_mode": true, ...}
```

### 4. Agent Mode with Streaming

```python
# Streaming with agent
response = requests.post("/api/chat", json={
    "messages": [{"role": "user", "content": "我想做一个关于Python的课件"}],
    "use_agent": True,
    "stream": True,
    "session_id": "user-123"
})
# Returns: SSE stream with chunks and session_id
```

## Features

### Agent Mode Benefits

1. **Multi-turn Conversation**: Maintains conversation history via Redis
2. **Tool Integration**: Automatic tool calling (RAG retrieval, PPT generation)
3. **Session Management**: Persistent memory across requests
4. **Comprehensive Logging**: Detailed logs for debugging

### Logging

Agent mode includes detailed logging:
- Session start/completion
- Tool invocations
- Error tracking

Example logs:
```
INFO: Agent chat started - session_id: abc123, message: 我想做一个关于Python的课件...
INFO: Agent chat completed - session_id: abc123
```

### Error Handling

Both modes provide consistent error responses:
```json
{
  "error": "Agent 调用失败: connection timeout"
}
```

## Migration Guide

### Frontend Changes Required

No breaking changes. Existing frontend code works as-is.

To enable agent mode:
```javascript
// Add optional parameters
const response = await fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({
    messages: [...],
    use_agent: true,        // Enable agent
    session_id: sessionId   // Optional
  })
});
```

### Session Management

```javascript
// Store session_id from first response
const { session_id } = await response.json();

// Use in subsequent requests
const nextResponse = await fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({
    messages: [...],
    use_agent: true,
    session_id: session_id  // Reuse session
  })
});
```

## Configuration

Agent mode requires:
- `DEEPSEEK_API_KEY`: DeepSeek API key
- `REDIS_URL`: Redis connection URL (default: redis://localhost:6379/0)

## Testing

### Test Traditional Mode
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}], "stream": false}'
```

### Test Agent Mode
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}], "use_agent": true}'
```

### Test Agent Streaming
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}], "use_agent": true, "stream": true}'
```

## Architecture

```
┌─────────────────┐
│  POST /api/chat │
└────────┬────────┘
         │
         ├─ use_agent=false ──► Traditional LLM (core.llm)
         │                      └─ SSE streaming support
         │
         └─ use_agent=true ───► LangChain Agent
                                ├─ Session management (Redis)
                                ├─ Tool integration
                                ├─ Conversation memory
                                └─ SSE streaming support
```

## Notes

- Session TTL: 24 hours (configurable via `memory_ttl`)
- Agent singleton: Shared across requests for efficiency
- Backward compatible: All existing frontend code works unchanged
- Tool calls are logged automatically in agent mode
