"""
Evidence Ingestion Service — Ingest evidence and connect to regulatory twin.

Workflow:
  1. Create artifact (file metadata + content hash)
  2. Create evidence_item (typed, linked to device version)
  3. Create trace_link to the relevant claim/test/control
  4. Optionally log AI assist via ai_runs if AI helped classify

Design:
  - Best-effort persistence (never crashes on DB failure)
  - Uses TwinRepository for dual Supabase/local Postgres support
  - Returns structured results for every operation
  - Detects unlinked evidence for gap analysis

Sprint 2b — 2026-02-07
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.core.regulatory_twin import EvidenceItem
from src.core.traceability import TraceabilityEngine

logger = logging.getLogger(__name__)


# =========================================================================
# Response Models
# =========================================================================


class IngestionResult(BaseModel):
    """Result of a single evidence ingestion."""

    success: bool = False
    evidence_item_id: UUID | None = None
    artifact_id: UUID | None = None
    trace_link_id: UUID | None = None
    error: str | None = None


class BulkIngestionResult(BaseModel):
    """Result of a bulk evidence ingestion."""

    total: int = 0
    succeeded: int = 0
    failed: int = 0
    results: list[IngestionResult] = Field(default_factory=list)


# =========================================================================
# Evidence Ingestion Service
# =========================================================================


class EvidenceIngestionService:
    """Ingest evidence and connect it to the regulatory twin.

    Workflow:
      1. Create artifact (file metadata + content hash)
      2. Create evidence_item (typed, with strength assessment)
      3. Create trace_link to the relevant claim/test/control
      4. Optionally log AI assist via ai_runs if AI helped classify

    All operations are best-effort: never crash on DB failure.
    """

    def __init__(self) -> None:
        from src.persistence.twin_repository import TwinRepository

        self._repo = TwinRepository()
        self._trace_engine = TraceabilityEngine()

    @property
    def is_available(self) -> bool:
        """Check if DB backend is available."""
        return self._repo.is_available

    # -----------------------------------------------------------------
    # INGEST SINGLE EVIDENCE
    # -----------------------------------------------------------------

    def ingest_evidence(
        self,
        organization_id: UUID | str,
        device_version_id: UUID | str,
        evidence_type: str,
        title: str,
        artifact_type: str = "document",
        artifact_title: str | None = None,
        description: str | None = None,
        storage_uri: str | None = None,
        content_hash: str | None = None,
        content_mime: str | None = None,
        content_bytes: int | None = None,
        source_reference: str | None = None,
        strength: str | None = None,
        linked_to_type: str | None = None,
        linked_to_id: UUID | str | None = None,
        link_relationship: str | None = None,
        created_by: UUID | str | None = None,
    ) -> IngestionResult:
        """Ingest a single piece of evidence.

        Steps:
          1. Create artifact record (file/document metadata)
          2. Create evidence_item linked to device version
          3. Optionally create trace_link if linked_to is specified

        Returns IngestionResult with IDs of created records.
        """
        result = IngestionResult()
        org_id = str(organization_id)
        dv_id = str(device_version_id)

        if not self.is_available:
            result.error = "No database backend available"
            return result

        # Step 1: Create artifact
        artifact_data: dict[str, Any] = {
            "organization_id": org_id,
            "artifact_type": artifact_type,
            "title": artifact_title or title,
            "description": description,
            "storage_uri": storage_uri,
            "content_sha256": content_hash,
            "content_mime": content_mime,
        }
        if content_bytes is not None:
            artifact_data["content_bytes"] = content_bytes
        if created_by:
            artifact_data["created_by"] = str(created_by)

        # Remove None values
        artifact_data = {k: v for k, v in artifact_data.items() if v is not None}

        artifact_row = self._insert_artifact(artifact_data)
        if not artifact_row:
            result.error = "Failed to create artifact record"
            return result

        artifact_id_str = artifact_row.get("id", "")
        if artifact_id_str:
            result.artifact_id = UUID(str(artifact_id_str))

        # Step 2: Create evidence_item
        evidence = EvidenceItem(
            organization_id=UUID(org_id),
            device_version_id=UUID(dv_id),
            evidence_type=evidence_type,  # type: ignore[arg-type]
            title=title,
            description=description,
            source_ref=source_reference,
            artifact_id=result.artifact_id,
            strength=strength,  # type: ignore[arg-type]
            created_by=UUID(str(created_by)) if created_by else None,
        )

        evidence_row = self._repo.create("evidence_items", evidence)
        if not evidence_row:
            result.error = "Failed to create evidence_item record"
            return result

        evidence_id_str = evidence_row.get("id", "")
        if evidence_id_str:
            result.evidence_item_id = UUID(str(evidence_id_str))

        # Step 3: Create trace_link (optional)
        if linked_to_type and linked_to_id and link_relationship:
            link = self._trace_engine.create_link(
                organization_id=org_id,
                source_type=linked_to_type,
                source_id=str(linked_to_id),
                target_type="evidence_item",
                target_id=str(result.evidence_item_id),
                relationship=link_relationship,
                rationale=f"Evidence ingested: {title}",
                created_by=str(created_by) if created_by else None,
            )
            if link and link.id:
                result.trace_link_id = link.id

        result.success = True
        return result

    # -----------------------------------------------------------------
    # BULK INGEST
    # -----------------------------------------------------------------

    def bulk_ingest(
        self,
        organization_id: UUID | str,
        device_version_id: UUID | str,
        items: list[dict[str, Any]],
    ) -> BulkIngestionResult:
        """Ingest multiple evidence items.

        Each item dict should contain keys matching ingest_evidence params:
          - evidence_type, title (required)
          - artifact_type, description, storage_uri, etc. (optional)
          - linked_to_type, linked_to_id, link_relationship (optional)

        Returns BulkIngestionResult with per-item results.
        """
        bulk_result = BulkIngestionResult(total=len(items))

        for item in items:
            single_result = self.ingest_evidence(
                organization_id=organization_id,
                device_version_id=device_version_id,
                evidence_type=item.get("evidence_type", "test_report"),
                title=item.get("title", "Untitled Evidence"),
                artifact_type=item.get("artifact_type", "document"),
                artifact_title=item.get("artifact_title"),
                description=item.get("description"),
                storage_uri=item.get("storage_uri"),
                content_hash=item.get("content_hash"),
                content_mime=item.get("content_mime"),
                content_bytes=item.get("content_bytes"),
                source_reference=item.get("source_reference"),
                strength=item.get("strength"),
                linked_to_type=item.get("linked_to_type"),
                linked_to_id=item.get("linked_to_id"),
                link_relationship=item.get("link_relationship"),
                created_by=item.get("created_by"),
            )
            bulk_result.results.append(single_result)
            if single_result.success:
                bulk_result.succeeded += 1
            else:
                bulk_result.failed += 1

        return bulk_result

    # -----------------------------------------------------------------
    # QUERY
    # -----------------------------------------------------------------

    def get_evidence_for_claim(self, claim_id: UUID | str) -> list[dict[str, Any]]:
        """Get all evidence items linked to a claim (via trace_links).

        Follows: claim -[supported_by]-> evidence_item
        """
        links = self._trace_engine.get_links_from("claim", claim_id)
        evidence_ids = [
            str(link.target_id) for link in links if link.target_type == "evidence_item"
        ]

        results: list[dict[str, Any]] = []
        for eid in evidence_ids:
            row = self._repo.get_by_id("evidence_items", eid)
            if row:
                results.append(row)
        return results

    def get_evidence_for_test(self, test_type: str, test_id: UUID | str) -> list[dict[str, Any]]:
        """Get evidence items linked to a verification/validation test."""
        links = self._trace_engine.get_links_from(test_type, test_id)
        evidence_ids = [
            str(link.target_id) for link in links if link.target_type == "evidence_item"
        ]

        results: list[dict[str, Any]] = []
        for eid in evidence_ids:
            row = self._repo.get_by_id("evidence_items", eid)
            if row:
                results.append(row)
        return results

    def get_unlinked_evidence(self, device_version_id: UUID | str) -> list[dict[str, Any]]:
        """Find evidence items not connected to any claim/test/control.

        Returns evidence_items for the device version that have no
        incoming trace_links pointing to them.
        """
        all_evidence = self._repo.get_by_device_version("evidence_items", device_version_id)

        unlinked: list[dict[str, Any]] = []
        for ev in all_evidence:
            ev_id = ev.get("id", "")
            if not ev_id:
                continue
            # Check if anything links TO this evidence item
            links_to = self._trace_engine.get_links_to("evidence_item", ev_id)
            if not links_to:
                unlinked.append(ev)

        return unlinked

    # -----------------------------------------------------------------
    # HELPERS
    # -----------------------------------------------------------------

    @staticmethod
    def compute_content_hash(content: bytes) -> str:
        """Compute SHA-256 hash of content for integrity verification."""
        return hashlib.sha256(content).hexdigest()

    def _insert_artifact(self, data: dict[str, Any]) -> dict[str, Any] | None:
        """Insert into artifacts table (not a RegulatoryTwinBase model)."""
        if self._repo._use_supabase:
            return self._repo._supabase_insert("artifacts", data)
        return self._repo._local_insert("artifacts", data)


# =========================================================================
# Singleton
# =========================================================================

_service: EvidenceIngestionService | None = None


def get_evidence_ingestion_service() -> EvidenceIngestionService:
    """Get or create the singleton EvidenceIngestionService."""
    global _service  # noqa: PLW0603
    if _service is None:
        _service = EvidenceIngestionService()
    return _service
