"""
API tests for traceability, evidence, and attestation endpoints.

Tests route registration, request validation, valid relationships
endpoint, and error handling. No DB connection required.

Sprint 2d — 2026-02-07
"""

from __future__ import annotations

from uuid import uuid4

# =========================================================================
# Test: Route Registration
# =========================================================================


class TestRouteRegistration:
    """Test that all traceability routes are registered."""

    def test_trace_links_post_exists(self, api_client) -> None:
        """POST /api/v1/trace-links should exist (not 404/405)."""
        response = api_client.post(
            "/api/v1/trace-links",
            json={
                "organization_id": str(uuid4()),
                "source_type": "claim",
                "source_id": str(uuid4()),
                "target_type": "hazard",
                "target_id": str(uuid4()),
                "relationship": "addresses",
            },
        )
        # Should be 422 (invalid link/no DB) or 500, NOT 404
        assert response.status_code != 404

    def test_valid_relationships_get_exists(self, api_client) -> None:
        """GET /api/v1/trace-links/valid-relationships should return 200."""
        response = api_client.get("/api/v1/trace-links/valid-relationships")
        assert response.status_code == 200

    def test_trace_chain_get_exists(self, api_client) -> None:
        """GET /api/v1/trace-chains/{type}/{id} should exist."""
        response = api_client.get(f"/api/v1/trace-chains/claim/{uuid4()}")
        assert response.status_code != 404

    def test_coverage_get_exists(self, api_client) -> None:
        """GET /api/v1/coverage/{id} should exist."""
        response = api_client.get(
            f"/api/v1/coverage/{uuid4()}",
            params={"organization_id": str(uuid4())},
        )
        assert response.status_code != 404

    def test_evidence_post_exists(self, api_client) -> None:
        """POST /api/v1/evidence should exist."""
        response = api_client.post(
            "/api/v1/evidence",
            json={
                "organization_id": str(uuid4()),
                "device_version_id": str(uuid4()),
                "evidence_type": "test_report",
                "title": "Test Report",
            },
        )
        assert response.status_code != 404

    def test_attestation_post_exists(self, api_client) -> None:
        """POST /api/v1/attestations should exist."""
        response = api_client.post(
            "/api/v1/attestations",
            json={
                "organization_id": str(uuid4()),
                "artifact_id": str(uuid4()),
                "attested_by": str(uuid4()),
                "attestation_type": "reviewed",
            },
        )
        assert response.status_code != 404

    def test_pending_attestations_get_exists(self, api_client) -> None:
        """GET /api/v1/attestations/pending/{org_id} should exist."""
        response = api_client.get(f"/api/v1/attestations/pending/{uuid4()}")
        assert response.status_code != 404

    def test_attestation_trail_get_exists(self, api_client) -> None:
        """GET /api/v1/attestations/trail/{artifact_id} should exist."""
        response = api_client.get(f"/api/v1/attestations/trail/{uuid4()}")
        assert response.status_code != 404

    def test_attestation_status_get_exists(self, api_client) -> None:
        """GET /api/v1/attestations/status/{artifact_id} should exist."""
        response = api_client.get(f"/api/v1/attestations/status/{uuid4()}")
        assert response.status_code != 404


# =========================================================================
# Test: Valid Relationships Endpoint
# =========================================================================


class TestValidRelationshipsEndpoint:
    """Test the valid-relationships endpoint."""

    def test_returns_relationships_key(self, api_client) -> None:
        response = api_client.get("/api/v1/trace-links/valid-relationships")
        data = response.json()
        assert "relationships" in data

    def test_returns_9_relationship_types(self, api_client) -> None:
        response = api_client.get("/api/v1/trace-links/valid-relationships")
        data = response.json()
        # 9 risk management + 7 design control = 16
        assert len(data["relationships"]) == 16

    def test_claim_hazard_in_relationships(self, api_client) -> None:
        response = api_client.get("/api/v1/trace-links/valid-relationships")
        data = response.json()
        assert "claim->hazard" in data["relationships"]
        assert "addresses" in data["relationships"]["claim->hazard"]

    def test_hazard_harm_in_relationships(self, api_client) -> None:
        response = api_client.get("/api/v1/trace-links/valid-relationships")
        data = response.json()
        assert "hazard->harm" in data["relationships"]
        assert "causes" in data["relationships"]["hazard->harm"]
        assert "may_cause" in data["relationships"]["hazard->harm"]


# =========================================================================
# Test: Request Validation
# =========================================================================


class TestRequestValidation:
    """Test that invalid requests return proper errors."""

    def test_invalid_trace_link_relationship(self, api_client) -> None:
        """Invalid relationship should return 422."""
        response = api_client.post(
            "/api/v1/trace-links",
            json={
                "organization_id": str(uuid4()),
                "source_type": "claim",
                "source_id": str(uuid4()),
                "target_type": "hazard",
                "target_id": str(uuid4()),
                "relationship": "invalid_rel",
            },
        )
        assert response.status_code == 422

    def test_reversed_relationship_rejected(self, api_client) -> None:
        """hazard -> claim with 'addresses' should be rejected."""
        response = api_client.post(
            "/api/v1/trace-links",
            json={
                "organization_id": str(uuid4()),
                "source_type": "hazard",
                "source_id": str(uuid4()),
                "target_type": "claim",
                "target_id": str(uuid4()),
                "relationship": "addresses",
            },
        )
        assert response.status_code == 422

    def test_attestation_both_ids_rejected(self, api_client) -> None:
        """Providing both artifact_id and artifact_link_id should fail."""
        response = api_client.post(
            "/api/v1/attestations",
            json={
                "organization_id": str(uuid4()),
                "artifact_id": str(uuid4()),
                "artifact_link_id": str(uuid4()),
                "attested_by": str(uuid4()),
                "attestation_type": "reviewed",
            },
        )
        assert response.status_code == 422

    def test_attestation_neither_id_rejected(self, api_client) -> None:
        """Providing neither artifact_id nor artifact_link_id should fail."""
        response = api_client.post(
            "/api/v1/attestations",
            json={
                "organization_id": str(uuid4()),
                "attested_by": str(uuid4()),
                "attestation_type": "reviewed",
            },
        )
        assert response.status_code == 422

    def test_missing_required_fields_trace_link(self, api_client) -> None:
        """Missing required fields should return 422."""
        response = api_client.post(
            "/api/v1/trace-links",
            json={"source_type": "claim"},
        )
        assert response.status_code == 422

    def test_missing_required_fields_evidence(self, api_client) -> None:
        """Missing required fields should return 422."""
        response = api_client.post(
            "/api/v1/evidence",
            json={"title": "missing fields"},
        )
        assert response.status_code == 422
