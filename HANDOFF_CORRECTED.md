# HANDOFF PROMPT — Paste this at the start of your new thread

> **Updated:** 2026-02-07 19:45 MST (Mountain Time — Edmonton)
> **⚠️ This replaces HANDOFF_SPRINT3.md which had an incorrect Sprint 3 definition.**

---

## PROJECT: Rigour Medtech — Health Canada MedDev Agent
**Repo:** rbhatti-ai/health-canada-meddev-agent (private, GitHub)
**Tech:** Python 3.11, FastAPI, Streamlit, LangGraph, ChromaDB/Pinecone, Anthropic Claude, OpenAI embeddings, local Postgres (dev), Supabase (prod)
**Purpose:** AI-powered regulatory compliance platform for medical device manufacturers navigating Health Canada and FDA submissions.

## CRITICAL: READ MASTER_SPRINT_PLAN_v2.md FIRST

The file `MASTER_SPRINT_PLAN_v2.md` in the project root is the **single source of truth** for sprint planning. Do NOT rely on the old `SPRINT_PLAN.md` or `HANDOFF_SPRINT3.md` — both are outdated.

**Key correction:** Sprint 3 = Gap Detection Engine (deterministic rules), NOT AI Agent Layer. The AI Agent Layer is Sprint 4. Architecture principle: "Structure first, AI second."

## CURRENT STATE (2026-02-07 19:45 MST)
- **Branch:** main
- **Latest commit:** `6f8853f` (Sprint 2d)
- **Tests:** 549/549 passing (4.40s runtime)
- **Pre-commit hooks:** black, isort, ruff, mypy (scoped to src/core + src/persistence), pytest-unit, pytest-regulatory

## COMPLETED SPRINTS

### Sprint 1 (commit f19051c) — Regulatory Twin Foundation
- 19 DB tables (10 regulatory twin: intended_uses, claims, hazards, harms, risk_controls, verification_tests, validation_tests, evidence_items, labeling_assets, submission_targets)
- Pydantic models with Literal types for enums
- TwinRepository: dual Supabase/local Postgres, best-effort persistence
- RLS policies, CHECK constraints, versioning support
- 410 tests

### Sprint 2 (commits 775b72a → 6f8853f) — Traceability, Evidence & Attestation
- **2a:** `src/core/traceability.py` — TraceabilityEngine: link validation, chain traversal, coverage reports (60 tests)
- **2b:** `src/core/evidence_ingestion.py` — EvidenceIngestionService: ingest artifact+evidence+link, bulk, unlinked detection (25 tests)
- **2c:** `src/core/attestation_service.py` — AttestationService: human sign-off, audit trail, 4 types (reviewed/approved/rejected/acknowledged) (35 tests)
- **2d:** `src/api/traceability_routes.py` — 13 FastAPI endpoints under /api/v1/ (19 tests)
- 549 tests total

## REGULATORY CHAIN (enforced by VALID_RELATIONSHIPS)
```
claim -[addresses]-> hazard -[causes/may_cause]-> harm
hazard -[mitigated_by]-> risk_control -[verified_by]-> verification_test
risk_control -[validated_by]-> validation_test
verification_test -[supported_by]-> evidence_item
validation_test -[supported_by]-> evidence_item
claim -[supported_by]-> evidence_item
```

## KEY FILES
```
src/core/traceability.py          — TraceabilityEngine (singleton)
src/core/evidence_ingestion.py    — EvidenceIngestionService (singleton)
src/core/attestation_service.py   — AttestationService (singleton)
src/core/regulatory_twin.py       — Pydantic models for all 10 entity types
src/persistence/twin_repository.py — Dual-backend persistence (Supabase + local Postgres)
src/api/main.py                   — FastAPI app with CORS, lifespan
src/api/traceability_routes.py    — Sprint 2 API routes (13 endpoints)
src/agents/regulatory_agent.py    — SimpleRegulatoryAgent (existing, basic)
configs/settings.py               — App settings
```

## DB TABLES (19 total)
organizations, users, products, device_versions, ai_runs, trace_links, artifacts, attestations, artifact_links, intended_uses, claims, hazards, harms, risk_controls, verification_tests, validation_tests, evidence_items, labeling_assets, submission_targets

## LOCAL POSTGRES SCHEMA QUIRKS
- organizations: (id, name, created_at) — NO slug column
- users: NO email/full_name columns
- products: uses org_id NOT organization_id
- device_versions: has NO organization_id column

## PATTERNS TO FOLLOW
- Best-effort persistence (never crash on DB failure)
- Singleton via get_*() functions
- Pydantic models with Literal types for enums
- to_db_dict() excludes id/created_at, converts UUIDs to strings
- from_db_row() ignores extra fields
- Tests: class-based, descriptive names, no DB required for unit tests
- Pre-commit hooks must all pass before commit
- Mountain Time (Edmonton) timestamps on all checkpoints

## NEXT: SPRINT 3 — GAP DETECTION ENGINE + READINESS ASSESSMENT

**NOT the AI Agent Layer.** See MASTER_SPRINT_PLAN_v2.md for full details.

Planned sub-sprints:
- **3a:** GapDetectionEngine + Pydantic models (GapRule, GapFinding, GapReport) + 12 rules (~65 tests)
- **3b:** ReadinessAssessment + ReadinessReport + regulatory-safe language enforcement (~20 tests)
- **3c:** API endpoints (gap_routes.py) + integration with FastAPI app (~20 tests)

Sprint 3 target: 650+ total tests

## UPCOMING AFTER SPRINT 3
- **Sprint 4:** AI Agent Layer (tools wrapping traceability + evidence + attestation + gap engine)
- **Sprint 5:** Streamlit UI + Submission Readiness Dashboard

## WORKING RULES
1. After ANY code change, run full test suite. Never skip tests.
2. Give bash commands to paste in terminal or Claude Code. Step by step, one at a time.
3. Create checkpoints with Mountain Time timestamps after each sub-sprint.
4. Regulatory-grade practices: traceable, auditable, legally defensible. No shortcuts.
5. Senior developer + senior tester rigor.
6. For long files, create downloadable files instead of heredocs (heredocs truncate in terminal).
