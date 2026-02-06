"""
Unit tests for Pydantic models.
"""

import pytest
from pydantic import ValidationError


@pytest.mark.unit
class TestDeviceClass:
    """Test DeviceClass enum."""

    def test_device_class_values(self):
        from src.core.models import DeviceClass

        assert DeviceClass.CLASS_I.value == "I"
        assert DeviceClass.CLASS_II.value == "II"
        assert DeviceClass.CLASS_III.value == "III"
        assert DeviceClass.CLASS_IV.value == "IV"

    def test_device_class_count(self):
        from src.core.models import DeviceClass

        assert len(DeviceClass) == 4


@pytest.mark.unit
class TestHealthcareSituation:
    """Test HealthcareSituation enum."""

    def test_healthcare_situation_values(self):
        from src.core.models import HealthcareSituation

        assert HealthcareSituation.CRITICAL.value == "critical"
        assert HealthcareSituation.SERIOUS.value == "serious"
        assert HealthcareSituation.NON_SERIOUS.value == "non_serious"


@pytest.mark.unit
class TestSaMDCategory:
    """Test SaMDCategory enum."""

    def test_samd_category_values(self):
        from src.core.models import SaMDCategory

        assert SaMDCategory.TREAT.value == "treat"
        assert SaMDCategory.DIAGNOSE.value == "diagnose"
        assert SaMDCategory.DRIVE.value == "drive"
        assert SaMDCategory.INFORM.value == "inform"


@pytest.mark.unit
class TestDeviceInfo:
    """Test DeviceInfo model."""

    def test_valid_device_info(self):
        from src.core.models import DeviceInfo

        device = DeviceInfo(
            name="Test Device",
            description="A test device",
            intended_use="Testing purposes",
            manufacturer_name="Test Inc",
        )
        assert device.name == "Test Device"
        assert device.is_software is False  # Default

    def test_device_info_with_software_flag(self):
        from src.core.models import DeviceInfo

        device = DeviceInfo(
            name="Test SaMD",
            description="Software device",
            intended_use="Testing",
            manufacturer_name="Test Inc",
            is_software=True,
        )
        assert device.is_software is True

    def test_device_info_required_fields(self):
        from src.core.models import DeviceInfo

        with pytest.raises(ValidationError):
            DeviceInfo(name="Test")  # Missing required fields


@pytest.mark.unit
class TestSaMDInfo:
    """Test SaMDInfo model."""

    def test_valid_samd_info(self):
        from src.core.models import SaMDInfo, HealthcareSituation, SaMDCategory

        samd = SaMDInfo(
            healthcare_situation=HealthcareSituation.SERIOUS,
            significance=SaMDCategory.DIAGNOSE,
        )
        assert samd.healthcare_situation == HealthcareSituation.SERIOUS
        assert samd.uses_ml is False  # Default

    def test_samd_with_ml(self):
        from src.core.models import SaMDInfo, HealthcareSituation, SaMDCategory

        samd = SaMDInfo(
            healthcare_situation=HealthcareSituation.CRITICAL,
            significance=SaMDCategory.TREAT,
            uses_ml=True,
            is_locked=False,
        )
        assert samd.uses_ml is True
        assert samd.is_locked is False


@pytest.mark.unit
class TestClassificationResult:
    """Test ClassificationResult model."""

    def test_classification_result_creation(self):
        from src.core.models import ClassificationResult, DeviceClass

        result = ClassificationResult(
            device_class=DeviceClass.CLASS_III,
            classification_rules=["Rule 1"],
            rationale="Test rationale",
            is_samd=True,
            confidence=0.9,
        )
        assert result.device_class == DeviceClass.CLASS_III
        assert result.is_samd is True
        assert result.confidence == 0.9

    def test_classification_result_with_warnings(self):
        from src.core.models import ClassificationResult, DeviceClass

        result = ClassificationResult(
            device_class=DeviceClass.CLASS_IV,
            classification_rules=["Test"],
            rationale="Test",
            is_samd=True,
            confidence=1.0,
            warnings=["Warning 1", "Warning 2"],
        )
        assert len(result.warnings) == 2
        assert "Warning 1" in result.warnings


@pytest.mark.unit
class TestChecklist:
    """Test Checklist model."""

    def test_checklist_computed_properties(self):
        from src.core.models import Checklist, ChecklistItem, DeviceClass

        items = [
            ChecklistItem(
                id="1",
                category="Test",
                title="Item 1",
                description="Test item 1",
                required=True,
                status="completed",
            ),
            ChecklistItem(
                id="2",
                category="Test",
                title="Item 2",
                description="Test item 2",
                required=True,
                status="not_started",
            ),
        ]

        checklist = Checklist(
            name="Test Checklist",
            device_class=DeviceClass.CLASS_III,
            items=items,
        )

        assert checklist.total_items == 2
        assert checklist.completed_items == 1
        assert checklist.completion_percentage == 50.0
