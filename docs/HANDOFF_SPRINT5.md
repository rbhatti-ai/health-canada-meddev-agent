# HANDOFF PROMPT — Rigour Medtech Regulatory Platform

> **As of:** 2026-02-07 21:30 MST (Mountain Time — Edmonton)
> **Purpose:** Complete context for a new AI session to continue development seamlessly.
> **Next task:** Sprint 5 — Streamlit UI + Submission Readiness Dashboard

---

## PROJECT OVERVIEW

**Rigour Medtech** — AI-powered regulatory compliance platform for medical device manufacturers navigating Health Canada and FDA submissions. Regulatory-grade infrastructure: traceable, auditable, legally defensible. Structure first, AI second.

**Tech stack:** Python 3.11+, FastAPI, Streamlit, LangGraph agents, ChromaDB/Pinecone RAG, Anthropic Claude, OpenAI embeddings, local Postgres (dev), Supabase (prod).

**Repo:** `~/health-canada-meddev-agent` (private GitHub: rbhatti-ai/health-canada-meddev-agent)
**venv:** `~/health-canada-meddev-agent/venv/` — always activate with `source venv/bin/activate`
**Python:** Use `python3` (not `python`)

---

## CURRENT STATE

- **Branch:** main
- **Latest commit:** 172b35c (Sprint 4D complete — Sprint 4 FULLY COMPLETE)
- **Tests:** 921/921 passing (14.38s runtime)
- **Pre-commit hooks:** black, isort, ruff, mypy (scoped), pytest-unit, pytest-regulatory — all 13 passing

---

## COMPLETED SPRINTS (ALL 4 DONE)

| Sprint | Commit | Tests | What Was Delivered |
|--------|--------|-------|--------------------|
| 1 | f19051c | 410 | 10 DB tables, Pydantic models, TwinRepository (dual Supabase/Postgres) |
| 2 | 6f8853f | 549 | TraceabilityEngine, EvidenceIngestion, Attestation, 13 API endpoints |
| 3a | c541059 | 627 | GapDetectionEngine, 12 deterministic rules (GAP-001 to GAP-012) |
| 3b | 43f9038 | 699 | ReadinessAssessment, penalty scoring, 14 forbidden words, language safety |
| 3c | 810b002 | 732 | Gap/Readiness API endpoints (4 new), 33 tests |
| 4A | 3912245 | 780 | 13 LangGraph agent tools, _safe_call wrapper, REGULATORY_TWIN_TOOLS list |
| 4B | (prev) | 847 | 6 system prompts, 6 structured output schemas, language safety, AI provenance |
| 4C | fb3ba0d | 888 | Agent orchestration: LangGraph StateGraph, 4 workflows, prompt routing, provenance, sanitization |
| **4D** | **172b35c** | **921** | **33 agent integration tests: workflows, provenance, language safety, error handling** |

---

## CRITICAL API PATTERNS (READ BEFORE WRITING CODE)

These patterns caused repeated bugs in earlier sprints. Follow them exactly:

1. **TwinRepository** — Generic methods ONLY: `get_by_device_version(table, dvid)`, `get_by_id(table, id)`, `get_by_field(table, field, value)`, `get_by_org(table, org_id)`, `create(table, data)`, `update(table, id, data)`, `count(table)`. Returns `list[dict]`. NO entity-specific methods.

2. **TraceLink** — Pydantic model. Use attribute access (`.source_type`, `.target_type`), NOT `.get()` dict style.

3. **Logger import:** `from src.utils.logging import get_logger` (NOT `src.utils.logger`)

4. **ruff B017:** Never `pytest.raises(Exception)` — always use specific exception types.

5. **ruff B904:** Always `raise HTTPException(...) from e` or `from None` in except blocks.

6. **ruff modern style:** Use `list[str]` not `List[str]`, `dict[str, Any]` not `Dict[str, Any]`, `str | None` not `Optional[str]`. Run `ruff check --fix` after creating files.

7. **mypy:** All functions in `src/agents/` need return type annotations. Watch `str | None` vs `str` — use `value or ""` pattern.

8. **Tests:** Class-based, descriptive names, no DB required for unit tests. Use `SimpleNamespace` via `make_link()`/`make_finding()` helpers in tests that need mock objects.

9. **Regulatory-safe language:** NEVER "compliant", "ready", "will pass", "guaranteed", "approved", "certified". ALWAYS "readiness assessment based on configured expectations."

