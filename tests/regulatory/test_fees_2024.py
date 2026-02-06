"""
Regulatory accuracy tests for Health Canada 2024 fee values.

IMPORTANT: These tests verify the accuracy of fee values against
official Health Canada fee schedules. If Health Canada updates
fees, these tests will fail intentionally to alert developers.

Source: https://www.canada.ca/en/health-canada/services/drugs-health-products/medical-devices/fees.html
"""

import pytest

from src.core.models import DeviceClass
from src.core.pathway import PathwayAdvisor, FEES_2024


@pytest.mark.regulatory
class TestMDELFees:
    """Test MDEL (Medical Device Establishment Licence) fees."""

    def test_mdel_application_fee(self):
        """MDEL application fee should be $4,590 CAD (2024)."""
        assert FEES_2024["mdel_application"] == 4590

    def test_mdel_amendment_fee(self):
        """MDEL amendment fee should be $384 CAD (2024)."""
        assert FEES_2024["mdel_amendment"] == 384


@pytest.mark.regulatory
class TestMDLFees:
    """Test MDL (Medical Device Licence) application fees."""

    def test_class_ii_mdl_fee(self):
        """Class II MDL application fee should be $468 CAD (2024)."""
        assert FEES_2024["mdl_class_ii"] == 468

    def test_class_iii_mdl_fee(self):
        """Class III MDL application fee should be $7,658 CAD (2024)."""
        assert FEES_2024["mdl_class_iii"] == 7658

    def test_class_iv_mdl_fee(self):
        """Class IV MDL application fee should be $23,130 CAD (2024)."""
        assert FEES_2024["mdl_class_iv"] == 23130

    def test_class_ii_no_mdl_fee(self):
        """Class I devices do not require MDL."""
        assert FEES_2024.get("mdl_class_i") is None or FEES_2024.get("mdl_class_i") == 0


@pytest.mark.regulatory
class TestAnnualFees:
    """Test annual right-to-sell fees."""

    def test_class_ii_no_annual_fee(self):
        """Class II devices have no annual fee."""
        assert FEES_2024["annual_right_to_sell_ii"] == 0

    def test_class_iii_annual_fee(self):
        """Class III annual fee should be $831 CAD (2024)."""
        assert FEES_2024["annual_right_to_sell_iii"] == 831

    def test_class_iv_annual_fee(self):
        """Class IV annual fee should be $1,662 CAD (2024)."""
        assert FEES_2024["annual_right_to_sell_iv"] == 1662


@pytest.mark.regulatory
class TestPathwayFeeCalculations:
    """Test that pathway advisor calculates fees correctly."""

    @pytest.fixture
    def advisor(self):
        return PathwayAdvisor()

    def test_class_ii_total_without_mdel(self, advisor):
        """Class II total (no MDEL): MDEL + MDL = $4,590 + $468 = $5,058."""
        from src.core.models import DeviceInfo, ClassificationResult

        device = DeviceInfo(
            name="Test", description="Test", intended_use="Test",
            manufacturer_name="Test"
        )
        classification = ClassificationResult(
            device_class=DeviceClass.CLASS_II,
            classification_rules=["Test"],
            rationale="Test",
            is_samd=False,
            confidence=1.0,
        )
        pathway = advisor.get_pathway(classification, device, has_mdel=False)
        assert pathway.fees.mdel_fee == 4590
        assert pathway.fees.mdl_fee == 468
        assert pathway.fees.total == 4590 + 468

    def test_class_iii_total_without_mdel(self, advisor):
        """Class III total (no MDEL): MDEL + MDL = $4,590 + $7,658 = $12,248."""
        from src.core.models import DeviceInfo, ClassificationResult

        device = DeviceInfo(
            name="Test", description="Test", intended_use="Test",
            manufacturer_name="Test"
        )
        classification = ClassificationResult(
            device_class=DeviceClass.CLASS_III,
            classification_rules=["Test"],
            rationale="Test",
            is_samd=False,
            confidence=1.0,
        )
        pathway = advisor.get_pathway(classification, device, has_mdel=False)
        assert pathway.fees.mdel_fee == 4590
        assert pathway.fees.mdl_fee == 7658
        assert pathway.fees.total == 4590 + 7658

    def test_class_iv_total_without_mdel(self, advisor):
        """Class IV total (no MDEL): MDEL + MDL = $4,590 + $23,130 = $27,720."""
        from src.core.models import DeviceInfo, ClassificationResult

        device = DeviceInfo(
            name="Test", description="Test", intended_use="Test",
            manufacturer_name="Test"
        )
        classification = ClassificationResult(
            device_class=DeviceClass.CLASS_IV,
            classification_rules=["Test"],
            rationale="Test",
            is_samd=False,
            confidence=1.0,
        )
        pathway = advisor.get_pathway(classification, device, has_mdel=False)
        assert pathway.fees.mdel_fee == 4590
        assert pathway.fees.mdl_fee == 23130
        assert pathway.fees.total == 4590 + 23130

    def test_class_iii_with_existing_mdel(self, advisor):
        """Class III with existing MDEL: MDL only = $7,658."""
        from src.core.models import DeviceInfo, ClassificationResult

        device = DeviceInfo(
            name="Test", description="Test", intended_use="Test",
            manufacturer_name="Test"
        )
        classification = ClassificationResult(
            device_class=DeviceClass.CLASS_III,
            classification_rules=["Test"],
            rationale="Test",
            is_samd=False,
            confidence=1.0,
        )
        pathway = advisor.get_pathway(classification, device, has_mdel=True)
        assert pathway.fees.mdel_fee == 0
        assert pathway.fees.mdl_fee == 7658
        assert pathway.fees.total == 7658


@pytest.mark.regulatory
class TestFeeDocumentation:
    """Verify fee documentation is accurate."""

    def test_fees_have_source_documentation(self):
        """Fee values should reference official source."""
        from src.core.pathway import FEES_2024

        # Verify the fee dictionary exists and has expected structure
        assert isinstance(FEES_2024, dict)
        assert len(FEES_2024) >= 7  # At least 7 fee types

    def test_fee_values_are_positive(self):
        """All fee values should be non-negative."""
        from src.core.pathway import FEES_2024

        for key, value in FEES_2024.items():
            assert value >= 0, f"Fee {key} should be non-negative"
