"""
Pytest configuration and shared fixtures.
"""

import os
import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment
os.environ["TESTING"] = "true"
os.environ.setdefault("OPENAI_API_KEY", "test-key-placeholder-not-real")


# ============================================================================
# Device Fixtures
# ============================================================================


@pytest.fixture
def samd_device_class_iii():
    """SaMD device that should classify as Class III."""
    from src.core.models import DeviceInfo, HealthcareSituation, SaMDCategory, SaMDInfo

    device = DeviceInfo(
        name="AI Skin Cancer Detector",
        description="ML-powered skin lesion analysis for melanoma screening",
        intended_use="Assist dermatologists in early melanoma detection",
        manufacturer_name="SkinTech Inc",
        is_software=True,
    )
    samd = SaMDInfo(
        healthcare_situation=HealthcareSituation.SERIOUS,
        significance=SaMDCategory.DIAGNOSE,
        uses_ml=True,
    )
    return device, samd


@pytest.fixture
def samd_device_class_iv():
    """SaMD device that should classify as Class IV."""
    from src.core.models import DeviceInfo, HealthcareSituation, SaMDCategory, SaMDInfo

    device = DeviceInfo(
        name="AI Cardiac Treatment Advisor",
        description="ML algorithm for cardiac treatment decisions",
        intended_use="Recommend treatment for cardiac conditions",
        manufacturer_name="CardioAI Inc",
        is_software=True,
    )
    samd = SaMDInfo(
        healthcare_situation=HealthcareSituation.CRITICAL,
        significance=SaMDCategory.TREAT,
        uses_ml=True,
    )
    return device, samd


@pytest.fixture
def samd_device_class_ii():
    """SaMD device that should classify as Class II."""
    from src.core.models import DeviceInfo, HealthcareSituation, SaMDCategory, SaMDInfo

    device = DeviceInfo(
        name="Wellness Tracker",
        description="General wellness monitoring software",
        intended_use="Track general health metrics",
        manufacturer_name="HealthApp Inc",
        is_software=True,
    )
    samd = SaMDInfo(
        healthcare_situation=HealthcareSituation.NON_SERIOUS,
        significance=SaMDCategory.INFORM,
        uses_ml=False,
    )
    return device, samd


@pytest.fixture
def implant_device_class_iv():
    """Implantable device that should classify as Class IV."""
    from src.core.models import DeviceInfo

    return DeviceInfo(
        name="Hip Replacement System",
        description="Titanium hip joint replacement prosthesis",
        intended_use="Total hip arthroplasty",
        manufacturer_name="OrthoMed Inc",
        is_software=False,
        is_implantable=True,
        contact_duration="long-term",
    )


@pytest.fixture
def implant_device_class_iii():
    """Short-term implant that should classify as Class III."""
    from src.core.models import DeviceInfo

    return DeviceInfo(
        name="Surgical Drain",
        description="Temporary post-surgical drainage device",
        intended_use="Short-term surgical drainage",
        manufacturer_name="SurgTech Inc",
        is_software=False,
        is_implantable=True,
        contact_duration="short-term",
    )


# ============================================================================
# API Fixtures
# ============================================================================


@pytest.fixture
def api_client():
    """FastAPI test client."""
    from fastapi.testclient import TestClient

    from src.api.main import app

    return TestClient(app)


# ============================================================================
# Classification Fixtures
# ============================================================================


@pytest.fixture
def classification_engine():
    """Classification engine instance."""
    from src.core.classification import ClassificationEngine

    return ClassificationEngine()


# ============================================================================
# Fee Fixtures (2024 Values)
# ============================================================================


@pytest.fixture
def fees_2024():
    """Official Health Canada 2024 fee values."""
    return {
        "mdel": 4590,
        "mdl_class_ii": 468,
        "mdl_class_iii": 7658,
        "mdl_class_iv": 23130,
        "annual_class_ii": 0,
        "annual_class_iii": 831,
        "annual_class_iv": 1662,
    }


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Fast, isolated unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "regulatory: Health Canada accuracy tests")
    config.addinivalue_line("markers", "slow: Tests that take > 5 seconds")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "rag: RAG system tests")
