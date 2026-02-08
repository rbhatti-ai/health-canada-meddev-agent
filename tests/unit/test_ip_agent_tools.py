"""
Tests for IP Classification Agent Tools — Sprint 6D

Tests the classify_confidentiality and get_ip_inventory tools.
All tests reset the confidentiality service singleton to ensure isolation.
"""

from uuid import uuid4

import pytest

from src.agents.tools import classify_confidentiality, get_ip_inventory
from src.core.confidentiality import reset_confidentiality_service

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def reset_service():
    """Reset the confidentiality service singleton before each test."""
    reset_confidentiality_service()
    yield
    reset_confidentiality_service()


# =============================================================================
# classify_confidentiality Tests
# =============================================================================


@pytest.mark.unit
class TestClassifyConfidentialityTool:
    """Tests for the classify_confidentiality agent tool."""

    def test_classify_public_success(self):
        """Should classify entity as public."""
        org_id = str(uuid4())
        entity_id = str(uuid4())

        result = classify_confidentiality.invoke(
            {
                "entity_type": "evidence_item",
                "entity_id": entity_id,
                "organization_id": org_id,
                "level": "public",
            }
        )

        assert result["success"] is True
        assert result["level"] == "public"
        assert result["requires_cbi_request"] is False

    def test_classify_trade_secret_success(self):
        """Should classify entity as trade_secret with required fields."""
        org_id = str(uuid4())
        entity_id = str(uuid4())

        result = classify_confidentiality.invoke(
            {
                "entity_type": "evidence_item",
                "entity_id": entity_id,
                "organization_id": org_id,
                "level": "trade_secret",
                "justification": "Proprietary algorithm",
                "harm_if_disclosed": "Competitor advantage lost",
            }
        )

        assert result["success"] is True
        assert result["level"] == "trade_secret"
        assert result["requires_cbi_request"] is True

    def test_classify_patent_pending_success(self):
        """Should classify entity as patent_pending with patent number."""
        org_id = str(uuid4())
        entity_id = str(uuid4())

        result = classify_confidentiality.invoke(
            {
                "entity_type": "evidence_item",
                "entity_id": entity_id,
                "organization_id": org_id,
                "level": "patent_pending",
                "patent_number": "US2024/123456",
            }
        )

        assert result["success"] is True
        assert result["level"] == "patent_pending"
        assert result["requires_cbi_request"] is False

    def test_classify_confidential_submission_success(self):
        """Should classify entity as confidential_submission."""
        org_id = str(uuid4())
        entity_id = str(uuid4())

        result = classify_confidentiality.invoke(
            {
                "entity_type": "artifact",
                "entity_id": entity_id,
                "organization_id": org_id,
                "level": "confidential_submission",
                "justification": "Manufacturing details",
                "harm_if_disclosed": "Process could be replicated",
            }
        )

        assert result["success"] is True
        assert result["level"] == "confidential_submission"
        assert result["requires_cbi_request"] is True

    def test_invalid_level_returns_error(self):
        """Should return error for invalid level."""
        result = classify_confidentiality.invoke(
            {
                "entity_type": "evidence_item",
                "entity_id": str(uuid4()),
                "organization_id": str(uuid4()),
                "level": "super_secret",
            }
        )

        assert result["success"] is False
        assert "Invalid level" in result["error"]

    def test_invalid_uuid_returns_error(self):
        """Should return error for invalid UUID."""
        result = classify_confidentiality.invoke(
            {
                "entity_type": "evidence_item",
                "entity_id": "not-a-uuid",
                "organization_id": str(uuid4()),
                "level": "public",
            }
        )

        assert result["success"] is False
        assert "Invalid UUID" in result["error"]

    def test_trade_secret_without_justification_returns_error(self):
        """Should require justification for trade_secret."""
        result = classify_confidentiality.invoke(
            {
                "entity_type": "evidence_item",
                "entity_id": str(uuid4()),
                "organization_id": str(uuid4()),
                "level": "trade_secret",
                "harm_if_disclosed": "Competitive harm",
            }
        )

        assert result["success"] is False
        assert "justification" in result["error"]

    def test_trade_secret_without_harm_returns_error(self):
        """Should require harm_if_disclosed for trade_secret."""
        result = classify_confidentiality.invoke(
            {
                "entity_type": "evidence_item",
                "entity_id": str(uuid4()),
                "organization_id": str(uuid4()),
                "level": "trade_secret",
                "justification": "Proprietary",
            }
        )

        assert result["success"] is False
        assert "harm_if_disclosed" in result["error"]

    def test_patent_pending_without_number_returns_error(self):
        """Should require patent_number for patent_pending."""
        result = classify_confidentiality.invoke(
            {
                "entity_type": "evidence_item",
                "entity_id": str(uuid4()),
                "organization_id": str(uuid4()),
                "level": "patent_pending",
            }
        )

        assert result["success"] is False
        assert "patent_number" in result["error"]

    def test_result_includes_citation(self):
        """Should include regulatory citation in result."""
        result = classify_confidentiality.invoke(
            {
                "entity_type": "evidence_item",
                "entity_id": str(uuid4()),
                "organization_id": str(uuid4()),
                "level": "public",
            }
        )

        assert result["success"] is True
        assert "SOR/98-282" in result["citation"]


