"""
Test script for monitoring module functionality.
"""

import asyncio
import sys
import os

# Keep pytest capture stable: only re-wrap stdio in standalone script mode.
if __name__ == "__main__" and sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.monitoring import (
    error_tracker,
    performance_monitor,
    health_check,
    monitor_performance,
    get_system_metrics
)


def test_error_tracking():
    """Test error tracking functionality."""
    print("Testing error tracking...")

    # Record some test errors
    error_tracker.record_error(
        endpoint="/api/test",
        error_type="ValueError",
        error_message="Test error message",
        stack_trace="Test stack trace"
    )

    error_tracker.record_error(
        endpoint="/api/test",
        error_type="KeyError",
        error_message="Another test error",
        stack_trace="Another stack trace"
    )

    # Get errors
    errors = error_tracker.get_errors(limit=10)
    print(f"  [OK] Recorded {len(errors)} errors")

    # Get summary
    summary = error_tracker.get_error_summary()
    print(f"  [OK] Error summary: {summary['total_errors']} total errors")

    assert summary["total_errors"] >= 2


def test_performance_monitoring():
    """Test performance monitoring functionality."""
    print("Testing performance monitoring...")

    # Record some test requests
    performance_monitor.record_request("/api/test", 0.123, 200)
    performance_monitor.record_request("/api/test", 0.456, 200)
    performance_monitor.record_request("/api/test", 0.789, 500)

    # Get stats
    stats = performance_monitor.get_stats("/api/test")
    print(f"  [OK] Recorded {stats['count']} requests")
    print(f"  [OK] Average duration: {stats['avg_duration']:.3f}s")
    print(f"  [OK] P95: {stats['p95']:.3f}s")

    assert stats["count"] >= 3


def test_health_check():
    """Test health check functionality."""
    print("Testing health check...")

    health = asyncio.run(health_check())
    print(f"  [OK] Status: {health['status']}")
    print(f"  [OK] Memory usage: {health['system']['memory']['percent']:.1f}%")
    print(f"  [OK] CPU usage: {health['system']['cpu']['percent']:.1f}%")
    assert health["status"] in {"healthy", "degraded"}


def test_system_metrics():
    """Test system metrics collection."""
    print("Testing system metrics...")

    metrics = get_system_metrics()
    print(f"  [OK] Memory: {metrics['memory']['used_mb']:.0f}MB / {metrics['memory']['total_mb']:.0f}MB")
    print(f"  [OK] CPU: {metrics['cpu']['percent']:.1f}%")
    print(f"  [OK] CPU cores: {metrics['cpu']['count']}")

    assert metrics["cpu"]["count"] >= 1


@monitor_performance("test_operation")
async def _exercise_decorator():
    """Test performance monitoring decorator."""
    await asyncio.sleep(0.1)
    return "success"


def test_performance_decorator():
    """Test the performance monitoring decorator."""
    print("Testing performance decorator...")

    result = asyncio.run(_exercise_decorator())
    print(f"  [OK] Decorator test: {result}")
    assert result == "success"


async def main():
    """Run all tests."""
    print("=" * 50)
    print("FastPPT Monitoring Module Tests")
    print("=" * 50)
    print()

    tests = [
        ("Error Tracking", test_error_tracking),
        ("Performance Monitoring", test_performance_monitoring),
        ("Health Check", test_health_check),
        ("System Metrics", test_system_metrics),
        ("Performance Decorator", test_performance_decorator),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()

            if result:
                passed += 1
                print(f"[PASS] {name}\n")
            else:
                failed += 1
                print(f"[FAIL] {name}\n")
        except Exception as e:
            failed += 1
            print(f"[FAIL] {name} - Error: {e}\n")

    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
