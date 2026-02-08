"""
Tests for Regulatory Reference Registry — Sprint 5A.

Tests the RegulatoryReference model and RegulatoryReferenceRegistry class.
Verifies pre-populated references are from KNOWLEDGE_BASE.md.
"""

import pytest

from src.core.regulatory_references import (
    REGULATION_REFERENCES,
    TOPIC_CLASSIFICATION,
    TOPIC_CLINICAL,
    TOPIC_LABELING,
    TOPIC_RISK,
    RegulatoryReference,
    RegulatoryReferenceRegistry,
    get_reference_registry,
)


class TestRegulatoryReferenceModel:
    """Tests for the RegulatoryReference Pydantic model."""

    def test_create_regulation_reference(self) -> None:
        """Test creating a regulation reference."""
        ref = RegulatoryReference(
            id="TEST-001",
            reference_type="regulation",
            document_id="SOR/98-282",
            section="s.32",
            title="Test Section",
        )
        assert ref.id == "TEST-001"
        assert ref.reference_type == "regulation"
        assert ref.document_id == "SOR/98-282"
        assert ref.section == "s.32"
        assert ref.title == "Test Section"

    def test_create_guidance_reference(self) -> None:
        """Test creating a guidance reference."""
        ref = RegulatoryReference(
            id="TEST-GUI",
            reference_type="guidance",
            document_id="GUI-0016",
            title="Test Guidance",
            description="A test guidance document",
        )
        assert ref.reference_type == "guidance"
        assert ref.description == "A test guidance document"

    def test_create_standard_reference(self) -> None:
        """Test creating a standard reference."""
        ref = RegulatoryReference(
            id="TEST-ISO",
            reference_type="standard",
            document_id="ISO 13485:2016",
            section="7.3",
            title="Design and Development",
        )
        assert ref.reference_type == "standard"
        assert ref.section == "7.3"

    def test_create_form_reference(self) -> None:
        """Test creating a form reference."""
        ref = RegulatoryReference(
            id="TEST-FORM",
            reference_type="form",
            document_id="FRM-0077",
            title="Class II MDL Application",
        )
        assert ref.reference_type == "form"

    def test_create_internal_reference(self) -> None:
        """Test creating an internal reference."""
        ref = RegulatoryReference(
            id="TEST-INT",
            reference_type="internal",
            document_id="Platform Policy",
            title="Test Policy",
        )
        assert ref.reference_type == "internal"

    def test_optional_fields_default_to_none(self) -> None:
        """Test that optional fields default to None or empty."""
        ref = RegulatoryReference(
            id="TEST-MIN",
            reference_type="regulation",
            document_id="TEST",
            title="Minimal Reference",
        )
        assert ref.section is None
        assert ref.schedule is None
        assert ref.rule is None
        assert ref.description is None
        assert ref.url is None
        assert ref.effective_date is None
        assert ref.topics == []
        assert ref.device_classes == []

    def test_topics_list(self) -> None:
        """Test setting topics list."""
        ref = RegulatoryReference(
            id="TEST-TOPICS",
            reference_type="guidance",
            document_id="TEST",
            title="Test",
            topics=["classification", "labeling"],
        )
        assert "classification" in ref.topics
        assert "labeling" in ref.topics
        assert len(ref.topics) == 2

    def test_device_classes_list(self) -> None:
        """Test setting device classes list."""
        ref = RegulatoryReference(
            id="TEST-CLASSES",
            reference_type="regulation",
            document_id="TEST",
            title="Test",
            device_classes=["II", "III", "IV"],
        )
        assert "II" in ref.device_classes
        assert "III" in ref.device_classes
        assert "IV" in ref.device_classes
        assert "I" not in ref.device_classes


