"""
Design Controls — ISO 13485 Section 7.3 Traceability.

Implements design control entities for:
- Design Inputs (7.3.2): User needs, requirements
- Design Outputs (7.3.3): Specifications meeting inputs
- Design Reviews (7.3.5): Formal review records
- Design Verification (7.3.6): Confirms outputs meet inputs
- Design Validation (7.3.7): Confirms device meets user needs

REGULATORY REFERENCES:
    - ISO 13485:2016 Sections 7.3.1-7.3.10
    - SOR/98-282 s.10 (Quality management system)
    - GUI-0064 (Design Control Guidance)

CITATION-FIRST PRINCIPLE:
    All models include regulatory_reference fields for traceability.
"""

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from src.utils.logging import get_logger

# =============================================================================
# Type Definitions
# =============================================================================

DesignInputSource = Literal[
    "user_need",
    "clinical_feedback",
    "regulatory",
    "standard",
    "competitive",
    "risk_analysis",
]

DesignInputPriority = Literal["essential", "desired", "nice_to_have"]

DesignOutputType = Literal[
    "specification",
    "drawing",
    "procedure",
    "software_requirement",
    "test_method",
    "manufacturing_spec",
]

DesignOutputStatus = Literal["draft", "reviewed", "approved", "released"]

DesignPhase = Literal[
    "concept",
    "feasibility",
    "development",
    "verification",
    "validation",
    "transfer",
    "post_market",
]

DesignReviewDecision = Literal["proceed", "proceed_with_conditions", "repeat", "stop"]

VerificationMethod = Literal[
    "inspection",
    "analysis",
    "test",
    "demonstration",
]

# =============================================================================
# Models
# =============================================================================


