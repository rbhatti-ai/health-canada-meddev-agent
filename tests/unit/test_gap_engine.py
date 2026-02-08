"""
Unit tests for the Gap Detection Engine.

Sprint 3a — Tests for GapDetectionEngine, all 12 gap rules,
Pydantic models, and regulatory language safety.

Tests use mock dependencies (no DB required).

MOCK PATTERNS:
    - TwinRepository: generic methods (get_by_device_version, get_by_id,
      get_by_field). Mocked with return_value for simple cases.
    - TraceabilityEngine: get_links_from returns TraceLink-like objects.
      We use SimpleNamespace to provide attribute access matching
      Pydantic TraceLink (link.target_type, not link["target_type"]).
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.core.gap_engine import (
    GapDetectionEngine,
    GapFinding,
    GapReport,
    GapRuleDefinition,
    get_gap_engine,
)

# =============================================================================
# Helpers
# =============================================================================


def make_link(**kwargs):
    """Create a mock TraceLink-like object with attribute access.

    Usage:
        make_link(target_type="risk_control", target_id="rc1",
                  relationship="mitigated_by")
    """
    return SimpleNamespace(**kwargs)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_traceability():
    """Mock TraceabilityEngine with no links by default."""
    engine = MagicMock()
    engine.get_links_from.return_value = []
    engine.get_links_to.return_value = []
    return engine


@pytest.fixture
def mock_repository():
    """Mock TwinRepository with empty results by default.

    Uses generic API matching TwinRepository:
        get_by_device_version(table, dvid) -> list[dict]
        get_by_id(table, id) -> dict | None
        get_by_field(table, field, value) -> list[dict]
    """
    repo = MagicMock()
    repo.get_by_device_version.return_value = []
    repo.get_by_id.return_value = None
    repo.get_by_field.return_value = []
    return repo


@pytest.fixture
def gap_engine(mock_traceability, mock_repository):
    """GapDetectionEngine with mocked dependencies."""
    return GapDetectionEngine(
        traceability_engine=mock_traceability,
        twin_repository=mock_repository,
    )


DEVICE_VERSION_ID = "test-device-version-001"


# =============================================================================
# Pydantic Model Tests
# =============================================================================


@pytest.mark.unit
class TestGapFindingModel:
    """Tests for GapFinding Pydantic model."""

    def test_valid_gap_finding(self):
        """GapFinding with all required fields should be valid."""
        finding = GapFinding(
            rule_id="GAP-001",
            rule_name="Test Rule",
            severity="critical",
            category="coverage",
            description="Test description",
            remediation="Test remediation",
        )
        assert finding.rule_id == "GAP-001"
        assert finding.severity == "critical"

    def test_gap_finding_with_optional_fields(self):
        """GapFinding should accept optional entity fields."""
        finding = GapFinding(
            rule_id="GAP-001",
            rule_name="Test Rule",
            severity="major",
            category="completeness",
            description="Test",
            remediation="Test",
            entity_type="hazard",
            entity_id="hazard-123",
            details={"key": "value"},
        )
        assert finding.entity_type == "hazard"
        assert finding.entity_id == "hazard-123"
        assert finding.details == {"key": "value"}

    def test_gap_finding_severity_values(self):
        """GapFinding should accept all valid severity levels."""
        for severity in ("critical", "major", "minor", "info"):
            finding = GapFinding(
                rule_id="GAP-001",
                rule_name="Test",
                severity=severity,
                category="coverage",
                description="Test",
                remediation="Test",
            )
            assert finding.severity == severity

    def test_gap_finding_category_values(self):
        """GapFinding should accept all valid category values."""
        for category in (
            "coverage",
            "completeness",
            "consistency",
            "evidence_strength",
        ):
            finding = GapFinding(
                rule_id="GAP-001",
                rule_name="Test",
                severity="minor",
                category=category,
                description="Test",
                remediation="Test",
            )
            assert finding.category == category


@pytest.mark.unit
class TestGapRuleDefinitionModel:
    """Tests for GapRuleDefinition Pydantic model."""

    def test_valid_rule_definition(self):
        """GapRuleDefinition with required fields should be valid."""
        rule = GapRuleDefinition(
            id="GAP-TEST",
            name="Test Rule",
            description="Test",
            severity="critical",
            category="coverage",
        )
        assert rule.id == "GAP-TEST"
        assert rule.version == 1
        assert rule.enabled is True

    def test_rule_definition_defaults(self):
        """GapRuleDefinition should have correct default values."""
        rule = GapRuleDefinition(
            id="GAP-TEST",
            name="Test",
            description="Test",
            severity="minor",
            category="completeness",
        )
        assert rule.version == 1
        assert rule.enabled is True

    def test_rule_definition_disabled(self):
        """GapRuleDefinition can be disabled."""
        rule = GapRuleDefinition(
            id="GAP-TEST",
            name="Test",
            description="Test",
            severity="minor",
            category="completeness",
            enabled=False,
        )
        assert rule.enabled is False


@pytest.mark.unit
class TestGapReportModel:
    """Tests for GapReport Pydantic model."""

    def test_valid_gap_report(self):
        """GapReport with required fields should be valid."""
        report = GapReport(
            device_version_id="test-123",
            evaluated_at="2026-02-07T20:00:00+00:00",
            rules_executed=12,
            total_findings=3,
            critical_count=1,
            major_count=2,
        )
        assert report.rules_executed == 12
        assert report.total_findings == 3

    def test_gap_report_defaults(self):
        """GapReport should have correct default values."""
        report = GapReport(
            device_version_id="test-123",
            evaluated_at="2026-02-07T20:00:00+00:00",
            rules_executed=0,
            total_findings=0,
        )
        assert report.findings == []
        assert report.critical_findings == []
        assert report.critical_count == 0
        assert report.major_count == 0
        assert report.minor_count == 0
        assert report.info_count == 0


# =============================================================================
# Engine Mechanics Tests
# =============================================================================


@pytest.mark.unit
class TestGapEngineInitialization:
    """Tests for GapDetectionEngine initialization."""

    def test_engine_creates_with_dependencies(self, mock_traceability, mock_repository):
        """Engine should initialize with provided dependencies."""
        engine = GapDetectionEngine(
            traceability_engine=mock_traceability,
            twin_repository=mock_repository,
        )
        assert engine is not None

    def test_engine_has_12_rules(self, gap_engine):
        """Engine should have exactly 12 rule definitions."""
        rules = gap_engine.get_rules()
        assert len(rules) == 12

    def test_engine_has_12_evaluators(self, gap_engine):
        """Engine should have an evaluator for each rule."""
        assert len(gap_engine._rule_evaluators) == 12

    def test_all_rules_have_evaluators(self, gap_engine):
        """Every defined rule should have a matching evaluator."""
        for rule_id in gap_engine.RULE_DEFINITIONS:
            assert rule_id in gap_engine._rule_evaluators, f"Rule {rule_id} has no evaluator"

    def test_all_evaluators_have_rules(self, gap_engine):
        """Every evaluator should have a matching rule definition."""
        for rule_id in gap_engine._rule_evaluators:
            assert (
                rule_id in gap_engine.RULE_DEFINITIONS
            ), f"Evaluator {rule_id} has no rule definition"

    def test_rule_ids_are_sequential(self, gap_engine):
        """Rule IDs should follow GAP-NNN pattern."""
        for rule_id in gap_engine.RULE_DEFINITIONS:
            assert rule_id.startswith("GAP-"), f"Rule {rule_id} doesn't follow GAP-NNN pattern"
            num = int(rule_id.split("-")[1])
            assert 1 <= num <= 12


@pytest.mark.unit
class TestGapEngineEvaluate:
    """Tests for GapDetectionEngine.evaluate() method."""

    def test_evaluate_returns_gap_report(self, gap_engine):
        """evaluate() should return a GapReport."""
        report = gap_engine.evaluate(DEVICE_VERSION_ID)
        assert isinstance(report, GapReport)

    def test_evaluate_sets_device_version_id(self, gap_engine):
        """Report should contain the evaluated device version ID."""
        report = gap_engine.evaluate(DEVICE_VERSION_ID)
        assert report.device_version_id == DEVICE_VERSION_ID

    def test_evaluate_sets_timestamp(self, gap_engine):
        """Report should have an evaluation timestamp."""
        report = gap_engine.evaluate(DEVICE_VERSION_ID)
        assert report.evaluated_at is not None
        assert len(report.evaluated_at) > 0

    def test_evaluate_counts_rules_executed(self, gap_engine):
        """Report should count how many rules were executed."""
        report = gap_engine.evaluate(DEVICE_VERSION_ID)
        assert report.rules_executed == 12

    def test_evaluate_empty_device_has_completeness_gaps(self, gap_engine, mock_repository):
        """Empty device should trigger completeness rules (004, 007, 009)."""
        report = gap_engine.evaluate(DEVICE_VERSION_ID)
        rule_ids = {f.rule_id for f in report.findings}
        assert "GAP-004" in rule_ids  # Missing intended use
        assert "GAP-007" in rule_ids  # No submission target
        assert "GAP-009" in rule_ids  # Missing labeling

    def test_evaluate_counts_match_findings(self, gap_engine):
        """Finding counts should match the actual findings list."""
        report = gap_engine.evaluate(DEVICE_VERSION_ID)
        assert report.total_findings == len(report.findings)
        assert report.critical_count == len(report.critical_findings)

    def test_evaluate_continues_on_rule_failure(self, gap_engine, mock_repository):
        """Engine should continue evaluating if one rule throws."""
        mock_repository.get_by_device_version.side_effect = Exception("DB error")
        # Should not raise — best-effort pattern
        report = gap_engine.evaluate(DEVICE_VERSION_ID)
        assert report.rules_executed == 12

    def test_evaluate_skips_disabled_rules(self, mock_traceability, mock_repository):
        """Disabled rules should not be executed."""
        engine = GapDetectionEngine(
            traceability_engine=mock_traceability,
            twin_repository=mock_repository,
        )
        # Disable GAP-004
        engine.RULE_DEFINITIONS["GAP-004"] = GapRuleDefinition(
            id="GAP-004",
            name="Missing intended use",
            description="Disabled for test",
            severity="critical",
            category="completeness",
            enabled=False,
        )
        report = engine.evaluate(DEVICE_VERSION_ID)
        rule_ids = {f.rule_id for f in report.findings}
        assert "GAP-004" not in rule_ids


@pytest.mark.unit
class TestGapEngineEvaluateRule:
    """Tests for GapDetectionEngine.evaluate_rule() method."""

    def test_evaluate_rule_returns_list(self, gap_engine):
        """evaluate_rule() should return a list of GapFinding."""
        findings = gap_engine.evaluate_rule("GAP-004", DEVICE_VERSION_ID)
        assert isinstance(findings, list)

    def test_evaluate_rule_unknown_id_raises(self, gap_engine):
        """evaluate_rule() with unknown ID should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown rule ID"):
            gap_engine.evaluate_rule("GAP-999", DEVICE_VERSION_ID)

    def test_evaluate_rule_disabled_returns_empty(self, mock_traceability, mock_repository):
        """Disabled rule should return empty list."""
        engine = GapDetectionEngine(
            traceability_engine=mock_traceability,
            twin_repository=mock_repository,
        )
        engine.RULE_DEFINITIONS["GAP-004"] = GapRuleDefinition(
            id="GAP-004",
            name="Disabled",
            description="Disabled",
            severity="critical",
            category="completeness",
            enabled=False,
        )
        findings = engine.evaluate_rule("GAP-004", DEVICE_VERSION_ID)
        assert findings == []


