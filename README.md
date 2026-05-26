# Research Assistant

An AI-powered research pipeline that searches ArXiv, retrieves relevant paper sections,
synthesizes a structured report, and verifies every claim — all streamed live to a React
frontend over WebSocket.

---

## Architecture

```
┌────────────────────────────────────────────┐
│  Browser (React + Vite + TypeScript)       │
│  SearchBar → AgentLog ← ResearchReport     │
│              ↕ WebSocket                   │
├────────────────────────────────────────────┤
│  FastAPI Backend (Python)                  │
│  /ws/research  /health                     │
│                                            │
│  Agent Pipeline (LangChain + Groq)         │
│  1. decompose_query   → 3 sub-questions    │
│  2. search_arxiv      → top 5 papers each │
│  3. retrieve_chunks   → FAISS + embeddings │
│  4. synthesize_report → markdown report    │
│  5. verify_facts      → confidence labels  │
└────────────────────────────────────────────┘
```

---

## Prerequisites

| Tool    | Version  |
|---------|----------|
| Python  | ≥ 3.10   |
| Node.js | ≥ 18     |
| npm     | ≥ 9      |

You also need a **Groq API key** — get one free at <https://console.groq.com>.

---

## Setup

### 1. Clone / enter the project

```bash
cd research-assistant
```

### 2. Backend setup

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set GROQ_API_KEY=<your key>
```

### 3. Frontend setup

```bash
cd ../frontend

npm install

# Optional: copy env (default WS URL is ws://localhost:8000)
cp .env.example .env
```

---

## Running Locally

Open **two terminals**:

**Terminal 1 — Backend**

```bash
cd backend
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — Frontend**

```bash
cd frontend
npm run dev
```

Then open <http://localhost:5173> in your browser.

### Health check

```bash
curl http://localhost:8000/health
# {"status":"ok","groq_configured":true}
```

---

## How It Works

1. You type a research question and click **Research**.
2. The frontend opens a WebSocket to `ws://localhost:8000/ws/research` and sends
   `{"question": "..."}`.
3. The backend agent runs five tools in sequence, streaming JSON events after
   each step:

| Event type  | Meaning                                    |
|-------------|--------------------------------------------|
| `thinking`  | Agent is reasoning (shown in gray italic)  |
| `tool_call` | A tool is being invoked (blue monospace)   |
| `result`    | A tool returned data (green)               |
| `report`    | Final report is ready                      |
| `error`     | Something went wrong (red)                 |
| `done`      | Pipeline complete                          |

4. When the `report` event arrives, the React app renders the markdown report
   with inline confidence badges (**HIGH** / **MED** / **LOW**).

---

## Running Tests

```bash
cd backend
source .venv/bin/activate

# Run all unit tests (no API key required — LLM calls are mocked)
pytest tests/ -v

# Run only fast unit tests, skipping integration
pytest tests/ -v -m "not integration"

# Run integration tests (real Groq API calls — requires valid GROQ_API_KEY)
pytest tests/ -v -m integration
```

### Test coverage

| File                      | What it tests                                      |
|---------------------------|----------------------------------------------------|
| `tests/test_arxiv.py`     | ArXiv paper search — shape, fields, deduplication  |
| `tests/test_chunker.py`   | Text tokenization and overlapping chunk windows    |
| `tests/test_decomposer.py`| Query decomposition — mock + real API              |
| `tests/test_verifier.py`  | Fact verification — mock + real API                |

---

## Project Structure

```
research-assistant/
├── backend/
│   ├── agent/
│   │   ├── __init__.py
│   │   └── researcher.py        # Agent loop + event streaming
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic schemas for all I/O
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── decomposer.py        # Tool 1: query decomposition
│   │   ├── arxiv_search.py      # Tool 2: ArXiv search
│   │   ├── retriever.py         # Tool 3: FAISS chunk retrieval
│   │   ├── synthesizer.py       # Tool 4: report synthesis
│   │   └── verifier.py          # Tool 5: fact verification
│   ├── main.py                  # FastAPI app entry point
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SearchBar.tsx
│   │   │   ├── AgentLog.tsx
│   │   │   └── ResearchReport.tsx
│   │   ├── services/
│   │   │   └── websocket.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── .env.example
├── tests/
│   ├── conftest.py
│   ├── test_arxiv.py
│   ├── test_chunker.py
│   ├── test_decomposer.py
│   └── test_verifier.py
└── README.md
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable       | Required | Description                    |
|----------------|----------|--------------------------------|
| `GROQ_API_KEY` | Yes      | API key from console.groq.com  |

### Frontend (`frontend/.env`)

| Variable       | Default                   | Description                      |
|----------------|---------------------------|----------------------------------|
| `VITE_WS_URL`  | `ws://localhost:8000`     | WebSocket base URL for backend   |

---

## Notes

- The FAISS index is built **in-memory per request** — no persistence required.
- ar5iv.org fetches are best-effort; the tool falls back to the abstract if the
  HTML fetch fails or times out.
- The Groq model used is `llama-3.1-70b-versatile`. Swap via environment variable
  or edit the model name in each tool file if needed.
- Integration tests call the real Groq API and will consume quota.
