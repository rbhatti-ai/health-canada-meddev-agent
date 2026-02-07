"""
Traceability, Evidence & Attestation API Routes.

Provides REST endpoints for:
  - Trace link creation and querying
  - Chain traversal and coverage reports
  - Evidence ingestion (single + bulk)
  - Unlinked evidence detection
  - Attestation creation and audit trails

All endpoints are under /api/v1/ and follow regulatory-safe language.

Sprint 2d — 2026-02-07
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1", tags=["traceability"])


# =========================================================================
# Request/Response Models
# =========================================================================


class CreateTraceLinkRequest(BaseModel):
    """Request to create a trace link."""

    organization_id: str
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    relationship: str
    rationale: str | None = None
    created_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TraceLinkResponse(BaseModel):
    """Response for a single trace link."""

    id: str | None = None
    organization_id: str
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    relationship: str
    rationale: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None


class IngestEvidenceRequest(BaseModel):
    """Request to ingest a single evidence item."""

    organization_id: str
    device_version_id: str
    evidence_type: str
    title: str
    artifact_type: str = "document"
    artifact_title: str | None = None
    description: str | None = None
    storage_uri: str | None = None
    content_hash: str | None = None
    content_mime: str | None = None
    content_bytes: int | None = None
    source_reference: str | None = None
    strength: str | None = None
    linked_to_type: str | None = None
    linked_to_id: str | None = None
    link_relationship: str | None = None
    created_by: str | None = None


class BulkIngestRequest(BaseModel):
    """Request to ingest multiple evidence items."""

    organization_id: str
    device_version_id: str
    items: list[dict[str, Any]]


class CreateAttestationRequest(BaseModel):
    """Request to create an attestation."""

    organization_id: str
    artifact_id: str | None = None
    artifact_link_id: str | None = None
    attested_by: str
    attestation_type: str
    note: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# =========================================================================
# Trace Link Endpoints
# =========================================================================


@router.post("/trace-links")
async def create_trace_link(request: CreateTraceLinkRequest) -> dict[str, Any]:
    """Create a trace link between two regulatory entities."""
    from src.core.traceability import get_traceability_engine

    engine = get_traceability_engine()

    # Validate first
    if not engine.validate_link(request.source_type, request.target_type, request.relationship):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid relationship: {request.source_type} -[{request.relationship}]-> {request.target_type}",
        )

    link = engine.create_link(
        organization_id=request.organization_id,
        source_type=request.source_type,
        source_id=request.source_id,
        target_type=request.target_type,
        target_id=request.target_id,
        relationship=request.relationship,
        rationale=request.rationale,
        created_by=request.created_by,
        metadata=request.metadata,
    )

    if not link:
        raise HTTPException(status_code=500, detail="Failed to create trace link")

    return {
        "id": str(link.id) if link.id else None,
        "source_type": link.source_type,
        "source_id": str(link.source_id),
        "target_type": link.target_type,
        "target_id": str(link.target_id),
        "relationship": link.relationship,
        "rationale": link.rationale,
    }


@router.get("/trace-links/by-id/{link_id}")
async def get_trace_link(link_id: str) -> dict[str, Any]:
    """Get a single trace link by ID."""
    from src.core.traceability import get_traceability_engine

    engine = get_traceability_engine()
    link = engine.get_link_by_id(link_id)

    if not link:
        raise HTTPException(status_code=404, detail="Trace link not found")

    return {
        "id": str(link.id) if link.id else None,
        "organization_id": str(link.organization_id),
        "source_type": link.source_type,
        "source_id": str(link.source_id),
        "target_type": link.target_type,
        "target_id": str(link.target_id),
        "relationship": link.relationship,
        "rationale": link.rationale,
        "metadata": link.metadata,
        "created_at": str(link.created_at) if link.created_at else None,
    }


@router.get("/trace-links/valid-relationships")
async def get_valid_relationships() -> dict[str, Any]:
    """Get all valid relationship types."""
    from src.core.traceability import TraceabilityEngine

    rels = TraceabilityEngine.get_valid_relationships()
    # Convert tuple keys to strings for JSON
    return {"relationships": {f"{src}->{tgt}": rel_list for (src, tgt), rel_list in rels.items()}}


# =========================================================================
# Chain Traversal Endpoints
# =========================================================================


@router.get("/trace-chains/{entity_type}/{entity_id}")
async def get_trace_chain(entity_type: str, entity_id: str) -> dict[str, Any]:
    """Get the full trace chain from an entity down to evidence."""
    from src.core.traceability import get_traceability_engine

    engine = get_traceability_engine()
    chain = engine.get_full_chain(entity_type, entity_id)

    def node_to_dict(node: Any) -> dict[str, Any]:
        return {
            "entity_type": node.entity_type,
            "entity_id": str(node.entity_id),
            "relationship": node.relationship,
            "children": [node_to_dict(c) for c in node.children],
        }

    return {
        "root_type": chain.root_type,
        "root_id": str(chain.root_id),
        "total_links": chain.total_links,
        "max_depth": chain.max_depth,
        "nodes": [node_to_dict(n) for n in chain.nodes],
    }


@router.get("/coverage/{device_version_id}")
async def get_coverage_report(device_version_id: str, organization_id: str) -> dict[str, Any]:
    """Get coverage report for a device version.

    Shows for each claim: linked hazards, controls, tests, and evidence.
    """
    from src.core.traceability import get_traceability_engine

    engine = get_traceability_engine()
    report = engine.get_coverage_report(device_version_id, organization_id)

    return {
        "device_version_id": str(report.device_version_id),
        "total_claims": report.total_claims,
        "claims_with_full_coverage": report.claims_with_full_coverage,
        "claims_with_partial_coverage": report.claims_with_partial_coverage,
        "claims_with_no_coverage": report.claims_with_no_coverage,
        "coverage_percentage": report.coverage_percentage,
        "claims": [
            {
                "claim_id": str(c.claim_id),
                "hazards": [str(h) for h in c.hazards],
                "risk_controls": [str(r) for r in c.risk_controls],
                "verification_tests": [str(v) for v in c.verification_tests],
                "validation_tests": [str(v) for v in c.validation_tests],
                "evidence_items": [str(e) for e in c.evidence_items],
                "has_hazard_link": c.has_hazard_link,
                "has_control_link": c.has_control_link,
                "has_test_link": c.has_test_link,
                "has_evidence_link": c.has_evidence_link,
            }
            for c in report.claims
        ],
    }


# =========================================================================
# Evidence Endpoints
# =========================================================================


@router.post("/evidence")
async def ingest_evidence(request: IngestEvidenceRequest) -> dict[str, Any]:
    """Ingest a single evidence item with artifact and optional trace link."""
    from src.core.evidence_ingestion import get_evidence_ingestion_service

    service = get_evidence_ingestion_service()
    result = service.ingest_evidence(
        organization_id=request.organization_id,
        device_version_id=request.device_version_id,
        evidence_type=request.evidence_type,
        title=request.title,
        artifact_type=request.artifact_type,
        artifact_title=request.artifact_title,
        description=request.description,
        storage_uri=request.storage_uri,
        content_hash=request.content_hash,
        content_mime=request.content_mime,
        content_bytes=request.content_bytes,
        source_reference=request.source_reference,
        strength=request.strength,
        linked_to_type=request.linked_to_type,
        linked_to_id=request.linked_to_id,
        link_relationship=request.link_relationship,
        created_by=request.created_by,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Evidence ingestion failed")

    return {
        "success": True,
        "evidence_item_id": str(result.evidence_item_id) if result.evidence_item_id else None,
        "artifact_id": str(result.artifact_id) if result.artifact_id else None,
        "trace_link_id": str(result.trace_link_id) if result.trace_link_id else None,
    }


@router.post("/evidence/bulk")
async def bulk_ingest_evidence(request: BulkIngestRequest) -> dict[str, Any]:
    """Ingest multiple evidence items."""
    from src.core.evidence_ingestion import get_evidence_ingestion_service

    service = get_evidence_ingestion_service()
    result = service.bulk_ingest(
        organization_id=request.organization_id,
        device_version_id=request.device_version_id,
        items=request.items,
    )

    return {
        "total": result.total,
        "succeeded": result.succeeded,
        "failed": result.failed,
        "results": [
            {
                "success": r.success,
                "evidence_item_id": str(r.evidence_item_id) if r.evidence_item_id else None,
                "artifact_id": str(r.artifact_id) if r.artifact_id else None,
                "error": r.error,
            }
            for r in result.results
        ],
    }


@router.get("/evidence/{device_version_id}")
async def get_evidence_for_device(device_version_id: str) -> dict[str, Any]:
    """List all evidence items for a device version."""
    from src.persistence.twin_repository import get_twin_repository

    repo = get_twin_repository()
    items = repo.get_by_device_version("evidence_items", device_version_id)
    return {"device_version_id": device_version_id, "evidence_items": items}


@router.get("/evidence/unlinked/{device_version_id}")
async def get_unlinked_evidence(device_version_id: str) -> dict[str, Any]:
    """Find evidence items not connected to any claim, test, or control."""
    from src.core.evidence_ingestion import get_evidence_ingestion_service

    service = get_evidence_ingestion_service()
    unlinked = service.get_unlinked_evidence(device_version_id)
    return {
        "device_version_id": device_version_id,
        "unlinked_count": len(unlinked),
        "unlinked_evidence": unlinked,
    }


# =========================================================================
# Attestation Endpoints
# =========================================================================


@router.post("/attestations")
async def create_attestation(request: CreateAttestationRequest) -> dict[str, Any]:
    """Create an attestation (human sign-off) on an artifact or link."""
    from src.core.attestation_service import get_attestation_service

    service = get_attestation_service()

    if request.artifact_id and not request.artifact_link_id:
        att = service.attest_artifact(
            organization_id=request.organization_id,
            artifact_id=request.artifact_id,
            attested_by=request.attested_by,
            attestation_type=request.attestation_type,
            note=request.note,
            metadata=request.metadata,
        )
    elif request.artifact_link_id and not request.artifact_id:
        att = service.attest_link(
            organization_id=request.organization_id,
            artifact_link_id=request.artifact_link_id,
            attested_by=request.attested_by,
            attestation_type=request.attestation_type,
            note=request.note,
            metadata=request.metadata,
        )
    else:
        raise HTTPException(
            status_code=422,
            detail="Provide exactly one of artifact_id or artifact_link_id",
        )

    if not att:
        raise HTTPException(status_code=500, detail="Failed to create attestation")

    return {
        "id": str(att.id) if att.id else None,
        "attestation_type": att.attestation_type,
        "artifact_id": str(att.artifact_id) if att.artifact_id else None,
        "artifact_link_id": str(att.artifact_link_id) if att.artifact_link_id else None,
        "attested_by": str(att.attested_by) if att.attested_by else None,
    }


@router.get("/attestations/pending/{organization_id}")
async def get_pending_attestations(organization_id: str) -> dict[str, Any]:
    """Get artifacts that have not been attested."""
    from src.core.attestation_service import get_attestation_service

    service = get_attestation_service()
    unattested = service.get_unattested_items(organization_id)
    return {
        "organization_id": organization_id,
        "unattested_count": len(unattested),
        "unattested_items": unattested,
    }


@router.get("/attestations/trail/{artifact_id}")
async def get_attestation_trail(artifact_id: str) -> dict[str, Any]:
    """Get the full attestation audit trail for an artifact."""
    from src.core.attestation_service import get_attestation_service

    service = get_attestation_service()
    trail = service.get_attestation_audit_trail(artifact_id)

    return {
        "artifact_id": artifact_id,
        "total_attestations": len(trail),
        "trail": [
            {
                "id": str(a.id) if a.id else None,
                "attestation_type": a.attestation_type,
                "attested_by": str(a.attested_by) if a.attested_by else None,
                "note": a.attestation_note,
                "created_at": str(a.created_at) if a.created_at else None,
            }
            for a in trail
        ],
    }


@router.get("/attestations/status/{artifact_id}")
async def get_attestation_status(artifact_id: str) -> dict[str, Any]:
    """Get the attestation status summary for an artifact."""
    from src.core.attestation_service import get_attestation_service

    service = get_attestation_service()
    status = service.get_attestation_status(artifact_id)

    return {
        "artifact_id": artifact_id,
        "total_attestations": status.total_attestations,
        "latest_type": status.latest_type,
        "is_approved": status.is_approved,
        "is_rejected": status.is_rejected,
    }
