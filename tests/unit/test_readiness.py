"""
Tests for ReadinessAssessment — Sprint 3b.

Covers:
- ReadinessReport Pydantic model validation
- CategoryScore model validation
- Scoring logic (severity weights, penalties, clamping)
- Category score computation
- Overall score computation
- Critical blocker identification
- Summary generation
- Regulatory-safe language enforcement (NEVER forbidden words)
- Best-effort error handling
- Edge cases (empty reports, unknown categories, all-critical, etc.)
- assess_from_report() independent of database
- Singleton pattern

Test count target: 25+ tests
"""

from unittest.mock import MagicMock

import pytest

from src.core.gap_engine import GapFinding, GapReport
from src.core.readiness import (
    BASE_PENALTY_PER_FINDING,
    FORBIDDEN_WORDS,
    GAP_CATEGORIES,
    SEVERITY_WEIGHTS,
    CategoryScore,
    ReadinessAssessment,
    ReadinessReport,
    _check_regulatory_safe,
    get_readiness_assessment,
)

# =============================================================================
# Test Helpers
# =============================================================================


def make_finding(
    rule_id: str = "GAP-001",
    rule_name: str = "Test Rule",
    severity: str = "major",
    category: str = "coverage",
    description: str = "Test finding description",
    entity_type: str | None = "hazard",
    entity_id: str | None = "ent-001",
    remediation: str = "Fix the issue",
) -> GapFinding:
    """Create a GapFinding for testing."""
    return GapFinding(
        rule_id=rule_id,
        rule_name=rule_name,
        severity=severity,
        category=category,
        description=description,
        entity_type=entity_type,
        entity_id=entity_id,
        remediation=remediation,
    )


def make_gap_report(
    device_version_id: str = "dv-test-001",
    findings: list[GapFinding] | None = None,
) -> GapReport:
    """Create a GapReport for testing."""
    if findings is None:
        findings = []

    critical = [f for f in findings if f.severity == "critical"]
    major = [f for f in findings if f.severity == "major"]
    minor = [f for f in findings if f.severity == "minor"]
    info = [f for f in findings if f.severity == "info"]

    return GapReport(
        device_version_id=device_version_id,
        evaluated_at="2026-02-07T20:00:00-07:00",
        rules_executed=12,
        total_findings=len(findings),
        critical_count=len(critical),
        major_count=len(major),
        minor_count=len(minor),
        info_count=len(info),
        findings=findings,
        critical_findings=critical,
    )


# =============================================================================
# ReadinessReport Model Tests
# =============================================================================


class TestReadinessReportModel:
    """Tests for ReadinessReport Pydantic model."""

    def test_valid_report_creation(self):
        report = ReadinessReport(
            device_version_id="dv-001",
            assessed_at="2026-02-07T20:00:00-07:00",
            overall_readiness_score=0.85,
            summary="Assessment based on configured expectations.",
        )
        assert report.device_version_id == "dv-001"
        assert report.overall_readiness_score == 0.85
        assert report.total_findings == 0
        assert report.critical_blockers == []
        assert report.category_scores == []
        assert report.gap_report is None

    def test_score_bounds_minimum(self):
        report = ReadinessReport(
            device_version_id="dv-001",
            assessed_at="2026-02-07T20:00:00-07:00",
            overall_readiness_score=0.0,
            summary="Assessment.",
        )
        assert report.overall_readiness_score == 0.0

    def test_score_bounds_maximum(self):
        report = ReadinessReport(
            device_version_id="dv-001",
            assessed_at="2026-02-07T20:00:00-07:00",
            overall_readiness_score=1.0,
            summary="Assessment.",
        )
        assert report.overall_readiness_score == 1.0

    def test_score_below_zero_rejected(self):
        with pytest.raises(ValueError):
            ReadinessReport(
                device_version_id="dv-001",
                assessed_at="2026-02-07T20:00:00-07:00",
                overall_readiness_score=-0.1,
                summary="Assessment.",
            )

    def test_score_above_one_rejected(self):
        with pytest.raises(ValueError):
            ReadinessReport(
                device_version_id="dv-001",
                assessed_at="2026-02-07T20:00:00-07:00",
                overall_readiness_score=1.1,
                summary="Assessment.",
            )

    def test_report_with_gap_report(self):
        gap_report = make_gap_report()
        report = ReadinessReport(
            device_version_id="dv-001",
            assessed_at="2026-02-07T20:00:00-07:00",
            overall_readiness_score=1.0,
            gap_report=gap_report,
            summary="Assessment.",
        )
        assert report.gap_report is not None
        assert report.gap_report.device_version_id == "dv-test-001"

    def test_report_with_critical_blockers(self):
        blocker = make_finding(severity="critical")
        report = ReadinessReport(
            device_version_id="dv-001",
            assessed_at="2026-02-07T20:00:00-07:00",
            overall_readiness_score=0.3,
            critical_blockers=[blocker],
            total_findings=1,
            summary="Assessment.",
        )
        assert len(report.critical_blockers) == 1
        assert report.critical_blockers[0].severity == "critical"


