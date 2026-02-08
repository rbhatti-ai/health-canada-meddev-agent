"""
API endpoint tests for gap detection, readiness assessment, and rules.

Sprint 3c — Tests all 4 endpoints in gap_routes.py:
    GET /api/v1/gaps/{device_version_id}          — full gap report
    GET /api/v1/gaps/{device_version_id}/critical  — critical gaps only
    GET /api/v1/readiness/{device_version_id}      — readiness assessment
    GET /api/v1/rules                              — list all gap rules

All tests use mocked gap engine and readiness assessment to avoid
database dependencies. Tests verify status codes, response shapes,
error handling, and regulatory-safe language.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# =============================================================================
# Fixtures
# =============================================================================


def _make_finding(**overrides):
    """Create a mock GapFinding as SimpleNamespace."""
    defaults = {
        "rule_id": "GAP-001",
        "rule_name": "Unmitigated hazards",
        "severity": "critical",
        "category": "coverage",
        "description": "Hazard has no linked risk control",
        "entity_type": "hazard",
        "entity_id": "haz-001",
        "remediation": "Link a risk control to this hazard",
        "details": {},
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_gap_report(device_version_id="dv-test-001", findings=None):
    """Create a mock GapReport as SimpleNamespace."""
    if findings is None:
        findings = []
    critical = [f for f in findings if f.severity == "critical"]
    major = [f for f in findings if f.severity == "major"]
    minor = [f for f in findings if f.severity == "minor"]
    info = [f for f in findings if f.severity == "info"]
    return SimpleNamespace(
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


def _make_category_score(**overrides):
    """Create a mock CategoryScore as SimpleNamespace."""
    defaults = {
        "category": "coverage",
        "score": 0.85,
        "finding_count": 2,
        "critical_count": 1,
        "assessment": "Coverage evaluation indicates areas requiring attention.",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_readiness_report(
    device_version_id="dv-test-001",
    score=0.75,
    category_scores=None,
    critical_blockers=None,
    summary=None,
):
    """Create a mock ReadinessReport as SimpleNamespace."""
    if category_scores is None:
        category_scores = [_make_category_score()]
    if critical_blockers is None:
        critical_blockers = []
    if summary is None:
        summary = "Readiness assessment based on configured expectations."
    return SimpleNamespace(
        device_version_id=device_version_id,
        overall_readiness_score=score,
        category_scores=category_scores,
        critical_blockers=critical_blockers,
        summary=summary,
    )


def _make_rule(**overrides):
    """Create a mock GapRuleDefinition as SimpleNamespace."""
    defaults = {
        "id": "GAP-001",
        "name": "Unmitigated hazards",
        "description": "Checks for hazards with no linked risk control",
        "severity": "critical",
        "category": "coverage",
        "version": 1,
        "enabled": True,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


@pytest.fixture
def gap_client():
    """Create a TestClient with gap routes registered."""
    from fastapi import FastAPI

    from src.api.gap_routes import router

    test_app = FastAPI()
    test_app.include_router(router)
    return TestClient(test_app)


# =============================================================================
# GET /api/v1/gaps/{device_version_id} — Full Gap Report
# =============================================================================


@pytest.mark.api
class TestGapReportEndpoint:
    """Test GET /api/v1/gaps/{device_version_id}."""

    @patch("src.api.gap_routes.get_gap_engine")
    def test_gap_report_returns_200(self, mock_get_engine, gap_client):
        """Successful gap report returns 200."""
        mock_engine = MagicMock()
        mock_engine.evaluate.return_value = _make_gap_report()
        mock_get_engine.return_value = mock_engine

        response = gap_client.get("/api/v1/gaps/dv-test-001")
        assert response.status_code == 200

    @patch("src.api.gap_routes.get_gap_engine")
    def test_gap_report_response_shape(self, mock_get_engine, gap_client):
        """Response contains all expected top-level fields."""
        mock_engine = MagicMock()
        mock_engine.evaluate.return_value = _make_gap_report()
        mock_get_engine.return_value = mock_engine

        response = gap_client.get("/api/v1/gaps/dv-test-001")
        data = response.json()

        assert "device_version_id" in data
        assert "evaluated_at" in data
        assert "rules_executed" in data
        assert "total_findings" in data
        assert "critical_count" in data
        assert "major_count" in data
        assert "minor_count" in data
        assert "info_count" in data
        assert "findings" in data
        assert isinstance(data["findings"], list)

    @patch("src.api.gap_routes.get_gap_engine")
    def test_gap_report_with_findings(self, mock_get_engine, gap_client):
        """Report with findings returns correct counts and finding data."""
        findings = [
            _make_finding(rule_id="GAP-001", severity="critical"),
            _make_finding(rule_id="GAP-003", severity="major", rule_name="Unsupported claims"),
            _make_finding(rule_id="GAP-007", severity="minor", rule_name="No submission target"),
        ]
        mock_engine = MagicMock()
        mock_engine.evaluate.return_value = _make_gap_report(findings=findings)
        mock_get_engine.return_value = mock_engine

        response = gap_client.get("/api/v1/gaps/dv-test-001")
        data = response.json()

        assert data["total_findings"] == 3
        assert data["critical_count"] == 1
        assert data["major_count"] == 1
        assert data["minor_count"] == 1
        assert len(data["findings"]) == 3

    @patch("src.api.gap_routes.get_gap_engine")
    def test_gap_report_finding_fields(self, mock_get_engine, gap_client):
        """Each finding has all required fields."""
        findings = [_make_finding()]
        mock_engine = MagicMock()
        mock_engine.evaluate.return_value = _make_gap_report(findings=findings)
        mock_get_engine.return_value = mock_engine

        response = gap_client.get("/api/v1/gaps/dv-test-001")
        finding = response.json()["findings"][0]

        assert finding["rule_id"] == "GAP-001"
        assert finding["rule_name"] == "Unmitigated hazards"
        assert finding["severity"] == "critical"
        assert finding["category"] == "coverage"
        assert "description" in finding
        assert "entity_type" in finding
        assert "remediation" in finding

    @patch("src.api.gap_routes.get_gap_engine")
    def test_gap_report_empty_findings(self, mock_get_engine, gap_client):
        """Report with no findings returns empty list and zero counts."""
        mock_engine = MagicMock()
        mock_engine.evaluate.return_value = _make_gap_report(findings=[])
        mock_get_engine.return_value = mock_engine

        response = gap_client.get("/api/v1/gaps/dv-test-001")
        data = response.json()

        assert data["total_findings"] == 0
        assert data["critical_count"] == 0
        assert data["findings"] == []

    @patch("src.api.gap_routes.get_gap_engine")
    def test_gap_report_passes_device_version_id(self, mock_get_engine, gap_client):
        """Endpoint passes the device_version_id to the engine."""
        mock_engine = MagicMock()
        mock_engine.evaluate.return_value = _make_gap_report(device_version_id="dv-specific-123")
        mock_get_engine.return_value = mock_engine

        gap_client.get("/api/v1/gaps/dv-specific-123")
        mock_engine.evaluate.assert_called_once_with("dv-specific-123")

    @patch("src.api.gap_routes.get_gap_engine")
    def test_gap_report_engine_value_error_returns_400(self, mock_get_engine, gap_client):
        """ValueError from engine returns 400."""
        mock_engine = MagicMock()
        mock_engine.evaluate.side_effect = ValueError("Invalid device version ID")
        mock_get_engine.return_value = mock_engine

        response = gap_client.get("/api/v1/gaps/invalid-id")
        assert response.status_code == 400
        assert "Invalid device version ID" in response.json()["detail"]

    @patch("src.api.gap_routes.get_gap_engine")
    def test_gap_report_engine_failure_returns_500(self, mock_get_engine, gap_client):
        """Unexpected engine failure returns 500."""
        mock_engine = MagicMock()
        mock_engine.evaluate.side_effect = RuntimeError("DB connection failed")
        mock_get_engine.return_value = mock_engine

        response = gap_client.get("/api/v1/gaps/dv-test-001")
        assert response.status_code == 500
        assert "RuntimeError" in response.json()["detail"]


# =============================================================================
# GET /api/v1/gaps/{device_version_id}/critical — Critical Gaps Only
# =============================================================================


@pytest.mark.api
class TestCriticalGapsEndpoint:
    """Test GET /api/v1/gaps/{device_version_id}/critical."""

    @patch("src.api.gap_routes.get_gap_engine")
    def test_critical_gaps_returns_200(self, mock_get_engine, gap_client):
        """Successful critical gaps request returns 200."""
        mock_engine = MagicMock()
        mock_engine.evaluate.return_value = _make_gap_report()
        mock_get_engine.return_value = mock_engine

        response = gap_client.get("/api/v1/gaps/dv-test-001/critical")
        assert response.status_code == 200

    @patch("src.api.gap_routes.get_gap_engine")
    def test_critical_gaps_response_shape(self, mock_get_engine, gap_client):
        """Response contains expected fields."""
        mock_engine = MagicMock()
        mock_engine.evaluate.return_value = _make_gap_report()
        mock_get_engine.return_value = mock_engine

        response = gap_client.get("/api/v1/gaps/dv-test-001/critical")
        data = response.json()

        assert "device_version_id" in data
        assert "critical_count" in data
        assert "critical_findings" in data
        assert isinstance(data["critical_findings"], list)

    @patch("src.api.gap_routes.get_gap_engine")
    def test_critical_gaps_filters_correctly(self, mock_get_engine, gap_client):
        """Only critical findings are returned."""
        findings = [
            _make_finding(rule_id="GAP-001", severity="critical"),
            _make_finding(rule_id="GAP-003", severity="major"),
            _make_finding(
                rule_id="GAP-010", severity="critical", rule_name="Incomplete risk chain"
            ),
        ]
        mock_engine = MagicMock()
        mock_engine.evaluate.return_value = _make_gap_report(findings=findings)
        mock_get_engine.return_value = mock_engine

        response = gap_client.get("/api/v1/gaps/dv-test-001/critical")
        data = response.json()

        assert data["critical_count"] == 2
        assert len(data["critical_findings"]) == 2
        for f in data["critical_findings"]:
            assert f["severity"] == "critical"

    @patch("src.api.gap_routes.get_gap_engine")
    def test_critical_gaps_none_found(self, mock_get_engine, gap_client):
        """No critical findings returns empty list."""
        findings = [_make_finding(severity="major")]
        mock_engine = MagicMock()
        mock_engine.evaluate.return_value = _make_gap_report(findings=findings)
        mock_get_engine.return_value = mock_engine

        response = gap_client.get("/api/v1/gaps/dv-test-001/critical")
        data = response.json()

        assert data["critical_count"] == 0
        assert data["critical_findings"] == []

    @patch("src.api.gap_routes.get_gap_engine")
    def test_critical_gaps_engine_failure_returns_500(self, mock_get_engine, gap_client):
        """Unexpected engine failure returns 500."""
        mock_engine = MagicMock()
        mock_engine.evaluate.side_effect = RuntimeError("DB timeout")
        mock_get_engine.return_value = mock_engine

        response = gap_client.get("/api/v1/gaps/dv-test-001/critical")
        assert response.status_code == 500


# =============================================================================
# GET /api/v1/readiness/{device_version_id} — Readiness Assessment
# =============================================================================


@pytest.mark.api
class TestReadinessEndpoint:
    """Test GET /api/v1/readiness/{device_version_id}."""

    @patch("src.api.gap_routes.get_readiness_assessment")
    def test_readiness_returns_200(self, mock_get_assessment, gap_client):
        """Successful readiness assessment returns 200."""
        mock_assessment = MagicMock()
        mock_assessment.assess.return_value = _make_readiness_report()
        mock_get_assessment.return_value = mock_assessment

        response = gap_client.get("/api/v1/readiness/dv-test-001")
        assert response.status_code == 200

    @patch("src.api.gap_routes.get_readiness_assessment")
    def test_readiness_response_shape(self, mock_get_assessment, gap_client):
        """Response contains all expected fields."""
        mock_assessment = MagicMock()
        mock_assessment.assess.return_value = _make_readiness_report()
        mock_get_assessment.return_value = mock_assessment

        response = gap_client.get("/api/v1/readiness/dv-test-001")
        data = response.json()

        assert "device_version_id" in data
        assert "overall_readiness_score" in data
        assert "category_scores" in data
        assert "critical_blockers" in data
        assert "summary" in data
        assert isinstance(data["category_scores"], list)
        assert isinstance(data["critical_blockers"], list)

    @patch("src.api.gap_routes.get_readiness_assessment")
    def test_readiness_score_range(self, mock_get_assessment, gap_client):
        """Readiness score is between 0.0 and 1.0."""
        mock_assessment = MagicMock()
        mock_assessment.assess.return_value = _make_readiness_report(score=0.72)
        mock_get_assessment.return_value = mock_assessment

        response = gap_client.get("/api/v1/readiness/dv-test-001")
        data = response.json()

        assert 0.0 <= data["overall_readiness_score"] <= 1.0

    @patch("src.api.gap_routes.get_readiness_assessment")
    def test_readiness_category_scores(self, mock_get_assessment, gap_client):
        """Category scores contain expected fields."""
        scores = [
            _make_category_score(category="coverage", score=0.9),
            _make_category_score(category="completeness", score=0.7),
        ]
        mock_assessment = MagicMock()
        mock_assessment.assess.return_value = _make_readiness_report(category_scores=scores)
        mock_get_assessment.return_value = mock_assessment

        response = gap_client.get("/api/v1/readiness/dv-test-001")
        data = response.json()

        assert len(data["category_scores"]) == 2
        cs = data["category_scores"][0]
        assert "category" in cs
        assert "score" in cs
        assert "finding_count" in cs
        assert "critical_count" in cs
        assert "assessment" in cs

    @patch("src.api.gap_routes.get_readiness_assessment")
    def test_readiness_with_blockers(self, mock_get_assessment, gap_client):
        """Critical blockers are included in response."""
        blockers = [_make_finding(severity="critical")]
        mock_assessment = MagicMock()
        mock_assessment.assess.return_value = _make_readiness_report(critical_blockers=blockers)
        mock_get_assessment.return_value = mock_assessment

        response = gap_client.get("/api/v1/readiness/dv-test-001")
        data = response.json()

        assert len(data["critical_blockers"]) == 1
        assert data["critical_blockers"][0]["severity"] == "critical"

    @patch("src.api.gap_routes.get_readiness_assessment")
    def test_readiness_summary_is_regulatory_safe(self, mock_get_assessment, gap_client):
        """Summary text uses regulatory-safe language."""
        mock_assessment = MagicMock()
        mock_assessment.assess.return_value = _make_readiness_report(
            summary="Readiness assessment based on configured expectations."
        )
        mock_get_assessment.return_value = mock_assessment

        response = gap_client.get("/api/v1/readiness/dv-test-001")
        data = response.json()

        summary = data["summary"].lower()
        # Forbidden words per regulatory safety requirements
        forbidden = ["compliant", "certified", "approved", "guaranteed", "assured"]
        for word in forbidden:
            assert word not in summary, f"Forbidden word '{word}' found in summary"

    @patch("src.api.gap_routes.get_readiness_assessment")
    def test_readiness_passes_device_version_id(self, mock_get_assessment, gap_client):
        """Endpoint passes device_version_id to assessment."""
        mock_assessment = MagicMock()
        mock_assessment.assess.return_value = _make_readiness_report()
        mock_get_assessment.return_value = mock_assessment

        gap_client.get("/api/v1/readiness/dv-specific-456")
        mock_assessment.assess.assert_called_once_with("dv-specific-456")

    @patch("src.api.gap_routes.get_readiness_assessment")
    def test_readiness_value_error_returns_400(self, mock_get_assessment, gap_client):
        """ValueError from assessment returns 400."""
        mock_assessment = MagicMock()
        mock_assessment.assess.side_effect = ValueError("Bad device version")
        mock_get_assessment.return_value = mock_assessment

        response = gap_client.get("/api/v1/readiness/bad-id")
        assert response.status_code == 400

    @patch("src.api.gap_routes.get_readiness_assessment")
    def test_readiness_failure_returns_500(self, mock_get_assessment, gap_client):
        """Unexpected assessment failure returns 500."""
        mock_assessment = MagicMock()
        mock_assessment.assess.side_effect = RuntimeError("Scoring engine crashed")
        mock_get_assessment.return_value = mock_assessment

        response = gap_client.get("/api/v1/readiness/dv-test-001")
        assert response.status_code == 500
        assert "RuntimeError" in response.json()["detail"]


# =============================================================================
# GET /api/v1/rules — List All Gap Rules
# =============================================================================


@pytest.mark.api
class TestRulesEndpoint:
    """Test GET /api/v1/rules."""

    @patch("src.api.gap_routes.get_gap_engine")
    def test_rules_returns_200(self, mock_get_engine, gap_client):
        """Rules listing returns 200."""
        mock_engine = MagicMock()
        mock_engine.get_rules.return_value = [_make_rule()]
        mock_get_engine.return_value = mock_engine

        response = gap_client.get("/api/v1/rules")
        assert response.status_code == 200

    @patch("src.api.gap_routes.get_gap_engine")
    def test_rules_response_shape(self, mock_get_engine, gap_client):
        """Response contains expected top-level fields."""
        mock_engine = MagicMock()
        mock_engine.get_rules.return_value = [_make_rule()]
        mock_get_engine.return_value = mock_engine

        response = gap_client.get("/api/v1/rules")
        data = response.json()

        assert "total_rules" in data
        assert "enabled_rules" in data
        assert "rules" in data
        assert isinstance(data["rules"], list)

    @patch("src.api.gap_routes.get_gap_engine")
    def test_rules_returns_all_12(self, mock_get_engine, gap_client):
        """Returns all 12 rules when all are present."""
        rules = [_make_rule(id=f"GAP-{i:03d}", name=f"Rule {i}") for i in range(1, 13)]
        mock_engine = MagicMock()
        mock_engine.get_rules.return_value = rules
        mock_get_engine.return_value = mock_engine

        response = gap_client.get("/api/v1/rules")
        data = response.json()

        assert data["total_rules"] == 12
        assert data["enabled_rules"] == 12
        assert len(data["rules"]) == 12

    @patch("src.api.gap_routes.get_gap_engine")
    def test_rules_counts_disabled(self, mock_get_engine, gap_client):
        """Correctly counts enabled vs disabled rules."""
        rules = [
            _make_rule(id="GAP-001", enabled=True),
            _make_rule(id="GAP-002", enabled=True),
            _make_rule(id="GAP-003", enabled=False),
        ]
        mock_engine = MagicMock()
        mock_engine.get_rules.return_value = rules
        mock_get_engine.return_value = mock_engine

        response = gap_client.get("/api/v1/rules")
        data = response.json()

        assert data["total_rules"] == 3
        assert data["enabled_rules"] == 2

    @patch("src.api.gap_routes.get_gap_engine")
    def test_rules_rule_fields(self, mock_get_engine, gap_client):
        """Each rule has all required fields."""
        mock_engine = MagicMock()
        mock_engine.get_rules.return_value = [_make_rule()]
        mock_get_engine.return_value = mock_engine

        response = gap_client.get("/api/v1/rules")
        rule = response.json()["rules"][0]

        assert rule["id"] == "GAP-001"
        assert rule["name"] == "Unmitigated hazards"
        assert rule["severity"] == "critical"
        assert rule["category"] == "coverage"
        assert rule["version"] == 1
        assert rule["enabled"] is True
        assert "description" in rule

    @patch("src.api.gap_routes.get_gap_engine")
    def test_rules_engine_failure_returns_500(self, mock_get_engine, gap_client):
        """Engine failure returns 500."""
        mock_engine = MagicMock()
        mock_engine.get_rules.side_effect = RuntimeError("Config error")
        mock_get_engine.return_value = mock_engine

        response = gap_client.get("/api/v1/rules")
        assert response.status_code == 500


# =============================================================================
# Edge Cases & Integration
# =============================================================================


@pytest.mark.api
class TestGapEndpointEdgeCases:
    """Edge case tests across all gap endpoints."""

    def test_wrong_method_gaps_returns_405(self, gap_client):
        """POST to GET-only endpoint returns 405."""
        response = gap_client.post("/api/v1/gaps/dv-test-001")
        assert response.status_code == 405

    def test_wrong_method_readiness_returns_405(self, gap_client):
        """POST to readiness endpoint returns 405."""
        response = gap_client.post("/api/v1/readiness/dv-test-001")
        assert response.status_code == 405

    def test_wrong_method_rules_returns_405(self, gap_client):
        """POST to rules endpoint returns 405."""
        response = gap_client.post("/api/v1/rules")
        assert response.status_code == 405

    @patch("src.api.gap_routes.get_gap_engine")
    def test_gap_report_with_special_chars_in_id(self, mock_get_engine, gap_client):
        """Device version ID with UUID format works."""
        mock_engine = MagicMock()
        mock_engine.evaluate.return_value = _make_gap_report(
            device_version_id="550e8400-e29b-41d4-a716-446655440000"
        )
        mock_get_engine.return_value = mock_engine

        response = gap_client.get("/api/v1/gaps/550e8400-e29b-41d4-a716-446655440000")
        assert response.status_code == 200
        assert response.json()["device_version_id"] == "550e8400-e29b-41d4-a716-446655440000"

    @patch("src.api.gap_routes.get_gap_engine")
    def test_gap_report_finding_with_no_entity_id(self, mock_get_engine, gap_client):
        """Finding with None entity_id returns empty string."""
        finding = _make_finding(entity_id=None)
        mock_engine = MagicMock()
        mock_engine.evaluate.return_value = _make_gap_report(findings=[finding])
        mock_get_engine.return_value = mock_engine

        response = gap_client.get("/api/v1/gaps/dv-test-001")
        assert response.json()["findings"][0]["entity_id"] == ""
