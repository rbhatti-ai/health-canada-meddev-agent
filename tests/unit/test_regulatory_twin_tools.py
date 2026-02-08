"""
Tests for Regulatory Twin Agent Tools — Sprint 4A

Tests all 13 LangGraph tools wrapping regulatory services.
All tests use mocked services — no DB required.

Test categories per tool:
1. Success path — tool returns expected result
2. Input validation — tool handles bad inputs gracefully
3. Error handling — tool returns error dict (never raises)
4. Serialization — Pydantic models convert to dicts

Naming convention: test_{tool_name}_{scenario}
"""

import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _uuid() -> str:
    """Generate a random UUID string for test data."""
    return str(uuid.uuid4())


def _make_trace_link(**overrides) -> SimpleNamespace:
    """Create a mock TraceLink object with Pydantic-like interface."""
    defaults = {
        "id": _uuid(),
        "source_type": "claim",
        "source_id": _uuid(),
        "target_type": "hazard",
        "target_id": _uuid(),
        "relationship": "addresses",
        "rationale": "Test rationale",
        "created_by": _uuid(),
        "organization_id": _uuid(),
        "device_version_id": _uuid(),
    }
    defaults.update(overrides)
    obj = SimpleNamespace(**defaults)
    obj.model_dump = lambda: defaults
    return obj


def _make_gap_finding(**overrides) -> SimpleNamespace:
    """Create a mock GapFinding object."""
    defaults = {
        "rule_id": "GAP-001",
        "rule_name": "Unmitigated hazards",
        "severity": "critical",
        "category": "coverage",
        "description": "Hazard has no linked risk control",
        "entity_type": "hazard",
        "entity_id": _uuid(),
        "remediation": "Create a risk control and link it",
        "details": {},
    }
    defaults.update(overrides)
    obj = SimpleNamespace(**defaults)
    obj.model_dump = lambda: defaults
    return obj


def _make_gap_report(**overrides) -> SimpleNamespace:
    """Create a mock GapReport object."""
    finding_critical = _make_gap_finding(severity="critical")
    finding_major = _make_gap_finding(
        rule_id="GAP-003", severity="major", rule_name="Unsupported claims"
    )
    defaults = {
        "device_version_id": _uuid(),
        "evaluated_at": "2026-02-07T12:00:00",
        "rules_executed": 12,
        "total_findings": 2,
        "critical_count": 1,
        "major_count": 1,
        "minor_count": 0,
        "info_count": 0,
        "findings": [finding_critical, finding_major],
        "critical_findings": [finding_critical],
    }
    defaults.update(overrides)
    obj = SimpleNamespace(**defaults)
    obj.model_dump = lambda: {
        k: (
            [f.model_dump() for f in v]
            if isinstance(v, list) and v and hasattr(v[0], "model_dump")
            else v
        )
        for k, v in defaults.items()
    }
    return obj


def _make_readiness_report(**overrides) -> SimpleNamespace:
    """Create a mock ReadinessReport object."""
    defaults = {
        "overall_readiness_score": 0.72,
        "category_scores": {
            "coverage": 0.8,
            "completeness": 0.7,
            "consistency": 0.65,
            "evidence_strength": 0.75,
        },
        "critical_blockers": [],
        "summary": "Readiness assessment based on configured expectations.",
    }
    defaults.update(overrides)
    obj = SimpleNamespace(**defaults)
    obj.model_dump = lambda: defaults
    return obj


def _make_evidence_item(**overrides) -> SimpleNamespace:
    """Create a mock evidence item."""
    defaults = {
        "id": _uuid(),
        "device_version_id": _uuid(),
        "evidence_type": "bench_test",
        "title": "Biocompatibility test report",
        "status": "final",
        "strength": "strong",
    }
    defaults.update(overrides)
    obj = SimpleNamespace(**defaults)
    obj.model_dump = lambda: defaults
    return obj


def _make_attestation(**overrides) -> SimpleNamespace:
    """Create a mock attestation."""
    defaults = {
        "id": _uuid(),
        "artifact_id": _uuid(),
        "attested_by": _uuid(),
        "attestation_type": "approved",
        "attestation_note": "Reviewed and approved",
        "organization_id": _uuid(),
    }
    defaults.update(overrides)
    obj = SimpleNamespace(**defaults)
    obj.model_dump = lambda: defaults
    return obj


