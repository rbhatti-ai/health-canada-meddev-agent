"""
Tests for Predicate Device Analysis — Sprint 7B

Tests all components:
- PredicateDevice model
- PredicateComparisonMatrix
- SubstantialEquivalenceReport
- PredicateAnalysisService scoring and comparison
"""

from uuid import uuid4

import pytest

from src.core.predicate_analysis import (
    EQUIVALENCE_WEIGHTS,
    PredicateAnalysisService,
    PredicateDevice,
    get_predicate_analysis_service,
    reset_predicate_analysis_service,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def reset_service():
    """Reset the predicate analysis service singleton before each test."""
    reset_predicate_analysis_service()
    yield
    reset_predicate_analysis_service()


@pytest.fixture
def service() -> PredicateAnalysisService:
    """Fresh service instance for each test."""
    return get_predicate_analysis_service()


@pytest.fixture
def org_id():
    """Organization ID for tests."""
    return uuid4()


@pytest.fixture
def device_version_id():
    """Device version ID for tests."""
    return uuid4()


# =============================================================================
# Weight Constants Tests
# =============================================================================


@pytest.mark.unit
class TestEquivalenceWeights:
    """Tests for equivalence weight constants."""

    def test_intended_use_weight(self):
        """Intended use should have 35% weight."""
        assert EQUIVALENCE_WEIGHTS["intended_use"] == 0.35

    def test_technological_weight(self):
        """Technological should have 35% weight."""
        assert EQUIVALENCE_WEIGHTS["technological"] == 0.35

    def test_performance_weight(self):
        """Performance should have 30% weight."""
        assert EQUIVALENCE_WEIGHTS["performance"] == 0.30

    def test_weights_sum_to_one(self):
        """All weights should sum to 1.0."""
        total = sum(EQUIVALENCE_WEIGHTS.values())
        assert total == pytest.approx(1.0)


# =============================================================================
# PredicateDevice Model Tests
# =============================================================================


@pytest.mark.unit
class TestPredicateDeviceModel:
    """Tests for PredicateDevice Pydantic model."""

    def test_minimal_predicate_creation(self, org_id, device_version_id):
        """Should create predicate with required fields only."""
        predicate = PredicateDevice(
            organization_id=org_id,
            device_version_id=device_version_id,
            predicate_name="Existing Device",
            predicate_manufacturer="Acme Medical",
            predicate_device_class="II",
            intended_use_comparison="Both devices for cardiac monitoring",
            technological_characteristics="Both use ECG sensors",
            performance_comparison="Similar accuracy specifications",
        )
        assert predicate.predicate_name == "Existing Device"
        assert predicate.id is None  # Not assigned until create()

    def test_predicate_with_equivalence_flags(self, org_id, device_version_id):
        """Should create predicate with equivalence assessments."""
        predicate = PredicateDevice(
            organization_id=org_id,
            device_version_id=device_version_id,
            predicate_name="Predicate A",
            predicate_manufacturer="Manufacturer A",
            predicate_device_class="II",
            intended_use_comparison="Same intended use",
            intended_use_equivalent=True,
            technological_characteristics="Same technology",
            technological_equivalent=True,
            performance_comparison="Same performance",
            performance_equivalent=True,
        )
        assert predicate.intended_use_equivalent is True
        assert predicate.technological_equivalent is True
        assert predicate.performance_equivalent is True

    def test_predicate_with_differences(self, org_id, device_version_id):
        """Should capture differences and mitigations."""
        predicate = PredicateDevice(
            organization_id=org_id,
            device_version_id=device_version_id,
            predicate_name="Predicate B",
            predicate_manufacturer="Manufacturer B",
            predicate_device_class="III",
            intended_use_comparison="Similar use",
            intended_use_equivalent=False,
            intended_use_differences=["Subject includes pediatric use"],
            technological_characteristics="Different materials",
            technological_equivalent=False,
            technological_differences=["Titanium vs stainless steel"],
            technological_mitigations=["Biocompatibility testing completed"],
            performance_comparison="Equivalent performance",
            performance_equivalent=True,
        )
        assert len(predicate.intended_use_differences) == 1
        assert len(predicate.technological_differences) == 1
        assert len(predicate.technological_mitigations) == 1

    def test_predicate_default_values(self, org_id, device_version_id):
        """Should have correct default values."""
        predicate = PredicateDevice(
            organization_id=org_id,
            device_version_id=device_version_id,
            predicate_name="Test",
            predicate_manufacturer="Test",
            predicate_device_class="II",
            intended_use_comparison="Test",
            technological_characteristics="Test",
            performance_comparison="Test",
        )
        assert predicate.intended_use_equivalent is False
        assert predicate.technological_equivalent is False
        assert predicate.performance_equivalent is False
        assert predicate.equivalence_conclusion == "requires_additional_analysis"

    def test_predicate_has_citation(self, org_id, device_version_id):
        """Predicate should include SOR/98-282 citation."""
        predicate = PredicateDevice(
            organization_id=org_id,
            device_version_id=device_version_id,
            predicate_name="Test",
            predicate_manufacturer="Test",
            predicate_device_class="II",
            intended_use_comparison="Test",
            technological_characteristics="Test",
            performance_comparison="Test",
        )
        assert "SOR/98-282" in predicate.citation_text


# =============================================================================
# PredicateAnalysisService Create Tests
# =============================================================================


@pytest.mark.unit
class TestPredicateAnalysisServiceCreate:
    """Tests for PredicateAnalysisService.create()."""

    def test_create_assigns_id(self, service, org_id, device_version_id):
        """Create should assign UUID if not present."""
        predicate = PredicateDevice(
            organization_id=org_id,
            device_version_id=device_version_id,
            predicate_name="Test Predicate",
            predicate_manufacturer="Test Mfg",
            predicate_device_class="II",
            intended_use_comparison="Same",
            technological_characteristics="Same",
            performance_comparison="Same",
        )
        created = service.create(predicate)
        assert created.id is not None

    def test_create_calculates_score(self, service, org_id, device_version_id):
        """Create should calculate equivalence score."""
        predicate = PredicateDevice(
            organization_id=org_id,
            device_version_id=device_version_id,
            predicate_name="Test",
            predicate_manufacturer="Test",
            predicate_device_class="II",
            intended_use_comparison="Same",
            intended_use_equivalent=True,
            technological_characteristics="Same",
            technological_equivalent=True,
            performance_comparison="Same",
            performance_equivalent=True,
        )
        created = service.create(predicate)
        assert created.equivalence_score == 1.0

    def test_create_determines_conclusion(self, service, org_id, device_version_id):
        """Create should determine equivalence conclusion."""
        predicate = PredicateDevice(
            organization_id=org_id,
            device_version_id=device_version_id,
            predicate_name="Test",
            predicate_manufacturer="Test",
            predicate_device_class="II",
            intended_use_comparison="Same",
            intended_use_equivalent=True,
            technological_characteristics="Same",
            technological_equivalent=True,
            performance_comparison="Same",
            performance_equivalent=True,
        )
        created = service.create(predicate)
        assert created.equivalence_conclusion == "substantially_equivalent"

    def test_create_sets_timestamps(self, service, org_id, device_version_id):
        """Create should set timestamps."""
        predicate = PredicateDevice(
            organization_id=org_id,
            device_version_id=device_version_id,
            predicate_name="Test",
            predicate_manufacturer="Test",
            predicate_device_class="II",
            intended_use_comparison="Test",
            technological_characteristics="Test",
            performance_comparison="Test",
        )
        created = service.create(predicate)
        assert created.created_at is not None
        assert created.updated_at is not None


# =============================================================================
# Equivalence Score Calculation Tests
# =============================================================================


@pytest.mark.unit
class TestEquivalenceScoreCalculation:
    """Tests for equivalence score calculation."""

    def test_perfect_equivalence_score(self, service, org_id, device_version_id):
        """All equivalent should score 1.0."""
        predicate = PredicateDevice(
            organization_id=org_id,
            device_version_id=device_version_id,
            predicate_name="Test",
            predicate_manufacturer="Test",
            predicate_device_class="II",
            intended_use_comparison="Same",
            intended_use_equivalent=True,
            technological_characteristics="Same",
            technological_equivalent=True,
            performance_comparison="Same",
            performance_equivalent=True,
        )
        score = service.calculate_equivalence_score(predicate)
        assert score == 1.0

    def test_no_equivalence_low_score(self, service, org_id, device_version_id):
        """None equivalent should score low."""
        predicate = PredicateDevice(
            organization_id=org_id,
            device_version_id=device_version_id,
            predicate_name="Test",
            predicate_manufacturer="Test",
            predicate_device_class="II",
            intended_use_comparison="Different",
            intended_use_equivalent=False,
            technological_characteristics="Different",
            technological_equivalent=False,
            performance_comparison="Different",
            performance_equivalent=False,
        )
        score = service.calculate_equivalence_score(predicate)
        assert score < 0.3

    def test_mitigations_improve_score(self, service, org_id, device_version_id):
        """Mitigations should improve score over unaddressed differences."""
        predicate_unaddressed = PredicateDevice(
            organization_id=org_id,
            device_version_id=device_version_id,
            predicate_name="Test",
            predicate_manufacturer="Test",
            predicate_device_class="II",
            intended_use_comparison="Same",
            intended_use_equivalent=True,
            technological_characteristics="Different",
            technological_equivalent=False,
            technological_differences=["Material difference"],
            performance_comparison="Same",
            performance_equivalent=True,
        )
        predicate_addressed = PredicateDevice(
            organization_id=org_id,
            device_version_id=device_version_id,
            predicate_name="Test",
            predicate_manufacturer="Test",
            predicate_device_class="II",
            intended_use_comparison="Same",
            intended_use_equivalent=True,
            technological_characteristics="Different",
            technological_equivalent=False,
            technological_differences=["Material difference"],
            technological_mitigations=["Biocompatibility data provided"],
            performance_comparison="Same",
            performance_equivalent=True,
        )
        score_unaddressed = service.calculate_equivalence_score(predicate_unaddressed)
        score_addressed = service.calculate_equivalence_score(predicate_addressed)
        assert score_addressed > score_unaddressed

    def test_performance_data_improves_score(self, service, org_id, device_version_id):
        """Performance data sources should improve score."""
        predicate_no_data = PredicateDevice(
            organization_id=org_id,
            device_version_id=device_version_id,
            predicate_name="Test",
            predicate_manufacturer="Test",
            predicate_device_class="II",
            intended_use_comparison="Same",
            intended_use_equivalent=True,
            technological_characteristics="Same",
            technological_equivalent=True,
            performance_comparison="Different",
            performance_equivalent=False,
        )
        predicate_with_data = PredicateDevice(
            organization_id=org_id,
            device_version_id=device_version_id,
            predicate_name="Test",
            predicate_manufacturer="Test",
            predicate_device_class="II",
            intended_use_comparison="Same",
            intended_use_equivalent=True,
            technological_characteristics="Same",
            technological_equivalent=True,
            performance_comparison="Different",
            performance_equivalent=False,
            performance_data_sources=["Bench testing", "Clinical study"],
        )
        score_no_data = service.calculate_equivalence_score(predicate_no_data)
        score_with_data = service.calculate_equivalence_score(predicate_with_data)
        assert score_with_data > score_no_data


# =============================================================================
# Conclusion Determination Tests
# =============================================================================


@pytest.mark.unit
class TestConclusionDetermination:
    """Tests for equivalence conclusion determination."""

    def test_fully_equivalent_conclusion(self, service, org_id, device_version_id):
        """All equivalent should conclude substantially_equivalent."""
        predicate = PredicateDevice(
            organization_id=org_id,
            device_version_id=device_version_id,
            predicate_name="Test",
            predicate_manufacturer="Test",
            predicate_device_class="II",
            intended_use_comparison="Same",
            intended_use_equivalent=True,
            technological_characteristics="Same",
            technological_equivalent=True,
            performance_comparison="Same",
            performance_equivalent=True,
        )
        created = service.create(predicate)
        assert created.equivalence_conclusion == "substantially_equivalent"

    def test_not_equivalent_conclusion(self, service, org_id, device_version_id):
        """Low score should conclude not_equivalent."""
        predicate = PredicateDevice(
            organization_id=org_id,
            device_version_id=device_version_id,
            predicate_name="Test",
            predicate_manufacturer="Test",
            predicate_device_class="II",
            intended_use_comparison="Different",
            intended_use_equivalent=False,
            technological_characteristics="Different",
            technological_equivalent=False,
            performance_comparison="Different",
            performance_equivalent=False,
        )
        created = service.create(predicate)
        assert created.equivalence_conclusion == "not_equivalent"

    def test_with_data_conclusion(self, service, org_id, device_version_id):
        """Moderate score should conclude with_data."""
        predicate = PredicateDevice(
            organization_id=org_id,
            device_version_id=device_version_id,
            predicate_name="Test",
            predicate_manufacturer="Test",
            predicate_device_class="II",
            intended_use_comparison="Same",
            intended_use_equivalent=True,
            technological_characteristics="Different",
            technological_equivalent=False,
            technological_differences=["Minor difference"],
            technological_mitigations=["Addressed with testing"],
            performance_comparison="Same",
            performance_equivalent=True,
        )
        created = service.create(predicate)
        assert created.equivalence_conclusion in (
            "substantially_equivalent_with_data",
            "requires_additional_analysis",
        )


# =============================================================================
# Comparison Matrix Tests
# =============================================================================


@pytest.mark.unit
class TestComparisonMatrix:
    """Tests for comparison matrix generation."""

    def test_matrix_returns_none_for_missing(self, service, device_version_id):
        """Should return None for non-existent predicate."""
        matrix = service.generate_comparison_matrix(device_version_id, uuid4())
        assert matrix is None

    def test_matrix_has_assessments(self, service, org_id, device_version_id):
        """Matrix should have all three dimension assessments."""
        predicate = service.create(
            PredicateDevice(
                organization_id=org_id,
                device_version_id=device_version_id,
                predicate_name="Test",
                predicate_manufacturer="Test",
                predicate_device_class="II",
                intended_use_comparison="Same",
                intended_use_equivalent=True,
                technological_characteristics="Same",
                technological_equivalent=True,
                performance_comparison="Same",
                performance_equivalent=True,
            )
        )
        matrix = service.generate_comparison_matrix(device_version_id, predicate.id)
        assert matrix is not None
        assert matrix.intended_use_assessment == "equivalent"
        assert matrix.technological_assessment == "equivalent"
        assert matrix.performance_assessment == "equivalent"

    def test_matrix_has_dimension_scores(self, service, org_id, device_version_id):
        """Matrix should include dimension scores."""
        predicate = service.create(
            PredicateDevice(
                organization_id=org_id,
                device_version_id=device_version_id,
                predicate_name="Test",
                predicate_manufacturer="Test",
                predicate_device_class="II",
                intended_use_comparison="Same",
                intended_use_equivalent=True,
                technological_characteristics="Same",
                technological_equivalent=True,
                performance_comparison="Same",
                performance_equivalent=True,
            )
        )
        matrix = service.generate_comparison_matrix(device_version_id, predicate.id)
        assert "intended_use" in matrix.dimension_scores
        assert "technological" in matrix.dimension_scores
        assert "performance" in matrix.dimension_scores

    def test_matrix_identifies_unaddressed(self, service, org_id, device_version_id):
        """Matrix should identify unaddressed differences."""
        predicate = service.create(
            PredicateDevice(
                organization_id=org_id,
                device_version_id=device_version_id,
                predicate_name="Test",
                predicate_manufacturer="Test",
                predicate_device_class="II",
                intended_use_comparison="Same",
                intended_use_equivalent=True,
                technological_characteristics="Different",
                technological_equivalent=False,
                technological_differences=["Unaddressed difference"],
                performance_comparison="Same",
                performance_equivalent=True,
            )
        )
        matrix = service.generate_comparison_matrix(device_version_id, predicate.id)
        assert len(matrix.unaddressed_differences) > 0

    def test_matrix_provides_recommendations(self, service, org_id, device_version_id):
        """Matrix should provide recommendations for gaps."""
        predicate = service.create(
            PredicateDevice(
                organization_id=org_id,
                device_version_id=device_version_id,
                predicate_name="Test",
                predicate_manufacturer="Test",
                predicate_device_class="II",
                intended_use_comparison="Same",
                intended_use_equivalent=True,
                technological_characteristics="Different",
                technological_equivalent=False,
                technological_differences=["Gap"],
                performance_comparison="Same",
                performance_equivalent=True,
            )
        )
        matrix = service.generate_comparison_matrix(device_version_id, predicate.id)
        assert len(matrix.recommended_actions) > 0

    def test_matrix_has_citation(self, service, org_id, device_version_id):
        """Matrix should include citation."""
        predicate = service.create(
            PredicateDevice(
                organization_id=org_id,
                device_version_id=device_version_id,
                predicate_name="Test",
                predicate_manufacturer="Test",
                predicate_device_class="II",
                intended_use_comparison="Test",
                technological_characteristics="Test",
                performance_comparison="Test",
            )
        )
        matrix = service.generate_comparison_matrix(device_version_id, predicate.id)
        assert "SOR/98-282" in matrix.citation_text


# =============================================================================
# SE Report Tests
# =============================================================================


@pytest.mark.unit
class TestSEReport:
    """Tests for substantial equivalence report generation."""

    def test_empty_report_for_no_predicates(self, service, org_id, device_version_id):
        """Should return report indicating no predicates analyzed."""
        report = service.generate_se_report(device_version_id, org_id)
        assert report.predicate_count == 0
        assert report.se_demonstration_possible is False

    def test_report_identifies_best_predicate(self, service, org_id, device_version_id):
        """Should identify best predicate match."""
        # Create weak predicate
        service.create(
            PredicateDevice(
                organization_id=org_id,
                device_version_id=device_version_id,
                predicate_name="Weak Predicate",
                predicate_manufacturer="Test",
                predicate_device_class="II",
                intended_use_comparison="Different",
                technological_characteristics="Different",
                performance_comparison="Different",
            )
        )
        # Create strong predicate
        strong = service.create(
            PredicateDevice(
                organization_id=org_id,
                device_version_id=device_version_id,
                predicate_name="Strong Predicate",
                predicate_manufacturer="Test",
                predicate_device_class="II",
                intended_use_comparison="Same",
                intended_use_equivalent=True,
                technological_characteristics="Same",
                technological_equivalent=True,
                performance_comparison="Same",
                performance_equivalent=True,
            )
        )

        report = service.generate_se_report(device_version_id, org_id)
        assert report.recommended_predicate_id == strong.id
        assert report.recommended_predicate_name == "Strong Predicate"

    def test_report_indicates_se_possible(self, service, org_id, device_version_id):
        """Should indicate SE is possible with good predicate."""
        service.create(
            PredicateDevice(
                organization_id=org_id,
                device_version_id=device_version_id,
                predicate_name="Good Predicate",
                predicate_manufacturer="Test",
                predicate_device_class="II",
                intended_use_comparison="Same",
                intended_use_equivalent=True,
                technological_characteristics="Same",
                technological_equivalent=True,
                performance_comparison="Same",
                performance_equivalent=True,
            )
        )

        report = service.generate_se_report(device_version_id, org_id)
        assert report.se_demonstration_possible is True

    def test_report_collects_data_gaps(self, service, org_id, device_version_id):
        """Should collect all data gaps from predicates."""
        service.create(
            PredicateDevice(
                organization_id=org_id,
                device_version_id=device_version_id,
                predicate_name="Predicate",
                predicate_manufacturer="Test",
                predicate_device_class="II",
                intended_use_comparison="Same",
                intended_use_equivalent=True,
                technological_characteristics="Different",
                technological_equivalent=False,
                technological_differences=["Difference"],
                additional_data_required=["Biocompatibility data", "Bench testing"],
                performance_comparison="Same",
                performance_equivalent=True,
            )
        )

        report = service.generate_se_report(device_version_id, org_id)
        assert len(report.data_gaps) > 0

    def test_report_uses_safe_language(self, service, org_id, device_version_id):
        """Report should not use 'approved' or 'compliant'."""
        service.create(
            PredicateDevice(
                organization_id=org_id,
                device_version_id=device_version_id,
                predicate_name="Predicate",
                predicate_manufacturer="Test",
                predicate_device_class="II",
                intended_use_comparison="Same",
                intended_use_equivalent=True,
                technological_characteristics="Same",
                technological_equivalent=True,
                performance_comparison="Same",
                performance_equivalent=True,
            )
        )

        report = service.generate_se_report(device_version_id, org_id)
        assert "approved" not in report.assessment_summary.lower()
        assert "compliant" not in report.assessment_summary.lower()


# =============================================================================
# Service CRUD Tests
# =============================================================================


@pytest.mark.unit
class TestPredicateServiceCRUD:
    """Tests for CRUD operations."""

    def test_get_returns_none_for_missing(self, service):
        """Get should return None for non-existent ID."""
        assert service.get(uuid4()) is None

    def test_get_by_device_version(self, service, org_id, device_version_id):
        """Should return only predicates for specified device."""
        other_dv = uuid4()

        service.create(
            PredicateDevice(
                organization_id=org_id,
                device_version_id=device_version_id,
                predicate_name="Target",
                predicate_manufacturer="Test",
                predicate_device_class="II",
                intended_use_comparison="Test",
                technological_characteristics="Test",
                performance_comparison="Test",
            )
        )
        service.create(
            PredicateDevice(
                organization_id=org_id,
                device_version_id=other_dv,
                predicate_name="Other",
                predicate_manufacturer="Test",
                predicate_device_class="II",
                intended_use_comparison="Test",
                technological_characteristics="Test",
                performance_comparison="Test",
            )
        )

        results = service.get_by_device_version(device_version_id)
        assert len(results) == 1
        assert results[0].predicate_name == "Target"

    def test_delete(self, service, org_id, device_version_id):
        """Delete should remove predicate."""
        predicate = service.create(
            PredicateDevice(
                organization_id=org_id,
                device_version_id=device_version_id,
                predicate_name="Test",
                predicate_manufacturer="Test",
                predicate_device_class="II",
                intended_use_comparison="Test",
                technological_characteristics="Test",
                performance_comparison="Test",
            )
        )
        assert service.delete(predicate.id) is True
        assert service.get(predicate.id) is None

    def test_count(self, service, org_id, device_version_id):
        """Count should return total predicates."""
        assert service.count() == 0
        service.create(
            PredicateDevice(
                organization_id=org_id,
                device_version_id=device_version_id,
                predicate_name="Test",
                predicate_manufacturer="Test",
                predicate_device_class="II",
                intended_use_comparison="Test",
                technological_characteristics="Test",
                performance_comparison="Test",
            )
        )
        assert service.count() == 1


# =============================================================================
# Singleton Tests
# =============================================================================


@pytest.mark.unit
class TestPredicateSingleton:
    """Tests for singleton access."""

    def test_get_service_returns_instance(self):
        """get_predicate_analysis_service should return instance."""
        service = get_predicate_analysis_service()
        assert service is not None
        assert isinstance(service, PredicateAnalysisService)

    def test_get_service_returns_same_instance(self):
        """Subsequent calls should return same instance."""
        s1 = get_predicate_analysis_service()
        s2 = get_predicate_analysis_service()
        assert s1 is s2

    def test_reset_clears_singleton(self):
        """Reset should clear the singleton."""
        s1 = get_predicate_analysis_service()
        reset_predicate_analysis_service()
        s2 = get_predicate_analysis_service()
        assert s1 is not s2
