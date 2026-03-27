# Patronus Intelligence 🔍

> An AI-powered document research agent — query the **Cyber Ireland 2022 Report** with exact citations, powered by GPT-4o-mini and a from-scratch TF-IDF vector store.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
  - [Step 1 — Ingest the PDF](#step-1--ingest-the-pdf)
  - [Step 2 — Start the API](#step-2--start-the-api)
  - [Step 3 — Query the Agent](#step-3--query-the-agent)
  - [Step 4 — Run Evaluations](#step-4--run-evaluations)
- [API Reference](#api-reference)
- [How It Works](#how-it-works)
- [Configuration](#configuration)
- [Sample Output](#sample-output)
- [License](#license)

---

## Overview

Patronus Intelligence is a **Retrieval-Augmented Generation (RAG)** pipeline built entirely from scratch — no LangChain, no vector database SDK, no heavyweight dependencies.

You give it a PDF. It parses, chunks, and indexes it. Then an agentic loop powered by GPT-4o-mini answers natural language questions by searching the index, running calculations, and returning answers with **exact page-number citations**.

Key capabilities:

- 📄 **PDF parsing** — extracts both body text and structured tables (via `pdfplumber`)
- 🔎 **TF-IDF vector search** — custom-built, zero-dependency keyword index with text/table filtering
- 🤖 **Agentic reasoning** — OpenAI tool-calling loop (up to 8 iterations) for multi-hop queries
- 🧮 **Built-in calculators** — `calculate()` (safe `eval`) and `compute_cagr()` tools
- 🌐 **REST API** — Flask server exposing `/query`, `/logs`, and `/logs/<trace_id>`
- 🧪 **Evaluation suite** — 3 challenge queries with full JSON trace logging
- 🔄 **Fallback mode** — runs without an API key using heuristic pattern matching

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                          ETL Pipeline                            │
│                                                                  │
│  PDF File  ──►  parse_pdf.py  ──►  chunk.py  ──►  vector_store  │
│                (text + tables)    (1600-char     (TF-IDF index,  │
│                                   chunks w/      saved to JSON)  │
│                                   320 overlap)                   │
└──────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼  data/index.json
┌──────────────────────────────────────────────────────────────────┐
│                          Agent Loop                              │
│                                                                  │
│  User Query                                                      │
│      │                                                           │
│      ▼                                                           │
│  GPT-4o-mini  ◄──►  Tool Dispatcher  ──►  search_document()     │
│  (system prompt)                     ──►  calculate()            │
│                                      ──►  compute_cagr()         │
│      │                                                           │
│      ▼                                                           │
│  Final Answer  +  Citations  +  Trace Log                        │
└──────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────┐
│                          Flask REST API                          │
│                                                                  │
│  POST /query         GET /logs        GET /logs/<trace_id>       │
└──────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
patronus-intelligence/
│
├── agent/
│   ├── agent.py          # PatronusAgent (OpenAI loop) + FallbackAgent + TraceLogger
│   └── tools.py          # search_document(), calculate(), compute_cagr(), extract_number()
│
├── api/
│   └── main.py           # Flask REST API — /query, /logs, /logs/<trace_id>
│
├── etl/
│   ├── ingest.py         # Orchestrates full ETL pipeline (parse → chunk → index)
│   ├── parse_pdf.py      # pdfplumber-based PDF parser (text + tables, table-aware)
│   ├── chunk.py          # Text chunker (1600-char target, 320 overlap, sentence-aware)
│   └── vector_store.py   # Custom TF-IDF index (build, search, save/load as JSON)
│
├── data/
│   └── cyber_ireland_2022.pdf   # Source document
│   # (parsed.json, chunks.json, index.json are generated — see .gitignore)
│
├── logs/                 # Agent trace logs (auto-created, gitignored)
│
├── run_tests.py          # Evaluation runner — 3 challenge queries + combined trace log
├── requirements.txt      # pdfplumber, Flask
└── README.md
```

---

## Setup & Installation

**Prerequisites:** Python 3.9+

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/patronus-intelligence.git
cd patronus-intelligence

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

**Optional (for GPT-4o-mini):** Set your OpenAI API key:

```bash
export OPENAI_API_KEY="sk-..."   # macOS/Linux
set OPENAI_API_KEY=sk-...        # Windows CMD
```

> Without an API key the agent runs in **FallbackAgent** mode using heuristic search — useful for offline testing.

---

## Usage

### Step 1 — Ingest the PDF

Parse the PDF, build chunks, and create the TF-IDF index. This only needs to run once (or whenever you swap in a new document).

```bash
python etl/ingest.py data/cyber_ireland_2022.pdf
```

Output:

```
=== STEP 1: Parsing PDF ===
[ETL] Parsing 52 pages...
[ETL] Done. 23 tables found.

=== STEP 2: Chunking ===
[Chunk] 187 chunks (164 text, 23 table)

=== STEP 3: Building Index ===
[Store] Index built: 187 chunks, vocab 4821
[Store] Saved → data/index.json

=== DONE === Pages: 52, Tables: 23, Chunks: 187
```

### Step 2 — Start the API

```bash
python api/main.py
```

```
==================================================
  Patronus Intelligence API
  Model   : gpt-4o-mini
  API Key : SET ✓
  URL     : http://localhost:5000
==================================================
```

### Step 3 — Query the Agent

```bash
curl -X POST http://localhost:5000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the total number of cybersecurity jobs in Ireland in 2022?"}'
```

Add `"include_trace": true` to the request body to receive the full reasoning trace.

### Step 4 — Run Evaluations

Runs three predefined challenge queries and saves a combined JSON trace:

```bash
python run_tests.py
```

Results are saved to `logs/test_run_combined.json`.

---

## API Reference

### `GET /`

Health check.

```json
{
  "status": "ok",
  "service": "Patronus Intelligence API",
  "endpoints": {
    "POST /query": "Submit a query",
    "GET /logs": "List traces"
  }
}
```

---

### `POST /query`

Submit a natural language query.

**Request body:**

| Field           | Type    | Required | Description                                      |
|----------------|---------|----------|--------------------------------------------------|
| `query`         | string  | ✅       | The question to ask                              |
| `include_trace` | boolean | ❌       | Include the full reasoning trace in the response |

**Response:**

```json
{
  "request_id": "a1b2c3d4",
  "query": "What is the total number of cybersecurity jobs?",
  "answer": "According to page 12 of the Cyber Ireland 2022 Report, there are 7,200 cybersecurity jobs in Ireland.",
  "citations": [
    { "page": 12, "context": "...7,200 cybersecurity jobs..." }
  ],
  "iterations": 3,
  "trace_file": "logs/trace_a1b2c3d4.json",
  "duration_seconds": 4.21
}
```

---

### `GET /logs`

Returns the 20 most recent trace files.

```json
{
  "logs": [
    {
      "file": "trace_a1b2c3d4.json",
      "trace_id": "a1b2c3d4",
      "query": "What is the total number of...",
      "duration_seconds": 4.21,
      "steps": 7
    }
  ],
  "count": 1
}
```

---

### `GET /logs/<trace_id>`

Returns the full JSON trace for a specific run — including every LLM call, tool invocation, and result.

---

## How It Works

### 1. ETL Pipeline

**Parsing (`etl/parse_pdf.py`)** — `pdfplumber` extracts text and tables from each page. A bounding-box pass removes words that fall inside table regions from the text extraction, keeping text and table content cleanly separated.

**Chunking (`etl/chunk.py`)** — Text chunks target 1,600 characters with 320-character overlap. Chunk boundaries are snapped to sentence endings (`. `, `.\n`, `\n\n`) to avoid mid-sentence splits. Tables are chunked as single units with a `[TABLE on page N]` header.

**Indexing (`etl/vector_store.py`)** — A custom TF-IDF index is built in pure Python. Term frequency is computed per chunk; IDF is calculated with add-one (Laplace) smoothing. The full index (chunks, TF vectors, IDF weights) is persisted to `data/index.json`.

### 2. Vector Search

`TFIDFIndex.search()` scores each chunk against the query using a dot product of TF-IDF weights. Results can be filtered by `type` (`text` or `table`). The top-K chunks are returned with scores.

### 3. Agent Loop (`agent/agent.py`)

The `PatronusAgent` drives a multi-turn OpenAI tool-calling loop:

1. Sends the user query + system prompt to GPT-4o-mini
2. If the model calls a tool (`search_document`, `calculate`, or `compute_cagr`), the result is appended and the loop continues
3. When the model returns a plain text response (no tool calls), that is the final answer
4. Citations are extracted via regex patterns (`page N`, `p. N`, `(p. N)`)
5. Every step is recorded by `TraceLogger` and saved to `logs/trace_<id>.json`

If no `OPENAI_API_KEY` is set, `FallbackAgent` handles the three built-in test queries with hardcoded search patterns.

---

## Configuration

| Variable        | Default        | Description                     |
|----------------|----------------|---------------------------------|
| `OPENAI_API_KEY`| *(unset)*      | OpenAI API key (optional)       |
| `OPENAI_MODEL`  | `gpt-4o-mini`  | Model used for the agent loop   |
| `TARGET`        | `1600`         | Target chunk size in characters |
| `OVERLAP`       | `320`          | Chunk overlap in characters     |

To use a different document, replace `data/cyber_ireland_2022.pdf` and re-run `python etl/ingest.py`.

---

## Sample Output

**Query:** *"Based on our 2022 baseline and the stated 2030 job target, what is the required CAGR to hit that goal?"*

```
Answer:
To achieve the target of 17,000 cybersecurity jobs by 2030 from a 2022
baseline of 7,200, the required compound annual growth rate (CAGR) is
approximately 11.35% per year (page 38).

Formula: (17000 / 7200) ^ (1 / 8) - 1 = 0.1135

Citations: page 38
```

---

## License

MIT — see [LICENSE](LICENSE) for details.
