"""
Agent tools for the regulatory assistant.

Provides structured tools that the LLM agent can use to:
- Classify devices
- Generate pathways
- Create checklists
- Search regulatory documents
"""

from typing import Any

from langchain_core.tools import tool

from src.core.checklist import generate_checklist as _generate_checklist
from src.core.classification import classify_device as _classify_device
from src.core.confidentiality import get_confidentiality_service
from src.core.models import (
    DeviceClass,
    DeviceInfo,
    HealthcareSituation,
    SaMDCategory,
    SaMDInfo,
)
from src.core.pathway import get_pathway as _get_pathway
from src.retrieval.retriever import retrieve
from src.utils.logging import get_logger

logger = get_logger(__name__)


@tool
def classify_device(
    name: str,
    description: str,
    intended_use: str,
    manufacturer_name: str,
    is_software: bool = False,
    is_ivd: bool = False,
    is_implantable: bool = False,
    is_active: bool = False,
    healthcare_situation: str | None = None,
    significance: str | None = None,
    uses_ml: bool = False,
) -> dict[str, Any]:
    """
    Classify a medical device according to Health Canada regulations.

    Use this tool when a user asks about device classification or wants to
    determine the regulatory class of their device.

    Args:
        name: Device name
        description: Device description
        intended_use: Intended use statement
        manufacturer_name: Manufacturer name
        is_software: True if this is a software device (SaMD)
        is_ivd: True if this is an in-vitro diagnostic device
        is_implantable: True if this is an implantable device
        is_active: True if this is a powered/active device
        healthcare_situation: For SaMD - "critical", "serious", or "non_serious"
        significance: For SaMD - "treat", "diagnose", "drive", or "inform"
        uses_ml: For SaMD - True if device uses machine learning

    Returns:
        Classification result including device class and rationale
    """
    logger.info(f"Classifying device: {name}")

    device_info = DeviceInfo(
        name=name,
        description=description,
        intended_use=intended_use,
        manufacturer_name=manufacturer_name,
        is_software=is_software,
        is_ivd=is_ivd,
        is_implantable=is_implantable,
        is_active=is_active,
    )

    samd_info = None
    if is_software and healthcare_situation and significance:
        situation_map = {
            "critical": HealthcareSituation.CRITICAL,
            "serious": HealthcareSituation.SERIOUS,
            "non_serious": HealthcareSituation.NON_SERIOUS,
        }
        significance_map = {
            "treat": SaMDCategory.TREAT,
            "diagnose": SaMDCategory.DIAGNOSE,
            "drive": SaMDCategory.DRIVE,
            "inform": SaMDCategory.INFORM,
        }
        samd_info = SaMDInfo(
            healthcare_situation=situation_map.get(
                healthcare_situation, HealthcareSituation.SERIOUS
            ),
            significance=significance_map.get(significance, SaMDCategory.DIAGNOSE),
            uses_ml=uses_ml,
        )

    result = _classify_device(device_info, samd_info)

    return {
        "device_class": result.device_class.value,
        "risk_level": result.device_class.risk_level,
        "requires_mdl": result.device_class.requires_mdl,
        "review_days": result.device_class.review_days,
        "rationale": result.rationale,
        "classification_rules": result.classification_rules,
        "is_samd": result.is_samd,
        "warnings": result.warnings,
        "references": result.references,
        "confidence": result.confidence,
    }


