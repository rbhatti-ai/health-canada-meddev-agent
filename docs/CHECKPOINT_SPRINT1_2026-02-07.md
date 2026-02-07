# SPRINT 1 CHECKPOINT — Regulatory Twin Foundation
> **Timestamp:** 2026-02-06 19:00 MST (Mountain Time Edmonton)
> **Sprint:** 1 (Regulatory Twin Core Entities)
> **Status:** ✅ COMPLETE
> **Final Commit:** `5038632`
> **Test Count:** 410/410 passing
> **Branch:** main

---

## COMMITS THIS SPRINT

| Commit | Description | Tests |
|--------|-------------|-------|
| `ec7bfb6` | Sprint 1a: DB migration — 10 tables, RLS, CHECK constraints | 339 |
| `3906a6c` | Sprint 1b: Pydantic models — 10 entities, registry, serialization | 392 |
| `5038632` | Sprint 1c: Persistence layer — TwinRepository, integration tests | 410 |

---

## DELIVERABLES COMPLETED

### Sprint 1a: Database Migration
**File:** `scripts/migrations/2026-02-07_regulatory_twin_core.sql` (32,397 bytes)
- 10 tables created: intended_uses, claims, hazards, harms, risk_controls,
  verification_tests, validation_tests, evidence_items, labeling_assets, submission_targets
- All org-scoped with organization_id FK
- 8 versioned tables with version + supersedes_id (immutable versioning)
- 22 CHECK constraints for ISO 14971 enums
- 30+ indexes
- RLS enabled on all 10 (19 total RLS tables)
- Supabase auth guard pattern with EXECUTE $pol$

### Sprint 1b: Pydantic Models
**File:** `src/core/regulatory_twin.py` (12,686 bytes)
- 10 models matching DB schema exactly
- Literal types enforce CHECK constraint values in Python
- to_db_dict() / from_db_row() serialization round-trip
- TWIN_MODEL_REGISTRY maps table names → model classes

### Sprint 1c: Persistence Layer
**File:** `src/persistence/twin_repository.py` (17,608 bytes)
- TwinRepository class with generic CRUD
- Dual backend: Supabase (production) + local Postgres (dev)
- Best-effort pattern (never crashes app)
- Typed convenience functions for all 10 entities

### Tests
| File | Tests | Type |
|------|-------|------|
| tests/unit/test_regulatory_twin_migration.py | 182 | Unit (SQL structure) |
| tests/unit/test_regulatory_twin_models.py | 53 | Unit (Pydantic validation) |
| tests/integration/test_twin_persistence.py | 18 | Integration (DB round-trip) |
| (previous tests) | 157 | Unit + Integration |
| **TOTAL** | **410** | |

---

## EXIT CRITERIA CHECKLIST

- [x] Migration creates all 10 new tables
- [x] RLS enabled on all 10 new tables (19 total)
- [x] All tables have version + supersedes_id columns (8 of 10, 2 immutable by design)
- [x] Pydantic models for all 10 entities
- [x] Persistence CRUD for: intended_uses, claims, hazards, harms, risk_controls,
      verification_tests, validation_tests, evidence_items, labeling_assets, submission_targets
- [x] 200+ total tests passing (410)
- [x] Committed to main
- [x] Checkpoint documented

---

## KNOWN SCHEMA DISCREPANCIES (for future reference)

Local Postgres base tables differ from Supabase schema doc:
- `organizations`: columns are (id, name, created_at) — NO slug
- `users`: columns are (id, organization_id, created_at) — NO email, full_name
- `products`: uses `org_id` not `organization_id`
- `device_versions`: NO organization_id column (linked via product_id → products.org_id)

These are important for any future test fixtures or migrations.

---

## NEXT: SPRINT 2 — Traceability Engine + Evidence Ingestion

**Goal:** Make trace_links operational. Connect: claim → hazard → risk_control → verification → evidence.

Key deliverables:
- 2a: Traceability service (link creation, graph traversal)
- 2b: Evidence ingestion pipeline (file upload → artifact → evidence_item)
- 2c: Gap detection (find claims without evidence, hazards without controls)
- 2d: Tests + checkpoint
