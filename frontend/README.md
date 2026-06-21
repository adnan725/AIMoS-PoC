# Frontend — DIP Fraktionsverteilung

A small React (Vite + Tailwind) UI for the PoC:

- **Wahlperiode tabs** at the top (WP 20 / 21 / 19 / 18).
- **Left panel** — the fraction distribution for the selected period: a stacked
  proportion bar in the parties' real colours, a data table, and the LLM
  summary.
- **Right panel** — a chat that runs the full agent loop. The LLM picks the
  tool itself (via MCP), and the UI shows which tool it chose as a badge above
  each answer.

## Run it (two terminals)

The frontend talks to the FastAPI backend. In development you run both:

**Terminal 1 — backend (port 8000):**

```bash
# from the project root, with your venv active and deps installed
pip install -e ".[dev]"        # picks up fastapi + uvicorn
python -m dip_poc.web.run      # or: dip-web
```

**Terminal 2 — frontend (port 5173):**

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173. Vite proxies `/api/*` to the backend, so no
CORS setup is needed.

> The chat needs a `GROQ_API_KEY` in your `.env`. Without it, the distribution
> tab still works (with the deterministic summary), and the chat shows a notice.
> The distribution tab needs a valid `DIP_API_KEY` (the public one expired end
> of 05/2026).

## One-process demo (optional)

Build the frontend once and let FastAPI serve it, so everything runs from a
single command — nice for a clean interview demo:

```bash
cd frontend && npm run build && cd ..
python -m dip_poc.web.run
# open http://localhost:8000
```

`app.py` auto-serves `frontend/dist` if it exists.

## What maps to what

| UI piece | Backend |
|---|---|
| Wahlperiode tab change | `GET /api/distribution/{wp}` → `get_fraktion_distribution` |
| Proportion bar + table | the `data.shares` from the pure core |
| "Auswertung" text | `format_distribution` (Groq or fallback) |
| Chat message | `POST /api/chat` → `answer_question` (agent + MCP) |
| Tool badge | the `tools_used` the agent reports back |