# ===========================================================================
# TRACEABILITY TOOLS — create_trace_link
# ===========================================================================


class TestCreateTraceLink:
    """Tests for the create_trace_link tool."""

    @patch("src.agents.regulatory_twin_tools._get_traceability_engine")
    def test_success_returns_link(self, mock_get_engine):
        from src.agents.regulatory_twin_tools import create_trace_link

        mock_link = _make_trace_link()
        mock_engine = MagicMock()
        mock_engine.create_link.return_value = mock_link
        mock_get_engine.return_value = mock_engine

        result = create_trace_link.invoke(
            {
                "source_type": "claim",
                "source_id": _uuid(),
                "target_type": "hazard",
                "target_id": _uuid(),
                "relationship": "addresses",
                "rationale": "Test link",
                "created_by": _uuid(),
                "organization_id": _uuid(),
                "device_version_id": _uuid(),
            }
        )

        assert result["status"] == "success"
        assert result["tool"] == "create_trace_link"
        assert "result" in result

    @patch("src.agents.regulatory_twin_tools._get_traceability_engine")
    def test_invalid_relationship_returns_error(self, mock_get_engine):
        from src.agents.regulatory_twin_tools import create_trace_link

        mock_engine = MagicMock()
        mock_engine.create_link.side_effect = ValueError(
            "Invalid relationship: claim -> harm with 'causes'"
        )
        mock_get_engine.return_value = mock_engine

        result = create_trace_link.invoke(
            {
                "source_type": "claim",
                "source_id": _uuid(),
                "target_type": "harm",
                "target_id": _uuid(),
                "relationship": "causes",
                "rationale": "Bad link",
                "created_by": _uuid(),
                "organization_id": _uuid(),
                "device_version_id": _uuid(),
            }
        )

        assert result["status"] == "error"
        assert "Invalid relationship" in result["error"]

    @patch("src.agents.regulatory_twin_tools._get_traceability_engine")
    def test_unexpected_error_returns_error_dict(self, mock_get_engine):
        from src.agents.regulatory_twin_tools import create_trace_link

        mock_engine = MagicMock()
        mock_engine.create_link.side_effect = RuntimeError("DB connection lost")
        mock_get_engine.return_value = mock_engine

        result = create_trace_link.invoke(
            {
                "source_type": "claim",
                "source_id": _uuid(),
                "target_type": "hazard",
                "target_id": _uuid(),
                "relationship": "addresses",
                "rationale": "Test",
                "created_by": _uuid(),
                "organization_id": _uuid(),
                "device_version_id": _uuid(),
            }
        )

        assert result["status"] == "error"
        assert "Unexpected error" in result["error"]

    @patch("src.agents.regulatory_twin_tools._get_traceability_engine")
    def test_result_contains_tool_name(self, mock_get_engine):
        from src.agents.regulatory_twin_tools import create_trace_link

        mock_engine = MagicMock()
        mock_engine.create_link.return_value = _make_trace_link()
        mock_get_engine.return_value = mock_engine

        result = create_trace_link.invoke(
            {
                "source_type": "claim",
                "source_id": _uuid(),
                "target_type": "hazard",
                "target_id": _uuid(),
                "relationship": "addresses",
                "rationale": "Test",
                "created_by": _uuid(),
                "organization_id": _uuid(),
                "device_version_id": _uuid(),
            }
        )

        assert result["tool"] == "create_trace_link"


# ===========================================================================
# TRACEABILITY TOOLS — get_trace_chain
# ===========================================================================