@pytest.mark.unit
class TestGetRules:
    """Tests for rule listing methods."""

    def test_get_rules_returns_all(self, gap_engine):
        """get_rules() should return all 12 rules."""
        rules = gap_engine.get_rules()
        assert len(rules) == 12

    def test_get_enabled_rules_default(self, gap_engine):
        """get_enabled_rules() should return 12 by default (all enabled)."""
        rules = gap_engine.get_enabled_rules()
        assert len(rules) == 12

    def test_get_enabled_rules_excludes_disabled(self, mock_traceability, mock_repository):
        """get_enabled_rules() should exclude disabled rules."""
        engine = GapDetectionEngine(
            traceability_engine=mock_traceability,
            twin_repository=mock_repository,
        )
        engine.RULE_DEFINITIONS["GAP-007"] = GapRuleDefinition(
            id="GAP-007",
            name="Disabled",
            description="Disabled",
            severity="minor",
            category="completeness",
            enabled=False,
        )
        rules = engine.get_enabled_rules()
        assert len(rules) == 11
        assert all(r.id != "GAP-007" for r in rules)


# =============================================================================
# Individual Rule Tests
# =============================================================================


@pytest.mark.unit
class TestGAP001UnmitigatedHazards:
    """Tests for GAP-001: Unmitigated hazards."""

    def test_no_hazards_no_findings(self, gap_engine, mock_repository):
        """No hazards should produce no findings."""
        mock_repository.get_by_device_version.return_value = []
        findings = gap_engine.evaluate_rule("GAP-001", DEVICE_VERSION_ID)
        assert len(findings) == 0

    def test_hazard_without_control_produces_finding(
        self, gap_engine, mock_repository, mock_traceability
    ):
        """Hazard with no mitigated_by link should produce a finding."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "h1", "description": "Electrical shock"}
        ]
        mock_traceability.get_links_from.return_value = []

        findings = gap_engine.evaluate_rule("GAP-001", DEVICE_VERSION_ID)
        assert len(findings) == 1
        assert findings[0].severity == "critical"
        assert findings[0].entity_type == "hazard"
        assert findings[0].entity_id == "h1"

    def test_hazard_with_control_no_finding(self, gap_engine, mock_repository, mock_traceability):
        """Hazard with mitigated_by link should produce no finding."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "h1", "description": "Electrical shock"}
        ]
        mock_traceability.get_links_from.return_value = [
            make_link(
                target_type="risk_control",
                target_id="rc1",
                relationship="mitigated_by",
            )
        ]

        findings = gap_engine.evaluate_rule("GAP-001", DEVICE_VERSION_ID)
        assert len(findings) == 0

    def test_multiple_hazards_partial_coverage(
        self, gap_engine, mock_repository, mock_traceability
    ):
        """Two hazards, one mitigated = one finding."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "h1", "description": "Shock"},
            {"id": "h2", "description": "Burn"},
        ]

        def links_from(source_type, source_id):
            if source_id == "h1":
                return [
                    make_link(
                        target_type="risk_control",
                        target_id="rc1",
                        relationship="mitigated_by",
                    )
                ]
            return []

        mock_traceability.get_links_from.side_effect = links_from

        findings = gap_engine.evaluate_rule("GAP-001", DEVICE_VERSION_ID)
        assert len(findings) == 1
        assert findings[0].entity_id == "h2"


@pytest.mark.unit
class TestGAP002UnverifiedControls:
    """Tests for GAP-002: Unverified controls."""

    def test_no_hazards_no_findings(self, gap_engine, mock_repository):
        """No hazards means no controls to check."""
        findings = gap_engine.evaluate_rule("GAP-002", DEVICE_VERSION_ID)
        assert len(findings) == 0

    def test_control_without_verification_produces_finding(
        self, gap_engine, mock_repository, mock_traceability
    ):
        """Risk control with no verified_by link should produce finding."""
        mock_repository.get_by_device_version.return_value = [{"id": "h1", "description": "Shock"}]

        def links_from(source_type, source_id):
            if source_type == "hazard" and source_id == "h1":
                return [
                    make_link(
                        target_type="risk_control",
                        target_id="rc1",
                        relationship="mitigated_by",
                    )
                ]
            if source_type == "risk_control" and source_id == "rc1":
                return []  # No verification
            return []

        mock_traceability.get_links_from.side_effect = links_from

        findings = gap_engine.evaluate_rule("GAP-002", DEVICE_VERSION_ID)
        assert len(findings) == 1
        assert findings[0].severity == "critical"
        assert findings[0].entity_type == "risk_control"

    def test_control_with_verification_no_finding(
        self, gap_engine, mock_repository, mock_traceability
    ):
        """Risk control with verified_by link should produce no finding."""
        mock_repository.get_by_device_version.return_value = [{"id": "h1", "description": "Shock"}]

        def links_from(source_type, source_id):
            if source_type == "hazard":
                return [
                    make_link(
                        target_type="risk_control",
                        target_id="rc1",
                        relationship="mitigated_by",
                    )
                ]
            if source_type == "risk_control":
                return [
                    make_link(
                        target_type="verification_test",
                        target_id="vt1",
                        relationship="verified_by",
                    )
                ]
            return []

        mock_traceability.get_links_from.side_effect = links_from

        findings = gap_engine.evaluate_rule("GAP-002", DEVICE_VERSION_ID)
        assert len(findings) == 0


@pytest.mark.unit
class TestGAP003UnsupportedClaims:
    """Tests for GAP-003: Unsupported claims."""

    def test_no_claims_no_findings(self, gap_engine, mock_repository):
        """No claims should produce no findings."""
        findings = gap_engine.evaluate_rule("GAP-003", DEVICE_VERSION_ID)
        assert len(findings) == 0

    def test_claim_without_evidence_produces_finding(
        self, gap_engine, mock_repository, mock_traceability
    ):
        """Claim with no supported_by link should produce finding."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "c1", "statement": "Device is safe"}
        ]
        mock_traceability.get_links_from.return_value = []

        findings = gap_engine.evaluate_rule("GAP-003", DEVICE_VERSION_ID)
        assert len(findings) == 1
        assert findings[0].severity == "major"
        assert findings[0].entity_type == "claim"

    def test_claim_with_evidence_no_finding(self, gap_engine, mock_repository, mock_traceability):
        """Claim with supported_by link should produce no finding."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "c1", "statement": "Device is safe"}
        ]
        mock_traceability.get_links_from.return_value = [
            make_link(
                target_type="evidence_item",
                target_id="ev1",
                relationship="supported_by",
            )
        ]

        findings = gap_engine.evaluate_rule("GAP-003", DEVICE_VERSION_ID)
        assert len(findings) == 0


@pytest.mark.unit
class TestGAP004MissingIntendedUse:
    """Tests for GAP-004: Missing intended use."""

    def test_no_intended_use_produces_finding(self, gap_engine, mock_repository):
        """No intended use should produce a critical finding."""
        mock_repository.get_by_device_version.return_value = []
        findings = gap_engine.evaluate_rule("GAP-004", DEVICE_VERSION_ID)
        assert len(findings) == 1
        assert findings[0].severity == "critical"
        assert findings[0].rule_id == "GAP-004"

    def test_with_intended_use_no_finding(self, gap_engine, mock_repository):
        """Having an intended use should produce no finding."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "iu1", "statement": "Monitor heart rate"}
        ]
        findings = gap_engine.evaluate_rule("GAP-004", DEVICE_VERSION_ID)
        assert len(findings) == 0