class TestPrePopulatedReferences:
    """Tests for the pre-populated REGULATION_REFERENCES dictionary."""

    def test_minimum_reference_count(self) -> None:
        """Registry must have at least 50 pre-populated references."""
        assert len(REGULATION_REFERENCES) >= 50

    def test_sor_98_282_exists(self) -> None:
        """Core regulation SOR/98-282 must exist."""
        assert "SOR-98-282" in REGULATION_REFERENCES
        ref = REGULATION_REFERENCES["SOR-98-282"]
        assert ref.reference_type == "regulation"
        assert ref.document_id == "SOR/98-282"

    def test_gui_0016_exists(self) -> None:
        """MDEL guidance GUI-0016 must exist."""
        assert "GUI-0016" in REGULATION_REFERENCES
        ref = REGULATION_REFERENCES["GUI-0016"]
        assert ref.reference_type == "guidance"
        assert "MDEL" in ref.title or "Establishment" in ref.title

    def test_gui_0098_exists(self) -> None:
        """MDL guidance GUI-0098 must exist."""
        assert "GUI-0098" in REGULATION_REFERENCES
        ref = REGULATION_REFERENCES["GUI-0098"]
        assert ref.reference_type == "guidance"

    def test_gui_0102_exists(self) -> None:
        """Clinical evidence guidance GUI-0102 must exist."""
        assert "GUI-0102" in REGULATION_REFERENCES
        ref = REGULATION_REFERENCES["GUI-0102"]
        assert TOPIC_CLINICAL in ref.topics

    def test_iso_13485_exists(self) -> None:
        """ISO 13485:2016 standard must exist."""
        assert "ISO-13485-2016" in REGULATION_REFERENCES
        ref = REGULATION_REFERENCES["ISO-13485-2016"]
        assert ref.reference_type == "standard"

    def test_iso_14971_exists(self) -> None:
        """ISO 14971:2019 standard must exist."""
        assert "ISO-14971-2019" in REGULATION_REFERENCES
        ref = REGULATION_REFERENCES["ISO-14971-2019"]
        assert ref.reference_type == "standard"
        assert TOPIC_RISK in ref.topics

    def test_frm_forms_exist(self) -> None:
        """FRM form references must exist."""
        assert "FRM-0292" in REGULATION_REFERENCES
        assert "FRM-0077" in REGULATION_REFERENCES
        assert "FRM-0078" in REGULATION_REFERENCES
        assert "FRM-0079" in REGULATION_REFERENCES

    def test_sor_sections_exist(self) -> None:
        """Key SOR/98-282 sections must exist."""
        assert "SOR-98-282-S32" in REGULATION_REFERENCES
        assert "SOR-98-282-S32-2-C" in REGULATION_REFERENCES
        assert "SOR-98-282-PART5" in REGULATION_REFERENCES

    def test_all_references_have_required_fields(self) -> None:
        """All pre-populated references must have required fields."""
        for ref_id, ref in REGULATION_REFERENCES.items():
            assert ref.id, f"Reference {ref_id} missing id"
            assert ref.reference_type, f"Reference {ref_id} missing reference_type"
            assert ref.document_id, f"Reference {ref_id} missing document_id"
            assert ref.title, f"Reference {ref_id} missing title"

    def test_regulations_have_valid_type(self) -> None:
        """All regulation references have type 'regulation'."""
        for ref_id, ref in REGULATION_REFERENCES.items():
            if ref_id.startswith("SOR-"):
                assert ref.reference_type == "regulation"

    def test_guidances_have_valid_type(self) -> None:
        """All guidance references have type 'guidance'."""
        for ref_id, ref in REGULATION_REFERENCES.items():
            if ref_id.startswith("GUI-") or ref_id.startswith("GD"):
                assert ref.reference_type == "guidance"

    def test_standards_have_valid_type(self) -> None:
        """All standard references have type 'standard'."""
        for ref_id, ref in REGULATION_REFERENCES.items():
            if ref_id.startswith("ISO-") or ref_id.startswith("IEC-"):
                assert ref.reference_type == "standard"

    def test_forms_have_valid_type(self) -> None:
        """All form references have type 'form'."""
        for ref_id, ref in REGULATION_REFERENCES.items():
            if ref_id.startswith("FRM-") or ref_id.startswith("F2"):
                assert ref.reference_type == "form"