class TestGetTraceChain:
    """Tests for the get_trace_chain tool."""

    @patch("src.agents.regulatory_twin_tools._get_traceability_engine")
    def test_success_returns_chain(self, mock_get_engine):
        from src.agents.regulatory_twin_tools import get_trace_chain

        mock_chain = SimpleNamespace(
            claim_id=_uuid(),
            links=[],
        )
        mock_chain.model_dump = lambda: {
            "claim_id": mock_chain.claim_id,
            "links": [],
        }
        mock_engine = MagicMock()
        mock_engine.get_full_chain.return_value = mock_chain
        mock_get_engine.return_value = mock_engine

        result = get_trace_chain.invoke({"claim_id": _uuid()})

        assert result["status"] == "success"
        assert "claim_id" in result["result"]

    @patch("src.agents.regulatory_twin_tools._get_traceability_engine")
    def test_nonexistent_claim_returns_error(self, mock_get_engine):
        from src.agents.regulatory_twin_tools import get_trace_chain

        mock_engine = MagicMock()
        mock_engine.get_full_chain.side_effect = ValueError("Claim not found")
        mock_get_engine.return_value = mock_engine

        result = get_trace_chain.invoke({"claim_id": _uuid()})

        assert result["status"] == "error"

    @patch("src.agents.regulatory_twin_tools._get_traceability_engine")
    def test_dict_return_handled(self, mock_get_engine):
        from src.agents.regulatory_twin_tools import get_trace_chain

        mock_engine = MagicMock()
        mock_engine.get_full_chain.return_value = {"claim_id": "abc", "links": []}
        mock_get_engine.return_value = mock_engine

        result = get_trace_chain.invoke({"claim_id": _uuid()})

        assert result["status"] == "success"
        assert result["result"]["claim_id"] == "abc"


# ===========================================================================
# TRACEABILITY TOOLS — get_coverage_report
# ===========================================================================


class TestGetCoverageReport:
    """Tests for the get_coverage_report tool."""

    @patch("src.agents.regulatory_twin_tools._get_traceability_engine")
    def test_success(self, mock_get_engine):
        from src.agents.regulatory_twin_tools import get_coverage_report

        mock_report = SimpleNamespace(claims=[], coverage_percent=85.0)
        mock_report.model_dump = lambda: {"claims": [], "coverage_percent": 85.0}
        mock_engine = MagicMock()
        mock_engine.get_coverage_report.return_value = mock_report
        mock_get_engine.return_value = mock_engine

        result = get_coverage_report.invoke({"device_version_id": _uuid()})

        assert result["status"] == "success"
        assert result["result"]["coverage_percent"] == 85.0

    @patch("src.agents.regulatory_twin_tools._get_traceability_engine")
    def test_error_returns_dict(self, mock_get_engine):
        from src.agents.regulatory_twin_tools import get_coverage_report

        mock_engine = MagicMock()
        mock_engine.get_coverage_report.side_effect = RuntimeError("DB down")
        mock_get_engine.return_value = mock_engine

        result = get_coverage_report.invoke({"device_version_id": _uuid()})

        assert result["status"] == "error"
        assert result["tool"] == "get_coverage_report"


# ===========================================================================
# TRACEABILITY TOOLS — validate_trace_relationship
# ===========================================================================


class TestValidateTraceRelationship:
    """Tests for the validate_trace_relationship tool."""

    @patch("src.agents.regulatory_twin_tools._get_traceability_engine")
    def test_valid_relationship(self, mock_get_engine):
        from src.agents.regulatory_twin_tools import validate_trace_relationship

        mock_engine = MagicMock()
        mock_engine.validate_link.return_value = True
        mock_get_engine.return_value = mock_engine

        result = validate_trace_relationship.invoke(
            {
                "source_type": "claim",
                "target_type": "hazard",
                "relationship": "addresses",
            }
        )

        assert result["status"] == "success"
        assert result["result"]["is_valid"] is True

    @patch("src.agents.regulatory_twin_tools._get_traceability_engine")
    def test_invalid_relationship(self, mock_get_engine):
        from src.agents.regulatory_twin_tools import validate_trace_relationship

        mock_engine = MagicMock()
        mock_engine.validate_link.return_value = False
        mock_get_engine.return_value = mock_engine

        result = validate_trace_relationship.invoke(
            {
                "source_type": "claim",
                "target_type": "harm",
                "relationship": "causes",
            }
        )

        assert result["status"] == "success"
        assert result["result"]["is_valid"] is False

    @patch("src.agents.regulatory_twin_tools._get_traceability_engine")
    def test_result_includes_input_params(self, mock_get_engine):
        from src.agents.regulatory_twin_tools import validate_trace_relationship

        mock_engine = MagicMock()
        mock_engine.validate_link.return_value = True
        mock_get_engine.return_value = mock_engine

        result = validate_trace_relationship.invoke(
            {
                "source_type": "hazard",
                "target_type": "risk_control",
                "relationship": "mitigated_by",
            }
        )

        assert result["result"]["source_type"] == "hazard"
        assert result["result"]["target_type"] == "risk_control"
        assert result["result"]["relationship"] == "mitigated_by"