@pytest.mark.unit
class TestGAP005WeakEvidence:
    """Tests for GAP-005: Weak evidence."""

    def test_no_evidence_no_findings(self, gap_engine, mock_repository):
        """No evidence items should produce no findings."""
        findings = gap_engine.evaluate_rule("GAP-005", DEVICE_VERSION_ID)
        assert len(findings) == 0

    def test_weak_evidence_produces_finding(self, gap_engine, mock_repository):
        """Evidence with 'weak' strength should produce finding."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "ev1", "title": "Bench test", "strength": "weak"}
        ]
        findings = gap_engine.evaluate_rule("GAP-005", DEVICE_VERSION_ID)
        assert len(findings) == 1
        assert findings[0].details["current_strength"] == "weak"

    def test_insufficient_evidence_produces_finding(self, gap_engine, mock_repository):
        """Evidence with 'insufficient' strength should produce finding."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "ev1", "title": "Lit review", "strength": "insufficient"}
        ]
        findings = gap_engine.evaluate_rule("GAP-005", DEVICE_VERSION_ID)
        assert len(findings) == 1

    def test_strong_evidence_no_finding(self, gap_engine, mock_repository):
        """Evidence with 'strong' strength should produce no finding."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "ev1", "title": "Clinical trial", "strength": "strong"}
        ]
        findings = gap_engine.evaluate_rule("GAP-005", DEVICE_VERSION_ID)
        assert len(findings) == 0

    def test_moderate_evidence_no_finding(self, gap_engine, mock_repository):
        """Evidence with 'moderate' strength should produce no finding."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "ev1", "title": "Bench test", "strength": "moderate"}
        ]
        findings = gap_engine.evaluate_rule("GAP-005", DEVICE_VERSION_ID)
        assert len(findings) == 0


