"""
Tests for Clinical Evidence Service — Sprint 7A

Tests all components:
- ClinicalStudyType and evidence hierarchy scoring
- ClinicalEvidence Pydantic model
- ClinicalEvidencePortfolio aggregation
- ClinicalPackageAssessment against device class thresholds
- ClinicalEvidenceService CRUD and scoring operations
"""

from uuid import uuid4

import pytest

from src.core.clinical_evidence import (
    CLASS_EVIDENCE_THRESHOLDS,
    EVIDENCE_HIERARCHY_SCORE,
    ClinicalEvidence,
    ClinicalEvidenceService,
    get_clinical_evidence_service,
    reset_clinical_evidence_service,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def reset_service():
    """Reset the clinical evidence service singleton before each test."""
    reset_clinical_evidence_service()
    yield
    reset_clinical_evidence_service()


@pytest.fixture
def service() -> ClinicalEvidenceService:
    """Fresh service instance for each test."""
    return get_clinical_evidence_service()


@pytest.fixture
def org_id():
    """Organization ID for tests."""
    return uuid4()


@pytest.fixture
def device_version_id():
    """Device version ID for tests."""
    return uuid4()


# =============================================================================
# Evidence Hierarchy Tests
# =============================================================================


@pytest.mark.unit
class TestEvidenceHierarchy:
    """Tests for evidence hierarchy scoring constants."""

    def test_rct_has_highest_score(self):
        """RCT should have score of 1.0."""
        assert EVIDENCE_HIERARCHY_SCORE["randomized_controlled_trial"] == 1.0

    def test_prospective_cohort_score(self):
        """Prospective cohort should have score of 0.85."""
        assert EVIDENCE_HIERARCHY_SCORE["prospective_cohort"] == 0.85

    def test_retrospective_cohort_score(self):
        """Retrospective cohort should have score of 0.70."""
        assert EVIDENCE_HIERARCHY_SCORE["retrospective_cohort"] == 0.70

    def test_registry_data_score(self):
        """Registry data should have score of 0.60."""
        assert EVIDENCE_HIERARCHY_SCORE["registry_data"] == 0.60

    def test_case_control_score(self):
        """Case-control should have score of 0.55."""
        assert EVIDENCE_HIERARCHY_SCORE["case_control"] == 0.55

    def test_case_series_score(self):
        """Case series should have score of 0.40."""
        assert EVIDENCE_HIERARCHY_SCORE["case_series"] == 0.40

    def test_case_report_score(self):
        """Case report should have score of 0.25."""
        assert EVIDENCE_HIERARCHY_SCORE["case_report"] == 0.25

    def test_expert_opinion_score(self):
        """Expert opinion should have score of 0.15."""
        assert EVIDENCE_HIERARCHY_SCORE["expert_opinion"] == 0.15

    def test_literature_review_score(self):
        """Literature review should have score of 0.15."""
        assert EVIDENCE_HIERARCHY_SCORE["literature_review"] == 0.15

    def test_all_study_types_have_scores(self):
        """All 9 study types should have defined scores."""
        assert len(EVIDENCE_HIERARCHY_SCORE) == 9


# =============================================================================
# Device Class Thresholds Tests
# =============================================================================


@pytest.mark.unit
class TestClassThresholds:
    """Tests for device class evidence thresholds."""

    def test_class_i_no_requirement(self):
        """Class I devices should have 0.0 threshold."""
        assert CLASS_EVIDENCE_THRESHOLDS["I"] == 0.0

    def test_class_ii_threshold(self):
        """Class II should require at least case series level."""
        assert CLASS_EVIDENCE_THRESHOLDS["II"] == 0.40

    def test_class_iii_threshold(self):
        """Class III should require registry data or better."""
        assert CLASS_EVIDENCE_THRESHOLDS["III"] == 0.60

    def test_class_iv_threshold(self):
        """Class IV should require prospective cohort or better."""
        assert CLASS_EVIDENCE_THRESHOLDS["IV"] == 0.85

    def test_all_classes_have_thresholds(self):
        """All 4 device classes should have thresholds."""
        assert len(CLASS_EVIDENCE_THRESHOLDS) == 4


# =============================================================================
# ClinicalEvidence Model Tests
# =============================================================================


@pytest.mark.unit
class TestClinicalEvidenceModel:
    """Tests for ClinicalEvidence Pydantic model."""

    def test_minimal_evidence_creation(self, org_id, device_version_id):
        """Should create evidence with required fields only."""
        evidence = ClinicalEvidence(
            organization_id=org_id,
            device_version_id=device_version_id,
            study_type="randomized_controlled_trial",
            title="Test RCT Study",
        )
        assert evidence.study_type == "randomized_controlled_trial"
        assert evidence.title == "Test RCT Study"
        assert evidence.id is None  # Not assigned until create()

    def test_evidence_with_all_fields(self, org_id, device_version_id):
        """Should create evidence with all optional fields."""
        evidence = ClinicalEvidence(
            organization_id=org_id,
            device_version_id=device_version_id,
            study_type="prospective_cohort",
            study_id="NCT12345678",
            title="Prospective Study of Device X",
            blinding="double_blind",
            control_type="active",
            randomized=True,
            multi_center=True,
            sample_size=250,
            primary_endpoint="All-cause mortality at 12 months",
            peer_reviewed=True,
        )
        assert evidence.study_id == "NCT12345678"
        assert evidence.blinding == "double_blind"
        assert evidence.sample_size == 250
        assert evidence.peer_reviewed is True

    def test_evidence_default_values(self, org_id, device_version_id):
        """Should have correct default values."""
        evidence = ClinicalEvidence(
            organization_id=org_id,
            device_version_id=device_version_id,
            study_type="case_series",
            title="Test",
        )
        assert evidence.inclusion_criteria == []
        assert evidence.exclusion_criteria == []
        assert evidence.peer_reviewed is False
        assert evidence.multi_center is False
        assert evidence.randomized is False

    def test_evidence_has_citation(self, org_id, device_version_id):
        """Evidence should include GUI-0102 citation."""
        evidence = ClinicalEvidence(
            organization_id=org_id,
            device_version_id=device_version_id,
            study_type="case_report",
            title="Test",
        )
        assert "GUI-0102" in evidence.citation_text


# =============================================================================
# ClinicalEvidenceService Create Tests
# =============================================================================


@pytest.mark.unit
class TestClinicalEvidenceServiceCreate:
    """Tests for ClinicalEvidenceService.create()."""

    def test_create_assigns_id(self, service, org_id, device_version_id):
        """Create should assign UUID if not present."""
        evidence = ClinicalEvidence(
            organization_id=org_id,
            device_version_id=device_version_id,
            study_type="randomized_controlled_trial",
            title="Test RCT",
        )
        created = service.create(evidence)
        assert created.id is not None

    def test_create_calculates_quality_score(self, service, org_id, device_version_id):
        """Create should calculate and assign quality score."""
        evidence = ClinicalEvidence(
            organization_id=org_id,
            device_version_id=device_version_id,
            study_type="randomized_controlled_trial",
            title="Test RCT",
        )
        created = service.create(evidence)
        assert created.quality_score is not None
        assert created.quality_score > 0

    def test_create_sets_timestamps(self, service, org_id, device_version_id):
        """Create should set created_at and updated_at."""
        evidence = ClinicalEvidence(
            organization_id=org_id,
            device_version_id=device_version_id,
            study_type="case_series",
            title="Test",
        )
        created = service.create(evidence)
        assert created.created_at is not None
        assert created.updated_at is not None

    def test_create_stores_evidence(self, service, org_id, device_version_id):
        """Create should store evidence retrievable by get()."""
        evidence = ClinicalEvidence(
            organization_id=org_id,
            device_version_id=device_version_id,
            study_type="prospective_cohort",
            title="Test",
        )
        created = service.create(evidence)
        retrieved = service.get(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id


# =============================================================================
# Quality Score Calculation Tests
# =============================================================================


@pytest.mark.unit
class TestQualityScoreCalculation:
    """Tests for ClinicalEvidenceService.calculate_quality_score()."""

    def test_rct_base_score(self, service, org_id, device_version_id):
        """RCT base score should be 0.50 (1.0 * 0.5 weight)."""
        evidence = ClinicalEvidence(
            organization_id=org_id,
            device_version_id=device_version_id,
            study_type="randomized_controlled_trial",
            title="Test",
        )
        score = service.calculate_quality_score(evidence)
        assert score >= 0.50  # Base score only

    def test_blinding_bonus(self, service, org_id, device_version_id):
        """Double blind should add blinding bonus."""
        evidence_open = ClinicalEvidence(
            organization_id=org_id,
            device_version_id=device_version_id,
            study_type="prospective_cohort",
            title="Test",
            blinding="open",
        )
        evidence_double = ClinicalEvidence(
            organization_id=org_id,
            device_version_id=device_version_id,
            study_type="prospective_cohort",
            title="Test",
            blinding="double_blind",
        )
        score_open = service.calculate_quality_score(evidence_open)
        score_double = service.calculate_quality_score(evidence_double)
        assert score_double > score_open

    def test_sample_size_bonus(self, service, org_id, device_version_id):
        """Larger sample size should increase score."""
        evidence_small = ClinicalEvidence(
            organization_id=org_id,
            device_version_id=device_version_id,
            study_type="prospective_cohort",
            title="Test",
            sample_size=20,
        )
        evidence_large = ClinicalEvidence(
            organization_id=org_id,
            device_version_id=device_version_id,
            study_type="prospective_cohort",
            title="Test",
            sample_size=500,
        )
        score_small = service.calculate_quality_score(evidence_small)
        score_large = service.calculate_quality_score(evidence_large)
        assert score_large > score_small

    def test_peer_review_bonus(self, service, org_id, device_version_id):
        """Peer reviewed should add 0.10 bonus."""
        evidence_not_reviewed = ClinicalEvidence(
            organization_id=org_id,
            device_version_id=device_version_id,
            study_type="retrospective_cohort",
            title="Test",
            peer_reviewed=False,
        )
        evidence_reviewed = ClinicalEvidence(
            organization_id=org_id,
            device_version_id=device_version_id,
            study_type="retrospective_cohort",
            title="Test",
            peer_reviewed=True,
        )
        score_not = service.calculate_quality_score(evidence_not_reviewed)
        score_yes = service.calculate_quality_score(evidence_reviewed)
        assert score_yes - score_not == pytest.approx(0.10, abs=0.01)

    def test_multi_center_bonus(self, service, org_id, device_version_id):
        """Multi-center should add 0.10 bonus."""
        evidence_single = ClinicalEvidence(
            organization_id=org_id,
            device_version_id=device_version_id,
            study_type="prospective_cohort",
            title="Test",
            multi_center=False,
        )
        evidence_multi = ClinicalEvidence(
            organization_id=org_id,
            device_version_id=device_version_id,
            study_type="prospective_cohort",
            title="Test",
            multi_center=True,
        )
        score_single = service.calculate_quality_score(evidence_single)
        score_multi = service.calculate_quality_score(evidence_multi)
        assert score_multi - score_single == pytest.approx(0.10, abs=0.01)

    def test_score_capped_at_one(self, service, org_id, device_version_id):
        """Score should never exceed 1.0."""
        evidence = ClinicalEvidence(
            organization_id=org_id,
            device_version_id=device_version_id,
            study_type="randomized_controlled_trial",
            title="Test",
            blinding="triple_blind",
            sample_size=1000,
            peer_reviewed=True,
            multi_center=True,
        )
        score = service.calculate_quality_score(evidence)
        assert score <= 1.0


# =============================================================================
# Portfolio Tests
# =============================================================================


@pytest.mark.unit
class TestClinicalEvidencePortfolio:
    """Tests for ClinicalEvidenceService.get_portfolio()."""

    def test_empty_portfolio(self, service, device_version_id):
        """Should return empty portfolio when no evidence."""
        portfolio = service.get_portfolio(device_version_id)
        assert portfolio.total_studies == 0
        assert portfolio.evidence_items == []

    def test_portfolio_counts_studies(self, service, org_id, device_version_id):
        """Should count total studies in portfolio."""
        for _ in range(3):
            service.create(
                ClinicalEvidence(
                    organization_id=org_id,
                    device_version_id=device_version_id,
                    study_type="case_series",
                    title="Test",
                )
            )
        portfolio = service.get_portfolio(device_version_id)
        assert portfolio.total_studies == 3

    def test_portfolio_counts_by_type(self, service, org_id, device_version_id):
        """Should count RCTs, observational, and case studies."""
        service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=device_version_id,
                study_type="randomized_controlled_trial",
                title="RCT",
            )
        )
        service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=device_version_id,
                study_type="prospective_cohort",
                title="Cohort",
            )
        )
        service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=device_version_id,
                study_type="case_report",
                title="Case",
            )
        )

        portfolio = service.get_portfolio(device_version_id)
        assert portfolio.rct_count == 1
        assert portfolio.observational_count == 1
        assert portfolio.case_study_count == 1

    def test_portfolio_total_subjects(self, service, org_id, device_version_id):
        """Should sum sample sizes."""
        service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=device_version_id,
                study_type="prospective_cohort",
                title="Study 1",
                sample_size=100,
            )
        )
        service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=device_version_id,
                study_type="retrospective_cohort",
                title="Study 2",
                sample_size=150,
            )
        )

        portfolio = service.get_portfolio(device_version_id)
        assert portfolio.total_subjects == 250

    def test_portfolio_highest_evidence(self, service, org_id, device_version_id):
        """Should identify highest evidence level."""
        service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=device_version_id,
                study_type="case_series",
                title="Case",
            )
        )
        service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=device_version_id,
                study_type="randomized_controlled_trial",
                title="RCT",
            )
        )

        portfolio = service.get_portfolio(device_version_id)
        assert portfolio.highest_evidence_level == "randomized_controlled_trial"

    def test_portfolio_weighted_score(self, service, org_id, device_version_id):
        """Should calculate sample-weighted quality score."""
        service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=device_version_id,
                study_type="randomized_controlled_trial",
                title="RCT",
                sample_size=200,
            )
        )
        portfolio = service.get_portfolio(device_version_id)
        assert portfolio.weighted_quality_score > 0

    def test_portfolio_peer_reviewed_pct(self, service, org_id, device_version_id):
        """Should calculate peer-reviewed percentage."""
        service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=device_version_id,
                study_type="prospective_cohort",
                title="Study 1",
                peer_reviewed=True,
            )
        )
        service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=device_version_id,
                study_type="prospective_cohort",
                title="Study 2",
                peer_reviewed=False,
            )
        )

        portfolio = service.get_portfolio(device_version_id)
        assert portfolio.peer_reviewed_percentage == 50.0


