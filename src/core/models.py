"""
Core domain models for the Health Canada Medical Device Regulatory Agent.

These models represent the key concepts in medical device regulation:
- Device classification
- Regulatory pathways
- Documentation requirements
- Compliance tracking
"""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class DeviceClass(StrEnum):
    """Health Canada medical device classification levels."""

    CLASS_I = "I"
    CLASS_II = "II"
    CLASS_III = "III"
    CLASS_IV = "IV"

    @property
    def risk_level(self) -> str:
        """Return human-readable risk level."""
        levels = {
            "I": "Lowest Risk",
            "II": "Low-Moderate Risk",
            "III": "Moderate-High Risk",
            "IV": "Highest Risk",
        }
        return levels[self.value]

    @property
    def review_days(self) -> int:
        """Standard Health Canada review time in calendar days."""
        days = {
            "I": 0,  # No MDL required for Class I
            "II": 15,
            "III": 75,
            "IV": 90,
        }
        return days[self.value]

    @property
    def requires_mdl(self) -> bool:
        """Whether this class requires a Medical Device Licence."""
        return self.value != "I"


class SaMDCategory(StrEnum):
    """IMDRF SaMD significance categories."""

    INFORM = "inform"  # Inform clinical management
    DRIVE = "drive"  # Drive clinical management
    DIAGNOSE = "diagnose"  # Diagnose or screen
    TREAT = "treat"  # Treat or prevent


class HealthcareSituation(StrEnum):
    """IMDRF healthcare situation/state categories."""

    NON_SERIOUS = "non_serious"
    SERIOUS = "serious"
    CRITICAL = "critical"


class DeviceInfo(BaseModel):
    """Information about a medical device for classification."""

    name: str = Field(..., description="Device name or identifier")
    description: str = Field(..., description="Description of device function")
    intended_use: str = Field(..., description="Intended use/purpose statement")
    is_software: bool = Field(default=False, description="Is this a software device (SaMD)?")
    is_ivd: bool = Field(default=False, description="Is this an in-vitro diagnostic device?")
    is_implantable: bool = Field(default=False, description="Is this an implantable device?")
    is_active: bool = Field(default=False, description="Is this an active (powered) device?")
    contact_duration: str | None = Field(
        default=None, description="Duration of body contact (transient/short-term/long-term)"
    )
    invasive_type: str | None = Field(
        default=None, description="Type of invasive use (surgical/body orifice/none)"
    )
    target_population: str | None = Field(default=None, description="Target patient population")
    manufacturer_name: str = Field(..., description="Legal manufacturer name")
    manufacturer_country: str = Field(default="Canada", description="Country of manufacturer")


class SaMDInfo(BaseModel):
    """Additional information specific to Software as Medical Device."""

    healthcare_situation: HealthcareSituation = Field(
        ..., description="Criticality of healthcare situation"
    )
    significance: SaMDCategory = Field(
        ..., description="Significance of information provided by SaMD"
    )
    uses_ml: bool = Field(default=False, description="Does the SaMD use machine learning/AI?")
    is_locked: bool = Field(default=True, description="Is the algorithm locked (non-adaptive)?")
    clinical_validation_patients: int | None = Field(
        default=None, description="Number of patients in clinical validation"
    )


class ClassificationResult(BaseModel):
    """Result of device classification analysis."""

    device_class: DeviceClass = Field(..., description="Determined device class")
    classification_rules: list[str] = Field(
        default_factory=list,
        description="Classification rules applied (e.g., 'Schedule 1, Rule 11')",
    )
    rationale: str = Field(..., description="Explanation of classification decision")
    is_samd: bool = Field(default=False, description="Whether device is classified as SaMD")
    samd_category: str | None = Field(default=None, description="SaMD category if applicable")
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence in classification (0-1)"
    )
    warnings: list[str] = Field(default_factory=list, description="Any warnings or considerations")
    references: list[str] = Field(default_factory=list, description="Regulatory references cited")


class PathwayStep(BaseModel):
    """A single step in the regulatory pathway."""

    step_number: int = Field(..., description="Step sequence number")
    name: str = Field(..., description="Step name")
    description: str = Field(..., description="What this step involves")
    required: bool = Field(default=True, description="Whether this step is mandatory")
    estimated_duration_days: int | None = Field(
        default=None, description="Estimated duration in days"
    )
    dependencies: list[int] = Field(
        default_factory=list, description="Step numbers that must be completed first"
    )
    documents_required: list[str] = Field(
        default_factory=list, description="Documents needed for this step"
    )
    forms: list[str] = Field(default_factory=list, description="Health Canada forms for this step")
    fees: float | None = Field(default=None, description="Fees for this step in CAD")


