"""
Unit tests for Post-Market Surveillance Planning.

Sprint 9B — Tests for PostMarketService, incident reporting,
PMCF activities, and post-market planning.

Tests use mock data (no DB required).
"""

from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

import pytest

from src.core.post_market import (
    MANDATORY_REPORTING_TIMELINES,
    REPORTING_REQUIREMENTS,
    IncidentReport,
    MandatoryReportingRequirement,
    PMCFActivity,
    PostMarketPlan,
    PostMarketService,
    RecallPlan,
    get_post_market_service,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def post_market_service() -> PostMarketService:
    """Get post-market service."""
    return PostMarketService()


@pytest.fixture
def organization_id() -> uuid4:
    """Get a sample organization ID."""
    return uuid4()


@pytest.fixture
def device_version_id() -> uuid4:
    """Get a sample device version ID."""
    return uuid4()


# =============================================================================
# MandatoryReportingRequirement Model Tests
# =============================================================================


@pytest.mark.unit
class TestMandatoryReportingRequirementModel:
    """Tests for MandatoryReportingRequirement model."""

    def test_valid_requirement(self):
        """Create a valid reporting requirement."""
        req = MandatoryReportingRequirement(
            id="RPT-TEST",
            incident_types=["death"],
            severity_levels=["death"],
            timeline="10_days",
            timeline_days=10,
            description="Death reporting requirement",
            citation="[SOR/98-282, s.59(1)(a)]",
        )
        assert req.id == "RPT-TEST"
        assert req.timeline_days == 10

    def test_multiple_incident_types(self):
        """Requirement can have multiple incident types."""
        req = MandatoryReportingRequirement(
            id="RPT-MULTI",
            incident_types=["death", "serious_deterioration"],
            severity_levels=["death", "life_threatening"],
            timeline="10_days",
            timeline_days=10,
            description="Serious incident reporting",
            citation="[SOR/98-282, s.59(1)]",
        )
        assert len(req.incident_types) == 2
        assert len(req.severity_levels) == 2


# =============================================================================
# IncidentReport Model Tests
# =============================================================================


@pytest.mark.unit
class TestIncidentReportModel:
    """Tests for IncidentReport model."""

    def test_valid_incident_report(self, organization_id, device_version_id):
        """Create a valid incident report."""
        report = IncidentReport(
            organization_id=organization_id,
            device_version_id=device_version_id,
            incident_type="death",
            severity="death",
            incident_date=date.today(),
            description="Patient death during device use",
        )
        assert report.incident_type == "death"
        assert report.regulation_ref == "SOR-98-282-S59"

    def test_deadline_calculation_death(self, organization_id, device_version_id):
        """Death incidents should have 10-day deadline."""
        incident_date = date.today()
        report = IncidentReport(
            organization_id=organization_id,
            device_version_id=device_version_id,
            incident_type="death",
            severity="death",
            incident_date=incident_date,
            description="Patient death",
        )
        expected_deadline = incident_date + timedelta(days=10)
        assert report.reporting_deadline == expected_deadline

    def test_deadline_calculation_serious(self, organization_id, device_version_id):
        """Serious deterioration should have 10-day deadline."""
        incident_date = date.today()
        report = IncidentReport(
            organization_id=organization_id,
            device_version_id=device_version_id,
            incident_type="serious_deterioration",
            severity="hospitalization",
            incident_date=incident_date,
            description="Patient hospitalized",
        )
        expected_deadline = incident_date + timedelta(days=10)
        assert report.reporting_deadline == expected_deadline

    def test_deadline_calculation_minor(self, organization_id, device_version_id):
        """Minor incidents should have 30-day deadline."""
        incident_date = date.today()
        report = IncidentReport(
            organization_id=organization_id,
            device_version_id=device_version_id,
            incident_type="device_deficiency",
            severity="minor",
            incident_date=incident_date,
            description="Minor device issue",
        )
        expected_deadline = incident_date + timedelta(days=30)
        assert report.reporting_deadline == expected_deadline

    def test_on_time_reporting(self, organization_id, device_version_id):
        """On-time flag should be calculated correctly."""
        incident_date = date.today() - timedelta(days=5)
        report = IncidentReport(
            organization_id=organization_id,
            device_version_id=device_version_id,
            incident_type="death",
            severity="death",
            incident_date=incident_date,
            description="Patient death",
            reported_date=date.today(),
        )
        # Reported within 10 days, should be on time
        assert report.on_time is True

    def test_late_reporting(self, organization_id, device_version_id):
        """Late reporting should be flagged."""
        incident_date = date.today() - timedelta(days=15)
        report = IncidentReport(
            organization_id=organization_id,
            device_version_id=device_version_id,
            incident_type="death",
            severity="death",
            incident_date=incident_date,
            description="Patient death",
            reported_date=date.today(),
        )
        # Reported after 10 days, should be late
        assert report.on_time is False


# =============================================================================
# PMCFActivity Model Tests
# =============================================================================


@pytest.mark.unit
class TestPMCFActivityModel:
    """Tests for PMCFActivity model."""

    def test_valid_pmcf_activity(self, organization_id, device_version_id):
        """Create a valid PMCF activity."""
        activity = PMCFActivity(
            organization_id=organization_id,
            device_version_id=device_version_id,
            activity_type="clinical_investigation",
            title="Post-market clinical study",
            description="5-year follow-up study",
        )
        assert activity.activity_type == "clinical_investigation"
        assert activity.status == "planned"

    def test_pmcf_with_dates(self, organization_id, device_version_id):
        """PMCF activity with planning dates."""
        activity = PMCFActivity(
            organization_id=organization_id,
            device_version_id=device_version_id,
            activity_type="literature_review",
            title="Annual literature review",
            description="Review of published literature",
            planned_start=date.today(),
            planned_end=date.today() + timedelta(days=30),
        )
        assert activity.planned_start is not None
        assert activity.planned_end is not None

    def test_pmcf_with_findings(self, organization_id, device_version_id):
        """PMCF activity with findings."""
        activity = PMCFActivity(
            organization_id=organization_id,
            device_version_id=device_version_id,
            activity_type="complaint_analysis",
            title="Quarterly complaint analysis",
            description="Analysis of customer complaints",
            status="completed",
            findings="No safety signals identified",
            actions_required=["Continue monitoring"],
        )
        assert activity.findings is not None
        assert len(activity.actions_required) == 1


# =============================================================================
# RecallPlan Model Tests
# =============================================================================


@pytest.mark.unit
class TestRecallPlanModel:
    """Tests for RecallPlan model."""

    def test_valid_recall_plan(self, organization_id, device_version_id):
        """Create a valid recall plan."""
        plan = RecallPlan(
            organization_id=organization_id,
            device_version_id=device_version_id,
            reason="Software defect identified",
            scope="Canada",
            recall_class="II",
        )
        assert plan.recall_class == "II"
        assert plan.regulation_ref == "SOR-98-282-S64"

    def test_recall_with_lots(self, organization_id, device_version_id):
        """Recall plan with affected lots."""
        plan = RecallPlan(
            organization_id=organization_id,
            device_version_id=device_version_id,
            reason="Material defect",
            scope="North America",
            affected_lots=["LOT-2026-001", "LOT-2026-002"],
            affected_units=5000,
        )
        assert len(plan.affected_lots) == 2
        assert plan.affected_units == 5000


# =============================================================================
# PostMarketPlan Model Tests
# =============================================================================


@pytest.mark.unit
class TestPostMarketPlanModel:
    """Tests for PostMarketPlan model."""

    def test_valid_pms_plan(self, organization_id, device_version_id):
        """Create a valid post-market plan."""
        plan = PostMarketPlan(
            organization_id=organization_id,
            device_version_id=device_version_id,
            device_class="III",
        )
        assert plan.device_class == "III"
        assert plan.status == "draft"
        assert plan.regulation_ref == "SOR-98-282-PART6"

    def test_pms_plan_with_personnel(self, organization_id, device_version_id):
        """PMS plan with responsible personnel."""
        plan = PostMarketPlan(
            organization_id=organization_id,
            device_version_id=device_version_id,
            device_class="II",
            pms_manager="Jane Doe",
            medical_device_safety_officer="Dr. Smith",
            quality_manager="John QA",
        )
        assert plan.pms_manager == "Jane Doe"

    def test_pms_plan_with_pmcf(self, organization_id, device_version_id):
        """PMS plan with PMCF activities."""
        activity = PMCFActivity(
            organization_id=organization_id,
            device_version_id=device_version_id,
            activity_type="registry_data",
            title="Registry study",
            description="Real-world data collection",
        )
        plan = PostMarketPlan(
            organization_id=organization_id,
            device_version_id=device_version_id,
            device_class="IV",
            pmcf_required=True,
            pmcf_rationale="High-risk implantable device",
            pmcf_activities=[activity],
        )
        assert plan.pmcf_required is True
        assert len(plan.pmcf_activities) == 1


# =============================================================================
# Pre-populated Requirements Tests
# =============================================================================


@pytest.mark.unit
class TestPrePopulatedRequirements:
    """Tests for pre-populated reporting requirements."""

    def test_requirements_count(self):
        """Should have at least 5 reporting requirements."""
        assert len(REPORTING_REQUIREMENTS) >= 5

    def test_death_requirement_exists(self):
        """Should have death reporting requirement."""
        death_reqs = [r for r in REPORTING_REQUIREMENTS.values() if "death" in r.incident_types]
        assert len(death_reqs) >= 1

    def test_10_day_requirements_exist(self):
        """Should have 10-day timeline requirements."""
        ten_day_reqs = [r for r in REPORTING_REQUIREMENTS.values() if r.timeline == "10_days"]
        assert len(ten_day_reqs) >= 3

    def test_all_requirements_have_citations(self):
        """All requirements should have citations."""
        for req_id, req in REPORTING_REQUIREMENTS.items():
            assert req.citation is not None, f"{req_id} missing citation"
            assert "SOR/98-282" in req.citation

    def test_mandatory_timelines_dict(self):
        """Should have mandatory timelines dictionary."""
        assert "death_or_serious" in MANDATORY_REPORTING_TIMELINES
        assert "other_incident" in MANDATORY_REPORTING_TIMELINES


# =============================================================================
# PostMarketService Tests
# =============================================================================


@pytest.mark.unit
class TestPostMarketService:
    """Tests for PostMarketService."""

    def test_get_reporting_requirements(self, post_market_service):
        """Should return all reporting requirements."""
        reqs = post_market_service.get_reporting_requirements()
        assert len(reqs) >= 5

    def test_get_timeline_death(self, post_market_service):
        """Death incidents should have 10-day timeline."""
        timeline, days = post_market_service.get_reporting_timeline("death", "death")
        assert timeline == "10_days"
        assert days == 10

    def test_get_timeline_serious(self, post_market_service):
        """Serious deterioration should have 10-day timeline."""
        timeline, days = post_market_service.get_reporting_timeline(
            "serious_deterioration", "hospitalization"
        )
        assert timeline == "10_days"
        assert days == 10

    def test_get_timeline_minor(self, post_market_service):
        """Minor incidents should have 30-day timeline."""
        timeline, days = post_market_service.get_reporting_timeline("device_deficiency", "minor")
        assert timeline == "30_days"
        assert days == 30

    def test_create_incident_report(self, post_market_service, organization_id, device_version_id):
        """Should create incident report with deadline."""
        report = post_market_service.create_incident_report(
            organization_id=organization_id,
            device_version_id=device_version_id,
            incident_type="death",
            severity="death",
            incident_date=date.today(),
            description="Test incident",
        )
        assert isinstance(report, IncidentReport)
        assert report.reporting_deadline is not None

    def test_create_pmcf_activity(self, post_market_service, organization_id, device_version_id):
        """Should create PMCF activity."""
        activity = post_market_service.create_pmcf_activity(
            organization_id=organization_id,
            device_version_id=device_version_id,
            activity_type="literature_review",
            title="Annual review",
            description="Review of literature",
        )
        assert isinstance(activity, PMCFActivity)
        assert activity.activity_type == "literature_review"

    def test_create_post_market_plan(self, post_market_service, organization_id, device_version_id):
        """Should create post-market plan."""
        plan = post_market_service.create_post_market_plan(
            organization_id=organization_id,
            device_version_id=device_version_id,
            device_class="III",
        )
        assert isinstance(plan, PostMarketPlan)
        assert plan.device_class == "III"
        # Class III should have PMCF required
        assert plan.pmcf_required is True

    def test_is_pmcf_required_class_iii(self, post_market_service):
        """Class III should require PMCF."""
        assert post_market_service.is_pmcf_required("III") is True

    def test_is_pmcf_required_class_iv(self, post_market_service):
        """Class IV should require PMCF."""
        assert post_market_service.is_pmcf_required("IV") is True

    def test_is_pmcf_required_class_ii(self, post_market_service):
        """Class II should not require PMCF by default."""
        assert post_market_service.is_pmcf_required("II") is False

    def test_is_pmcf_required_class_i(self, post_market_service):
        """Class I should not require PMCF."""
        assert post_market_service.is_pmcf_required("I") is False


# =============================================================================
# Plan Completeness Tests
# =============================================================================


@pytest.mark.unit
class TestPlanCompleteness:
    """Tests for post-market plan completeness calculation."""

    def test_empty_plan_low_score(self, post_market_service, organization_id, device_version_id):
        """Empty plan should have low completeness score."""
        plan = PostMarketPlan(
            organization_id=organization_id,
            device_version_id=device_version_id,
            device_class="II",
        )
        score = post_market_service.calculate_plan_completeness(plan)
        assert score < 0.5

    def test_complete_class_ii_plan(self, post_market_service, organization_id, device_version_id):
        """Complete Class II plan should have high score."""
        plan = PostMarketPlan(
            organization_id=organization_id,
            device_version_id=device_version_id,
            device_class="II",
            pms_manager="Jane Doe",
            incident_reporting_procedure="SOP-PMS-001",
            reporting_timelines_acknowledged=True,
            complaint_handling_procedure="SOP-CAPA-002",
            recall_procedure="SOP-RECALL-001",
            trend_analysis_procedure="SOP-TREND-001",
        )
        score = post_market_service.calculate_plan_completeness(plan)
        assert score >= 0.8

    def test_complete_class_iii_plan(self, post_market_service, organization_id, device_version_id):
        """Complete Class III plan with PMCF should have high score."""
        plan = PostMarketPlan(
            organization_id=organization_id,
            device_version_id=device_version_id,
            device_class="III",
            pms_manager="Jane Doe",
            incident_reporting_procedure="SOP-PMS-001",
            reporting_timelines_acknowledged=True,
            complaint_handling_procedure="SOP-CAPA-002",
            recall_procedure="SOP-RECALL-001",
            trend_analysis_procedure="SOP-TREND-001",
            pmcf_required=True,
            pmcf_rationale="High-risk device requires clinical follow-up",
        )
        score = post_market_service.calculate_plan_completeness(plan)
        assert score >= 0.8


# =============================================================================
# Singleton Tests
# =============================================================================


@pytest.mark.unit
class TestSingleton:
    """Tests for singleton accessor."""

    def test_get_post_market_service(self):
        """Should return a PostMarketService."""
        service = get_post_market_service()
        assert isinstance(service, PostMarketService)

    def test_singleton_returns_same_instance(self):
        """Should return the same instance."""
        service1 = get_post_market_service()
        service2 = get_post_market_service()
        assert service1 is service2


# =============================================================================
# Regulatory Citation Tests
# =============================================================================


@pytest.mark.unit
@pytest.mark.regulatory
class TestRegulatoryCitations:
    """Tests for regulatory citation compliance."""

    def test_requirements_cite_sor_98_282(self):
        """All requirements should cite SOR/98-282."""
        for req in REPORTING_REQUIREMENTS.values():
            assert "SOR/98-282" in req.citation

    def test_incident_report_has_citation(self, organization_id, device_version_id):
        """Incident reports should have regulation reference."""
        report = IncidentReport(
            organization_id=organization_id,
            device_version_id=device_version_id,
            incident_type="death",
            severity="death",
            incident_date=date.today(),
            description="Test incident",
        )
        assert "SOR" in report.regulation_ref

    def test_pmcf_has_citations(self, organization_id, device_version_id):
        """PMCF activities should have citations."""
        activity = PMCFActivity(
            organization_id=organization_id,
            device_version_id=device_version_id,
            activity_type="clinical_investigation",
            title="Test study",
            description="Test",
        )
        assert "SOR" in activity.regulation_ref
        assert "GUI" in activity.guidance_ref

    def test_pms_plan_has_citations(self, organization_id, device_version_id):
        """PMS plans should have citations."""
        plan = PostMarketPlan(
            organization_id=organization_id,
            device_version_id=device_version_id,
            device_class="II",
        )
        assert "SOR" in plan.regulation_ref
