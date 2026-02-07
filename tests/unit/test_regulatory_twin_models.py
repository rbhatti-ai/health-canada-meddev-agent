"""
Unit tests for Regulatory Twin Pydantic models.

Tests validate:
  - All 10 models instantiate with valid data
  - Required fields enforced
  - Literal type constraints reject invalid values
  - Default values correct
  - Version field enforces ge=1
  - to_db_dict() serialization
  - from_db_row() deserialization
  - TWIN_MODEL_REGISTRY completeness

Sprint 1b — 2026-02-07
"""

from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.core.regulatory_twin import (
    TWIN_MODEL_REGISTRY,
    Claim,
    EvidenceItem,
    Harm,
    Hazard,
    IntendedUse,
    LabelingAsset,
    RiskControl,
    SubmissionTarget,
    ValidationTest,
    VerificationTest,
)

# =========================================================================
# Shared fixtures
# =========================================================================

ORG_ID = uuid4()
DEVICE_VERSION_ID = uuid4()
USER_ID = uuid4()
HAZARD_ID = uuid4()
ARTIFACT_ID = uuid4()


# =========================================================================
# IntendedUse
# =========================================================================
@pytest.mark.unit
class TestIntendedUse:
    def test_valid_creation(self):
        iu = IntendedUse(
            organization_id=ORG_ID,
            device_version_id=DEVICE_VERSION_ID,
            statement="Monitor blood pressure in adults",
        )
        assert iu.statement == "Monitor blood pressure in adults"
        assert iu.version == 1
        assert iu.indications == []
        assert iu.contraindications == []

    def test_missing_statement_fails(self):
        with pytest.raises(ValidationError):
            IntendedUse(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                statement="",
            )

    def test_missing_org_id_fails(self):
        with pytest.raises(ValidationError):
            IntendedUse(
                device_version_id=DEVICE_VERSION_ID,
                statement="Monitor blood pressure",
            )

    def test_with_all_fields(self):
        iu = IntendedUse(
            organization_id=ORG_ID,
            device_version_id=DEVICE_VERSION_ID,
            statement="Monitor blood pressure",
            indications=["hypertension screening"],
            contraindications=["children under 3"],
            target_population="Adults 18+",
            use_environment="Clinical",
            created_by=USER_ID,
            version=2,
            supersedes_id=uuid4(),
        )
        assert iu.version == 2
        assert len(iu.indications) == 1

    def test_to_db_dict(self):
        iu = IntendedUse(
            organization_id=ORG_ID,
            device_version_id=DEVICE_VERSION_ID,
            statement="Test statement",
        )
        d = iu.to_db_dict()
        assert isinstance(d["organization_id"], str)
        assert d["statement"] == "Test statement"
        assert "id" not in d  # None excluded
        assert "created_at" not in d  # None excluded

    def test_from_db_row(self):
        row = {
            "id": str(uuid4()),
            "organization_id": str(ORG_ID),
            "device_version_id": str(DEVICE_VERSION_ID),
            "statement": "From DB",
            "indications": ["a"],
            "contraindications": [],
            "target_population": None,
            "use_environment": None,
            "created_by": None,
            "version": 1,
            "supersedes_id": None,
            "created_at": "2026-02-07T00:00:00+00:00",
        }
        iu = IntendedUse.from_db_row(row)
        assert iu.statement == "From DB"


# =========================================================================
# Claim
# =========================================================================
@pytest.mark.unit
class TestClaim:
    def test_valid_creation(self):
        c = Claim(
            organization_id=ORG_ID,
            device_version_id=DEVICE_VERSION_ID,
            claim_type="safety",
            statement="Device does not cause burns",
        )
        assert c.status == "draft"
        assert c.claim_type == "safety"

    def test_invalid_claim_type(self):
        with pytest.raises(ValidationError):
            Claim(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                claim_type="invalid_type",
                statement="Test",
            )

    def test_invalid_status(self):
        with pytest.raises(ValidationError):
            Claim(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                claim_type="safety",
                statement="Test",
                status="bogus",
            )

    def test_all_claim_types(self):
        for ct in [
            "safety",
            "performance",
            "usability",
            "biocompatibility",
            "sterility",
            "shelf_life",
            "software_performance",
            "other",
        ]:
            c = Claim(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                claim_type=ct,
                statement=f"Claim for {ct}",
            )
            assert c.claim_type == ct

    def test_all_statuses(self):
        for s in ["draft", "under_review", "accepted", "rejected", "superseded"]:
            c = Claim(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                claim_type="safety",
                statement="Test",
                status=s,
            )
            assert c.status == s

    def test_version_must_be_positive(self):
        with pytest.raises(ValidationError):
            Claim(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                claim_type="safety",
                statement="Test",
                version=0,
            )


