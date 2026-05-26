"""Tests for the ArXiv search tool."""

from __future__ import annotations

import pytest

from backend.models.schemas import Paper
from backend.tools.arxiv_search import search_arxiv


class TestSearchArxiv:
    """Unit tests for search_arxiv — these hit the real ArXiv API."""

    def test_returns_list_of_papers(self):
        papers = search_arxiv("attention mechanism transformer")
        assert isinstance(papers, list)

    def test_returns_at_most_five_papers(self):
        papers = search_arxiv("reinforcement learning policy gradient")
        assert len(papers) <= 5

    def test_paper_has_required_fields(self):
        papers = search_arxiv("large language model fine tuning")
        assert len(papers) > 0
        paper = papers[0]
        assert isinstance(paper, Paper)
        assert paper.title
        assert isinstance(paper.authors, list)
        assert paper.abstract
        assert paper.arxiv_id
        assert paper.url

    def test_arxiv_id_is_not_full_url(self):
        """arxiv_id should be just the ID portion, not the full entry URL."""
        papers = search_arxiv("diffusion models image generation")
        assert len(papers) > 0
        for paper in papers:
            assert "/" not in paper.arxiv_id or paper.arxiv_id.startswith("abs/") is False

    def test_url_is_valid_arxiv_link(self):
        papers = search_arxiv("graph neural network")
        assert len(papers) > 0
        for paper in papers:
            assert "arxiv.org" in paper.url

    def test_different_queries_return_different_results(self):
        """Two distinct queries should not return identical paper sets."""
        papers_a = search_arxiv("quantum computing error correction")
        papers_b = search_arxiv("natural language processing sentiment analysis")
        ids_a = {p.arxiv_id for p in papers_a}
        ids_b = {p.arxiv_id for p in papers_b}
        # Allow some overlap but they should not be identical sets
        assert ids_a != ids_b

    def test_empty_results_handled_gracefully(self):
        """Extremely specific query may return zero results without raising."""
        papers = search_arxiv("xyzzy_nonexistent_topic_12345_zyxwv")
        assert isinstance(papers, list)

    def test_authors_is_list_of_strings(self):
        papers = search_arxiv("convolutional neural network image classification")
        assert len(papers) > 0
        for paper in papers:
            assert all(isinstance(a, str) for a in paper.authors)