10. **AI provenance:** Every AI output → `ai_runs` table BEFORE display.

11. **For long files:** Create downloadable files — heredocs truncate in terminal.

12. **ToolNode + mocks:** When mocking tools for `RegulatoryAgent` tests, you MUST also mock `_build_graph` via `patch.object(RegulatoryAgent, "_build_graph")` because `ToolNode` rejects `MagicMock` objects. See the `mock_agent` fixture in `tests/unit/test_agent_orchestration.py` and `tests/integration/test_agent_flow.py` for the pattern.

13. **Unused variables in tests:** ruff F841 catches unused `result = ...` in tests. Either use the variable in an assertion or call the method directly without assignment.

---

## FILE INVENTORY

### Core Services (8 classes, all singletons via `get_*()`)

```
src/core/traceability.py            — TraceabilityEngine: link validation, chain traversal, coverage
src/core/evidence_ingestion.py      — EvidenceIngestionService: ingest, bulk, unlinked detection
src/core/attestation_service.py     — AttestationService: human sign-off, audit trail, 4 types
src/core/gap_engine.py              — GapDetectionEngine: 12 rules (GAP-001 to GAP-012)
src/core/readiness.py               — ReadinessAssessment: penalty scoring, category scores, language safety
src/core/regulatory_twin.py         — Pydantic models for all 10 entity types
src/core/classification.py          — Device classification engine (SaMD, IVD, risk classes)
src/persistence/twin_repository.py  — Dual-backend persistence (Supabase + local Postgres)
```

### Agent Layer

```
src/agents/tools.py                 — 5 original tools (classify, pathway, checklist, search, fees)
src/agents/regulatory_twin_tools.py — 13 new tools (Sprint 4A), _safe_call wrapper, REGULATORY_TWIN_TOOLS list
src/agents/prompts.py               — 6 system prompts, 6 structured output schemas, language safety, AI provenance (Sprint 4B)
src/agents/regulatory_agent.py      — RegulatoryAgent (LangGraph orchestration) + SimpleRegulatoryAgent (deprecated) (Sprint 4C)
src/agents/__init__.py              — Exports: RegulatoryAgent, SimpleRegulatoryAgent, get_regulatory_agent, AgentState, WORKFLOW_DEFINITIONS, detect_workflow, detect_task_type, get_agent_tools, get_regulatory_twin_tools, REGULATORY_TWIN_TOOLS
```

### API Layer (23 endpoints total)

```
src/api/main.py                     — FastAPI app with CORS, lifespan
src/api/traceability_routes.py      — Sprint 2 routes (13 endpoints)
src/api/gap_routes.py               — Sprint 3c routes (4 endpoints)
+ 6 original endpoints (health, stats, classify, pathway, search, chat)
```

### Tests (921 total)

```
tests/integration/test_agent_flow.py    — 33 tests (Sprint 4D) ← NEW
tests/unit/test_agent_orchestration.py  — 41 tests (Sprint 4C)
tests/unit/test_prompts.py              — 67 tests (Sprint 4B)
tests/unit/test_regulatory_twin_tools.py — 48 tests (Sprint 4A)
tests/unit/test_gap_engine.py           — 78 tests (Sprint 3a)
tests/unit/test_readiness.py            — 72 tests (Sprint 3b)
tests/unit/test_traceability.py         — ~60 tests (Sprint 2)
tests/unit/test_regulatory_twin_models.py — model validation tests
tests/unit/test_regulatory_twin_migration.py — SQL schema tests
tests/api/test_gap_endpoints.py         — 33 tests (Sprint 3c)
tests/api/test_endpoints.py             — API route tests
tests/integration/                      — Integration test suites
tests/regulatory/                       — Regulatory correctness tests
```

---

## AGENT LAYER DETAILS (Sprint 4, all sub-sprints)

### Sprint 4C: RegulatoryAgent (`src/agents/regulatory_agent.py`)

**AgentState (TypedDict):** Extended with 7 new fields:
- `current_workflow: str | None` — Active workflow name
- `workflow_step: int` — Current step in workflow (0-based)
- `workflow_results: dict[str, Any]` — Accumulated workflow step results
- `device_version_id: str | None` — Current device context
- `organization_id: str | None` — Current org context
- `task_type: str | None` — Detected task type for prompt routing
- `provenance_records: list[dict[str, Any]]` — AI provenance audit trail

