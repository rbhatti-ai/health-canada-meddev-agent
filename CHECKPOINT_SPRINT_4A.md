# CHECKPOINT — Sprint 4A: Agent Tool Definitions

> **Timestamp:** 2026-02-07 19:55 MST (Mountain Time — Edmonton)
> **Branch:** main
> **Commit:** `3912245`
> **Previous commit:** `810b002` (Sprint 3c)
> **Tests at entry:** 732
> **Tests at exit:** 780 (+48)

---

## Deliverable

**File:** `src/agents/regulatory_twin_tools.py`

13 LangGraph-compatible `@tool` functions wrapping all regulatory services:

| # | Tool | Service | Purpose |
|---|------|---------|---------|
| 1 | `create_trace_link` | TraceabilityEngine | Create regulatory trace links |
| 2 | `get_trace_chain` | TraceabilityEngine | Claim → evidence chain traversal |
| 3 | `get_coverage_report` | TraceabilityEngine | Coverage completeness report |
| 4 | `validate_trace_relationship` | TraceabilityEngine | Link type validation |
| 5 | `ingest_evidence` | EvidenceIngestionService | Evidence + artifact ingestion |
| 6 | `get_evidence_for_device` | EvidenceIngestionService | Evidence inventory |
| 7 | `find_unlinked_evidence` | EvidenceIngestionService | Orphaned evidence detection |
| 8 | `create_attestation` | AttestationService | Human sign-off |
| 9 | `get_pending_attestations` | AttestationService | Unreviewed items |
| 10 | `get_attestation_trail` | AttestationService | Audit trail |
| 11 | `run_gap_analysis` | GapDetectionEngine | Full gap report (12 rules) |
| 12 | `get_critical_gaps` | GapDetectionEngine | Critical blockers only |
| 13 | `get_readiness_assessment` | ReadinessAssessment | Readiness score + summary |

### Design Decisions

1. **13 tools, not 12.** Master plan listed 12, handoff doc listed a different 12. Analysis showed both `get_evidence_for_device` and `get_attestation_trail` are non-negotiable for regulatory workflows. See analysis in chat log.
2. **`_safe_call` wrapper.** All tools return `{"status": "success"|"error", "tool": "...", "result"|"error": ...}`. Tools NEVER raise exceptions — this prevents LangGraph agent crashes.
3. **Lazy service imports.** `_get_*()` helper functions use deferred imports to prevent circular dependency issues at module load time.
4. **Pydantic serialization.** Tools handle `model_dump()`, `dict()`, and plain `dict` return types from services.
5. **`REGULATORY_TWIN_TOOLS` registry.** Ordered list of all 13 tools. `get_regulatory_twin_tools()` returns a copy.

### Test File

**File:** `tests/unit/test_regulatory_twin_tools.py` — 48 tests

| Test Class | Tests | What's Covered |
|------------|-------|----------------|
| TestCreateTraceLink | 4 | Success, invalid relationship, unexpected error, tool name |
| TestGetTraceChain | 3 | Success, nonexistent claim, dict return |
| TestGetCoverageReport | 2 | Success, error handling |
| TestValidateTraceRelationship | 3 | Valid, invalid, input params in result |
| TestIngestEvidence | 2 | Success, validation error |
| TestGetEvidenceForDevice | 3 | With items, empty, dict items |
| TestFindUnlinkedEvidence | 3 | Orphans found, none found, error |
| TestCreateAttestation | 2 | Success, invalid type |
| TestGetPendingAttestations | 2 | With pending, none pending |
| TestGetAttestationTrail | 3 | With trail, empty, error |
| TestRunGapAnalysis | 3 | Success, error, dict report |
| TestGetCriticalGaps | 4 | Critical found, none, dict filtering, error |
| TestGetReadinessAssessment | 3 | Success, error, regulatory-safe language |
| TestToolRegistry | 7 | Count=13, list type, BaseTool check, unique names, descriptions, expected names, copy semantics |
| TestSafeCall | 4 | Success wrap, ValueError, RuntimeError, never raises |

### Pre-commit Results

- black: ✅ Passed
- isort: ✅ Passed
- ruff: ✅ Passed
- mypy: ✅ Passed
- pytest-unit: ✅ Passed
- pytest-regulatory: ✅ Passed

### Known Issues

- `mypy` initially failed on missing type annotations for `_safe_call` params and `_execute()` / `_get_*()` return types. Fixed with `-> Any` annotations. All 5 helpers and 13 inner functions annotated.
- Trailing whitespace auto-fixed in `CLAUDE.md` and architecture doc (pre-existing, not from our code).

---

## Cumulative Milestone Tracker

| Metric | Sprint 1 | Sprint 2 | Sprint 3a | Sprint 3b | Sprint 3c | Sprint 4A |
|--------|----------|----------|-----------|-----------|-----------|-----------|
| Commit | f19051c | 6f8853f | c541059 | 43f9038 | 810b002 | 3912245 |
| Service classes | 3 | 6 | 7 | 8 | 8 | 8 |
| API endpoints | 6 | 19 | 19 | 19 | 23 | 23 |
| Agent tools | 5 | 5 | 5 | 5 | 5 | **18** (5 original + 13 new) |
| Gap rules | 0 | 0 | 12 | 12 | 12 | 12 |
| Total tests | 410 | 549 | 627 | 699 | 732 | **780** |

---

## Next: Sprint 4B — Regulatory Analysis Prompts

**File:** `src/agents/prompts.py`
- System prompts for regulatory analysis
- Structured output schemas (Pydantic models for agent responses)
- Regulatory-safe language enforcement
- AI provenance logging patterns
- Target: ~15 new tests → ~795 total

---

*End of Sprint 4A checkpoint*