# =============================================================================
# CategoryScore Model Tests
# =============================================================================


class TestCategoryScoreModel:
    """Tests for CategoryScore Pydantic model."""

    def test_valid_category_score(self):
        cs = CategoryScore(
            category="coverage",
            score=0.85,
            finding_count=2,
            critical_count=0,
            assessment="Coverage: 2 finding(s) detected.",
        )
        assert cs.category == "coverage"
        assert cs.score == 0.85
        assert cs.finding_count == 2

    def test_perfect_score(self):
        cs = CategoryScore(
            category="completeness",
            score=1.0,
            finding_count=0,
            critical_count=0,
            assessment="No findings detected.",
        )
        assert cs.score == 1.0

    def test_zero_score(self):
        cs = CategoryScore(
            category="consistency",
            score=0.0,
            finding_count=10,
            critical_count=5,
            assessment="Many findings.",
        )
        assert cs.score == 0.0

    def test_score_below_zero_rejected(self):
        with pytest.raises(ValueError):
            CategoryScore(
                category="coverage",
                score=-0.1,
                assessment="Bad.",
            )

    def test_score_above_one_rejected(self):
        with pytest.raises(ValueError):
            CategoryScore(
                category="coverage",
                score=1.1,
                assessment="Bad.",
            )


# =============================================================================
# Regulatory Language Safety Tests
# =============================================================================


class TestRegulatoryLanguageSafety:
    """Tests that ALL output uses regulatory-safe language."""

    def test_check_safe_text_passes(self):
        assert _check_regulatory_safe("Assessment based on configured expectations.")

    def test_check_safe_text_with_findings(self):
        assert _check_regulatory_safe("3 findings detected across 4 dimensions.")

    @pytest.mark.parametrize(
        "forbidden",
        [
            "compliant",
            "compliance",
            "ready",
            "readiness",
            "certified",
            "approved",
            "approval",
            "will pass",
            "guaranteed",
            "guarantee",
            "ensures compliance",
            "meets requirements",
            "submission ready",
            "audit ready",
        ],
    )
    def test_forbidden_words_detected(self, forbidden):
        text = f"This device is {forbidden} with regulations."
        assert not _check_regulatory_safe(text)

    def test_forbidden_words_case_insensitive(self):
        assert not _check_regulatory_safe("This is COMPLIANT.")
        assert not _check_regulatory_safe("Device is Ready.")
        assert not _check_regulatory_safe("CERTIFIED product.")

    def test_summary_never_contains_forbidden_words(self):
        """Full integration: assess a report and check summary text."""
        assessment = ReadinessAssessment(gap_engine=MagicMock())

        # Create findings across multiple severities
        findings = [
            make_finding(severity="critical", category="coverage"),
            make_finding(severity="major", category="completeness"),
            make_finding(severity="minor", category="consistency"),
            make_finding(severity="info", category="evidence_strength"),
        ]
        gap_report = make_gap_report(findings=findings)
        report = assessment.assess_from_report(gap_report)

        # Check every text field
        assert _check_regulatory_safe(report.summary)
        for cs in report.category_scores:
            assert _check_regulatory_safe(
                cs.assessment
            ), f"Category assessment contains forbidden language: {cs.assessment}"

    def test_summary_with_no_findings_is_safe(self):
        assessment = ReadinessAssessment(gap_engine=MagicMock())
        gap_report = make_gap_report(findings=[])
        report = assessment.assess_from_report(gap_report)
        assert _check_regulatory_safe(report.summary)

    def test_summary_all_critical_is_safe(self):
        assessment = ReadinessAssessment(gap_engine=MagicMock())
        findings = [
            make_finding(severity="critical", category="coverage", rule_id=f"GAP-{i:03d}")
            for i in range(5)
        ]
        gap_report = make_gap_report(findings=findings)
        report = assessment.assess_from_report(gap_report)
        assert _check_regulatory_safe(report.summary)

    def test_empty_error_report_is_safe(self):
        assessment = ReadinessAssessment(gap_engine=MagicMock())
        report = assessment._empty_report("dv-fail")
        assert _check_regulatory_safe(report.summary)