@tool
def get_regulatory_pathway(
    device_class: str,
    is_software: bool = False,
    has_mdel: bool = False,
    has_qms_certificate: bool = False,
) -> dict[str, Any]:
    """
    Get the complete regulatory pathway for a device class.

    Use this tool when a user asks about the regulatory pathway, timeline,
    or steps needed to get their device licensed in Canada.

    Args:
        device_class: Device class ("I", "II", "III", or "IV")
        is_software: Whether this is a software device
        has_mdel: Whether the company already has an MDEL
        has_qms_certificate: Whether the company has ISO 13485 certification

    Returns:
        Complete pathway with steps, timeline, and fees
    """
    logger.info(f"Getting pathway for Class {device_class}")

    class_map = {
        "I": DeviceClass.CLASS_I,
        "II": DeviceClass.CLASS_II,
        "III": DeviceClass.CLASS_III,
        "IV": DeviceClass.CLASS_IV,
    }

    dc = class_map.get(device_class.upper())
    if not dc:
        return {"error": f"Invalid device class: {device_class}"}

    from src.core.models import ClassificationResult

    classification = ClassificationResult(
        device_class=dc,
        rationale="User-specified classification",
        is_samd=is_software,
    )

    device_info = DeviceInfo(
        name="Device",
        description="Device for pathway calculation",
        intended_use="Pathway planning",
        is_software=is_software,
        manufacturer_name="Manufacturer",
    )

    pathway = _get_pathway(classification, device_info, has_mdel, has_qms_certificate)

    return {
        "pathway_name": pathway.pathway_name,
        "device_class": pathway.device_class.value,
        "requires_mdel": pathway.requires_mdel,
        "requires_mdl": pathway.requires_mdl,
        "steps": [
            {
                "step_number": step.step_number,
                "name": step.name,
                "description": step.description,
                "duration_days": step.estimated_duration_days,
                "documents_required": step.documents_required,
                "forms": step.forms,
                "fees": step.fees,
            }
            for step in pathway.steps
        ],
        "timeline": {
            "min_days": pathway.timeline.total_days_min,
            "max_days": pathway.timeline.total_days_max,
            "target_completion": str(pathway.timeline.target_completion),
        },
        "fees": {
            "mdel_fee": pathway.fees.mdel_fee,
            "mdl_fee": pathway.fees.mdl_fee,
            "annual_fee": pathway.fees.annual_fee,
            "total": pathway.fees.total,
            "currency": pathway.fees.currency,
            "notes": pathway.fees.notes,
        },
        "special_requirements": pathway.special_requirements,
    }


@tool
def create_checklist(
    device_class: str,
    device_name: str,
    device_description: str,
    intended_use: str,
    is_software: bool = False,
    include_optional: bool = True,
) -> dict[str, Any]:
    """
    Generate a regulatory checklist for a device.

    Use this tool when a user asks about what documents or steps they need,
    or wants a checklist for their regulatory submission.

    Args:
        device_class: Device class ("I", "II", "III", or "IV")
        device_name: Name of the device
        device_description: Description of the device
        intended_use: Intended use statement
        is_software: Whether this is a software device
        include_optional: Whether to include optional items

    Returns:
        Complete checklist with items organized by category
    """
    logger.info(f"Creating checklist for Class {device_class} device")

    class_map = {
        "I": DeviceClass.CLASS_I,
        "II": DeviceClass.CLASS_II,
        "III": DeviceClass.CLASS_III,
        "IV": DeviceClass.CLASS_IV,
    }

    dc = class_map.get(device_class.upper())
    if not dc:
        return {"error": f"Invalid device class: {device_class}"}

    from src.core.models import ClassificationResult

    classification = ClassificationResult(
        device_class=dc,
        rationale="User-specified classification",
        is_samd=is_software,
    )

    device_info = DeviceInfo(
        name=device_name,
        description=device_description,
        intended_use=intended_use,
        is_software=is_software,
        manufacturer_name="Manufacturer",
    )

    checklist = _generate_checklist(classification, device_info, include_optional=include_optional)

    # Organize by category
    by_category: dict[str, list[dict[str, Any]]] = {}
    for item in checklist.items:
        if item.category not in by_category:
            by_category[item.category] = []
        by_category[item.category].append(
            {
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "required": item.required,
                "status": item.status.value,
                "guidance_reference": item.guidance_reference,
                "form_number": item.form_number,
            }
        )

    return {
        "checklist_name": checklist.name,
        "device_class": checklist.device_class.value,
        "total_items": checklist.total_items,
        "items_by_category": by_category,
        "created_date": str(checklist.created_date),
    }


