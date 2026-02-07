"""
Unit tests for AttestationService.

Tests model validation, attestation types, status computation,
and service construction. No DB connection required.

Sprint 2c — 2026-02-07
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

# =========================================================================
# Test: Attestation Model
# =========================================================================


class TestAttestationModel:
    """Test Attestation Pydantic model."""

    def _make_attestation(self, **overrides: Any):
        from src.core.attestation_service import Attestation

        defaults: dict[str, Any] = {
            "organization_id": uuid4(),
            "artifact_id": uuid4(),
            "attested_by": uuid4(),
            "attestation_type": "reviewed",
        }
        defaults.update(overrides)
        return Attestation(**defaults)

    def test_create_minimal(self) -> None:
        att = self._make_attestation()
        assert att.attestation_type == "reviewed"

    def test_id_defaults_to_none(self) -> None:
        att = self._make_attestation()
        assert att.id is None

    def test_created_at_defaults_to_none(self) -> None:
        att = self._make_attestation()
        assert att.created_at is None

    def test_note_defaults_to_none(self) -> None:
        att = self._make_attestation()
        assert att.attestation_note is None

    def test_json_defaults_to_empty_dict(self) -> None:
        att = self._make_attestation()
        assert att.attestation_json == {}

    def test_artifact_link_id_defaults_to_none(self) -> None:
        att = self._make_attestation()
        assert att.artifact_link_id is None

    def test_approved_type(self) -> None:
        att = self._make_attestation(attestation_type="approved")
        assert att.attestation_type == "approved"

    def test_rejected_type(self) -> None:
        att = self._make_attestation(attestation_type="rejected")
        assert att.attestation_type == "rejected"

    def test_acknowledged_type(self) -> None:
        att = self._make_attestation(attestation_type="acknowledged")
        assert att.attestation_type == "acknowledged"

    def test_to_db_dict_excludes_id(self) -> None:
        att = self._make_attestation()
        data = att.to_db_dict()
        assert "id" not in data

    def test_to_db_dict_excludes_created_at(self) -> None:
        att = self._make_attestation()
        data = att.to_db_dict()
        assert "created_at" not in data

    def test_to_db_dict_converts_uuid_to_str(self) -> None:
        org_id = uuid4()
        att = self._make_attestation(organization_id=org_id)
        data = att.to_db_dict()
        assert data["organization_id"] == str(org_id)

    def test_to_db_dict_excludes_none_link_id(self) -> None:
        att = self._make_attestation(artifact_link_id=None)
        data = att.to_db_dict()
        assert "artifact_link_id" not in data

    def test_to_db_dict_includes_note(self) -> None:
        att = self._make_attestation(attestation_note="Reviewed per SOP-042")
        data = att.to_db_dict()
        assert data["attestation_note"] == "Reviewed per SOP-042"

    def test_to_db_dict_includes_json(self) -> None:
        att = self._make_attestation(attestation_json={"reviewer_role": "QA Lead"})
        data = att.to_db_dict()
        assert data["attestation_json"] == {"reviewer_role": "QA Lead"}

    def test_from_db_row(self) -> None:
        from src.core.attestation_service import Attestation

        row = {
            "id": str(uuid4()),
            "organization_id": str(uuid4()),
            "artifact_id": str(uuid4()),
            "attested_by": str(uuid4()),
            "attestation_type": "approved",
            "attestation_note": "LGTM",
            "attestation_json": {},
            "created_at": "2026-02-07T12:00:00+00:00",
        }
        att = Attestation.from_db_row(row)
        assert att.attestation_type == "approved"
        assert att.attestation_note == "LGTM"

    def test_from_db_row_ignores_extra_fields(self) -> None:
        from src.core.attestation_service import Attestation

        row = {
            "id": str(uuid4()),
            "organization_id": str(uuid4()),
            "artifact_id": str(uuid4()),
            "attestation_type": "reviewed",
            "attestation_json": {},
            "extra_col": "ignored",
        }
        att = Attestation.from_db_row(row)
        assert att.attestation_type == "reviewed"

    def test_link_attestation(self) -> None:
        """Attestation with artifact_link_id instead of artifact_id."""
        att = self._make_attestation(
            artifact_id=None,
            artifact_link_id=uuid4(),
        )
        assert att.artifact_id is None
        assert att.artifact_link_id is not None


# =========================================================================
# Test: AttestationStatus Model
# =========================================================================


class TestAttestationStatusModel:
    """Test AttestationStatus model."""

    def test_default_status(self) -> None:
        from src.core.attestation_service import AttestationStatus

        status = AttestationStatus(artifact_id=uuid4())
        assert status.total_attestations == 0
        assert status.latest_type is None
        assert status.is_approved is False
        assert status.is_rejected is False
        assert status.attestations == []

    def test_approved_status(self) -> None:
        from src.core.attestation_service import AttestationStatus

        status = AttestationStatus(
            artifact_id=uuid4(),
            total_attestations=1,
            latest_type="approved",
            is_approved=True,
        )
        assert status.is_approved is True
        assert status.is_rejected is False

    def test_rejected_status(self) -> None:
        from src.core.attestation_service import AttestationStatus

        status = AttestationStatus(
            artifact_id=uuid4(),
            total_attestations=2,
            latest_type="rejected",
            is_rejected=True,
        )
        assert status.is_rejected is True


# =========================================================================
# Test: AttestationService construction
# =========================================================================


class TestAttestationServiceInit:
    """Test service construction and singleton."""

    def test_service_creates(self) -> None:
        from src.core.attestation_service import AttestationService

        service = AttestationService()
        assert service is not None

    def test_service_has_repo(self) -> None:
        from src.core.attestation_service import AttestationService

        service = AttestationService()
        assert service._repo is not None

    def test_valid_types_list(self) -> None:
        from src.core.attestation_service import AttestationService

        assert "reviewed" in AttestationService.VALID_TYPES
        assert "approved" in AttestationService.VALID_TYPES
        assert "rejected" in AttestationService.VALID_TYPES
        assert "acknowledged" in AttestationService.VALID_TYPES
        assert len(AttestationService.VALID_TYPES) == 4

    def test_table_constant(self) -> None:
        from src.core.attestation_service import AttestationService

        assert AttestationService.TABLE == "attestations"

    def test_singleton_returns_same_instance(self) -> None:
        import src.core.attestation_service as mod
        from src.core.attestation_service import get_attestation_service

        mod._service = None

        s1 = get_attestation_service()
        s2 = get_attestation_service()
        assert s1 is s2

        mod._service = None

    def test_singleton_reset(self) -> None:
        import src.core.attestation_service as mod

        mod._service = None
        s1 = mod.get_attestation_service()
        mod._service = None
        s2 = mod.get_attestation_service()
        assert s1 is not s2


# =========================================================================
# Test: Validation
# =========================================================================


class TestAttestationValidation:
    """Test attestation type validation."""

    def _make_service_no_db(self):
        from src.core.attestation_service import AttestationService

        service = AttestationService()
        service._repo._use_supabase = False
        service._repo._use_local = False
        return service

    def test_invalid_type_returns_none_artifact(self) -> None:
        service = self._make_service_no_db()
        result = service.attest_artifact(
            organization_id=uuid4(),
            artifact_id=uuid4(),
            attested_by=uuid4(),
            attestation_type="invalid_type",
        )
        assert result is None

    def test_invalid_type_returns_none_link(self) -> None:
        service = self._make_service_no_db()
        result = service.attest_link(
            organization_id=uuid4(),
            artifact_link_id=uuid4(),
            attested_by=uuid4(),
            attestation_type="invalid_type",
        )
        assert result is None

    def test_no_db_attest_artifact_returns_none(self) -> None:
        service = self._make_service_no_db()
        result = service.attest_artifact(
            organization_id=uuid4(),
            artifact_id=uuid4(),
            attested_by=uuid4(),
            attestation_type="reviewed",
        )
        assert result is None

    def test_no_db_attest_link_returns_none(self) -> None:
        service = self._make_service_no_db()
        result = service.attest_link(
            organization_id=uuid4(),
            artifact_link_id=uuid4(),
            attested_by=uuid4(),
            attestation_type="approved",
        )
        assert result is None

    def test_no_db_unattested_items_returns_empty(self) -> None:
        service = self._make_service_no_db()
        result = service.get_unattested_items(uuid4())
        assert result == []

    def test_no_db_audit_trail_returns_empty(self) -> None:
        service = self._make_service_no_db()
        result = service.get_attestation_audit_trail(uuid4())
        assert result == []

    def test_no_db_status_returns_default(self) -> None:
        service = self._make_service_no_db()
        status = service.get_attestation_status(uuid4())
        assert status.total_attestations == 0
        assert status.is_approved is False

    def test_no_db_link_audit_trail_returns_empty(self) -> None:
        service = self._make_service_no_db()
        result = service.get_link_attestation_audit_trail(uuid4())
        assert result == []