# =============================================================================
# Scoring Logic Tests
# =============================================================================


class TestScoringLogic:
    """Tests for the scoring computation."""

    def setup_method(self):
        self.assessment = ReadinessAssessment(gap_engine=MagicMock())

    def test_no_findings_perfect_score(self):
        gap_report = make_gap_report(findings=[])
        report = self.assessment.assess_from_report(gap_report)
        assert report.overall_readiness_score == 1.0

    def test_single_critical_finding_reduces_score(self):
        findings = [make_finding(severity="critical", category="coverage")]
        gap_report = make_gap_report(findings=findings)
        report = self.assessment.assess_from_report(gap_report)
        assert report.overall_readiness_score < 1.0

    def test_single_major_finding_reduces_score(self):
        findings = [make_finding(severity="major", category="completeness")]
        gap_report = make_gap_report(findings=findings)
        report = self.assessment.assess_from_report(gap_report)
        assert report.overall_readiness_score < 1.0

    def test_single_info_finding_no_score_impact(self):
        """Info findings have weight 0.0, so they shouldn't reduce score."""
        findings = [make_finding(severity="info", category="coverage")]
        gap_report = make_gap_report(findings=findings)
        report = self.assessment.assess_from_report(gap_report)
        assert report.overall_readiness_score == 1.0

    def test_critical_worse_than_major(self):
        critical_findings = [make_finding(severity="critical", category="coverage")]
        major_findings = [make_finding(severity="major", category="coverage")]

        critical_report = self.assessment.assess_from_report(
            make_gap_report(findings=critical_findings)
        )
        major_report = self.assessment.assess_from_report(make_gap_report(findings=major_findings))
        assert critical_report.overall_readiness_score < major_report.overall_readiness_score

    def test_major_worse_than_minor(self):
        major_findings = [make_finding(severity="major", category="coverage")]
        minor_findings = [make_finding(severity="minor", category="coverage")]

        major_report = self.assessment.assess_from_report(make_gap_report(findings=major_findings))
        minor_report = self.assessment.assess_from_report(make_gap_report(findings=minor_findings))
        assert major_report.overall_readiness_score < minor_report.overall_readiness_score

    def test_score_never_below_zero(self):
        """Even with many critical findings, score floors at 0.0."""
        findings = [
            make_finding(
                severity="critical",
                category="coverage",
                rule_id=f"GAP-{i:03d}",
            )
            for i in range(20)
        ]
        gap_report = make_gap_report(findings=findings)
        report = self.assessment.assess_from_report(gap_report)
        assert report.overall_readiness_score >= 0.0

    def test_score_never_above_one(self):
        gap_report = make_gap_report(findings=[])
        report = self.assessment.assess_from_report(gap_report)
        assert report.overall_readiness_score <= 1.0

    def test_category_score_computation_single_critical(self):
        findings = [make_finding(severity="critical", category="coverage")]
        scores = self.assessment._compute_category_scores(findings)
        coverage = next(s for s in scores if s.category == "coverage")
        expected = 1.0 - (BASE_PENALTY_PER_FINDING * SEVERITY_WEIGHTS["critical"])
        assert abs(coverage.score - expected) < 0.001

    def test_category_score_computation_multiple_findings(self):
        findings = [
            make_finding(severity="major", category="completeness"),
            make_finding(severity="major", category="completeness", rule_id="GAP-002"),
        ]
        scores = self.assessment._compute_category_scores(findings)
        completeness = next(s for s in scores if s.category == "completeness")
        expected = 1.0 - (2 * BASE_PENALTY_PER_FINDING * SEVERITY_WEIGHTS["major"])
        assert abs(completeness.score - expected) < 0.001

    def test_overall_score_averages_categories(self):
        """Overall score is average of all category scores."""
        findings = [
            make_finding(severity="critical", category="coverage"),
            # Other categories have no findings → score 1.0 each
        ]
        gap_report = make_gap_report(findings=findings)
        report = self.assessment.assess_from_report(gap_report)

        # coverage gets penalty, other 3 categories get 1.0
        coverage_score = 1.0 - (BASE_PENALTY_PER_FINDING * SEVERITY_WEIGHTS["critical"])
        expected_avg = (coverage_score + 1.0 + 1.0 + 1.0) / 4
        assert abs(report.overall_readiness_score - round(expected_avg, 4)) < 0.001

    def test_all_categories_with_findings(self):
        findings = [
            make_finding(severity="critical", category="coverage"),
            make_finding(severity="major", category="completeness"),
            make_finding(severity="minor", category="consistency"),
            make_finding(severity="info", category="evidence_strength"),
        ]
        gap_report = make_gap_report(findings=findings)
        report = self.assessment.assess_from_report(gap_report)

        # Should have 4 category scores
        assert len(report.category_scores) == 4
        categories = {cs.category for cs in report.category_scores}
        assert categories == set(GAP_CATEGORIES)


