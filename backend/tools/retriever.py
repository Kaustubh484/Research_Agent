"""Tool 3: Retrieve and rank relevant text chunks from papers using FAISS + embeddings."""

from __future__ import annotations

import re
from typing import List

import numpy as np
import requests
from bs4 import BeautifulSoup

from backend.models.schemas import Chunk, Paper

# Lazy imports for heavy ML deps — loaded once on first call
_embedder = None
_faiss = None

AR5IV_BASE = "https://ar5iv.org/html/{arxiv_id}"
CHUNK_TOKENS = 500
CHUNK_OVERLAP = 50
TOP_K = 5
REQUEST_TIMEOUT = 10


def _get_embedder():
    """Singleton loader for SentenceTransformer to avoid repeated init."""
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def _get_faiss():
    global _faiss
    if _faiss is None:
        import faiss as f
        _faiss = f
    return _faiss


def _fetch_paper_text(paper: Paper) -> str:
    """Fetch intro + conclusion from ar5iv HTML; fall back to abstract."""
    url = AR5IV_BASE.format(arxiv_id=paper.arxiv_id)
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        sections: List[str] = []
        for heading in soup.find_all(["h1", "h2", "h3"]):
            title_text = heading.get_text(strip=True).lower()
            if any(kw in title_text for kw in ("introduction", "conclusion", "abstract")):
                # Gather paragraph siblings until the next heading
                sibling = heading.find_next_sibling()
                while sibling and sibling.name not in ("h1", "h2", "h3"):
                    if sibling.name == "p":
                        sections.append(sibling.get_text(separator=" ", strip=True))
                    sibling = sibling.find_next_sibling()

        text = " ".join(sections).strip()
        if len(text) > 200:
            return text
    except Exception:
        pass

    return paper.abstract


def _tokenize(text: str) -> List[str]:
    """Naive whitespace tokenizer producing word-level tokens."""
    return re.split(r"\s+", text.strip())


def _chunk_text(text: str, chunk_size: int = CHUNK_TOKENS, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping token-window chunks."""
    tokens = _tokenize(text)
    chunks: List[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunks.append(" ".join(tokens[start:end]))
        if end == len(tokens):
            break
        start += chunk_size - overlap
    return chunks


def retrieve_chunks(papers: List[Paper], question: str) -> List[Chunk]:
    """Embed paper text chunks and return the TOP_K most relevant to the question.

    Args:
        papers: List of Paper objects to process.
        question: The user's research question used for relevance ranking.

    Returns:
        Up to TOP_K Chunk objects with source attribution.
    """
    embedder = _get_embedder()
    faiss = _get_faiss()

    all_chunks: List[Chunk] = []
    all_texts: List[str] = []

    for paper in papers:
        raw_text = _fetch_paper_text(paper)
        pieces = _chunk_text(raw_text)
        for piece in pieces:
            all_chunks.append(
                Chunk(
                    text=piece,
                    source_title=paper.title,
                    source_id=paper.arxiv_id,
                    source_url=paper.url,
                )
            )
            all_texts.append(piece)

    if not all_texts:
        return []

    # Embed all chunks and the query
    all_embeddings = embedder.encode(all_texts, convert_to_numpy=True, normalize_embeddings=True)
    query_embedding = embedder.encode([question], convert_to_numpy=True, normalize_embeddings=True)

    dim = all_embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner product on normalized vecs = cosine similarity
    index.add(all_embeddings.astype(np.float32))

    k = min(TOP_K, len(all_texts))
    _, indices = index.search(query_embedding.astype(np.float32), k)

    return [all_chunks[i] for i in indices[0] if i < len(all_chunks)]
