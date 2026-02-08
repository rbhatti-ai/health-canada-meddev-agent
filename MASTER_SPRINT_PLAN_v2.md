# MASTER SPRINT PLAN v2 — Rigour Medtech Regulatory Platform

> **Revised:** 2026-02-07 19:45 MST (Mountain Time — Edmonton)
> **Revision reason:** Sprint 3 was incorrectly redefined as "AI Agent Layer" in the handoff document (HANDOFF_SPRINT3.md). The original SPRINT_PLAN.md and the governing architecture (`REGULATORY_EXECUTION_PLATFORM_ARCHITECTURE.md`) both specify the correct order: **Structure first, AI second.** Gap Detection Engine is deterministic structure — it belongs before the AI Agent Layer. This revision corrects the ordering.
> **Governing doc:** `docs/architecture/REGULATORY_EXECUTION_PLATFORM_ARCHITECTURE.md`
> **Priority order (from architecture):** Regulatory Twin → Traceability → Gap Detection → AI Agent → Dashboard → Document Generation → Deficiency Copilot
> **Repo:** rbhatti-ai/health-canada-meddev-agent (private, GitHub)
> **Tech:** Python 3.11, FastAPI, Streamlit, LangGraph, ChromaDB/Pinecone, Anthropic Claude, OpenAI embeddings, local Postgres (dev), Supabase (prod)

---

## ⚠️ INSTRUCTIONS FOR FUTURE AI SESSIONS (Claude, Claude Code, etc.)

**READ THIS FIRST.** This is the single source of truth for sprint planning.

1. Do NOT rely on `HANDOFF_SPRINT3.md` for sprint ordering — it contains an error (see revision reason above).
2. The original `SPRINT_PLAN.md` had the correct Sprint 3 (Gap Detection) but is now outdated because Sprints 1 and 2 are complete.
3. **This document supersedes both.** Follow this plan.
4. After ANY code change, run full test suite. Never skip tests.
5. Give bash commands to paste in terminal or Claude Code. Step by step, one at a time.
6. Create checkpoints with Mountain Time (Edmonton) timestamps after each sub-sprint.
7. Regulatory-grade practices: traceable, auditable, legally defensible. No shortcuts.
8. Senior developer + senior tester rigor.
9. For long files, create downloadable files instead of heredocs (heredocs truncate in terminal).

---

## CURRENT STATE (as of 2026-02-07 19:45 MST)

- **Branch:** main
- **Latest commit:** `6f8853f` (Sprint 2d complete)
- **Tests:** 549/549 passing (4.40s runtime)
- **Pre-commit hooks:** black, isort, ruff, mypy (scoped to src/core + src/persistence), pytest-unit, pytest-regulatory
- **DB tables:** 19 total
- **API endpoints:** 13 (Sprint 2 traceability routes) + existing classification/pathway/search endpoints

---

## COMPLETED SPRINTS

### ✅ Sprint 1 (commit f19051c) — Regulatory Twin Foundation

**Completed:** 2026-02-07
**Tests at exit:** 410

**What was delivered:**
- 10 new DB tables: intended_uses, claims, hazards, harms, risk_controls, verification_tests, validation_tests, evidence_items, labeling_assets, submission_targets
- Pydantic models with Literal types for enums in `src/core/regulatory_twin.py`
- TwinRepository in `src/persistence/twin_repository.py`: dual Supabase/local Postgres, best-effort persistence
- RLS policies, CHECK constraints, versioning support (version + supersedes_id pattern)
- Sub-sprints: 1a (DB migration), 1b (Pydantic models), 1c (persistence layer)

---

### ✅ Sprint 2 (commits 775b72a → 6f8853f) — Traceability, Evidence & Attestation

**Completed:** 2026-02-07
**Tests at exit:** 549

