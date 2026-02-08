"""
Confidentiality Classification Service — Sprint 6A.

Provides IP protection classifications for regulatory artifacts.
Supports 4 confidentiality levels aligned with Health Canada CBI requirements.

Per SOR/98-282 Section 43.2:
- Confidential Business Information (CBI) must be identified in submissions
- Trade secrets require specific justification for confidential treatment
- Patent-pending information can reference application numbers

CONFIDENTIALITY LEVELS:
    - public: Can appear in any document or public summary
    - confidential_submission: Redacted from public portions of submission
    - trade_secret: Never disclosed, summarized only
    - patent_pending: Can reference patent application number

Usage:
    service = get_confidentiality_service()
    tag = service.classify("evidence_item", uuid, "trade_secret")
    unclassified = service.get_unclassified(org_id)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from src.core.regulatory_references import get_reference_registry
from src.utils.logging import get_logger

# =============================================================================
# Types
# =============================================================================

ConfidentialityLevel = Literal[
    "public",  # Can appear in any document
    "confidential_submission",  # Redacted from public portions
    "trade_secret",  # Never disclosed, summarized only
    "patent_pending",  # Can reference patent application
]

# Valid entity types that can be classified
CLASSIFIABLE_ENTITY_TYPES = [
    "evidence_item",
    "artifact",
    "claim",
    "document",
    "test_data",
    "design_file",
    "manufacturing_process",
    "supplier_agreement",
]

# =============================================================================
# Models
# =============================================================================


class ConfidentialityTag(BaseModel):
    """IP protection classification for a regulatory entity.

    Each entity (evidence, artifact, claim, etc.) can have one
    confidentiality classification that determines how it can
    be disclosed in regulatory submissions.

    Citations: [SOR/98-282, s.43.2]
    """

    id: UUID | None = Field(default=None, description="Tag ID (assigned on persistence)")
    organization_id: UUID = Field(..., description="Organization that owns this entity")
    entity_type: str = Field(
        ..., description="Type of entity (evidence_item, artifact, claim, etc.)"
    )
    entity_id: UUID = Field(..., description="ID of the classified entity")
    level: ConfidentialityLevel = Field(..., description="Confidentiality level")
    patent_application_number: str | None = Field(
        default=None, description="Patent application number if patent_pending"
    )
    trade_secret_attestation: bool = Field(
        default=False, description="Whether trade secret status has been attested"
    )
    disclosure_restrictions: list[str] = Field(
        default_factory=list, description="Specific disclosure restrictions"
    )
    summary_for_public_use: str | None = Field(
        default=None, description="Public-safe summary if original is confidential"
    )
    justification: str | None = Field(
        default=None, description="Justification for confidential classification"
    )
    harm_if_disclosed: str | None = Field(
        default=None, description="Competitive harm if disclosed (required for CBI)"
    )
    classified_by: UUID | None = Field(default=None, description="User who classified this entity")
    classified_at: datetime | None = Field(default=None, description="When classification was made")
    # Citation (Sprint 5C alignment)
    regulation_ref: str = Field(
        default="SOR-98-282-S43.2", description="Regulatory reference for CBI"
    )
    citation_text: str = Field(default="[SOR/98-282, s.43.2]", description="Formatted citation")


class ConfidentialityReport(BaseModel):
    """Summary report of confidentiality classifications for an organization."""

    organization_id: UUID = Field(..., description="Organization analyzed")
    generated_at: str = Field(..., description="Report generation timestamp")
    total_entities: int = Field(default=0, description="Total entities reviewed")
    public_count: int = Field(default=0, description="Entities classified as public")
    confidential_submission_count: int = Field(
        default=0, description="Confidential submission entities"
    )
    trade_secret_count: int = Field(default=0, description="Trade secret entities")
    patent_pending_count: int = Field(default=0, description="Patent pending entities")
    unclassified_count: int = Field(default=0, description="Unclassified entities")
    requires_cbi_request: bool = Field(default=False, description="Whether CBI request is needed")
    unclassified_entities: list[dict[str, Any]] = Field(
        default_factory=list, description="List of unclassified entity references"
    )


# =============================================================================
# Service Class
# =============================================================================


class ConfidentialityService:
    """
    Manages IP protection classifications for regulatory artifacts.

    Provides methods to:
    - Classify entities by confidentiality level
    - Query classifications
    - Identify unclassified assets
    - Generate CBI-readiness reports

    In-memory storage for now; production would use TwinRepository.

    Usage:
        service = get_confidentiality_service()
        tag = service.classify("evidence_item", uuid, "trade_secret")
    """

    def __init__(self) -> None:
        """Initialize the service with empty storage."""
        self.logger = get_logger(self.__class__.__name__)
        self._tags: dict[tuple[str, UUID], ConfidentialityTag] = {}
        self._citation_registry = get_reference_registry()
        self.logger.info("ConfidentialityService initialized")

    def classify(
        self,
        entity_type: str,
        entity_id: UUID,
        level: ConfidentialityLevel,
        organization_id: UUID,
        classified_by: UUID | None = None,
        patent_application_number: str | None = None,
        justification: str | None = None,
        harm_if_disclosed: str | None = None,
        summary_for_public_use: str | None = None,
        trade_secret_attestation: bool = False,
        disclosure_restrictions: list[str] | None = None,
    ) -> ConfidentialityTag:
        """
        Classify an entity's confidentiality level.

        Args:
            entity_type: Type of entity (evidence_item, artifact, etc.)
            entity_id: UUID of the entity
            level: Confidentiality level to assign
            organization_id: Organization that owns the entity
            classified_by: User making the classification
            patent_application_number: Patent app number if patent_pending
            justification: Reason for confidential classification
            harm_if_disclosed: Competitive harm description (required for CBI)
            summary_for_public_use: Public-safe summary
            trade_secret_attestation: Whether trade secret is attested
            disclosure_restrictions: List of specific restrictions

        Returns:
            ConfidentialityTag with the classification.

        Raises:
            ValueError: If entity_type is not valid or required fields missing.
        """
        if entity_type not in CLASSIFIABLE_ENTITY_TYPES:
            raise ValueError(
                f"Invalid entity_type '{entity_type}'. " f"Valid types: {CLASSIFIABLE_ENTITY_TYPES}"
            )

        if level == "patent_pending" and not patent_application_number:
            raise ValueError("patent_application_number required for patent_pending level")

        if level == "trade_secret" and not trade_secret_attestation:
            self.logger.warning(
                f"Trade secret classification for {entity_type}/{entity_id} "
                "without attestation — attestation recommended"
            )

        tag = ConfidentialityTag(
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            level=level,
            patent_application_number=patent_application_number,
            trade_secret_attestation=trade_secret_attestation,
            disclosure_restrictions=disclosure_restrictions or [],
            summary_for_public_use=summary_for_public_use,
            justification=justification,
            harm_if_disclosed=harm_if_disclosed,
            classified_by=classified_by,
            classified_at=datetime.now(UTC),
        )

        self._tags[(entity_type, entity_id)] = tag
        self.logger.info(
            f"Classified {entity_type}/{entity_id} as {level} " f"for org {organization_id}"
        )

        return tag

    def get_classification(self, entity_type: str, entity_id: UUID) -> ConfidentialityTag | None:
        """
        Get the confidentiality classification for an entity.

        Args:
            entity_type: Type of entity
            entity_id: UUID of the entity

        Returns:
            ConfidentialityTag if found, None otherwise.
        """
        return self._tags.get((entity_type, entity_id))

    def get_all_classifications(self, organization_id: UUID) -> list[ConfidentialityTag]:
        """
        Get all classifications for an organization.

        Args:
            organization_id: Organization to query

        Returns:
            List of all ConfidentialityTag for the organization.
        """
        return [tag for tag in self._tags.values() if tag.organization_id == organization_id]

    def get_by_level(
        self, organization_id: UUID, level: ConfidentialityLevel
    ) -> list[ConfidentialityTag]:
        """
        Get all classifications at a specific level.

        Args:
            organization_id: Organization to query
            level: Confidentiality level to filter by

        Returns:
            List of ConfidentialityTag at that level.
        """
        return [
            tag
            for tag in self._tags.values()
            if tag.organization_id == organization_id and tag.level == level
        ]

    def get_trade_secrets(self, organization_id: UUID) -> list[ConfidentialityTag]:
        """
        Get all trade secret classifications for an organization.

        Args:
            organization_id: Organization to query

        Returns:
            List of trade secret ConfidentialityTag.
        """
        return self.get_by_level(organization_id, "trade_secret")

    def get_patent_pending(self, organization_id: UUID) -> list[ConfidentialityTag]:
        """
        Get all patent-pending classifications for an organization.

        Args:
            organization_id: Organization to query

        Returns:
            List of patent-pending ConfidentialityTag.
        """
        return self.get_by_level(organization_id, "patent_pending")

    def get_confidential_submission(self, organization_id: UUID) -> list[ConfidentialityTag]:
        """
        Get all confidential_submission classifications.

        Args:
            organization_id: Organization to query

        Returns:
            List of confidential_submission ConfidentialityTag.
        """
        return self.get_by_level(organization_id, "confidential_submission")

    def get_public(self, organization_id: UUID) -> list[ConfidentialityTag]:
        """
        Get all public classifications.

        Args:
            organization_id: Organization to query

        Returns:
            List of public ConfidentialityTag.
        """
        return self.get_by_level(organization_id, "public")

    def get_cbi_candidates(self, organization_id: UUID) -> list[ConfidentialityTag]:
        """
        Get all entities that require CBI request.

        CBI = trade_secret OR confidential_submission

        Args:
            organization_id: Organization to query

        Returns:
            List of ConfidentialityTag requiring CBI treatment.
        """
        return [
            tag
            for tag in self._tags.values()
            if tag.organization_id == organization_id
            and tag.level in ("trade_secret", "confidential_submission")
        ]

    def is_disclosable(self, entity_type: str, entity_id: UUID) -> bool:
        """
        Check if an entity can be disclosed publicly.

        Args:
            entity_type: Type of entity
            entity_id: UUID of the entity

        Returns:
            True if public or unclassified (default to disclosable),
            False if confidential.
        """
        tag = self.get_classification(entity_type, entity_id)
        if tag is None:
            return True  # Unclassified defaults to disclosable
        return tag.level == "public"

    def requires_redaction(self, entity_type: str, entity_id: UUID) -> bool:
        """
        Check if an entity requires redaction in public documents.

        Args:
            entity_type: Type of entity
            entity_id: UUID of the entity

        Returns:
            True if trade_secret or confidential_submission.
        """
        tag = self.get_classification(entity_type, entity_id)
        if tag is None:
            return False
        return tag.level in ("trade_secret", "confidential_submission")

    def get_unclassified(
        self,
        organization_id: UUID,
        known_entities: list[tuple[str, UUID]],
    ) -> list[tuple[str, UUID]]:
        """
        Get entities that have not been classified.

        Args:
            organization_id: Organization to check
            known_entities: List of (entity_type, entity_id) tuples

        Returns:
            List of unclassified (entity_type, entity_id) tuples.
        """
        classified_keys = {
            (tag.entity_type, tag.entity_id)
            for tag in self._tags.values()
            if tag.organization_id == organization_id
        }
        return [
            (etype, eid) for etype, eid in known_entities if (etype, eid) not in classified_keys
        ]

    def remove_classification(self, entity_type: str, entity_id: UUID) -> bool:
        """
        Remove a confidentiality classification.

        Args:
            entity_type: Type of entity
            entity_id: UUID of the entity

        Returns:
            True if removed, False if not found.
        """
        key = (entity_type, entity_id)
        if key in self._tags:
            del self._tags[key]
            self.logger.info(f"Removed classification for {entity_type}/{entity_id}")
            return True
        return False

    def generate_report(
        self,
        organization_id: UUID,
        known_entities: list[tuple[str, UUID]] | None = None,
    ) -> ConfidentialityReport:
        """
        Generate a confidentiality status report.

        Args:
            organization_id: Organization to report on
            known_entities: Optional list of all known entities to check

        Returns:
            ConfidentialityReport with summary statistics.
        """
        all_tags = self.get_all_classifications(organization_id)

        public_count = sum(1 for t in all_tags if t.level == "public")
        conf_sub_count = sum(1 for t in all_tags if t.level == "confidential_submission")
        trade_secret_count = sum(1 for t in all_tags if t.level == "trade_secret")
        patent_pending_count = sum(1 for t in all_tags if t.level == "patent_pending")

        unclassified: list[tuple[str, UUID]] = []
        if known_entities:
            unclassified = self.get_unclassified(organization_id, known_entities)

        unclassified_dicts = [
            {"entity_type": etype, "entity_id": str(eid)} for etype, eid in unclassified
        ]

        requires_cbi = (conf_sub_count + trade_secret_count) > 0

        return ConfidentialityReport(
            organization_id=organization_id,
            generated_at=datetime.now(UTC).isoformat(),
            total_entities=len(all_tags) + len(unclassified),
            public_count=public_count,
            confidential_submission_count=conf_sub_count,
            trade_secret_count=trade_secret_count,
            patent_pending_count=patent_pending_count,
            unclassified_count=len(unclassified),
            requires_cbi_request=requires_cbi,
            unclassified_entities=unclassified_dicts,
        )

    def count(self, organization_id: UUID | None = None) -> int:
        """
        Count total classifications.

        Args:
            organization_id: Optional filter by organization

        Returns:
            Number of classifications.
        """
        if organization_id:
            return sum(1 for t in self._tags.values() if t.organization_id == organization_id)
        return len(self._tags)


# =============================================================================
# Singleton Access
# =============================================================================

_confidentiality_service: ConfidentialityService | None = None


def get_confidentiality_service() -> ConfidentialityService:
    """Get or create the singleton ConfidentialityService instance.

    Returns:
        ConfidentialityService singleton.
    """
    global _confidentiality_service
    if _confidentiality_service is None:
        _confidentiality_service = ConfidentialityService()
    return _confidentiality_service


def reset_confidentiality_service() -> None:
    """Reset the singleton (for testing)."""
    global _confidentiality_service
    _confidentiality_service = None


# =============================================================================
# CBI Request Generator (Sprint 6B)
# =============================================================================


class CBIItem(BaseModel):
    """Single item in a Confidential Business Information (CBI) request.

    Per SOR/98-282, Section 43.2, each CBI item must include:
    - Description of what is confidential
    - Justification for confidential treatment
    - Harm if disclosed

    Citation: [SOR/98-282, s.43.2]
    """

    entity_type: str = Field(..., description="Type of entity (evidence_item, artifact, etc.)")
    entity_id: UUID = Field(..., description="ID of the entity")
    description: str = Field(..., description="What information is confidential")
    justification: str = Field(..., description="Why this is CBI")
    harm_if_disclosed: str = Field(..., description="Competitive harm if disclosed to public")
    page_references: list[str] = Field(
        default_factory=list, description="Page/section references in submission"
    )
    confidentiality_level: ConfidentialityLevel = Field(
        default="confidential_submission", description="Level of confidentiality"
    )
    summary_for_public_use: str | None = Field(
        default=None, description="Public-safe summary if original is redacted"
    )


class CBIRequest(BaseModel):
    """Confidential Business Information request for Health Canada submission.

    Per SOR/98-282, Section 43.2:
    - Must identify all CBI in the submission
    - Must justify confidential treatment for each item
    - Must describe competitive harm if disclosed

    This document accompanies a regulatory submission to identify
    which portions should not be publicly disclosed.

    Citation: [SOR/98-282, s.43.2]
    """

    id: UUID | None = Field(default=None, description="Request ID")
    organization_id: UUID = Field(..., description="Organization making the request")
    submission_reference: str = Field(
        ..., description="Submission ID or reference (e.g., MDL application number)"
    )
    device_name: str = Field(..., description="Name of the medical device")
    items: list[CBIItem] = Field(default_factory=list, description="CBI items")
    attestation_text: str = Field(
        default=(
            "The undersigned hereby certifies that the information identified "
            "as confidential business information constitutes trade secrets or "
            "confidential commercial information and that disclosure of such "
            "information would cause significant competitive harm to the applicant."
        ),
        description="Attestation statement",
    )
    attested_by: UUID | None = Field(default=None, description="User who attested")
    attested_at: datetime | None = Field(default=None, description="When attested")
    created_at: datetime | None = Field(default=None, description="When request was created")
    # Citation fields (Sprint 5C)
    regulation_ref: str = Field(default="SOR-98-282-S43.2", description="Regulatory reference")
    citation_text: str = Field(default="[SOR/98-282, s.43.2]", description="Citation")

    @property
    def total_items(self) -> int:
        """Total number of CBI items."""
        return len(self.items)

    @property
    def trade_secret_count(self) -> int:
        """Number of trade secret items."""
        return sum(1 for i in self.items if i.confidentiality_level == "trade_secret")

    @property
    def has_attestation(self) -> bool:
        """Whether the request has been attested."""
        return self.attested_by is not None and self.attested_at is not None


def create_cbi_items_from_tags(
    tags: list[ConfidentialityTag],
) -> list[CBIItem]:
    """
    Create CBIItems from ConfidentialityTags.

    Args:
        tags: List of ConfidentialityTag (should be CBI candidates only)

    Returns:
        List of CBIItem ready for inclusion in a CBI request.

    Raises:
        ValueError: If a tag lacks required justification or harm description.
    """
    items: list[CBIItem] = []

    for tag in tags:
        if tag.level not in ("trade_secret", "confidential_submission"):
            continue  # Only CBI-eligible levels

        if not tag.justification:
            raise ValueError(
                f"Entity {tag.entity_type}/{tag.entity_id} lacks justification " "for CBI treatment"
            )

        if not tag.harm_if_disclosed:
            raise ValueError(
                f"Entity {tag.entity_type}/{tag.entity_id} lacks harm_if_disclosed "
                "description required for CBI"
            )

        items.append(
            CBIItem(
                entity_type=tag.entity_type,
                entity_id=tag.entity_id,
                description=tag.summary_for_public_use or f"Confidential {tag.entity_type}",
                justification=tag.justification,
                harm_if_disclosed=tag.harm_if_disclosed,
                confidentiality_level=tag.level,
                summary_for_public_use=tag.summary_for_public_use,
            )
        )

    return items


def generate_cbi_request(
    organization_id: UUID,
    submission_reference: str,
    device_name: str,
    tags: list[ConfidentialityTag],
    attested_by: UUID | None = None,
) -> CBIRequest:
    """
    Generate a CBI request from confidentiality tags.

    Args:
        organization_id: Organization making the request
        submission_reference: Submission ID or reference
        device_name: Name of the medical device
        tags: List of ConfidentialityTag for CBI items
        attested_by: User attesting the request (optional)

    Returns:
        CBIRequest ready for submission.
    """
    items = create_cbi_items_from_tags(tags)

    now = datetime.now(UTC)
    request = CBIRequest(
        organization_id=organization_id,
        submission_reference=submission_reference,
        device_name=device_name,
        items=items,
        created_at=now,
    )

    if attested_by:
        request.attested_by = attested_by
        request.attested_at = now

    return request


def generate_cbi_request_document(request: CBIRequest) -> str:
    """
    Generate a CBI request document as formatted text.

    Args:
        request: CBIRequest with items

    Returns:
        Formatted CBI request document text.
    """
    lines: list[str] = []

    lines.append("=" * 70)
    lines.append("CONFIDENTIAL BUSINESS INFORMATION (CBI) REQUEST")
    lines.append("=" * 70)
    lines.append("")
    lines.append(f"Submission Reference: {request.submission_reference}")
    lines.append(f"Device Name: {request.device_name}")
    lines.append(
        f"Date: {request.created_at.strftime('%Y-%m-%d') if request.created_at else 'Not dated'}"
    )
    lines.append(f"Citation: {request.citation_text}")
    lines.append("")
    lines.append("-" * 70)
    lines.append("CBI ITEMS")
    lines.append("-" * 70)
    lines.append("")

    for idx, item in enumerate(request.items, start=1):
        lines.append(f"Item {idx}:")
        lines.append(f"  Type: {item.entity_type}")
        lines.append(f"  Level: {item.confidentiality_level}")
        lines.append(f"  Description: {item.description}")
        lines.append(f"  Justification: {item.justification}")
        lines.append(f"  Harm if Disclosed: {item.harm_if_disclosed}")
        if item.page_references:
            lines.append(f"  Page References: {', '.join(item.page_references)}")
        if item.summary_for_public_use:
            lines.append(f"  Public Summary: {item.summary_for_public_use}")
        lines.append("")

    lines.append("-" * 70)
    lines.append("ATTESTATION")
    lines.append("-" * 70)
    lines.append("")
    lines.append(request.attestation_text)
    lines.append("")

    if request.has_attestation:
        lines.append(f"Attested by: {request.attested_by}")
        lines.append(
            f"Date: {request.attested_at.strftime('%Y-%m-%d %H:%M:%S UTC') if request.attested_at else 'N/A'}"
        )
    else:
        lines.append("[ ] I certify the above statement is true and accurate.")
        lines.append("")
        lines.append("Signature: _________________________")
        lines.append("Name: _________________________")
        lines.append("Title: _________________________")
        lines.append("Date: _________________________")

    lines.append("")
    lines.append("=" * 70)
    lines.append(f"Total CBI Items: {request.total_items}")
    lines.append(f"Trade Secrets: {request.trade_secret_count}")
    lines.append("=" * 70)

    return "\n".join(lines)