# =========================================================================
# Hazard
# =========================================================================
@pytest.mark.unit
class TestHazard:
    def test_valid_creation(self):
        h = Hazard(
            organization_id=ORG_ID,
            device_version_id=DEVICE_VERSION_ID,
            hazard_category="software",
            description="Algorithm produces incorrect output",
        )
        assert h.hazard_category == "software"
        assert h.severity is None

    def test_invalid_category(self):
        with pytest.raises(ValidationError):
            Hazard(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                hazard_category="magic",
                description="Test",
            )

    def test_all_categories(self):
        cats = [
            "electrical",
            "biological",
            "chemical",
            "mechanical",
            "thermal",
            "radiation",
            "software",
            "use_error",
            "cybersecurity",
            "environmental",
            "other",
        ]
        for cat in cats:
            h = Hazard(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                hazard_category=cat,
                description=f"Hazard: {cat}",
            )
            assert h.hazard_category == cat

    def test_severity_values(self):
        for s in ["negligible", "marginal", "critical", "catastrophic"]:
            h = Hazard(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                hazard_category="software",
                description="Test",
                severity=s,
            )
            assert h.severity == s

    def test_invalid_severity(self):
        with pytest.raises(ValidationError):
            Hazard(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                hazard_category="software",
                description="Test",
                severity="extreme",
            )

    def test_probability_values(self):
        for p in ["improbable", "remote", "occasional", "probable", "frequent"]:
            h = Hazard(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                hazard_category="software",
                description="Test",
                probability=p,
            )
            assert h.probability == p

    def test_risk_level_values(self):
        for r in ["low", "medium", "high", "unacceptable"]:
            h = Hazard(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                hazard_category="software",
                description="Test",
                risk_level_pre=r,
            )
            assert h.risk_level_pre == r


# =========================================================================
# Harm
# =========================================================================
@pytest.mark.unit
class TestHarm:
    def test_valid_creation(self):
        h = Harm(
            organization_id=ORG_ID,
            hazard_id=HAZARD_ID,
            harm_type="injury",
            description="Patient receives incorrect dosage",
            severity="critical",
        )
        assert h.severity == "critical"

    def test_missing_severity_fails(self):
        with pytest.raises(ValidationError):
            Harm(
                organization_id=ORG_ID,
                hazard_id=HAZARD_ID,
                harm_type="injury",
                description="Test",
            )

    def test_all_harm_types(self):
        for ht in [
            "injury",
            "death",
            "misdiagnosis",
            "delayed_treatment",
            "unnecessary_treatment",
            "infection",
            "tissue_damage",
            "psychological",
            "financial",
            "other",
        ]:
            h = Harm(
                organization_id=ORG_ID,
                hazard_id=HAZARD_ID,
                harm_type=ht,
                description=f"Harm: {ht}",
                severity="marginal",
            )
            assert h.harm_type == ht

    def test_no_version_field(self):
        """Harms are not versioned (linked to specific hazard version)."""
        h = Harm(
            organization_id=ORG_ID,
            hazard_id=HAZARD_ID,
            harm_type="injury",
            description="Test",
            severity="negligible",
        )
        assert not hasattr(h, "version") or "version" not in h.model_fields


# =========================================================================
# RiskControl
# =========================================================================
@pytest.mark.unit
class TestRiskControl:
    def test_valid_creation(self):
        rc = RiskControl(
            organization_id=ORG_ID,
            hazard_id=HAZARD_ID,
            control_type="inherent_safety",
            description="Remove sharp edges",
        )
        assert rc.implementation_status == "planned"

    def test_iso14971_hierarchy(self):
        """ISO 14971 requires controls in order: inherent > protective > info."""
        for ct in [
            "inherent_safety",
            "protective_measure",
            "information_for_safety",
        ]:
            rc = RiskControl(
                organization_id=ORG_ID,
                hazard_id=HAZARD_ID,
                control_type=ct,
                description=f"Control: {ct}",
            )
            assert rc.control_type == ct

    def test_invalid_control_type(self):
        with pytest.raises(ValidationError):
            RiskControl(
                organization_id=ORG_ID,
                hazard_id=HAZARD_ID,
                control_type="magic_shield",
                description="Test",
            )

    def test_implementation_statuses(self):
        for s in ["planned", "in_progress", "implemented", "verified", "retired"]:
            rc = RiskControl(
                organization_id=ORG_ID,
                hazard_id=HAZARD_ID,
                control_type="inherent_safety",
                description="Test",
                implementation_status=s,
            )
            assert rc.implementation_status == s