# ===========================================================================
# EVIDENCE TOOLS — ingest_evidence
# ===========================================================================


class TestIngestEvidence:
    """Tests for the ingest_evidence tool."""

    @patch("src.agents.regulatory_twin_tools._get_evidence_service")
    def test_success(self, mock_get_service):
        from src.agents.regulatory_twin_tools import ingest_evidence

        mock_item = _make_evidence_item()
        mock_service = MagicMock()
        mock_service.ingest_evidence.return_value = mock_item
        mock_get_service.return_value = mock_service

        result = ingest_evidence.invoke(
            {
                "device_version_id": _uuid(),
                "evidence_type": "bench_test",
                "title": "Test report",
                "artifact_data": {"type": "report", "title": "Test"},
                "linked_to": {"target_type": "claim", "target_id": _uuid()},
                "organization_id": _uuid(),
                "created_by": _uuid(),
            }
        )

        assert result["status"] == "success"

    @patch("src.agents.regulatory_twin_tools._get_evidence_service")
    def test_validation_error(self, mock_get_service):
        from src.agents.regulatory_twin_tools import ingest_evidence

        mock_service = MagicMock()
        mock_service.ingest_evidence.side_effect = ValueError("Invalid evidence type")
        mock_get_service.return_value = mock_service

        result = ingest_evidence.invoke(
            {
                "device_version_id": _uuid(),
                "evidence_type": "invalid_type",
                "title": "Test",
                "artifact_data": {},
                "linked_to": {},
                "organization_id": _uuid(),
                "created_by": _uuid(),
            }
        )

        assert result["status"] == "error"
        assert "Invalid evidence type" in result["error"]


# ===========================================================================
# EVIDENCE TOOLS — get_evidence_for_device
# ===========================================================================


class TestGetEvidenceForDevice:
    """Tests for the get_evidence_for_device tool."""

    @patch("src.agents.regulatory_twin_tools._get_evidence_service")
    def test_success_with_items(self, mock_get_service):
        from src.agents.regulatory_twin_tools import get_evidence_for_device

        items = [_make_evidence_item(), _make_evidence_item()]
        mock_service = MagicMock()
        mock_service.get_evidence_for_device.return_value = items
        mock_get_service.return_value = mock_service

        dvid = _uuid()
        result = get_evidence_for_device.invoke({"device_version_id": dvid})

        assert result["status"] == "success"
        assert result["result"]["device_version_id"] == dvid
        assert len(result["result"]["evidence_items"]) == 2

    @patch("src.agents.regulatory_twin_tools._get_evidence_service")
    def test_empty_result(self, mock_get_service):
        from src.agents.regulatory_twin_tools import get_evidence_for_device

        mock_service = MagicMock()
        mock_service.get_evidence_for_device.return_value = []
        mock_get_service.return_value = mock_service

        result = get_evidence_for_device.invoke({"device_version_id": _uuid()})

        assert result["status"] == "success"
        assert len(result["result"]["evidence_items"]) == 0

    @patch("src.agents.regulatory_twin_tools._get_evidence_service")
    def test_dict_items_handled(self, mock_get_service):
        from src.agents.regulatory_twin_tools import get_evidence_for_device

        mock_service = MagicMock()
        mock_service.get_evidence_for_device.return_value = [
            {"id": "1", "title": "Report A"},
            {"id": "2", "title": "Report B"},
        ]
        mock_get_service.return_value = mock_service

        result = get_evidence_for_device.invoke({"device_version_id": _uuid()})

        assert result["status"] == "success"
        assert result["result"]["evidence_items"][0]["title"] == "Report A"


# ===========================================================================
# EVIDENCE TOOLS — find_unlinked_evidence
# ===========================================================================