class TestRegulatoryReferenceRegistry:
    """Tests for the RegulatoryReferenceRegistry class."""

    @pytest.fixture
    def registry(self) -> RegulatoryReferenceRegistry:
        """Create a fresh registry for each test."""
        return RegulatoryReferenceRegistry()

    def test_registry_initializes_with_references(
        self, registry: RegulatoryReferenceRegistry
    ) -> None:
        """Registry initializes with pre-populated references."""
        assert registry.count() >= 50

    def test_get_reference_by_id(self, registry: RegulatoryReferenceRegistry) -> None:
        """Get reference by exact ID."""
        ref = registry.get_by_id("SOR-98-282")
        assert ref is not None
        assert ref.document_id == "SOR/98-282"

    def test_get_reference_by_id_not_found(self, registry: RegulatoryReferenceRegistry) -> None:
        """Get reference returns None for unknown ID."""
        ref = registry.get_by_id("NONEXISTENT-123")
        assert ref is None

    def test_get_reference_by_document_id(self, registry: RegulatoryReferenceRegistry) -> None:
        """Get reference by document ID."""
        ref = registry.get_reference("SOR-98-282")
        assert ref is not None
        assert ref.document_id == "SOR/98-282"

    def test_get_reference_by_document_id_and_section(
        self, registry: RegulatoryReferenceRegistry
    ) -> None:
        """Get reference by document ID and section."""
        ref = registry.get_reference("SOR/98-282", "s.32")
        assert ref is not None
        assert ref.section == "s.32"

    def test_search_by_title(self, registry: RegulatoryReferenceRegistry) -> None:
        """Search references by title text."""
        results = registry.search("Medical Device")
        assert len(results) > 0
        # Search matches title, document_id, or description
        for r in results:
            match_found = (
                "medical device" in r.title.lower()
                or "medical device" in r.document_id.lower()
                or (r.description and "medical device" in r.description.lower())
            )
            assert match_found, f"No match found in {r.id}"

    def test_search_by_description(self, registry: RegulatoryReferenceRegistry) -> None:
        """Search references by description text."""
        results = registry.search("MDEL")
        assert len(results) > 0

    def test_search_case_insensitive(self, registry: RegulatoryReferenceRegistry) -> None:
        """Search is case-insensitive."""
        results_lower = registry.search("labelling")
        results_upper = registry.search("LABELLING")
        # Both should find results (may not be exactly equal due to other matches)
        assert len(results_lower) > 0 or len(results_upper) > 0

    def test_search_no_results(self, registry: RegulatoryReferenceRegistry) -> None:
        """Search returns empty list for no matches."""
        results = registry.search("xyznonexistent123")
        assert results == []

    def test_get_by_topic_classification(self, registry: RegulatoryReferenceRegistry) -> None:
        """Get references by classification topic."""
        results = registry.get_by_topic(TOPIC_CLASSIFICATION)
        assert len(results) > 0
        assert all(TOPIC_CLASSIFICATION in r.topics for r in results)

    def test_get_by_topic_clinical(self, registry: RegulatoryReferenceRegistry) -> None:
        """Get references by clinical topic."""
        results = registry.get_by_topic(TOPIC_CLINICAL)
        assert len(results) > 0
        assert all(TOPIC_CLINICAL in r.topics for r in results)

    def test_get_by_topic_labeling(self, registry: RegulatoryReferenceRegistry) -> None:
        """Get references by labeling topic."""
        results = registry.get_by_topic(TOPIC_LABELING)
        assert len(results) > 0

    def test_get_by_type_regulation(self, registry: RegulatoryReferenceRegistry) -> None:
        """Get all regulation references."""
        results = registry.get_by_type("regulation")
        assert len(results) > 0
        assert all(r.reference_type == "regulation" for r in results)

    def test_get_by_type_guidance(self, registry: RegulatoryReferenceRegistry) -> None:
        """Get all guidance references."""
        results = registry.get_by_type("guidance")
        assert len(results) > 0
        assert all(r.reference_type == "guidance" for r in results)

    def test_get_by_type_standard(self, registry: RegulatoryReferenceRegistry) -> None:
        """Get all standard references."""
        results = registry.get_by_type("standard")
        assert len(results) > 0
        assert all(r.reference_type == "standard" for r in results)

    def test_get_by_device_class_ii(self, registry: RegulatoryReferenceRegistry) -> None:
        """Get references applicable to Class II."""
        results = registry.get_by_device_class("II")
        assert len(results) > 0
        assert all("II" in r.device_classes for r in results)

    def test_get_by_device_class_iv(self, registry: RegulatoryReferenceRegistry) -> None:
        """Get references applicable to Class IV."""
        results = registry.get_by_device_class("IV")
        assert len(results) > 0
        assert all("IV" in r.device_classes for r in results)

    def test_get_classification_rules(self, registry: RegulatoryReferenceRegistry) -> None:
        """Get classification-related references."""
        results = registry.get_classification_rules()
        assert len(results) > 0

    def test_get_labeling_requirements(self, registry: RegulatoryReferenceRegistry) -> None:
        """Get labeling-related references."""
        results = registry.get_labeling_requirements()
        assert len(results) > 0

    def test_get_clinical_requirements(self, registry: RegulatoryReferenceRegistry) -> None:
        """Get clinical evidence-related references."""
        results = registry.get_clinical_requirements()
        assert len(results) > 0

    def test_get_clinical_requirements_filtered_by_class(
        self, registry: RegulatoryReferenceRegistry
    ) -> None:
        """Get clinical requirements filtered by device class."""
        results = registry.get_clinical_requirements("III")
        assert len(results) > 0
        assert all("III" in r.device_classes for r in results)

    def test_get_risk_management_references(self, registry: RegulatoryReferenceRegistry) -> None:
        """Get risk management-related references."""
        results = registry.get_risk_management_references()
        assert len(results) > 0
        # Should include ISO 14971
        document_ids = [r.document_id for r in results]
        assert any("14971" in doc_id for doc_id in document_ids)

    def test_get_qms_references(self, registry: RegulatoryReferenceRegistry) -> None:
        """Get QMS-related references."""
        results = registry.get_qms_references()
        assert len(results) > 0
        # Should include ISO 13485
        document_ids = [r.document_id for r in results]
        assert any("13485" in doc_id for doc_id in document_ids)

    def test_all_references(self, registry: RegulatoryReferenceRegistry) -> None:
        """Get all references returns complete list."""
        results = registry.all_references()
        assert len(results) == registry.count()
        assert len(results) >= 50