@pytest.mark.unit
class TestGAP006UntestedClaims:
    """Tests for GAP-006: Untested claims."""

    def test_no_claims_no_findings(self, gap_engine, mock_repository):
        """No claims should produce no findings."""
        findings = gap_engine.evaluate_rule("GAP-006", DEVICE_VERSION_ID)
        assert len(findings) == 0

    def test_claim_with_full_chain_no_finding(self, gap_engine, mock_repository, mock_traceability):
        """Claim linked through hazard->control->test should have no finding."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "c1", "statement": "Safe device"}
        ]

        def links_from(source_type, source_id):
            if source_type == "claim":
                return [
                    make_link(
                        target_type="hazard",
                        target_id="h1",
                        relationship="addresses",
                    )
                ]
            if source_type == "hazard":
                return [
                    make_link(
                        target_type="risk_control",
                        target_id="rc1",
                        relationship="mitigated_by",
                    )
                ]
            if source_type == "risk_control":
                return [
                    make_link(
                        target_type="verification_test",
                        target_id="vt1",
                        relationship="verified_by",
                    )
                ]
            return []

        mock_traceability.get_links_from.side_effect = links_from

        findings = gap_engine.evaluate_rule("GAP-006", DEVICE_VERSION_ID)
        assert len(findings) == 0

    def test_claim_with_no_chain_produces_finding(
        self, gap_engine, mock_repository, mock_traceability
    ):
        """Claim with no path to tests should produce finding."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "c1", "statement": "Safe device"}
        ]
        mock_traceability.get_links_from.return_value = []

        findings = gap_engine.evaluate_rule("GAP-006", DEVICE_VERSION_ID)
        assert len(findings) == 1
        assert findings[0].severity == "major"