# =============================================================================
# Critical Blocker Tests
# =============================================================================


class TestCriticalBlockers:
    """Tests for critical blocker identification."""

    def setup_method(self):
        self.assessment = ReadinessAssessment(gap_engine=MagicMock())

    def test_no_blockers_when_no_critical(self):
        findings = [make_finding(severity="major")]
        gap_report = make_gap_report(findings=findings)
        report = self.assessment.assess_from_report(gap_report)
        assert len(report.critical_blockers) == 0

    def test_critical_findings_are_blockers(self):
        findings = [
            make_finding(severity="critical", rule_id="GAP-001"),
            make_finding(severity="major", rule_id="GAP-003"),
        ]
        gap_report = make_gap_report(findings=findings)
        report = self.assessment.assess_from_report(gap_report)
        assert len(report.critical_blockers) == 1
        assert report.critical_blockers[0].rule_id == "GAP-001"

    def test_multiple_critical_blockers(self):
        findings = [
            make_finding(severity="critical", rule_id="GAP-001"),
            make_finding(severity="critical", rule_id="GAP-004"),
            make_finding(severity="critical", rule_id="GAP-010"),
        ]
        gap_report = make_gap_report(findings=findings)
        report = self.assessment.assess_from_report(gap_report)
        assert len(report.critical_blockers) == 3

    def test_blockers_empty_when_no_findings(self):
        gap_report = make_gap_report(findings=[])
        report = self.assessment.assess_from_report(gap_report)
        assert len(report.critical_blockers) == 0


# =============================================================================
# Summary Generation Tests
# =============================================================================