# =========================================================================
# VerificationTest
# =========================================================================
@pytest.mark.unit
class TestVerificationTest:
    def test_valid_creation(self):
        vt = VerificationTest(
            organization_id=ORG_ID,
            device_version_id=DEVICE_VERSION_ID,
            test_type="software",
            title="Unit test coverage",
            acceptance_criteria=">=90% coverage",
        )
        assert vt.pass_fail is None

    def test_all_test_types(self):
        for tt in [
            "bench",
            "software",
            "biocompatibility",
            "electrical_safety",
            "emc",
            "sterilization",
            "packaging",
            "shelf_life",
            "cybersecurity",
            "other",
        ]:
            vt = VerificationTest(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                test_type=tt,
                title=f"Test: {tt}",
                acceptance_criteria="Must pass",
            )
            assert vt.test_type == tt

    def test_pass_fail_values(self):
        for pf in ["pass", "fail", "conditional", "pending"]:
            vt = VerificationTest(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                test_type="bench",
                title="Test",
                acceptance_criteria="Pass",
                pass_fail=pf,
            )
            assert vt.pass_fail == pf


# =========================================================================
# ValidationTest
# =========================================================================
@pytest.mark.unit
class TestValidationTest:
    def test_valid_creation(self):
        vt = ValidationTest(
            organization_id=ORG_ID,
            device_version_id=DEVICE_VERSION_ID,
            test_type="usability",
            title="Summative usability study",
            acceptance_criteria="Task success rate >= 95%",
        )
        assert vt.participant_count is None

    def test_with_participants(self):
        vt = ValidationTest(
            organization_id=ORG_ID,
            device_version_id=DEVICE_VERSION_ID,
            test_type="summative",
            title="Study",
            acceptance_criteria="Pass",
            participant_count=30,
        )
        assert vt.participant_count == 30

    def test_negative_participants_fails(self):
        with pytest.raises(ValidationError):
            ValidationTest(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                test_type="usability",
                title="Study",
                acceptance_criteria="Pass",
                participant_count=-1,
            )

    def test_all_validation_types(self):
        for tt in [
            "usability",
            "clinical_investigation",
            "clinical_evaluation",
            "simulated_use",
            "formative",
            "summative",
            "other",
        ]:
            vt = ValidationTest(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                test_type=tt,
                title=f"Test: {tt}",
                acceptance_criteria="Pass",
            )
            assert vt.test_type == tt


# =========================================================================
# EvidenceItem
# =========================================================================
@pytest.mark.unit
class TestEvidenceItem:
    def test_valid_creation(self):
        ei = EvidenceItem(
            organization_id=ORG_ID,
            device_version_id=DEVICE_VERSION_ID,
            evidence_type="test_report",
            title="Biocompatibility test report",
        )
        assert ei.strength == "moderate"
        assert ei.status == "draft"

    def test_all_evidence_types(self):
        for et in [
            "test_report",
            "literature_review",
            "clinical_data",
            "standard_reference",
            "predicate_comparison",
            "risk_analysis",
            "design_output",
            "manufacturing_record",
            "post_market_data",
            "expert_opinion",
            "other",
        ]:
            ei = EvidenceItem(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                evidence_type=et,
                title=f"Evidence: {et}",
            )
            assert ei.evidence_type == et

    def test_strength_values(self):
        for s in ["strong", "moderate", "weak", "insufficient"]:
            ei = EvidenceItem(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                evidence_type="test_report",
                title="Test",
                strength=s,
            )
            assert ei.strength == s

    def test_with_artifact(self):
        ei = EvidenceItem(
            organization_id=ORG_ID,
            device_version_id=DEVICE_VERSION_ID,
            evidence_type="test_report",
            title="Test",
            artifact_id=ARTIFACT_ID,
        )
        assert ei.artifact_id == ARTIFACT_ID