class DesignInput(BaseModel):
    """User need or requirement driving design (ISO 13485 7.3.2).

    Design inputs are requirements that the device design must meet.
    They come from various sources: user needs, regulatory requirements,
    clinical feedback, applicable standards, competitive analysis.

    Citation: [ISO 13485:2016, 7.3.2]
    """

    id: UUID | None = Field(default=None, description="Design input record ID")
    organization_id: UUID = Field(..., description="Owning organization")
    device_version_id: UUID = Field(..., description="Device version")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")

    # Source and classification
    source: DesignInputSource = Field(..., description="Source of this input")
    priority: DesignInputPriority = Field(default="essential", description="Input priority")
    input_type: str = Field(default="functional", description="Type of input requirement")

    # Content
    title: str = Field(..., description="Short title for the input")
    description: str = Field(..., description="Detailed description of the requirement")
    rationale: str | None = Field(default=None, description="Why this input is needed")
    acceptance_criteria: str | None = Field(
        default=None, description="How to verify this input is satisfied"
    )

    # Traceability
    regulatory_reference: str | None = Field(
        default=None, description="Citation if regulatory-driven"
    )
    standard_reference: str | None = Field(
        default=None, description="Standard reference if standard-driven"
    )
    source_document: str | None = Field(default=None, description="Source document reference")

    # Status
    status: str = Field(default="active", description="Input status")
    version: int = Field(default=1, description="Version number")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DesignOutput(BaseModel):
    """Specification or deliverable meeting design input (ISO 13485 7.3.3).

    Design outputs are the specifications, drawings, procedures, or other
    artifacts that document how design inputs will be met.

    Citation: [ISO 13485:2016, 7.3.3]
    """

    id: UUID | None = Field(default=None, description="Design output record ID")
    organization_id: UUID = Field(..., description="Owning organization")
    device_version_id: UUID = Field(..., description="Device version")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")

    # Linked input
    design_input_id: UUID | None = Field(
        default=None, description="Design input this output satisfies"
    )

    # Classification
    output_type: DesignOutputType = Field(..., description="Type of output")
    status: DesignOutputStatus = Field(default="draft", description="Approval status")

    # Content
    title: str = Field(..., description="Output title")
    specification: str = Field(..., description="The specification content")
    acceptance_criteria: str = Field(..., description="How to verify this output")
    drawing_number: str | None = Field(default=None, description="Drawing/document number")

    # Traceability
    regulatory_reference: str | None = Field(default=None, description="Applicable regulation")
    standard_reference: str | None = Field(default=None, description="Applicable standard")

    # Approval
    approved_by: str | None = Field(default=None, description="Approver name")
    approved_at: datetime | None = Field(default=None, description="Approval timestamp")
    version: int = Field(default=1, description="Version number")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DesignReview(BaseModel):
    """Formal design review record (ISO 13485 7.3.5).

    Design reviews are systematic examinations of design at defined stages
    to evaluate ability to meet requirements and identify problems.

    Citation: [ISO 13485:2016, 7.3.5]
    """

    id: UUID | None = Field(default=None, description="Design review record ID")
    organization_id: UUID = Field(..., description="Owning organization")
    device_version_id: UUID = Field(..., description="Device version reviewed")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")

    # Review identification
    phase: DesignPhase = Field(..., description="Design phase being reviewed")
    review_number: int = Field(default=1, description="Review number within phase")
    review_date: date = Field(..., description="Date of the review")
    review_title: str = Field(..., description="Review meeting title")

    # Participants
    participants: list[str] = Field(default_factory=list, description="Review participants")
    chairperson: str | None = Field(default=None, description="Review chairperson")

    # Review content
    objectives: list[str] = Field(default_factory=list, description="Review objectives")
    documents_reviewed: list[str] = Field(default_factory=list, description="Documents reviewed")
    findings: list[str] = Field(default_factory=list, description="Review findings")
    action_items: list[str] = Field(default_factory=list, description="Action items")

    # Decision
    decision: DesignReviewDecision = Field(..., description="Review decision")
    conditions: list[str] = Field(
        default_factory=list, description="Conditions if proceed_with_conditions"
    )
    rationale: str | None = Field(default=None, description="Decision rationale")

    # Traceability
    regulatory_reference: str | None = Field(default=None, description="Applicable regulation")
    meeting_minutes_ref: str | None = Field(
        default=None, description="Meeting minutes document reference"
    )

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DesignVerification(BaseModel):
    """Design verification record (ISO 13485 7.3.6).

    Design verification confirms that design outputs meet design inputs.
    Methods include inspection, analysis, test, and demonstration.

    Citation: [ISO 13485:2016, 7.3.6]
    """

    id: UUID | None = Field(default=None, description="Verification record ID")
    organization_id: UUID = Field(..., description="Owning organization")
    device_version_id: UUID = Field(..., description="Device version")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")

    # Links
    design_output_id: UUID = Field(..., description="Output being verified")
    design_input_id: UUID | None = Field(default=None, description="Input being verified against")

    # Verification method
    method: VerificationMethod = Field(..., description="Verification method used")
    protocol_reference: str | None = Field(default=None, description="Test protocol reference")

    # Content
    title: str = Field(..., description="Verification title")
    description: str = Field(..., description="What was verified")
    acceptance_criteria: str = Field(..., description="Acceptance criteria")

    # Results
    result: Literal["pass", "fail", "conditional"] = Field(..., description="Verification result")
    actual_results: str = Field(..., description="Actual results observed")
    deviations: list[str] = Field(default_factory=list, description="Any deviations noted")
    pass_with_deviation: bool = Field(default=False, description="Pass despite deviations")

    # Evidence
    evidence_references: list[str] = Field(
        default_factory=list, description="Test reports, data references"
    )
    test_date: date | None = Field(default=None, description="Date testing performed")
    performed_by: str | None = Field(default=None, description="Who performed verification")

    # Traceability
    regulatory_reference: str | None = Field(default=None, description="Applicable regulation")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DesignValidation(BaseModel):
    """Design validation record (ISO 13485 7.3.7).

    Design validation confirms the device meets user needs and intended use.
    Must be performed under defined operating conditions on initial
    production units, lots, or batches.

    Citation: [ISO 13485:2016, 7.3.7]
    """

    id: UUID | None = Field(default=None, description="Validation record ID")
    organization_id: UUID = Field(..., description="Owning organization")
    device_version_id: UUID = Field(..., description="Device version")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")

    # Links
    design_output_id: UUID | None = Field(default=None, description="Related design output")
    design_input_id: UUID | None = Field(default=None, description="User need being validated")

    # Validation type
    validation_type: Literal["clinical", "usability", "simulated_use", "field"] = Field(
        ..., description="Type of validation"
    )
    protocol_reference: str | None = Field(default=None, description="Validation protocol")

    # Content
    title: str = Field(..., description="Validation title")
    description: str = Field(..., description="What was validated")
    user_needs_addressed: list[str] = Field(
        default_factory=list, description="User needs this validates"
    )
    acceptance_criteria: str = Field(..., description="Acceptance criteria")

    # Sample information
    sample_description: str | None = Field(
        default=None, description="Sample units used (production representative)"
    )
    sample_size: int | None = Field(default=None, description="Number of samples")
    lot_batch_number: str | None = Field(default=None, description="Lot/batch identifier")

    # Results
    result: Literal["pass", "fail", "conditional"] = Field(..., description="Validation result")
    actual_results: str = Field(..., description="Actual results observed")
    conclusions: str = Field(..., description="Validation conclusions")
    deviations: list[str] = Field(default_factory=list, description="Any deviations noted")

    # Evidence
    evidence_references: list[str] = Field(
        default_factory=list, description="Reports, data references"
    )
    validation_date: date | None = Field(default=None, description="Date validation performed")
    performed_by: str | None = Field(default=None, description="Who performed validation")

    # Traceability
    regulatory_reference: str | None = Field(default=None, description="Applicable regulation")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DesignChange(BaseModel):
    """Design change record (ISO 13485 7.3.9).

    Design changes must be identified, reviewed, verified, validated
    as appropriate, and approved before implementation.

    Citation: [ISO 13485:2016, 7.3.9]
    """

    id: UUID | None = Field(default=None, description="Change record ID")
    organization_id: UUID = Field(..., description="Owning organization")
    device_version_id: UUID = Field(..., description="Device version")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")

    # Change identification
    change_number: str = Field(..., description="Unique change identifier")
    title: str = Field(..., description="Change title")
    description: str = Field(..., description="Detailed description of change")
    rationale: str = Field(..., description="Why change is needed")

    # Classification
    change_type: Literal["major", "minor", "administrative"] = Field(
        ..., description="Change classification"
    )
    affected_items: list[str] = Field(default_factory=list, description="Design outputs affected")

    # Impact assessment
    impact_assessment: str = Field(..., description="Impact analysis")
    risk_impact: str | None = Field(default=None, description="Impact on risk analysis")
    regulatory_impact: str | None = Field(
        default=None, description="Regulatory impact (new submission needed?)"
    )
    verification_required: bool = Field(default=True, description="Re-verification needed")
    validation_required: bool = Field(default=False, description="Re-validation needed")

    # Approval
    status: Literal["proposed", "under_review", "approved", "rejected", "implemented"] = Field(
        default="proposed", description="Change status"
    )
    approved_by: str | None = Field(default=None, description="Approver")
    approved_at: datetime | None = Field(default=None, description="Approval timestamp")
    implemented_at: datetime | None = Field(default=None, description="Implementation date")

    # Traceability
    regulatory_reference: str | None = Field(default=None, description="Applicable regulation")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DesignHistoryRecord(BaseModel):
    """Single entry in the Design History File (ISO 13485 7.3.10).

    The Design History File contains or references all design records
    demonstrating the design was developed in accordance with the plan.

    Citation: [ISO 13485:2016, 7.3.10]
    """

    id: UUID | None = Field(default=None, description="Record ID")
    organization_id: UUID = Field(..., description="Owning organization")
    device_version_id: UUID = Field(..., description="Device version")

    # Record identification
    record_type: Literal[
        "input", "output", "review", "verification", "validation", "change", "transfer"
    ] = Field(..., description="Type of record")
    record_id: UUID = Field(..., description="ID of the actual record")
    record_date: date = Field(..., description="Date of the record")

    # Content
    title: str = Field(..., description="Record title")
    summary: str = Field(..., description="Brief summary")
    document_reference: str | None = Field(default=None, description="Document number/reference")

    # Status
    status: str = Field(default="active", description="Record status")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# =============================================================================
