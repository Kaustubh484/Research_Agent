"""Tool 1: Decompose a research question into 3 focused ArXiv sub-questions."""

from __future__ import annotations

import json
import os
from typing import List

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


SYSTEM_PROMPT = """You are a research assistant specializing in academic literature search.
Given a broad research question, decompose it into exactly 3 focused sub-questions
that are ideal for searching ArXiv. Each sub-question should target a distinct aspect
of the topic. Return ONLY a valid JSON array of exactly 3 strings, no other text."""


def decompose_query(question: str) -> List[str]:
    """Break a research question into exactly 3 ArXiv-ready sub-questions.

    Args:
        question: The high-level research question from the user.

    Returns:
        A list of exactly 3 focused sub-questions.

    Raises:
        ValueError: If the LLM response cannot be parsed or doesn't yield 3 questions.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError("GROQ_API_KEY environment variable is not set.")

    llm = ChatGroq(
        model="llama-3.1-70b-versatile",
        temperature=0.3,
        groq_api_key=api_key,
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"Research question: {question}\n\nReturn a JSON array of exactly 3 sub-questions."
        ),
    ]

    response = llm.invoke(messages)
    raw = response.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    sub_questions: List[str] = json.loads(raw)

    if not isinstance(sub_questions, list) or len(sub_questions) != 3:
        raise ValueError(
            f"Expected exactly 3 sub-questions, got: {sub_questions}"
        )

    return [str(q) for q in sub_questions]
