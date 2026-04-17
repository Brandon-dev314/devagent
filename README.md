# DevAgent

**AI-powered developer support agent** with RAG + MCP capabilities.

An intelligent conversational agent that understands technical documentation (RAG), executes real actions through tool use (MCP), and maintains conversational context. Think of it as a "copilot for developer support" that can search docs, create GitHub issues, run database queries, and execute code in sandboxes.

<!-- TODO: Add CI badge when repo is on GitHub -->
<!-- ![CI](https://github.com//devagent/actions/workflows/ci.yml/badge.svg) -->

## Features

- **RAG Pipeline** — Ingests technical documentation (Markdown, PDF), chunks and embeds it, and retrieves relevant context to answer questions with source citations.
- **MCP Tool Use** — Creates GitHub issues, runs read-only database queries, and executes code snippets in isolated Docker sandboxes.
- **Agent Orchestrator** — Routes user intents, manages conversation memory, and plans multi-step actions using the ReAct pattern.
- **Streaming Chat UI** — React frontend with real-time response streaming, source panel, and tool usage indicators.
- **Observability** — Prometheus metrics, Grafana dashboards, and LLM evaluation logging.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Python 3.12 |
| LLM | OpenAI API (GPT-4o-mini) |
| Vector DB | Qdrant |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Frontend | React, Vite |
| Infrastructure | Docker Compose |
| Monitoring | Prometheus + Grafana |
| CI/CD | GitHub Actions |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- An OpenAI API key

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/YOUR-USER/devagent.git
cd devagent

# 2. Create your .env file
cp backend/.env.example backend/.env
# Edit backend/.env and add your OPENAI_API_KEY

# 3. Start everything
make up

# 4. Verify it's running
curl http://localhost:8000/health
```

The API will be available at `http://localhost:8000` with Swagger docs at `http://localhost:8000/docs`.

### Development

```bash
# Run tests
make test

# View logs
make logs

# Open database shell
make db-shell

# Stop everything
make down
```

## Architecture

```
┌─────────────────────────────────────┐
│           Chat UI (React)           │
└──────────────┬──────────────────────┘
               │ WebSocket / REST
┌──────────────▼──────────────────────┐
│       Agent Orchestrator (FastAPI)   │
│  ┌──────────┬───────────┬────────┐  │
│  │LLM Router│Conv Memory│Tool Sel│  │
│  └──────────┴───────────┴────────┘  │
└──┬──────────────┬───────────────┬───┘
   │              │               │
┌──▼───┐    ┌────▼────┐    ┌────▼─────┐
│ RAG  │    │MCP Tools│    │Code Exec │
│Qdrant│    │GitHub,DB│    │ Sandbox  │
└──────┘    └─────────┘    └──────────┘
```

## Project Structure

```
devagent/
├── backend/
│   ├── app/
│   │   ├── agent/       # Orchestrator, planner, memory, router
│   │   ├── rag/         # Ingestion, chunking, embeddings, retrieval
│   │   ├── tools/       # MCP servers (GitHub, DB, code executor)
│   │   ├── models/      # Pydantic schemas, DB entities
│   │   ├── api/         # FastAPI route handlers
│   │   ├── config.py    # Centralized settings (pydantic-settings)
│   │   └── main.py      # App entry point
│   └── tests/           # Mirrors app/ structure
├── frontend/            # React chat interface
├── monitoring/          # Prometheus + Grafana config
├── scripts/             # Ingestion, seeding, evaluation
└── docker-compose.yml   # Full stack orchestration
```

## License

MIT