class Timeline(BaseModel):
    """Estimated timeline for regulatory pathway completion."""

    total_days_min: int = Field(..., description="Minimum estimated days")
    total_days_max: int = Field(..., description="Maximum estimated days")
    critical_path: list[str] = Field(default_factory=list, description="Critical path steps")
    start_date: date | None = Field(default=None, description="Projected start date")
    target_completion: date | None = Field(default=None, description="Target completion date")
    milestones: dict[str, date] = Field(default_factory=dict, description="Key milestone dates")


class FeeBreakdown(BaseModel):
    """Breakdown of regulatory fees."""

    mdel_fee: float = Field(default=0.0, description="MDEL application fee")
    mdl_fee: float = Field(default=0.0, description="MDL application fee")
    annual_fee: float = Field(default=0.0, description="Annual right-to-sell fee")
    amendment_fees: float = Field(default=0.0, description="Any amendment fees")
    total: float = Field(default=0.0, description="Total fees")
    currency: str = Field(default="CAD", description="Currency")
    fee_schedule_date: str = Field(default="2024-04-01", description="Fee schedule effective date")
    notes: list[str] = Field(default_factory=list, description="Notes about fee calculations")


class RegulatoryPathway(BaseModel):
    """Complete regulatory pathway for a device."""

    pathway_name: str = Field(..., description="Name of the pathway")
    device_class: DeviceClass = Field(..., description="Device class")
    requires_mdel: bool = Field(default=True, description="Whether MDEL is required")
    requires_mdl: bool = Field(..., description="Whether MDL is required")
    steps: list[PathwayStep] = Field(default_factory=list, description="Pathway steps")
    timeline: Timeline = Field(..., description="Estimated timeline")
    fees: FeeBreakdown = Field(..., description="Fee breakdown")
    special_requirements: list[str] = Field(
        default_factory=list, description="Special requirements for this pathway"
    )


class ComplianceStatus(StrEnum):
    """Status of a compliance requirement."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    NOT_APPLICABLE = "not_applicable"
    BLOCKED = "blocked"


class ChecklistItem(BaseModel):
    """A single item in a regulatory checklist."""

    id: str = Field(..., description="Unique identifier")
    category: str = Field(..., description="Category (e.g., 'MDEL', 'QMS', 'Clinical')")
    title: str = Field(..., description="Item title")
    description: str = Field(..., description="Detailed description")
    status: ComplianceStatus = Field(
        default=ComplianceStatus.NOT_STARTED, description="Current status"
    )
    required: bool = Field(default=True, description="Whether item is required")
    device_classes: list[DeviceClass] = Field(
        default_factory=list, description="Applicable device classes"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="IDs of items that must be completed first"
    )
    guidance_reference: str | None = Field(
        default=None, description="Reference to guidance document"
    )
    form_number: str | None = Field(
        default=None, description="Associated Health Canada form number"
    )
    notes: str | None = Field(default=None, description="Additional notes")


class Checklist(BaseModel):
    """A complete regulatory checklist."""

    name: str = Field(..., description="Checklist name")
    device_class: DeviceClass = Field(..., description="Target device class")
    items: list[ChecklistItem] = Field(default_factory=list, description="Checklist items")
    created_date: date = Field(default_factory=date.today)
    last_updated: date = Field(default_factory=date.today)

    @property
    def total_items(self) -> int:
        """Total number of items."""
        return len(self.items)

    @property
    def completed_items(self) -> int:
        """Number of completed items."""
        return sum(1 for item in self.items if item.status == ComplianceStatus.COMPLETED)

    @property
    def completion_percentage(self) -> float:
        """Percentage of items completed."""
        if self.total_items == 0:
            return 0.0
        return (self.completed_items / self.total_items) * 100


class DocumentRequirement(BaseModel):
    """A required document for regulatory submission."""

    name: str = Field(..., description="Document name")
    imdrf_section: str | None = Field(default=None, description="IMDRF Table of Contents section")
    description: str = Field(..., description="What the document should contain")
    required_for_classes: list[DeviceClass] = Field(
        default_factory=list, description="Device classes requiring this document"
    )
    template_available: bool = Field(default=False, description="Whether a template is available")
    guidance_reference: str | None = Field(default=None, description="Guidance document reference")
    examples: list[str] = Field(default_factory=list, description="Example content or formats")