# =============================================================================
# Package Assessment Tests
# =============================================================================


@pytest.mark.unit
class TestClinicalPackageAssessment:
    """Tests for ClinicalEvidenceService.assess_package()."""

    def test_class_i_always_meets_threshold(self, service, org_id, device_version_id):
        """Class I with any evidence should meet threshold."""
        service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=device_version_id,
                study_type="expert_opinion",
                title="Opinion",
            )
        )
        assessment = service.assess_package(device_version_id, "I")
        assert assessment.meets_threshold is True

    def test_class_iv_requires_strong_evidence(self, service, org_id, device_version_id):
        """Class IV with weak evidence should not meet threshold."""
        service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=device_version_id,
                study_type="case_report",
                title="Case",
            )
        )
        assessment = service.assess_package(device_version_id, "IV")
        assert assessment.meets_threshold is False

    def test_assessment_includes_score_gap(self, service, org_id, device_version_id):
        """Assessment should include gap from threshold."""
        service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=device_version_id,
                study_type="prospective_cohort",
                title="Cohort",
                sample_size=100,
            )
        )
        assessment = service.assess_package(device_version_id, "III")
        assert assessment.score_gap is not None

    def test_assessment_provides_recommendations(self, service, org_id, device_version_id):
        """Assessment should provide recommendations when below threshold."""
        service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=device_version_id,
                study_type="case_series",
                title="Case",
            )
        )
        assessment = service.assess_package(device_version_id, "IV")
        assert len(assessment.recommendations) > 0

    def test_assessment_suggests_study_types(self, service, org_id, device_version_id):
        """Assessment should suggest additional study types when needed."""
        service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=device_version_id,
                study_type="case_report",
                title="Case",
            )
        )
        assessment = service.assess_package(device_version_id, "IV")
        assert len(assessment.additional_studies_suggested) > 0

    def test_assessment_identifies_gaps(self, service, org_id, device_version_id):
        """Assessment should identify evidence gaps."""
        service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=device_version_id,
                study_type="case_series",
                title="Case",
                sample_size=10,
            )
        )
        assessment = service.assess_package(device_version_id, "IV")
        assert len(assessment.evidence_gaps) > 0

    def test_assessment_has_citation(self, service, org_id, device_version_id):
        """Assessment should include GUI-0102 citation."""
        assessment = service.assess_package(device_version_id, "II")
        assert "GUI-0102" in assessment.citation_text

    def test_assessment_summary_uses_safe_language(self, service, org_id, device_version_id):
        """Assessment summary should not use 'compliant' or 'approved'."""
        service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=device_version_id,
                study_type="randomized_controlled_trial",
                title="RCT",
                sample_size=200,
            )
        )
        assessment = service.assess_package(device_version_id, "III")
        assert "compliant" not in assessment.assessment_summary.lower()
        assert "approved" not in assessment.assessment_summary.lower()


