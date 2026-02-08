# CLAUDE.md — AUTONOMOUS AGENT OPERATING DIRECTIVE

> **Last updated:** 2026-02-07 23:30 MST (Mountain Time — Edmonton)
> **Owner:** Raj (Rajbir) — rbhatti-ai
> **Governing plan:** MASTER_SPRINT_PLAN_v3.md (supersedes v2)
> **Architecture doc:** docs/architecture/REGULATORY_EXECUTION_PLATFORM_ARCHITECTURE.md

---

## ⚠️ READ THIS ENTIRE FILE BEFORE ANY WORK

This file is your single source of truth. It contains everything you need to execute sprints autonomously. Do not ask Raj for permission on routine operations — just execute.

---

## SECTION 1: PLATFORM IDENTITY

**Rigour Medtech** — AI-powered regulatory compliance platform for medical device manufacturers navigating Health Canada and FDA submissions.

This is **Regulatory Execution Infrastructure.**
NOT a chatbot. NOT a template generator. NOT an AI gimmick.

Optimize for: auditability, traceability, explainability, regulatory defensibility, security.
Over speed. Over cleverness. Over novelty.

**Target client:** Senior cardiologist-entrepreneur with 20 years medical education, research/IP expertise, QMS proficiency, building cardiac medical devices (Class III/IV or SaMD).

**Tech stack:** Python 3.11+, FastAPI, Streamlit, LangGraph agents, ChromaDB/Pinecone RAG, Anthropic Claude, OpenAI embeddings, local Postgres (dev), Supabase (prod).

---

## SECTION 2: AUTONOMOUS EXECUTION PERMISSIONS

You have standing permission to:

1. **Create, modify, and delete files** in the codebase
2. **Run all tests** (unit, integration, API, e2e, regulatory) after every change
3. **Run linters and formatters** (black, isort, ruff, mypy) after every change
4. **Commit to local git** with descriptive commit messages after each sub-sprint
5. **Push to GitHub** (`git push origin main`) after each sub-sprint
6. **Create checkpoint documents** after each sub-sprint
7. **Proceed to the next sub-sprint** automatically when the current one passes all tests
8. **Install Python packages** using `pip install --break-system-packages` if needed
9. **Read any file** in the repo for context

**DO NOT ask Raj for permission to:**
- Run tests
- Commit code
- Push to GitHub
- Move to the next sub-sprint
- Create checkpoint files
- Fix linter errors

**DO ask Raj before:**
- Changing the database schema in ways not specified in MASTER_SPRINT_PLAN_v3.md
- Deleting or fundamentally restructuring existing working code
- Deviating from the sprint plan
- Any decision that feels architecturally significant and isn't covered by the plan

---

## SECTION 3: ENVIRONMENT SETUP

```bash
# ALWAYS run these first in every session
cd ~/health-canada-meddev-agent
source venv/bin/activate

# Use python3, not python
python3 --version

# Verify current state
git status
git log --oneline -5
```

**Repo:** `~/health-canada-meddev-agent`
**venv:** `~/health-canada-meddev-agent/venv/` — ALWAYS activate before any work
**Python:** Use `python3` (not `python`)
**Branch:** `main` (all work on main)

---

## SECTION 4: CURRENT STATE (as of Sprint 4D completion)

- **Latest commit:** 172b35c (Sprint 4D complete — Sprint 4 FULLY COMPLETE)
- **Tests:** 921/921 passing (14.38s runtime)
- **Pre-commit hooks:** black, isort, ruff, mypy (scoped), pytest-unit, pytest-regulatory — all 13 passing

### Completed Sprints

| Sprint | Commit | Tests | What Was Delivered |
|--------|--------|-------|--------------------|
| 1 | f19051c | 410 | 10 DB tables, Pydantic models, TwinRepository |
| 2 | 6f8853f | 549 | TraceabilityEngine, EvidenceIngestion, Attestation, 13 API endpoints |
| 3a | c541059 | 627 | GapDetectionEngine, 12 rules (GAP-001 to GAP-012) |
| 3b | 43f9038 | 699 | ReadinessAssessment, penalty scoring, language safety |
| 3c | 810b002 | 732 | Gap/Readiness API endpoints (4 new) |
| 4A | 3912245 | 780 | 13 LangGraph agent tools, REGULATORY_TWIN_TOOLS |
| 4B | (prev) | 847 | 6 system prompts, 6 structured schemas, AI provenance |
| 4C | fb3ba0d | 888 | Agent orchestration: LangGraph StateGraph, 4 workflows |
| 4D | 172b35c | 921 | 33 agent integration tests |

