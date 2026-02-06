"""Unit tests for regulatory pathway advisor."""

import pytest
from datetime import date

from src.core.models import (
    DeviceClass,
    DeviceInfo,
    ClassificationResult,
)
from src.core.pathway import PathwayAdvisor, get_pathway, FEES_2024


@pytest.fixture
def pathway_advisor():
    """Create a pathway advisor instance."""
    return PathwayAdvisor()


@pytest.fixture
def basic_device():
    """Create a basic device info."""
    return DeviceInfo(
        name="Test Device",
        description="A test medical device",
        intended_use="Testing purposes",
        is_software=False,
        manufacturer_name="Test Manufacturer",
    )


@pytest.fixture
def software_device():
    """Create a software device info."""
    return DeviceInfo(
        name="Test SaMD",
        description="A test software device",
        intended_use="AI-assisted diagnosis",
        is_software=True,
        manufacturer_name="Test Manufacturer",
    )


def make_classification(device_class: DeviceClass, is_samd: bool = False) -> ClassificationResult:
    """Helper to create classification results."""
    return ClassificationResult(
        device_class=device_class,
        rationale="Test classification",
        is_samd=is_samd,
    )


class TestPathwayGeneration:
    """Tests for pathway generation."""

    def test_class_i_no_mdl_required(self, pathway_advisor, basic_device):
        """Class I devices don't require MDL."""
        classification = make_classification(DeviceClass.CLASS_I)
        pathway = pathway_advisor.get_pathway(classification, basic_device)

        assert pathway.requires_mdl is False
        assert pathway.device_class == DeviceClass.CLASS_I

    def test_class_ii_requires_mdl(self, pathway_advisor, basic_device):
        """Class II devices require MDL."""
        classification = make_classification(DeviceClass.CLASS_II)
        pathway = pathway_advisor.get_pathway(classification, basic_device)

        assert pathway.requires_mdl is True
        assert any("MDL" in step.name for step in pathway.steps)

    def test_class_iv_requires_mdl(self, pathway_advisor, basic_device):
        """Class IV devices require MDL."""
        classification = make_classification(DeviceClass.CLASS_IV)
        pathway = pathway_advisor.get_pathway(classification, basic_device)

        assert pathway.requires_mdl is True

    def test_new_company_includes_mdel_step(self, pathway_advisor, basic_device):
        """New companies (no MDEL) should have MDEL step."""
        classification = make_classification(DeviceClass.CLASS_II)
        pathway = pathway_advisor.get_pathway(
            classification, basic_device, has_mdel=False
        )

        assert pathway.requires_mdel is True
        assert any("MDEL" in step.name for step in pathway.steps)

    def test_existing_mdel_skips_mdel_step(self, pathway_advisor, basic_device):
        """Companies with MDEL should skip MDEL step."""
        classification = make_classification(DeviceClass.CLASS_II)
        pathway = pathway_advisor.get_pathway(
            classification, basic_device, has_mdel=True
        )

        assert pathway.requires_mdel is False
        assert not any("MDEL" in step.name for step in pathway.steps)

    def test_software_device_includes_cybersecurity(self, pathway_advisor, software_device):
        """Software devices should include cybersecurity step."""
        classification = make_classification(DeviceClass.CLASS_II, is_samd=True)
        pathway = pathway_advisor.get_pathway(classification, software_device)

        assert any("Cybersecurity" in step.name for step in pathway.steps)

    def test_class_iii_includes_clinical_evidence(self, pathway_advisor, basic_device):
        """Class III devices should require clinical evidence."""
        classification = make_classification(DeviceClass.CLASS_III)
        pathway = pathway_advisor.get_pathway(classification, basic_device)

        assert any("Clinical" in step.name for step in pathway.steps)