@pytest.mark.unit
class TestGAP007NoSubmissionTarget:
    """Tests for GAP-007: No submission target."""

    def test_no_target_produces_finding(self, gap_engine, mock_repository):
        """No submission target should produce a minor finding."""
        mock_repository.get_by_device_version.return_value = []
        findings = gap_engine.evaluate_rule("GAP-007", DEVICE_VERSION_ID)
        assert len(findings) == 1
        assert findings[0].severity == "minor"

    def test_with_target_no_finding(self, gap_engine, mock_repository):
        """Having a submission target should produce no finding."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "st1", "regulatory_body": "health_canada"}
        ]
        findings = gap_engine.evaluate_rule("GAP-007", DEVICE_VERSION_ID)
        assert len(findings) == 0


@pytest.mark.unit
class TestGAP008UnattestedAIOutputs:
    """Tests for GAP-008: Unattested AI outputs.

    Engine uses get_by_field("artifacts", "device_version_id", dvid)
    to find artifacts that may need attestation.
    """

    def test_no_unattested_no_findings(self, gap_engine, mock_repository):
        """No artifacts should produce no findings."""
        mock_repository.get_by_field.return_value = []
        findings = gap_engine.evaluate_rule("GAP-008", DEVICE_VERSION_ID)
        assert len(findings) == 0

    def test_unattested_ai_artifact_produces_finding(self, gap_engine, mock_repository):
        """Unattested AI artifact should produce a major finding."""
        mock_repository.get_by_field.return_value = [
            {"id": "art1", "title": "AI-generated risk assessment"}
        ]
        findings = gap_engine.evaluate_rule("GAP-008", DEVICE_VERSION_ID)
        assert len(findings) == 1
        assert findings[0].severity == "major"
        assert "human" in findings[0].description.lower()


@pytest.mark.unit
class TestGAP009MissingLabeling:
    """Tests for GAP-009: Missing labeling."""

    def test_no_labeling_produces_finding(self, gap_engine, mock_repository):
        """No labeling assets should produce a major finding."""
        mock_repository.get_by_device_version.return_value = []
        findings = gap_engine.evaluate_rule("GAP-009", DEVICE_VERSION_ID)
        assert len(findings) == 1
        assert findings[0].severity == "major"

    def test_with_labeling_no_finding(self, gap_engine, mock_repository):
        """Having labeling assets should produce no finding."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "la1", "asset_type": "ifu", "title": "Instructions"}
        ]
        findings = gap_engine.evaluate_rule("GAP-009", DEVICE_VERSION_ID)
        assert len(findings) == 0


