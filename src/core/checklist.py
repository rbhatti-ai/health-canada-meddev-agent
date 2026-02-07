"""
Regulatory checklist management.

Provides dynamic checklist generation and tracking based on device
classification and regulatory requirements.
"""

import json
from datetime import date
from typing import Any, TypedDict

from src.core.models import (
    Checklist,
    ChecklistItem,
    ClassificationResult,
    ComplianceStatus,
    DeviceClass,
    DeviceInfo,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)


class ChecklistItemData(TypedDict, total=False):
    """Type definition for master checklist item data."""

    id: str
    category: str
    title: str
    description: str
    required: bool
    device_classes: list[DeviceClass]
    guidance_reference: str | None
    form_number: str | None


# Master checklist template with all possible items
MASTER_CHECKLIST_ITEMS: list[ChecklistItemData] = [
    # MDEL Requirements
    {
        "id": "mdel_application",
        "category": "MDEL",
        "title": "MDEL Application (FRM-0292)",
        "description": "Complete and submit Medical Device Establishment Licence application form FRM-0292. Required for any company importing, distributing, or selling medical devices in Canada.",
        "required": True,
        "device_classes": [
            DeviceClass.CLASS_I,
            DeviceClass.CLASS_II,
            DeviceClass.CLASS_III,
            DeviceClass.CLASS_IV,
        ],
        "guidance_reference": "GUI-0016: Guidance on Medical Device Establishment Licensing",
        "form_number": "FRM-0292",
    },
    {
        "id": "mdel_site_licence",
        "category": "MDEL",
        "title": "Site Information Documentation",
        "description": "Prepare site master file with facility information, quality procedures, and organizational structure.",
        "required": True,
        "device_classes": [DeviceClass.CLASS_II, DeviceClass.CLASS_III, DeviceClass.CLASS_IV],
        "guidance_reference": "GUI-0016",
    },
    # QMS Requirements
    {
        "id": "qms_iso13485",
        "category": "QMS",
        "title": "ISO 13485 QMS Certification",
        "description": "Obtain ISO 13485:2016 Quality Management System certification from a Health Canada recognized registrar. Certificate must cover the device types being licensed.",
        "required": True,
        "device_classes": [DeviceClass.CLASS_II, DeviceClass.CLASS_III, DeviceClass.CLASS_IV],
        "guidance_reference": "GD210: ISO 13485 Quality Management System Audits",
    },
    {
        "id": "qms_audit_report",
        "category": "QMS",
        "title": "QMS Audit Report (GD211 Format)",
        "description": "QMS audit report conforming to GD211 format requirements, issued by recognized registrar.",
        "required": True,
        "device_classes": [DeviceClass.CLASS_II, DeviceClass.CLASS_III, DeviceClass.CLASS_IV],
        "guidance_reference": "GD211: Guidance on Content of QMS Audit Reports",
    },
    {
        "id": "qms_mdsap",
        "category": "QMS",
        "title": "MDSAP Audit (Recommended)",
        "description": "Medical Device Single Audit Program (MDSAP) audit covering Canada. While not mandatory, MDSAP satisfies QMS requirements for multiple jurisdictions.",
        "required": False,
        "device_classes": [DeviceClass.CLASS_II, DeviceClass.CLASS_III, DeviceClass.CLASS_IV],
        "guidance_reference": "MDSAP Recognition Process Guidance",
    },
    # MDL Application
    {
        "id": "mdl_application_form",
        "category": "MDL",
        "title": "MDL Application Form",
        "description": "Complete the appropriate MDL application form: FRM-0077 (Class II), FRM-0078 (Class III), or FRM-0079 (Class IV).",
        "required": True,
        "device_classes": [DeviceClass.CLASS_II, DeviceClass.CLASS_III, DeviceClass.CLASS_IV],
        "guidance_reference": "Guidance on How to Complete MDL Application",
        "form_number": "FRM-0077/0078/0079",
    },
    {
        "id": "mdl_device_description",
        "category": "MDL",
        "title": "Device Description",
        "description": "Comprehensive device description including technical specifications, materials, components, and principles of operation.",
        "required": True,
        "device_classes": [DeviceClass.CLASS_II, DeviceClass.CLASS_III, DeviceClass.CLASS_IV],
    },
    {
        "id": "mdl_intended_use",
        "category": "MDL",
        "title": "Intended Use Statement",
        "description": "Clear statement of intended use, indications for use, target patient population, and contraindications.",
        "required": True,
        "device_classes": [DeviceClass.CLASS_II, DeviceClass.CLASS_III, DeviceClass.CLASS_IV],
    },
    # Clinical Evidence
    {
        "id": "clinical_evaluation",
        "category": "Clinical",
        "title": "Clinical Evaluation Report",
        "description": "Comprehensive clinical evaluation demonstrating safety and effectiveness through clinical data, literature, and/or predicate comparison.",
        "required": True,
        "device_classes": [DeviceClass.CLASS_III, DeviceClass.CLASS_IV],
        "guidance_reference": "Guidance on Clinical Evidence Requirements",
    },
    {
        "id": "clinical_study",
        "category": "Clinical",
        "title": "Clinical Validation Study",
        "description": "Clinical investigation data with appropriate patient population (typically 100-500+ patients for Class III/IV).",
        "required": True,
        "device_classes": [DeviceClass.CLASS_III, DeviceClass.CLASS_IV],
        "guidance_reference": "Guidance on Clinical Evidence Requirements",
    },
    # SaMD Specific
    {
        "id": "samd_classification",
        "category": "SaMD",
        "title": "SaMD Classification Justification",
        "description": "Documentation of SaMD classification using IMDRF framework including healthcare situation and significance of information provided.",
        "required": True,
        "device_classes": [DeviceClass.CLASS_II, DeviceClass.CLASS_III, DeviceClass.CLASS_IV],
        "guidance_reference": "Health Canada SaMD Definition and Classification Guidance",
    },
    {
        "id": "samd_software_documentation",
        "category": "SaMD",
        "title": "Software Documentation (IEC 62304)",
        "description": "Software lifecycle documentation per IEC 62304 including requirements, architecture, design, testing, and maintenance.",
        "required": True,
        "device_classes": [DeviceClass.CLASS_II, DeviceClass.CLASS_III, DeviceClass.CLASS_IV],
        "guidance_reference": "IEC 62304 Medical Device Software Lifecycle",
    },
    {
        "id": "pccp_documentation",
        "category": "SaMD",
        "title": "PCCP Documentation (for ML devices)",
        "description": "Predetermined Change Control Plan for machine learning/AI devices describing planned modifications and validation approach.",
        "required": False,  # Only for ML devices
        "device_classes": [DeviceClass.CLASS_II, DeviceClass.CLASS_III, DeviceClass.CLASS_IV],
        "guidance_reference": "Pre-market Guidance for ML-enabled Medical Devices",
    },
    # Cybersecurity
    {
        "id": "cybersecurity_assessment",
        "category": "Cybersecurity",
        "title": "Cybersecurity Risk Assessment",
        "description": "Threat modeling, vulnerability assessment, and security risk management documentation.",
        "required": True,
        "device_classes": [DeviceClass.CLASS_II, DeviceClass.CLASS_III, DeviceClass.CLASS_IV],
        "guidance_reference": "Pre-market Requirements for Medical Device Cybersecurity",
    },
    {
        "id": "sbom",
        "category": "Cybersecurity",
        "title": "Software Bill of Materials (SBOM)",
        "description": "Complete inventory of software components including third-party libraries, versions, and known vulnerabilities.",
        "required": True,
        "device_classes": [DeviceClass.CLASS_II, DeviceClass.CLASS_III, DeviceClass.CLASS_IV],
        "guidance_reference": "Pre-market Requirements for Medical Device Cybersecurity",
    },
    # Safety & Risk
    {
        "id": "risk_management",
        "category": "Safety",
        "title": "Risk Management File (ISO 14971)",
        "description": "Complete risk management file per ISO 14971 including hazard analysis, risk evaluation, and mitigation measures.",
        "required": True,
        "device_classes": [DeviceClass.CLASS_II, DeviceClass.CLASS_III, DeviceClass.CLASS_IV],
    },
    {
        "id": "biocompatibility",
        "category": "Safety",
        "title": "Biocompatibility Testing (ISO 10993)",
        "description": "Biocompatibility evaluation per ISO 10993 for devices with patient contact.",
        "required": True,
        "device_classes": [DeviceClass.CLASS_III, DeviceClass.CLASS_IV],
    },
    # Labeling
    {
        "id": "labeling",
        "category": "Labeling",
        "title": "Device Labeling",
        "description": "Complete labeling including device label, packaging, and Instructions for Use (IFU) in English and French.",
        "required": True,
        "device_classes": [
            DeviceClass.CLASS_I,
            DeviceClass.CLASS_II,
            DeviceClass.CLASS_III,
            DeviceClass.CLASS_IV,
        ],
    },
    # IMDRF ToC
    {
        "id": "imdrf_toc",
        "category": "Submission",
        "title": "IMDRF Table of Contents Submission Format",
        "description": "Organize submission according to Health Canada adapted IMDRF Table of Contents format.",
        "required": True,
        "device_classes": [DeviceClass.CLASS_II, DeviceClass.CLASS_III, DeviceClass.CLASS_IV],
        "guidance_reference": "Health Canada IMDRF ToC Assembly Guide",
    },
]


