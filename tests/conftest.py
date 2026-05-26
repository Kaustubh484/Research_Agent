"""Shared pytest fixtures and configuration."""

import os

import pytest


@pytest.fixture(autouse=True)
def set_dummy_groq_key(monkeypatch):
    """Provide a dummy GROQ_API_KEY so imports don't fail during unit tests.

    Individual tests that actually call the Groq API should use a real key
    via environment variable and mark themselves with @pytest.mark.integration.
    """
    if not os.getenv("GROQ_API_KEY"):
        monkeypatch.setenv("GROQ_API_KEY", "test-dummy-key")