class TestFindUnlinkedEvidence:
    """Tests for the find_unlinked_evidence tool."""

    @patch("src.agents.regulatory_twin_tools._get_evidence_service")
    def test_success_with_orphans(self, mock_get_service):
        from src.agents.regulatory_twin_tools import find_unlinked_evidence

        orphan = _make_evidence_item(title="Orphaned report")
        mock_service = MagicMock()
        mock_service.get_unlinked_evidence.return_value = [orphan]
        mock_get_service.return_value = mock_service

        result = find_unlinked_evidence.invoke({"device_version_id": _uuid()})

        assert result["status"] == "success"
        assert result["result"]["unlinked_count"] == 1

    @patch("src.agents.regulatory_twin_tools._get_evidence_service")
    def test_no_orphans(self, mock_get_service):
        from src.agents.regulatory_twin_tools import find_unlinked_evidence

        mock_service = MagicMock()
        mock_service.get_unlinked_evidence.return_value = []
        mock_get_service.return_value = mock_service

        result = find_unlinked_evidence.invoke({"device_version_id": _uuid()})

        assert result["status"] == "success"
        assert result["result"]["unlinked_count"] == 0

    @patch("src.agents.regulatory_twin_tools._get_evidence_service")
    def test_error_handling(self, mock_get_service):
        from src.agents.regulatory_twin_tools import find_unlinked_evidence

        mock_service = MagicMock()
        mock_service.get_unlinked_evidence.side_effect = RuntimeError("Query failed")
        mock_get_service.return_value = mock_service

        result = find_unlinked_evidence.invoke({"device_version_id": _uuid()})

        assert result["status"] == "error"


# ===========================================================================
# ATTESTATION TOOLS — create_attestation
# ===========================================================================


class TestCreateAttestation:
    """Tests for the create_attestation tool."""

    @patch("src.agents.regulatory_twin_tools._get_attestation_service")
    def test_success(self, mock_get_service):
        from src.agents.regulatory_twin_tools import create_attestation

        mock_att = _make_attestation()
        mock_service = MagicMock()
        mock_service.attest_artifact.return_value = mock_att
        mock_get_service.return_value = mock_service

        result = create_attestation.invoke(
            {
                "artifact_id": _uuid(),
                "attested_by": _uuid(),
                "attestation_type": "approved",
                "note": "Looks good",
                "organization_id": _uuid(),
            }
        )

        assert result["status"] == "success"

    @patch("src.agents.regulatory_twin_tools._get_attestation_service")
    def test_invalid_type_returns_error(self, mock_get_service):
        from src.agents.regulatory_twin_tools import create_attestation

        mock_service = MagicMock()
        mock_service.attest_artifact.side_effect = ValueError("Invalid attestation type: 'maybe'")
        mock_get_service.return_value = mock_service

        result = create_attestation.invoke(
            {
                "artifact_id": _uuid(),
                "attested_by": _uuid(),
                "attestation_type": "maybe",
                "note": "Not sure",
                "organization_id": _uuid(),
            }
        )

        assert result["status"] == "error"
        assert "Invalid attestation type" in result["error"]


# ===========================================================================
# ATTESTATION TOOLS — get_pending_attestations
# ===========================================================================


class TestGetPendingAttestations:
    """Tests for the get_pending_attestations tool."""

    @patch("src.agents.regulatory_twin_tools._get_attestation_service")
    def test_success_with_pending(self, mock_get_service):
        from src.agents.regulatory_twin_tools import get_pending_attestations

        pending = [
            {"artifact_id": _uuid(), "title": "AI classification output"},
            {"artifact_id": _uuid(), "title": "Risk analysis draft"},
        ]
        mock_service = MagicMock()
        mock_service.get_unattested_items.return_value = pending
        mock_get_service.return_value = mock_service

        org_id = _uuid()
        result = get_pending_attestations.invoke({"organization_id": org_id})

        assert result["status"] == "success"
        assert result["result"]["pending_count"] == 2
        assert result["result"]["organization_id"] == org_id

    @patch("src.agents.regulatory_twin_tools._get_attestation_service")
    def test_no_pending(self, mock_get_service):
        from src.agents.regulatory_twin_tools import get_pending_attestations

        mock_service = MagicMock()
        mock_service.get_unattested_items.return_value = []
        mock_get_service.return_value = mock_service

        result = get_pending_attestations.invoke({"organization_id": _uuid()})

        assert result["status"] == "success"
        assert result["result"]["pending_count"] == 0


