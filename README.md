




# Nexus

Agentic RAG pipeline for real-time academic research synthesis

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## Demo

https://github.com/user-attachments/assets/f39870f4-ce26-456e-a30a-b0ff3f5d1662

---

## How it works

```
User Question
    |
    v
Query Decomposer        (LLM rewrites question into 3 orthogonal ArXiv queries)
    |
    v
ArXiv Search (x3)       (fetches top-5 papers per sub-question, deduplicates by ID)
    |
    v
RAG Retriever (FAISS)   (chunks paper text, embeds with MiniLM, ranks by cosine similarity)
    |
    v
Report Synthesizer      (LLM writes 6-section markdown report with inline citations)
    |
    v
Fact Verifier           (LLM cross-checks each cited claim against source chunks)
    |
    v
Verified Report with Citations
```

---

## Features

- LLM-driven query decomposition into 3 focused sub-questions
- ArXiv paper retrieval with deduplication across sub-questions
- FAISS semantic search over chunked paper content
- Structured report synthesis with citations
- Per-claim confidence verification (HIGH/MEDIUM/LOW)
- Real-time agent reasoning streamed via WebSockets
- Local LLM inference via Ollama (zero API cost)

---

## Tech stack

| Layer | Technology |
|---|---|
| LLM | Ollama + `llama3.2` (local) |
| Embeddings | `sentence-transformers` / `all-MiniLM-L6-v2` |
| Vector store | `faiss-cpu` / `IndexFlatIP` (in-memory, cosine similarity) |
| Agent framework | LangChain + `langchain-ollama` + `langchain-core` |
| Backend | FastAPI + Uvicorn (async WebSocket) |
| Frontend | React 18 + TypeScript + Vite |
| Real-time | Native WebSocket + `asyncio.to_thread` |
| Data source | ArXiv API (`arxiv` SDK) + ar5iv.org HTML (`beautifulsoup4`) |

---

## Quick start

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.com) installed and running (`ollama serve`)

### 1. Clone the repo

```bash
git clone <repo-url>
cd nexus
```

### 2. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

No `.env` file is required. Ollama runs locally with no API key.

### 3. Pull Ollama models

```bash
ollama pull llama3.2
```

### 4. Frontend setup

```bash
cd frontend
npm install
```

### 5. Run the backend

```bash
cd backend
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

### 6. Run the frontend

```bash
cd frontend
npm run dev
```

Open **http://localhost:5173**.

---

## Architecture decisions

**Query decomposition.** A single broad question like "How does RLHF improve LLM alignment?" maps to multiple distinct sub-topics: reward modeling, preference data collection, and policy optimization. A single ArXiv query for the full question tends to return papers that touch all three areas superficially. Decomposing into three orthogonal sub-queries and merging results by `arxiv_id` gives broader topical coverage with fewer redundant documents, and provides the retriever with a richer candidate pool to rank against the original question.

**In-memory FAISS vs. persistent vector store.** Each research session assembles a new document set from scratch, typically 5-15 papers producing a few hundred chunks. There is no index to reuse across sessions, no multi-user concurrency requirement, and no dataset large enough to warrant disk-backed storage. A persistent store like Chroma or Pinecone would add serialization overhead and operational complexity for no practical gain. An in-memory `IndexFlatIP` index builds in under a second and is garbage-collected when the request completes.

**WebSockets vs. polling.** The pipeline takes 30-90 seconds with irregular bursts of activity: LLM calls finish unpredictably, ArXiv latency varies, and ar5iv fetches may time out. Polling at any reasonable interval would either miss events or generate wasteful round-trips. Server-Sent Events (SSE) would handle server-to-client streaming but are unidirectional, and the client needs to send the research question on connect. WebSockets cover both directions cleanly, and `asyncio.to_thread` ensures the event loop stays free to flush each send frame before the next blocking tool call begins.

**Local Ollama vs. cloud API.** Running inference locally via Ollama eliminates per-token API cost, removes the need for API key management, and avoids sending potentially sensitive research queries to a third-party service. For a pipeline that makes three to five LLM calls per query, cloud API costs accumulate quickly during development and testing. The tradeoff is inference speed: `llama3.2` on consumer hardware is slower than a hosted API, but for a research tool where the bottleneck is usually ArXiv network latency and HTML parsing, the difference is acceptable.

---

## Engineering highlights

- Built agentic RAG pipeline with LangChain + FAISS that decomposes research questions into 3 focused sub-questions via LLM-driven query decomposition and retrieves relevant ArXiv paper chunks via semantic similarity search

- Synthesized structured research reports with cited findings and per-claim confidence verification (HIGH/MEDIUM/LOW) across 15 retrieved paper chunks per query

- Streamed real-time agent reasoning to React/TypeScript frontend via FastAPI WebSockets, visualizing each pipeline step as it runs