class ChecklistManager:
    """
    Manages regulatory checklists for device submissions.

    Features:
    - Dynamic checklist generation based on device classification
    - Progress tracking
    - Gap analysis
    - Export capabilities
    """

    def __init__(self) -> None:
        self.logger = get_logger(self.__class__.__name__)
        self._master_items = MASTER_CHECKLIST_ITEMS

    def generate_checklist(
        self,
        classification: ClassificationResult,
        device_info: DeviceInfo,
        include_optional: bool = True,
    ) -> Checklist:
        """
        Generate a customized checklist based on device classification.

        Args:
            classification: Device classification result
            device_info: Device information
            include_optional: Whether to include optional items

        Returns:
            Customized Checklist
        """
        self.logger.info(f"Generating checklist for Class {classification.device_class.value}")

        device_class = classification.device_class
        is_samd = classification.is_samd or device_info.is_software

        items: list[ChecklistItem] = []
        for item_data in self._master_items:
            # Check if item applies to this device class
            applicable_classes = item_data.get("device_classes", [])
            if applicable_classes is None:
                applicable_classes = []
            if device_class not in applicable_classes:
                continue

            # Skip SaMD items for non-software devices
            if item_data["category"] == "SaMD" and not is_samd:
                continue

            # Skip optional items if not requested
            if not item_data.get("required", True) and not include_optional:
                continue

            # Handle PCCP - only for ML devices
            if item_data["id"] == "pccp_documentation":
                if not (is_samd and "ml" in device_info.description.lower()):
                    continue

            # Create checklist item
            item = ChecklistItem(
                id=item_data["id"],
                category=item_data["category"],
                title=item_data["title"],
                description=item_data["description"],
                status=ComplianceStatus.NOT_STARTED,
                required=item_data.get("required", True),
                device_classes=applicable_classes,
                guidance_reference=item_data.get("guidance_reference"),
                form_number=item_data.get("form_number"),
            )
            items.append(item)

        # Set up dependencies
        items = self._set_dependencies(items)

        checklist = Checklist(
            name=f"Class {device_class.value} Regulatory Checklist",
            device_class=device_class,
            items=items,
        )

        self.logger.info(f"Generated checklist with {len(items)} items")
        return checklist

    def _set_dependencies(self, items: list[ChecklistItem]) -> list[ChecklistItem]:
        """Set up item dependencies based on logical ordering."""
        dependency_map = {
            "mdl_application_form": ["mdel_application", "qms_iso13485"],
            "mdl_device_description": ["mdel_application"],
            "clinical_study": ["qms_iso13485"],
            "clinical_evaluation": ["clinical_study"],
            "imdrf_toc": ["mdl_device_description", "clinical_evaluation", "risk_management"],
        }

        item_ids = {item.id for item in items}

        for item in items:
            if item.id in dependency_map:
                # Only add dependencies that exist in the checklist
                valid_deps = [dep for dep in dependency_map[item.id] if dep in item_ids]
                item.dependencies = valid_deps

        return items

    def update_item_status(
        self,
        checklist: Checklist,
        item_id: str,
        status: ComplianceStatus,
        notes: str | None = None,
    ) -> Checklist:
        """
        Update the status of a checklist item.

        Args:
            checklist: Current checklist
            item_id: ID of item to update
            status: New status
            notes: Optional notes

        Returns:
            Updated checklist
        """
        for item in checklist.items:
            if item.id == item_id:
                item.status = status
                if notes:
                    item.notes = notes
                break

        checklist.last_updated = date.today()
        return checklist

    def get_next_actions(self, checklist: Checklist) -> list[ChecklistItem]:
        """
        Get items that are ready to be worked on.

        Returns items where:
        - Status is NOT_STARTED or IN_PROGRESS
        - All dependencies are COMPLETED

        Args:
            checklist: Current checklist

        Returns:
            List of actionable items
        """
        completed_ids = {
            item.id for item in checklist.items if item.status == ComplianceStatus.COMPLETED
        }

        actionable = []
        for item in checklist.items:
            if item.status in [ComplianceStatus.NOT_STARTED, ComplianceStatus.IN_PROGRESS]:
                # Check if all dependencies are complete
                deps_complete = all(dep in completed_ids for dep in item.dependencies)
                if deps_complete:
                    actionable.append(item)

        return actionable

    def get_gap_analysis(self, checklist: Checklist) -> dict[str, Any]:
        """
        Analyze gaps in checklist completion.

        Args:
            checklist: Current checklist

        Returns:
            Gap analysis report
        """
        total = len(checklist.items)
        completed = sum(1 for item in checklist.items if item.status == ComplianceStatus.COMPLETED)
        in_progress = sum(
            1 for item in checklist.items if item.status == ComplianceStatus.IN_PROGRESS
        )
        not_started = sum(
            1 for item in checklist.items if item.status == ComplianceStatus.NOT_STARTED
        )
        blocked = sum(1 for item in checklist.items if item.status == ComplianceStatus.BLOCKED)

        # Group by category
        by_category: dict[str, dict[str, Any]] = {}
        for item in checklist.items:
            if item.category not in by_category:
                by_category[item.category] = {"total": 0, "completed": 0, "items": []}
            by_category[item.category]["total"] += 1
            if item.status == ComplianceStatus.COMPLETED:
                by_category[item.category]["completed"] += 1
            if item.status != ComplianceStatus.COMPLETED:
                by_category[item.category]["items"].append(item.title)

        return {
            "summary": {
                "total_items": total,
                "completed": completed,
                "in_progress": in_progress,
                "not_started": not_started,
                "blocked": blocked,
                "completion_percentage": checklist.completion_percentage,
            },
            "by_category": by_category,
            "next_actions": [item.title for item in self.get_next_actions(checklist)],
            "blockers": [
                item.title for item in checklist.items if item.status == ComplianceStatus.BLOCKED
            ],
        }

    def export_checklist(
        self,
        checklist: Checklist,
        format: str = "json",
    ) -> str:
        """
        Export checklist to various formats.

        Args:
            checklist: Checklist to export
            format: Export format ("json", "markdown")

        Returns:
            Formatted checklist string
        """
        if format == "json":
            return self._export_json(checklist)
        elif format == "markdown":
            return self._export_markdown(checklist)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _export_json(self, checklist: Checklist) -> str:
        """Export checklist as JSON."""
        data = {
            "name": checklist.name,
            "device_class": checklist.device_class.value,
            "created_date": str(checklist.created_date),
            "last_updated": str(checklist.last_updated),
            "completion_percentage": checklist.completion_percentage,
            "items": [
                {
                    "id": item.id,
                    "category": item.category,
                    "title": item.title,
                    "description": item.description,
                    "status": item.status.value,
                    "required": item.required,
                    "guidance_reference": item.guidance_reference,
                    "form_number": item.form_number,
                    "notes": item.notes,
                }
                for item in checklist.items
            ],
        }
        return json.dumps(data, indent=2)

    def _export_markdown(self, checklist: Checklist) -> str:
        """Export checklist as Markdown."""
        lines = [
            f"# {checklist.name}",
            "",
            f"**Device Class:** {checklist.device_class.value}",
            f"**Created:** {checklist.created_date}",
            f"**Last Updated:** {checklist.last_updated}",
            f"**Progress:** {checklist.completion_percentage:.1f}%",
            "",
        ]

        # Group by category
        categories: dict[str, list[ChecklistItem]] = {}
        for item in checklist.items:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)

        for category, items in categories.items():
            lines.append(f"## {category}")
            lines.append("")
            for item in items:
                status_icon = {
                    ComplianceStatus.NOT_STARTED: "[ ]",
                    ComplianceStatus.IN_PROGRESS: "[~]",
                    ComplianceStatus.COMPLETED: "[x]",
                    ComplianceStatus.NOT_APPLICABLE: "[-]",
                    ComplianceStatus.BLOCKED: "[!]",
                }.get(item.status, "[ ]")

                required_marker = "*" if item.required else ""
                lines.append(f"- {status_icon} **{item.title}**{required_marker}")
                lines.append(f"  - {item.description}")
                if item.guidance_reference:
                    lines.append(f"  - Reference: {item.guidance_reference}")
                if item.notes:
                    lines.append(f"  - Notes: {item.notes}")
            lines.append("")

        return "\n".join(lines)


# Singleton instance
checklist_manager = ChecklistManager()


def generate_checklist(
    classification: ClassificationResult,
    device_info: DeviceInfo,
    include_optional: bool = True,
) -> Checklist:
    """Convenience function for checklist generation."""
    return checklist_manager.generate_checklist(classification, device_info, include_optional)