**4 Named Workflows (WORKFLOW_DEFINITIONS):**
- `full_analysis`: classify_device → get_coverage_report → run_gap_analysis → get_readiness_assessment
- `risk_assessment`: get_trace_chain → get_coverage_report → run_gap_analysis → get_critical_gaps
- `evidence_review`: get_evidence_for_device → find_unlinked_evidence → run_gap_analysis
- `submission_readiness`: run_gap_analysis → get_critical_gaps → get_readiness_assessment

**WORKFLOW_TRIGGERS:** Keyword-to-workflow mapping for auto-detection from user messages:
- `full_analysis`: "analyze my device", "full analysis", "complete analysis", "analyze device"
- `risk_assessment`: "risk assessment", "risk analysis", "hazard assessment", "risk review"
- `evidence_review`: "evidence review", "evidence assessment", "review evidence"
- `submission_readiness`: "submission readiness", "readiness assessment", "submission check", "am i ready"

**LangGraph StateGraph (4 nodes):**
1. `router` — Detects workflows and task types from user message
2. `agent` — Calls LLM with task-appropriate system prompt
3. `tools` — ToolNode with all 18 tools
4. `sanitize` — Applies `sanitize_ai_output()` + creates AI provenance record

**Flow:** router → agent → (tools ↔ agent loop) → sanitize → END

**RegulatoryAgent public API:**
- `chat(user_message)` → response string (sanitized, provenance-logged)
- `chat_with_context(user_message, device_version_id, organization_id)` → enriched dict
- `reset()` → clear all state
- `get_conversation_history()` → list of role/content dicts
- `get_provenance_records()` → list of provenance dicts
- `get_current_workflow()` → active workflow name or None
- `get_available_workflows()` → dict of workflow definitions
- `set_device_context(device_version_id, organization_id)` → set context
- `tool_count` → property, returns 18

**Singleton:** `get_regulatory_agent(model_name, temperature)` → cached RegulatoryAgent

### Sprint 4B: Prompts (`src/agents/prompts.py`)

**6 System Prompts:** REGULATORY_AGENT_SYSTEM_PROMPT, HAZARD_ASSESSMENT_PROMPT, COVERAGE_GAP_PROMPT, EVIDENCE_REVIEW_PROMPT, READINESS_SUMMARY_PROMPT, DEVICE_ANALYSIS_PROMPT

**6 Structured Output Schemas:** RegulatoryAnalysisResponse, HazardAssessmentResponse, CoverageGapInterpretation, EvidenceReviewResponse, ReadinessSummaryResponse, AIProvenance — all with `@field_validator` rejecting forbidden words.

**Language Safety:** `FORBIDDEN_WORDS` (14), `APPROVED_REPLACEMENTS` (14), `check_forbidden_words()`, `sanitize_ai_output()`, `validate_regulatory_language()`

**Prompt Router:** `get_prompt_for_task()`, `get_available_task_types()`, `build_contextualized_prompt()`

**AI Provenance:** `compute_hash()`, `create_ai_provenance()`, `provenance_to_db_dict()`

### Sprint 4A: 13 Agent Tools (`src/agents/regulatory_twin_tools.py`)

**Traceability (4):** create_trace_link, get_trace_chain, get_coverage_report, validate_trace_relationship
**Evidence (3):** ingest_evidence, get_evidence_for_device, find_unlinked_evidence
**Attestation (3):** create_attestation, get_pending_attestations, get_attestation_trail
**Gap/Readiness (3):** run_gap_analysis, get_critical_gaps, get_readiness_assessment

All wrapped in `_safe_call()`. Exported as `REGULATORY_TWIN_TOOLS` list. Total: 18 tools (13 new + 5 original).

---

## NEXT: SPRINT 5 — STREAMLIT UI + SUBMISSION READINESS DASHBOARD

Per MASTER_SPRINT_PLAN_v2.md:

**Goal:** Operational dashboard showing risk coverage, trace completeness, evidence strength, unresolved gaps. Agent chat interface. Per architecture: "Make it operational. Not decorative."

### Suggested Sub-Sprint Breakdown

| Sub-Sprint | Deliverable | Estimated Tests |
|------------|-------------|-----------------|
| **5A** | Readiness Dashboard — risk coverage, trace completeness, evidence strength, gap findings, readiness score | ~15 |
| **5B** | Regulatory Twin Management UI — device CRUD, claim/hazard/control/test management, evidence upload + linking, attestation workflow | ~15 |
| **5C** | Agent Chat Interface — conversational agent in Streamlit, tool execution visible, AI provenance display | ~10 |

