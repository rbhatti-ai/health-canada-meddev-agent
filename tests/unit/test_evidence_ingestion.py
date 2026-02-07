"""
Unit tests for EvidenceIngestionService.

Tests model validation, content hashing, service construction,
and response models. No DB connection required.

Sprint 2b — 2026-02-07
"""

from __future__ import annotations

from uuid import uuid4

# =========================================================================
# Test: Response Models
# =========================================================================


class TestIngestionResult:
    """Test IngestionResult Pydantic model."""

    def test_default_values(self) -> None:
        from src.core.evidence_ingestion import IngestionResult

        result = IngestionResult()
        assert result.success is False
        assert result.evidence_item_id is None
        assert result.artifact_id is None
        assert result.trace_link_id is None
        assert result.error is None

    def test_successful_result(self) -> None:
        from src.core.evidence_ingestion import IngestionResult

        result = IngestionResult(
            success=True,
            evidence_item_id=uuid4(),
            artifact_id=uuid4(),
            trace_link_id=uuid4(),
        )
        assert result.success is True
        assert result.evidence_item_id is not None
        assert result.artifact_id is not None
        assert result.trace_link_id is not None

    def test_failed_result_with_error(self) -> None:
        from src.core.evidence_ingestion import IngestionResult

        result = IngestionResult(
            success=False,
            error="No database backend available",
        )
        assert result.success is False
        assert result.error == "No database backend available"

    def test_partial_result(self) -> None:
        from src.core.evidence_ingestion import IngestionResult

        result = IngestionResult(
            success=False,
            artifact_id=uuid4(),
            error="Failed to create evidence_item record",
        )
        assert result.artifact_id is not None
        assert result.evidence_item_id is None


class TestBulkIngestionResult:
    """Test BulkIngestionResult Pydantic model."""

    def test_default_values(self) -> None:
        from src.core.evidence_ingestion import BulkIngestionResult

        result = BulkIngestionResult()
        assert result.total == 0
        assert result.succeeded == 0
        assert result.failed == 0
        assert result.results == []

    def test_mixed_results(self) -> None:
        from src.core.evidence_ingestion import BulkIngestionResult, IngestionResult

        result = BulkIngestionResult(
            total=3,
            succeeded=2,
            failed=1,
            results=[
                IngestionResult(success=True),
                IngestionResult(success=True),
                IngestionResult(success=False, error="DB error"),
            ],
        )
        assert result.total == 3
        assert result.succeeded == 2
        assert result.failed == 1
        assert len(result.results) == 3

    def test_all_succeeded(self) -> None:
        from src.core.evidence_ingestion import BulkIngestionResult, IngestionResult

        result = BulkIngestionResult(
            total=2,
            succeeded=2,
            failed=0,
            results=[
                IngestionResult(success=True),
                IngestionResult(success=True),
            ],
        )
        assert result.failed == 0

    def test_all_failed(self) -> None:
        from src.core.evidence_ingestion import BulkIngestionResult, IngestionResult

        result = BulkIngestionResult(
            total=2,
            succeeded=0,
            failed=2,
            results=[
                IngestionResult(success=False, error="err1"),
                IngestionResult(success=False, error="err2"),
            ],
        )
        assert result.succeeded == 0
        assert result.failed == 2


# =========================================================================
# Test: Content Hash
# =========================================================================