# =============================================================================
# get_ip_inventory Tests
# =============================================================================


@pytest.mark.unit
class TestGetIPInventoryTool:
    """Tests for the get_ip_inventory agent tool."""

    def test_empty_inventory(self):
        """Should return empty inventory for org with no classifications."""
        org_id = str(uuid4())

        result = get_ip_inventory.invoke({"organization_id": org_id})

        assert result["success"] is True
        assert result["summary"]["total_classified"] == 0
        assert result["cbi_status"]["requires_cbi_request"] is False

    def test_inventory_with_classifications(self):
        """Should count classifications by level."""
        org_id = str(uuid4())

        # Add some classifications
        classify_confidentiality.invoke(
            {
                "entity_type": "evidence_item",
                "entity_id": str(uuid4()),
                "organization_id": org_id,
                "level": "public",
            }
        )
        classify_confidentiality.invoke(
            {
                "entity_type": "evidence_item",
                "entity_id": str(uuid4()),
                "organization_id": org_id,
                "level": "trade_secret",
                "justification": "Secret",
                "harm_if_disclosed": "Harm",
            }
        )

        result = get_ip_inventory.invoke({"organization_id": org_id})

        assert result["success"] is True
        assert result["summary"]["public_count"] == 1
        assert result["summary"]["trade_secret_count"] == 1
        assert result["summary"]["total_classified"] == 2

    def test_cbi_status_with_trade_secrets(self):
        """Should indicate CBI request needed when trade secrets exist."""
        org_id = str(uuid4())

        classify_confidentiality.invoke(
            {
                "entity_type": "evidence_item",
                "entity_id": str(uuid4()),
                "organization_id": org_id,
                "level": "trade_secret",
                "justification": "Secret",
                "harm_if_disclosed": "Harm",
            }
        )

        result = get_ip_inventory.invoke({"organization_id": org_id})

        assert result["cbi_status"]["requires_cbi_request"] is True
        assert result["cbi_status"]["cbi_item_count"] == 1

    def test_trade_secrets_list(self):
        """Should list trade secrets with attestation status."""
        org_id = str(uuid4())
        entity_id = str(uuid4())

        classify_confidentiality.invoke(
            {
                "entity_type": "evidence_item",
                "entity_id": entity_id,
                "organization_id": org_id,
                "level": "trade_secret",
                "justification": "Secret",
                "harm_if_disclosed": "Harm",
            }
        )

        result = get_ip_inventory.invoke({"organization_id": org_id})

        assert len(result["trade_secrets"]) == 1
        assert result["trade_secrets"][0]["entity_id"] == entity_id
        assert result["trade_secrets"][0]["has_attestation"] is False

    def test_patents_pending_list(self):
        """Should list patent pending items with application numbers."""
        org_id = str(uuid4())
        entity_id = str(uuid4())

        classify_confidentiality.invoke(
            {
                "entity_type": "evidence_item",
                "entity_id": entity_id,
                "organization_id": org_id,
                "level": "patent_pending",
                "patent_number": "US2024/999",
            }
        )

        result = get_ip_inventory.invoke({"organization_id": org_id})

        assert len(result["patents_pending"]) == 1
        assert result["patents_pending"][0]["patent_application_number"] == "US2024/999"

    def test_invalid_org_id_returns_error(self):
        """Should return error for invalid organization ID."""
        result = get_ip_inventory.invoke({"organization_id": "not-a-uuid"})

        assert result["success"] is False
        assert "Invalid" in result["error"]

    def test_result_includes_citation(self):
        """Should include regulatory citation in result."""
        result = get_ip_inventory.invoke({"organization_id": str(uuid4())})

        assert result["success"] is True
        assert "SOR/98-282" in result["citation"]