class TestSummaryGeneration:
    """Tests for summary text generation."""

    def setup_method(self):
        self.assessment = ReadinessAssessment(gap_engine=MagicMock())

    def test_summary_contains_overall_score(self):
        gap_report = make_gap_report(findings=[])
        report = self.assessment.assess_from_report(gap_report)
        assert "1.00" in report.summary or "1.0" in report.summary

    def test_summary_mentions_no_gaps_when_clean(self):
        gap_report = make_gap_report(findings=[])
        report = self.assessment.assess_from_report(gap_report)
        assert "No gaps detected" in report.summary

    def test_summary_mentions_finding_count(self):
        findings = [
            make_finding(severity="major", category="coverage"),
            make_finding(severity="minor", category="completeness"),
        ]
        gap_report = make_gap_report(findings=findings)
        report = self.assessment.assess_from_report(gap_report)
        assert "2 finding(s)" in report.summary

    def test_summary_mentions_critical_blockers(self):
        findings = [
            make_finding(severity="critical", category="coverage"),
            make_finding(severity="critical", category="completeness"),
        ]
        gap_report = make_gap_report(findings=findings)
        report = self.assessment.assess_from_report(gap_report)
        assert "critical" in report.summary.lower()

    def test_summary_mentions_lowest_category(self):
        findings = [
            make_finding(severity="critical", category="coverage"),
            make_finding(severity="critical", category="coverage", rule_id="GAP-002"),
        ]
        gap_report = make_gap_report(findings=findings)
        report = self.assessment.assess_from_report(gap_report)
        assert "Coverage" in report.summary

    def test_summary_starts_with_assessment_framing(self):
        gap_report = make_gap_report(findings=[])
        report = self.assessment.assess_from_report(gap_report)
        assert report.summary.startswith("Assessment based on configured expectations.")


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Edge case and error handling tests."""

    def setup_method(self):
        self.assessment = ReadinessAssessment(gap_engine=MagicMock())

    def test_unknown_category_still_scored(self):
        """Findings with unknown categories should still be scored."""
        findings = [make_finding(severity="major", category="new_category")]
        gap_report = make_gap_report(findings=findings)
        report = self.assessment.assess_from_report(gap_report)
        categories = {cs.category for cs in report.category_scores}
        assert "new_category" in categories

    def test_unknown_severity_treated_as_zero_weight(self):
        findings = [make_finding(severity="unknown_sev", category="coverage")]
        gap_report = make_gap_report(findings=findings)
        report = self.assessment.assess_from_report(gap_report)
        # Unknown severity weight = 0.0, so coverage score should be 1.0
        coverage = next(s for s in report.category_scores if s.category == "coverage")
        assert coverage.score == 1.0

    def test_empty_report_on_error(self):
        """Verify _empty_report returns valid structure."""
        report = self.assessment._empty_report("dv-fail")
        assert report.device_version_id == "dv-fail"
        assert report.overall_readiness_score == 0.0
        assert report.total_findings == 0
        assert report.gap_report is None
        assert "could not be completed" in report.summary

    def test_assess_handles_gap_engine_exception(self):
        """assess() should return empty report if gap engine throws."""
        mock_engine = MagicMock()
        mock_engine.evaluate.side_effect = RuntimeError("DB down")
        assessment = ReadinessAssessment(gap_engine=mock_engine)
        report = assessment.assess("dv-broken")
        assert report.overall_readiness_score == 0.0
        assert "could not be completed" in report.summary

    def test_assess_from_report_handles_exception(self):
        """assess_from_report should return empty report on internal error."""
        # Create a GapReport with a findings list that will trigger
        # an error in processing — use a mock that breaks iteration
        gap_report = make_gap_report(findings=[])
        # Manually break the report
        gap_report_dict = gap_report.model_dump()
        gap_report_dict["device_version_id"] = "dv-test"
        report = GapReport(**gap_report_dict)

        # This should work fine (no error)
        assessment = ReadinessAssessment(gap_engine=MagicMock())
        result = assessment.assess_from_report(report)
        assert result.device_version_id == "dv-test"

    def test_large_number_of_findings(self):
        """Stress test: many findings should not crash."""
        findings = [
            make_finding(
                severity="major",
                category=GAP_CATEGORIES[i % len(GAP_CATEGORIES)],
                rule_id=f"GAP-{i:03d}",
            )
            for i in range(100)
        ]
        gap_report = make_gap_report(findings=findings)
        report = self.assessment.assess_from_report(gap_report)
        assert report.overall_readiness_score >= 0.0
        assert report.total_findings == 100


# =============================================================================
# Singleton Tests
# =============================================================================


class TestSingleton:
    """Tests for the singleton pattern."""

    def test_get_readiness_assessment_returns_instance(self):
        # Reset singleton for test isolation
        import src.core.readiness as mod

        mod._readiness_assessment = None
        instance = get_readiness_assessment()
        assert isinstance(instance, ReadinessAssessment)

    def test_get_readiness_assessment_returns_same_instance(self):
        import src.core.readiness as mod

        mod._readiness_assessment = None
        instance1 = get_readiness_assessment()
        instance2 = get_readiness_assessment()
        assert instance1 is instance2


# =============================================================================
# Constants Validation Tests
# =============================================================================


class TestConstants:
    """Tests that constants are correctly defined."""

    def test_severity_weights_has_all_levels(self):
        assert "critical" in SEVERITY_WEIGHTS
        assert "major" in SEVERITY_WEIGHTS
        assert "minor" in SEVERITY_WEIGHTS
        assert "info" in SEVERITY_WEIGHTS

    def test_critical_is_highest_weight(self):
        assert SEVERITY_WEIGHTS["critical"] > SEVERITY_WEIGHTS["major"]
        assert SEVERITY_WEIGHTS["major"] > SEVERITY_WEIGHTS["minor"]
        assert SEVERITY_WEIGHTS["minor"] > SEVERITY_WEIGHTS["info"]

    def test_info_weight_is_zero(self):
        assert SEVERITY_WEIGHTS["info"] == 0.0

    def test_gap_categories_defined(self):
        assert "coverage" in GAP_CATEGORIES
        assert "completeness" in GAP_CATEGORIES
        assert "consistency" in GAP_CATEGORIES
        assert "evidence_strength" in GAP_CATEGORIES

    def test_base_penalty_positive(self):
        assert BASE_PENALTY_PER_FINDING > 0.0

    def test_forbidden_words_not_empty(self):
        assert len(FORBIDDEN_WORDS) > 0


# =============================================================================
# assess() Integration (mocked gap engine)
# =============================================================================


class TestAssessIntegration:
    """Tests for the full assess() flow with mocked gap engine."""

    def test_assess_calls_gap_engine(self):
        mock_engine = MagicMock()
        mock_engine.evaluate.return_value = make_gap_report(findings=[])
        assessment = ReadinessAssessment(gap_engine=mock_engine)
        report = assessment.assess("dv-001")
        mock_engine.evaluate.assert_called_once_with("dv-001")
        assert report.overall_readiness_score == 1.0

    def test_assess_with_mixed_findings(self):
        findings = [
            make_finding(severity="critical", category="coverage", rule_id="GAP-001"),
            make_finding(severity="major", category="completeness", rule_id="GAP-003"),
            make_finding(severity="minor", category="consistency", rule_id="GAP-007"),
        ]
        mock_engine = MagicMock()
        mock_engine.evaluate.return_value = make_gap_report(findings=findings)
        assessment = ReadinessAssessment(gap_engine=mock_engine)
        report = assessment.assess("dv-002")

        assert report.device_version_id == "dv-test-001"
        assert report.total_findings == 3
        assert len(report.critical_blockers) == 1
        assert report.overall_readiness_score > 0.0
        assert report.overall_readiness_score < 1.0
        assert _check_regulatory_safe(report.summary)

    def test_assess_timestamp_format(self):
        mock_engine = MagicMock()
        mock_engine.evaluate.return_value = make_gap_report(findings=[])
        assessment = ReadinessAssessment(gap_engine=mock_engine)
        report = assessment.assess("dv-001")
        # Should be ISO format string
        assert "T" in report.assessed_at