class TestContentHash:
    """Test the static content hash method."""

    def test_hash_returns_string(self) -> None:
        from src.core.evidence_ingestion import EvidenceIngestionService

        result = EvidenceIngestionService.compute_content_hash(b"test content")
        assert isinstance(result, str)

    def test_hash_is_sha256_length(self) -> None:
        from src.core.evidence_ingestion import EvidenceIngestionService

        result = EvidenceIngestionService.compute_content_hash(b"test content")
        assert len(result) == 64  # SHA-256 hex digest

    def test_hash_is_deterministic(self) -> None:
        from src.core.evidence_ingestion import EvidenceIngestionService

        h1 = EvidenceIngestionService.compute_content_hash(b"same content")
        h2 = EvidenceIngestionService.compute_content_hash(b"same content")
        assert h1 == h2

    def test_hash_differs_for_different_content(self) -> None:
        from src.core.evidence_ingestion import EvidenceIngestionService

        h1 = EvidenceIngestionService.compute_content_hash(b"content A")
        h2 = EvidenceIngestionService.compute_content_hash(b"content B")
        assert h1 != h2

    def test_hash_empty_bytes(self) -> None:
        from src.core.evidence_ingestion import EvidenceIngestionService

        result = EvidenceIngestionService.compute_content_hash(b"")
        assert isinstance(result, str)
        assert len(result) == 64

    def test_hash_known_value(self) -> None:
        """Verify against a known SHA-256 hash."""
        import hashlib

        from src.core.evidence_ingestion import EvidenceIngestionService

        content = b"regulatory evidence document"
        expected = hashlib.sha256(content).hexdigest()
        actual = EvidenceIngestionService.compute_content_hash(content)
        assert actual == expected

    def test_hash_large_content(self) -> None:
        from src.core.evidence_ingestion import EvidenceIngestionService

        large_content = b"x" * 10_000_000  # 10MB
        result = EvidenceIngestionService.compute_content_hash(large_content)
        assert len(result) == 64


# =========================================================================
# Test: Service Construction
# =========================================================================


class TestEvidenceIngestionServiceInit:
    """Test service construction and singleton."""

    def test_service_creates(self) -> None:
        from src.core.evidence_ingestion import EvidenceIngestionService

        service = EvidenceIngestionService()
        assert service is not None

    def test_service_has_repo(self) -> None:
        from src.core.evidence_ingestion import EvidenceIngestionService

        service = EvidenceIngestionService()
        assert service._repo is not None

    def test_service_has_trace_engine(self) -> None:
        from src.core.evidence_ingestion import EvidenceIngestionService

        service = EvidenceIngestionService()
        assert service._trace_engine is not None

    def test_singleton_returns_same_instance(self) -> None:
        import src.core.evidence_ingestion as mod
        from src.core.evidence_ingestion import get_evidence_ingestion_service

        mod._service = None

        s1 = get_evidence_ingestion_service()
        s2 = get_evidence_ingestion_service()
        assert s1 is s2

        mod._service = None

    def test_singleton_reset(self) -> None:
        import src.core.evidence_ingestion as mod

        mod._service = None
        s1 = mod.get_evidence_ingestion_service()
        mod._service = None
        s2 = mod.get_evidence_ingestion_service()
        assert s1 is not s2


# =========================================================================
# Test: Ingest without DB (best-effort returns error)
# =========================================================================


class TestIngestWithoutDB:
    """Test ingestion behavior when no DB is available."""

    def _make_service_no_db(self):
        from src.core.evidence_ingestion import EvidenceIngestionService

        service = EvidenceIngestionService()
        # Force no DB
        service._repo._use_supabase = False
        service._repo._use_local = False
        return service

    def test_ingest_returns_error_no_db(self) -> None:
        service = self._make_service_no_db()
        result = service.ingest_evidence(
            organization_id=uuid4(),
            device_version_id=uuid4(),
            evidence_type="test_report",
            title="Test Report v1",
        )
        assert result.success is False
        assert result.error is not None

    def test_bulk_ingest_all_fail_no_db(self) -> None:
        service = self._make_service_no_db()
        items = [
            {"evidence_type": "test_report", "title": "Report 1"},
            {"evidence_type": "test_report", "title": "Report 2"},
        ]
        result = service.bulk_ingest(
            organization_id=uuid4(),
            device_version_id=uuid4(),
            items=items,
        )
        assert result.total == 2
        assert result.failed == 2
        assert result.succeeded == 0

    def test_get_unlinked_evidence_returns_empty_no_db(self) -> None:
        service = self._make_service_no_db()
        result = service.get_unlinked_evidence(uuid4())
        assert result == []

    def test_get_evidence_for_claim_returns_empty_no_db(self) -> None:
        service = self._make_service_no_db()
        result = service.get_evidence_for_claim(uuid4())
        assert result == []

    def test_get_evidence_for_test_returns_empty_no_db(self) -> None:
        service = self._make_service_no_db()
        result = service.get_evidence_for_test("verification_test", uuid4())
        assert result == []
