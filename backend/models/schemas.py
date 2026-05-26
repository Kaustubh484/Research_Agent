"""Pydantic schemas for all agent inputs, outputs, and WebSocket events."""

from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Event types streamed over WebSocket
# ---------------------------------------------------------------------------


class EventType(str, Enum):
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    RESULT = "result"
    REPORT = "report"
    ERROR = "error"
    DONE = "done"


class AgentEvent(BaseModel):
    """A single streaming event sent from backend to frontend."""

    type: EventType
    message: str
    data: Optional[Any] = None


# ---------------------------------------------------------------------------
# WebSocket messages
# ---------------------------------------------------------------------------


class ResearchRequest(BaseModel):
    """Payload sent by the client over WebSocket to start research."""

    question: str = Field(..., min_length=5, max_length=1000)


# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------


class DecomposeInput(BaseModel):
    question: str


class DecomposeOutput(BaseModel):
    sub_questions: List[str] = Field(..., min_length=3, max_length=3)


class Paper(BaseModel):
    title: str
    authors: List[str]
    abstract: str
    arxiv_id: str
    url: str


class SearchArxivInput(BaseModel):
    sub_question: str


class SearchArxivOutput(BaseModel):
    papers: List[Paper]


class Chunk(BaseModel):
    text: str
    source_title: str
    source_id: str
    source_url: str


class RetrieveChunksInput(BaseModel):
    papers: List[Paper]
    question: str


class RetrieveChunksOutput(BaseModel):
    chunks: List[Chunk]


class SynthesizeReportInput(BaseModel):
    chunks: List[Chunk]
    question: str


class SynthesizeReportOutput(BaseModel):
    report: str


class VerifyFactsInput(BaseModel):
    report: str
    chunks: List[Chunk]


class VerifyFactsOutput(BaseModel):
    verified_report: str