**What was delivered:**
- **2a:** `src/core/traceability.py` — TraceabilityEngine: link validation, chain traversal, coverage reports (60 tests)
- **2b:** `src/core/evidence_ingestion.py` — EvidenceIngestionService: ingest artifact+evidence+link, bulk, unlinked detection (25 tests)
- **2c:** `src/core/attestation_service.py` — AttestationService: human sign-off, audit trail, 4 types (reviewed/approved/rejected/acknowledged) (35 tests)
- **2d:** `src/api/traceability_routes.py` — 13 FastAPI endpoints under /api/v1/ (19 tests)

**Regulatory chain enforced by VALID_RELATIONSHIPS:**
```
claim -[addresses]-> hazard -[causes/may_cause]-> harm
hazard -[mitigated_by]-> risk_control -[verified_by]-> verification_test
risk_control -[validated_by]-> validation_test
verification_test -[supported_by]-> evidence_item
validation_test -[supported_by]-> evidence_item
claim -[supported_by]-> evidence_item
```

---

## UPCOMING SPRINTS

### 🔲 Sprint 3 — GAP DETECTION ENGINE + READINESS ASSESSMENT

**Status:** NOT STARTED
**Goal:** The highest-value feature. Deterministic, rules-based engine that surfaces what's missing, weak, or inconsistent. Per architecture: "Never say 'You are submission ready.' Always say 'Readiness assessment based on configured expectations.'"
**Why this comes before AI:** This is pure structure — versioned, deterministic rules. No AI dependency. The architecture is explicit: "Structure first, AI second." The AI agent layer (Sprint 4) becomes dramatically more valuable when it can invoke the gap engine.

#### Deliverable 3A: Gap Detection Rules Engine

**File:** `src/core/gap_engine.py`

```python
class GapDetectionEngine:
    """
    Rules-based engine that evaluates regulatory readiness.
    Rules are versioned, deterministic, and explainable.
    Each rule produces a GapFinding with severity, description, and remediation.
    """

    def evaluate(self, device_version_id) -> GapReport:
        """Run all rules against a device version."""

    def evaluate_rule(self, rule_id, device_version_id) -> List[GapFinding]:
        """Run a single rule."""

    def get_rules(self) -> List[GapRule]:
        """List all active rules with descriptions."""


class GapRule:
    """A single detection rule. Deterministic. Explainable."""
    id: str
    name: str
    description: str
    severity: str          # critical, major, minor, info
    category: str          # coverage, completeness, consistency, evidence_strength
    version: int
    evaluate: Callable     # returns List[GapFinding]
```

**Initial rule set (12 rules, Health Canada focus):**

| Rule ID | Name | What it checks | Severity |
|---------|------|---------------|----------|
| GAP-001 | Unmitigated hazards | Hazards with no linked risk_control | CRITICAL |
| GAP-002 | Unverified controls | Risk controls with no linked verification_test | CRITICAL |
| GAP-003 | Unsupported claims | Claims with no linked evidence_item | MAJOR |
| GAP-004 | Missing intended use | Device version with no intended_use record | CRITICAL |
| GAP-005 | Weak evidence | Evidence items with strength = 'weak' or 'insufficient' | MAJOR |
| GAP-006 | Untested claims | Claims with no linked verification OR validation test | MAJOR |
| GAP-007 | No submission target | Device version with no submission_target | MINOR |
| GAP-008 | Unattested AI outputs | ai_runs linked to artifacts but not attested | MAJOR |
| GAP-009 | Missing labeling | Device version with no labeling_assets | MAJOR |
| GAP-010 | Incomplete risk chain | Hazard → harm → control chain has breaks | CRITICAL |
| GAP-011 | Draft evidence only | All evidence_items in 'draft' status | MAJOR |
| GAP-012 | No clinical evidence (III/IV) | Class III/IV with no clinical evidence type | CRITICAL |

#### Deliverable 3B: Readiness Assessment

**File:** `src/core/readiness.py`

