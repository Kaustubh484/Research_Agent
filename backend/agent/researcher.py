"""Agent loop: orchestrates the 5 research tools and streams events over WebSocket."""

from __future__ import annotations

import asyncio
import json
import traceback
from typing import Any, Callable, Coroutine, List

from backend.models.schemas import AgentEvent, Chunk, EventType, Paper
from backend.tools.arxiv_search import search_arxiv
from backend.tools.decomposer import decompose_query
from backend.tools.retriever import retrieve_chunks
from backend.tools.synthesizer import synthesize_report
from backend.tools.verifier import verify_facts

# Type alias for the WebSocket send callable
SendFn = Callable[[str], Coroutine[Any, Any, None]]


async def _emit(send: SendFn, event_type: EventType, message: str, data: Any = None) -> None:
    """Serialize and send a single AgentEvent JSON string over the WebSocket."""
    event = AgentEvent(type=event_type, message=message, data=data)
    await send(event.model_dump_json())


async def run_research_agent(question: str, send: SendFn) -> None:
    """Execute the full 5-step research pipeline and stream progress events.

    Steps:
      1. decompose_query   — break question into 3 sub-questions
      2. search_arxiv      — fetch papers for each sub-question
      3. retrieve_chunks   — embed, index, and rank relevant chunks
      4. synthesize_report — generate structured markdown report
      5. verify_facts      — annotate each claim with confidence labels

    Every step emits thinking → tool_call → result events. On any exception
    an error event is streamed and the pipeline halts gracefully.

    Args:
        question: The user's research question.
        send:     Async callable that sends a string message over the WebSocket.
    """
    try:
        # ------------------------------------------------------------------ #
        # Step 1: Decompose query                                              #
        # ------------------------------------------------------------------ #
        await _emit(send, EventType.THINKING,
                    "Breaking down your research question into focused sub-questions...")

        await _emit(send, EventType.TOOL_CALL,
                    "decompose_query", {"question": question})

        sub_questions: List[str] = await asyncio.to_thread(decompose_query, question)

        await _emit(send, EventType.RESULT,
                    f"Generated {len(sub_questions)} sub-questions",
                    {"sub_questions": sub_questions})

        # ------------------------------------------------------------------ #
        # Step 2: Search ArXiv for each sub-question                          #
        # ------------------------------------------------------------------ #
        all_papers: List[Paper] = []
        seen_ids: set[str] = set()

        for i, sq in enumerate(sub_questions, start=1):
            await _emit(send, EventType.THINKING,
                        f"Searching ArXiv for sub-question {i}/{len(sub_questions)}: {sq}")

            await _emit(send, EventType.TOOL_CALL,
                        "search_arxiv", {"sub_question": sq})

            papers = await asyncio.to_thread(search_arxiv, sq)

            # Deduplicate by arxiv_id across sub-question searches
            new_papers = [p for p in papers if p.arxiv_id not in seen_ids]
            seen_ids.update(p.arxiv_id for p in new_papers)
            all_papers.extend(new_papers)

            paper_summaries = [{"title": p.title, "arxiv_id": p.arxiv_id} for p in papers]
            await _emit(send, EventType.RESULT,
                        f"Found {len(papers)} papers ({len(new_papers)} new)",
                        {"papers": paper_summaries})

        await _emit(send, EventType.THINKING,
                    f"Collected {len(all_papers)} unique papers across all sub-questions.")

        # ------------------------------------------------------------------ #
        # Step 3: Retrieve and rank relevant chunks                           #
        # ------------------------------------------------------------------ #
        await _emit(send, EventType.THINKING,
                    "Fetching paper content, chunking, and ranking by relevance...")

        await _emit(send, EventType.TOOL_CALL,
                    "retrieve_chunks",
                    {"num_papers": len(all_papers), "question": question})

        chunks: List[Chunk] = await asyncio.to_thread(retrieve_chunks, all_papers, question)

        chunk_previews = [
            {"source": c.source_title, "preview": c.text[:120] + "..."}
            for c in chunks
        ]
        await _emit(send, EventType.RESULT,
                    f"Retrieved {len(chunks)} top relevant chunks",
                    {"chunks": chunk_previews})

        # ------------------------------------------------------------------ #
        # Step 4: Synthesize report                                           #
        # ------------------------------------------------------------------ #
        await _emit(send, EventType.THINKING,
                    "Synthesizing a structured research report from retrieved chunks...")

        await _emit(send, EventType.TOOL_CALL,
                    "synthesize_report",
                    {"num_chunks": len(chunks), "question": question})

        report: str = await asyncio.to_thread(synthesize_report, chunks, question)

        await _emit(send, EventType.RESULT,
                    "Report synthesized successfully",
                    {"report_length": len(report)})

        # ------------------------------------------------------------------ #
        # Step 5: Verify facts                                                #
        # ------------------------------------------------------------------ #
        await _emit(send, EventType.THINKING,
                    "Verifying claims against source chunks and assigning confidence labels...")

        await _emit(send, EventType.TOOL_CALL,
                    "verify_facts",
                    {"report_length": len(report), "num_chunks": len(chunks)})

        verified_report: str = await asyncio.to_thread(verify_facts, report, chunks)

        await _emit(send, EventType.RESULT,
                    "Fact verification complete",
                    {"verified_report_length": len(verified_report)})

        # ------------------------------------------------------------------ #
        # Final report delivery                                               #
        # ------------------------------------------------------------------ #
        await _emit(send, EventType.REPORT,
                    "Research complete",
                    {"report": verified_report})

        await _emit(send, EventType.DONE,
                    "Research pipeline finished successfully.")

    except EnvironmentError as exc:
        await _emit(send, EventType.ERROR,
                    f"Configuration error: {exc}")
    except Exception as exc:
        tb = traceback.format_exc()
        await _emit(send, EventType.ERROR,
                    f"Pipeline error: {exc}",
                    {"traceback": tb})