@tool
def search_regulations(
    query: str,
    category: str | None = None,
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """
    Search Health Canada regulatory documents.

    Use this tool when a user asks specific questions about regulations,
    guidance, or requirements that require looking up official documents.

    Args:
        query: Search query
        category: Optional filter - "regulation", "guidance", "standard", or "form"
        top_k: Number of results to return

    Returns:
        List of relevant document excerpts with sources
    """
    logger.info(f"Searching regulations: {query}")

    results = retrieve(
        query=query,
        top_k=top_k,
        filter_category=category,
    )

    return [
        {
            "content": result.content,
            "source": result.source,
            "score": result.score,
            "category": result.metadata.get("category", "unknown"),
            "title": result.metadata.get("title", "Unknown"),
        }
        for result in results
    ]


@tool
def get_fee_information(device_class: str) -> dict[str, Any]:
    """
    Get current Health Canada fee information for a device class.

    Use this tool when a user asks about regulatory fees, costs,
    or pricing for device licensing.

    Args:
        device_class: Device class ("I", "II", "III", or "IV")

    Returns:
        Fee breakdown including MDEL, MDL, and annual fees
    """
    logger.info(f"Getting fees for Class {device_class}")

    from src.core.pathway import FEES_2024

    class_map = {
        "I": DeviceClass.CLASS_I,
        "II": DeviceClass.CLASS_II,
        "III": DeviceClass.CLASS_III,
        "IV": DeviceClass.CLASS_IV,
    }

    dc = class_map.get(device_class.upper())
    if not dc:
        return {"error": f"Invalid device class: {device_class}"}

    mdl_fees = {
        "I": 0,
        "II": FEES_2024["mdl_class_ii"],
        "III": FEES_2024["mdl_class_iii"],
        "IV": FEES_2024["mdl_class_iv"],
    }

    annual_fees = {
        "I": 0,
        "II": 0,
        "III": FEES_2024["annual_right_to_sell_iii"],
        "IV": FEES_2024["annual_right_to_sell_iv"],
    }

    return {
        "device_class": device_class.upper(),
        "mdel_application_fee": FEES_2024["mdel_application"],
        "mdl_application_fee": mdl_fees[device_class.upper()],
        "annual_right_to_sell_fee": annual_fees[device_class.upper()],
        "mdl_amendment_fee": FEES_2024["mdl_amendment_admin"],
        "significant_change_fee": FEES_2024["mdl_amendment_significant"],
        "currency": "CAD",
        "fee_schedule_date": "April 2024",
        "notes": [
            "Fees are subject to annual adjustments",
            "MDEL fee is one-time; renewal is automatic if compliant",
            "Verify current fees with Health Canada before submission",
        ],
    }


@tool
def classify_confidentiality(
    entity_type: str,
    entity_id: str,
    organization_id: str,
    level: str,
    patent_number: str | None = None,
    justification: str | None = None,
    harm_if_disclosed: str | None = None,
) -> dict[str, Any]:
    """
    Classify an entity's confidentiality level for IP protection.

    Use this tool when a user needs to mark sensitive information as
    confidential, trade secret, or patent-pending before submission.
    Per SOR/98-282 s.43.2, manufacturers must identify CBI in submissions.

    Args:
        entity_type: Type of entity - one of:
            "evidence_item", "artifact", "claim", "document",
            "test_data", "design_file", "manufacturing_process",
            "supplier_agreement"
        entity_id: UUID of the entity to classify
        organization_id: UUID of the owning organization
        level: Confidentiality level - one of:
            "public" - Can appear in any document
            "confidential_submission" - Redacted from public portions
            "trade_secret" - Never disclosed, summarized only
            "patent_pending" - Can reference patent application
        patent_number: Required if level is "patent_pending"
        justification: Reason for confidential classification (required for CBI)
        harm_if_disclosed: Competitive harm if disclosed (required for CBI)

    Returns:
        Classification result with tag details
    """
    from uuid import UUID

    logger.info(f"Classifying {entity_type}/{entity_id} as {level}")

    # Validate level
    valid_levels = ["public", "confidential_submission", "trade_secret", "patent_pending"]
    if level not in valid_levels:
        return {
            "success": False,
            "error": f"Invalid level '{level}'. Valid levels: {valid_levels}",
        }

    try:
        entity_uuid = UUID(entity_id)
        org_uuid = UUID(organization_id)
    except ValueError as e:
        return {
            "success": False,
            "error": f"Invalid UUID: {e}",
        }

    # Check required fields for CBI
    if level in ("trade_secret", "confidential_submission"):
        if not justification:
            return {
                "success": False,
                "error": f"CBI classification ({level}) requires justification",
            }
        if not harm_if_disclosed:
            return {
                "success": False,
                "error": f"CBI classification ({level}) requires harm_if_disclosed",
            }

    if level == "patent_pending" and not patent_number:
        return {
            "success": False,
            "error": "patent_pending level requires patent_number",
        }

    try:
        service = get_confidentiality_service()
        tag = service.classify(
            entity_type=entity_type,
            entity_id=entity_uuid,
            level=level,  # type: ignore[arg-type]
            organization_id=org_uuid,
            patent_application_number=patent_number,
            justification=justification,
            harm_if_disclosed=harm_if_disclosed,
        )

        return {
            "success": True,
            "entity_type": tag.entity_type,
            "entity_id": str(tag.entity_id),
            "level": tag.level,
            "requires_cbi_request": tag.level in ("trade_secret", "confidential_submission"),
            "citation": tag.citation_text,
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
        }


@tool
def get_ip_inventory(organization_id: str) -> dict[str, Any]:
    """
    Get summary of IP assets (trade secrets, patents pending).

    Use this tool when a user wants to review their confidential
    business information before submission, or needs to generate
    a CBI request document.

    Args:
        organization_id: UUID of the organization

    Returns:
        IP inventory summary with counts by level and CBI status
    """
    from uuid import UUID

    logger.info(f"Getting IP inventory for org {organization_id}")

    try:
        org_uuid = UUID(organization_id)
    except ValueError as e:
        return {
            "success": False,
            "error": f"Invalid organization_id: {e}",
        }

    service = get_confidentiality_service()

    # Get classifications by level
    trade_secrets = service.get_trade_secrets(org_uuid)
    patent_pending = service.get_patent_pending(org_uuid)
    confidential_submission = service.get_confidential_submission(org_uuid)
    public = service.get_public(org_uuid)

    # Get CBI candidates (trade_secret + confidential_submission)
    cbi_candidates = service.get_cbi_candidates(org_uuid)

    return {
        "success": True,
        "organization_id": organization_id,
        "summary": {
            "public_count": len(public),
            "confidential_submission_count": len(confidential_submission),
            "trade_secret_count": len(trade_secrets),
            "patent_pending_count": len(patent_pending),
            "total_classified": len(public)
            + len(confidential_submission)
            + len(trade_secrets)
            + len(patent_pending),
        },
        "cbi_status": {
            "requires_cbi_request": len(cbi_candidates) > 0,
            "cbi_item_count": len(cbi_candidates),
        },
        "trade_secrets": [
            {
                "entity_type": ts.entity_type,
                "entity_id": str(ts.entity_id),
                "has_attestation": ts.trade_secret_attestation,
            }
            for ts in trade_secrets
        ],
        "patents_pending": [
            {
                "entity_type": pp.entity_type,
                "entity_id": str(pp.entity_id),
                "patent_application_number": pp.patent_application_number,
            }
            for pp in patent_pending
        ],
        "citation": "[SOR/98-282, s.43.2]",
    }


def get_agent_tools() -> list[Any]:
    """Return all available agent tools."""
    return [
        classify_device,
        get_regulatory_pathway,
        create_checklist,
        search_regulations,
        get_fee_information,
        classify_confidentiality,
        get_ip_inventory,
    ]