@pytest.mark.unit
class TestGAP010IncompleteRiskChain:
    """Tests for GAP-010: Incomplete risk chain."""

    def test_no_hazards_no_findings(self, gap_engine, mock_repository):
        """No hazards should produce no findings."""
        findings = gap_engine.evaluate_rule("GAP-010", DEVICE_VERSION_ID)
        assert len(findings) == 0

    def test_hazard_with_no_harm_and_no_control(
        self, gap_engine, mock_repository, mock_traceability
    ):
        """Hazard with neither harm nor control should produce finding."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "h1", "description": "Overheating"}
        ]
        mock_traceability.get_links_from.return_value = []

        findings = gap_engine.evaluate_rule("GAP-010", DEVICE_VERSION_ID)
        assert len(findings) == 1
        assert findings[0].severity == "critical"
        assert findings[0].details["has_harm"] is False
        assert findings[0].details["has_control"] is False

    def test_hazard_with_control_but_no_harm(self, gap_engine, mock_repository, mock_traceability):
        """Hazard with control but no harm link should produce finding."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "h1", "description": "Overheating"}
        ]
        mock_traceability.get_links_from.return_value = [
            make_link(
                target_type="risk_control",
                target_id="rc1",
                relationship="mitigated_by",
            )
        ]

        findings = gap_engine.evaluate_rule("GAP-010", DEVICE_VERSION_ID)
        assert len(findings) == 1
        assert findings[0].details["has_harm"] is False
        assert findings[0].details["has_control"] is True

    def test_hazard_with_both_harm_and_control_no_finding(
        self, gap_engine, mock_repository, mock_traceability
    ):
        """Hazard with both harm and control should produce no finding."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "h1", "description": "Overheating"}
        ]
        mock_traceability.get_links_from.return_value = [
            make_link(
                target_type="harm",
                target_id="harm1",
                relationship="causes",
            ),
            make_link(
                target_type="risk_control",
                target_id="rc1",
                relationship="mitigated_by",
            ),
        ]

        findings = gap_engine.evaluate_rule("GAP-010", DEVICE_VERSION_ID)
        assert len(findings) == 0


@pytest.mark.unit
class TestGAP011DraftEvidenceOnly:
    """Tests for GAP-011: Draft evidence only."""

    def test_no_evidence_no_findings(self, gap_engine, mock_repository):
        """No evidence items should produce no findings (other rules catch)."""
        findings = gap_engine.evaluate_rule("GAP-011", DEVICE_VERSION_ID)
        assert len(findings) == 0

    def test_all_draft_produces_finding(self, gap_engine, mock_repository):
        """All evidence in draft should produce finding."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "ev1", "status": "draft"},
            {"id": "ev2", "status": "draft"},
        ]
        findings = gap_engine.evaluate_rule("GAP-011", DEVICE_VERSION_ID)
        assert len(findings) == 1
        assert findings[0].severity == "major"
        assert findings[0].details["total_evidence"] == 2

    def test_mixed_status_no_finding(self, gap_engine, mock_repository):
        """Mixed status evidence should produce no finding."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "ev1", "status": "draft"},
            {"id": "ev2", "status": "accepted"},
        ]
        findings = gap_engine.evaluate_rule("GAP-011", DEVICE_VERSION_ID)
        assert len(findings) == 0

    def test_all_accepted_no_finding(self, gap_engine, mock_repository):
        """All accepted evidence should produce no finding."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "ev1", "status": "accepted"},
        ]
        findings = gap_engine.evaluate_rule("GAP-011", DEVICE_VERSION_ID)
        assert len(findings) == 0


