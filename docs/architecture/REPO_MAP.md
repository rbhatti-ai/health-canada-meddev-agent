# REPOSITORY MAP (ORIENTATION ONLY)

> Last updated: 2026-02-06
> Status: **Working Python project with Streamlit UI, FastAPI backend (Vercel), and RAG-enabled regulatory agent.**
> Rule: This document describes WHAT EXISTS in THIS repo. It must not invent files or claim phases completed unless verified by `ls` / `git`.

---

## Purpose
AI agents must read this file before making changes. It prevents:
- breaking existing flows
- duplicating logic
- creating parallel scaffolds
- drifting from the governing architecture

Governing docs:
- `/docs/architecture/REGULATORY_EXECUTION_PLATFORM_ARCHITECTURE.md`
- `/CLAUDE.md`

---

## Ground-truth commands (use these; do not guess)
- `pwd`
- `ls -la`
- `find . -maxdepth 2 -type f | sort`
- `git status --porcelain=v1 -b`
- `rg -n "supabase|s3|boto3|streamlit|fastapi|openai|anthropic" .`

---

## Current repo structure (filled from ground truth)

### Root (top level)
| File/Folder | Purpose |
|-------------|---------|
| `streamlit_app.py` | Main Streamlit UI (connects to Vercel API backend) |
| `CLAUDE.md` | Agent operating directive |
| `pyproject.toml` | Python dependencies (Python 3.11+) |
| `requirements.txt` | Minimal pip requirements |
| `Dockerfile` | Container config |
| `docker-compose.yml` | Multi-container orchestration |
| `vercel.json` | Vercel deployment config |
| `.vercelignore` | Vercel exclusion patterns |
| `pytest.ini` | Test configuration |
| `VALIDATION_STATUS.md` | Test validation status |
| `runtime.txt` | Python runtime version |

### `src/` (core application code)
| Module | Files | Responsibility |
|--------|-------|----------------|
| `src/core/` | `models.py`, `classification.py`, `pathway.py`, `checklist.py` | Domain models (Pydantic), device classification engine (IMDRF SaMD matrix), pathway advisor, checklist generator |
| `src/agents/` | `regulatory_agent.py`, `tools.py` | LangGraph-based conversational agent with tool-calling; 5 tools: classify, pathway, checklist, search, fees |
| `src/api/` | `main.py` | FastAPI REST API (full version with RAG support) |
| `src/ingestion/` | `loader.py`, `chunker.py`, `embedder.py`, `pipeline.py` | Document loading, chunking, OpenAI embeddings |
| `src/retrieval/` | `retriever.py`, `vectorstore.py`, `reranker.py` | RAG retrieval layer using ChromaDB (dev) / Pinecone (prod) |
| `src/ui/` | `app.py` | Alternative Streamlit UI module |
| `src/utils/` | `logging.py` | Structured logging (structlog) |
| `src/cli.py` | CLI entry point using Typer |

### `api/` (Vercel serverless)
| File | Purpose |
|------|---------|
| `index.py` | Lightweight FastAPI for Vercel (no RAG, inline models to avoid import issues) |
| `requirements.txt` | Vercel-specific minimal dependencies |

**Endpoints (Vercel):**
- `GET /` — service info
- `GET /health` — health check
- `POST /api/v1/classify` — device classification
- `POST /api/v1/pathway` — regulatory pathway + fees

### `docs/`
| File | Purpose |
|------|---------|
| `ARCHITECTURE.md` | Original architecture notes |
| `KNOWLEDGE_BASE.md` | Regulatory knowledge base docs |
| `TESTING_PLAN.md` | Test strategy |
| `architecture/REGULATORY_EXECUTION_PLATFORM_ARCHITECTURE.md` | **GOVERNING DOCUMENT** |
| `architecture/REPO_MAP.md` | This file |

### `tests/` (~1,473 lines total)
| Folder | Contents |
|--------|----------|
| `unit/` | `test_classification.py`, `test_models.py`, `test_pathway.py` |
| `integration/` | `test_classification_flow.py` |
| `api/` | `test_endpoints.py` |
| `regulatory/` | `test_fees_2024.py`, `test_samd_matrix.py` |
| `fixtures/` | Test fixtures |
| `rag/` | (empty - RAG tests not implemented) |
| `performance/` | (empty - perf tests not implemented) |
| `conftest.py` | Pytest fixtures incl. FastAPI TestClient |

