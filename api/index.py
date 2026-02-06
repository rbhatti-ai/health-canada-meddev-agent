"""
Vercel serverless function - Lightweight API.
Core classification, pathway, and checklist endpoints only.
(RAG/search requires separate deployment due to size limits)
"""

from typing import Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from enum import Enum

# ============================================================================
# Models (inline to avoid import issues)
# ============================================================================

class DeviceClass(str, Enum):
    CLASS_I = "I"
    CLASS_II = "II"
    CLASS_III = "III"
    CLASS_IV = "IV"

class HealthcareSituation(str, Enum):
    CRITICAL = "critical"
    SERIOUS = "serious"
    NON_SERIOUS = "non_serious"

class SaMDCategory(str, Enum):
    TREAT = "treat"
    DIAGNOSE = "diagnose"
    DRIVE = "drive"
    INFORM = "inform"

# IMDRF SaMD Classification Matrix
SAMD_MATRIX = {
    (HealthcareSituation.CRITICAL, SaMDCategory.TREAT): DeviceClass.CLASS_IV,
    (HealthcareSituation.CRITICAL, SaMDCategory.DIAGNOSE): DeviceClass.CLASS_IV,
    (HealthcareSituation.CRITICAL, SaMDCategory.DRIVE): DeviceClass.CLASS_III,
    (HealthcareSituation.CRITICAL, SaMDCategory.INFORM): DeviceClass.CLASS_II,
    (HealthcareSituation.SERIOUS, SaMDCategory.TREAT): DeviceClass.CLASS_IV,
    (HealthcareSituation.SERIOUS, SaMDCategory.DIAGNOSE): DeviceClass.CLASS_III,
    (HealthcareSituation.SERIOUS, SaMDCategory.DRIVE): DeviceClass.CLASS_II,
    (HealthcareSituation.SERIOUS, SaMDCategory.INFORM): DeviceClass.CLASS_II,
    (HealthcareSituation.NON_SERIOUS, SaMDCategory.TREAT): DeviceClass.CLASS_III,
    (HealthcareSituation.NON_SERIOUS, SaMDCategory.DIAGNOSE): DeviceClass.CLASS_II,
    (HealthcareSituation.NON_SERIOUS, SaMDCategory.DRIVE): DeviceClass.CLASS_II,
    (HealthcareSituation.NON_SERIOUS, SaMDCategory.INFORM): DeviceClass.CLASS_I,
}

# 2024 Health Canada Fees
FEES_2024 = {
    "mdel_application": 4590,
    "mdl_class_ii": 468,
    "mdl_class_iii": 7658,
    "mdl_class_iv": 23130,
    "annual_class_ii": 0,
    "annual_class_iii": 831,
    "annual_class_iv": 1662,
}

# ============================================================================
# Request/Response Models
# ============================================================================

class DeviceInfoRequest(BaseModel):
    name: str
    description: str
    intended_use: str
    manufacturer_name: str
    is_software: bool = False
    is_implantable: bool = False
    contact_duration: Optional[str] = None
    is_active: bool = False

class SaMDInfoRequest(BaseModel):
    healthcare_situation: HealthcareSituation
    significance: SaMDCategory
    uses_ml: bool = False

class ClassifyRequest(BaseModel):
    device_info: DeviceInfoRequest
    samd_info: Optional[SaMDInfoRequest] = None

class ClassifyResponse(BaseModel):
    device_class: str
    risk_level: str
    is_samd: bool
    rationale: str
    confidence: float
    warnings: List[str] = []

class PathwayRequest(BaseModel):
    device_class: str
    is_software: bool = False
    has_mdel: bool = False

class FeeBreakdown(BaseModel):
    mdel_fee: float
    mdl_fee: float
    annual_fee: float
    total: float

class PathwayStep(BaseModel):
    name: str
    description: str
    duration_days: Optional[int] = None

class PathwayResponse(BaseModel):
    device_class: str
    steps: List[PathwayStep]
    fees: FeeBreakdown
    timeline_days_min: int
    timeline_days_max: int

# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Health Canada MedDev Agent API",
    description="Medical device classification, pathway, and fee calculation API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Endpoints
# ============================================================================

@app.get("/")
def root():
    return {
        "service": "Health Canada Medical Device Regulatory Agent",
        "version": "1.0.0",
        "endpoints": ["/health", "/api/v1/classify", "/api/v1/pathway", "/docs"],
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "health-canada-meddev-agent"}