# ===========================================================================
# ATTESTATION TOOLS — get_attestation_trail
# ===========================================================================


class TestGetAttestationTrail:
    """Tests for the get_attestation_trail tool."""

    @patch("src.agents.regulatory_twin_tools._get_attestation_service")
    def test_success_with_trail(self, mock_get_service):
        from src.agents.regulatory_twin_tools import get_attestation_trail

        trail = [_make_attestation(), _make_attestation(attestation_type="reviewed")]
        mock_service = MagicMock()
        mock_service.get_attestation_audit_trail.return_value = trail
        mock_get_service.return_value = mock_service

        art_id = _uuid()
        result = get_attestation_trail.invoke({"artifact_id": art_id})

        assert result["status"] == "success"
        assert result["result"]["artifact_id"] == art_id
        assert result["result"]["attestation_count"] == 2

    @patch("src.agents.regulatory_twin_tools._get_attestation_service")
    def test_empty_trail(self, mock_get_service):
        from src.agents.regulatory_twin_tools import get_attestation_trail

        mock_service = MagicMock()
        mock_service.get_attestation_audit_trail.return_value = []
        mock_get_service.return_value = mock_service

        result = get_attestation_trail.invoke({"artifact_id": _uuid()})

        assert result["status"] == "success"
        assert result["result"]["attestation_count"] == 0

    @patch("src.agents.regulatory_twin_tools._get_attestation_service")
    def test_error_returns_dict(self, mock_get_service):
        from src.agents.regulatory_twin_tools import get_attestation_trail

        mock_service = MagicMock()
        mock_service.get_attestation_audit_trail.side_effect = RuntimeError("DB error")
        mock_get_service.return_value = mock_service

        result = get_attestation_trail.invoke({"artifact_id": _uuid()})

        assert result["status"] == "error"
        assert result["tool"] == "get_attestation_trail"


# ===========================================================================
# GAP DETECTION TOOLS — run_gap_analysis
# ===========================================================================


class TestRunGapAnalysis:
    """Tests for the run_gap_analysis tool."""

    @patch("src.agents.regulatory_twin_tools._get_gap_engine")
    def test_success(self, mock_get_engine):
        from src.agents.regulatory_twin_tools import run_gap_analysis

        mock_report = _make_gap_report()
        mock_engine = MagicMock()
        mock_engine.evaluate.return_value = mock_report
        mock_get_engine.return_value = mock_engine

        result = run_gap_analysis.invoke({"device_version_id": _uuid()})

        assert result["status"] == "success"
        assert result["tool"] == "run_gap_analysis"

    @patch("src.agents.regulatory_twin_tools._get_gap_engine")
    def test_error(self, mock_get_engine):
        from src.agents.regulatory_twin_tools import run_gap_analysis

        mock_engine = MagicMock()
        mock_engine.evaluate.side_effect = ValueError("Device version not found")
        mock_get_engine.return_value = mock_engine

        result = run_gap_analysis.invoke({"device_version_id": _uuid()})

        assert result["status"] == "error"

    @patch("src.agents.regulatory_twin_tools._get_gap_engine")
    def test_dict_report_handled(self, mock_get_engine):
        from src.agents.regulatory_twin_tools import run_gap_analysis

        mock_engine = MagicMock()
        mock_engine.evaluate.return_value = {
            "total_findings": 3,
            "findings": [],
        }
        mock_get_engine.return_value = mock_engine

        result = run_gap_analysis.invoke({"device_version_id": _uuid()})

        assert result["status"] == "success"
        assert result["result"]["total_findings"] == 3


# ===========================================================================
# GAP DETECTION TOOLS — get_critical_gaps
# ===========================================================================


