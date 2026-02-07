"""
Attestation Workflow Service — Human-in-the-loop sign-off.

Every AI output, every trace link, every evidence assessment
can be attested to by a human reviewer.

Uses the existing attestations table:
  - artifact_id OR artifact_link_id (exactly one, enforced by DB CHECK)
  - attestation_type: reviewed, approved, rejected, acknowledged
  - Full audit trail per artifact

Design:
  - Best-effort persistence (never crashes on DB failure)
  - Uses TwinRepository for dual Supabase/local Postgres support
  - Audit trail query for any artifact or link
  - Unattested item detection for workflow dashboards

Sprint 2c — 2026-02-07
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =========================================================================
# Types
# =========================================================================

AttestationType = Literal["reviewed", "approved", "rejected", "acknowledged"]


# =========================================================================
# Models
# =========================================================================


class Attestation(BaseModel):
    """A human attestation on an artifact or artifact_link.

    Maps directly to the attestations DB table.
    """

    id: UUID | None = None
    organization_id: UUID
    artifact_id: UUID | None = None
    artifact_link_id: UUID | None = None
    attested_by: UUID | None = None
    attestation_type: AttestationType
    attestation_note: str | None = None
    attestation_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    def to_db_dict(self) -> dict[str, Any]:
        """Convert to dict for DB insert."""
        data: dict[str, Any] = {}
        for field_name, value in self:
            if value is None:
                continue
            if field_name == "id":
                continue
            if field_name == "created_at":
                continue
            if isinstance(value, UUID):
                data[field_name] = str(value)
            elif isinstance(value, dict):
                data[field_name] = value
            else:
                data[field_name] = value
        return data

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> Attestation:
        """Create from a DB row dict."""
        return cls(**{k: v for k, v in row.items() if k in cls.model_fields})


class AttestationStatus(BaseModel):
    """Summary of attestation status for an artifact."""

    artifact_id: UUID | None = None
    artifact_link_id: UUID | None = None
    total_attestations: int = 0
    latest_type: AttestationType | None = None
    latest_by: UUID | None = None
    latest_at: datetime | None = None
    is_approved: bool = False
    is_rejected: bool = False
    attestations: list[Attestation] = Field(default_factory=list)


# =========================================================================
# Attestation Service
# =========================================================================


class AttestationService:
    """Human-in-the-loop sign-off on artifacts and links.

    Types:
      - reviewed:     human reviewed the content
      - approved:     human approved for regulatory use
      - rejected:     human rejected, needs rework
      - acknowledged: human saw it, no opinion

    All operations are best-effort: never crash on DB failure.
    """

    VALID_TYPES = ["reviewed", "approved", "rejected", "acknowledged"]
    TABLE = "attestations"

    def __init__(self) -> None:
        from src.persistence.twin_repository import TwinRepository

        self._repo = TwinRepository()

    @property
    def is_available(self) -> bool:
        """Check if DB backend is available."""
        return self._repo.is_available

    # -----------------------------------------------------------------
    # CREATE
    # -----------------------------------------------------------------

    def attest_artifact(
        self,
        organization_id: UUID | str,
        artifact_id: UUID | str,
        attested_by: UUID | str,
        attestation_type: str,
        note: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Attestation | None:
        """Create an attestation for an artifact.

        Returns the created Attestation or None on failure.
        """
        if attestation_type not in self.VALID_TYPES:
            logger.warning("Invalid attestation type: %s", attestation_type)
            return None

        attestation = Attestation(
            organization_id=UUID(str(organization_id)),
            artifact_id=UUID(str(artifact_id)),
            attested_by=UUID(str(attested_by)),
            attestation_type=attestation_type,  # type: ignore[arg-type]
            attestation_note=note,
            attestation_json=metadata or {},
        )

        return self._insert_attestation(attestation)

    def attest_link(
        self,
        organization_id: UUID | str,
        artifact_link_id: UUID | str,
        attested_by: UUID | str,
        attestation_type: str,
        note: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Attestation | None:
        """Create an attestation for an artifact_link.

        Returns the created Attestation or None on failure.
        """
        if attestation_type not in self.VALID_TYPES:
            logger.warning("Invalid attestation type: %s", attestation_type)
            return None

        attestation = Attestation(
            organization_id=UUID(str(organization_id)),
            artifact_link_id=UUID(str(artifact_link_id)),
            attested_by=UUID(str(attested_by)),
            attestation_type=attestation_type,  # type: ignore[arg-type]
            attestation_note=note,
            attestation_json=metadata or {},
        )

        return self._insert_attestation(attestation)

    # -----------------------------------------------------------------
    # QUERY
    # -----------------------------------------------------------------

    def get_attestation_status(self, artifact_id: UUID | str) -> AttestationStatus:
        """Get the attestation status for an artifact.

        Returns summary including latest attestation type and full history.
        """
        status = AttestationStatus(artifact_id=UUID(str(artifact_id)))

        rows = self._repo.get_by_field(self.TABLE, "artifact_id", str(artifact_id))

        attestations = []
        for row in rows:
            try:
                attestations.append(Attestation.from_db_row(row))
            except Exception as exc:
                logger.warning("Failed to parse attestation row: %s", exc)

        status.total_attestations = len(attestations)
        status.attestations = attestations

        if attestations:
            # Sort by created_at descending to find latest
            sorted_att = sorted(
                attestations,
                key=lambda a: a.created_at or datetime.min,
                reverse=True,
            )
            latest = sorted_att[0]
            status.latest_type = latest.attestation_type
            status.latest_by = latest.attested_by
            status.latest_at = latest.created_at
            status.is_approved = any(a.attestation_type == "approved" for a in attestations)
            status.is_rejected = any(a.attestation_type == "rejected" for a in attestations)

        return status

    def get_attestation_audit_trail(self, artifact_id: UUID | str) -> list[Attestation]:
        """Get the full attestation audit trail for an artifact.

        Returns all attestations in chronological order.
        """
        rows = self._repo.get_by_field(self.TABLE, "artifact_id", str(artifact_id))

        attestations = []
        for row in rows:
            try:
                attestations.append(Attestation.from_db_row(row))
            except Exception as exc:
                logger.warning("Failed to parse attestation row: %s", exc)

        # Sort chronologically
        attestations.sort(key=lambda a: a.created_at or datetime.min)
        return attestations

    def get_unattested_items(self, organization_id: UUID | str) -> list[dict[str, Any]]:
        """Find artifacts that have not been attested.

        Returns artifacts for the organization that have zero attestations.
        """
        if not self.is_available:
            return []

        # Get all artifacts for org
        all_artifacts = self._repo.get_by_field(
            "artifacts", "organization_id", str(organization_id)
        )

        # Get all attestations for org
        all_attestations = self._repo.get_by_field(
            self.TABLE, "organization_id", str(organization_id)
        )

        # Build set of attested artifact IDs
        attested_ids: set[str] = set()
        for att in all_attestations:
            aid = att.get("artifact_id")
            if aid:
                attested_ids.add(str(aid))

        # Filter to unattested
        unattested = [art for art in all_artifacts if str(art.get("id", "")) not in attested_ids]

        return unattested

    def get_link_attestation_audit_trail(self, artifact_link_id: UUID | str) -> list[Attestation]:
        """Get the full attestation audit trail for an artifact_link."""
        rows = self._repo.get_by_field(self.TABLE, "artifact_link_id", str(artifact_link_id))

        attestations = []
        for row in rows:
            try:
                attestations.append(Attestation.from_db_row(row))
            except Exception as exc:
                logger.warning("Failed to parse attestation row: %s", exc)

        attestations.sort(key=lambda a: a.created_at or datetime.min)
        return attestations

    # -----------------------------------------------------------------
    # HELPERS
    # -----------------------------------------------------------------

    def _insert_attestation(self, attestation: Attestation) -> Attestation | None:
        """Insert an attestation record into the DB."""
        if not self.is_available:
            logger.warning("No DB available for attestation")
            return None

        data = attestation.to_db_dict()

        try:
            if self._repo._use_supabase:
                result = self._repo._supabase_insert(self.TABLE, data)
            else:
                result = self._repo._local_insert(self.TABLE, data)

            if result:
                merged = {**data, **result}
                return Attestation.from_db_row(merged)
            return None
        except Exception as exc:
            logger.warning("Insert attestation failed: %s", exc)
            return None


# =========================================================================
# Singleton
# =========================================================================

_service: AttestationService | None = None


def get_attestation_service() -> AttestationService:
    """Get or create the singleton AttestationService."""
    global _service  # noqa: PLW0603
    if _service is None:
        _service = AttestationService()
    return _service