@pytest.mark.unit
class TestGAP012NoClinicalEvidence:
    """Tests for GAP-012: No clinical evidence for Class III/IV.

    Engine uses get_by_id("device_versions", dvid) for device info and
    get_by_device_version("evidence_items", dvid) for evidence.
    """

    def test_no_device_version_no_findings(self, gap_engine, mock_repository):
        """No device version found should produce no findings."""
        mock_repository.get_by_id.return_value = None
        findings = gap_engine.evaluate_rule("GAP-012", DEVICE_VERSION_ID)
        assert len(findings) == 0

    def test_class_ii_no_finding(self, gap_engine, mock_repository):
        """Class II device should not require clinical evidence."""
        mock_repository.get_by_id.return_value = {
            "id": DEVICE_VERSION_ID,
            "device_class": "II",
        }
        findings = gap_engine.evaluate_rule("GAP-012", DEVICE_VERSION_ID)
        assert len(findings) == 0

    def test_class_iii_without_clinical_produces_finding(self, gap_engine, mock_repository):
        """Class III without clinical evidence should produce finding."""
        mock_repository.get_by_id.return_value = {
            "id": DEVICE_VERSION_ID,
            "device_class": "III",
        }
        mock_repository.get_by_device_version.return_value = [
            {"id": "ev1", "evidence_type": "test_report"},
        ]
        findings = gap_engine.evaluate_rule("GAP-012", DEVICE_VERSION_ID)
        assert len(findings) == 1
        assert findings[0].severity == "critical"
        assert findings[0].details["device_class"] == "III"

    def test_class_iv_without_clinical_produces_finding(self, gap_engine, mock_repository):
        """Class IV without clinical evidence should produce finding."""
        mock_repository.get_by_id.return_value = {
            "id": DEVICE_VERSION_ID,
            "device_class": "IV",
        }
        mock_repository.get_by_device_version.return_value = []
        findings = gap_engine.evaluate_rule("GAP-012", DEVICE_VERSION_ID)
        assert len(findings) == 1

    def test_class_iii_with_clinical_no_finding(self, gap_engine, mock_repository):
        """Class III with clinical evidence should produce no finding."""
        mock_repository.get_by_id.return_value = {
            "id": DEVICE_VERSION_ID,
            "device_class": "III",
        }
        mock_repository.get_by_device_version.return_value = [
            {"id": "ev1", "evidence_type": "clinical_data"},
        ]
        findings = gap_engine.evaluate_rule("GAP-012", DEVICE_VERSION_ID)
        assert len(findings) == 0

    def test_class_i_no_finding(self, gap_engine, mock_repository):
        """Class I device should not require clinical evidence."""
        mock_repository.get_by_id.return_value = {
            "id": DEVICE_VERSION_ID,
            "device_class": "I",
        }
        findings = gap_engine.evaluate_rule("GAP-012", DEVICE_VERSION_ID)
        assert len(findings) == 0


# =============================================================================
# Regulatory Language Safety Tests
# =============================================================================


@pytest.mark.unit
@pytest.mark.regulatory
class TestRegulatoryLanguageSafety:
    """Ensure no rule uses forbidden regulatory language."""

    FORBIDDEN_WORDS = ["compliant", "compliance", "ready", "approved", "pass"]
    FORBIDDEN_PHRASES = [
        "you are compliant",
        "device is compliant",
        "submission ready",
        "will pass",
        "is approved",
    ]

    def test_rule_descriptions_no_forbidden_language(self, gap_engine):
        """Rule descriptions must not use forbidden regulatory language."""
        for rule in gap_engine.get_rules():
            desc_lower = rule.description.lower()
            for phrase in self.FORBIDDEN_PHRASES:
                assert phrase not in desc_lower, (
                    f"Rule {rule.id} description contains " f"forbidden phrase: '{phrase}'"
                )

    def test_finding_descriptions_no_forbidden_language(self, gap_engine, mock_repository):
        """Finding descriptions must not use forbidden language."""
        # Run all rules to generate findings
        report = gap_engine.evaluate(DEVICE_VERSION_ID)
        for finding in report.findings:
            desc_lower = finding.description.lower()
            for phrase in self.FORBIDDEN_PHRASES:
                assert phrase not in desc_lower, (
                    f"Finding from {finding.rule_id} contains " f"forbidden phrase: '{phrase}'"
                )

    def test_remediation_no_forbidden_language(self, gap_engine, mock_repository):
        """Remediation text must not use forbidden language."""
        report = gap_engine.evaluate(DEVICE_VERSION_ID)
        for finding in report.findings:
            rem_lower = finding.remediation.lower()
            for phrase in self.FORBIDDEN_PHRASES:
                assert phrase not in rem_lower, (
                    f"Remediation from {finding.rule_id} contains " f"forbidden phrase: '{phrase}'"
                )