### Current Capabilities

- 8 service classes (all singletons via `get_*()`)
- 23 API endpoints
- 18 agent tools (13 new + 5 original)
- 12 gap detection rules (GAP-001 to GAP-012)
- 6 system prompts + 6 structured output schemas
- 4 named workflows
- 14 forbidden words (language safety)
- AI provenance logging
- 19 database tables

---

## SECTION 5: TESTING PROTOCOL (NON-NEGOTIABLE)

After **ANY** code change — even a one-line fix — run the FULL test suite:

```bash
# Full test suite (run this after EVERY change)
cd ~/health-canada-meddev-agent
source venv/bin/activate

# Step 1: Linters and formatters
python3 -m black src/ tests/ --check
python3 -m isort src/ tests/ --check-only
python3 -m ruff check src/ tests/
python3 -m mypy src/agents/ --ignore-missing-imports

# Step 2: Full test suite
python3 -m pytest tests/ -v --tb=short 2>&1 | tail -30

# Step 3: Verify count
python3 -m pytest tests/ --co -q 2>&1 | tail -5
```

**Rules:**
- NEVER skip tests. NEVER proceed with failing tests.
- If a test fails, fix it before doing anything else.
- If you broke an existing test, that's a critical bug — fix immediately.
- New code must be additive — never break the existing 921+ tests.
- Run linters BEFORE committing. Fix all linter errors.

### Quick fix commands for common linter issues:

```bash
# Auto-fix formatting
python3 -m black src/ tests/
python3 -m isort src/ tests/
python3 -m ruff check src/ tests/ --fix
```

---

## SECTION 6: GIT AND COMMIT PROTOCOL

### After each sub-sprint passes all tests:

```bash
# Stage all changes
git add -A

# Commit with descriptive message
git commit -m "Sprint XY: [brief description]

- [bullet 1: what was added]
- [bullet 2: what was modified]
- [bullet 3: test count]
- All tests passing: NNN/NNN
- Linters clean: black, isort, ruff, mypy"

# Push to GitHub
git push origin main
```

### Commit message format:

```
Sprint 5A: RegulatoryReferenceRegistry with 50+ pre-loaded references

- Added src/core/regulatory_references.py (RegulatoryReference model + Registry)
- Pre-populated 50+ Health Canada regulatory references
- Added tests/unit/test_regulatory_references.py (~30 tests)
- All tests passing: 951/951
- Linters clean: black, isort, ruff, mypy
```

---

## SECTION 7: CHECKPOINT PROTOCOL

After each sub-sprint, create a checkpoint file:

**File:** `docs/checkpoints/CHECKPOINT_S{sprint}{sub}.md`
**Example:** `docs/checkpoints/CHECKPOINT_S5A.md`

```markdown
# CHECKPOINT — Sprint 5A: Regulatory Reference Registry

> **Timestamp:** 2026-02-XX HH:MM MST (Mountain Time — Edmonton)
> **Commit:** [hash]
> **Branch:** main
> **Tests:** NNN/NNN passing

## What Was Delivered
- [list deliverables]

## Files Created/Modified
- [list files with brief description]

## Test Summary
- New tests added: NN
- Total tests: NNN
- All passing: YES/NO
- Linter status: CLEAN/[issues]

## Known Issues
- [any issues or none]

## Next Step
- Sprint [next sub-sprint]: [description]
```

Also update MASTER_SPRINT_PLAN_v3.md cumulative tracker after each sub-sprint.

---

## SECTION 8: CRITICAL API PATTERNS (BUGS HAPPEN WITHOUT THESE)

These patterns caused repeated bugs in earlier sprints. Follow them EXACTLY:

1. **TwinRepository** — Generic methods ONLY: `get_by_device_version(table, dvid)`, `get_by_id(table, id)`, `get_by_field(table, field, value)`, `get_by_org(table, org_id)`, `create(table, data)`, `update(table, id, data)`, `count(table)`. Returns `list[dict]`. NO entity-specific methods.

2. **TraceLink** — Pydantic model. Use `.source_type`, `.target_type` (attribute access), NOT `.get()` dict style.

3. **Logger import:** `from src.utils.logging import get_logger` (NOT `src.utils.logger`)

4. **ruff B017:** Never `pytest.raises(Exception)` — always use specific exception types.

5. **ruff B904:** Always `raise HTTPException(...) from e` or `from None` in except blocks.

6. **ruff modern style:** Use `list[str]` not `List[str]`, `dict[str, Any]` not `Dict[str, Any]`, `str | None` not `Optional[str]`.

7. **mypy:** All functions in `src/agents/` need return type annotations. Watch `str | None` vs `str` — use `value or ""` pattern.

8. **Tests:** Class-based, descriptive names, no DB required for unit tests. Use `SimpleNamespace` via `make_link()`/`make_finding()` helpers.

9. **Regulatory-safe language:** NEVER "compliant", "ready", "will pass", "guaranteed", "approved", "certified". ALWAYS "readiness assessment based on configured expectations."

10. **AI provenance:** Every AI output → `ai_runs` table BEFORE display.

11. **For long files:** Write files to disk, don't use heredocs (they truncate).

12. **ToolNode + mocks:** When mocking tools for `RegulatoryAgent` tests, MUST also mock `_build_graph` via `patch.object(RegulatoryAgent, "_build_graph")` because `ToolNode` rejects `MagicMock` objects.

13. **Unused variables in tests:** ruff F841 catches unused `result = ...`. Either assert on it or call the method directly.

14. **Never fabricate regulatory information.** Do NOT invent requirements, standards, pathways, citations. If unsure, label: "Citation required — verify with Health Canada."

---

## SECTION 9: FILE INVENTORY

### Core Services (8 classes, all singletons via `get_*()`)

```
src/core/traceability.py            — TraceabilityEngine
src/core/evidence_ingestion.py      — EvidenceIngestionService
src/core/attestation_service.py     — AttestationService
src/core/gap_engine.py              — GapDetectionEngine (12 rules)
src/core/readiness.py               — ReadinessAssessment
src/core/regulatory_twin.py         — Pydantic models (10 entity types)
src/core/classification.py          — Device classification engine
src/persistence/twin_repository.py  — Dual-backend persistence
```

### Agent Layer

```
src/agents/tools.py                 — 5 original tools
src/agents/regulatory_twin_tools.py — 13 new tools, _safe_call wrapper
src/agents/prompts.py               — 6 system prompts, 6 schemas, language safety
src/agents/regulatory_agent.py      — RegulatoryAgent (LangGraph orchestration)
src/agents/__init__.py              — All exports
```

### API Layer (23 endpoints)

```
src/api/main.py                     — FastAPI app
src/api/traceability_routes.py      — 13 endpoints
src/api/gap_routes.py               — 4 endpoints
+ 6 original endpoints
```

### Tests (921 total)

```
tests/unit/                         — Unit tests (gap, readiness, traceability, models, prompts, tools, orchestration)
tests/integration/                  — Integration tests (agent flow)
tests/api/                          — API endpoint tests
tests/regulatory/                   — Regulatory correctness tests
```

---

## SECTION 10: SPRINT EXECUTION PLAN

**Governing document:** MASTER_SPRINT_PLAN_v3.md

**Sprint order (from v3):**
- Sprint 5: Citation Infrastructure (P0) ← **CURRENT — START HERE**
- Sprint 6: IP Protection (P0)
- Sprint 7: Clinical Evidence + Predicate (P1)
- Sprint 8: Design Controls (P1)
- Sprint 9: Labeling + Post-Market (P2)
- Sprint 10: Streamlit Dashboard (P2)

### SPRINT 5 — CITATION INFRASTRUCTURE (P0)

