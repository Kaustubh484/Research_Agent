"""Tests for the fact verification tool.

Unit tests mock the Groq LLM; integration tests require GROQ_API_KEY.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.models.schemas import Chunk
from backend.tools.verifier import verify_facts


SAMPLE_CHUNKS = [
    Chunk(
        text="Transformer models use self-attention to relate positions in a sequence.",
        source_title="Attention Is All You Need",
        source_id="1706.03762",
        source_url="https://arxiv.org/abs/1706.03762",
    ),
    Chunk(
        text="RLHF aligns language models with human preferences through reward modeling.",
        source_title="Training Language Models to Follow Instructions",
        source_id="2203.02155",
        source_url="https://arxiv.org/abs/2203.02155",
    ),
]

SAMPLE_REPORT = """## Overview
Transformers use attention mechanisms [1]. RLHF is used for alignment [2].

## Key Findings
- Self-attention relates all sequence positions [1] [HIGH]
- Reward models guide policy training [2]
"""


def _make_mock_llm(response_text: str):
    mock_response = MagicMock()
    mock_response.content = response_text
    mock_instance = MagicMock()
    mock_instance.invoke.return_value = mock_response
    return mock_instance


class TestVerifyFactsUnit:
    """Unit tests with mocked LLM."""

    @patch("backend.tools.verifier.ChatGroq")
    def test_returns_string(self, MockChatGroq):
        annotated = "## Overview\nTransformers use attention [1] [HIGH]\n"
        MockChatGroq.return_value = _make_mock_llm(annotated)

        result = verify_facts(SAMPLE_REPORT, SAMPLE_CHUNKS)
        assert isinstance(result, str)

    @patch("backend.tools.verifier.ChatGroq")
    def test_result_is_non_empty(self, MockChatGroq):
        annotated = "Some annotated report content [HIGH]"
        MockChatGroq.return_value = _make_mock_llm(annotated)

        result = verify_facts(SAMPLE_REPORT, SAMPLE_CHUNKS)
        assert len(result) > 0

    @patch("backend.tools.verifier.ChatGroq")
    def test_confidence_labels_present_in_output(self, MockChatGroq):
        annotated = (
            "Transformers use self-attention [1] [HIGH]. "
            "RLHF is applied [2] [MEDIUM]. "
            "Speculative claim [LOW]."
        )
        MockChatGroq.return_value = _make_mock_llm(annotated)

        result = verify_facts(SAMPLE_REPORT, SAMPLE_CHUNKS)
        assert "[HIGH]" in result or "[MEDIUM]" in result or "[LOW]" in result

    @patch("backend.tools.verifier.ChatGroq")
    def test_original_content_preserved(self, MockChatGroq):
        """The verifier should not drop sections from the original report."""
        annotated = SAMPLE_REPORT + "\n[HIGH] [MEDIUM]"
        MockChatGroq.return_value = _make_mock_llm(annotated)

        result = verify_facts(SAMPLE_REPORT, SAMPLE_CHUNKS)
        assert "Overview" in result
        assert "Key Findings" in result

    @patch("backend.tools.verifier.ChatGroq")
    def test_source_context_passed_to_llm(self, MockChatGroq):
        """Chunk source titles must appear in the prompt to the LLM."""
        mock_instance = _make_mock_llm("verified [HIGH]")
        MockChatGroq.return_value = mock_instance

        verify_facts(SAMPLE_REPORT, SAMPLE_CHUNKS)

        call_args = mock_instance.invoke.call_args
        messages = call_args[0][0]
        combined = " ".join(m.content for m in messages)
        assert "Attention Is All You Need" in combined

    @patch("backend.tools.verifier.ChatGroq")
    def test_report_passed_to_llm(self, MockChatGroq):
        mock_instance = _make_mock_llm("verified")
        MockChatGroq.return_value = mock_instance

        verify_facts(SAMPLE_REPORT, SAMPLE_CHUNKS)

        call_args = mock_instance.invoke.call_args
        messages = call_args[0][0]
        combined = " ".join(m.content for m in messages)
        assert "Overview" in combined  # Part of SAMPLE_REPORT

    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        with pytest.raises(EnvironmentError, match="GROQ_API_KEY"):
            verify_facts(SAMPLE_REPORT, SAMPLE_CHUNKS)

    @patch("backend.tools.verifier.ChatGroq")
    def test_empty_chunks_handled(self, MockChatGroq):
        MockChatGroq.return_value = _make_mock_llm("report [LOW]")
        result = verify_facts(SAMPLE_REPORT, [])
        assert isinstance(result, str)

    @patch("backend.tools.verifier.ChatGroq")
    def test_empty_report_handled(self, MockChatGroq):
        MockChatGroq.return_value = _make_mock_llm("")
        result = verify_facts("", SAMPLE_CHUNKS)
        assert isinstance(result, str)


@pytest.mark.integration
class TestVerifyFactsIntegration:
    """Integration tests — require real GROQ_API_KEY."""

    def test_real_api_annotates_report(self):
        result = verify_facts(SAMPLE_REPORT, SAMPLE_CHUNKS)
        assert len(result) > 50
        labels = ["[HIGH]", "[MEDIUM]", "[LOW]"]
        assert any(label in result for label in labels)
