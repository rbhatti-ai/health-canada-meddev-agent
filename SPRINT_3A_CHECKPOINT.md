# SPRINT 3a CHECKPOINT — Gap Detection Engine

**Timestamp:** 2026-02-07 19:25 MST (Mountain Time - Edmonton)
**Branch:** main
**Commit:** c541059
**Previous Commit:** 0d0e27e (Sprint plan correction)

---

## Deliverables

| Item | Status | Details |
|------|--------|---------|
| GapDetectionEngine class | ✅ Done | `src/core/gap_engine.py` |
| 12 deterministic gap rules | ✅ Done | GAP-001 through GAP-012 |
| Pydantic models | ✅ Done | GapFinding, GapRuleDefinition, GapReport |
| Unit tests | ✅ Done | `tests/unit/test_gap_engine.py` |
| Pre-commit hooks | ✅ All passed | black, isort, ruff, mypy, pytest-unit, pytest-regulatory |
| Pushed to GitHub | ✅ Done | origin/main |

## Test Metrics

| Metric | Value |
|--------|-------|
| New tests (Sprint 3a) | 78 |
| Total tests passing | 627 |
| Regressions | 0 |
| Test runtime | 14.07s |

## Architecture Decisions

1. **Generic TwinRepository API** — Engine uses `get_by_device_version(table, dvid)`, `get_by_id(table, id)`, `get_by_field(table, field, val)`. No entity-specific methods.
2. **Pydantic TraceLink attribute access** — `link.target_type`, not `link.get("target_type")`. TraceLink is a Pydantic model.
3. **Instance-level rule copy** — `copy.deepcopy()` in `__init__` prevents cross-instance mutation (caught during testing).
4. **SimpleNamespace for test mocks** — `make_link()` helper creates TraceLink-like objects with attribute access for clean test setup.
5. **Best-effort pattern** — Engine logs errors and continues; never crashes on individual rule failure.
6. **Regulatory language safety** — No "compliant", "ready", "certified", "approved", "will pass" in any output.

## 12 Gap Detection Rules

| Rule | Name | Severity | Category |
|------|------|----------|----------|
| GAP-001 | Unmitigated hazards | critical | coverage |
| GAP-002 | Unverified controls | critical | coverage |
| GAP-003 | Unsupported claims | major | coverage |
| GAP-004 | Missing intended use | critical | completeness |
| GAP-005 | Weak evidence | major | evidence_strength |
| GAP-006 | Untested claims | major | coverage |
| GAP-007 | No submission target | minor | completeness |
| GAP-008 | Unattested AI outputs | major | consistency |
| GAP-009 | Missing labeling | major | completeness |
| GAP-010 | Incomplete risk chain | critical | consistency |
| GAP-011 | Draft evidence only | major | evidence_strength |
| GAP-012 | No clinical evidence (III/IV) | critical | evidence_strength |

## Issues Encountered & Resolved

1. **Pre-commit hook failures (first attempt):** Original code used fake entity-specific methods (`get_hazards_for_device()`) and dict-style TraceLink access (`.get("target_type")`). mypy caught 39 errors. Fixed by rewriting to use real generic API and Pydantic attributes.
2. **Import path:** `src.utils.logger` → `src.utils.logging` (module naming mismatch).
3. **Instance isolation bug:** Class-level `RULE_DEFINITIONS` dict was mutable, causing cross-test pollution when one test disabled a rule. Fixed with `copy.deepcopy()` in `__init__`.

## Files Changed

- `src/core/gap_engine.py` — NEW (2038 lines with tests)
- `tests/unit/test_gap_engine.py` — NEW

## Cumulative Project State

| Sprint | Commit | Tests | Key Deliverable |
|--------|--------|-------|-----------------|
| Sprint 1 | f19051c | 410 | 10 DB tables, Pydantic models, TwinRepository |
| Sprint 2 | 6f8853f | 549 | TraceabilityEngine, EvidenceIngestion, Attestation, 13 APIs |
| Sprint 3a | c541059 | 627 | GapDetectionEngine, 12 rules, 78 tests |

## Next Step

**Sprint 3b: ReadinessAssessment** — Aggregation layer that consumes GapReport and produces a structured readiness assessment with scoring dimensions.