```python
class ReadinessAssessment:
    """
    Aggregates gap findings into a readiness score.
    NEVER says "compliant" or "ready."
    ALWAYS says "Readiness assessment based on configured expectations."
    """

    def assess(self, device_version_id) -> ReadinessReport:
        """
        Returns:
        - overall_readiness_score: float (0.0 - 1.0)
        - category_scores: dict[str, float]
        - gap_findings: List[GapFinding]
        - critical_blockers: List[GapFinding]
        - summary: str  (regulatory-safe language)
        """

    def generate_summary(self, report: ReadinessReport) -> str:
        """
        Generates human-readable summary.
        Uses ONLY approved regulatory language.
        """
```

#### Deliverable 3C: API Endpoints

**File:** `src/api/gap_routes.py`

```
GET  /api/v1/gaps/{device_version_id}         — full gap report
GET  /api/v1/gaps/{device_version_id}/critical — critical gaps only
GET  /api/v1/readiness/{device_version_id}     — readiness assessment
GET  /api/v1/rules                             — list all gap rules
```

#### Deliverable 3D: Tests

**Files:**
- `tests/unit/test_gap_engine.py` — each rule individually tested (50+ tests)
- `tests/unit/test_readiness.py` — scoring, language safety (20+ tests)
- `tests/regulatory/test_gap_rules.py` — regulatory correctness of rules (15+ tests)
- `tests/integration/test_gap_detection_flow.py` — end-to-end (10+ tests)
- `tests/api/test_gap_endpoints.py` — API route tests (10+ tests)

#### Sprint 3 Sub-Sprint Breakdown

| Sub-Sprint | Deliverable | Estimated Tests |
|------------|-------------|-----------------|
| **3a** | GapDetectionEngine + Pydantic models (GapRule, GapFinding, GapReport) + 12 rules | ~65 |
| **3b** | ReadinessAssessment + ReadinessReport + regulatory-safe language enforcement | ~20 |
| **3c** | API endpoints (gap_routes.py) + integration with FastAPI app | ~20 |

#### Sprint 3 Exit Criteria

- [ ] 12 gap detection rules implemented and tested
- [ ] Each rule produces explainable findings with severity
- [ ] Readiness assessment with category scores
- [ ] ALL output uses regulatory-safe language (no "compliant", no "ready")
- [ ] API endpoints for gaps, readiness, rules
- [ ] 650+ total tests passing
- [ ] Checkpoint created with MST timestamp
- [ ] Committed to main

---

### 🔲 Sprint 4 — AI AGENT LAYER

**Status:** NOT STARTED
**Goal:** LangGraph tools that wrap ALL existing services (traceability, evidence, attestation, AND gap detection). Regulatory analysis prompts with structured output. Multi-step agent orchestration.
**Why this comes after Gap Engine:** The agent is dramatically more useful when it can invoke gap detection and readiness assessment — not just create links and ingest evidence.

#### Deliverable 4A: Agent Tool Definitions

**File:** `src/agents/regulatory_twin_tools.py`

New LangGraph-compatible tools wrapping Sprint 2 + Sprint 3 services:

**TraceabilityEngine tools (4):**
1. `create_trace_link` — Create a regulatory trace link between entities
2. `get_trace_chain` — Get full chain from claim down to evidence
3. `get_coverage_report` — Coverage report for a device version
4. `validate_trace_relationship` — Check if a link type is valid

**EvidenceIngestionService tools (2):**
5. `ingest_evidence` — Ingest evidence item with artifact + link
6. `find_unlinked_evidence` — Find orphaned evidence items

**AttestationService tools (3):**
7. `create_attestation` — Human sign-off on artifact
8. `get_pending_attestations` — Unattested items for an org
9. `get_attestation_trail` — Audit trail for an artifact

**GapDetectionEngine tools (3):**
10. `run_gap_analysis` — Full gap report for a device version
11. `get_critical_gaps` — Critical blockers only
12. `get_readiness_assessment` — Readiness score + summary

#### Deliverable 4B: Regulatory Analysis Prompts + Structured Output

**File:** `src/agents/prompts.py`

- System prompts for regulatory analysis (hazard assessment, coverage gap interpretation)
- Structured output schemas (Pydantic models for agent responses)
- Regulatory-safe language enforcement in all AI outputs
- AI provenance logging (every AI output → ai_runs table)