### `configs/`
| File | Purpose |
|------|---------|
| `settings.py` | Pydantic-settings config (env vars → typed settings) |

### `scripts/`
| File | Purpose |
|------|---------|
| `ingest_documents.py` | Document ingestion → ChromaDB vectorstore |

### `data/`
| Folder | Contents |
|--------|----------|
| `raw/` | Source docs: `checklists/`, `flowcharts/` |
| `processed/` | (empty) |
| `vectorstore/` | ChromaDB sqlite (~27 MB) + collection UUID folder |

---

## Key integrations (filled from code grep)

### Supabase
- **NOT USED** — No Supabase references found in codebase.
- Risk notes: Governing architecture specifies row-level security; current implementation has no multi-tenant database.

### S3 (or S3-compatible)
- **NOT USED** — No boto3/S3 references found.
- `docs/ARCHITECTURE.md` mentions S3 as future option.
- Risk notes: Governing doc specifies "Store outputs in S3" for documents; not implemented.

### AI calls
- **Providers:** OpenAI, Anthropic (Claude)
- **Where configured:**
  - `configs/settings.py:24-25` — API key env vars
  - `src/agents/regulatory_agent.py:14-15` — LangChain integrations
  - `src/ingestion/embedder.py:13,42-59` — OpenAI embeddings (text-embedding-3-small)
- **Models used:**
  - Default: `claude-3-5-sonnet-20241022` (settings.py:63)
  - Embeddings: `text-embedding-3-small` (1536 dims)
- **What's logged:**
  - `src/utils/logging.py` — structlog setup
  - Agent logs user messages (truncated) and responses
- **Guardrails present:**
  - Temperature: 0.1 (low)
  - System prompt forbids claiming compliance
  - Confidence scores returned with classifications
  - Warnings array for edge cases
- **Risk notes:**
  - NO `ai_runs` provenance table (required by governing doc)
  - NO human approval workflow for AI outputs

---

## Current user flows (as implemented)

### Streamlit UI (`streamlit_app.py`)
1. **Device Classification** — User inputs device info → POST `/api/v1/classify` → displays class, risk level, rationale, warnings
2. **Regulatory Pathway** — User selects class → POST `/api/v1/pathway` → displays steps, fees, timeline
3. **About** — Static info page

### CLI (`src/cli.py`)
- `meddev-agent classify` — interactive classification
- `meddev-agent pathway` — pathway generation
- `meddev-agent chat` — conversational agent
- `meddev-agent ui` — launch Streamlit

### API (full version: `src/api/main.py`)
- Same endpoints as Vercel + RAG search capabilities

---

## Known gaps vs governing architecture

| Requirement | Status | Gap |
|-------------|--------|-----|
| **Regulatory Twin** (structured device profile) | Partial | `DeviceInfo` model exists; no persistent storage, no versioning |
| **Traceability Engine** (polymorphic `trace_links`) | NOT STARTED | No link table, no claim→risk→control→evidence chain |
| **Evidence Gap Detection** | NOT STARTED | No rules engine, no gap scoring |
| **Submission Readiness Dashboard** | NOT STARTED | No dashboard UI |
| **Document Orchestration** | NOT STARTED | No document generation from structured data |
| **Deficiency Response Workflow** | NOT STARTED | No deficiency tracking |
| **AI Provenance Table (`ai_runs`)** | NOT STARTED | No storage of AI inputs/outputs/model/timestamp |
| **Human-in-the-Loop Approval** | NOT STARTED | No approval workflow |
| **Version Everything** | NOT STARTED | No immutable records, no version pointers |
| **Row-Level Security / Multi-Tenancy** | NOT STARTED | No auth, no tenant isolation |
| **S3 Document Storage** | NOT STARTED | No S3 integration |
| **Supabase / PostgreSQL** | NOT STARTED | No persistent database |

**Current state:** Phase 0 (Discovery) + partial Phase 1 (basic classification/pathway logic).

---

## Change safety rules
- No large refactors.
- Additive changes only unless explicitly authorized.
- Feature flags preferred for new modules.
- Never create a second "new project scaffold" inside this repo.
- Preserve existing: `streamlit_app.py`, `api/index.py`, `src/core/`, `src/agents/`, tests.
