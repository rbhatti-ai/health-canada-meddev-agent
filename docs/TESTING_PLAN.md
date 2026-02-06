# Testing Plan & Standing Instructions

## Overview

This document defines the comprehensive testing strategy for the Health Canada Medical Device Regulatory Agent. Tests run automatically after every code change via pre-commit hooks and CI/CD.

---

## Test Categories

### 1. Unit Tests (`tests/unit/`)
Test individual functions and classes in isolation.

| Test File | Coverage |
|-----------|----------|
| `test_models.py` | Pydantic models, enums, validation |
| `test_classification.py` | Classification engine, IMDRF matrix |
| `test_pathway.py` | Pathway advisor, fee calculations |
| `test_checklist.py` | Checklist generation, items |
| `test_retriever.py` | Document retrieval logic |
| `test_embedder.py` | Embedding generation |

**Run:** `pytest tests/unit/ -v`

### 2. Integration Tests (`tests/integration/`)
Test component interactions and data flow.

| Test File | Coverage |
|-----------|----------|
| `test_api_endpoints.py` | All REST API endpoints |
| `test_rag_pipeline.py` | RAG search + retrieval |
| `test_classification_flow.py` | End-to-end classification |
| `test_pathway_flow.py` | End-to-end pathway generation |

**Run:** `pytest tests/integration/ -v`

### 3. Regulatory Accuracy Tests (`tests/regulatory/`)
Verify Health Canada regulation compliance.

| Test File | Coverage |
|-----------|----------|
| `test_fees_2024.py` | Verify all 2024 fee values |
| `test_samd_matrix.py` | IMDRF N12 classification matrix |
| `test_device_classes.py` | Class I-IV rules |
| `test_timelines.py` | Review timeline accuracy |

**Run:** `pytest tests/regulatory/ -v`

### 4. RAG Quality Tests (`tests/rag/`)
Verify document retrieval quality.

| Test File | Coverage |
|-----------|----------|
| `test_search_relevance.py` | Search result relevance |
| `test_chunk_quality.py` | Document chunking quality |
| `test_category_filtering.py` | Category filter accuracy |

**Run:** `pytest tests/rag/ -v`

### 5. API Contract Tests (`tests/api/`)
Verify API request/response schemas.

| Test File | Coverage |
|-----------|----------|
| `test_classify_endpoint.py` | /api/v1/classify schema |
| `test_pathway_endpoint.py` | /api/v1/pathway schema |
| `test_search_endpoint.py` | /api/v1/search schema |
| `test_error_handling.py` | Error responses |

**Run:** `pytest tests/api/ -v`

### 6. Performance Tests (`tests/performance/`)
Verify response times and throughput.

| Test File | Coverage |
|-----------|----------|
| `test_api_latency.py` | API response times < 2s |
| `test_rag_latency.py` | RAG search < 3s |
| `test_classification_speed.py` | Classification < 100ms |

**Run:** `pytest tests/performance/ -v --benchmark`

---

## Test Data

### Fixtures Location: `tests/fixtures/`

```
tests/fixtures/
├── devices/
│   ├── samd_class_ii.json
│   ├── samd_class_iii.json
│   ├── samd_class_iv.json
│   ├── implant_class_iv.json
│   └── ivd_class_iii.json
├── expected_results/
│   ├── classification_results.json
│   ├── pathway_results.json
│   └── fee_calculations.json
└── documents/
    └── test_chunks.json
```

---

## Automatic Test Triggers

### Pre-commit Hook (Local)
Runs on every `git commit`:
- Linting (ruff)
- Type checking (mypy)
- Unit tests
- Regulatory accuracy tests

### Pre-push Hook (Local)
Runs on every `git push`:
- All unit tests
- All integration tests
- API contract tests

### GitHub Actions CI (Remote)
Runs on every PR and push to main:
- Full test suite
- Coverage report
- Performance benchmarks

---

## Test Commands

```bash
# Run all tests
pytest

# Run specific category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/regulatory/ -v

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_classification.py -v

# Run tests matching pattern
pytest -k "classification" -v

# Run only fast tests (no API calls)
pytest -m "not slow" -v

# Run performance benchmarks
pytest tests/performance/ --benchmark-only
```

---

## Coverage Requirements

| Category | Minimum Coverage |
|----------|------------------|
| Core Logic (`src/core/`) | 90% |
| API (`src/api/`) | 85% |
| Retrieval (`src/retrieval/`) | 80% |
| Overall | 80% |

---

## CI/CD Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Commit    │───▶│  Pre-commit │───▶│    Push     │
└─────────────┘    │    Hooks    │    └─────────────┘
                   │  - Lint     │           │
                   │  - Type     │           ▼
                   │  - Unit     │    ┌─────────────┐
                   └─────────────┘    │  GitHub     │
                                      │  Actions    │
                                      │  - Full     │
                                      │    Tests    │
                                      │  - Coverage │
                                      │  - Deploy   │
                                      └─────────────┘
```

---

## Standing Instructions

### For Every Code Change:

1. **Before Committing:**
   - Run `pytest tests/unit/ -v` to verify unit tests pass
   - Run `ruff check src/` to verify no linting errors
   - Run `mypy src/` to verify type safety

2. **Before Pushing:**
   - Run `pytest` to run full test suite
   - Verify coverage meets requirements: `pytest --cov=src`

3. **For Regulatory Changes:**
   - Always update `tests/regulatory/` tests first
   - Update fee values in both code AND tests
   - Verify against official Health Canada documents

4. **For API Changes:**
   - Update OpenAPI schema
   - Update `tests/api/` contract tests
   - Test all error scenarios

5. **For RAG Changes:**
   - Re-run relevance tests
   - Verify search quality hasn't degraded
   - Test with known queries

---

## Test Environment Setup

```bash
# Install test dependencies
pip install -e ".[dev]"

# Or manually:
pip install pytest pytest-cov pytest-asyncio pytest-benchmark httpx

# Set up test environment
export OPENAI_API_KEY="your-key"
export TESTING=true
```

---

## Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit          # Fast, isolated tests
@pytest.mark.integration   # Tests with dependencies
@pytest.mark.regulatory    # Health Canada accuracy tests
@pytest.mark.slow          # Tests > 5 seconds
@pytest.mark.api           # API endpoint tests
@pytest.mark.rag           # RAG system tests
```

Run by marker: `pytest -m "unit and not slow"`
