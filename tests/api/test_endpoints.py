"""
API endpoint tests.

Tests REST API endpoints for correct behavior, status codes,
and response schemas.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
class TestHealthEndpoint:
    """Test /health endpoint."""

    def test_health_returns_200(self, api_client):
        """Health endpoint should return 200 OK."""
        response = api_client.get("/health")
        assert response.status_code == 200

    def test_health_returns_status(self, api_client):
        """Health endpoint should return status field."""
        response = api_client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


@pytest.mark.api
class TestStatsEndpoint:
    """Test /stats endpoint."""

    def test_stats_returns_200(self, api_client):
        """Stats endpoint should return 200 OK."""
        response = api_client.get("/stats")
        assert response.status_code == 200

    def test_stats_returns_expected_fields(self, api_client):
        """Stats endpoint should return expected fields."""
        response = api_client.get("/stats")
        data = response.json()
        assert "version" in data


@pytest.mark.api
class TestClassifyEndpoint:
    """Test /api/v1/classify endpoint."""

    def test_classify_valid_request(self, api_client):
        """Valid classification request should return 200."""
        request = {
            "device_info": {
                "name": "Test Device",
                "description": "A test device",
                "intended_use": "Testing",
                "manufacturer_name": "Test Inc",
                "is_software": True,
            },
            "samd_info": {
                "healthcare_situation": "serious",
                "significance": "diagnose",
            },
        }
        response = api_client.post("/api/v1/classify", json=request)
        assert response.status_code == 200

    def test_classify_returns_device_class(self, api_client):
        """Classification response should include device_class."""
        request = {
            "device_info": {
                "name": "Test Device",
                "description": "A test device",
                "intended_use": "Testing",
                "manufacturer_name": "Test Inc",
                "is_software": True,
            },
            "samd_info": {
                "healthcare_situation": "serious",
                "significance": "diagnose",
            },
        }
        response = api_client.post("/api/v1/classify", json=request)
        data = response.json()
        assert "device_class" in data
        assert data["device_class"] in ["I", "II", "III", "IV"]

    def test_classify_missing_device_info(self, api_client):
        """Request without device_info should return 422."""
        request = {"samd_info": {"healthcare_situation": "serious"}}
        response = api_client.post("/api/v1/classify", json=request)
        assert response.status_code == 422

    def test_classify_samd_returns_is_samd_true(self, api_client):
        """SaMD classification should set is_samd=True."""
        request = {
            "device_info": {
                "name": "Test SaMD",
                "description": "Software device",
                "intended_use": "Testing",
                "manufacturer_name": "Test Inc",
                "is_software": True,
            },
            "samd_info": {
                "healthcare_situation": "critical",
                "significance": "treat",
            },
        }
        response = api_client.post("/api/v1/classify", json=request)
        data = response.json()
        assert data["is_samd"] is True


@pytest.mark.api
class TestPathwayEndpoint:
    """Test /api/v1/pathway endpoint."""

    def test_pathway_valid_request(self, api_client):
        """Valid pathway request should return 200."""
        request = {
            "device_class": "III",
            "is_software": True,
        }
        response = api_client.post("/api/v1/pathway", json=request)
        assert response.status_code == 200

    def test_pathway_returns_steps(self, api_client):
        """Pathway response should include steps."""
        request = {
            "device_class": "III",
            "is_software": True,
        }
        response = api_client.post("/api/v1/pathway", json=request)
        data = response.json()
        assert "steps" in data
        assert isinstance(data["steps"], list)
        assert len(data["steps"]) > 0

    def test_pathway_returns_fees(self, api_client):
        """Pathway response should include fees."""
        request = {
            "device_class": "III",
            "is_software": True,
        }
        response = api_client.post("/api/v1/pathway", json=request)
        data = response.json()
        assert "fees" in data
        assert "total" in data["fees"]

    def test_pathway_invalid_class(self, api_client):
        """Invalid device class should return 422."""
        request = {
            "device_class": "V",  # Invalid
            "is_software": True,
        }
        response = api_client.post("/api/v1/pathway", json=request)
        assert response.status_code == 422


@pytest.mark.api
class TestSearchEndpoint:
    """Test /api/v1/search endpoint."""

    @pytest.mark.slow
    def test_search_valid_request(self, api_client):
        """Valid search request should return 200."""
        request = {
            "query": "MDEL requirements",
            "top_k": 3,
        }
        response = api_client.post("/api/v1/search", json=request)
        assert response.status_code == 200

    @pytest.mark.slow
    def test_search_returns_results(self, api_client):
        """Search should return results array."""
        request = {
            "query": "classification rules",
            "top_k": 3,
        }
        response = api_client.post("/api/v1/search", json=request)
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_search_missing_query(self, api_client):
        """Search without query should return 422."""
        request = {"top_k": 3}
        response = api_client.post("/api/v1/search", json=request)
        assert response.status_code == 422


@pytest.mark.api
class TestErrorHandling:
    """Test API error handling."""

    def test_404_for_unknown_endpoint(self, api_client):
        """Unknown endpoint should return 404."""
        response = api_client.get("/api/v1/unknown")
        assert response.status_code == 404

    def test_405_for_wrong_method(self, api_client):
        """Wrong HTTP method should return 405."""
        response = api_client.get("/api/v1/classify")  # Should be POST
        assert response.status_code == 405

    def test_422_for_invalid_json(self, api_client):
        """Invalid JSON should return 422."""
        response = api_client.post(
            "/api/v1/classify",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422