# Service
# =============================================================================


class DesignControlService:
    """
    Service for managing design control records.

    Provides CRUD operations and design control queries for:
    - Design inputs and outputs
    - Design reviews
    - Verification and validation records
    - Design changes
    - Design history file generation

    All operations maintain traceability per ISO 13485.
    """

    def __init__(self) -> None:
        """Initialize the Design Control Service."""
        self.logger = get_logger(self.__class__.__name__)

        # In-memory storage (production would use database)
        self._inputs: dict[UUID, DesignInput] = {}
        self._outputs: dict[UUID, DesignOutput] = {}
        self._reviews: dict[UUID, DesignReview] = {}
        self._verifications: dict[UUID, DesignVerification] = {}
        self._validations: dict[UUID, DesignValidation] = {}
        self._changes: dict[UUID, DesignChange] = {}
        self._history: dict[UUID, DesignHistoryRecord] = {}

    # -------------------------------------------------------------------------
    # Design Input Operations
    # -------------------------------------------------------------------------

    def create_input(self, input_data: DesignInput) -> DesignInput:
        """Create a new design input."""
        from uuid import uuid4

        if input_data.id is None:
            input_data.id = uuid4()
        if input_data.created_at is None:
            input_data.created_at = datetime.utcnow()

        self._inputs[input_data.id] = input_data
        self.logger.info(f"Created design input: {input_data.id}")
        return input_data

    def get_input(self, input_id: UUID) -> DesignInput | None:
        """Get a design input by ID."""
        return self._inputs.get(input_id)

    def list_inputs(self, device_version_id: UUID) -> list[DesignInput]:
        """List all design inputs for a device version."""
        return [inp for inp in self._inputs.values() if inp.device_version_id == device_version_id]

    def get_inputs_by_source(
        self, device_version_id: UUID, source: DesignInputSource
    ) -> list[DesignInput]:
        """Get inputs filtered by source type."""
        return [
            inp
            for inp in self._inputs.values()
            if inp.device_version_id == device_version_id and inp.source == source
        ]

    def get_essential_inputs(self, device_version_id: UUID) -> list[DesignInput]:
        """Get all essential priority inputs."""
        return [
            inp
            for inp in self._inputs.values()
            if inp.device_version_id == device_version_id and inp.priority == "essential"
        ]

    # -------------------------------------------------------------------------
    # Design Output Operations
    # -------------------------------------------------------------------------

    def create_output(self, output_data: DesignOutput) -> DesignOutput:
        """Create a new design output."""
        from uuid import uuid4

        if output_data.id is None:
            output_data.id = uuid4()
        if output_data.created_at is None:
            output_data.created_at = datetime.utcnow()

        self._outputs[output_data.id] = output_data
        self.logger.info(f"Created design output: {output_data.id}")
        return output_data

    def get_output(self, output_id: UUID) -> DesignOutput | None:
        """Get a design output by ID."""
        return self._outputs.get(output_id)

    def list_outputs(self, device_version_id: UUID) -> list[DesignOutput]:
        """List all design outputs for a device version."""
        return [out for out in self._outputs.values() if out.device_version_id == device_version_id]

    def get_outputs_for_input(self, design_input_id: UUID) -> list[DesignOutput]:
        """Get all outputs that satisfy a given input."""
        return [out for out in self._outputs.values() if out.design_input_id == design_input_id]

    def get_approved_outputs(self, device_version_id: UUID) -> list[DesignOutput]:
        """Get all approved design outputs."""
        return [
            out
            for out in self._outputs.values()
            if out.device_version_id == device_version_id and out.status in ("approved", "released")
        ]

    # -------------------------------------------------------------------------
    # Design Review Operations
    # -------------------------------------------------------------------------

    def create_review(self, review_data: DesignReview) -> DesignReview:
        """Create a new design review record."""
        from uuid import uuid4

        if review_data.id is None:
            review_data.id = uuid4()
        if review_data.created_at is None:
            review_data.created_at = datetime.utcnow()

        self._reviews[review_data.id] = review_data
        self.logger.info(f"Created design review: {review_data.id}")
        return review_data

    def get_review(self, review_id: UUID) -> DesignReview | None:
        """Get a design review by ID."""
        return self._reviews.get(review_id)

    def list_reviews(self, device_version_id: UUID) -> list[DesignReview]:
        """List all design reviews for a device version."""
        return [rev for rev in self._reviews.values() if rev.device_version_id == device_version_id]

    def get_reviews_by_phase(
        self, device_version_id: UUID, phase: DesignPhase
    ) -> list[DesignReview]:
        """Get reviews for a specific design phase."""
        return [
            rev
            for rev in self._reviews.values()
            if rev.device_version_id == device_version_id and rev.phase == phase
        ]

    def get_latest_review(self, device_version_id: UUID) -> DesignReview | None:
        """Get the most recent design review."""
        reviews = self.list_reviews(device_version_id)
        if not reviews:
            return None
        return max(reviews, key=lambda r: r.review_date)

    # -------------------------------------------------------------------------
    # Design Verification Operations
    # -------------------------------------------------------------------------

    def create_verification(self, verification_data: DesignVerification) -> DesignVerification:
        """Create a new verification record."""
        from uuid import uuid4

        if verification_data.id is None:
            verification_data.id = uuid4()
        if verification_data.created_at is None:
            verification_data.created_at = datetime.utcnow()

        self._verifications[verification_data.id] = verification_data
        self.logger.info(f"Created design verification: {verification_data.id}")
        return verification_data

    def get_verification(self, verification_id: UUID) -> DesignVerification | None:
        """Get a verification record by ID."""
        return self._verifications.get(verification_id)

    def list_verifications(self, device_version_id: UUID) -> list[DesignVerification]:
        """List all verifications for a device version."""
        return [
            ver
            for ver in self._verifications.values()
            if ver.device_version_id == device_version_id
        ]

    def get_verifications_for_output(self, design_output_id: UUID) -> list[DesignVerification]:
        """Get verifications for a specific design output."""
        return [
            ver for ver in self._verifications.values() if ver.design_output_id == design_output_id
        ]

    # -------------------------------------------------------------------------
    # Design Validation Operations
    # -------------------------------------------------------------------------

    def create_validation(self, validation_data: DesignValidation) -> DesignValidation:
        """Create a new validation record."""
        from uuid import uuid4

        if validation_data.id is None:
            validation_data.id = uuid4()
        if validation_data.created_at is None:
            validation_data.created_at = datetime.utcnow()

        self._validations[validation_data.id] = validation_data
        self.logger.info(f"Created design validation: {validation_data.id}")
        return validation_data

    def get_validation(self, validation_id: UUID) -> DesignValidation | None:
        """Get a validation record by ID."""
        return self._validations.get(validation_id)

    def list_validations(self, device_version_id: UUID) -> list[DesignValidation]:
        """List all validations for a device version."""
        return [
            val for val in self._validations.values() if val.device_version_id == device_version_id
        ]

    def get_validations_by_type(
        self, device_version_id: UUID, validation_type: str
    ) -> list[DesignValidation]:
        """Get validations of a specific type."""
        return [
            val
            for val in self._validations.values()
            if val.device_version_id == device_version_id and val.validation_type == validation_type
        ]

    # -------------------------------------------------------------------------
    # Design Change Operations
    # -------------------------------------------------------------------------

    def create_change(self, change_data: DesignChange) -> DesignChange:
        """Create a new design change record."""
        from uuid import uuid4

        if change_data.id is None:
            change_data.id = uuid4()
        if change_data.created_at is None:
            change_data.created_at = datetime.utcnow()

        self._changes[change_data.id] = change_data
        self.logger.info(f"Created design change: {change_data.id}")
        return change_data

    def get_change(self, change_id: UUID) -> DesignChange | None:
        """Get a design change by ID."""
        return self._changes.get(change_id)

    def list_changes(self, device_version_id: UUID) -> list[DesignChange]:
        """List all design changes for a device version."""
        return [chg for chg in self._changes.values() if chg.device_version_id == device_version_id]

    def get_pending_changes(self, device_version_id: UUID) -> list[DesignChange]:
        """Get changes awaiting approval."""
        return [
            chg
            for chg in self._changes.values()
            if chg.device_version_id == device_version_id
            and chg.status in ("proposed", "under_review")
        ]

    # -------------------------------------------------------------------------
    # Analysis Methods
    # -------------------------------------------------------------------------

    def get_unmet_inputs(self, device_version_id: UUID) -> list[DesignInput]:
        """Get design inputs with no linked outputs.

        An input is considered "unmet" if there are no design outputs
        that reference it via design_input_id.
        """
        inputs = self.list_inputs(device_version_id)
        outputs = self.list_outputs(device_version_id)

        # Build set of input IDs that have outputs
        met_input_ids = {out.design_input_id for out in outputs if out.design_input_id}

        return [inp for inp in inputs if inp.id not in met_input_ids]

    def get_unverified_outputs(self, device_version_id: UUID) -> list[DesignOutput]:
        """Get design outputs with no passing verification.

        An output is "unverified" if there is no verification record
        with result="pass" referencing it.
        """
        outputs = self.list_outputs(device_version_id)
        verifications = self.list_verifications(device_version_id)

        # Build set of output IDs that have passing verifications
        verified_output_ids = {
            ver.design_output_id for ver in verifications if ver.result == "pass"
        }

        return [out for out in outputs if out.id not in verified_output_ids]

    def get_phases_without_review(self, device_version_id: UUID) -> list[DesignPhase]:
        """Get design phases that have no review record.

        Per ISO 13485, reviews should be conducted at suitable stages.
        This identifies phases that haven't had a formal review.
        """
        reviews = self.list_reviews(device_version_id)
        reviewed_phases = {rev.phase for rev in reviews}

        # Standard phases that should have reviews
        required_phases: list[DesignPhase] = [
            "concept",
            "development",
            "verification",
            "validation",
            "transfer",
        ]

        return [phase for phase in required_phases if phase not in reviewed_phases]

    def calculate_design_completeness(self, device_version_id: UUID) -> dict[str, Any]:
        """Calculate design control completeness metrics.

        Returns a summary of design control status including:
        - Input coverage
        - Output verification status
        - Review coverage
        - Validation status
        """
        inputs = self.list_inputs(device_version_id)
        outputs = self.list_outputs(device_version_id)
        reviews = self.list_reviews(device_version_id)
        verifications = self.list_verifications(device_version_id)
        validations = self.list_validations(device_version_id)

        unmet_inputs = self.get_unmet_inputs(device_version_id)
        unverified_outputs = self.get_unverified_outputs(device_version_id)
        missing_reviews = self.get_phases_without_review(device_version_id)

        total_inputs = len(inputs)
        total_outputs = len(outputs)

        return {
            "device_version_id": str(device_version_id),
            "inputs": {
                "total": total_inputs,
                "met": total_inputs - len(unmet_inputs),
                "unmet": len(unmet_inputs),
                "coverage_percent": (
                    ((total_inputs - len(unmet_inputs)) / total_inputs * 100)
                    if total_inputs > 0
                    else 0.0
                ),
            },
            "outputs": {
                "total": total_outputs,
                "verified": total_outputs - len(unverified_outputs),
                "unverified": len(unverified_outputs),
                "verification_percent": (
                    ((total_outputs - len(unverified_outputs)) / total_outputs * 100)
                    if total_outputs > 0
                    else 0.0
                ),
            },
            "reviews": {
                "total": len(reviews),
                "phases_reviewed": len({r.phase for r in reviews}),
                "phases_missing": missing_reviews,
            },
            "verifications": {"total": len(verifications)},
            "validations": {"total": len(validations)},
        }


# =============================================================================
# Singleton Access
# =============================================================================

_design_control_service: DesignControlService | None = None


def get_design_control_service() -> DesignControlService:
    """Get or create the singleton DesignControlService instance.

    Returns:
        DesignControlService singleton.
    """
    global _design_control_service
    if _design_control_service is None:
        _design_control_service = DesignControlService()
    return _design_control_service
