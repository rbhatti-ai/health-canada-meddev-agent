"""
Predicate Device Analysis — Sprint 7B.

Provides models and service for predicate device comparison,
supporting substantial equivalence (SE) demonstrations per
SOR/98-282 Section 32(4).

REGULATORY CONTEXT:
    For Class II and III devices, Health Canada accepts substantial
    equivalence to a legally marketed predicate device as part of
    the safety and effectiveness demonstration.

    Three comparison dimensions (SOR/98-282, s.32(4)):
    1. Intended use — Must be substantially equivalent
    2. Technological characteristics — Must be substantially equivalent
    3. Performance — Must demonstrate equivalent or improved safety/efficacy

REGULATORY LANGUAGE SAFETY:
    This module uses terms like "analysis indicates" and "comparison suggests"
    rather than "equivalent" as a final determination — all outputs require
    professional review.

Usage:
    service = get_predicate_analysis_service()
    predicate = service.create(PredicateDevice(...))
    matrix = service.generate_comparison_matrix(device_version_id, predicate_id)
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

EquivalenceConclusion = Literal[
    "substantially_equivalent",  # SE demonstrated
    "substantially_equivalent_with_data",  # SE with additional clinical/bench data
    "not_equivalent",  # Cannot claim SE
    "requires_additional_analysis",  # Insufficient information
]

ComparisonResult = Literal[
    "equivalent",  # No meaningful difference
    "different_with_mitigation",  # Different but addressed with data
    "different_unaddressed",  # Different and not addressed
    "not_compared",  # Comparison not performed
]

# Scoring for equivalence dimensions
EQUIVALENCE_WEIGHTS = {
    "intended_use": 0.35,  # Primary weight
    "technological": 0.35,  # Secondary weight
    "performance": 0.30,  # Tertiary weight
}

# =============================================================================
# Models
# =============================================================================


class PredicateDevice(BaseModel):
    """Predicate device for substantial equivalence comparison.

    Captures the predicate device identification and the three
    comparison dimensions required by SOR/98-282 s.32(4).

    Citation: [SOR/98-282, s.32(4)]
    """

    id: UUID | None = Field(default=None, description="Predicate record ID")
    organization_id: UUID = Field(..., description="Owning organization")
    device_version_id: UUID = Field(..., description="Subject device being compared")

    # Predicate identification
    predicate_name: str = Field(..., description="Predicate device name")
    predicate_manufacturer: str = Field(..., description="Predicate manufacturer")
    mdl_number: str | None = Field(default=None, description="Health Canada MDL number")
    mdall_id: str | None = Field(default=None, description="MDALL database ID")
    predicate_device_class: str = Field(..., description="Predicate device class")

    # Intended use comparison
    intended_use_comparison: str = Field(..., description="Comparison of intended uses")
    intended_use_equivalent: bool = Field(
        default=False, description="Whether intended uses are substantially equivalent"
    )
    intended_use_differences: list[str] = Field(
        default_factory=list, description="Identified differences in intended use"
    )

    # Technological characteristics comparison
    technological_characteristics: str = Field(
        ..., description="Description of technological comparison"
    )
    technological_equivalent: bool = Field(
        default=False, description="Whether technology is substantially equivalent"
    )
    technological_differences: list[str] = Field(
        default_factory=list, description="Identified technological differences"
    )
    technological_mitigations: list[str] = Field(
        default_factory=list, description="How differences are addressed"
    )

    # Performance comparison
    performance_comparison: str = Field(..., description="Performance data comparison")
    performance_equivalent: bool = Field(
        default=False, description="Whether performance is substantially equivalent"
    )
    performance_differences: list[str] = Field(
        default_factory=list, description="Performance differences identified"
    )
    performance_data_sources: list[str] = Field(
        default_factory=list, description="Sources of performance data"
    )

    # Conclusion
    equivalence_conclusion: EquivalenceConclusion = Field(
        default="requires_additional_analysis",
        description="Overall equivalence determination",
    )
    additional_data_required: list[str] = Field(
        default_factory=list, description="Additional data needed for determination"
    )
    conclusion_rationale: str | None = Field(default=None, description="Rationale for conclusion")

    # Quality score (calculated)
    equivalence_score: float | None = Field(
        default=None, description="Calculated equivalence score (0.0-1.0)"
    )

    # Timestamps
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")

    # Citation
    regulation_ref: str = Field(default="SOR-98-282-S32-4", description="Regulation reference")
    citation_text: str = Field(
        default="[SOR/98-282, s.32(4)]",
        description="Formatted citation",
    )


class PredicateComparisonMatrix(BaseModel):
    """Detailed comparison matrix between subject and predicate device.

    Structured breakdown of the three comparison dimensions with
    individual assessments and supporting evidence references.
    """

    device_version_id: UUID = Field(..., description="Subject device")
    predicate_id: UUID = Field(..., description="Predicate device record")
    generated_at: str = Field(..., description="Matrix generation timestamp")

    # Dimension assessments
    intended_use_assessment: ComparisonResult = Field(
        default="not_compared", description="Intended use comparison result"
    )
    technological_assessment: ComparisonResult = Field(
        default="not_compared", description="Technological comparison result"
    )
    performance_assessment: ComparisonResult = Field(
        default="not_compared", description="Performance comparison result"
    )

    # Dimension details
    intended_use_details: dict[str, str] = Field(
        default_factory=dict, description="Intended use comparison details"
    )
    technological_details: dict[str, str] = Field(
        default_factory=dict, description="Technological comparison details"
    )
    performance_details: dict[str, str] = Field(
        default_factory=dict, description="Performance comparison details"
    )

    # Scores
    dimension_scores: dict[str, float] = Field(
        default_factory=dict, description="Score by dimension"
    )
    overall_score: float = Field(default=0.0, description="Weighted overall score")

    # Gaps and recommendations
    unaddressed_differences: list[str] = Field(
        default_factory=list, description="Differences needing mitigation"
    )
    recommended_actions: list[str] = Field(
        default_factory=list, description="Recommended next steps"
    )

    # Conclusion
    matrix_conclusion: str = Field(default="", description="Matrix summary")

    # Citation
    citation_text: str = Field(default="[SOR/98-282, s.32(4)]", description="Formatted citation")


class SubstantialEquivalenceReport(BaseModel):
    """Complete substantial equivalence analysis report.

    Aggregates all predicate comparisons for a device version
    with summary statistics and overall assessment.
    """

    device_version_id: UUID = Field(..., description="Subject device")
    organization_id: UUID = Field(..., description="Organization")
    generated_at: str = Field(..., description="Report generation timestamp")

    # Predicates analyzed
    predicates: list[PredicateDevice] = Field(
        default_factory=list, description="All predicate comparisons"
    )
    predicate_count: int = Field(default=0, description="Number of predicates analyzed")

    # Best predicate
    recommended_predicate_id: UUID | None = Field(
        default=None, description="ID of best predicate match"
    )
    recommended_predicate_name: str | None = Field(
        default=None, description="Name of best predicate match"
    )
    best_equivalence_score: float = Field(default=0.0, description="Score of best predicate match")

    # Overall assessment
    se_demonstration_possible: bool = Field(
        default=False, description="Whether SE can be demonstrated"
    )
    assessment_summary: str = Field(default="", description="Summary of SE assessment")
    data_gaps: list[str] = Field(default_factory=list, description="Data gaps preventing SE")
    recommendations: list[str] = Field(
        default_factory=list, description="Recommendations for SE path"
    )

    # Citation
    guidance_reference: str = Field(default="GUI-0098", description="Guidance reference")
    citation_text: str = Field(default="[SOR/98-282, s.32(4)]", description="Formatted citation")


# =============================================================================
# Service Class
# =============================================================================


class PredicateAnalysisService:
    """
    Service for predicate device analysis.

    Provides methods to:
    - Create and store predicate device records
    - Calculate equivalence scores
    - Generate comparison matrices
    - Produce SE reports with recommendations

    In-memory storage for now; production would use persistence layer.

    Usage:
        service = get_predicate_analysis_service()
        predicate = service.create(PredicateDevice(...))
        matrix = service.generate_comparison_matrix(dv_id, pred_id)
    """

    def __init__(self) -> None:
        """Initialize the service with empty storage."""
        self.logger = get_logger(self.__class__.__name__)
        self._predicates: dict[UUID, PredicateDevice] = {}
        self._citation_registry = get_reference_registry()
        self.logger.info("PredicateAnalysisService initialized")

    def create(self, predicate: PredicateDevice) -> PredicateDevice:
        """
        Create a new predicate device record.

        Args:
            predicate: PredicateDevice to store

        Returns:
            PredicateDevice with ID and equivalence score assigned.
        """
        from uuid import uuid4

        # Assign ID if not present
        if predicate.id is None:
            predicate.id = uuid4()

        # Calculate equivalence score
        predicate.equivalence_score = self.calculate_equivalence_score(predicate)

        # Determine conclusion based on score and flags
        predicate.equivalence_conclusion = self._determine_conclusion(predicate)

        # Set timestamps
        now = datetime.now(UTC)
        predicate.created_at = now
        predicate.updated_at = now

        # Store
        self._predicates[predicate.id] = predicate
        self.logger.info(
            f"Created predicate {predicate.id} "
            f"(name={predicate.predicate_name}, score={predicate.equivalence_score:.2f})"
        )

        return predicate

    def get(self, predicate_id: UUID) -> PredicateDevice | None:
        """
        Get a predicate device record by ID.

        Args:
            predicate_id: UUID of the predicate record

        Returns:
            PredicateDevice if found, None otherwise.
        """
        return self._predicates.get(predicate_id)

    def get_by_device_version(self, device_version_id: UUID) -> list[PredicateDevice]:
        """
        Get all predicate comparisons for a device version.

        Args:
            device_version_id: Device version UUID

        Returns:
            List of PredicateDevice records.
        """
        return [p for p in self._predicates.values() if p.device_version_id == device_version_id]

    def calculate_equivalence_score(self, predicate: PredicateDevice) -> float:
        """
        Calculate overall equivalence score.

        Score is weighted combination of three dimensions:
        - Intended use equivalence: 35%
        - Technological equivalence: 35%
        - Performance equivalence: 30%

        Each dimension scores 1.0 if equivalent, reduced by
        unaddressed differences.

        Args:
            predicate: PredicateDevice to score

        Returns:
            Equivalence score from 0.0 to 1.0.
        """
        # Intended use score
        iu_score = 1.0 if predicate.intended_use_equivalent else 0.0
        if not predicate.intended_use_equivalent:
            # Partial credit if differences exist but may be addressable
            iu_score = 0.3 if predicate.intended_use_differences else 0.0

        # Technological score
        tech_score = 1.0 if predicate.technological_equivalent else 0.0
        if not predicate.technological_equivalent:
            # Credit for mitigations
            diff_count = len(predicate.technological_differences)
            mitigation_count = len(predicate.technological_mitigations)
            if diff_count > 0 and mitigation_count >= diff_count:
                tech_score = 0.7  # Differences addressed
            elif diff_count > 0 and mitigation_count > 0:
                tech_score = 0.4  # Partially addressed
            else:
                tech_score = 0.0

        # Performance score
        perf_score = 1.0 if predicate.performance_equivalent else 0.0
        if not predicate.performance_equivalent:
            # Credit for having performance data
            if predicate.performance_data_sources:
                perf_score = 0.5
            elif predicate.performance_differences:
                perf_score = 0.2
            else:
                perf_score = 0.0

        # Weighted combination
        score = (
            iu_score * EQUIVALENCE_WEIGHTS["intended_use"]
            + tech_score * EQUIVALENCE_WEIGHTS["technological"]
            + perf_score * EQUIVALENCE_WEIGHTS["performance"]
        )

        return round(score, 3)

    def _determine_conclusion(self, predicate: PredicateDevice) -> EquivalenceConclusion:
        """
        Determine equivalence conclusion based on scores and flags.

        Returns appropriate conclusion based on equivalence score
        and presence of unaddressed differences.
        """
        score = predicate.equivalence_score or 0.0

        # All three dimensions must be substantially equivalent
        all_equivalent = (
            predicate.intended_use_equivalent
            and predicate.technological_equivalent
            and predicate.performance_equivalent
        )

        if all_equivalent and score >= 0.9:
            return "substantially_equivalent"

        if score >= 0.7:
            # Good score but needs supporting data
            return "substantially_equivalent_with_data"

        if score < 0.4:
            return "not_equivalent"

        return "requires_additional_analysis"

    def generate_comparison_matrix(
        self, device_version_id: UUID, predicate_id: UUID
    ) -> PredicateComparisonMatrix | None:
        """
        Generate detailed comparison matrix.

        Args:
            device_version_id: Subject device UUID
            predicate_id: Predicate record UUID

        Returns:
            PredicateComparisonMatrix or None if predicate not found.
        """
        predicate = self.get(predicate_id)
        if not predicate:
            return None

        # Determine assessments
        iu_assessment = self._assess_dimension(
            predicate.intended_use_equivalent,
            predicate.intended_use_differences,
            [],  # No mitigations tracked for IU
        )
        tech_assessment = self._assess_dimension(
            predicate.technological_equivalent,
            predicate.technological_differences,
            predicate.technological_mitigations,
        )
        perf_assessment = self._assess_dimension(
            predicate.performance_equivalent,
            predicate.performance_differences,
            predicate.performance_data_sources,
        )

        # Calculate dimension scores
        dimension_scores = {
            "intended_use": (
                1.0
                if iu_assessment == "equivalent"
                else (0.5 if iu_assessment == "different_with_mitigation" else 0.0)
            ),
            "technological": (
                1.0
                if tech_assessment == "equivalent"
                else (0.5 if tech_assessment == "different_with_mitigation" else 0.0)
            ),
            "performance": (
                1.0
                if perf_assessment == "equivalent"
                else (0.5 if perf_assessment == "different_with_mitigation" else 0.0)
            ),
        }

        overall = sum(dimension_scores[k] * EQUIVALENCE_WEIGHTS[k] for k in dimension_scores)

        # Collect unaddressed differences
        unaddressed = []
        if iu_assessment == "different_unaddressed":
            unaddressed.extend(predicate.intended_use_differences)
        if tech_assessment == "different_unaddressed":
            unaddressed.extend(predicate.technological_differences)
        if perf_assessment == "different_unaddressed":
            unaddressed.extend(predicate.performance_differences)

        # Generate recommendations
        recommendations = []
        if iu_assessment == "different_unaddressed":
            recommendations.append(
                "Address intended use differences or select a different predicate"
            )
        if tech_assessment == "different_unaddressed":
            recommendations.append(
                "Provide bench testing data to address technological differences"
            )
        if perf_assessment == "different_unaddressed":
            recommendations.append("Conduct performance testing to demonstrate equivalence")

        # Build conclusion
        if overall >= 0.8:
            conclusion = (
                "Comparison matrix analysis indicates substantial equivalence "
                "may be demonstrated with current evidence."
            )
        elif overall >= 0.5:
            conclusion = (
                "Comparison matrix analysis suggests substantial equivalence "
                "may be possible with additional supporting data."
            )
        else:
            conclusion = (
                "Comparison matrix analysis indicates substantial equivalence "
                "is not supported. Consider alternative regulatory pathway."
            )

        return PredicateComparisonMatrix(
            device_version_id=device_version_id,
            predicate_id=predicate_id,
            generated_at=datetime.now(UTC).isoformat(),
            intended_use_assessment=iu_assessment,
            technological_assessment=tech_assessment,
            performance_assessment=perf_assessment,
            intended_use_details={
                "comparison": predicate.intended_use_comparison,
                "equivalent": str(predicate.intended_use_equivalent),
            },
            technological_details={
                "comparison": predicate.technological_characteristics,
                "equivalent": str(predicate.technological_equivalent),
                "differences_count": str(len(predicate.technological_differences)),
                "mitigations_count": str(len(predicate.technological_mitigations)),
            },
            performance_details={
                "comparison": predicate.performance_comparison,
                "equivalent": str(predicate.performance_equivalent),
                "data_sources": ", ".join(predicate.performance_data_sources) or "None",
            },
            dimension_scores=dimension_scores,
            overall_score=round(overall, 3),
            unaddressed_differences=unaddressed,
            recommended_actions=recommendations,
            matrix_conclusion=conclusion,
        )

    def _assess_dimension(
        self,
        is_equivalent: bool,
        differences: list[str],
        mitigations: list[str],
    ) -> ComparisonResult:
        """Assess a comparison dimension."""
        if is_equivalent:
            return "equivalent"
        if not differences:
            return "not_compared"
        if mitigations and len(mitigations) >= len(differences):
            return "different_with_mitigation"
        return "different_unaddressed"

    def generate_se_report(
        self, device_version_id: UUID, organization_id: UUID
    ) -> SubstantialEquivalenceReport:
        """
        Generate comprehensive SE report for a device.

        Args:
            device_version_id: Subject device UUID
            organization_id: Organization UUID

        Returns:
            SubstantialEquivalenceReport with all predicate analyses.
        """
        predicates = self.get_by_device_version(device_version_id)

        if not predicates:
            return SubstantialEquivalenceReport(
                device_version_id=device_version_id,
                organization_id=organization_id,
                generated_at=datetime.now(UTC).isoformat(),
                se_demonstration_possible=False,
                assessment_summary=(
                    "No predicate devices have been analyzed. "
                    "Substantial equivalence cannot be assessed."
                ),
                recommendations=[
                    "Identify potential predicate devices from MDALL database",
                    "Document predicate comparisons for SE demonstration",
                ],
            )

        # Find best predicate
        best = max(predicates, key=lambda p: p.equivalence_score or 0)
        best_score = best.equivalence_score or 0

        # Collect all data gaps
        all_gaps = []
        for p in predicates:
            all_gaps.extend(p.additional_data_required)

        # Determine if SE is possible
        se_possible = best.equivalence_conclusion in (
            "substantially_equivalent",
            "substantially_equivalent_with_data",
        )

        # Build summary
        if se_possible and best_score >= 0.8:
            summary = (
                f"Substantial equivalence analysis indicates SE demonstration "
                f"is possible using predicate '{best.predicate_name}' "
                f"(equivalence score: {best_score:.2f})."
            )
        elif se_possible:
            summary = (
                f"Substantial equivalence analysis suggests SE may be "
                f"demonstrated with additional data using predicate "
                f"'{best.predicate_name}' (equivalence score: {best_score:.2f})."
            )
        else:
            summary = (
                f"Substantial equivalence analysis indicates SE demonstration "
                f"is not supported with current predicates. Best candidate: "
                f"'{best.predicate_name}' (score: {best_score:.2f})."
            )

        # Recommendations
        recommendations = []
        if not se_possible:
            recommendations.append("Consider identifying additional predicate devices")
            recommendations.append("Evaluate de novo or full clinical pathway")
        if all_gaps:
            recommendations.append(f"Address {len(set(all_gaps))} data gaps identified")
        if best_score < 0.7:
            recommendations.append("Strengthen equivalence case with additional testing")

        return SubstantialEquivalenceReport(
            device_version_id=device_version_id,
            organization_id=organization_id,
            generated_at=datetime.now(UTC).isoformat(),
            predicates=predicates,
            predicate_count=len(predicates),
            recommended_predicate_id=best.id,
            recommended_predicate_name=best.predicate_name,
            best_equivalence_score=best_score,
            se_demonstration_possible=se_possible,
            assessment_summary=summary,
            data_gaps=list(set(all_gaps)),
            recommendations=recommendations,
        )

    def delete(self, predicate_id: UUID) -> bool:
        """
        Delete a predicate device record.

        Args:
            predicate_id: UUID of the predicate to delete

        Returns:
            True if deleted, False if not found.
        """
        if predicate_id in self._predicates:
            del self._predicates[predicate_id]
            self.logger.info(f"Deleted predicate {predicate_id}")
            return True
        return False

    def count(self, organization_id: UUID | None = None) -> int:
        """
        Count predicate device records.

        Args:
            organization_id: Optional filter by organization

        Returns:
            Number of predicate records.
        """
        if organization_id:
            return sum(1 for p in self._predicates.values() if p.organization_id == organization_id)
        return len(self._predicates)


# =============================================================================
# Singleton Access
# =============================================================================

_predicate_analysis_service: PredicateAnalysisService | None = None


def get_predicate_analysis_service() -> PredicateAnalysisService:
    """Get or create the singleton PredicateAnalysisService instance.

    Returns:
        PredicateAnalysisService singleton.
    """
    global _predicate_analysis_service
    if _predicate_analysis_service is None:
        _predicate_analysis_service = PredicateAnalysisService()
    return _predicate_analysis_service


def reset_predicate_analysis_service() -> None:
    """Reset the singleton (for testing)."""
    global _predicate_analysis_service
    _predicate_analysis_service = None