class TestGetCriticalGaps:
    """Tests for the get_critical_gaps tool."""

    @patch("src.agents.regulatory_twin_tools._get_gap_engine")
    def test_success_with_critical_findings(self, mock_get_engine):
        from src.agents.regulatory_twin_tools import get_critical_gaps

        mock_report = _make_gap_report()
        mock_engine = MagicMock()
        mock_engine.evaluate.return_value = mock_report
        mock_get_engine.return_value = mock_engine

        dvid = _uuid()
        result = get_critical_gaps.invoke({"device_version_id": dvid})

        assert result["status"] == "success"
        assert result["result"]["device_version_id"] == dvid
        assert result["result"]["critical_count"] == 1

    @patch("src.agents.regulatory_twin_tools._get_gap_engine")
    def test_no_critical_gaps(self, mock_get_engine):
        from src.agents.regulatory_twin_tools import get_critical_gaps

        report = _make_gap_report(
            findings=[_make_gap_finding(severity="minor")],
            critical_findings=[],
        )
        mock_engine = MagicMock()
        mock_engine.evaluate.return_value = report
        mock_get_engine.return_value = mock_engine

        result = get_critical_gaps.invoke({"device_version_id": _uuid()})

        assert result["status"] == "success"
        assert result["result"]["critical_count"] == 0

    @patch("src.agents.regulatory_twin_tools._get_gap_engine")
    def test_dict_report_filters_critical(self, mock_get_engine):
        from src.agents.regulatory_twin_tools import get_critical_gaps

        # Simulate a report returned as plain dict (no model_dump)
        mock_engine = MagicMock()
        report_dict = {
            "findings": [
                {"severity": "critical", "rule_id": "GAP-001"},
                {"severity": "major", "rule_id": "GAP-003"},
                {"severity": "critical", "rule_id": "GAP-010"},
            ]
        }
        # No critical_findings attribute, no model_dump — pure dict path
        mock_engine.evaluate.return_value = report_dict
        mock_get_engine.return_value = mock_engine

        result = get_critical_gaps.invoke({"device_version_id": _uuid()})

        assert result["status"] == "success"
        assert result["result"]["critical_count"] == 2

    @patch("src.agents.regulatory_twin_tools._get_gap_engine")
    def test_error(self, mock_get_engine):
        from src.agents.regulatory_twin_tools import get_critical_gaps

        mock_engine = MagicMock()
        mock_engine.evaluate.side_effect = RuntimeError("Engine failed")
        mock_get_engine.return_value = mock_engine

        result = get_critical_gaps.invoke({"device_version_id": _uuid()})

        assert result["status"] == "error"


# ===========================================================================
# READINESS ASSESSMENT TOOL
# ===========================================================================


class TestGetReadinessAssessment:
    """Tests for the get_readiness_assessment tool."""

    @patch("src.agents.regulatory_twin_tools._get_readiness_assessment")
    def test_success(self, mock_get_assessment):
        from src.agents.regulatory_twin_tools import get_readiness_assessment

        mock_report = _make_readiness_report()
        mock_assessment = MagicMock()
        mock_assessment.assess.return_value = mock_report
        mock_get_assessment.return_value = mock_assessment

        result = get_readiness_assessment.invoke({"device_version_id": _uuid()})

        assert result["status"] == "success"
        assert result["result"]["overall_readiness_score"] == 0.72

    @patch("src.agents.regulatory_twin_tools._get_readiness_assessment")
    def test_error(self, mock_get_assessment):
        from src.agents.regulatory_twin_tools import get_readiness_assessment

        mock_assessment = MagicMock()
        mock_assessment.assess.side_effect = ValueError("No data")
        mock_get_assessment.return_value = mock_assessment

        result = get_readiness_assessment.invoke({"device_version_id": _uuid()})

        assert result["status"] == "error"

    @patch("src.agents.regulatory_twin_tools._get_readiness_assessment")
    def test_regulatory_safe_summary(self, mock_get_assessment):
        from src.agents.regulatory_twin_tools import get_readiness_assessment

        mock_report = _make_readiness_report(
            summary="Readiness assessment based on configured expectations."
        )
        mock_assessment = MagicMock()
        mock_assessment.assess.return_value = mock_report
        mock_get_assessment.return_value = mock_assessment

        result = get_readiness_assessment.invoke({"device_version_id": _uuid()})

        summary = result["result"]["summary"]
        # Verify regulatory-safe language
        assert "compliant" not in summary.lower()
        assert "ready" not in summary.lower() or "readiness" in summary.lower()
        assert "will pass" not in summary.lower()