#### Deliverable 4C: Agent Orchestration

**File:** `src/agents/regulatory_agent.py` (refactor existing)

- Multi-step workflows: "Analyze my device" → classify → trace → gap analysis → readiness
- LangGraph StateGraph with conditional routing
- Tool-calling with Claude/OpenAI
- Conversation memory

#### Deliverable 4D: Tests

**Files:**
- `tests/unit/test_regulatory_twin_tools.py` — tool input/output validation (~40 tests)
- `tests/unit/test_prompts.py` — prompt construction, language safety (~15 tests)
- `tests/unit/test_agent_orchestration.py` — workflow routing, state transitions (~20 tests)
- `tests/integration/test_agent_flow.py` — end-to-end agent conversations (~10 tests)

#### Sprint 4 Exit Criteria

- [ ] 12 new agent tools wrapping all services
- [ ] Regulatory analysis prompts with structured output
- [ ] Agent orchestration with multi-step workflows
- [ ] ALL AI outputs logged to ai_runs table
- [ ] ALL AI outputs use regulatory-safe language
- [ ] 740+ total tests passing
- [ ] Checkpoint created with MST timestamp
- [ ] Committed to main

---

### 🔲 Sprint 5 — STREAMLIT UI + SUBMISSION READINESS DASHBOARD

**Status:** NOT STARTED
**Goal:** Operational dashboard showing risk coverage, trace completeness, evidence strength, unresolved gaps. Agent chat interface. Per architecture: "Make it operational. Not decorative."

#### Deliverable 5A: Readiness Dashboard

- Risk coverage visualization
- Trace completeness display
- Evidence strength indicators
- Gap findings with drill-down
- Readiness score display

#### Deliverable 5B: Regulatory Twin Management UI

- Device version CRUD
- Claim/hazard/control/test management
- Evidence upload + linking
- Attestation workflow UI

#### Deliverable 5C: Agent Chat Interface

- Conversational agent embedded in Streamlit
- Tool execution visible to user
- AI provenance display

#### Sprint 5 Exit Criteria

- [ ] Operational readiness dashboard
- [ ] Regulatory twin management UI
- [ ] Agent chat interface
- [ ] 800+ total tests passing
- [ ] Checkpoint created with MST timestamp
- [ ] Committed to main

---

## DEFERRED (Phase 4-5 per architecture)

These are explicitly excluded from Sprints 3-5 and will be planned separately:

| Feature | Architecture Phase | Reason for Deferral |
|---------|-------------------|---------------------|
| Document Orchestration | Phase 4 | Needs structured data + gap engine first |
| Deficiency Response Copilot | Phase 5 | High value but requires all prior layers |
| Regulatory Knowledge Graph | Future moat | "Do not rush it" per architecture |
| S3 signed URL document storage | Infrastructure | Needed for production, not dev |
| Real multi-tenancy testing | Infrastructure | Requires Supabase cloud deployment |
| AI-assisted link recommendations | AI feature | Needs agent layer + gap engine first |

---

## CUMULATIVE MILESTONE TRACKER

| Metric | Baseline | Sprint 1 ✅ | Sprint 2 ✅ | Sprint 3 | Sprint 4 | Sprint 5 |
|--------|----------|-------------|-------------|----------|----------|----------|
| DB tables | 9 | 19 | 19 | 19 | 19 | 19 |
| Python models | 6 | 16 | 16 | 18+ | 18+ | 18+ |
| Service classes | 2 | 3 | 6 | 8 | 8+ | 8+ |
| API endpoints | 6 | 6 | 19 | 23 | 23+ | 23+ |
| Agent tools | 5 | 5 | 5 | 5 | 17 | 17 |
| Gap rules | 0 | 0 | 0 | 12 | 12 | 12 |
| Total tests | 157 | 410 | 549 | 650+ | 740+ | 800+ |
| Trace link types | 0 | 0 | 9 | 9 | 9 | 9 |

---

## KEY FILES (current as of Sprint 2 completion)

