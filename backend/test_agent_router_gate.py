"""Regression tests for agent router gating via ENABLE_AGENT."""
from __future__ import annotations

import importlib

import main as backend_main


def _has_agent_routes(module) -> bool:
    return any(str(route.path).startswith("/api/agent") for route in module.app.routes)


def test_agent_router_not_registered_when_disabled(monkeypatch):
    monkeypatch.setenv("ENABLE_AGENT", "false")
    module = importlib.reload(backend_main)
    assert _has_agent_routes(module) is False


def test_agent_router_registered_when_enabled(monkeypatch):
    monkeypatch.setenv("ENABLE_AGENT", "true")
    module = importlib.reload(backend_main)
    assert _has_agent_routes(module) is True
