"""
Integration tests for end-to-end classification flow.

Tests the complete flow from device input to classification result,
including all components working together.
"""

import pytest


@pytest.mark.integration
class TestSaMDClassificationFlow:
    """Test end-to-end SaMD classification."""

    def test_full_samd_classification_class_iii(self, api_client):
        """Full SaMD flow for Class III device."""
        # Step 1: Classify device
        classify_request = {
            "device_info": {
                "name": "AI Diagnostic Software",
                "description": "ML-powered diagnostic assistance",
                "intended_use": "Assist in diagnosis",
                "manufacturer_name": "Test Inc",
                "is_software": True,
            },
            "samd_info": {
                "healthcare_situation": "serious",
                "significance": "diagnose",
                "uses_ml": True,
            },
        }
        response = api_client.post("/api/v1/classify", json=classify_request)
        assert response.status_code == 200

        classification = response.json()
        assert classification["device_class"] == "III"
        assert classification["is_samd"] is True

        # Step 2: Get pathway
        pathway_request = {
            "device_class": classification["device_class"],
            "is_software": True,
            "has_mdel": False,
        }
        response = api_client.post("/api/v1/pathway", json=pathway_request)
        assert response.status_code == 200

        pathway = response.json()
        assert len(pathway["steps"]) >= 3
        assert pathway["fees"]["total"] > 0

    def test_full_samd_classification_class_iv(self, api_client):
        """Full SaMD flow for Class IV device."""
        classify_request = {
            "device_info": {
                "name": "AI Treatment Advisor",
                "description": "ML-powered treatment recommendations",
                "intended_use": "Recommend treatments for critical conditions",
                "manufacturer_name": "Test Inc",
                "is_software": True,
            },
            "samd_info": {
                "healthcare_situation": "critical",
                "significance": "treat",
                "uses_ml": True,
            },
        }
        response = api_client.post("/api/v1/classify", json=classify_request)
        assert response.status_code == 200

        classification = response.json()
        assert classification["device_class"] == "IV"

        # Verify Class IV gets highest fees
        pathway_request = {
            "device_class": "IV",
            "is_software": True,
            "has_mdel": False,
        }
        response = api_client.post("/api/v1/pathway", json=pathway_request)
        pathway = response.json()
        assert pathway["fees"]["mdl_fee"] == 23130  # Class IV MDL fee


@pytest.mark.integration
class TestTraditionalDeviceFlow:
    """Test end-to-end traditional (non-software) device classification."""

    def test_implant_classification_flow(self, api_client):
        """Full flow for implantable device."""
        classify_request = {
            "device_info": {
                "name": "Hip Implant",
                "description": "Orthopedic implant",
                "intended_use": "Joint replacement",
                "manufacturer_name": "Test Inc",
                "is_software": False,
                "is_implantable": True,
                "contact_duration": "long-term",
            },
        }
        response = api_client.post("/api/v1/classify", json=classify_request)
        assert response.status_code == 200

        classification = response.json()
        assert classification["device_class"] == "IV"
        assert classification["is_samd"] is False


@pytest.mark.integration
class TestFeeConsistency:
    """Test that fees are consistent across the flow."""

    def test_class_iii_fee_consistency(self, api_client):
        """Verify Class III fees match expected values throughout flow."""
        # Get pathway for Class III
        response = api_client.post(
            "/api/v1/pathway",
            json={"device_class": "III", "is_software": True, "has_mdel": False},
        )
        pathway = response.json()

        # Verify against known 2024 values
        assert pathway["fees"]["mdel_fee"] == 4590
        assert pathway["fees"]["mdl_fee"] == 7658
        assert pathway["fees"]["total"] == 4590 + 7658

    def test_existing_mdel_reduces_fees(self, api_client):
        """Verify that having MDEL reduces total fees."""
        # Without MDEL
        response1 = api_client.post(
            "/api/v1/pathway",
            json={"device_class": "III", "is_software": True, "has_mdel": False},
        )
        total_without = response1.json()["fees"]["total"]

        # With MDEL
        response2 = api_client.post(
            "/api/v1/pathway",
            json={"device_class": "III", "is_software": True, "has_mdel": True},
        )
        total_with = response2.json()["fees"]["total"]

        assert total_with < total_without
        assert total_without - total_with == 4590  # MDEL fee difference
