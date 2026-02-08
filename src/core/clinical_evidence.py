"""
Clinical Evidence Service — Sprint 7A.

Provides structured clinical evidence models aligned with GUI-0102.
Evidence hierarchy scoring per established clinical research methodology.

GUI-0102 ALIGNMENT:
    Health Canada's "Guidance Document: Clinical Evidence Requirements for
    Medical Device Licence Applications" specifies evidence requirements
    by device class and risk level.

EVIDENCE HIERARCHY:
    Randomized controlled trials (RCTs) provide the strongest evidence.
    Observational studies and case reports provide progressively weaker
    evidence. Scoring reflects this hierarchy for regulatory assessment.

REGULATORY LANGUAGE SAFETY:
    This module uses terms like "assessment", "scoring", "evaluation"
    rather than "approval" or "compliance" — all outputs require
    professional review.

Usage:
    service = get_clinical_evidence_service()
    evidence = service.create(ClinicalEvidence(...))
    portfolio = service.get_portfolio(device_version_id)
    assessment = service.assess_package(device_version_id, "III")
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from src.core.regulatory_references import get_reference_registry
from src.utils.logging import get_logger

# =============================================================================
# Types
# =============================================================================

ClinicalStudyType = Literal[
    "randomized_controlled_trial",  # Score: 1.0 — Gold standard
    "prospective_cohort",  # Score: 0.85 — Strong observational
    "retrospective_cohort",  # Score: 0.70 — Good observational
    "case_control",  # Score: 0.55 — Moderate observational
    "case_series",  # Score: 0.40 — Weak, descriptive
    "case_report",  # Score: 0.25 — Anecdotal
    "expert_opinion",  # Score: 0.15 — Lowest evidence
    "literature_review",  # Score: 0.15 — Synthesis only
    "registry_data",  # Score: 0.60 — Real-world evidence
]

BlindingType = Literal["open", "single_blind", "double_blind", "triple_blind"]
ControlType = Literal["placebo", "active", "sham", "no_control"]

# Evidence hierarchy scores per established clinical research methodology
EVIDENCE_HIERARCHY_SCORE: dict[str, float] = {
    "randomized_controlled_trial": 1.0,
    "prospective_cohort": 0.85,
    "retrospective_cohort": 0.70,
    "registry_data": 0.60,
    "case_control": 0.55,
    "case_series": 0.40,
    "case_report": 0.25,
    "expert_opinion": 0.15,
    "literature_review": 0.15,
}

# Minimum evidence scores required by device class (GUI-0102 aligned)
CLASS_EVIDENCE_THRESHOLDS: dict[str, float] = {
    "I": 0.0,  # No clinical evidence required
    "II": 0.40,  # At least case series level
    "III": 0.60,  # Registry data or better
    "IV": 0.85,  # Prospective cohort or better
}

# =============================================================================
# Models
# =============================================================================


class ClinicalEvidence(BaseModel):
    """Structured clinical study data aligned with GUI-0102.

    Captures study design, population, endpoints, results, and
    quality indicators for regulatory assessment.

    Citation: [GUI-0102, Clinical Evidence Requirements]
    """

    id: UUID | None = Field(default=None, description="Evidence record ID")
    organization_id: UUID = Field(..., description="Owning organization")
    device_version_id: UUID = Field(..., description="Device version this evidence supports")

    # Identification
    study_type: ClinicalStudyType = Field(..., description="Type of clinical study")
    study_id: str | None = Field(default=None, description="Study identifier (NCT number, etc.)")
    title: str = Field(..., description="Study title")

    # Design
    blinding: BlindingType | None = Field(default=None, description="Blinding methodology")
    control_type: ControlType | None = Field(default=None, description="Control arm type")
    randomized: bool = Field(default=False, description="Whether randomization was used")
    multi_center: bool = Field(default=False, description="Whether multi-center study")

    # Population
    inclusion_criteria: list[str] = Field(default_factory=list, description="Inclusion criteria")
    exclusion_criteria: list[str] = Field(default_factory=list, description="Exclusion criteria")
    sample_size: int | None = Field(default=None, description="Number of subjects")
    population_description: str | None = Field(default=None, description="Population summary")

    # Endpoints
    primary_endpoint: str | None = Field(default=None, description="Primary efficacy endpoint")
    secondary_endpoints: list[str] = Field(default_factory=list, description="Secondary endpoints")
    safety_endpoints: list[str] = Field(default_factory=list, description="Safety endpoints")
    follow_up_duration: str | None = Field(default=None, description="Follow-up period")

    # Results
    results_summary: str | None = Field(default=None, description="Results summary")
    primary_outcome_met: bool | None = Field(default=None, description="Primary endpoint achieved")
    adverse_events_summary: str | None = Field(default=None, description="AE summary")
    serious_adverse_events: int | None = Field(default=None, description="SAE count")

    # Quality indicators
    peer_reviewed: bool = Field(default=False, description="Published in peer-reviewed journal")
    publication_reference: str | None = Field(default=None, description="Publication citation")
    ethics_approval: str | None = Field(default=None, description="Ethics committee approval")
    quality_score: float | None = Field(default=None, description="Calculated quality score")

    # Regulatory alignment
    hc_guidance_alignment: str | None = Field(
        default=None, description="Health Canada guidance reference"
    )
    evidence_item_id: UUID | None = Field(default=None, description="Link to evidence_items table")

    # Timestamps
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")

    # Citation
    regulation_ref: str = Field(default="GUI-0102", description="Guidance reference")
    citation_text: str = Field(
        default="[GUI-0102, Clinical Evidence Requirements]",
        description="Formatted citation",
    )


class ClinicalEvidencePortfolio(BaseModel):
    """Collection of clinical evidence for a device version.

    Aggregates all clinical studies supporting a device, with
    summary statistics and overall quality assessment.
    """

    device_version_id: UUID = Field(..., description="Device version")
    organization_id: UUID = Field(..., description="Organization")
    evidence_items: list[ClinicalEvidence] = Field(
        default_factory=list, description="All clinical evidence"
    )
    total_studies: int = Field(default=0, description="Total number of studies")
    total_subjects: int = Field(default=0, description="Combined sample size")

    # By study type
    rct_count: int = Field(default=0, description="RCT count")
    observational_count: int = Field(default=0, description="Observational study count")
    case_study_count: int = Field(default=0, description="Case report/series count")

    # Quality metrics
    highest_evidence_level: str | None = Field(
        default=None, description="Best study type in portfolio"
    )
    weighted_quality_score: float = Field(default=0.0, description="Sample-weighted quality score")
    peer_reviewed_percentage: float = Field(
        default=0.0, description="Percentage of peer-reviewed studies"
    )

    # Generated
    generated_at: str = Field(default="", description="Portfolio generation timestamp")


class ClinicalPackageAssessment(BaseModel):
    """Assessment of clinical evidence package against device class requirements.

    Evaluates whether the clinical evidence portfolio meets the
    requirements for the target device class per GUI-0102.

    REGULATORY LANGUAGE SAFETY:
        Uses "meets threshold" and "assessment indicates" rather than
        "compliant" or "approved".
    """

    device_version_id: UUID = Field(..., description="Device version assessed")
    device_class: str = Field(..., description="Target device class")
    assessed_at: str = Field(..., description="Assessment timestamp")

    # Scores
    portfolio_score: float = Field(..., description="Overall portfolio quality score")
    required_threshold: float = Field(..., description="Minimum required for class")
    score_gap: float = Field(..., description="Difference from threshold (+ = above)")

    # Assessment
    meets_threshold: bool = Field(..., description="Whether threshold is met")
    assessment_summary: str = Field(..., description="Human-readable summary")

    # Recommendations
    recommendations: list[str] = Field(
        default_factory=list, description="Recommendations for improvement"
    )
    additional_studies_suggested: list[str] = Field(
        default_factory=list, description="Suggested study types to add"
    )

    # Details
    strongest_evidence: str | None = Field(default=None, description="Best evidence in portfolio")
    weakest_evidence: str | None = Field(default=None, description="Weakest evidence in portfolio")
    evidence_gaps: list[str] = Field(default_factory=list, description="Identified gaps")

    # Citation
    guidance_reference: str = Field(default="GUI-0102", description="Guidance document reference")
    citation_text: str = Field(
        default="[GUI-0102, Clinical Evidence Requirements]",
        description="Formatted citation",
    )


# =============================================================================
# Service Class
# =============================================================================


class ClinicalEvidenceService:
    """
    Service for managing clinical evidence records.

    Provides methods to:
    - Create and store clinical evidence records
    - Calculate quality scores based on study design
    - Aggregate evidence into portfolios
    - Assess evidence packages against device class requirements

    In-memory storage for now; production would use persistence layer.

    Usage:
        service = get_clinical_evidence_service()
        evidence = service.create(ClinicalEvidence(...))
        score = service.calculate_quality_score(evidence)
        portfolio = service.get_portfolio(device_version_id)
    """

    def __init__(self) -> None:
        """Initialize the service with empty storage."""
        self.logger = get_logger(self.__class__.__name__)
        self._evidence: dict[UUID, ClinicalEvidence] = {}
        self._citation_registry = get_reference_registry()
        self.logger.info("ClinicalEvidenceService initialized")

    def create(self, evidence: ClinicalEvidence) -> ClinicalEvidence:
        """
        Create a new clinical evidence record.

        Args:
            evidence: ClinicalEvidence to store

        Returns:
            ClinicalEvidence with ID and quality score assigned.
        """
        from uuid import uuid4

        # Assign ID if not present
        if evidence.id is None:
            evidence.id = uuid4()

        # Calculate quality score
        evidence.quality_score = self.calculate_quality_score(evidence)

        # Set timestamps
        now = datetime.now(UTC)
        evidence.created_at = now
        evidence.updated_at = now

        # Store
        self._evidence[evidence.id] = evidence
        self.logger.info(
            f"Created clinical evidence {evidence.id} "
            f"(type={evidence.study_type}, score={evidence.quality_score:.2f})"
        )

        return evidence

    def get(self, evidence_id: UUID) -> ClinicalEvidence | None:
        """
        Get a clinical evidence record by ID.

        Args:
            evidence_id: UUID of the evidence record

        Returns:
            ClinicalEvidence if found, None otherwise.
        """
        return self._evidence.get(evidence_id)

    def get_by_device_version(self, device_version_id: UUID) -> list[ClinicalEvidence]:
        """
        Get all clinical evidence for a device version.

        Args:
            device_version_id: Device version UUID

        Returns:
            List of ClinicalEvidence records.
        """
        return [e for e in self._evidence.values() if e.device_version_id == device_version_id]

    def calculate_quality_score(self, evidence: ClinicalEvidence) -> float:
        """
        Calculate quality score for clinical evidence.

        Score is based on:
        - Study type (hierarchy score) — 50% weight
        - Blinding methodology — 15% weight
        - Sample size adequacy — 15% weight
        - Peer review status — 10% weight
        - Multi-center status — 10% weight

        Args:
            evidence: ClinicalEvidence to score

        Returns:
            Quality score from 0.0 to 1.0.
        """
        # Base score from hierarchy
        base_score = EVIDENCE_HIERARCHY_SCORE.get(evidence.study_type, 0.15)

        # Blinding bonus (0-0.15)
        blinding_score = 0.0
        if evidence.blinding == "triple_blind":
            blinding_score = 0.15
        elif evidence.blinding == "double_blind":
            blinding_score = 0.12
        elif evidence.blinding == "single_blind":
            blinding_score = 0.08
        elif evidence.blinding == "open":
            blinding_score = 0.03

        # Sample size bonus (0-0.15)
        sample_score = 0.0
        if evidence.sample_size:
            if evidence.sample_size >= 500:
                sample_score = 0.15
            elif evidence.sample_size >= 200:
                sample_score = 0.12
            elif evidence.sample_size >= 100:
                sample_score = 0.09
            elif evidence.sample_size >= 50:
                sample_score = 0.06
            elif evidence.sample_size >= 20:
                sample_score = 0.03

        # Peer review bonus (0-0.10)
        peer_score = 0.10 if evidence.peer_reviewed else 0.0

        # Multi-center bonus (0-0.10)
        multi_center_score = 0.10 if evidence.multi_center else 0.0

        # Weighted combination
        total = base_score * 0.50 + blinding_score + sample_score + peer_score + multi_center_score

        # Cap at 1.0
        return min(1.0, total)

    def get_portfolio(self, device_version_id: UUID) -> ClinicalEvidencePortfolio:
        """
        Get aggregated clinical evidence portfolio for a device.

        Args:
            device_version_id: Device version UUID

        Returns:
            ClinicalEvidencePortfolio with aggregated statistics.
        """
        evidence_list = self.get_by_device_version(device_version_id)

        if not evidence_list:
            # Return empty portfolio
            return ClinicalEvidencePortfolio(
                device_version_id=device_version_id,
                organization_id=UUID("00000000-0000-0000-0000-000000000000"),
                generated_at=datetime.now(UTC).isoformat(),
            )

        # Get org ID from first evidence
        org_id = evidence_list[0].organization_id

        # Count by type
        rct_count = sum(1 for e in evidence_list if e.study_type == "randomized_controlled_trial")
        observational_count = sum(
            1
            for e in evidence_list
            if e.study_type
            in ("prospective_cohort", "retrospective_cohort", "case_control", "registry_data")
        )
        case_count = sum(1 for e in evidence_list if e.study_type in ("case_series", "case_report"))

        # Total subjects
        total_subjects = sum(e.sample_size or 0 for e in evidence_list)

        # Highest evidence level
        study_types = [e.study_type for e in evidence_list]
        type_scores = [(t, EVIDENCE_HIERARCHY_SCORE.get(t, 0)) for t in study_types]
        highest = max(type_scores, key=lambda x: x[1])
        highest_level = highest[0]

        # Weighted quality score (by sample size)
        if total_subjects > 0:
            weighted_score = (
                sum((e.quality_score or 0) * (e.sample_size or 0) for e in evidence_list)
                / total_subjects
            )
        else:
            # Simple average if no sample sizes
            scores = [e.quality_score or 0 for e in evidence_list]
            weighted_score = sum(scores) / len(scores) if scores else 0.0

        # Peer review percentage
        peer_reviewed = sum(1 for e in evidence_list if e.peer_reviewed)
        peer_pct = (peer_reviewed / len(evidence_list) * 100) if evidence_list else 0.0

        return ClinicalEvidencePortfolio(
            device_version_id=device_version_id,
            organization_id=org_id,
            evidence_items=evidence_list,
            total_studies=len(evidence_list),
            total_subjects=total_subjects,
            rct_count=rct_count,
            observational_count=observational_count,
            case_study_count=case_count,
            highest_evidence_level=highest_level,
            weighted_quality_score=round(weighted_score, 3),
            peer_reviewed_percentage=round(peer_pct, 1),
            generated_at=datetime.now(UTC).isoformat(),
        )

    def assess_package(
        self, device_version_id: UUID, device_class: str
    ) -> ClinicalPackageAssessment:
        """
        Assess clinical evidence package against device class requirements.

        Per GUI-0102, higher-risk device classes require stronger
        clinical evidence. This assessment compares the portfolio
        quality score against class-specific thresholds.

        Args:
            device_version_id: Device version UUID
            device_class: Target device class ("I", "II", "III", "IV")

        Returns:
            ClinicalPackageAssessment with gap analysis.
        """
        portfolio = self.get_portfolio(device_version_id)
        threshold = CLASS_EVIDENCE_THRESHOLDS.get(device_class.upper(), 0.60)

        score = portfolio.weighted_quality_score
        gap = score - threshold
        meets = score >= threshold

        # Build recommendations
        recommendations: list[str] = []
        additional_studies: list[str] = []
        evidence_gaps: list[str] = []

        if not meets:
            recommendations.append(
                f"Current evidence score ({score:.2f}) is below "
                f"threshold ({threshold:.2f}) for Class {device_class}"
            )

            # Suggest study types based on gap
            if gap < -0.4:
                additional_studies.append("randomized_controlled_trial")
                recommendations.append("A randomized controlled trial is strongly recommended")
            elif gap < -0.2:
                additional_studies.append("prospective_cohort")
                recommendations.append("A prospective cohort study would strengthen the package")
            else:
                additional_studies.append("registry_data")
                recommendations.append("Additional real-world evidence or registry data may help")

        if portfolio.rct_count == 0 and device_class in ("III", "IV"):
            evidence_gaps.append("No randomized controlled trial in portfolio")

        if portfolio.total_subjects < 100 and device_class in ("III", "IV"):
            evidence_gaps.append("Combined sample size below 100 subjects")

        if portfolio.peer_reviewed_percentage < 50:
            evidence_gaps.append("Less than 50% of studies are peer-reviewed")

        # Summary
        if meets:
            summary = (
                f"Clinical evidence package assessment indicates the portfolio "
                f"(score: {score:.2f}) meets the threshold ({threshold:.2f}) "
                f"for Class {device_class} devices per GUI-0102."
            )
        else:
            summary = (
                f"Clinical evidence package assessment indicates the portfolio "
                f"(score: {score:.2f}) is below the threshold ({threshold:.2f}) "
                f"for Class {device_class} devices. Additional evidence may be needed."
            )

        # Find strongest and weakest
        strongest = portfolio.highest_evidence_level
        weakest = None
        if portfolio.evidence_items:
            type_scores = [
                (e.study_type, EVIDENCE_HIERARCHY_SCORE.get(e.study_type, 0))
                for e in portfolio.evidence_items
            ]
            weakest = min(type_scores, key=lambda x: x[1])[0]

        return ClinicalPackageAssessment(
            device_version_id=device_version_id,
            device_class=device_class,
            assessed_at=datetime.now(UTC).isoformat(),
            portfolio_score=round(score, 3),
            required_threshold=threshold,
            score_gap=round(gap, 3),
            meets_threshold=meets,
            assessment_summary=summary,
            recommendations=recommendations,
            additional_studies_suggested=additional_studies,
            strongest_evidence=strongest,
            weakest_evidence=weakest,
            evidence_gaps=evidence_gaps,
        )

    def delete(self, evidence_id: UUID) -> bool:
        """
        Delete a clinical evidence record.

        Args:
            evidence_id: UUID of the evidence to delete

        Returns:
            True if deleted, False if not found.
        """
        if evidence_id in self._evidence:
            del self._evidence[evidence_id]
            self.logger.info(f"Deleted clinical evidence {evidence_id}")
            return True
        return False

    def count(self, organization_id: UUID | None = None) -> int:
        """
        Count clinical evidence records.

        Args:
            organization_id: Optional filter by organization

        Returns:
            Number of evidence records.
        """
        if organization_id:
            return sum(1 for e in self._evidence.values() if e.organization_id == organization_id)
        return len(self._evidence)


# =============================================================================
# Singleton Access
# =============================================================================

_clinical_evidence_service: ClinicalEvidenceService | None = None


def get_clinical_evidence_service() -> ClinicalEvidenceService:
    """Get or create the singleton ClinicalEvidenceService instance.

    Returns:
        ClinicalEvidenceService singleton.
    """
    global _clinical_evidence_service
    if _clinical_evidence_service is None:
        _clinical_evidence_service = ClinicalEvidenceService()
    return _clinical_evidence_service


def reset_clinical_evidence_service() -> None:
    """Reset the singleton (for testing)."""
    global _clinical_evidence_service
    _clinical_evidence_service = None
