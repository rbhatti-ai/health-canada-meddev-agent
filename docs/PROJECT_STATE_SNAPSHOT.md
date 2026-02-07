# PROJECT STATE SNAPSHOT

> **Generated:** 2026-02-06 18:13:47 MST
> **Generator:** `scripts/snapshot.py`
> **This file is auto-generated. Do not edit manually.**

---

## Git Status

| Field | Value |
|-------|-------|
| Branch | `main` |
| Last Commit | `b7d4a05 fix: resolve 2 test failures + sanitize API key + fix ruff B904 - Stats endpoint returns version field - Pathway returns 422 for invalid class - Replaced hardcoded OpenAI key with placeholder - Fixed raise-from pattern (B904) in API exception handlers - 122/122 tests passing - Note: 34 pre-existing mypy errors in 11 files tracked as tech debt - Checkpoint PRE-RLS-MIGRATION baseline Feb 6 2026 1725 MST` |
| Commit Hash | `b7d4a05` |
| Total Commits | 15 |

**Uncommitted changes:**
  - `?? "Health Canada MedDev Agent_hand off plan Feb 6 1415pm.docx"`
  - `?? Makefile`
  - `?? docs/PROJECT_STATE_SNAPSHOT_2026-02-06.docx`
  - `?? "docs/latest ongoing thread to take over after reading other docs.docx"`
  - `?? scripts/migrations/2026-02-06_rls_policies_artifacts_attestations.sql`
  - `?? scripts/snapshot.py`
  - `?? tests/unit/test_rls_migration.py`

---

## Test Summary
```
========================= 157 tests collected in 0.12s =========================
```

---

## File Counts

| Category | Count |
|----------|-------|
| Python source files (src/) | 28 |
| Python test files (tests/) | 17 |
| SQL migration files | 4 |

---

## Database State (Local Postgres)

### Tables
```
ai_conversations
ai_runs
artifact_links
artifacts
attestations
device_versions
devices
documents
org_members
organizations
products
submissions
trace_links
users
```

### Row-Level Security

| Table | RLS |
|-------|-----|
| ai_conversations | OFF |
| ai_runs | OFF |
| artifact_links | OFF |
| artifacts | OFF |
| attestations | OFF |
| device_versions | OFF |
| devices | OFF |
| documents | OFF |
| org_members | OFF |
| organizations | OFF |
| products | OFF |
| submissions | OFF |
| trace_links | OFF |
| users | OFF |

### Policies

| Table | Policy | Command |
|-------|--------|---------|
| (none) | (none) | (none) |

---

## Known Gaps vs Governing Architecture

| Requirement | Status | Notes |
|-------------|--------|-------|
| Regulatory Twin (persistent) | PARTIAL | DeviceInfo model exists, no persistent storage |
| Traceability Engine | NOT STARTED | trace_links table exists, no UI/logic |
| Evidence Gap Detection | NOT STARTED | No rules engine |
| Submission Readiness Dashboard | NOT STARTED | No dashboard UI |
| Document Orchestration | NOT STARTED | No doc generation from structured data |
| Deficiency Response Workflow | NOT STARTED | No deficiency tracking |
| AI Provenance (ai_runs) | PARTIAL | Table + logger exist, no UI/approval flow |
| Human-in-the-Loop Approval | NOT STARTED | No approval workflow |
| RLS / Multi-Tenancy | IN PROGRESS | RLS enabled, policies Supabase-only |
| S3 Document Storage | NOT STARTED | No S3 integration |
| Supabase Cloud Deployment | NOT STARTED | Local Postgres only |

---

## Checkpoint History

| Timestamp | Commit | Description |
|-----------|--------|-------------|
| 2026-02-06 18:13:47 MST | `b7d4a05` | Auto-snapshot |

---

*End of snapshot*