# ===========================================================================
# TOOL REGISTRY TESTS
# ===========================================================================


class TestToolRegistry:
    """Tests for the tool registry and get_regulatory_twin_tools()."""

    def test_registry_has_13_tools(self):
        from src.agents.regulatory_twin_tools import REGULATORY_TWIN_TOOLS

        assert len(REGULATORY_TWIN_TOOLS) == 13

    def test_get_regulatory_twin_tools_returns_list(self):
        from src.agents.regulatory_twin_tools import get_regulatory_twin_tools

        tools = get_regulatory_twin_tools()
        assert isinstance(tools, list)
        assert len(tools) == 13

    def test_all_tools_are_langchain_tools(self):
        from langchain_core.tools import BaseTool

        from src.agents.regulatory_twin_tools import REGULATORY_TWIN_TOOLS

        for t in REGULATORY_TWIN_TOOLS:
            assert isinstance(t, BaseTool), f"{t.name} is not a BaseTool"

    def test_all_tools_have_unique_names(self):
        from src.agents.regulatory_twin_tools import REGULATORY_TWIN_TOOLS

        names = [t.name for t in REGULATORY_TWIN_TOOLS]
        assert len(names) == len(set(names)), f"Duplicate tool names: {names}"

    def test_all_tools_have_descriptions(self):
        from src.agents.regulatory_twin_tools import REGULATORY_TWIN_TOOLS

        for t in REGULATORY_TWIN_TOOLS:
            assert t.description, f"Tool {t.name} has no description"
            assert len(t.description) > 20, f"Tool {t.name} description too short"

    def test_expected_tool_names(self):
        from src.agents.regulatory_twin_tools import REGULATORY_TWIN_TOOLS

        expected = {
            "create_trace_link",
            "get_trace_chain",
            "get_coverage_report",
            "validate_trace_relationship",
            "ingest_evidence",
            "get_evidence_for_device",
            "find_unlinked_evidence",
            "create_attestation",
            "get_pending_attestations",
            "get_attestation_trail",
            "run_gap_analysis",
            "get_critical_gaps",
            "get_readiness_assessment",
        }
        actual = {t.name for t in REGULATORY_TWIN_TOOLS}
        assert actual == expected

    def test_get_returns_new_list_each_time(self):
        """Verify get_regulatory_twin_tools returns a copy, not the original."""
        from src.agents.regulatory_twin_tools import get_regulatory_twin_tools

        tools1 = get_regulatory_twin_tools()
        tools2 = get_regulatory_twin_tools()
        assert tools1 is not tools2
        assert tools1 == tools2


# ===========================================================================
# SAFE_CALL TESTS
# ===========================================================================


class TestSafeCall:
    """Tests for the _safe_call error handling wrapper."""

    def test_success_wraps_result(self):
        from src.agents.regulatory_twin_tools import _safe_call

        result = _safe_call("test_tool", lambda: {"data": "ok"})
        assert result["status"] == "success"
        assert result["tool"] == "test_tool"
        assert result["result"]["data"] == "ok"

    def test_value_error_caught(self):
        from src.agents.regulatory_twin_tools import _safe_call

        def _raise():
            raise ValueError("bad input")

        result = _safe_call("test_tool", _raise)
        assert result["status"] == "error"
        assert "bad input" in result["error"]

    def test_runtime_error_caught(self):
        from src.agents.regulatory_twin_tools import _safe_call

        def _raise():
            raise RuntimeError("crash")

        result = _safe_call("test_tool", _raise)
        assert result["status"] == "error"
        assert "Unexpected error" in result["error"]

    def test_never_raises(self):
        """_safe_call must NEVER raise — this is critical for agent stability."""
        from src.agents.regulatory_twin_tools import _safe_call

        def _raise():
            raise Exception("any error")

        # This must NOT raise
        result = _safe_call("test_tool", _raise)
        assert result["status"] == "error"
