"""
Post-Market Surveillance Planning — Sprint 9B.

Implements post-market surveillance planning per SOR/98-282 Part 6:
- Mandatory problem reporting timelines
- Post-Market Clinical Follow-up (PMCF) planning
- Vigilance and recall planning

Per CLAUDE.md: Structure first, AI second.
Per CLAUDE.md: Every substantive output cites its source.

All requirements are derived from SOR/98-282 Part 6 (Post-Market Requirements).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from src.utils.logging import get_logger

# =============================================================================
# Types
# =============================================================================

IncidentType = Literal[
    "death",
    "serious_deterioration",
    "device_deficiency",
    "near_miss",
    "other",
]

IncidentSeverity = Literal[
    "death",
    "life_threatening",
    "hospitalization",
    "disability",
    "intervention_required",
    "minor",
]

ReportingTimeline = Literal[
    "10_days",  # Death/serious deterioration with serious risk to health
    "30_days",  # Other incidents or deficiencies
    "as_requested",  # Health Canada may request additional info
]

PMCFActivityType = Literal[
    "clinical_investigation",
    "literature_review",
    "complaint_analysis",
    "registry_data",
    "field_safety_corrective_action",
    "periodic_safety_update",
]

# =============================================================================
# Reporting Timeline Constants (SOR/98-282, s.59-61)
# =============================================================================

MANDATORY_REPORTING_TIMELINES: dict[str, dict] = {
    "death_or_serious": {
        "timeline": "10_days",
        "description": "Death or serious deterioration in health with serious risk",
        "citation": "[SOR/98-282, s.59(1)]",
    },
    "other_incident": {
        "timeline": "30_days",
        "description": "Other incidents or device deficiencies",
        "citation": "[SOR/98-282, s.59(2)]",
    },
    "trend_analysis": {
        "timeline": "as_requested",
        "description": "Trend analysis of incidents upon request",
        "citation": "[SOR/98-282, s.60]",
    },
}


# =============================================================================
# Models
# =============================================================================


class MandatoryReportingRequirement(BaseModel):
    """A mandatory problem reporting requirement per SOR/98-282 s.59-61."""

    id: str
    incident_types: list[IncidentType]
    severity_levels: list[IncidentSeverity]
    timeline: ReportingTimeline
    timeline_days: int = Field(description="Number of days for reporting")
    description: str
    citation: str
    guidance_ref: str | None = None


class IncidentReport(BaseModel):
    """An incident report for post-market surveillance.

    Based on SOR/98-282 s.59-61 mandatory problem reporting.
    """

    id: UUID | None = None
    organization_id: UUID
    device_version_id: UUID

    # Incident details
    incident_type: IncidentType
    severity: IncidentSeverity
    incident_date: date
    description: str
    patient_outcome: str | None = None

    # Device information
    lot_number: str | None = None
    serial_number: str | None = None

    # Reporting
    reported_to_hc: bool = False
    reported_date: date | None = None
    report_reference: str | None = None

    # Timeline
    reporting_deadline: date | None = None
    on_time: bool | None = None

    # Citation
    regulation_ref: str = "SOR-98-282-S59"

    @model_validator(mode="after")
    def calculate_deadline(self) -> IncidentReport:
        """Calculate reporting deadline based on incident type and severity."""
        from datetime import timedelta

        if self.incident_type in ("death", "serious_deterioration"):
            if self.severity in ("death", "life_threatening", "hospitalization"):
                # 10 days for death/serious per s.59(1)
                self.reporting_deadline = self.incident_date + timedelta(days=10)
            else:
                # 30 days for other incidents
                self.reporting_deadline = self.incident_date + timedelta(days=30)
        else:
            # 30 days for other incidents
            self.reporting_deadline = self.incident_date + timedelta(days=30)

        if self.reported_date and self.reporting_deadline:
            self.on_time = self.reported_date <= self.reporting_deadline

        return self


class PMCFActivity(BaseModel):
    """A Post-Market Clinical Follow-up (PMCF) activity.

    PMCF is required to confirm clinical performance and safety
    throughout the device lifecycle.
    """

    id: UUID | None = None
    organization_id: UUID
    device_version_id: UUID

    activity_type: PMCFActivityType
    title: str
    description: str

    # Planning
    planned_start: date | None = None
    planned_end: date | None = None
    actual_start: date | None = None
    actual_end: date | None = None

    # Status
    status: Literal["planned", "in_progress", "completed", "cancelled"] = "planned"

    # Outcomes
    findings: str | None = None
    actions_required: list[str] = Field(default_factory=list)

    # Citations
    regulation_ref: str = "SOR-98-282-PART6"
    guidance_ref: str = "GUI-0102"


class RecallPlan(BaseModel):
    """A recall planning document for post-market.

    Based on SOR/98-282 s.64-65 recall requirements.
    """

    id: UUID | None = None
    organization_id: UUID
    device_version_id: UUID

    # Classification (Health Canada recall classification)
    recall_class: Literal["I", "II", "III"] | None = None

    # Recall details
    reason: str
    scope: str  # Geographic, product lines affected
    affected_units: int | None = None
    affected_lots: list[str] = Field(default_factory=list)

    # Actions
    customer_notification_template: str | None = None
    return_instructions: str | None = None
    replacement_plan: str | None = None

    # Status
    status: Literal["draft", "approved", "initiated", "completed", "closed"] = "draft"
    initiated_date: date | None = None
    completed_date: date | None = None

    # Health Canada notification
    hc_notified: bool = False
    hc_notification_date: date | None = None
    hc_reference: str | None = None

    # Citation
    regulation_ref: str = "SOR-98-282-S64"


class PostMarketPlan(BaseModel):
    """Complete post-market surveillance plan for a device.

    Encompasses:
    - Mandatory problem reporting procedures
    - PMCF activities
    - Vigilance procedures
    - Recall procedures
    """

    id: UUID | None = None
    organization_id: UUID
    device_version_id: UUID
    device_class: str

    # Plan metadata
    title: str = "Post-Market Surveillance Plan"
    version: str = "1.0"
    effective_date: date | None = None
    review_date: date | None = None
    status: Literal["draft", "review", "approved", "active", "retired"] = "draft"

    # Responsible personnel
    pms_manager: str | None = None
    medical_device_safety_officer: str | None = None
    quality_manager: str | None = None

    # Reporting procedures
    incident_reporting_procedure: str | None = None
    reporting_timelines_acknowledged: bool = False

    # PMCF
    pmcf_required: bool = False
    pmcf_rationale: str | None = None
    pmcf_activities: list[PMCFActivity] = Field(default_factory=list)

    # Vigilance
    complaint_handling_procedure: str | None = None
    trend_analysis_procedure: str | None = None
    trend_analysis_frequency: str | None = None  # e.g., "quarterly"

    # Recall readiness
    recall_procedure: str | None = None
    recall_plan_template: str | None = None

    # Periodic reporting
    periodic_safety_report_frequency: str | None = None
    next_periodic_report_date: date | None = None

    # Regulatory citations
    regulation_ref: str = "SOR-98-282-PART6"
    guidance_ref: str | None = "GUI-0102"

    # Completeness tracking
    completeness_score: float = 0.0

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Pre-populated Reporting Requirements
# =============================================================================

REPORTING_REQUIREMENTS: dict[str, MandatoryReportingRequirement] = {
    "RPT-001": MandatoryReportingRequirement(
        id="RPT-001",
        incident_types=["death"],
        severity_levels=["death"],
        timeline="10_days",
        timeline_days=10,
        description="Death of a patient associated with the device",
        citation="[SOR/98-282, s.59(1)(a)]",
    ),
    "RPT-002": MandatoryReportingRequirement(
        id="RPT-002",
        incident_types=["serious_deterioration"],
        severity_levels=["life_threatening", "hospitalization", "disability"],
        timeline="10_days",
        timeline_days=10,
        description="Serious deterioration in health with serious risk to health",
        citation="[SOR/98-282, s.59(1)(b)]",
    ),
    "RPT-003": MandatoryReportingRequirement(
        id="RPT-003",
        incident_types=["device_deficiency"],
        severity_levels=["intervention_required"],
        timeline="10_days",
        timeline_days=10,
        description="Device deficiency that could lead to death or serious deterioration",
        citation="[SOR/98-282, s.59(1)(c)]",
    ),
    "RPT-004": MandatoryReportingRequirement(
        id="RPT-004",
        incident_types=["device_deficiency", "other"],
        severity_levels=["minor"],
        timeline="30_days",
        timeline_days=30,
        description="Other incidents or deficiencies requiring reporting",
        citation="[SOR/98-282, s.59(2)]",
    ),
    "RPT-005": MandatoryReportingRequirement(
        id="RPT-005",
        incident_types=["other"],
        severity_levels=["minor"],
        timeline="as_requested",
        timeline_days=0,
        description="Trend analysis or additional information upon request",
        citation="[SOR/98-282, s.60]",
    ),
}


# =============================================================================
# Service
# =============================================================================


class PostMarketService:
    """Service for post-market surveillance planning and tracking.

    All requirements are derived from SOR/98-282 Part 6.
    """

    def __init__(self) -> None:
        """Initialize the post-market service."""
        self.logger = get_logger(__name__)
        self._reporting_requirements = REPORTING_REQUIREMENTS

    def get_reporting_requirements(self) -> list[MandatoryReportingRequirement]:
        """Get all mandatory reporting requirements."""
        return list(self._reporting_requirements.values())

    def get_reporting_timeline(
        self, incident_type: IncidentType, severity: IncidentSeverity
    ) -> tuple[ReportingTimeline, int]:
        """Get reporting timeline for an incident.

        Args:
            incident_type: Type of incident.
            severity: Severity of incident.

        Returns:
            Tuple of (timeline, days) for reporting.
        """
        # Death is always 10 days
        if incident_type == "death" or severity == "death":
            return "10_days", 10

        # Serious deterioration with serious outcomes is 10 days
        if incident_type == "serious_deterioration" and severity in (
            "life_threatening",
            "hospitalization",
            "disability",
        ):
            return "10_days", 10

        # Device deficiency that could cause serious harm is 10 days
        if incident_type == "device_deficiency" and severity in (
            "life_threatening",
            "intervention_required",
        ):
            return "10_days", 10

        # Other incidents are 30 days
        return "30_days", 30

    def create_incident_report(
        self,
        organization_id: UUID,
        device_version_id: UUID,
        incident_type: IncidentType,
        severity: IncidentSeverity,
        incident_date: date,
        description: str,
        **kwargs: Any,
    ) -> IncidentReport:
        """Create an incident report with calculated deadline.

        Args:
            organization_id: Organization UUID.
            device_version_id: Device version UUID.
            incident_type: Type of incident.
            severity: Severity of incident.
            incident_date: Date of incident.
            description: Description of incident.
            **kwargs: Additional fields.

        Returns:
            IncidentReport with deadline calculated.
        """
        return IncidentReport(
            organization_id=organization_id,
            device_version_id=device_version_id,
            incident_type=incident_type,
            severity=severity,
            incident_date=incident_date,
            description=description,
            **kwargs,
        )

    def create_pmcf_activity(
        self,
        organization_id: UUID,
        device_version_id: UUID,
        activity_type: PMCFActivityType,
        title: str,
        description: str,
        **kwargs: Any,
    ) -> PMCFActivity:
        """Create a PMCF activity.

        Args:
            organization_id: Organization UUID.
            device_version_id: Device version UUID.
            activity_type: Type of PMCF activity.
            title: Activity title.
            description: Activity description.
            **kwargs: Additional fields.

        Returns:
            PMCFActivity instance.
        """
        return PMCFActivity(
            organization_id=organization_id,
            device_version_id=device_version_id,
            activity_type=activity_type,
            title=title,
            description=description,
            **kwargs,
        )

    def create_post_market_plan(
        self,
        organization_id: UUID,
        device_version_id: UUID,
        device_class: str,
        **kwargs: Any,
    ) -> PostMarketPlan:
        """Create a post-market surveillance plan.

        Args:
            organization_id: Organization UUID.
            device_version_id: Device version UUID.
            device_class: Device class (I, II, III, IV).
            **kwargs: Additional fields.

        Returns:
            PostMarketPlan instance.
        """
        # PMCF is typically required for Class III/IV
        pmcf_required = device_class in ("III", "IV")

        plan = PostMarketPlan(
            organization_id=organization_id,
            device_version_id=device_version_id,
            device_class=device_class,
            pmcf_required=pmcf_required,
            **kwargs,
        )
        plan.completeness_score = self.calculate_plan_completeness(plan)
        return plan

    def calculate_plan_completeness(self, plan: PostMarketPlan) -> float:
        """Calculate the completeness score for a PMS plan.

        Args:
            plan: The post-market plan.

        Returns:
            Score between 0.0 and 1.0.
        """
        required_fields = [
            plan.pms_manager is not None,
            plan.incident_reporting_procedure is not None,
            plan.reporting_timelines_acknowledged,
            plan.complaint_handling_procedure is not None,
            plan.recall_procedure is not None,
        ]

        # PMCF required for Class III/IV
        if plan.device_class in ("III", "IV"):
            required_fields.extend(
                [
                    plan.pmcf_required,
                    plan.pmcf_rationale is not None or len(plan.pmcf_activities) > 0,
                ]
            )

        # Trend analysis for higher classes
        if plan.device_class in ("II", "III", "IV"):
            required_fields.append(plan.trend_analysis_procedure is not None)

        completed = sum(1 for f in required_fields if f)
        return completed / len(required_fields) if required_fields else 0.0

    def is_pmcf_required(self, device_class: str) -> bool:
        """Determine if PMCF is required for a device class.

        Per GUI-0102, PMCF is typically required for Class III/IV.

        Args:
            device_class: Device class.

        Returns:
            True if PMCF is required.
        """
        return device_class in ("III", "IV")


# =============================================================================
# Singleton accessor
# =============================================================================

_post_market_service: PostMarketService | None = None


def get_post_market_service() -> PostMarketService:
    """Get or create the post-market service singleton."""
    global _post_market_service
    if _post_market_service is None:
        _post_market_service = PostMarketService()
    return _post_market_service
