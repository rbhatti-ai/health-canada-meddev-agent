# CHECKPOINT — SPRINT 8 (Design Controls)

> **Timestamp:** 2026-02-07 23:30 MST (Mountain Time — Edmonton)
> **Tests:** 1273 passing (expected ~1271)
> **Commit:** 3a15ac1 (Sprint 8C)
> **Governing doc:** `docs/architecture/REGULATORY_EXECUTION_PLATFORM_ARCHITECTURE.md`

---

## SPRINT 8 SUMMARY

Sprint 8 implements ISO 13485:2016 Section 7.3 Design Control entities, trace links, and gap rules.

### 8A: Design Control Entities (49 tests)
**File:** `src/core/design_controls.py`

New Pydantic models:
- `DesignInput` — User needs driving design (7.3.2)
- `DesignOutput` — Specifications meeting inputs (7.3.3)
- `DesignReview` — Formal review records (7.3.5)
- `DesignVerification` — Verification against inputs (7.3.6)
- `DesignValidation` — Validation against user needs (7.3.7)
- `DesignChange` — Change control records (7.3.9)
- `DesignHistoryRecord` — DHF entries

New service:
- `DesignControlService` — CRUD and analysis methods
  - `get_unmet_inputs()` — Design inputs with no outputs
  - `get_unverified_outputs()` — Outputs without verification
  - `get_phases_without_review()` — Phases missing reviews
  - `calculate_design_completeness()` — 0.0-1.0 score

### 8B: Design Control Trace Links (7 new tests)
**File:** `src/core/traceability.py`

New trace link types:
- `design_input` → `design_output` (drives)
- `design_output` → `design_input` (satisfies)
- `design_output` → `design_verification` (verified_by)
- `design_output` → `design_validation` (validated_by)
- `design_review` → `design_output` (reviews)
- `design_verification` → `evidence_item` (supported_by)
- `design_validation` → `evidence_item` (supported_by)

VALID_RELATIONSHIPS now has 16 entries (9 risk + 7 design control).

### 8C: Design Control Gap Rules (12 new tests)
**File:** `src/core/gap_engine.py`

New gap rules:
| Rule | Name | Severity | Citation |
|------|------|----------|----------|
| GAP-017 | Unmet design inputs | major | ISO 13485:2016, 7.3.4 |
| GAP-018 | Unverified design outputs | critical | ISO 13485:2016, 7.3.6 |
| GAP-019 | Missing design review | major | ISO 13485:2016, 7.3.5 |

GapDetectionEngine now has 19 rules total (GAP-001 through GAP-019).

### New Regulatory References
**File:** `src/core/regulatory_references.py`

Added ISO 13485 section references:
- `ISO-13485-2016-7.3.4` — Design and Development Outputs
- `ISO-13485-2016-7.3.5` — Design and Development Review

---

## TEST COVERAGE

| Test File | Tests |
|-----------|-------|
| tests/unit/test_design_controls.py | 49 |
| tests/unit/test_traceability.py | 47 (+7 new) |
| tests/unit/test_gap_engine.py | 137 (+12 new) |

**Sprint 8 contribution:** ~68 new tests

---

## CUMULATIVE METRICS

| Metric | Sprint 7 | Sprint 8 | Delta |
|--------|----------|----------|-------|
| Tests | 1117 | 1273 | +156 |
| Gap rules | 16 | 19 | +3 |
| Entity models | 15 | 22 | +7 |
| Trace link types | 9 | 16 | +7 |
| Citations indexed | 60+ | 62+ | +2 |

---

## FILES MODIFIED/CREATED

### Created
- `src/core/design_controls.py` — 600+ lines
- `tests/unit/test_design_controls.py` — 900+ lines

### Modified
- `src/core/traceability.py` — Added design control types
- `src/core/gap_engine.py` — Added GAP-017/018/019
- `src/core/regulatory_references.py` — Added ISO 13485 sections
- `tests/unit/test_traceability.py` — 7 new tests
- `tests/unit/test_gap_engine.py` — 12 new tests, count updates

---

## SPRINT 8 EXIT CRITERIA ✅

- [x] DesignInput, DesignOutput, DesignReview models
- [x] DesignVerification, DesignValidation, DesignChange models
- [x] DesignControlService with analysis methods
- [x] Design control trace links (7 types)
- [x] GAP-017, GAP-018, GAP-019 rules
- [x] 1273 total tests passing (target: ~1271)
- [x] Checkpoint created with MST timestamp

---

## COMMITS

```
3a15ac1 Sprint 8C: Design control gap rules (GAP-017, GAP-018, GAP-019)
[Previous] Sprint 8B: Design control trace links
[Previous] Sprint 8A: Design control entities and service
```

---

## NEXT: SPRINT 9 — LABELING + POST-MARKET

Per MASTER_SPRINT_PLAN_v3.md:
- 9A: Labeling Compliance (~40 tests)
  - 30+ labeling requirements from SOR/98-282 Part 5
  - Device label, IFU, packaging, bilingual requirements
- 9B: Post-Market Planning (~30 tests)
  - PostMarketPlan model
  - Mandatory problem reporting timelines
  - PMCF planning

Expected: ~1341 tests after Sprint 9

---

*End of Sprint 8 checkpoint*
