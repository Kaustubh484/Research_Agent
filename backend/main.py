"""FastAPI application entry point with WebSocket research endpoint."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.agent.researcher import run_research_agent
from backend.models.schemas import AgentEvent, EventType

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle hook."""
    # Validate critical environment variables at startup
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError(
            "GROQ_API_KEY is not set. Copy backend/.env.example to backend/.env and fill in your key."
        )
    yield


app = FastAPI(
    title="Research Assistant API",
    description="AI-powered research pipeline with real-time streaming via WebSocket.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Lightweight liveness probe."""
    return {"status": "ok", "groq_configured": bool(os.getenv("GROQ_API_KEY"))}


@app.websocket("/ws/research")
async def research_websocket(websocket: WebSocket) -> None:
    """WebSocket endpoint that streams real-time agent events.

    Protocol:
      Client  → Server: JSON  {"question": "<research question>"}
      Server  → Client: JSON  AgentEvent (type, message, data)

    Event types: thinking | tool_call | result | report | error | done
    """
    await websocket.accept()

    try:
        # Receive the research question from the client
        raw = await websocket.receive_text()
        import json
        payload = json.loads(raw)
        question = payload.get("question", "").strip()

        if not question:
            error_event = AgentEvent(
                type=EventType.ERROR,
                message="No research question provided.",
            )
            await websocket.send_text(error_event.model_dump_json())
            await websocket.close()
            return

        # Run the research pipeline, streaming events through the WebSocket
        await run_research_agent(question, websocket.send_text)

    except WebSocketDisconnect:
        # Client disconnected mid-stream; nothing to do
        pass
    except Exception as exc:
        # Last-resort error handler — try to notify client before closing
        try:
            error_event = AgentEvent(
                type=EventType.ERROR,
                message=f"Unexpected server error: {exc}",
            )
            await websocket.send_text(error_event.model_dump_json())
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
