A few deliberate decisions:

- **The language model never computes.** All counting and percentages are done in pure, tested Python (`core/aggregation.py`). The model only turns finished numbers into text. This keeps the figures correct and reproducible.
- **MCP is applied where a language model is involved.** The chat goes through a real MCP server (tool discovery via `list_tools`, invocation via `call_tool` over stdio). The distribution view calls the same underlying service directly over HTTP — there is no need to route a deterministic lookup through a language model.
- **Observability is built in.** Structured JSON logs with a correlation id per request, audit events (which tool was selected, API latency, cache hits), secret redaction, and validation of model-chosen arguments. See `observability/`.

---

## Possible extensions

- A usage and cost dashboard built on the existing observability events. Tool usage and cache-hit rate are already captured, token consumption and cost estimation would be added by recording Groq's `usage` field per call.
- Additional MCP tools (e.g. lookups by topic or document), which the agent would pick up automatically.

## Getting Started

Follow these steps to set up and run the proof of concept locally.

> **Note:** All commands below are run from the **project root** (the folder containing `pyproject.toml`), unless stated otherwise.

### Prerequisites

- Python 3.10 or newer
- Node.js 18 or newer (only required for the web interface)
- A `DIP_API_KEY` and `GROQ_API_KEY` in a `.env` file

### 1. Set up the environment

Create and activate a virtual environment:

```bash
py -m venv .venv
source .venv/Scripts/activate      # Windows (Git Bash)
# source .venv/bin/activate        # macOS / Linux
```

Install the project and its dependencies:

```bash
pip install -e ".[dev]"
```

### 2. Configure API keys

Copy the example environment file and fill in your own keys:

```bash
cp .env.example .env
```

Then open `.env` and set:

- `DIP_API_KEY` — get a free key from `https://dip.bundestag.de/%C3%BCber-dip/hilfe/api`
- `GROQ_API_KEY` — create a free key at `https://console.groq.com/keys`.

### 3. Verify the setup

Run the test suite. These tests run fully offline and require no API keys:

```bash
pytest -q
```

A passing run confirms the core logic is working.

---

## Running the Application

There are two ways to use the application: a **command-line interface (CLI)** and a **web interface**.

### Option A — Command-Line Interface

From the project root, start the interactive agent:

```bash
py -m dip_poc.agent
```

You can then ask questions in the terminal, for example about a specific person or about the fraction distribution of a given electoral term.

### Option B — Web Interface (React)

The web interface requires **two servers running at the same time**: the React frontend and the Python backend.

**1. Start the frontend**

From the `frontend/` directory:

```bash
cd frontend
npm install
npm run dev
```

**2. Start the backend**

Open a **second terminal**, return to the project root, and activate the virtual environment before starting the backend:

```bash
source .venv/Scripts/activate      # Windows (Git Bash)
py -m dip_poc.web.run
```

**3. Open the application**

Once both servers are running, open the interface in your browser:

**http://localhost:5173/**