# =============================================================================
# Service CRUD Tests
# =============================================================================


@pytest.mark.unit
class TestClinicalEvidenceServiceCRUD:
    """Tests for CRUD operations."""

    def test_get_returns_none_for_missing(self, service):
        """Get should return None for non-existent ID."""
        assert service.get(uuid4()) is None

    def test_get_by_device_version(self, service, org_id, device_version_id):
        """Should return only evidence for specified device version."""
        other_dv = uuid4()

        service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=device_version_id,
                study_type="prospective_cohort",
                title="Target Device",
            )
        )
        service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=other_dv,
                study_type="case_series",
                title="Other Device",
            )
        )

        results = service.get_by_device_version(device_version_id)
        assert len(results) == 1
        assert results[0].title == "Target Device"

    def test_delete(self, service, org_id, device_version_id):
        """Delete should remove evidence."""
        evidence = service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=device_version_id,
                study_type="case_report",
                title="Test",
            )
        )
        assert service.delete(evidence.id) is True
        assert service.get(evidence.id) is None

    def test_delete_returns_false_for_missing(self, service):
        """Delete should return False for non-existent ID."""
        assert service.delete(uuid4()) is False

    def test_count(self, service, org_id, device_version_id):
        """Count should return total evidence records."""
        assert service.count() == 0
        service.create(
            ClinicalEvidence(
                organization_id=org_id,
                device_version_id=device_version_id,
                study_type="case_series",
                title="Test",
            )
        )
        assert service.count() == 1

    def test_count_by_organization(self, service, device_version_id):
        """Count should filter by organization."""
        org1 = uuid4()
        org2 = uuid4()

        service.create(
            ClinicalEvidence(
                organization_id=org1,
                device_version_id=device_version_id,
                study_type="case_series",
                title="Org1",
            )
        )
        service.create(
            ClinicalEvidence(
                organization_id=org2,
                device_version_id=device_version_id,
                study_type="case_report",
                title="Org2",
            )
        )

        assert service.count(org1) == 1
        assert service.count(org2) == 1
        assert service.count() == 2


# =============================================================================
# Singleton Tests
# =============================================================================


@pytest.mark.unit
class TestClinicalEvidenceSingleton:
    """Tests for singleton access."""

    def test_get_service_returns_instance(self):
        """get_clinical_evidence_service should return instance."""
        service = get_clinical_evidence_service()
        assert service is not None
        assert isinstance(service, ClinicalEvidenceService)

    def test_get_service_returns_same_instance(self):
        """Subsequent calls should return same instance."""
        s1 = get_clinical_evidence_service()
        s2 = get_clinical_evidence_service()
        assert s1 is s2

    def test_reset_clears_singleton(self):
        """Reset should clear the singleton."""
        s1 = get_clinical_evidence_service()
        reset_clinical_evidence_service()
        s2 = get_clinical_evidence_service()
        assert s1 is not s2