# =============================================================================
# Edge Case Tests
# =============================================================================


@pytest.mark.unit
class TestEdgeCases:
    """Edge case and boundary tests for robustness."""

    def test_engine_instance_isolation(self, mock_traceability, mock_repository):
        """Rule changes on one engine should not affect another."""
        engine1 = GapDetectionEngine(
            traceability_engine=mock_traceability,
            twin_repository=mock_repository,
        )
        engine2 = GapDetectionEngine(
            traceability_engine=mock_traceability,
            twin_repository=mock_repository,
        )
        # Disable a rule on engine1
        engine1.RULE_DEFINITIONS["GAP-001"].enabled = False
        # engine2 should be unaffected
        assert engine2.RULE_DEFINITIONS["GAP-001"].enabled is True

    def test_evaluate_with_none_device_version_id(self, gap_engine, mock_repository):
        """Engine should handle None-like device version gracefully."""
        # Empty string is edge case — engine should still run
        report = gap_engine.evaluate("")
        assert isinstance(report, GapReport)

    def test_multiple_findings_same_rule(self, gap_engine, mock_repository, mock_traceability):
        """Rule should produce one finding per unmitigated hazard."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "h1", "description": "Shock"},
            {"id": "h2", "description": "Burn"},
            {"id": "h3", "description": "Crush"},
        ]
        mock_traceability.get_links_from.return_value = []

        findings = gap_engine.evaluate_rule("GAP-001", DEVICE_VERSION_ID)
        assert len(findings) == 3


# =============================================================================
# Depth-Nested Traceability Tests
# =============================================================================


@pytest.mark.unit
class TestDepthNested:
    """Tests for rules that traverse multi-level trace chains."""

    def test_gap006_deep_chain_traversal(self, gap_engine, mock_repository, mock_traceability):
        """GAP-006 should follow claim->hazard->control->test chain."""
        mock_repository.get_by_device_version.return_value = [
            {"id": "c1", "statement": "Safety claim"}
        ]

        call_log = []

        def links_from(source_type, source_id):
            call_log.append((source_type, source_id))
            if source_type == "claim" and source_id == "c1":
                return [
                    make_link(
                        target_type="hazard",
                        target_id="h1",
                        relationship="addresses",
                    )
                ]
            if source_type == "hazard" and source_id == "h1":
                return [
                    make_link(
                        target_type="risk_control",
                        target_id="rc1",
                        relationship="mitigated_by",
                    )
                ]
            if source_type == "risk_control" and source_id == "rc1":
                return [
                    make_link(
                        target_type="verification_test",
                        target_id="vt1",
                        relationship="verified_by",
                    )
                ]
            return []

        mock_traceability.get_links_from.side_effect = links_from

        findings = gap_engine.evaluate_rule("GAP-006", DEVICE_VERSION_ID)
        assert len(findings) == 0
        # Verify the engine traversed the full chain
        assert ("claim", "c1") in call_log
        assert ("hazard", "h1") in call_log
        assert ("risk_control", "rc1") in call_log


# =============================================================================
# Singleton Tests
# =============================================================================


@pytest.mark.unit
class TestSingleton:
    """Tests for the get_gap_engine singleton function."""

    def test_get_gap_engine_returns_instance(self, mock_traceability, mock_repository):
        """get_gap_engine should return a GapDetectionEngine."""
        engine = get_gap_engine(
            traceability_engine=mock_traceability,
            twin_repository=mock_repository,
        )
        assert isinstance(engine, GapDetectionEngine)

    def test_get_gap_engine_with_overrides_creates_new(self, mock_traceability, mock_repository):
        """Providing dependencies should create a fresh instance."""
        engine1 = get_gap_engine(
            traceability_engine=mock_traceability,
            twin_repository=mock_repository,
        )
        engine2 = get_gap_engine(
            traceability_engine=MagicMock(),
            twin_repository=MagicMock(),
        )
        # With overrides, should create new
        assert engine1 is not engine2
