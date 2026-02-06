"""Unit tests for device classification engine."""

import pytest
from src.core.models import (
    DeviceClass,
    DeviceInfo,
    SaMDInfo,
    SaMDCategory,
    HealthcareSituation,
)
from src.core.classification import ClassificationEngine, classify_device


@pytest.fixture
def classification_engine():
    """Create a classification engine instance."""
    return ClassificationEngine()


@pytest.fixture
def basic_device():
    """Create a basic non-software device."""
    return DeviceInfo(
        name="Test Device",
        description="A simple medical device",
        intended_use="General diagnostic use",
        is_software=False,
        manufacturer_name="Test Manufacturer",
    )


@pytest.fixture
def software_device():
    """Create a software device (SaMD)."""
    return DeviceInfo(
        name="Test SaMD",
        description="AI-powered diagnostic software",
        intended_use="Assist in diagnosis of skin conditions",
        is_software=True,
        manufacturer_name="Test Manufacturer",
    )


class TestSaMDClassification:
    """Tests for SaMD classification using IMDRF framework."""

    def test_critical_treat_is_class_iv(self, classification_engine, software_device):
        """Critical healthcare + Treat/Diagnose = Class IV."""
        samd_info = SaMDInfo(
            healthcare_situation=HealthcareSituation.CRITICAL,
            significance=SaMDCategory.TREAT,
        )
        result = classification_engine.classify_device(software_device, samd_info)
        assert result.device_class == DeviceClass.CLASS_IV
        assert result.is_samd is True

    def test_critical_drive_is_class_iii(self, classification_engine, software_device):
        """Critical healthcare + Drive = Class III."""
        samd_info = SaMDInfo(
            healthcare_situation=HealthcareSituation.CRITICAL,
            significance=SaMDCategory.DRIVE,
        )
        result = classification_engine.classify_device(software_device, samd_info)
        assert result.device_class == DeviceClass.CLASS_III

    def test_non_serious_inform_is_class_i(self, classification_engine, software_device):
        """Non-serious healthcare + Inform = Class I."""
        samd_info = SaMDInfo(
            healthcare_situation=HealthcareSituation.NON_SERIOUS,
            significance=SaMDCategory.INFORM,
        )
        result = classification_engine.classify_device(software_device, samd_info)
        assert result.device_class == DeviceClass.CLASS_I

    def test_ml_device_includes_warning(self, classification_engine, software_device):
        """ML-enabled SaMD should include PCCP warning if adaptive."""
        samd_info = SaMDInfo(
            healthcare_situation=HealthcareSituation.SERIOUS,
            significance=SaMDCategory.DIAGNOSE,
            uses_ml=True,
            is_locked=False,  # Adaptive algorithm
        )
        result = classification_engine.classify_device(software_device, samd_info)
        assert any("PCCP" in warning for warning in result.warnings)


class TestTraditionalDeviceClassification:
    """Tests for non-software device classification."""

    def test_implantable_long_term_is_class_iv(self, classification_engine):
        """Long-term implantable device = Class IV."""
        device = DeviceInfo(
            name="Hip Implant",
            description="Orthopedic hip replacement",
            intended_use="Permanent hip joint replacement",
            is_implantable=True,
            contact_duration="long-term",
            manufacturer_name="Test",
        )
        result = classification_engine.classify_device(device)
        assert result.device_class == DeviceClass.CLASS_IV

    def test_surgical_invasive_is_class_iii(self, classification_engine):
        """Surgically invasive device = Class III."""
        device = DeviceInfo(
            name="Surgical Scalpel",
            description="Single-use surgical cutting instrument",
            intended_use="Surgical incisions",
            invasive_type="surgical",
            manufacturer_name="Test",
        )
        result = classification_engine.classify_device(device)
        assert result.device_class == DeviceClass.CLASS_III

    def test_active_device_is_class_ii(self, classification_engine):
        """Active (powered) device = Class II."""
        device = DeviceInfo(
            name="Blood Pressure Monitor",
            description="Electronic blood pressure measurement",
            intended_use="Non-invasive blood pressure measurement",
            is_active=True,
            manufacturer_name="Test",
        )
        result = classification_engine.classify_device(device)
        assert result.device_class == DeviceClass.CLASS_II

    def test_non_invasive_non_active_is_class_i(self, classification_engine):
        """Non-invasive, non-active device = Class I."""
        device = DeviceInfo(
            name="Bandage",
            description="Adhesive wound covering",
            intended_use="Cover minor wounds",
            manufacturer_name="Test",
        )
        result = classification_engine.classify_device(device)
        assert result.device_class == DeviceClass.CLASS_I


class TestIVDClassification:
    """Tests for In-Vitro Diagnostic device classification."""

    def test_blood_screening_ivd_is_class_iv(self, classification_engine):
        """Blood screening IVD = Class IV."""
        device = DeviceInfo(
            name="HIV Test Kit",
            description="HIV antibody detection",
            intended_use="Blood screening for HIV",
            is_ivd=True,
            manufacturer_name="Test",
        )
        result = classification_engine.classify_device(device)
        assert result.device_class == DeviceClass.CLASS_IV

    def test_cancer_diagnostic_ivd_is_class_iii(self, classification_engine):
        """Cancer diagnostic IVD = Class III."""
        device = DeviceInfo(
            name="Cancer Marker Test",
            description="Tumor marker detection",
            intended_use="Cancer screening and monitoring",
            is_ivd=True,
            manufacturer_name="Test",
        )
        result = classification_engine.classify_device(device)
        assert result.device_class == DeviceClass.CLASS_III

    def test_glucose_self_test_is_class_ii(self, classification_engine):
        """Glucose self-testing IVD = Class II."""
        device = DeviceInfo(
            name="Glucose Meter",
            description="Blood glucose measurement",
            intended_use="Self-testing glucose levels",
            is_ivd=True,
            manufacturer_name="Test",
        )
        result = classification_engine.classify_device(device)
        assert result.device_class == DeviceClass.CLASS_II


class TestConvenienceFunction:
    """Tests for the classify_device convenience function."""

    def test_classify_device_function(self, basic_device):
        """Test that convenience function works."""
        result = classify_device(basic_device)
        assert result.device_class is not None
        assert result.rationale is not None


class TestClassificationResult:
    """Tests for classification result properties."""

    def test_result_includes_references(self, classification_engine, basic_device):
        """Classification result should include regulatory references."""
        result = classification_engine.classify_device(basic_device)
        assert len(result.references) > 0

    def test_result_includes_rationale(self, classification_engine, basic_device):
        """Classification result should include rationale."""
        result = classification_engine.classify_device(basic_device)
        assert result.rationale is not None
        assert len(result.rationale) > 0