@app.post("/api/v1/classify", response_model=ClassifyResponse)
def classify_device(request: ClassifyRequest):
    """Classify a medical device according to Health Canada regulations."""
    device = request.device_info
    samd = request.samd_info

    warnings = []

    # SaMD Classification
    if device.is_software and samd:
        key = (samd.healthcare_situation, samd.significance)
        device_class = SAMD_MATRIX.get(key, DeviceClass.CLASS_II)

        rationale = (
            f"SaMD Classification (IMDRF N12): "
            f"Healthcare situation: {samd.healthcare_situation.value}, "
            f"Significance: {samd.significance.value}"
        )

        if samd.uses_ml:
            warnings.append("ML-enabled device may require PCCP (Predetermined Change Control Plan)")

        return ClassifyResponse(
            device_class=device_class.value,
            risk_level=_get_risk_level(device_class),
            is_samd=True,
            rationale=rationale,
            confidence=0.9,
            warnings=warnings,
        )

    # Traditional Device Classification
    if device.is_implantable:
        if device.contact_duration == "long-term":
            device_class = DeviceClass.CLASS_IV
            rationale = "Long-term implantable device (Schedule 1, Rule 8)"
        else:
            device_class = DeviceClass.CLASS_III
            rationale = "Short-term implantable device (Schedule 1, Rule 7)"
    elif device.is_active:
        device_class = DeviceClass.CLASS_II
        rationale = "Active (powered) device (Schedule 1, Rules 9-11)"
    else:
        device_class = DeviceClass.CLASS_I
        rationale = "Non-invasive, non-active device (Schedule 1, Rules 1-4)"

    return ClassifyResponse(
        device_class=device_class.value,
        risk_level=_get_risk_level(device_class),
        is_samd=False,
        rationale=rationale,
        confidence=0.85,
        warnings=warnings,
    )

@app.post("/api/v1/pathway", response_model=PathwayResponse)
def get_pathway(request: PathwayRequest):
    """Get regulatory pathway with fees and timeline."""

    device_class = request.device_class.upper()
    if device_class not in ["I", "II", "III", "IV"]:
        raise HTTPException(status_code=422, detail="Invalid device class")

    steps = []

    # MDEL Step
    if not request.has_mdel:
        steps.append(PathwayStep(
            name="Obtain MDEL",
            description="Medical Device Establishment Licence application",
            duration_days=30,
        ))

    # QMS Step (Class II-IV)
    if device_class != "I":
        steps.append(PathwayStep(
            name="ISO 13485 QMS Certificate",
            description="Obtain quality management system certification",
            duration_days=90,
        ))

    # Cybersecurity (Software)
    if request.is_software:
        steps.append(PathwayStep(
            name="Cybersecurity Documentation",
            description="Prepare cybersecurity risk assessment and SBOM",
            duration_days=14,
        ))

    # MDL Step (Class II-IV)
    if device_class != "I":
        review_days = {"II": 15, "III": 75, "IV": 90}.get(device_class, 75)
        steps.append(PathwayStep(
            name=f"Submit MDL Application (Class {device_class})",
            description=f"Medical Device Licence application - {review_days} day review",
            duration_days=review_days,
        ))

    # Calculate fees
    mdel_fee = 0 if request.has_mdel else FEES_2024["mdel_application"]
    mdl_fee = {
        "I": 0,
        "II": FEES_2024["mdl_class_ii"],
        "III": FEES_2024["mdl_class_iii"],
        "IV": FEES_2024["mdl_class_iv"],
    }.get(device_class, 0)
    annual_fee = {
        "I": 0,
        "II": FEES_2024["annual_class_ii"],
        "III": FEES_2024["annual_class_iii"],
        "IV": FEES_2024["annual_class_iv"],
    }.get(device_class, 0)

    # Calculate timeline
    timeline_min = sum(s.duration_days or 0 for s in steps)
    timeline_max = int(timeline_min * 1.5)

    return PathwayResponse(
        device_class=device_class,
        steps=steps,
        fees=FeeBreakdown(
            mdel_fee=mdel_fee,
            mdl_fee=mdl_fee,
            annual_fee=annual_fee,
            total=mdel_fee + mdl_fee,
        ),
        timeline_days_min=timeline_min,
        timeline_days_max=timeline_max,
    )

def _get_risk_level(device_class: DeviceClass) -> str:
    return {
        DeviceClass.CLASS_I: "Lowest Risk",
        DeviceClass.CLASS_II: "Low-Moderate Risk",
        DeviceClass.CLASS_III: "Moderate-High Risk",
        DeviceClass.CLASS_IV: "Highest Risk",
    }.get(device_class, "Unknown")