# =========================================================================
# LabelingAsset
# =========================================================================
@pytest.mark.unit
class TestLabelingAsset:
    def test_valid_creation(self):
        la = LabelingAsset(
            organization_id=ORG_ID,
            device_version_id=DEVICE_VERSION_ID,
            asset_type="ifu",
            title="Instructions for Use v1",
        )
        assert la.language == "en"
        assert la.status == "draft"

    def test_all_asset_types(self):
        for at in [
            "ifu",
            "label",
            "packaging",
            "e_labeling",
            "quick_reference",
            "patient_information",
            "surgical_technique",
            "other",
        ]:
            la = LabelingAsset(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                asset_type=at,
                title=f"Asset: {at}",
            )
            assert la.asset_type == at

    def test_regulatory_markets(self):
        for m in ["CA", "US", "EU", "UK", "AU", "JP", "CN", "other"]:
            la = LabelingAsset(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                asset_type="label",
                title="Test",
                regulatory_market=m,
            )
            assert la.regulatory_market == m

    def test_invalid_market(self):
        with pytest.raises(ValidationError):
            LabelingAsset(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                asset_type="label",
                title="Test",
                regulatory_market="XX",
            )


# =========================================================================
# SubmissionTarget
# =========================================================================
@pytest.mark.unit
class TestSubmissionTarget:
    def test_valid_creation(self):
        st = SubmissionTarget(
            organization_id=ORG_ID,
            device_version_id=DEVICE_VERSION_ID,
            regulatory_body="health_canada",
            submission_type="mdl",
        )
        assert st.status == "planning"

    def test_all_regulatory_bodies(self):
        for rb in [
            "health_canada",
            "fda",
            "eu_mdr",
            "mhra",
            "tga",
            "pmda",
            "nmpa",
            "other",
        ]:
            st = SubmissionTarget(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                regulatory_body=rb,
                submission_type="other",
            )
            assert st.regulatory_body == rb

    def test_all_submission_types(self):
        for stype in [
            "mdl",
            "510k",
            "de_novo",
            "pma",
            "ce_mark",
            "ukca",
            "tga_inclusion",
            "shonin",
            "other",
        ]:
            st = SubmissionTarget(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                regulatory_body="fda",
                submission_type=stype,
            )
            assert st.submission_type == stype

    def test_all_statuses(self):
        for s in [
            "planning",
            "preparing",
            "submitted",
            "under_review",
            "approved",
            "rejected",
            "withdrawn",
        ]:
            st = SubmissionTarget(
                organization_id=ORG_ID,
                device_version_id=DEVICE_VERSION_ID,
                regulatory_body="health_canada",
                submission_type="mdl",
                status=s,
            )
            assert st.status == s

    def test_with_target_date(self):
        st = SubmissionTarget(
            organization_id=ORG_ID,
            device_version_id=DEVICE_VERSION_ID,
            regulatory_body="health_canada",
            submission_type="mdl",
            target_date=date(2026, 6, 15),
        )
        assert st.target_date == date(2026, 6, 15)


# =========================================================================
# Serialization round-trip
# =========================================================================
@pytest.mark.unit
class TestSerialization:
    def test_to_db_dict_excludes_none(self):
        c = Claim(
            organization_id=ORG_ID,
            device_version_id=DEVICE_VERSION_ID,
            claim_type="safety",
            statement="Test",
        )
        d = c.to_db_dict()
        assert "id" not in d
        assert "created_at" not in d
        assert "evidence_basis" not in d

    def test_to_db_dict_converts_uuid(self):
        c = Claim(
            organization_id=ORG_ID,
            device_version_id=DEVICE_VERSION_ID,
            claim_type="safety",
            statement="Test",
        )
        d = c.to_db_dict()
        assert isinstance(d["organization_id"], str)

    def test_from_db_row_round_trip(self):
        original = Hazard(
            id=uuid4(),
            organization_id=ORG_ID,
            device_version_id=DEVICE_VERSION_ID,
            hazard_category="cybersecurity",
            description="Unauthorized access",
            severity="critical",
            version=3,
        )
        row = original.to_db_dict()
        restored = Hazard.from_db_row(row)
        assert restored.hazard_category == "cybersecurity"
        assert restored.severity == "critical"
        assert restored.version == 3


# =========================================================================
# Registry
# =========================================================================
@pytest.mark.unit
class TestRegistry:
    def test_registry_has_10_entries(self):
        assert len(TWIN_MODEL_REGISTRY) == 10

    def test_registry_keys_match_tables(self):
        expected = {
            "intended_uses",
            "claims",
            "hazards",
            "harms",
            "risk_controls",
            "verification_tests",
            "validation_tests",
            "evidence_items",
            "labeling_assets",
            "submission_targets",
        }
        assert set(TWIN_MODEL_REGISTRY.keys()) == expected

    def test_registry_values_are_classes(self):
        for name, cls in TWIN_MODEL_REGISTRY.items():
            assert isinstance(cls, type), f"{name} is not a class"
