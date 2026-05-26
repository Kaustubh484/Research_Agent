"""Tests for the query decomposition tool.

Unit tests mock the Groq LLM to avoid network calls.
Integration tests (marked) hit the real API and require GROQ_API_KEY.
"""

from __future__ import annotations

import json
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from backend.tools.decomposer import decompose_query


def _make_llm_response(sub_questions: List[str]) -> MagicMock:
    """Helper: build a mock LLM response returning a JSON list."""
    mock_response = MagicMock()
    mock_response.content = json.dumps(sub_questions)
    return mock_response


class TestDecomposeQueryUnit:
    """Unit tests — LLM is mocked."""

    @patch("backend.tools.decomposer.ChatGroq")
    def test_returns_three_sub_questions(self, MockChatGroq):
        questions = [
            "How do transformers handle long sequences?",
            "What positional encodings are used in modern LLMs?",
            "How does attention scale with sequence length?",
        ]
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = _make_llm_response(questions)
        MockChatGroq.return_value = mock_instance

        result = decompose_query("How do large language models process long documents?")

        assert isinstance(result, list)
        assert len(result) == 3

    @patch("backend.tools.decomposer.ChatGroq")
    def test_returns_strings(self, MockChatGroq):
        questions = ["Q1", "Q2", "Q3"]
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = _make_llm_response(questions)
        MockChatGroq.return_value = mock_instance

        result = decompose_query("What is quantum entanglement?")
        assert all(isinstance(q, str) for q in result)

    @patch("backend.tools.decomposer.ChatGroq")
    def test_handles_markdown_code_fence(self, MockChatGroq):
        """LLM sometimes wraps JSON in ```json ... ``` blocks."""
        raw_with_fence = '```json\n["Q1", "Q2", "Q3"]\n```'
        mock_response = MagicMock()
        mock_response.content = raw_with_fence
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = mock_response
        MockChatGroq.return_value = mock_instance

        result = decompose_query("Any question")
        assert len(result) == 3

    @patch("backend.tools.decomposer.ChatGroq")
    def test_raises_on_wrong_count(self, MockChatGroq):
        """Should raise ValueError if the LLM returns != 3 questions."""
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = _make_llm_response(["Only one question"])
        MockChatGroq.return_value = mock_instance

        with pytest.raises(ValueError, match="exactly 3"):
            decompose_query("Some question")

    @patch("backend.tools.decomposer.ChatGroq")
    def test_raises_on_invalid_json(self, MockChatGroq):
        """Should raise if LLM returns unparseable output."""
        mock_response = MagicMock()
        mock_response.content = "Not valid JSON at all"
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = mock_response
        MockChatGroq.return_value = mock_instance

        with pytest.raises(Exception):
            decompose_query("Some question")

    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        with pytest.raises(EnvironmentError, match="GROQ_API_KEY"):
            decompose_query("Any question")

    @patch("backend.tools.decomposer.ChatGroq")
    def test_llm_called_with_question(self, MockChatGroq):
        """The original question should appear in the prompt sent to the LLM."""
        question = "What is the role of attention in transformers?"
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = _make_llm_response(["A", "B", "C"])
        MockChatGroq.return_value = mock_instance

        decompose_query(question)

        call_args = mock_instance.invoke.call_args
        messages = call_args[0][0]
        combined = " ".join(m.content for m in messages)
        assert question in combined


@pytest.mark.integration
class TestDecomposeQueryIntegration:
    """Integration tests — require real GROQ_API_KEY in environment."""

    def test_real_api_call(self):
        result = decompose_query("How does RLHF improve language model alignment?")
        assert len(result) == 3
        assert all(len(q) > 10 for q in result), "Sub-questions should be non-trivial"