```
src/core/traceability.py            — TraceabilityEngine (singleton)
src/core/evidence_ingestion.py      — EvidenceIngestionService (singleton)
src/core/attestation_service.py     — AttestationService (singleton)
src/core/regulatory_twin.py         — Pydantic models for all 10 entity types
src/persistence/twin_repository.py  — Dual-backend persistence (Supabase + local Postgres)
src/api/main.py                     — FastAPI app with CORS, lifespan
src/api/traceability_routes.py      — Sprint 2 API routes (13 endpoints)
src/agents/regulatory_agent.py      — RegulatoryAgent + SimpleRegulatoryAgent
src/agents/tools.py                 — 5 existing agent tools (classify, pathway, checklist, search, fees)
configs/settings.py                 — App settings
```

**Sprint 3 will add:**
```
src/core/gap_engine.py              — GapDetectionEngine + 12 rules
src/core/readiness.py               — ReadinessAssessment
src/api/gap_routes.py               — Gap/readiness API endpoints
```

**Sprint 4 will add:**
```
src/agents/regulatory_twin_tools.py — 12 new agent tools
src/agents/prompts.py               — Regulatory analysis prompts
```

---

## DB TABLES (19 total, unchanged since Sprint 1)

organizations, users, products, device_versions, ai_runs, trace_links, artifacts, attestations, artifact_links, intended_uses, claims, hazards, harms, risk_controls, verification_tests, validation_tests, evidence_items, labeling_assets, submission_targets

## LOCAL POSTGRES SCHEMA QUIRKS

- organizations: (id, name, created_at) — NO slug column
- users: NO email/full_name columns
- products: uses org_id NOT organization_id
- device_versions: has NO organization_id column

---

## PATTERNS TO FOLLOW (all sprints)

- Best-effort persistence (never crash on DB failure)
- Singleton via get_*() functions
- Pydantic models with Literal types for enums
- to_db_dict() excludes id/created_at, converts UUIDs to strings
- from_db_row() ignores extra fields
- Tests: class-based, descriptive names, no DB required for unit tests
- Pre-commit hooks must all pass before commit
- Mountain Time (Edmonton) timestamps on all checkpoints
- Regulatory-safe language: NEVER "compliant", "ready", "will pass"
- AI provenance: every AI output → ai_runs table before display

---

## RISK REGISTER

| Risk | Impact | Mitigation |
|------|--------|------------|
| Schema changes break existing tests | HIGH | All migrations idempotent, run full suite before and after |
| Gap rules too rigid | LOW | Version rules, allow disable/enable per org |
| No real multi-user testing | HIGH | Supabase cloud deployment before Sprint 5 |
| AI agent producing unsafe language | HIGH | Regulatory-safe language checks in tests + prompts |
| Sprint ordering confusion (this incident) | MEDIUM | This master plan is the single source of truth |
| Handoff docs diverging from plan | MEDIUM | Always update THIS file, generate handoffs FROM it |

---

## TECH DEBT

| Item | Priority | When |
|------|----------|------|
| mypy errors (ongoing) | MEDIUM | Fix progressively per sprint |
| Supabase cloud deployment | HIGH | Before Sprint 5 (need real auth for RLS testing) |
| S3 document storage | MEDIUM | Before Document Orchestration phase |
| Pre-commit mypy enforcement | LOW | After mypy errors resolved |

---

## CHANGE LOG

| Date (MST) | Change | Reason |
|------------|--------|--------|
| 2026-02-06 18:25 | Original SPRINT_PLAN.md created | Initial 3-sprint plan |
| 2026-02-07 18:00 | HANDOFF_SPRINT3.md created | Handoff for new session — **incorrectly redefined Sprint 3 as AI Agent Layer** |
| 2026-02-07 19:45 | **MASTER_SPRINT_PLAN_v2.md created (THIS FILE)** | Corrected sprint ordering. Gap Engine restored to Sprint 3. AI Agent Layer moved to Sprint 4. Streamlit UI moved to Sprint 5. Added deferred items. This is now the single source of truth. |

---

*End of master sprint plan v2*
