"""Tool 4: Synthesize a structured markdown research report from retrieved chunks."""

from __future__ import annotations

from typing import List

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from backend.models.schemas import Chunk


SYSTEM_PROMPT = """You are an expert academic research writer. Given a set of source
chunks from academic papers and a research question, write a comprehensive, structured
markdown report. The report MUST contain these sections (use ## headings):

## Overview
## Key Findings
## Methodology
## Open Challenges
## Recommended Reading
## References

Rules:
- Every claim must include an inline citation like [1], [2], etc.
- The References section must list all cited papers with their ArXiv IDs.
- Be thorough but concise. Use bullet points where appropriate.
- Do NOT invent facts — base everything on the provided source chunks."""


def _build_context(chunks: List[Chunk]) -> str:
    """Format chunks into a numbered source list for the prompt."""
    lines: List[str] = []
    for i, chunk in enumerate(chunks, start=1):
        lines.append(
            f"[{i}] SOURCE: {chunk.source_title} (ArXiv: {chunk.source_id})\n"
            f"    URL: {chunk.source_url}\n"
            f"    TEXT: {chunk.text}\n"
        )
    return "\n".join(lines)


def synthesize_report(chunks: List[Chunk], question: str) -> str:
    """Use Ollama to synthesize a structured, cited research report.

    Args:
        chunks: Retrieved and ranked text chunks with source metadata.
        question: The original research question.

    Returns:
        A markdown-formatted research report string.

    """
    llm = ChatOllama(model="llama3.2", temperature=0.3)

    context = _build_context(chunks)
    user_message = (
        f"Research Question: {question}\n\n"
        f"Source Chunks:\n{context}\n\n"
        "Write the full structured markdown research report now."
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    response = llm.invoke(messages)
    return response.content.strip()