class TestFeeCalculation:
    """Tests for fee calculations."""

    def test_class_ii_fee(self, pathway_advisor, basic_device):
        """Class II MDL fee is correct."""
        classification = make_classification(DeviceClass.CLASS_II)
        pathway = pathway_advisor.get_pathway(
            classification, basic_device, has_mdel=True
        )

        assert pathway.fees.mdl_fee == FEES_2024["mdl_class_ii"]

    def test_class_iii_fee(self, pathway_advisor, basic_device):
        """Class III MDL fee is correct."""
        classification = make_classification(DeviceClass.CLASS_III)
        pathway = pathway_advisor.get_pathway(
            classification, basic_device, has_mdel=True
        )

        assert pathway.fees.mdl_fee == FEES_2024["mdl_class_iii"]

    def test_class_iv_fee(self, pathway_advisor, basic_device):
        """Class IV MDL fee is correct."""
        classification = make_classification(DeviceClass.CLASS_IV)
        pathway = pathway_advisor.get_pathway(
            classification, basic_device, has_mdel=True
        )

        assert pathway.fees.mdl_fee == FEES_2024["mdl_class_iv"]

    def test_mdel_fee_included_for_new_company(self, pathway_advisor, basic_device):
        """MDEL fee included when company doesn't have one."""
        classification = make_classification(DeviceClass.CLASS_II)
        pathway = pathway_advisor.get_pathway(
            classification, basic_device, has_mdel=False
        )

        assert pathway.fees.mdel_fee == FEES_2024["mdel_application"]
        assert pathway.fees.total == pathway.fees.mdel_fee + pathway.fees.mdl_fee

    def test_no_mdel_fee_for_existing_holder(self, pathway_advisor, basic_device):
        """No MDEL fee when company already has MDEL."""
        classification = make_classification(DeviceClass.CLASS_II)
        pathway = pathway_advisor.get_pathway(
            classification, basic_device, has_mdel=True
        )

        assert pathway.fees.mdel_fee == 0


class TestTimeline:
    """Tests for timeline calculations."""

    def test_class_ii_timeline(self, pathway_advisor, basic_device):
        """Class II has 15-30 day review timeline."""
        classification = make_classification(DeviceClass.CLASS_II)
        pathway = pathway_advisor.get_pathway(
            classification, basic_device, has_mdel=True
        )

        assert pathway.timeline.total_days_min >= 15
        assert pathway.timeline.total_days_max <= 60  # Some buffer

    def test_class_iii_timeline(self, pathway_advisor, basic_device):
        """Class III has 75+ day review timeline."""
        classification = make_classification(DeviceClass.CLASS_III)
        pathway = pathway_advisor.get_pathway(
            classification, basic_device, has_mdel=True
        )

        assert pathway.timeline.total_days_min >= 75

    def test_class_iv_timeline(self, pathway_advisor, basic_device):
        """Class IV has 90+ day review timeline."""
        classification = make_classification(DeviceClass.CLASS_IV)
        pathway = pathway_advisor.get_pathway(
            classification, basic_device, has_mdel=True
        )

        assert pathway.timeline.total_days_min >= 90

    def test_timeline_has_milestones(self, pathway_advisor, basic_device):
        """Timeline should include milestones."""
        classification = make_classification(DeviceClass.CLASS_III)
        pathway = pathway_advisor.get_pathway(classification, basic_device)

        assert len(pathway.timeline.milestones) > 0

    def test_timeline_start_date_is_today(self, pathway_advisor, basic_device):
        """Timeline should start from today."""
        classification = make_classification(DeviceClass.CLASS_II)
        pathway = pathway_advisor.get_pathway(classification, basic_device)

        assert pathway.timeline.start_date == date.today()


class TestSpecialRequirements:
    """Tests for special requirements detection."""

    def test_samd_requirements(self, pathway_advisor, software_device):
        """SaMD should have SaMD-specific requirements."""
        classification = make_classification(DeviceClass.CLASS_II, is_samd=True)
        pathway = pathway_advisor.get_pathway(classification, software_device)

        assert any("SaMD" in req for req in pathway.special_requirements)

    def test_class_iv_presubmission_recommendation(self, pathway_advisor, basic_device):
        """Class IV should recommend pre-submission meeting."""
        classification = make_classification(DeviceClass.CLASS_IV)
        pathway = pathway_advisor.get_pathway(classification, basic_device)

        assert any("pre-submission" in req.lower() for req in pathway.special_requirements)


class TestConvenienceFunction:
    """Tests for the get_pathway convenience function."""

    def test_get_pathway_function(self, basic_device):
        """Test that convenience function works."""
        classification = make_classification(DeviceClass.CLASS_II)
        pathway = get_pathway(classification, basic_device)

        assert pathway is not None
        assert pathway.device_class == DeviceClass.CLASS_II
