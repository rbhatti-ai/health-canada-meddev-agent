# SPRINT 2 CHECKPOINT — Traceability, Evidence & Attestation
**Timestamp:** 2026-02-07 17:55 MST (Mountain Time — Edmonton)
**Branch:** main
**Status:** ✅ COMPLETE — All 4 deliverables shipped

---

## SPRINT SUMMARY

| Metric | Value |
|---|---|
| Starting tests | 470 (end of Sprint 2a) / 410 (end of Sprint 1) |
| Final tests | **549 passing** |
| New tests | **139 total** (60 + 25 + 35 + 19) |
| Runtime | 4.40s |
| New files | 8 (4 source + 4 test) |
| Commits | 4 |

---

## DELIVERABLES

### Sprint 2a: TraceabilityEngine — `775b72a`
- **File:** `src/core/traceability.py` (609 lines)
- **Tests:** `tests/unit/test_traceability.py` (553 lines, 60 tests)
- **Features:**
  - VALID_RELATIONSHIPS dict: 9 allowed link types enforcing regulatory chain
  - validate_link() — static validation of relationship types
  - create_link() — validates then persists to trace_links table
  - get_links_from/to() — compound queries (source_type + source_id)
  - get_full_chain() — recursive traversal with cycle detection
  - get_coverage_report() — per device version, claim→hazard→control→test→evidence
  - Singleton pattern, best-effort persistence, dual backend

### Sprint 2b: EvidenceIngestionService — `00bf1f8`
- **File:** `src/core/evidence_ingestion.py` (339 lines)
- **Tests:** `tests/unit/test_evidence_ingestion.py` (297 lines, 25 tests)
- **Features:**
  - ingest_evidence() — artifact + evidence_item + trace_link in one call
  - bulk_ingest() — batch processing with per-item results
  - get_evidence_for_claim/test() — query via trace links
  - get_unlinked_evidence() — gap detection for orphaned evidence
  - compute_content_hash() — SHA-256 for integrity verification
  - Mypy caught source_ref field name bug (fixed before commit)

### Sprint 2c: AttestationService — `853baa7`
- **File:** `src/core/attestation_service.py` (349 lines)
- **Tests:** `tests/unit/test_attestation_service.py` (297 lines, 35 tests)
- **Features:**
  - attest_artifact() — human sign-off on artifacts
  - attest_link() — human sign-off on artifact links
  - get_attestation_status() — summary with is_approved/is_rejected flags
  - get_attestation_audit_trail() — chronological history
  - get_unattested_items() — workflow dashboard: what needs review
  - get_link_attestation_audit_trail() — trail for links
  - 4 types: reviewed, approved, rejected, acknowledged

### Sprint 2d: API Routes — `6f8853f`
- **File:** `src/api/traceability_routes.py` (396 lines)
- **Tests:** `tests/api/test_traceability_endpoints.py` (200 lines, 19 tests)
- **Endpoints:**
  - POST /api/v1/trace-links — create with validation
  - GET /api/v1/trace-links/valid-relationships — list allowed types
  - GET /api/v1/trace-links/by-id/{id} — single link lookup
  - GET /api/v1/trace-chains/{type}/{id} — full chain traversal
  - GET /api/v1/coverage/{device_version_id} — coverage report
  - POST /api/v1/evidence — single ingest
  - POST /api/v1/evidence/bulk — batch ingest
  - GET /api/v1/evidence/{device_version_id} — list evidence
  - GET /api/v1/evidence/unlinked/{device_version_id} — orphans
  - POST /api/v1/attestations — create sign-off
  - GET /api/v1/attestations/pending/{org_id} — unattested items
  - GET /api/v1/attestations/trail/{artifact_id} — audit trail
  - GET /api/v1/attestations/status/{artifact_id} — summary
- **Fix:** Route ordering conflict resolved (valid-relationships vs {link_id})
- **Fix:** isort import ordering in main.py

---

## BUGS CAUGHT & FIXED

| Bug | Caught by | Fix |
|---|---|---|
| `source_reference` vs `source_ref` field name | mypy pre-commit | Renamed in evidence_ingestion.py |
| Route ordering: `{link_id}` matched before `valid-relationships` | pytest (5 failures) | Changed path to `/trace-links/by-id/{link_id}` |
| Import placement (E402 module-level import) | ruff pre-commit | Moved import to top of main.py |
| isort ordering in main.py | isort pre-commit | Auto-fixed on re-stage |

---

## GIT LOG

```
6f8853f Sprint 2d: Traceability/Evidence/Attestation API routes (19 new tests, 549 total)
853baa7 Sprint 2c: AttestationService with audit trail, unattested detection (35 new tests, 530 total)
00bf1f8 Sprint 2b: EvidenceIngestionService with bulk ingest, unlinked detection (25 new tests, 495 total)
775b72a Sprint 2a: TraceabilityEngine with link validation, chain traversal, coverage reports (60 new tests, 470 total)
f19051c Sprint 1 (prior baseline)
```

---

## FILE INVENTORY (Sprint 2 additions)

```
src/core/traceability.py          — TraceabilityEngine
src/core/evidence_ingestion.py    — EvidenceIngestionService
src/core/attestation_service.py   — AttestationService
src/api/traceability_routes.py    — FastAPI APIRouter (13 endpoints)
tests/unit/test_traceability.py   — 60 tests
tests/unit/test_evidence_ingestion.py — 25 tests
tests/unit/test_attestation_service.py — 35 tests
tests/api/test_traceability_endpoints.py — 19 tests
```

---

## REGULATORY CHAIN ENFORCED

```
claim -[addresses]-> hazard -[causes/may_cause]-> harm
hazard -[mitigated_by]-> risk_control -[verified_by]-> verification_test
risk_control -[validated_by]-> validation_test
verification_test -[supported_by]-> evidence_item
validation_test -[supported_by]-> evidence_item
claim -[supported_by]-> evidence_item
```

All 9 relationship types are enforced at the application layer via VALID_RELATIONSHIPS.

---

## NEXT: SPRINT 3 (Planned)

Sprint 3 will focus on the **AI Agent Layer** — connecting Claude to the regulatory infrastructure:
- 3a: Agent tool definitions (LangGraph tools wrapping the services)
- 3b: Regulatory analysis prompts + structured output
- 3c: Agent orchestration (multi-step regulatory workflows)
- 3d: Streamlit UI integration
