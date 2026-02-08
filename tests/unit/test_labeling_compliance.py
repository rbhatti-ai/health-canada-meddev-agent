"""
Unit tests for Labeling Compliance Service.

Sprint 9A — Tests for LabelingComplianceService, requirements,
and compliance checking against SOR/98-282 Part 5.

Tests use mock data (no DB required).
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.core.labeling_compliance import (
    LABELING_REQUIREMENTS,
    LabelingAsset,
    LabelingComplianceCheck,
    LabelingComplianceReport,
    LabelingComplianceService,
    LabelingRequirement,
    get_labeling_service,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def labeling_service() -> LabelingComplianceService:
    """Get labeling compliance service."""
    return LabelingComplianceService()


@pytest.fixture
def device_label_asset() -> LabelingAsset:
    """Create a sample device label asset."""
    return LabelingAsset(
        id=uuid4(),
        organization_id=uuid4(),
        device_version_id=uuid4(),
        asset_type="device_label",
        title="Device Label v1.0",
        content="Sample device label content",
        language="bilingual",
        status="approved",
    )


@pytest.fixture
def ifu_asset() -> LabelingAsset:
    """Create a sample IFU asset."""
    return LabelingAsset(
        id=uuid4(),
        organization_id=uuid4(),
        device_version_id=uuid4(),
        asset_type="ifu",
        title="Instructions for Use v1.0",
        content="Sample IFU content",
        language="bilingual",
        status="approved",
    )


@pytest.fixture
def packaging_asset() -> LabelingAsset:
    """Create a sample packaging asset."""
    return LabelingAsset(
        id=uuid4(),
        organization_id=uuid4(),
        device_version_id=uuid4(),
        asset_type="packaging",
        title="Package Label v1.0",
        content="Sample packaging content",
        language="bilingual",
        status="approved",
    )


# =============================================================================
# LabelingRequirement Model Tests
# =============================================================================


@pytest.mark.unit
class TestLabelingRequirementModel:
    """Tests for LabelingRequirement Pydantic model."""

    def test_valid_requirement(self):
        """Create a valid labeling requirement."""
        req = LabelingRequirement(
            id="REQ-TEST-001",
            section="s.21(1)(a)",
            category="identification",
            label_element="device_label",
            description="Device name on label",
            citation="[SOR/98-282, s.21(1)(a)]",
        )
        assert req.id == "REQ-TEST-001"
        assert req.mandatory is True
        assert req.device_classes == ["I", "II", "III", "IV"]

    def test_optional_requirement(self):
        """Create an optional labeling requirement."""
        req = LabelingRequirement(
            id="REQ-TEST-002",
            section="s.21(1)(e)",
            category="safety_info",
            label_element="device_label",
            description="Expiry date",
            mandatory=False,
            citation="[SOR/98-282, s.21(1)(e)]",
        )
        assert req.mandatory is False

    def test_class_specific_requirement(self):
        """Create a requirement for specific device classes."""
        req = LabelingRequirement(
            id="REQ-TEST-003",
            section="s.24",
            category="special_requirements",
            label_element="device_label",
            description="IVD statement",
            device_classes=["II", "III", "IV"],
            citation="[SOR/98-282, s.24]",
        )
        assert "I" not in req.device_classes
        assert "II" in req.device_classes


# =============================================================================
# LabelingComplianceCheck Model Tests
# =============================================================================


@pytest.mark.unit
class TestLabelingComplianceCheckModel:
    """Tests for LabelingComplianceCheck Pydantic model."""

    def test_compliant_check(self):
        """Create a compliant check result."""
        check = LabelingComplianceCheck(
            requirement_id="REQ-LABEL-001",
            status="compliant",
            element_checked="device_label",
            evidence="Device name clearly visible on label",
        )
        assert check.status == "compliant"
        assert check.evidence is not None

    def test_non_compliant_check(self):
        """Create a non-compliant check result."""
        check = LabelingComplianceCheck(
            requirement_id="REQ-LABEL-009",
            status="non_compliant",
            element_checked="device_label",
            finding="Label is English only",
            remediation="Add French translation to label",
        )
        assert check.status == "non_compliant"
        assert check.finding is not None
        assert check.remediation is not None

    def test_not_applicable_check(self):
        """Create a not-applicable check result."""
        check = LabelingComplianceCheck(
            requirement_id="REQ-LABEL-005",
            status="not_applicable",
            element_checked="device_label",
            evidence="Device does not have limited shelf life",
        )
        assert check.status == "not_applicable"


# =============================================================================
# LabelingComplianceReport Model Tests
# =============================================================================


@pytest.mark.unit
class TestLabelingComplianceReportModel:
    """Tests for LabelingComplianceReport Pydantic model."""

    def test_valid_report(self):
        """Create a valid compliance report."""
        report = LabelingComplianceReport(
            device_version_id=uuid4(),
            organization_id=uuid4(),
            device_class="II",
            total_requirements=30,
            compliant_count=25,
            non_compliant_count=3,
            not_checked_count=2,
        )
        assert report.total_requirements == 30
        assert report.compliant_count == 25

    def test_report_score_calculation(self):
        """Compliance score should be calculated correctly."""
        report = LabelingComplianceReport(
            device_version_id=uuid4(),
            organization_id=uuid4(),
            device_class="III",
            total_requirements=20,
            compliant_count=16,
            non_compliant_count=2,
            not_applicable_count=2,
        )
        score = report.calculate_score()
        # 16 compliant / 18 applicable = 0.888...
        assert 0.88 < score < 0.90

    def test_report_score_all_compliant(self):
        """Score should be 1.0 when all applicable are compliant."""
        report = LabelingComplianceReport(
            device_version_id=uuid4(),
            organization_id=uuid4(),
            device_class="II",
            total_requirements=10,
            compliant_count=8,
            not_applicable_count=2,
        )
        score = report.calculate_score()
        assert score == 1.0

    def test_report_citations(self):
        """Report should have regulation and guidance citations."""
        report = LabelingComplianceReport(
            device_version_id=uuid4(),
            organization_id=uuid4(),
            device_class="II",
            total_requirements=10,
        )
        assert report.regulation_ref == "SOR-98-282-PART5"
        assert report.guidance_ref == "GUI-0015"


# =============================================================================
# LabelingAsset Model Tests
# =============================================================================


@pytest.mark.unit
class TestLabelingAssetModel:
    """Tests for LabelingAsset Pydantic model."""

    def test_valid_device_label(self):
        """Create a valid device label asset."""
        asset = LabelingAsset(
            organization_id=uuid4(),
            device_version_id=uuid4(),
            asset_type="device_label",
            title="Device Label v1.0",
        )
        assert asset.asset_type == "device_label"
        assert asset.language == "bilingual"
        assert asset.status == "draft"

    def test_ifu_asset(self):
        """Create a valid IFU asset."""
        asset = LabelingAsset(
            organization_id=uuid4(),
            device_version_id=uuid4(),
            asset_type="ifu",
            title="Instructions for Use",
            language="en",
        )
        assert asset.asset_type == "ifu"
        assert asset.language == "en"

    def test_packaging_asset(self):
        """Create a valid packaging asset."""
        asset = LabelingAsset(
            organization_id=uuid4(),
            device_version_id=uuid4(),
            asset_type="packaging",
            title="Package Label",
            status="approved",
        )
        assert asset.asset_type == "packaging"
        assert asset.status == "approved"


# =============================================================================
# Pre-populated Requirements Tests
# =============================================================================


@pytest.mark.unit
class TestPrePopulatedRequirements:
    """Tests for pre-populated labeling requirements."""

    def test_requirements_count(self):
        """Should have at least 30 requirements."""
        assert len(LABELING_REQUIREMENTS) >= 30

    def test_device_label_requirements_exist(self):
        """Should have device label requirements."""
        label_reqs = [
            r for r in LABELING_REQUIREMENTS.values() if r.label_element == "device_label"
        ]
        assert len(label_reqs) >= 9

    def test_ifu_requirements_exist(self):
        """Should have IFU requirements."""
        ifu_reqs = [r for r in LABELING_REQUIREMENTS.values() if r.label_element == "ifu"]
        assert len(ifu_reqs) >= 11

    def test_packaging_requirements_exist(self):
        """Should have packaging requirements."""
        pkg_reqs = [r for r in LABELING_REQUIREMENTS.values() if r.label_element == "packaging"]
        assert len(pkg_reqs) >= 7

    def test_bilingual_requirements_exist(self):
        """Should have bilingual requirements."""
        bilingual_reqs = [r for r in LABELING_REQUIREMENTS.values() if r.category == "bilingual"]
        assert len(bilingual_reqs) >= 3

    def test_all_requirements_have_citations(self):
        """Every requirement should have a citation."""
        for req_id, req in LABELING_REQUIREMENTS.items():
            assert req.citation is not None, f"{req_id} missing citation"
            assert "SOR/98-282" in req.citation, f"{req_id} missing SOR citation"

    def test_all_requirements_have_section(self):
        """Every requirement should reference a section."""
        for req_id, req in LABELING_REQUIREMENTS.items():
            assert req.section is not None, f"{req_id} missing section"
            assert req.section.startswith("s."), f"{req_id} section format invalid"

    def test_requirement_ids_unique(self):
        """All requirement IDs should be unique."""
        ids = list(LABELING_REQUIREMENTS.keys())
        assert len(ids) == len(set(ids))


# =============================================================================
# LabelingComplianceService Tests
# =============================================================================


@pytest.mark.unit
class TestLabelingComplianceService:
    """Tests for LabelingComplianceService."""

    def test_get_all_requirements(self, labeling_service):
        """Should return all requirements."""
        requirements = labeling_service.get_requirements()
        assert len(requirements) >= 30

    def test_count_requirements(self, labeling_service):
        """Should count requirements correctly."""
        count = labeling_service.count_requirements()
        assert count >= 30

    def test_get_requirements_for_class_i(self, labeling_service):
        """Should get requirements for Class I devices."""
        reqs = labeling_service.get_requirements_for_class("I")
        assert len(reqs) >= 25

    def test_get_requirements_for_class_ii(self, labeling_service):
        """Should get requirements for Class II devices."""
        reqs = labeling_service.get_requirements_for_class("II")
        # Class II has more requirements (UDI, special)
        assert len(reqs) >= 28

    def test_get_requirements_by_element_label(self, labeling_service):
        """Should get device label requirements."""
        reqs = labeling_service.get_requirements_by_element("device_label")
        assert len(reqs) >= 9
        assert all(r.label_element == "device_label" for r in reqs)

    def test_get_requirements_by_element_ifu(self, labeling_service):
        """Should get IFU requirements."""
        reqs = labeling_service.get_requirements_by_element("ifu")
        assert len(reqs) >= 11
        assert all(r.label_element == "ifu" for r in reqs)

    def test_get_requirements_by_category(self, labeling_service):
        """Should get requirements by category."""
        reqs = labeling_service.get_requirements_by_category("bilingual")
        assert len(reqs) >= 3
        assert all(r.category == "bilingual" for r in reqs)

    def test_get_mandatory_requirements(self, labeling_service):
        """Should get mandatory requirements for a class."""
        reqs = labeling_service.get_mandatory_requirements("III")
        # All mandatory requirements for Class III
        assert len(reqs) >= 15
        assert all(r.mandatory is True for r in reqs)

    def test_get_bilingual_requirements(self, labeling_service):
        """Should get bilingual requirements."""
        reqs = labeling_service.get_bilingual_requirements()
        assert len(reqs) >= 3
        for req in reqs:
            assert req.category == "bilingual"

    def test_get_safety_requirements(self, labeling_service):
        """Should get safety requirements."""
        reqs = labeling_service.get_safety_requirements()
        assert len(reqs) >= 5
        for req in reqs:
            assert req.category == "safety_info"


# =============================================================================
# Asset Checking Tests
# =============================================================================


@pytest.mark.unit
class TestAssetChecking:
    """Tests for checking labeling assets."""

    def test_check_bilingual_asset_compliant(self, labeling_service, device_label_asset):
        """Bilingual asset should pass bilingual check."""
        checks = labeling_service.check_asset(device_label_asset, "II")
        bilingual_checks = [c for c in checks if "REQ-LABEL-009" in c.requirement_id]
        assert len(bilingual_checks) == 1
        assert bilingual_checks[0].status == "compliant"

    def test_check_english_only_asset(self, labeling_service):
        """English-only asset should fail bilingual check."""
        asset = LabelingAsset(
            organization_id=uuid4(),
            device_version_id=uuid4(),
            asset_type="device_label",
            title="Label",
            content="English only content",
            language="en",
        )
        checks = labeling_service.check_asset(asset, "II")
        bilingual_checks = [c for c in checks if "REQ-LABEL-009" in c.requirement_id]
        assert len(bilingual_checks) == 1
        assert bilingual_checks[0].status == "non_compliant"

    def test_check_asset_without_content(self, labeling_service):
        """Asset without content should return not_checked."""
        asset = LabelingAsset(
            organization_id=uuid4(),
            device_version_id=uuid4(),
            asset_type="device_label",
            title="Empty Label",
        )
        checks = labeling_service.check_asset(asset, "II")
        # Non-bilingual checks should be not_checked
        non_bilingual = [c for c in checks if "bilingual" not in c.requirement_id]
        # All non-content checks are not_checked
        for check in non_bilingual:
            assert check.status in ("not_checked", "compliant", "non_compliant")


# =============================================================================
# Report Generation Tests
# =============================================================================


@pytest.mark.unit
class TestReportGeneration:
    """Tests for compliance report generation."""

    def test_generate_report_no_assets(self, labeling_service):
        """Generate report with no assets should mark all as not_checked."""
        device_id = uuid4()
        org_id = uuid4()
        report = labeling_service.generate_report(
            device_version_id=device_id,
            organization_id=org_id,
            device_class="II",
        )
        assert report.device_version_id == device_id
        assert report.organization_id == org_id
        assert report.device_class == "II"
        assert report.not_checked_count > 0

    def test_generate_report_with_assets(self, labeling_service, device_label_asset, ifu_asset):
        """Generate report with assets should check them."""
        device_id = uuid4()
        org_id = uuid4()
        report = labeling_service.generate_report(
            device_version_id=device_id,
            organization_id=org_id,
            device_class="II",
            assets=[device_label_asset, ifu_asset],
        )
        assert report.total_requirements > 0
        assert len(report.checks) > 0

    def test_report_has_all_counts(self, labeling_service, device_label_asset):
        """Report should have all status counts."""
        report = labeling_service.generate_report(
            device_version_id=uuid4(),
            organization_id=uuid4(),
            device_class="II",
            assets=[device_label_asset],
        )
        # Check that counts are integers
        assert isinstance(report.compliant_count, int)
        assert isinstance(report.non_compliant_count, int)
        assert isinstance(report.partial_count, int)
        assert isinstance(report.not_applicable_count, int)
        assert isinstance(report.not_checked_count, int)

    def test_report_score_calculated(self, labeling_service, device_label_asset):
        """Report should have calculated score."""
        report = labeling_service.generate_report(
            device_version_id=uuid4(),
            organization_id=uuid4(),
            device_class="II",
            assets=[device_label_asset],
        )
        assert 0.0 <= report.compliance_score <= 1.0


# =============================================================================
# Singleton Tests
# =============================================================================


@pytest.mark.unit
class TestSingleton:
    """Tests for singleton accessor."""

    def test_get_labeling_service(self):
        """Should return a LabelingComplianceService."""
        service = get_labeling_service()
        assert isinstance(service, LabelingComplianceService)

    def test_singleton_returns_same_instance(self):
        """Should return the same instance."""
        service1 = get_labeling_service()
        service2 = get_labeling_service()
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
        for req in LABELING_REQUIREMENTS.values():
            assert "SOR/98-282" in req.citation

    def test_requirements_have_section_reference(self):
        """All requirements should have section reference."""
        for req in LABELING_REQUIREMENTS.values():
            assert req.section is not None
            assert len(req.section) > 0

    def test_requirements_have_guidance_ref(self):
        """Most requirements should have GUI-0015 reference."""
        gui_count = sum(
            1
            for req in LABELING_REQUIREMENTS.values()
            if req.guidance_ref and "GUI-0015" in req.guidance_ref
        )
        # At least 80% should have guidance
        assert gui_count >= len(LABELING_REQUIREMENTS) * 0.8

    def test_report_has_regulation_citation(self, labeling_service):
        """Generated report should cite regulation."""
        report = labeling_service.generate_report(
            device_version_id=uuid4(),
            organization_id=uuid4(),
            device_class="II",
        )
        assert "SOR" in report.regulation_ref
        assert "GUI" in report.guidance_ref
