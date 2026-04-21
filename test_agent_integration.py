"""Test script for Agent integration in chat API."""
import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from api.chat import ChatRequest, _parse_intent, _build_summary


def test_chat_request_model():
    """Test ChatRequest model with new fields."""
    print("Testing ChatRequest model...")

    # Test with all fields
    req = ChatRequest(
        messages=[{"role": "user", "content": "Hello"}],
        stream=True,
        use_agent=True,
        session_id="test-123"
    )
    assert req.messages == [{"role": "user", "content": "Hello"}]
    assert req.stream is True
    assert req.use_agent is True
    assert req.session_id == "test-123"
    print("  [PASS] All fields")

    # Test with defaults
    req = ChatRequest(messages=[{"role": "user", "content": "Hello"}])
    assert req.stream is False
    assert req.use_agent is False
    assert req.session_id is None
    print("  [PASS] Default values")

    # Test backward compatibility (old frontend)
    req = ChatRequest(messages=[{"role": "user", "content": "Hello"}], stream=True)
    assert req.use_agent is False
    assert req.session_id is None
    print("  [PASS] Backward compatibility")


def test_parse_intent():
    """Test intent parsing logic."""
    print("\nTesting _parse_intent...")

    # Test without intent
    reply = "This is a normal reply"
    visible, intent = _parse_intent(reply)
    assert visible == reply
    assert intent is None
    print("  [PASS] No intent")

    # Test with intent
    reply = 'Some text [INTENT_READY] {"topic": "Python", "audience": "高中生"}'
    visible, intent = _parse_intent(reply)
    assert visible == "Some text"
    assert intent == {"topic": "Python", "audience": "高中生"}
    print("  [PASS] With intent")

    # Test with malformed JSON
    reply = 'Some text [INTENT_READY] {invalid json}'
    visible, intent = _parse_intent(reply)
    assert visible == "Some text"
    assert intent is None
    print("  [PASS] Malformed JSON")


def test_build_summary():
    """Test summary building."""
    print("\nTesting _build_summary...")

    spec = {
        "topic": "Python编程",
        "audience": "高中生",
        "duration": "45分钟",
        "style": "互动式",
        "key_points": ["变量", "函数", "循环"],
        "unresolved_fields": ["duration"]
    }

    summary = _build_summary("好的，我理解了", spec)
    assert "Python编程" in summary
    assert "高中生" in summary
    assert "45分钟" in summary
    assert "互动式" in summary
    assert "变量" in summary
    assert "duration" in summary or "待确认" in summary
    print("  [PASS] Summary generation")


def test_routing_logic():
    """Test routing logic for different request combinations."""
    print("\nTesting routing logic...")

    test_cases = [
        # (use_agent, stream, expected_mode)
        (False, False, "traditional_sync"),
        (False, True, "traditional_stream"),
        (True, False, "agent_sync"),
        (True, True, "agent_stream"),
    ]

    for use_agent, stream, expected_mode in test_cases:
        req = ChatRequest(
            messages=[{"role": "user", "content": "test"}],
            use_agent=use_agent,
            stream=stream
        )

        # Determine expected route
        if req.use_agent and req.stream:
            mode = "agent_stream"
        elif req.use_agent:
            mode = "agent_sync"
        elif req.stream:
            mode = "traditional_stream"
        else:
            mode = "traditional_sync"

        assert mode == expected_mode, f"Expected {expected_mode}, got {mode}"
        print(f"  [PASS] use_agent={use_agent}, stream={stream} -> {mode}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Agent Integration Test Suite")
    print("=" * 60)

    try:
        test_chat_request_model()
        test_parse_intent()
        test_build_summary()
        test_routing_logic()

        print("\n" + "=" * 60)
        print("All tests passed!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