### Sprint 5 Exit Criteria (from master plan)

- [ ] Operational readiness dashboard
- [ ] Regulatory twin management UI
- [ ] Agent chat interface
- [ ] 800+ total tests passing (we're already at 921)
- [ ] Checkpoint created with MST timestamp
- [ ] Committed to main

### Key Considerations for Sprint 5

1. **Streamlit app entry point:** `src/ui/app.py` (referenced in `src/cli.py` under the `ui` command)
2. **All backend services are ready** — gap engine, readiness, traceability, evidence, attestation, agent — all have singleton accessors (`get_*()`)
3. **API endpoints exist** — 23 endpoints available; UI can call them or use services directly
4. **Agent chat** — `RegulatoryAgent.chat()` and `.chat_with_context()` are the entry points
5. **Testing Streamlit:** Use `pytest` with mocked Streamlit state (`st.session_state`). Streamlit testing patterns needed.
6. **No real LLM calls in tests** — mock the agent for UI tests
7. **Regulatory-safe language** — UI must never display forbidden words. Sanitization happens at agent level, but verify in UI tests too.

---

## REGULATORY CHAIN (enforced by VALID_RELATIONSHIPS)

```
claim -[addresses]-> hazard -[causes/may_cause]-> harm
hazard -[mitigated_by]-> risk_control -[verified_by]-> verification_test
risk_control -[validated_by]-> validation_test
verification_test -[supported_by]-> evidence_item
validation_test -[supported_by]-> evidence_item
claim -[supported_by]-> evidence_item
```

---

## DB TABLES (19 total, unchanged since Sprint 1)

organizations, users, products, device_versions, ai_runs, trace_links, artifacts, attestations, artifact_links, intended_uses, claims, hazards, harms, risk_controls, verification_tests, validation_tests, evidence_items, labeling_assets, submission_targets

**Local Postgres schema quirks:**
- organizations: (id, name, created_at) — NO slug column
- users: NO email/full_name columns
- products: uses `org_id` NOT `organization_id`
- device_versions: has NO `organization_id` column

---

## WORKING RULES (NON-NEGOTIABLE)

1. After ANY code change, run FULL test suite (unit + integration + API + e2e + regulatory). Senior dev + senior tester rigor. Never skip.
2. Give bash commands to paste in terminal. Step by step, one at a time.
3. Mountain Time (Edmonton) timestamps on all checkpoints.
4. Create checkpoint docs after each sub-sprint.
5. No yes-manship — if something's wrong, say so.
6. Read project files (MASTER_SPRINT_PLAN_v2.md, ARCHITECTURE.md, REPO_MAP.md) before writing code.
7. For long files, create downloadable files — heredocs truncate in terminal.
8. Regulatory-safe language: NEVER "compliant", "ready", "will pass". ALWAYS "readiness assessment based on configured expectations."
9. AI provenance: every AI output → ai_runs table before display.
10. User's name is Raj (Rajbir). Never call him Moin.
11. Use simple, conversational, non-technical language with Raj.
12. Always activate venv: `source venv/bin/activate`
13. Unused variables: ruff F841 catches these. Don't assign to `result` unless you assert on it.

---

## CUMULATIVE MILESTONE TRACKER

| Metric | S1 | S2 | S3a | S3b | S3c | S4A | S4B | S4C | S4D |
|--------|----|----|-----|-----|-----|-----|-----|-----|-----|
| Commit | f19051c | 6f8853f | c541059 | 43f9038 | 810b002 | 3912245 | (prev) | fb3ba0d | 172b35c |
| Service classes | 3 | 6 | 7 | 8 | 8 | 8 | 8 | 8 | 8 |
| API endpoints | 6 | 19 | 19 | 19 | 23 | 23 | 23 | 23 | 23 |
| Agent tools | 5 | 5 | 5 | 5 | 5 | 18 | 18 | 18 | 18 |
| Gap rules | 0 | 0 | 12 | 12 | 12 | 12 | 12 | 12 | 12 |
| System prompts | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 6 | 6 |
| Structured schemas | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 6 | 6 |
| Workflows | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 4 |
| Integration tests | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 33 |
| Total tests | 410 | 549 | 627 | 699 | 732 | 780 | 847 | 888 | 921 |

---

*End of handoff prompt. Begin by reading MASTER_SPRINT_PLAN_v2.md, then proceed to Sprint 5A.*
