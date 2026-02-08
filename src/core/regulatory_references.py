"""
Regulatory Reference Registry — Sprint 5A.

Provides structured citations to Health Canada regulatory sources.
All references are verified from KNOWLEDGE_BASE.md — NO fabricated citations.

Citation-first principle: Every substantive output must cite its source.

Usage:
    registry = get_reference_registry()
    ref = registry.get_reference("SOR-98-282", "s.32(2)(c)")
    citation = registry.format_citation(ref)
    # Returns: "[SOR/98-282, s.32(2)(c)]"
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from src.utils.logging import get_logger

# =============================================================================
# Types
# =============================================================================

ReferenceType = Literal["regulation", "guidance", "standard", "form", "internal"]

# Topics for search
TOPIC_CLASSIFICATION = "classification"
TOPIC_LABELING = "labeling"
TOPIC_CLINICAL = "clinical"
TOPIC_QMS = "qms"
TOPIC_RISK = "risk"
TOPIC_MDEL = "mdel"
TOPIC_MDL = "mdl"
TOPIC_SAMD = "samd"
TOPIC_CYBERSECURITY = "cybersecurity"
TOPIC_POST_MARKET = "post_market"

# =============================================================================
# Models
# =============================================================================


class RegulatoryReference(BaseModel):
    """A structured citation to a regulatory source.

    All fields are from verified Health Canada documents.
    Never fabricate document IDs or section numbers.
    """

    id: str = Field(..., description="Unique identifier (e.g., 'SOR-98-282-S32')")
    reference_type: ReferenceType = Field(..., description="Type of regulatory source")
    document_id: str = Field(..., description="Official document ID (e.g., 'SOR/98-282')")
    section: str | None = Field(default=None, description="Section reference (e.g., 's.32(2)(c)')")
    schedule: str | None = Field(
        default=None, description="Schedule reference (e.g., 'Schedule 1')"
    )
    rule: str | None = Field(default=None, description="Rule number (e.g., 'Rule 11')")
    title: str = Field(..., description="Human-readable title")
    description: str | None = Field(default=None, description="Brief description of content")
    url: str | None = Field(default=None, description="Health Canada URL if available")
    effective_date: date | None = Field(default=None, description="When this became effective")
    topics: list[str] = Field(default_factory=list, description="Topic tags for search")
    device_classes: list[str] = Field(
        default_factory=list, description="Applicable device classes (I, II, III, IV)"
    )


# =============================================================================
# Pre-populated Reference Registry
# Verified from docs/KNOWLEDGE_BASE.md — DO NOT FABRICATE
# =============================================================================

REGULATION_REFERENCES: dict[str, RegulatoryReference] = {
    # -------------------------------------------------------------------------
    # Core Regulation: SOR/98-282 (Medical Devices Regulations)
    # -------------------------------------------------------------------------
    "SOR-98-282": RegulatoryReference(
        id="SOR-98-282",
        reference_type="regulation",
        document_id="SOR/98-282",
        title="Medical Devices Regulations",
        description="Core Canadian medical device regulations",
        url="https://laws-lois.justice.gc.ca/eng/regulations/SOR-98-282/",
        topics=[TOPIC_CLASSIFICATION, TOPIC_LABELING, TOPIC_MDL, TOPIC_MDEL],
        device_classes=["I", "II", "III", "IV"],
    ),
    # Part 1: Interpretation
    "SOR-98-282-PART1": RegulatoryReference(
        id="SOR-98-282-PART1",
        reference_type="regulation",
        document_id="SOR/98-282",
        section="Part 1",
        title="Interpretation and Application",
        description="Definitions and scope of regulations",
        topics=[TOPIC_CLASSIFICATION],
        device_classes=["I", "II", "III", "IV"],
    ),
    # Part 2: Classification
    "SOR-98-282-PART2": RegulatoryReference(
        id="SOR-98-282-PART2",
        reference_type="regulation",
        document_id="SOR/98-282",
        section="Part 2",
        title="Device Classification",
        description="Classification rules and Schedule 1",
        topics=[TOPIC_CLASSIFICATION],
        device_classes=["I", "II", "III", "IV"],
    ),
    # Part 3: MDEL
    "SOR-98-282-PART3": RegulatoryReference(
        id="SOR-98-282-PART3",
        reference_type="regulation",
        document_id="SOR/98-282",
        section="Part 3",
        title="Establishment Licensing (MDEL)",
        description="Medical Device Establishment Licence requirements",
        topics=[TOPIC_MDEL],
        device_classes=["I", "II", "III", "IV"],
    ),
    # Part 4: MDL
    "SOR-98-282-PART4": RegulatoryReference(
        id="SOR-98-282-PART4",
        reference_type="regulation",
        document_id="SOR/98-282",
        section="Part 4",
        title="Device Licensing (MDL)",
        description="Medical Device Licence application requirements",
        topics=[TOPIC_MDL],
        device_classes=["II", "III", "IV"],
    ),
    # Part 5: Labelling
    "SOR-98-282-PART5": RegulatoryReference(
        id="SOR-98-282-PART5",
        reference_type="regulation",
        document_id="SOR/98-282",
        section="Part 5",
        title="Labelling Requirements",
        description="Device labelling, IFU, and packaging requirements",
        topics=[TOPIC_LABELING],
        device_classes=["I", "II", "III", "IV"],
    ),
    # Part 6: Post-Market
    "SOR-98-282-PART6": RegulatoryReference(
        id="SOR-98-282-PART6",
        reference_type="regulation",
        document_id="SOR/98-282",
        section="Part 6",
        title="Post-Market Requirements",
        description="Mandatory problem reporting, recalls",
        topics=[TOPIC_POST_MARKET],
        device_classes=["I", "II", "III", "IV"],
    ),
    # Schedule 1: Classification Rules
    "SOR-98-282-SCH1": RegulatoryReference(
        id="SOR-98-282-SCH1",
        reference_type="regulation",
        document_id="SOR/98-282",
        schedule="Schedule 1",
        title="Classification Rules",
        description="17 rules for determining device class",
        topics=[TOPIC_CLASSIFICATION],
        device_classes=["I", "II", "III", "IV"],
    ),
    # Specific sections referenced by gap rules
    "SOR-98-282-S10": RegulatoryReference(
        id="SOR-98-282-S10",
        reference_type="regulation",
        document_id="SOR/98-282",
        section="s.10",
        title="Safety and Effectiveness",
        description="General safety and effectiveness requirements",
        topics=[TOPIC_RISK],
        device_classes=["I", "II", "III", "IV"],
    ),
    "SOR-98-282-S21": RegulatoryReference(
        id="SOR-98-282-S21",
        reference_type="regulation",
        document_id="SOR/98-282",
        section="s.21",
        title="Device Label Requirements",
        description="Information required on device labels",
        topics=[TOPIC_LABELING],
        device_classes=["I", "II", "III", "IV"],
    ),
    "SOR-98-282-S22": RegulatoryReference(
        id="SOR-98-282-S22",
        reference_type="regulation",
        document_id="SOR/98-282",
        section="s.22",
        title="Instructions for Use Requirements",
        description="IFU content requirements",
        topics=[TOPIC_LABELING],
        device_classes=["I", "II", "III", "IV"],
    ),
    "SOR-98-282-S23": RegulatoryReference(
        id="SOR-98-282-S23",
        reference_type="regulation",
        document_id="SOR/98-282",
        section="s.23",
        title="Packaging Label Requirements",
        description="Information required on packaging",
        topics=[TOPIC_LABELING],
        device_classes=["I", "II", "III", "IV"],
    ),
    "SOR-98-282-S26": RegulatoryReference(
        id="SOR-98-282-S26",
        reference_type="regulation",
        document_id="SOR/98-282",
        section="s.26",
        title="Submission Target Requirements",
        description="Regulatory submission requirements",
        topics=[TOPIC_MDL],
        device_classes=["II", "III", "IV"],
    ),
    "SOR-98-282-S32": RegulatoryReference(
        id="SOR-98-282-S32",
        reference_type="regulation",
        document_id="SOR/98-282",
        section="s.32",
        title="MDL Application Content",
        description="Required content for MDL applications",
        topics=[TOPIC_MDL, TOPIC_CLINICAL],
        device_classes=["II", "III", "IV"],
    ),
    "SOR-98-282-S32-2-A": RegulatoryReference(
        id="SOR-98-282-S32-2-A",
        reference_type="regulation",
        document_id="SOR/98-282",
        section="s.32(2)(a)",
        title="Intended Use Statement Requirement",
        description="MDL must include intended use statement",
        topics=[TOPIC_MDL],
        device_classes=["II", "III", "IV"],
    ),
    "SOR-98-282-S32-2-C": RegulatoryReference(
        id="SOR-98-282-S32-2-C",
        reference_type="regulation",
        document_id="SOR/98-282",
        section="s.32(2)(c)",
        title="Clinical Evidence Requirement",
        description="Clinical data requirements for Class III/IV",
        topics=[TOPIC_MDL, TOPIC_CLINICAL],
        device_classes=["III", "IV"],
    ),
    "SOR-98-282-S32-4": RegulatoryReference(
        id="SOR-98-282-S32-4",
        reference_type="regulation",
        document_id="SOR/98-282",
        section="s.32(4)",
        title="Evidence Requirements",
        description="Evidence to support claims and safety",
        topics=[TOPIC_MDL, TOPIC_CLINICAL],
        device_classes=["II", "III", "IV"],
    ),
    "SOR-98-282-S43.2": RegulatoryReference(
        id="SOR-98-282-S43.2",
        reference_type="regulation",
        document_id="SOR/98-282",
        section="s.43.2",
        title="Confidential Business Information",
        description="CBI treatment and identification requirements",
        topics=[TOPIC_MDL],
        device_classes=["II", "III", "IV"],
    ),
    # -------------------------------------------------------------------------
    # Guidance Documents (GUI- series)
    # -------------------------------------------------------------------------
    "GUI-0016": RegulatoryReference(
        id="GUI-0016",
        reference_type="guidance",
        document_id="GUI-0016",
        title="Guidance on Medical Device Establishment Licensing",
        description="Complete MDEL requirements and process",
        url="https://www.canada.ca/en/health-canada/services/drugs-health-products/medical-devices/application-information/guidance-documents/guidance-medical-device-establishment-licensing-0016.html",
        topics=[TOPIC_MDEL],
        device_classes=["I", "II", "III", "IV"],
    ),
    "GUI-0098": RegulatoryReference(
        id="GUI-0098",
        reference_type="guidance",
        document_id="GUI-0098",
        title="How to Complete a Medical Device Licence Application",
        description="Step-by-step MDL application guidance",
        topics=[TOPIC_MDL],
        device_classes=["II", "III", "IV"],
    ),
    "GUI-0102": RegulatoryReference(
        id="GUI-0102",
        reference_type="guidance",
        document_id="GUI-0102",
        title="Guidance on Clinical Evidence Requirements",
        description="Clinical data requirements by device class",
        topics=[TOPIC_CLINICAL, TOPIC_MDL],
        device_classes=["II", "III", "IV"],
    ),
    "GUI-0015": RegulatoryReference(
        id="GUI-0015",
        reference_type="guidance",
        document_id="GUI-0015",
        title="Labelling Requirements for Medical Devices",
        description="Detailed labelling guidance",
        topics=[TOPIC_LABELING],
        device_classes=["I", "II", "III", "IV"],
    ),
    # SaMD Guidance
    "GUI-SAMD-DEF": RegulatoryReference(
        id="GUI-SAMD-DEF",
        reference_type="guidance",
        document_id="SaMD Definition and Classification",
        title="Software as a Medical Device: Definition and Classification",
        description="IMDRF framework for SaMD classification",
        topics=[TOPIC_SAMD, TOPIC_CLASSIFICATION],
        device_classes=["I", "II", "III", "IV"],
    ),
    "GUI-SAMD-EXAMPLES": RegulatoryReference(
        id="GUI-SAMD-EXAMPLES",
        reference_type="guidance",
        document_id="SaMD Classification Examples",
        title="SaMD Classification Examples",
        description="Real-world SaMD classification examples",
        topics=[TOPIC_SAMD, TOPIC_CLASSIFICATION],
        device_classes=["I", "II", "III", "IV"],
    ),
    # QMS Guidance Documents (GD series)
    "GD210": RegulatoryReference(
        id="GD210",
        reference_type="guidance",
        document_id="GD210",
        title="ISO 13485 QMS Audits",
        description="QMS audit requirements for medical devices",
        topics=[TOPIC_QMS],
        device_classes=["I", "II", "III", "IV"],
    ),
    "GD211": RegulatoryReference(
        id="GD211",
        reference_type="guidance",
        document_id="GD211",
        title="Content of QMS Audit Reports",
        description="Required content for QMS audit reports",
        topics=[TOPIC_QMS],
        device_classes=["I", "II", "III", "IV"],
    ),
    "GD207": RegulatoryReference(
        id="GD207",
        reference_type="guidance",
        document_id="GD207",
        title="Content of ISO 13485 Certificates",
        description="Requirements for QMS certificates",
        topics=[TOPIC_QMS],
        device_classes=["I", "II", "III", "IV"],
    ),
    # ML/AI Guidance
    "GUI-ML": RegulatoryReference(
        id="GUI-ML",
        reference_type="guidance",
        document_id="ML Pre-market Guidance",
        title="Pre-market Guidance for Machine Learning-Enabled Medical Devices",
        description="PCCP, validation requirements for ML devices",
        topics=[TOPIC_SAMD, TOPIC_CLINICAL],
        device_classes=["II", "III", "IV"],
    ),
    # Cybersecurity Guidance
    "GUI-CYBER": RegulatoryReference(
        id="GUI-CYBER",
        reference_type="guidance",
        document_id="Cybersecurity Pre-market Requirements",
        title="Pre-market Requirements for Medical Device Cybersecurity",
        description="SBOM and cybersecurity requirements",
        topics=[TOPIC_CYBERSECURITY],
        device_classes=["II", "III", "IV"],
    ),
    # IMDRF ToC
    "GUI-IMDRF-TOC": RegulatoryReference(
        id="GUI-IMDRF-TOC",
        reference_type="guidance",
        document_id="IMDRF ToC Guide",
        title="Health Canada Adapted IMDRF Table of Contents",
        description="Submission format and structure requirements",
        topics=[TOPIC_MDL],
        device_classes=["II", "III", "IV"],
    ),
    # MDSAP
    "GUI-MDSAP": RegulatoryReference(
        id="GUI-MDSAP",
        reference_type="guidance",
        document_id="MDSAP Requirements",
        title="MDSAP Auditing Organizations Requirements",
        description="Medical Device Single Audit Program requirements",
        topics=[TOPIC_QMS],
        device_classes=["II", "III", "IV"],
    ),
    # -------------------------------------------------------------------------
    # ISO Standards
    # -------------------------------------------------------------------------
    "ISO-13485-2016": RegulatoryReference(
        id="ISO-13485-2016",
        reference_type="standard",
        document_id="ISO 13485:2016",
        title="Medical Devices — Quality Management Systems",
        description="QMS requirements for medical device organizations",
        topics=[TOPIC_QMS],
        device_classes=["I", "II", "III", "IV"],
    ),
    "ISO-13485-2016-7.3": RegulatoryReference(
        id="ISO-13485-2016-7.3",
        reference_type="standard",
        document_id="ISO 13485:2016",
        section="7.3",
        title="Design and Development",
        description="Design control requirements",
        topics=[TOPIC_QMS],
        device_classes=["I", "II", "III", "IV"],
    ),
    "ISO-13485-2016-7.3.4": RegulatoryReference(
        id="ISO-13485-2016-7.3.4",
        reference_type="standard",
        document_id="ISO 13485:2016",
        section="7.3.4",
        title="Design and Development Outputs",
        description="Requirements for design outputs to meet design inputs",
        topics=[TOPIC_QMS],
        device_classes=["I", "II", "III", "IV"],
    ),
    "ISO-13485-2016-7.3.5": RegulatoryReference(
        id="ISO-13485-2016-7.3.5",
        reference_type="standard",
        document_id="ISO 13485:2016",
        section="7.3.5",
        title="Design and Development Review",
        description="Design review requirements at suitable stages",
        topics=[TOPIC_QMS],
        device_classes=["I", "II", "III", "IV"],
    ),
    "ISO-13485-2016-7.3.6": RegulatoryReference(
        id="ISO-13485-2016-7.3.6",
        reference_type="standard",
        document_id="ISO 13485:2016",
        section="7.3.6",
        title="Design and Development Verification",
        description="Verification requirements for design outputs",
        topics=[TOPIC_QMS],
        device_classes=["I", "II", "III", "IV"],
    ),
    "ISO-14971-2019": RegulatoryReference(
        id="ISO-14971-2019",
        reference_type="standard",
        document_id="ISO 14971:2019",
        title="Medical Devices — Application of Risk Management",
        description="Risk management process for medical devices",
        topics=[TOPIC_RISK],
        device_classes=["I", "II", "III", "IV"],
    ),
    "ISO-14971-2019-6": RegulatoryReference(
        id="ISO-14971-2019-6",
        reference_type="standard",
        document_id="ISO 14971:2019",
        section="6",
        title="Risk Analysis",
        description="Risk analysis requirements",
        topics=[TOPIC_RISK],
        device_classes=["I", "II", "III", "IV"],
    ),
    "ISO-14971-2019-7": RegulatoryReference(
        id="ISO-14971-2019-7",
        reference_type="standard",
        document_id="ISO 14971:2019",
        section="7",
        title="Risk Evaluation and Control",
        description="Risk evaluation and control measures",
        topics=[TOPIC_RISK],
        device_classes=["I", "II", "III", "IV"],
    ),
    "ISO-14971-2019-7.1": RegulatoryReference(
        id="ISO-14971-2019-7.1",
        reference_type="standard",
        document_id="ISO 14971:2019",
        section="7.1",
        title="Risk Control Option Analysis",
        description="Analysis of risk control options",
        topics=[TOPIC_RISK],
        device_classes=["I", "II", "III", "IV"],
    ),
    "ISO-14971-2019-7.2": RegulatoryReference(
        id="ISO-14971-2019-7.2",
        reference_type="standard",
        document_id="ISO 14971:2019",
        section="7.2",
        title="Implementation of Risk Control Measures",
        description="Implementation and verification of controls",
        topics=[TOPIC_RISK],
        device_classes=["I", "II", "III", "IV"],
    ),
    "IEC-62304-2006": RegulatoryReference(
        id="IEC-62304-2006",
        reference_type="standard",
        document_id="IEC 62304:2006",
        title="Medical Device Software — Software Life Cycle Processes",
        description="Software development lifecycle requirements",
        topics=[TOPIC_SAMD],
        device_classes=["I", "II", "III", "IV"],
    ),
    "ISO-14155-2020": RegulatoryReference(
        id="ISO-14155-2020",
        reference_type="standard",
        document_id="ISO 14155:2020",
        title="Clinical Investigation of Medical Devices for Human Subjects",
        description="Good clinical practice for device trials",
        topics=[TOPIC_CLINICAL],
        device_classes=["II", "III", "IV"],
    ),
    # -------------------------------------------------------------------------
    # Forms
    # -------------------------------------------------------------------------
    "FRM-0292": RegulatoryReference(
        id="FRM-0292",
        reference_type="form",
        document_id="FRM-0292",
        title="Medical Device Establishment Licence Application",
        description="MDEL application form",
        topics=[TOPIC_MDEL],
        device_classes=["I", "II", "III", "IV"],
    ),
    "FRM-0077": RegulatoryReference(
        id="FRM-0077",
        reference_type="form",
        document_id="FRM-0077",
        title="MDL Application - Class II",
        description="Class II medical device licence application form",
        topics=[TOPIC_MDL],
        device_classes=["II"],
    ),
    "FRM-0078": RegulatoryReference(
        id="FRM-0078",
        reference_type="form",
        document_id="FRM-0078",
        title="MDL Application - Class III",
        description="Class III medical device licence application form",
        topics=[TOPIC_MDL],
        device_classes=["III"],
    ),
    "FRM-0079": RegulatoryReference(
        id="FRM-0079",
        reference_type="form",
        document_id="FRM-0079",
        title="MDL Application - Class IV",
        description="Class IV medical device licence application form",
        topics=[TOPIC_MDL],
        device_classes=["IV"],
    ),
    "F201": RegulatoryReference(
        id="F201",
        reference_type="form",
        document_id="F201",
        title="Manufacturer Registration Status Change",
        description="Form for manufacturer registration updates",
        topics=[TOPIC_MDEL],
        device_classes=["I", "II", "III", "IV"],
    ),
    "F202": RegulatoryReference(
        id="F202",
        reference_type="form",
        document_id="F202",
        title="QMS Certificate Filing",
        description="Form for submitting QMS certificates",
        topics=[TOPIC_QMS],
        device_classes=["II", "III", "IV"],
    ),
    # -------------------------------------------------------------------------
    # Internal Platform References
    # -------------------------------------------------------------------------
    "PLATFORM-PROVENANCE": RegulatoryReference(
        id="PLATFORM-PROVENANCE",
        reference_type="internal",
        document_id="Platform Policy",
        title="AI Provenance Requirements",
        description="All AI outputs require human attestation before use",
        topics=[],
        device_classes=["I", "II", "III", "IV"],
    ),
    "PLATFORM-LANGUAGE": RegulatoryReference(
        id="PLATFORM-LANGUAGE",
        reference_type="internal",
        document_id="Platform Policy",
        title="Regulatory-Safe Language",
        description="Forbidden words and approved replacements for outputs",
        topics=[],
        device_classes=["I", "II", "III", "IV"],
    ),
    # Additional Schedule 1 Rules
    "SOR-98-282-SCH1-R11": RegulatoryReference(
        id="SOR-98-282-SCH1-R11",
        reference_type="regulation",
        document_id="SOR/98-282",
        schedule="Schedule 1",
        rule="Rule 11",
        title="Classification Rule 11 - Software",
        description="Classification rule for software medical devices (SaMD)",
        topics=[TOPIC_CLASSIFICATION, TOPIC_SAMD],
        device_classes=["I", "II", "III", "IV"],
    ),
    "SOR-98-282-SCH1-R12": RegulatoryReference(
        id="SOR-98-282-SCH1-R12",
        reference_type="regulation",
        document_id="SOR/98-282",
        schedule="Schedule 1",
        rule="Rule 12",
        title="Classification Rule 12 - IVD",
        description="Classification rule for in-vitro diagnostic devices",
        topics=[TOPIC_CLASSIFICATION],
        device_classes=["I", "II", "III", "IV"],
    ),
    # Additional ISO sections
    "ISO-13485-2016-7.3.7": RegulatoryReference(
        id="ISO-13485-2016-7.3.7",
        reference_type="standard",
        document_id="ISO 13485:2016",
        section="7.3.7",
        title="Design and Development Validation",
        description="Validation requirements for design outputs",
        topics=[TOPIC_QMS],
        device_classes=["I", "II", "III", "IV"],
    ),
}


# =============================================================================
# Registry Class
# =============================================================================


class RegulatoryReferenceRegistry:
    """
    Registry of Health Canada regulatory references.

    Pre-populated with verified references from KNOWLEDGE_BASE.md.
    Provides search and citation formatting capabilities.

    Never fabricate references — only return what's in the registry.

    Usage:
        registry = get_reference_registry()
        ref = registry.get_reference("SOR-98-282-S32")
        citation = registry.format_citation(ref)
    """

    def __init__(self) -> None:
        """Initialize the registry with pre-populated references."""
        self.logger = get_logger(self.__class__.__name__)
        self._references: dict[str, RegulatoryReference] = dict(REGULATION_REFERENCES)
        self.logger.info(f"Registry initialized with {len(self._references)} references")

    def get_reference(
        self, document_id: str, section: str | None = None
    ) -> RegulatoryReference | None:
        """Get a reference by document ID and optional section.

        Args:
            document_id: Document ID (e.g., "SOR-98-282" or "GUI-0016")
            section: Optional section (e.g., "s.32(2)(c)")

        Returns:
            RegulatoryReference if found, None otherwise.
        """
        # Try exact match first
        if section:
            # Build possible IDs
            for ref_id, ref in self._references.items():
                if ref.document_id == document_id and ref.section == section:
                    return ref
                # Also check normalized document_id
                if document_id.replace("/", "-").replace(":", "-") in ref_id:
                    if ref.section == section:
                        return ref

        # Try by ID directly
        if document_id in self._references:
            return self._references[document_id]

        # Try normalized ID
        normalized = document_id.replace("/", "-").replace(":", "-").upper()
        for ref_id, ref in self._references.items():
            if ref_id.upper() == normalized:
                return ref

        return None

    def get_by_id(self, reference_id: str) -> RegulatoryReference | None:
        """Get a reference by its exact ID.

        Args:
            reference_id: Exact reference ID (e.g., "SOR-98-282-S32-2-C")

        Returns:
            RegulatoryReference if found, None otherwise.
        """
        return self._references.get(reference_id)

    def search(self, query: str) -> list[RegulatoryReference]:
        """Search references by text in title, description, or document_id.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching references.
        """
        query_lower = query.lower()
        results: list[RegulatoryReference] = []

        for ref in self._references.values():
            if (
                query_lower in ref.title.lower()
                or query_lower in ref.document_id.lower()
                or (ref.description and query_lower in ref.description.lower())
            ):
                results.append(ref)

        return results

    def get_by_topic(self, topic: str) -> list[RegulatoryReference]:
        """Get references by topic tag.

        Args:
            topic: Topic tag (e.g., "classification", "labeling")

        Returns:
            List of references with that topic.
        """
        topic_lower = topic.lower()
        return [ref for ref in self._references.values() if topic_lower in ref.topics]

    def get_by_type(self, reference_type: ReferenceType) -> list[RegulatoryReference]:
        """Get references by type.

        Args:
            reference_type: Type of reference ("regulation", "guidance", etc.)

        Returns:
            List of references of that type.
        """
        return [ref for ref in self._references.values() if ref.reference_type == reference_type]

    def get_by_device_class(self, device_class: str) -> list[RegulatoryReference]:
        """Get references applicable to a device class.

        Args:
            device_class: Device class ("I", "II", "III", or "IV")

        Returns:
            List of applicable references.
        """
        return [ref for ref in self._references.values() if device_class in ref.device_classes]

    def get_classification_rules(self) -> list[RegulatoryReference]:
        """Get references related to device classification.

        Returns:
            List of classification-related references.
        """
        return self.get_by_topic(TOPIC_CLASSIFICATION)

    def get_labeling_requirements(self) -> list[RegulatoryReference]:
        """Get references related to labeling.

        Returns:
            List of labeling-related references.
        """
        return self.get_by_topic(TOPIC_LABELING)

    def get_clinical_requirements(
        self, device_class: str | None = None
    ) -> list[RegulatoryReference]:
        """Get references related to clinical evidence.

        Args:
            device_class: Optional device class filter

        Returns:
            List of clinical evidence-related references.
        """
        refs = self.get_by_topic(TOPIC_CLINICAL)
        if device_class:
            refs = [ref for ref in refs if device_class in ref.device_classes]
        return refs

    def get_risk_management_references(self) -> list[RegulatoryReference]:
        """Get references related to risk management.

        Returns:
            List of risk management-related references.
        """
        return self.get_by_topic(TOPIC_RISK)

    def get_qms_references(self) -> list[RegulatoryReference]:
        """Get references related to QMS.

        Returns:
            List of QMS-related references.
        """
        return self.get_by_topic(TOPIC_QMS)

    def format_citation(self, ref: RegulatoryReference) -> str:
        """Format a reference as a citation string.

        Args:
            ref: RegulatoryReference to format

        Returns:
            Formatted citation string (e.g., "[SOR/98-282, s.32(2)(c)]")
        """
        parts = [ref.document_id]

        if ref.section:
            parts.append(ref.section)
        if ref.schedule:
            parts.append(ref.schedule)
        if ref.rule:
            parts.append(ref.rule)

        return f"[{', '.join(parts)}]"

    def format_full_citation(self, ref: RegulatoryReference) -> str:
        """Format a reference as a full citation with title.

        Args:
            ref: RegulatoryReference to format

        Returns:
            Full citation string (e.g., "[SOR/98-282, s.32(2)(c)] — Intended Use Statement Requirement")
        """
        base = self.format_citation(ref)
        return f"{base} — {ref.title}"

    def all_references(self) -> list[RegulatoryReference]:
        """Get all references in the registry.

        Returns:
            List of all RegulatoryReference objects.
        """
        return list(self._references.values())

    def count(self) -> int:
        """Get the total number of references in the registry.

        Returns:
            Number of references.
        """
        return len(self._references)

    def add_reference(self, ref: RegulatoryReference) -> None:
        """Add a reference to the registry.

        Args:
            ref: RegulatoryReference to add

        Note:
            Only use for verified references. Never fabricate.
        """
        self._references[ref.id] = ref
        self.logger.info(f"Added reference: {ref.id}")


# =============================================================================
# Singleton Access
# =============================================================================

_registry: RegulatoryReferenceRegistry | None = None


def get_reference_registry() -> RegulatoryReferenceRegistry:
    """Get or create the singleton RegulatoryReferenceRegistry instance.

    Returns:
        RegulatoryReferenceRegistry singleton.
    """
    global _registry
    if _registry is None:
        _registry = RegulatoryReferenceRegistry()
    return _registry
