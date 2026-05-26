"""Tool 5: Verify report claims against source chunks and add confidence labels."""

from __future__ import annotations

import os
from typing import List

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from backend.models.schemas import Chunk


SYSTEM_PROMPT = """You are a rigorous fact-checker for academic research reports.
You will receive a markdown research report and a set of source chunks.

Your task:
1. Review each factual claim in the report.
2. After each claim (sentence or bullet point containing a citation like [1]), add a
   confidence label on the SAME line: [HIGH], [MEDIUM], or [LOW].
   - [HIGH]: claim is directly supported verbatim or paraphrase by a source chunk.
   - [MEDIUM]: claim is plausibly inferred from the sources but not explicitly stated.
   - [LOW]: claim is weakly supported, speculative, or not found in source chunks.
3. Return the complete modified report with confidence labels added.
4. Do NOT remove or modify any existing content — only append the confidence labels.
5. Preserve all markdown formatting exactly."""


def _build_source_context(chunks: List[Chunk]) -> str:
    lines: List[str] = []
    for i, chunk in enumerate(chunks, start=1):
        lines.append(f"[{i}] {chunk.source_title}: {chunk.text[:500]}")
    return "\n\n".join(lines)


def verify_facts(report: str, chunks: List[Chunk]) -> str:
    """Verify report claims and annotate each with a confidence label.

    Args:
        report: The synthesized markdown report to verify.
        chunks: Source chunks used as ground truth for verification.

    Returns:
        The annotated report with [HIGH], [MEDIUM], or [LOW] labels appended
        after each cited claim.

    Raises:
        EnvironmentError: If GROQ_API_KEY is not set.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY environment variable is not set.")

    llm = ChatGroq(
        model="llama-3.1-70b-versatile",
        temperature=0.1,
        max_tokens=4096,
        groq_api_key=api_key,
    )

    source_context = _build_source_context(chunks)
    user_message = (
        f"SOURCE CHUNKS:\n{source_context}\n\n"
        f"REPORT TO VERIFY:\n{report}\n\n"
        "Add confidence labels [HIGH], [MEDIUM], or [LOW] after each factual claim. "
        "Return the complete annotated report."
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    response = llm.invoke(messages)
    return response.content.strip()