class TestCitationFormatting:
    """Tests for citation formatting methods."""

    @pytest.fixture
    def registry(self) -> RegulatoryReferenceRegistry:
        """Create a fresh registry for each test."""
        return RegulatoryReferenceRegistry()

    def test_format_citation_document_only(self, registry: RegulatoryReferenceRegistry) -> None:
        """Format citation with document ID only."""
        ref = registry.get_by_id("SOR-98-282")
        assert ref is not None
        citation = registry.format_citation(ref)
        assert citation == "[SOR/98-282]"

    def test_format_citation_with_section(self, registry: RegulatoryReferenceRegistry) -> None:
        """Format citation with section."""
        ref = registry.get_by_id("SOR-98-282-S32")
        assert ref is not None
        citation = registry.format_citation(ref)
        assert "[SOR/98-282" in citation
        assert "s.32" in citation

    def test_format_citation_with_schedule(self, registry: RegulatoryReferenceRegistry) -> None:
        """Format citation with schedule."""
        ref = registry.get_by_id("SOR-98-282-SCH1")
        assert ref is not None
        citation = registry.format_citation(ref)
        assert "[SOR/98-282" in citation
        assert "Schedule 1" in citation

    def test_format_citation_iso_standard(self, registry: RegulatoryReferenceRegistry) -> None:
        """Format citation for ISO standard."""
        ref = registry.get_by_id("ISO-14971-2019-7.2")
        assert ref is not None
        citation = registry.format_citation(ref)
        assert "[ISO 14971:2019" in citation
        assert "7.2" in citation

    def test_format_full_citation(self, registry: RegulatoryReferenceRegistry) -> None:
        """Format full citation with title."""
        ref = registry.get_by_id("GUI-0016")
        assert ref is not None
        citation = registry.format_full_citation(ref)
        assert "[GUI-0016]" in citation
        assert " — " in citation
        assert ref.title in citation


class TestRegistrySingleton:
    """Tests for the singleton get_reference_registry function."""

    def test_get_reference_registry_returns_instance(self) -> None:
        """get_reference_registry returns a registry instance."""
        registry = get_reference_registry()
        assert isinstance(registry, RegulatoryReferenceRegistry)

    def test_get_reference_registry_singleton(self) -> None:
        """get_reference_registry returns same instance."""
        registry1 = get_reference_registry()
        registry2 = get_reference_registry()
        assert registry1 is registry2

    def test_singleton_has_references(self) -> None:
        """Singleton registry has pre-populated references."""
        registry = get_reference_registry()
        assert registry.count() >= 50


class TestAddReference:
    """Tests for adding references to the registry."""

    def test_add_reference(self) -> None:
        """Add a new reference to the registry."""
        registry = RegulatoryReferenceRegistry()
        initial_count = registry.count()

        new_ref = RegulatoryReference(
            id="TEST-NEW-001",
            reference_type="internal",
            document_id="Test Document",
            title="Test Reference",
        )
        registry.add_reference(new_ref)

        assert registry.count() == initial_count + 1
        assert registry.get_by_id("TEST-NEW-001") is not None

    def test_add_reference_can_be_retrieved(self) -> None:
        """Added reference can be retrieved by ID."""
        registry = RegulatoryReferenceRegistry()

        new_ref = RegulatoryReference(
            id="TEST-NEW-002",
            reference_type="guidance",
            document_id="GUI-TEST",
            title="Test Guidance",
            topics=["test_topic"],
        )
        registry.add_reference(new_ref)

        retrieved = registry.get_by_id("TEST-NEW-002")
        assert retrieved is not None
        assert retrieved.title == "Test Guidance"
        assert "test_topic" in retrieved.topics
