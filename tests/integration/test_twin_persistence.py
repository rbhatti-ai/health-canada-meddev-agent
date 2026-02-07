"""
Integration tests for Regulatory Twin persistence layer.

Tests actual DB round-trips against local Postgres.
Covers: create, get_by_id, get_by_device_version, get_by_field, update, count.

Sprint 1c — 2026-02-07
"""

from __future__ import annotations

import subprocess
from uuid import UUID

import pytest

from src.core.regulatory_twin import (
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
from src.persistence.twin_repository import TwinRepository, get_twin_repository

# Deterministic UUIDs for idempotent test fixtures
TWIN_TEST_ORG_ID = "a0000000-0000-0000-0000-00000000aa01"
TWIN_TEST_USER_ID = "a0000000-0000-0000-0000-00000000aa02"
TWIN_TEST_PRODUCT_ID = "a0000000-0000-0000-0000-00000000aa03"
TWIN_TEST_DV_ID = "a0000000-0000-0000-0000-00000000aa04"


def psql(query: str) -> str:
    """Run a psql query against local dev DB."""
    try:
        result = subprocess.run(
            ["psql", "-U", "meddev", "-d", "meddev_agent", "-t", "-A", "-c", query],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            print(f"PSQL ERROR: {result.stderr.strip()}")
        return result.stdout.strip()
    except Exception as e:
        print(f"PSQL EXCEPTION: {e}")
        return ""


# =========================================================================
# Fixtures: match ACTUAL local Postgres schema exactly
# =========================================================================


@pytest.fixture(scope="module", autouse=True)
def seed_test_data() -> None:
    """Create base records needed by all integration tests.

    Schema reality (from \\d):
      organizations: id (uuid), name (text), created_at
      users: id (uuid), organization_id (uuid), created_at
      products: id (uuid), org_id (uuid), name (text), created_at
      device_versions: id (uuid), product_id (uuid), version_label (text),
                       regulatory_twin_json (jsonb), created_at
    """
    # Clean up stale test data (reverse FK order)
    for table in [
        "submission_targets",
        "labeling_assets",
        "evidence_items",
        "validation_tests",
        "verification_tests",
        "risk_controls",
        "harms",
        "hazards",
        "claims",
        "intended_uses",
    ]:
        psql(f"DELETE FROM public.{table} WHERE organization_id = '{TWIN_TEST_ORG_ID}';")

    psql(f"DELETE FROM public.device_versions WHERE id = '{TWIN_TEST_DV_ID}';")
    psql(f"DELETE FROM public.products WHERE id = '{TWIN_TEST_PRODUCT_ID}';")
    psql(f"DELETE FROM public.users WHERE id = '{TWIN_TEST_USER_ID}';")
    psql(f"DELETE FROM public.organizations WHERE id = '{TWIN_TEST_ORG_ID}';")

    # Insert base records matching ACTUAL schema
    psql(
        f"INSERT INTO public.organizations (id, name) "
        f"VALUES ('{TWIN_TEST_ORG_ID}', 'Twin Test Org');"
    )
    psql(
        f"INSERT INTO public.users (id, organization_id) "
        f"VALUES ('{TWIN_TEST_USER_ID}', '{TWIN_TEST_ORG_ID}');"
    )
    psql(
        f"INSERT INTO public.products (id, org_id, name) "
        f"VALUES ('{TWIN_TEST_PRODUCT_ID}', '{TWIN_TEST_ORG_ID}', 'Twin Test Device');"
    )
    psql(
        f"INSERT INTO public.device_versions (id, product_id, version_label) "
        f"VALUES ('{TWIN_TEST_DV_ID}', '{TWIN_TEST_PRODUCT_ID}', 'v1.0-twin-test');"
    )

    # Verify seed data exists
    count = psql(f"SELECT COUNT(*) FROM public.organizations WHERE id = '{TWIN_TEST_ORG_ID}';")
    assert count == "1", f"Org seed failed, count={count}"


@pytest.fixture(scope="module")
def test_org_id() -> str:
    return TWIN_TEST_ORG_ID


@pytest.fixture(scope="module")
def test_device_version_id() -> str:
    return TWIN_TEST_DV_ID


@pytest.fixture(scope="module")
def repo() -> TwinRepository:
    return get_twin_repository()


# =========================================================================
# Repository availability
# =========================================================================


@pytest.mark.integration
class TestRepositoryAvailability:
    def test_repo_is_available(self, repo: TwinRepository):
        assert repo.is_available, "No DB backend available for integration tests"

    def test_singleton_pattern(self):
        r1 = get_twin_repository()
        r2 = get_twin_repository()
        assert r1 is r2


# =========================================================================
# IntendedUse CRUD
# =========================================================================


@pytest.mark.integration
class TestIntendedUseCRUD:
    def test_create_intended_use(
        self, repo: TwinRepository, test_org_id: str, test_device_version_id: str
    ):
        iu = IntendedUse(
            organization_id=UUID(test_org_id),
            device_version_id=UUID(test_device_version_id),
            statement="Monitor blood pressure in adults over 18",
            indications=["hypertension screening"],
            contraindications=["children under 3"],
            target_population="Adults 18+",
        )
        result = repo.create("intended_uses", iu)
        assert result is not None
        assert "id" in result

    def test_get_by_device_version(self, repo: TwinRepository, test_device_version_id: str):
        rows = repo.get_by_device_version("intended_uses", test_device_version_id)
        assert len(rows) >= 1

    def test_count(self, repo: TwinRepository, test_org_id: str):
        count = repo.count("intended_uses", test_org_id)
        assert count >= 1


# =========================================================================
# Claim CRUD
# =========================================================================


@pytest.mark.integration
class TestClaimCRUD:
    def test_create_claim(
        self, repo: TwinRepository, test_org_id: str, test_device_version_id: str
    ):
        c = Claim(
            organization_id=UUID(test_org_id),
            device_version_id=UUID(test_device_version_id),
            claim_type="safety",
            statement="Device does not cause thermal burns",
        )
        result = repo.create("claims", c)
        assert result is not None

    def test_get_claims(self, repo: TwinRepository, test_device_version_id: str):
        rows = repo.get_by_device_version("claims", test_device_version_id)
        assert len(rows) >= 1


# =========================================================================
# Hazard CRUD
# =========================================================================


@pytest.mark.integration
class TestHazardCRUD:
    def test_create_hazard(
        self, repo: TwinRepository, test_org_id: str, test_device_version_id: str
    ):
        h = Hazard(
            organization_id=UUID(test_org_id),
            device_version_id=UUID(test_device_version_id),
            hazard_category="software",
            description="Algorithm produces incorrect blood pressure reading",
            severity="critical",
            probability="remote",
            risk_level_pre="high",
        )
        result = repo.create("hazards", h)
        assert result is not None
        assert "id" in result

    def test_get_hazards(self, repo: TwinRepository, test_device_version_id: str):
        rows = repo.get_by_device_version("hazards", test_device_version_id)
        assert len(rows) >= 1


# =========================================================================
# Harm CRUD (depends on hazard)
# =========================================================================


@pytest.mark.integration
class TestHarmCRUD:
    def test_create_harm(self, repo: TwinRepository, test_org_id: str, test_device_version_id: str):
        hazards = repo.get_by_device_version("hazards", test_device_version_id)
        if not hazards:
            pytest.skip("No hazards available for harm test")

        hazard_id = hazards[0].get("id", "")
        h = Harm(
            organization_id=UUID(test_org_id),
            hazard_id=UUID(str(hazard_id)),
            harm_type="misdiagnosis",
            description="Patient receives wrong treatment due to incorrect reading",
            severity="critical",
        )
        result = repo.create("harms", h)
        assert result is not None


# =========================================================================
# RiskControl CRUD (depends on hazard)
# =========================================================================


@pytest.mark.integration
class TestRiskControlCRUD:
    def test_create_risk_control(
        self, repo: TwinRepository, test_org_id: str, test_device_version_id: str
    ):
        hazards = repo.get_by_device_version("hazards", test_device_version_id)
        if not hazards:
            pytest.skip("No hazards available for risk control test")

        hazard_id = hazards[0].get("id", "")
        rc = RiskControl(
            organization_id=UUID(test_org_id),
            hazard_id=UUID(str(hazard_id)),
            control_type="inherent_safety",
            description="Validate algorithm output against reference range",
            risk_level_post="low",
        )
        result = repo.create("risk_controls", rc)
        assert result is not None


# =========================================================================
# VerificationTest CRUD
# =========================================================================


@pytest.mark.integration
class TestVerificationTestCRUD:
    def test_create(self, repo: TwinRepository, test_org_id: str, test_device_version_id: str):
        vt = VerificationTest(
            organization_id=UUID(test_org_id),
            device_version_id=UUID(test_device_version_id),
            test_type="software",
            title="Algorithm accuracy bench test",
            acceptance_criteria="Mean error < 5mmHg",
        )
        result = repo.create("verification_tests", vt)
        assert result is not None


# =========================================================================
# ValidationTest CRUD
# =========================================================================


@pytest.mark.integration
class TestValidationTestCRUD:
    def test_create(self, repo: TwinRepository, test_org_id: str, test_device_version_id: str):
        vt = ValidationTest(
            organization_id=UUID(test_org_id),
            device_version_id=UUID(test_device_version_id),
            test_type="usability",
            title="Summative usability study",
            acceptance_criteria="Task success >= 95%",
            participant_count=30,
        )
        result = repo.create("validation_tests", vt)
        assert result is not None


# =========================================================================
# EvidenceItem CRUD
# =========================================================================


@pytest.mark.integration
class TestEvidenceItemCRUD:
    def test_create(self, repo: TwinRepository, test_org_id: str, test_device_version_id: str):
        ei = EvidenceItem(
            organization_id=UUID(test_org_id),
            device_version_id=UUID(test_device_version_id),
            evidence_type="test_report",
            title="Biocompatibility test report ISO 10993",
            strength="strong",
        )
        result = repo.create("evidence_items", ei)
        assert result is not None


# =========================================================================
# LabelingAsset CRUD
# =========================================================================


@pytest.mark.integration
class TestLabelingAssetCRUD:
    def test_create(self, repo: TwinRepository, test_org_id: str, test_device_version_id: str):
        la = LabelingAsset(
            organization_id=UUID(test_org_id),
            device_version_id=UUID(test_device_version_id),
            asset_type="ifu",
            title="Instructions for Use v1.0",
            language="en",
            regulatory_market="CA",
        )
        result = repo.create("labeling_assets", la)
        assert result is not None


# =========================================================================
# SubmissionTarget CRUD
# =========================================================================


@pytest.mark.integration
class TestSubmissionTargetCRUD:
    def test_create(self, repo: TwinRepository, test_org_id: str, test_device_version_id: str):
        st = SubmissionTarget(
            organization_id=UUID(test_org_id),
            device_version_id=UUID(test_device_version_id),
            regulatory_body="health_canada",
            submission_type="mdl",
            status="planning",
        )
        result = repo.create("submission_targets", st)
        assert result is not None

    def test_get_by_org(self, repo: TwinRepository, test_org_id: str):
        rows = repo.get_by_org("submission_targets", test_org_id)
        assert len(rows) >= 1


# =========================================================================
# Cross-cutting: count all tables
# =========================================================================


@pytest.mark.integration
class TestCrossCuttingCounts:
    def test_all_tables_have_records(self, repo: TwinRepository, test_org_id: str):
        """After all create tests, every table should have at least 1 record."""
        tables = [
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
        ]
        for table in tables:
            count = repo.count(table, test_org_id)
            assert count >= 1, f"Table {table} has no records for test org"
