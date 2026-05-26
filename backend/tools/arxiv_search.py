"""Tool 2: Search ArXiv for papers matching a sub-question."""

from __future__ import annotations

from typing import List

import arxiv

from backend.models.schemas import Paper


MAX_RESULTS = 5
SORT_BY = arxiv.SortCriterion.Relevance


def search_arxiv(sub_question: str) -> List[Paper]:
    """Search ArXiv and return the top 5 most relevant papers.

    Args:
        sub_question: A focused search query string.

    Returns:
        A list of up to 5 Paper objects with metadata.
    """
    client = arxiv.Client()
    search = arxiv.Search(
        query=sub_question,
        max_results=MAX_RESULTS,
        sort_by=SORT_BY,
    )

    papers: List[Paper] = []
    for result in client.results(search):
        arxiv_id = result.entry_id.split("/")[-1]
        papers.append(
            Paper(
                title=result.title.strip(),
                authors=[a.name for a in result.authors],
                abstract=result.summary.strip(),
                arxiv_id=arxiv_id,
                url=result.entry_id,
            )
        )

    return papers