**Goal:** Every substantive output includes mandatory regulatory citations.

#### 5A: Regulatory Reference Registry (~30 tests)

**New file:** `src/core/regulatory_references.py`

Create:
- `RegulatoryReference(BaseModel)` — structured citation model with id, reference_type, document_id, section, schedule, title, url, effective_date
- `ReferenceType = Literal["regulation", "guidance", "standard", "form", "internal"]`
- `RegulatoryReferenceRegistry` class with methods: `get_reference()`, `search()`, `get_by_topic()`, `get_classification_rules()`, `get_labeling_requirements()`, `get_clinical_requirements()`, `format_citation()`
- `REGULATION_REFERENCES` dict — 50+ pre-populated entries from KNOWLEDGE_BASE.md

**Pre-populated references (VERIFIED from KNOWLEDGE_BASE.md — do NOT invent others):**

| ID | Document | Type |
|----|----------|------|
| SOR-98-282 | Medical Devices Regulations (SOR/98-282) | regulation |
| GUI-0016 | MDEL Guidance | guidance |
| GUI-0098 | How to Complete MDL Application | guidance |
| GUI-0102 | Clinical Evidence Requirements | guidance |
| GUI-0123 | SaMD Pre-market Guidance | guidance |
| GD210 | ISO 13485 QMS Audits | guidance |
| GD211 | Content of QMS Audit Reports | guidance |
| GD207 | Content of ISO 13485 Certificates | guidance |
| ISO-13485-2016 | Medical Device QMS | standard |
| ISO-14971-2019 | Risk Management | standard |
| IEC-62304-2006 | Medical Device Software | standard |
| FRM-0292 | MDEL Application | form |
| FRM-0077 | Class II MDL | form |
| FRM-0078 | Class III MDL | form |
| FRM-0079 | Class IV MDL | form |

Plus additional section-level references (SOR/98-282 Part 1-6, Schedule 1, specific sections like s.26, s.32, s.21-23, etc.)

**Test file:** `tests/unit/test_regulatory_references.py`

**Exit criteria:**
- [ ] RegulatoryReferenceRegistry with 50+ references
- [ ] All methods working with tests
- [ ] ~951 total tests passing (921 + ~30)
- [ ] Checkpoint created, committed, pushed

#### 5B: Citation-Enabled Gap Findings (~25 tests)

**Modify:** `src/core/gap_engine.py`

Add citation fields to GapFinding model:
- `regulation_section: str | None = None`
- `guidance_document: str | None = None`
- `iso_reference: str | None = None`
- `schedule_rule: str | None = None`
- `form_reference: str | None = None`
- `citation_text: str | None = None`

Update all 12 gap rules with citations:

| Rule | Primary Citation | Secondary |
|------|------------------|-----------|
| GAP-001 | ISO 14971:2019, 7.1 | SOR/98-282, s.10.1 |
| GAP-002 | ISO 14971:2019, 7.2 | ISO 13485:2016, 7.3.6 |
| GAP-003 | SOR/98-282, s.32(4) | — |
| GAP-004 | SOR/98-282, s.32(2)(a) | — |
| GAP-005 | GUI-0102, Section 3.2 | — |
| GAP-006 | ISO 13485:2016, 7.3.6 | — |
| GAP-007 | SOR/98-282, s.26 | — |
| GAP-008 | Platform policy | — |
| GAP-009 | SOR/98-282, Part 5 | GUI-0015 |
| GAP-010 | ISO 14971:2019, 6.1-6.4 | — |
| GAP-011 | GUI-0098, Section 5.1 | — |
| GAP-012 | GUI-0102, Section 4.1 | SOR/98-282, s.32(2)(c) |

**Test file:** `tests/unit/test_gap_citations.py`

**Critical:** All existing gap_engine tests MUST still pass. Additive changes only.

**Exit criteria:**
- [ ] All 12 gap rules have citations
- [ ] Existing tests still pass
- [ ] ~976 total tests passing (951 + ~25)
- [ ] Checkpoint created, committed, pushed

#### 5C: Citation in Agent Outputs (~15 tests)

