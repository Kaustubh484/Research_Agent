"""Tests for the text chunking logic in the retriever tool."""

from __future__ import annotations

from typing import List

import pytest

# Import internal helpers directly for white-box testing
from backend.tools.retriever import _chunk_text, _tokenize


class TestTokenize:
    def test_splits_on_whitespace(self):
        tokens = _tokenize("hello world foo bar")
        assert tokens == ["hello", "world", "foo", "bar"]

    def test_handles_multiple_spaces(self):
        tokens = _tokenize("  hello   world  ")
        assert "hello" in tokens and "world" in tokens

    def test_empty_string_returns_empty(self):
        tokens = _tokenize("")
        assert tokens == [] or tokens == [""]  # split behaviour on empty

    def test_single_word(self):
        tokens = _tokenize("neuroscience")
        assert "neuroscience" in tokens


class TestChunkText:
    def _word_sequence(self, n: int) -> str:
        """Generate a reproducible string of n space-separated words."""
        return " ".join(f"word{i}" for i in range(n))

    def test_short_text_is_single_chunk(self):
        text = self._word_sequence(100)
        chunks = _chunk_text(text, chunk_size=500, overlap=50)
        assert len(chunks) == 1

    def test_long_text_produces_multiple_chunks(self):
        text = self._word_sequence(1200)
        chunks = _chunk_text(text, chunk_size=500, overlap=50)
        assert len(chunks) > 1

    def test_chunks_are_non_empty(self):
        text = self._word_sequence(800)
        chunks = _chunk_text(text)
        assert all(len(c) > 0 for c in chunks)

    def test_overlap_shares_tokens(self):
        """Consecutive chunks should share `overlap` tokens at the boundary."""
        text = self._word_sequence(600)
        chunks = _chunk_text(text, chunk_size=100, overlap=20)
        assert len(chunks) >= 2

        tokens_0 = _tokenize(chunks[0])
        tokens_1 = _tokenize(chunks[1])

        # The tail of chunk 0 should appear at the head of chunk 1
        tail = tokens_0[-20:]
        head = tokens_1[:20]
        assert tail == head, f"Expected overlap: {tail} != {head}"

    def test_custom_chunk_size(self):
        text = self._word_sequence(500)
        chunks = _chunk_text(text, chunk_size=100, overlap=0)
        # With no overlap and chunk_size=100, 500 words → exactly 5 chunks
        assert len(chunks) == 5

    def test_chunk_size_respected(self):
        text = self._word_sequence(1000)
        chunk_size = 200
        chunks = _chunk_text(text, chunk_size=chunk_size, overlap=0)
        for chunk in chunks[:-1]:  # Last chunk can be shorter
            tokens = _tokenize(chunk)
            assert len(tokens) == chunk_size

    def test_no_content_loss(self):
        """All words in the original text should appear in at least one chunk."""
        text = self._word_sequence(300)
        chunks = _chunk_text(text, chunk_size=100, overlap=10)
        combined_tokens = set()
        for c in chunks:
            combined_tokens.update(_tokenize(c))
        original_tokens = set(_tokenize(text))
        assert original_tokens.issubset(combined_tokens)

    def test_zero_overlap(self):
        text = self._word_sequence(400)
        chunks = _chunk_text(text, chunk_size=100, overlap=0)
        # No repeated tokens between adjacent chunks
        for i in range(len(chunks) - 1):
            t0 = set(_tokenize(chunks[i]))
            t1 = set(_tokenize(chunks[i + 1]))
            assert len(t0 & t1) == 0
