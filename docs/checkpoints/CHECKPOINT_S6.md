# CHECKPOINT — Sprint 6: IP Protection Framework

> **Timestamp:** 2026-02-08 00:05 MST (Mountain Time — Edmonton)
> **Branch:** main
> **Commit:** 3fb4857
> **Previous commit:** 8b3401e (Sprint 5C checkpoint)
> **Tests at entry:** 1010
> **Tests at exit:** 1094 (84 new)
> **Test runtime:** 11.34s
> **Status:** COMPLETE — Committed and pushed

---

## What Was Delivered

Sprint 6 delivered a complete IP protection framework across 4 sub-sprints:

| Sub-Sprint | Deliverable | Commit | Tests Added |
|------------|-------------|--------|-------------|
| 6A | ConfidentialityService (4 levels) | 17e1b6d | 43 |
| 6B | CBI Request Generator | 7d0a74a | 16 |
| 6C | GAP-013 rule for unclassified assets | cc960ed | 8 |
| 6D | IP classification agent tools | 3fb4857 | 17 |
| **Total** | **Complete IP framework** | | **84** |

---

### Sprint 6A: Confidentiality Service

**File:** `src/core/confidentiality.py`

| Component | Description |
|-----------|-------------|
| `ConfidentialityLevel` | 4 levels: public, confidential_submission, trade_secret, patent_pending |
| `ConfidentialityTag` | Pydantic model for IP classification with citations |
| `ConfidentialityReport` | Summary report with CBI status |
| `ConfidentialityService` | Singleton service for classify, query, report |
| `CLASSIFIABLE_ENTITY_TYPES` | 8 entity types that can be classified |

---

### Sprint 6B: CBI Request Generator

**File:** `src/core/confidentiality.py` (extended)

| Component | Description |
|-----------|-------------|
| `CBIItem` | Single item in CBI request with justification, harm |
| `CBIRequest` | Complete CBI request with items and attestation |
| `create_cbi_items_from_tags()` | Convert ConfidentialityTags to CBIItems |
| `generate_cbi_request()` | Create CBI request from tags |
| `generate_cbi_request_document()` | Generate formatted CBI document |

**Regulatory Citation:** [SOR/98-282, s.43.2]

---

### Sprint 6C: GAP-013 Rule

**File:** `src/core/gap_engine.py` (extended)

| Component | Description |
|-----------|-------------|
| GAP-013 | "Unclassified sensitive assets" rule |
| Severity | minor |
| Category | consistency |
| Citation | [SOR/98-282, s.43.2] |

**Added Reference:** `SOR-98-282-S43.2` in regulatory_references.py (52 total refs)

---

### Sprint 6D: IP Agent Tools

**File:** `src/agents/tools.py` (extended)

| Tool | Description |
|------|-------------|
| `classify_confidentiality` | Classify entity's IP level (public, trade_secret, etc.) |
| `get_ip_inventory` | Get summary of IP assets by organization |

**Agent Tool Count:** 20 (7 base + 13 twin)

---

## Quality Gates Passed

| Gate | Status |
|------|--------|
| ruff check (0 errors) | PASS |
| black formatting | PASS |
| isort import ordering | PASS |
| mypy (clean) | PASS |
| 84 new tests passing | PASS |
| 1094 total tests passing | PASS |
| ConfidentialityService complete | PASS |
| CBI request generation works | PASS |
| GAP-013 integrated with citations | PASS |
| IP tools accessible to agent | PASS |

---

## API Summary

### ConfidentialityService Methods

```python
service = get_confidentiality_service()

# Classification
tag = service.classify(entity_type, entity_id, level, organization_id, ...)

# Queries
tags = service.get_all_classifications(organization_id)
tags = service.get_trade_secrets(organization_id)
tags = service.get_cbi_candidates(organization_id)
unclassified = service.get_unclassified(organization_id, known_entities)

# Helpers
is_public = service.is_disclosable(entity_type, entity_id)
needs_redaction = service.requires_redaction(entity_type, entity_id)

# Reporting
report = service.generate_report(organization_id, known_entities)
```

### CBI Functions

```python
items = create_cbi_items_from_tags(tags)
request = generate_cbi_request(org_id, submission_ref, device_name, tags)
document = generate_cbi_request_document(request)
```

### Agent Tools

```python
# Via agent chat or direct invocation
result = classify_confidentiality.invoke({
    "entity_type": "evidence_item",
    "entity_id": str(uuid),
    "organization_id": str(uuid),
    "level": "trade_secret",
    "justification": "...",
    "harm_if_disclosed": "...",
})

result = get_ip_inventory.invoke({
    "organization_id": str(uuid),
})
```

---

## Confidentiality Levels

| Level | Public Disclosure | CBI Request Required | Use Case |
|-------|-------------------|---------------------|----------|
| `public` | Yes | No | General info, published specs |
| `confidential_submission` | No (redacted) | Yes | Proprietary details |
| `trade_secret` | Never | Yes | Core algorithms, processes |
| `patent_pending` | Reference only | No | Pending patent apps |

---

## Cumulative Milestone Tracker

| Metric | Sprint 5C | Sprint 6A | Sprint 6B | Sprint 6C | Sprint 6D |
|--------|-----------|-----------|-----------|-----------|-----------|
| Commit | 8b3401e | 17e1b6d | 7d0a74a | cc960ed | 3fb4857 |
| Service classes | 8 | 9 | 9 | 9 | 9 |
| API endpoints | 23 | 23 | 23 | 23 | 23 |
| Agent tools | 18 | 18 | 18 | 18 | 20 |
| Gap rules | 12 | 12 | 12 | 13 | 13 |
| System prompts | 6 | 6 | 6 | 6 | 6 |
| Regulatory references | 51 | 51 | 51 | 52 | 52 |
| Total tests | 1010 | 1053 | 1069 | 1077 | 1094 |

---

## Sprint 6 Exit Criteria

Per MASTER_SPRINT_PLAN_v3.md:

- [x] ConfidentialityService with 4 levels
- [x] CBIRequest generator
- [x] GAP-013 rule
- [x] 2 new agent tools
- [x] ~1,066 total tests passing (actual: 1094)
- [x] Checkpoint created with MST timestamp

---

## What's Next: Sprint 7 — Clinical Evidence + Predicate

Per MASTER_SPRINT_PLAN_v3.md:

### 7A: Clinical Evidence Model (~50 tests)
- ClinicalStudyType Literal with 9 study types
- Evidence hierarchy scoring (1.0 for RCT, down to 0.15 for expert opinion)
- ClinicalEvidenceItem with study metadata
- ClinicalEvidencePackage for aggregated evidence

### 7B: Predicate Device Comparison (~30 tests)
- PredicateDevice model
- SubstantialEquivalenceAnalysis
- Comparison scoring for predicate selection

---

*End of Sprint 6 checkpoint — IP Protection Framework COMPLETE*