**Modify:** `src/agents/prompts.py`

Add CITATION REQUIREMENT block to all 6 system prompts:
```
CITATION REQUIREMENT:
Every substantive statement must cite its source.
FORMAT: "[Statement]. [Citation]"
EXAMPLES:
- "Class III devices require clinical evidence. [SOR/98-282, s.32(2)(c)]"
- "Risk controls must be verified. [ISO 14971:2019, 7.2]"
IF NO CITATION AVAILABLE:
- "[Statement]. [Citation required — verify with Health Canada]"
FORBIDDEN:
- Substantive claims without citations
- Invented regulation sections
- Made-up guidance document numbers
```

**Test file:** `tests/unit/test_prompt_citations.py`

**Exit criteria:**
- [ ] All 6 prompts include citation requirements
- [ ] ~991 total tests passing (976 + ~15)
- [ ] Checkpoint created, committed, pushed
- [ ] Sprint 5 complete — proceed to Sprint 6

### SPRINT 6-10: FUTURE SPRINTS

Read MASTER_SPRINT_PLAN_v3.md for full details on Sprints 6-10. After completing Sprint 5, proceed to Sprint 6 (IP Protection) following the same patterns.

---

## SECTION 11: REGULATORY CHAIN

```
claim -[addresses]-> hazard -[causes/may_cause]-> harm
hazard -[mitigated_by]-> risk_control -[verified_by]-> verification_test
risk_control -[validated_by]-> validation_test
verification_test -[supported_by]-> evidence_item
validation_test -[supported_by]-> evidence_item
claim -[supported_by]-> evidence_item
```

---

## SECTION 12: DATABASE (19 tables)

organizations, users, products, device_versions, ai_runs, trace_links, artifacts, attestations, artifact_links, intended_uses, claims, hazards, harms, risk_controls, verification_tests, validation_tests, evidence_items, labeling_assets, submission_targets

**Local Postgres quirks:**
- organizations: (id, name, created_at) — NO slug column
- users: NO email/full_name columns
- products: uses `org_id` NOT `organization_id`
- device_versions: has NO `organization_id` column

---

## SECTION 13: LANGUAGE SAFETY

**FORBIDDEN words (never output these):**
compliant, compliance, ready, certified, approved, guaranteed, ensures, will pass, fully meets, certify, warrant, assure, verify (as absolute), confirm (as absolute)

**APPROVED replacements:**
"readiness assessment based on configured expectations", "potential gaps detected", "draft for professional review", "alignment assessment", "coverage analysis"

---

## SECTION 14: ENGINEERING PHILOSOPHY

- Move deliberately. Favor durability over speed.
- Structure first, AI second. AI operates ON structured data.
- Additive changes. Don't break existing functionality.
- Version everything. Audit trails are infrastructure.
- Human-in-the-loop required. No AI output is final without human approval.
- Every meaningful output answers: Why? What triggered it? What data? What confidence?
- When uncertain, favor systems that strengthen: Claim → Risk → Control → Verification → Evidence linking.

---

## SECTION 15: WORKFLOW SUMMARY

**For each sub-sprint, do this in order:**

1. Read the relevant section of MASTER_SPRINT_PLAN_v3.md
2. Read existing source files you'll modify
3. Write the code (new files or modifications)
4. Run linters: `black`, `isort`, `ruff check --fix`, `mypy`
5. Write tests
6. Run FULL test suite (all tests, not just new ones)
7. Fix any failures
8. Commit with descriptive message
9. Push to GitHub
10. Create checkpoint document
11. Proceed to next sub-sprint

**Repeat until sprint is complete.**

---

## CHANGE LOG

| Date (MST) | Change |
|------------|--------|
| 2026-02-07 23:30 | CLAUDE.md v2 — comprehensive autonomous execution directive. Replaces v1 (philosophy-only). Includes full sprint plan, testing protocol, commit protocol, checkpoint protocol, API patterns, environment setup, and autonomous permissions. |

---

*This file is the single source of truth for Claude Code sessions. When in doubt, follow this file. For sprint details beyond what's here, read MASTER_SPRINT_PLAN_v3.md.*
