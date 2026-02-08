"""
Tests for src/core/confidentiality.py — Sprint 6A.

Covers:
- ConfidentialityTag model
- ConfidentialityService methods
- Classification levels
- CBI candidate detection
- Unclassified asset detection
- Report generation
"""

from uuid import uuid4

import pytest

from src.core.confidentiality import (
    CLASSIFIABLE_ENTITY_TYPES,
    ConfidentialityLevel,
    ConfidentialityService,
    ConfidentialityTag,
    get_confidentiality_service,
    reset_confidentiality_service,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def service():
    """Fresh ConfidentialityService for each test."""
    reset_confidentiality_service()
    return ConfidentialityService()


@pytest.fixture
def org_id():
    """Sample organization ID."""
    return uuid4()


@pytest.fixture
def user_id():
    """Sample user ID."""
    return uuid4()


@pytest.fixture
def entity_id():
    """Sample entity ID."""
    return uuid4()


# =============================================================================
# ConfidentialityTag Model Tests
# =============================================================================


@pytest.mark.unit
class TestConfidentialityTagModel:
    """Tests for ConfidentialityTag Pydantic model."""

    def test_valid_tag_public(self, org_id, entity_id):
        """ConfidentialityTag should accept public level."""
        tag = ConfidentialityTag(
            organization_id=org_id,
            entity_type="evidence_item",
            entity_id=entity_id,
            level="public",
        )
        assert tag.level == "public"
        assert tag.organization_id == org_id
        assert tag.entity_id == entity_id

    def test_valid_tag_trade_secret(self, org_id, entity_id):
        """ConfidentialityTag should accept trade_secret level."""
        tag = ConfidentialityTag(
            organization_id=org_id,
            entity_type="artifact",
            entity_id=entity_id,
            level="trade_secret",
            trade_secret_attestation=True,
            justification="Proprietary algorithm",
            harm_if_disclosed="Competitive advantage lost",
        )
        assert tag.level == "trade_secret"
        assert tag.trade_secret_attestation is True
        assert tag.justification == "Proprietary algorithm"

    def test_valid_tag_patent_pending(self, org_id, entity_id):
        """ConfidentialityTag should accept patent_pending level."""
        tag = ConfidentialityTag(
            organization_id=org_id,
            entity_type="design_file",
            entity_id=entity_id,
            level="patent_pending",
            patent_application_number="CA2024/123456",
        )
        assert tag.level == "patent_pending"
        assert tag.patent_application_number == "CA2024/123456"

    def test_valid_tag_confidential_submission(self, org_id, entity_id):
        """ConfidentialityTag should accept confidential_submission level."""
        tag = ConfidentialityTag(
            organization_id=org_id,
            entity_type="test_data",
            entity_id=entity_id,
            level="confidential_submission",
            summary_for_public_use="Summary of test results",
        )
        assert tag.level == "confidential_submission"
        assert tag.summary_for_public_use == "Summary of test results"

    def test_tag_has_citation_fields(self, org_id, entity_id):
        """Tag should have citation fields (Sprint 5C alignment)."""
        tag = ConfidentialityTag(
            organization_id=org_id,
            entity_type="evidence_item",
            entity_id=entity_id,
            level="public",
        )
        assert tag.regulation_ref == "SOR-98-282-S43.2"
        assert tag.citation_text == "[SOR/98-282, s.43.2]"

    def test_tag_defaults(self, org_id, entity_id):
        """Tag should have correct default values."""
        tag = ConfidentialityTag(
            organization_id=org_id,
            entity_type="evidence_item",
            entity_id=entity_id,
            level="public",
        )
        assert tag.id is None
        assert tag.patent_application_number is None
        assert tag.trade_secret_attestation is False
        assert tag.disclosure_restrictions == []
        assert tag.classified_by is None
        assert tag.classified_at is None


# =============================================================================
# ConfidentialityService Tests
# =============================================================================


@pytest.mark.unit
class TestConfidentialityServiceClassify:
    """Tests for ConfidentialityService.classify() method."""

    def test_classify_public(self, service, org_id, entity_id):
        """classify() should create a public classification."""
        tag = service.classify(
            entity_type="evidence_item",
            entity_id=entity_id,
            level="public",
            organization_id=org_id,
        )
        assert tag.level == "public"
        assert tag.classified_at is not None

    def test_classify_trade_secret(self, service, org_id, entity_id, user_id):
        """classify() should create a trade_secret classification."""
        tag = service.classify(
            entity_type="artifact",
            entity_id=entity_id,
            level="trade_secret",
            organization_id=org_id,
            classified_by=user_id,
            trade_secret_attestation=True,
            justification="Proprietary manufacturing process",
            harm_if_disclosed="Loss of competitive advantage",
        )
        assert tag.level == "trade_secret"
        assert tag.trade_secret_attestation is True
        assert tag.classified_by == user_id

    def test_classify_patent_pending_requires_number(self, service, org_id, entity_id):
        """patent_pending level requires patent_application_number."""
        with pytest.raises(ValueError, match="patent_application_number required"):
            service.classify(
                entity_type="design_file",
                entity_id=entity_id,
                level="patent_pending",
                organization_id=org_id,
            )

    def test_classify_patent_pending_with_number(self, service, org_id, entity_id):
        """patent_pending level works with application number."""
        tag = service.classify(
            entity_type="design_file",
            entity_id=entity_id,
            level="patent_pending",
            organization_id=org_id,
            patent_application_number="CA2024/789012",
        )
        assert tag.level == "patent_pending"
        assert tag.patent_application_number == "CA2024/789012"

    def test_classify_invalid_entity_type(self, service, org_id, entity_id):
        """classify() should reject invalid entity types."""
        with pytest.raises(ValueError, match="Invalid entity_type"):
            service.classify(
                entity_type="invalid_type",
                entity_id=entity_id,
                level="public",
                organization_id=org_id,
            )

    def test_classify_all_valid_entity_types(self, service, org_id):
        """classify() should accept all valid entity types."""
        for entity_type in CLASSIFIABLE_ENTITY_TYPES:
            tag = service.classify(
                entity_type=entity_type,
                entity_id=uuid4(),
                level="public",
                organization_id=org_id,
            )
            assert tag.entity_type == entity_type


@pytest.mark.unit
class TestConfidentialityServiceQuery:
    """Tests for ConfidentialityService query methods."""

    def test_get_classification(self, service, org_id, entity_id):
        """get_classification() should return existing classification."""
        service.classify("evidence_item", entity_id, "public", org_id)
        tag = service.get_classification("evidence_item", entity_id)
        assert tag is not None
        assert tag.level == "public"

    def test_get_classification_not_found(self, service):
        """get_classification() should return None for unclassified."""
        tag = service.get_classification("evidence_item", uuid4())
        assert tag is None

    def test_get_all_classifications(self, service, org_id):
        """get_all_classifications() should return all org classifications."""
        id1, id2, id3 = uuid4(), uuid4(), uuid4()
        service.classify("evidence_item", id1, "public", org_id)
        service.classify("artifact", id2, "trade_secret", org_id, trade_secret_attestation=True)
        service.classify("claim", id3, "confidential_submission", org_id)

        all_tags = service.get_all_classifications(org_id)
        assert len(all_tags) == 3

    def test_get_all_classifications_filters_by_org(self, service):
        """get_all_classifications() should filter by organization."""
        org1, org2 = uuid4(), uuid4()
        service.classify("evidence_item", uuid4(), "public", org1)
        service.classify("artifact", uuid4(), "public", org2)

        org1_tags = service.get_all_classifications(org1)
        org2_tags = service.get_all_classifications(org2)

        assert len(org1_tags) == 1
        assert len(org2_tags) == 1

    def test_get_by_level(self, service, org_id):
        """get_by_level() should filter by confidentiality level."""
        service.classify("evidence_item", uuid4(), "public", org_id)
        service.classify("artifact", uuid4(), "public", org_id)
        service.classify("claim", uuid4(), "trade_secret", org_id, trade_secret_attestation=True)

        public = service.get_by_level(org_id, "public")
        trade_secret = service.get_by_level(org_id, "trade_secret")

        assert len(public) == 2
        assert len(trade_secret) == 1

    def test_get_trade_secrets(self, service, org_id):
        """get_trade_secrets() should return only trade secrets."""
        service.classify("evidence_item", uuid4(), "public", org_id)
        service.classify("artifact", uuid4(), "trade_secret", org_id, trade_secret_attestation=True)
        service.classify(
            "design_file", uuid4(), "trade_secret", org_id, trade_secret_attestation=True
        )

        secrets = service.get_trade_secrets(org_id)
        assert len(secrets) == 2
        assert all(t.level == "trade_secret" for t in secrets)

    def test_get_patent_pending(self, service, org_id):
        """get_patent_pending() should return only patent pending."""
        service.classify("evidence_item", uuid4(), "public", org_id)
        service.classify(
            "design_file",
            uuid4(),
            "patent_pending",
            org_id,
            patent_application_number="CA2024/111111",
        )

        patents = service.get_patent_pending(org_id)
        assert len(patents) == 1
        assert patents[0].level == "patent_pending"

    def test_get_cbi_candidates(self, service, org_id):
        """get_cbi_candidates() should return trade_secret + confidential_submission."""
        service.classify("evidence_item", uuid4(), "public", org_id)
        service.classify("artifact", uuid4(), "trade_secret", org_id, trade_secret_attestation=True)
        service.classify("claim", uuid4(), "confidential_submission", org_id)
        service.classify(
            "design_file", uuid4(), "patent_pending", org_id, patent_application_number="CA123"
        )

        cbi = service.get_cbi_candidates(org_id)
        assert len(cbi) == 2
        levels = {t.level for t in cbi}
        assert levels == {"trade_secret", "confidential_submission"}


@pytest.mark.unit
class TestConfidentialityServiceDisclosure:
    """Tests for disclosure-related methods."""

    def test_is_disclosable_public(self, service, org_id, entity_id):
        """Public entities are disclosable."""
        service.classify("evidence_item", entity_id, "public", org_id)
        assert service.is_disclosable("evidence_item", entity_id) is True

    def test_is_disclosable_unclassified(self, service):
        """Unclassified entities default to disclosable."""
        assert service.is_disclosable("evidence_item", uuid4()) is True

    def test_is_disclosable_trade_secret(self, service, org_id, entity_id):
        """Trade secrets are not disclosable."""
        service.classify(
            "evidence_item", entity_id, "trade_secret", org_id, trade_secret_attestation=True
        )
        assert service.is_disclosable("evidence_item", entity_id) is False

    def test_requires_redaction_trade_secret(self, service, org_id, entity_id):
        """Trade secrets require redaction."""
        service.classify(
            "evidence_item", entity_id, "trade_secret", org_id, trade_secret_attestation=True
        )
        assert service.requires_redaction("evidence_item", entity_id) is True

    def test_requires_redaction_confidential_submission(self, service, org_id, entity_id):
        """Confidential submission requires redaction."""
        service.classify("evidence_item", entity_id, "confidential_submission", org_id)
        assert service.requires_redaction("evidence_item", entity_id) is True

    def test_requires_redaction_public(self, service, org_id, entity_id):
        """Public entities don't require redaction."""
        service.classify("evidence_item", entity_id, "public", org_id)
        assert service.requires_redaction("evidence_item", entity_id) is False

    def test_requires_redaction_unclassified(self, service):
        """Unclassified entities don't require redaction."""
        assert service.requires_redaction("evidence_item", uuid4()) is False


@pytest.mark.unit
class TestConfidentialityServiceUnclassified:
    """Tests for unclassified asset detection."""

    def test_get_unclassified(self, service, org_id):
        """get_unclassified() should return entities without classification."""
        id1, id2, id3 = uuid4(), uuid4(), uuid4()
        known = [
            ("evidence_item", id1),
            ("artifact", id2),
            ("claim", id3),
        ]

        # Classify only id1
        service.classify("evidence_item", id1, "public", org_id)

        unclassified = service.get_unclassified(org_id, known)
        assert len(unclassified) == 2
        assert ("artifact", id2) in unclassified
        assert ("claim", id3) in unclassified

    def test_get_unclassified_all_classified(self, service, org_id):
        """get_unclassified() should return empty if all classified."""
        id1, id2 = uuid4(), uuid4()
        known = [("evidence_item", id1), ("artifact", id2)]

        service.classify("evidence_item", id1, "public", org_id)
        service.classify("artifact", id2, "trade_secret", org_id, trade_secret_attestation=True)

        unclassified = service.get_unclassified(org_id, known)
        assert len(unclassified) == 0


@pytest.mark.unit
class TestConfidentialityServiceReport:
    """Tests for report generation."""

    def test_generate_report_empty(self, service, org_id):
        """generate_report() should work with no classifications."""
        report = service.generate_report(org_id)
        assert report.total_entities == 0
        assert report.requires_cbi_request is False

    def test_generate_report_with_classifications(self, service, org_id):
        """generate_report() should count classifications correctly."""
        service.classify("evidence_item", uuid4(), "public", org_id)
        service.classify("artifact", uuid4(), "public", org_id)
        service.classify("claim", uuid4(), "trade_secret", org_id, trade_secret_attestation=True)
        service.classify("design_file", uuid4(), "confidential_submission", org_id)
        service.classify(
            "test_data", uuid4(), "patent_pending", org_id, patent_application_number="CA123"
        )

        report = service.generate_report(org_id)
        assert report.public_count == 2
        assert report.trade_secret_count == 1
        assert report.confidential_submission_count == 1
        assert report.patent_pending_count == 1
        assert report.requires_cbi_request is True

    def test_generate_report_with_unclassified(self, service, org_id):
        """generate_report() should track unclassified entities."""
        id1, id2 = uuid4(), uuid4()
        known = [("evidence_item", id1), ("artifact", id2)]

        service.classify("evidence_item", id1, "public", org_id)

        report = service.generate_report(org_id, known_entities=known)
        assert report.unclassified_count == 1
        assert len(report.unclassified_entities) == 1

    def test_report_requires_cbi_trade_secret(self, service, org_id):
        """Report should flag CBI requirement for trade secrets."""
        service.classify("artifact", uuid4(), "trade_secret", org_id, trade_secret_attestation=True)
        report = service.generate_report(org_id)
        assert report.requires_cbi_request is True

    def test_report_requires_cbi_confidential_submission(self, service, org_id):
        """Report should flag CBI requirement for confidential submissions."""
        service.classify("artifact", uuid4(), "confidential_submission", org_id)
        report = service.generate_report(org_id)
        assert report.requires_cbi_request is True


@pytest.mark.unit
class TestConfidentialityServiceMisc:
    """Miscellaneous service tests."""

    def test_remove_classification(self, service, org_id, entity_id):
        """remove_classification() should delete a classification."""
        service.classify("evidence_item", entity_id, "public", org_id)
        assert service.get_classification("evidence_item", entity_id) is not None

        removed = service.remove_classification("evidence_item", entity_id)
        assert removed is True
        assert service.get_classification("evidence_item", entity_id) is None

    def test_remove_classification_not_found(self, service):
        """remove_classification() should return False if not found."""
        removed = service.remove_classification("evidence_item", uuid4())
        assert removed is False

    def test_count(self, service, org_id):
        """count() should return total classifications."""
        assert service.count() == 0
        service.classify("evidence_item", uuid4(), "public", org_id)
        service.classify("artifact", uuid4(), "trade_secret", org_id, trade_secret_attestation=True)
        assert service.count() == 2

    def test_count_by_org(self, service):
        """count() should filter by organization."""
        org1, org2 = uuid4(), uuid4()
        service.classify("evidence_item", uuid4(), "public", org1)
        service.classify("artifact", uuid4(), "public", org1)
        service.classify("claim", uuid4(), "public", org2)

        assert service.count(org1) == 2
        assert service.count(org2) == 1


@pytest.mark.unit
class TestSingleton:
    """Tests for singleton pattern."""

    def test_get_confidentiality_service_returns_instance(self):
        """get_confidentiality_service() should return a service."""
        reset_confidentiality_service()
        service = get_confidentiality_service()
        assert isinstance(service, ConfidentialityService)

    def test_get_confidentiality_service_is_singleton(self):
        """get_confidentiality_service() should return same instance."""
        reset_confidentiality_service()
        s1 = get_confidentiality_service()
        s2 = get_confidentiality_service()
        assert s1 is s2

    def test_reset_clears_singleton(self):
        """reset_confidentiality_service() should clear the singleton."""
        s1 = get_confidentiality_service()
        reset_confidentiality_service()
        s2 = get_confidentiality_service()
        assert s1 is not s2


@pytest.mark.unit
class TestConfidentialityLevels:
    """Tests for confidentiality level constants."""

    def test_all_levels_valid(self):
        """All defined levels should be valid ConfidentialityLevel."""
        levels: list[ConfidentialityLevel] = [
            "public",
            "confidential_submission",
            "trade_secret",
            "patent_pending",
        ]
        assert len(levels) == 4

    def test_classifiable_entity_types(self):
        """CLASSIFIABLE_ENTITY_TYPES should have expected types."""
        assert "evidence_item" in CLASSIFIABLE_ENTITY_TYPES
        assert "artifact" in CLASSIFIABLE_ENTITY_TYPES
        assert "claim" in CLASSIFIABLE_ENTITY_TYPES
        assert "design_file" in CLASSIFIABLE_ENTITY_TYPES
        assert len(CLASSIFIABLE_ENTITY_TYPES) >= 5
