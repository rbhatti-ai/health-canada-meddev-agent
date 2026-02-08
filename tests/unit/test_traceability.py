"""
Unit tests for TraceabilityEngine.

Tests link validation, model serialization, chain traversal logic,
coverage report logic, and edge cases.

All tests are pure unit tests — no DB connection required.

Sprint 2a — 2026-02-07
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

# =========================================================================
# Test: VALID_RELATIONSHIPS definition
# =========================================================================


class TestValidRelationships:
    """Test the VALID_RELATIONSHIPS constant."""

    def test_valid_relationships_exists(self) -> None:
        from src.core.traceability import VALID_RELATIONSHIPS

        assert isinstance(VALID_RELATIONSHIPS, dict)
        assert len(VALID_RELATIONSHIPS) > 0

    def test_valid_relationships_has_expected_count(self) -> None:
        from src.core.traceability import VALID_RELATIONSHIPS

        # 9 risk management + 7 design control = 16
        assert len(VALID_RELATIONSHIPS) == 16

    def test_claim_to_hazard_addresses(self) -> None:
        from src.core.traceability import VALID_RELATIONSHIPS

        assert ("claim", "hazard") in VALID_RELATIONSHIPS
        assert "addresses" in VALID_RELATIONSHIPS[("claim", "hazard")]

    def test_claim_to_evidence_supported_by(self) -> None:
        from src.core.traceability import VALID_RELATIONSHIPS

        assert ("claim", "evidence_item") in VALID_RELATIONSHIPS
        assert "supported_by" in VALID_RELATIONSHIPS[("claim", "evidence_item")]

    def test_hazard_to_harm_causes(self) -> None:
        from src.core.traceability import VALID_RELATIONSHIPS

        key = ("hazard", "harm")
        assert key in VALID_RELATIONSHIPS
        assert "causes" in VALID_RELATIONSHIPS[key]
        assert "may_cause" in VALID_RELATIONSHIPS[key]

    def test_hazard_to_risk_control_mitigated_by(self) -> None:
        from src.core.traceability import VALID_RELATIONSHIPS

        assert ("hazard", "risk_control") in VALID_RELATIONSHIPS
        assert "mitigated_by" in VALID_RELATIONSHIPS[("hazard", "risk_control")]

    def test_risk_control_to_verification_test(self) -> None:
        from src.core.traceability import VALID_RELATIONSHIPS

        assert ("risk_control", "verification_test") in VALID_RELATIONSHIPS
        assert "verified_by" in VALID_RELATIONSHIPS[("risk_control", "verification_test")]

    def test_risk_control_to_validation_test(self) -> None:
        from src.core.traceability import VALID_RELATIONSHIPS

        assert ("risk_control", "validation_test") in VALID_RELATIONSHIPS
        assert "validated_by" in VALID_RELATIONSHIPS[("risk_control", "validation_test")]

    def test_verification_test_to_evidence(self) -> None:
        from src.core.traceability import VALID_RELATIONSHIPS

        assert ("verification_test", "evidence_item") in VALID_RELATIONSHIPS
        assert "supported_by" in VALID_RELATIONSHIPS[("verification_test", "evidence_item")]

    def test_validation_test_to_evidence(self) -> None:
        from src.core.traceability import VALID_RELATIONSHIPS

        assert ("validation_test", "evidence_item") in VALID_RELATIONSHIPS
        assert "supported_by" in VALID_RELATIONSHIPS[("validation_test", "evidence_item")]

    def test_evidence_to_artifact(self) -> None:
        from src.core.traceability import VALID_RELATIONSHIPS

        assert ("evidence_item", "artifact") in VALID_RELATIONSHIPS
        assert "documented_in" in VALID_RELATIONSHIPS[("evidence_item", "artifact")]

    # Design control relationships (ISO 13485 7.3)

    def test_design_input_to_design_output_drives(self) -> None:
        from src.core.traceability import VALID_RELATIONSHIPS

        assert ("design_input", "design_output") in VALID_RELATIONSHIPS
        assert "drives" in VALID_RELATIONSHIPS[("design_input", "design_output")]

    def test_design_output_to_design_input_satisfies(self) -> None:
        from src.core.traceability import VALID_RELATIONSHIPS

        assert ("design_output", "design_input") in VALID_RELATIONSHIPS
        assert "satisfies" in VALID_RELATIONSHIPS[("design_output", "design_input")]

    def test_design_output_to_verification_verified_by(self) -> None:
        from src.core.traceability import VALID_RELATIONSHIPS

        assert ("design_output", "design_verification") in VALID_RELATIONSHIPS
        assert "verified_by" in VALID_RELATIONSHIPS[("design_output", "design_verification")]

    def test_design_output_to_validation_validated_by(self) -> None:
        from src.core.traceability import VALID_RELATIONSHIPS

        assert ("design_output", "design_validation") in VALID_RELATIONSHIPS
        assert "validated_by" in VALID_RELATIONSHIPS[("design_output", "design_validation")]

    def test_design_review_to_output_reviews(self) -> None:
        from src.core.traceability import VALID_RELATIONSHIPS

        assert ("design_review", "design_output") in VALID_RELATIONSHIPS
        assert "reviews" in VALID_RELATIONSHIPS[("design_review", "design_output")]

    def test_design_verification_to_evidence_supported_by(self) -> None:
        from src.core.traceability import VALID_RELATIONSHIPS

        assert ("design_verification", "evidence_item") in VALID_RELATIONSHIPS
        assert "supported_by" in VALID_RELATIONSHIPS[("design_verification", "evidence_item")]

    def test_design_validation_to_evidence_supported_by(self) -> None:
        from src.core.traceability import VALID_RELATIONSHIPS

        assert ("design_validation", "evidence_item") in VALID_RELATIONSHIPS
        assert "supported_by" in VALID_RELATIONSHIPS[("design_validation", "evidence_item")]

    def test_all_keys_are_string_tuples(self) -> None:
        from src.core.traceability import VALID_RELATIONSHIPS

        for key in VALID_RELATIONSHIPS:
            assert isinstance(key, tuple)
            assert len(key) == 2
            assert isinstance(key[0], str)
            assert isinstance(key[1], str)

    def test_all_values_are_string_lists(self) -> None:
        from src.core.traceability import VALID_RELATIONSHIPS

        for rels in VALID_RELATIONSHIPS.values():
            assert isinstance(rels, list)
            for rel in rels:
                assert isinstance(rel, str)

    def test_no_self_referencing_relationships(self) -> None:
        """No entity type should link to itself."""
        from src.core.traceability import VALID_RELATIONSHIPS

        for src, tgt in VALID_RELATIONSHIPS:
            assert src != tgt, f"Self-reference found: {src} -> {tgt}"


# =========================================================================
# Test: validate_link (static method)
# =========================================================================


class TestValidateLink:
    """Test the static validate_link method."""

    def test_valid_claim_hazard_addresses(self) -> None:
        from src.core.traceability import TraceabilityEngine

        assert TraceabilityEngine.validate_link("claim", "hazard", "addresses") is True

    def test_valid_hazard_harm_causes(self) -> None:
        from src.core.traceability import TraceabilityEngine

        assert TraceabilityEngine.validate_link("hazard", "harm", "causes") is True

    def test_valid_hazard_harm_may_cause(self) -> None:
        from src.core.traceability import TraceabilityEngine

        assert TraceabilityEngine.validate_link("hazard", "harm", "may_cause") is True

    def test_valid_hazard_risk_control(self) -> None:
        from src.core.traceability import TraceabilityEngine

        assert TraceabilityEngine.validate_link("hazard", "risk_control", "mitigated_by") is True

    def test_valid_risk_control_verification(self) -> None:
        from src.core.traceability import TraceabilityEngine

        assert (
            TraceabilityEngine.validate_link("risk_control", "verification_test", "verified_by")
            is True
        )

    def test_valid_evidence_artifact(self) -> None:
        from src.core.traceability import TraceabilityEngine

        assert (
            TraceabilityEngine.validate_link("evidence_item", "artifact", "documented_in") is True
        )

    def test_invalid_reversed_direction(self) -> None:
        """hazard -> claim is NOT valid (only claim -> hazard)."""
        from src.core.traceability import TraceabilityEngine

        assert TraceabilityEngine.validate_link("hazard", "claim", "addresses") is False

    def test_invalid_unknown_source_type(self) -> None:
        from src.core.traceability import TraceabilityEngine

        assert TraceabilityEngine.validate_link("widget", "claim", "addresses") is False

    def test_invalid_unknown_target_type(self) -> None:
        from src.core.traceability import TraceabilityEngine

        assert TraceabilityEngine.validate_link("claim", "widget", "addresses") is False

    def test_invalid_wrong_relationship(self) -> None:
        """claim -> hazard with 'mitigated_by' is not valid."""
        from src.core.traceability import TraceabilityEngine

        assert TraceabilityEngine.validate_link("claim", "hazard", "mitigated_by") is False

    def test_invalid_empty_strings(self) -> None:
        from src.core.traceability import TraceabilityEngine

        assert TraceabilityEngine.validate_link("", "", "") is False

    def test_invalid_none_like_strings(self) -> None:
        from src.core.traceability import TraceabilityEngine

        assert TraceabilityEngine.validate_link("none", "none", "none") is False

    def test_all_valid_relationships_pass_validation(self) -> None:
        """Every entry in VALID_RELATIONSHIPS should pass validate_link."""
        from src.core.traceability import VALID_RELATIONSHIPS, TraceabilityEngine

        for (src, tgt), rels in VALID_RELATIONSHIPS.items():
            for rel in rels:
                assert (
                    TraceabilityEngine.validate_link(src, tgt, rel) is True
                ), f"Expected valid: {src} -[{rel}]-> {tgt}"


# =========================================================================
# Test: get_valid_relationships helpers
# =========================================================================


class TestGetValidRelationships:
    """Test helper methods for relationship queries."""

    def test_get_valid_relationships_returns_dict(self) -> None:
        from src.core.traceability import TraceabilityEngine

        result = TraceabilityEngine.get_valid_relationships()
        assert isinstance(result, dict)
        # 9 risk management + 7 design control = 16
        assert len(result) == 16

    def test_get_valid_relationships_is_copy(self) -> None:
        """Returned dict should be a copy, not the original."""
        from src.core.traceability import VALID_RELATIONSHIPS, TraceabilityEngine

        result = TraceabilityEngine.get_valid_relationships()
        assert result is not VALID_RELATIONSHIPS
        assert result == VALID_RELATIONSHIPS

    def test_get_valid_for_claim_source(self) -> None:
        from src.core.traceability import TraceabilityEngine

        result = TraceabilityEngine.get_valid_relationships_for_source("claim")
        assert "hazard" in result
        assert "evidence_item" in result
        assert len(result) == 2

    def test_get_valid_for_hazard_source(self) -> None:
        from src.core.traceability import TraceabilityEngine

        result = TraceabilityEngine.get_valid_relationships_for_source("hazard")
        assert "harm" in result
        assert "risk_control" in result
        assert len(result) == 2

    def test_get_valid_for_risk_control_source(self) -> None:
        from src.core.traceability import TraceabilityEngine

        result = TraceabilityEngine.get_valid_relationships_for_source("risk_control")
        assert "verification_test" in result
        assert "validation_test" in result

    def test_get_valid_for_unknown_source(self) -> None:
        from src.core.traceability import TraceabilityEngine

        result = TraceabilityEngine.get_valid_relationships_for_source("widget")
        assert result == {}

    def test_get_valid_for_artifact_source(self) -> None:
        """artifact is only a target, never a source."""
        from src.core.traceability import TraceabilityEngine

        result = TraceabilityEngine.get_valid_relationships_for_source("artifact")
        assert result == {}


# =========================================================================
# Test: TraceLink Pydantic model
# =========================================================================


class TestTraceLinkModel:
    """Test TraceLink Pydantic model."""

    def _make_link(self, **overrides: Any):
        from src.core.traceability import TraceLink

        defaults: dict[str, Any] = {
            "organization_id": uuid4(),
            "source_type": "claim",
            "source_id": uuid4(),
            "target_type": "hazard",
            "target_id": uuid4(),
            "relationship": "addresses",
        }
        defaults.update(overrides)
        return TraceLink(**defaults)

    def test_create_minimal(self) -> None:
        link = self._make_link()
        assert link.source_type == "claim"
        assert link.target_type == "hazard"
        assert link.relationship == "addresses"

    def test_id_defaults_to_none(self) -> None:
        link = self._make_link()
        assert link.id is None

    def test_created_at_defaults_to_none(self) -> None:
        link = self._make_link()
        assert link.created_at is None

    def test_rationale_defaults_to_none(self) -> None:
        link = self._make_link()
        assert link.rationale is None

    def test_metadata_defaults_to_empty_dict(self) -> None:
        link = self._make_link()
        assert link.metadata == {}

    def test_to_db_dict_excludes_id(self) -> None:
        link = self._make_link()
        data = link.to_db_dict()
        assert "id" not in data

    def test_to_db_dict_excludes_created_at(self) -> None:
        link = self._make_link()
        data = link.to_db_dict()
        assert "created_at" not in data

    def test_to_db_dict_converts_uuid_to_str(self) -> None:
        org_id = uuid4()
        link = self._make_link(organization_id=org_id)
        data = link.to_db_dict()
        assert data["organization_id"] == str(org_id)

    def test_to_db_dict_includes_rationale_when_set(self) -> None:
        link = self._make_link(rationale="Risk mitigation per ISO 14971")
        data = link.to_db_dict()
        assert data["rationale"] == "Risk mitigation per ISO 14971"

    def test_to_db_dict_excludes_none_created_by(self) -> None:
        link = self._make_link(created_by=None)
        data = link.to_db_dict()
        assert "created_by" not in data

    def test_to_db_dict_includes_metadata(self) -> None:
        link = self._make_link(metadata={"note": "test"})
        data = link.to_db_dict()
        assert data["metadata"] == {"note": "test"}

    def test_from_db_row(self) -> None:
        from src.core.traceability import TraceLink

        row = {
            "id": str(uuid4()),
            "organization_id": str(uuid4()),
            "source_type": "claim",
            "source_id": str(uuid4()),
            "target_type": "hazard",
            "target_id": str(uuid4()),
            "relationship": "addresses",
            "rationale": "test rationale",
            "metadata": {"key": "value"},
            "created_at": "2026-02-07T12:00:00+00:00",
        }
        link = TraceLink.from_db_row(row)
        assert link.source_type == "claim"
        assert link.rationale == "test rationale"

    def test_from_db_row_ignores_extra_fields(self) -> None:
        from src.core.traceability import TraceLink

        row = {
            "id": str(uuid4()),
            "organization_id": str(uuid4()),
            "source_type": "claim",
            "source_id": str(uuid4()),
            "target_type": "hazard",
            "target_id": str(uuid4()),
            "relationship": "addresses",
            "metadata": {},
            "extra_field": "should be ignored",
        }
        link = TraceLink.from_db_row(row)
        assert link.source_type == "claim"


# =========================================================================
# Test: TraceChain model
# =========================================================================


class TestTraceChainModel:
    """Test TraceChain and TraceChainNode models."""

    def test_empty_chain(self) -> None:
        from src.core.traceability import TraceChain

        chain = TraceChain(root_type="claim", root_id=uuid4())
        assert chain.nodes == []
        assert chain.total_links == 0
        assert chain.max_depth == 0

    def test_chain_with_nodes(self) -> None:
        from src.core.traceability import TraceChain, TraceChainNode

        child = TraceChainNode(
            entity_type="hazard",
            entity_id=uuid4(),
            relationship="addresses",
        )
        chain = TraceChain(
            root_type="claim",
            root_id=uuid4(),
            nodes=[child],
            total_links=1,
            max_depth=1,
        )
        assert len(chain.nodes) == 1
        assert chain.nodes[0].entity_type == "hazard"

    def test_nested_nodes(self) -> None:
        from src.core.traceability import TraceChainNode

        evidence = TraceChainNode(
            entity_type="evidence_item",
            entity_id=uuid4(),
            relationship="supported_by",
        )
        test = TraceChainNode(
            entity_type="verification_test",
            entity_id=uuid4(),
            relationship="verified_by",
            children=[evidence],
        )
        assert len(test.children) == 1
        assert test.children[0].entity_type == "evidence_item"


# =========================================================================
# Test: CoverageReport model
# =========================================================================


class TestCoverageReportModel:
    """Test CoverageReport and ClaimCoverage models."""

    def test_empty_coverage_report(self) -> None:
        from src.core.traceability import CoverageReport

        report = CoverageReport(device_version_id=uuid4())
        assert report.total_claims == 0
        assert report.coverage_percentage == 0.0
        assert report.claims == []

    def test_claim_coverage_defaults(self) -> None:
        from src.core.traceability import ClaimCoverage

        coverage = ClaimCoverage(claim_id=uuid4())
        assert coverage.hazards == []
        assert coverage.risk_controls == []
        assert coverage.verification_tests == []
        assert coverage.validation_tests == []
        assert coverage.evidence_items == []
        assert coverage.has_hazard_link is False
        assert coverage.has_control_link is False
        assert coverage.has_test_link is False
        assert coverage.has_evidence_link is False

    def test_claim_coverage_with_full_chain(self) -> None:
        from src.core.traceability import ClaimCoverage

        coverage = ClaimCoverage(
            claim_id=uuid4(),
            hazards=[uuid4()],
            risk_controls=[uuid4()],
            verification_tests=[uuid4()],
            evidence_items=[uuid4()],
            has_hazard_link=True,
            has_control_link=True,
            has_test_link=True,
            has_evidence_link=True,
        )
        assert coverage.has_hazard_link is True
        assert coverage.has_control_link is True
        assert coverage.has_test_link is True
        assert coverage.has_evidence_link is True

    def test_coverage_report_with_mixed_claims(self) -> None:
        from src.core.traceability import CoverageReport

        report = CoverageReport(
            device_version_id=uuid4(),
            total_claims=3,
            claims_with_full_coverage=1,
            claims_with_partial_coverage=1,
            claims_with_no_coverage=1,
            coverage_percentage=33.3,
        )
        assert report.total_claims == 3
        assert report.coverage_percentage == 33.3


# =========================================================================
# Test: TraceabilityEngine instantiation
# =========================================================================


class TestTraceabilityEngineInit:
    """Test engine construction and singleton."""

    def test_engine_creates(self) -> None:
        from src.core.traceability import TraceabilityEngine

        engine = TraceabilityEngine()
        assert engine is not None

    def test_singleton_returns_same_instance(self) -> None:
        # Reset singleton for test isolation
        import src.core.traceability as mod
        from src.core.traceability import get_traceability_engine

        mod._engine = None

        engine1 = get_traceability_engine()
        engine2 = get_traceability_engine()
        assert engine1 is engine2

        # Clean up
        mod._engine = None

    def test_engine_has_table_constant(self) -> None:
        from src.core.traceability import TraceabilityEngine

        assert TraceabilityEngine.TABLE == "trace_links"

    def test_compute_depth_empty(self) -> None:
        from src.core.traceability import TraceabilityEngine

        engine = TraceabilityEngine()
        assert engine._compute_depth([]) == 0

    def test_compute_depth_one_level(self) -> None:
        from src.core.traceability import TraceabilityEngine, TraceChainNode

        engine = TraceabilityEngine()
        nodes = [
            TraceChainNode(entity_type="hazard", entity_id=uuid4()),
        ]
        assert engine._compute_depth(nodes) == 1

    def test_compute_depth_nested(self) -> None:
        from src.core.traceability import TraceabilityEngine, TraceChainNode

        engine = TraceabilityEngine()
        leaf = TraceChainNode(entity_type="evidence_item", entity_id=uuid4())
        mid = TraceChainNode(
            entity_type="verification_test",
            entity_id=uuid4(),
            children=[leaf],
        )
        top = TraceChainNode(
            entity_type="hazard",
            entity_id=uuid4(),
            children=[mid],
        )
        assert engine._compute_depth([top]) == 3
