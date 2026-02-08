"""
FastAPI REST API for the Health Canada Medical Device Regulatory Agent.

Provides endpoints for:
- Device classification
- Regulatory pathway generation
- Checklist creation
- Document search
- Chat interface
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from configs.settings import settings
from src.agents.regulatory_agent import SimpleRegulatoryAgent
from src.api.gap_routes import router as gap_router
from src.api.traceability_routes import router as traceability_router
from src.core.checklist import generate_checklist
from src.core.classification import classify_device
from src.core.models import (
    ClassificationResult,
    DeviceClass,
    DeviceInfo,
    HealthcareSituation,
    SaMDCategory,
    SaMDInfo,
)
from src.core.pathway import get_pathway
from src.retrieval.retriever import retrieve
from src.retrieval.vectorstore import vector_store
from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)

# Global agent instance
_agent: SimpleRegulatoryAgent | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    setup_logging(settings.log_level)
    logger.info("Starting Health Canada MedDev Agent API")

    global _agent
    _agent = SimpleRegulatoryAgent()

    yield

    # Shutdown
    logger.info("Shutting down API")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Health Canada Medical Device Regulatory Agent",
        description="AI-powered assistant for navigating Health Canada medical device regulations",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_app()


app.include_router(traceability_router)
app.include_router(gap_router)


# =============================================================================
# Request/Response Models
# =============================================================================


class DeviceInfoRequest(BaseModel):
    """Request model for device information."""

    name: str = Field(..., description="Device name")
    description: str = Field(..., description="Device description")
    intended_use: str = Field(..., description="Intended use statement")
    manufacturer_name: str = Field(..., description="Manufacturer name")
    is_software: bool = Field(default=False, description="Is this a software device?")
    is_ivd: bool = Field(default=False, description="Is this an IVD?")
    is_implantable: bool = Field(default=False, description="Is this implantable?")
    is_active: bool = Field(default=False, description="Is this an active device?")
    contact_duration: str | None = Field(default=None)
    invasive_type: str | None = Field(default=None)


class SaMDInfoRequest(BaseModel):
    """Request model for SaMD-specific information."""

    healthcare_situation: str = Field(..., description="critical, serious, or non_serious")
    significance: str = Field(..., description="treat, diagnose, drive, or inform")
    uses_ml: bool = Field(default=False)
    is_locked: bool = Field(default=True)
    clinical_validation_patients: int | None = Field(default=None)


class ClassificationRequest(BaseModel):
    """Request model for device classification."""

    device_info: DeviceInfoRequest
    samd_info: SaMDInfoRequest | None = None


class ClassificationResponse(BaseModel):
    """Response model for device classification."""

    device_class: str
    risk_level: str
    requires_mdl: bool
    review_days: int
    rationale: str
    classification_rules: list[str]
    is_samd: bool
    warnings: list[str]
    references: list[str]
    confidence: float


class PathwayRequest(BaseModel):
    """Request model for pathway generation."""

    device_class: str = Field(..., description="I, II, III, or IV")
    is_software: bool = Field(default=False)
    has_mdel: bool = Field(default=False)
    has_qms_certificate: bool = Field(default=False)


class ChecklistRequest(BaseModel):
    """Request model for checklist generation."""

    device_class: str
    device_info: DeviceInfoRequest
    include_optional: bool = Field(default=True)


class ChatRequest(BaseModel):
    """Request model for chat."""

    message: str = Field(..., description="User message")
    session_id: str | None = Field(default=None)


class ChatResponse(BaseModel):
    """Response model for chat."""

    response: str
    session_id: str


class SearchRequest(BaseModel):
    """Request model for document search."""

    query: str
    category: str | None = Field(default=None)
    top_k: int = Field(default=5, ge=1, le=20)


# =============================================================================
# API Endpoints
# =============================================================================


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/stats")
async def get_stats():
    """Get vector store statistics."""
    stats = vector_store.get_stats()
    stats["version"] = "0.1.0"
    return stats


@app.post("/api/v1/classify", response_model=ClassificationResponse)
async def classify_device_endpoint(request: ClassificationRequest):
    """
    Classify a medical device according to Health Canada regulations.

    Returns the device class (I-IV), rationale, and applicable rules.
    """
    try:
        # Convert request to domain models
        device_info = DeviceInfo(
            name=request.device_info.name,
            description=request.device_info.description,
            intended_use=request.device_info.intended_use,
            manufacturer_name=request.device_info.manufacturer_name,
            is_software=request.device_info.is_software,
            is_ivd=request.device_info.is_ivd,
            is_implantable=request.device_info.is_implantable,
            is_active=request.device_info.is_active,
            contact_duration=request.device_info.contact_duration,
            invasive_type=request.device_info.invasive_type,
        )

        samd_info = None
        if request.samd_info:
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
                healthcare_situation=situation_map[request.samd_info.healthcare_situation],
                significance=significance_map[request.samd_info.significance],
                uses_ml=request.samd_info.uses_ml,
                is_locked=request.samd_info.is_locked,
                clinical_validation_patients=request.samd_info.clinical_validation_patients,
            )

        # Classify
        result = classify_device(device_info, samd_info)

        return ClassificationResponse(
            device_class=result.device_class.value,
            risk_level=result.device_class.risk_level,
            requires_mdl=result.device_class.requires_mdl,
            review_days=result.device_class.review_days,
            rationale=result.rationale,
            classification_rules=result.classification_rules,
            is_samd=result.is_samd,
            warnings=result.warnings,
            references=result.references,
            confidence=result.confidence,
        )

    except Exception as e:
        logger.error(f"Classification error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/pathway")
async def get_pathway_endpoint(request: PathwayRequest):
    """
    Get the regulatory pathway for a device class.

    Returns steps, timeline, and fees.
    """
    try:
        class_map = {
            "I": DeviceClass.CLASS_I,
            "II": DeviceClass.CLASS_II,
            "III": DeviceClass.CLASS_III,
            "IV": DeviceClass.CLASS_IV,
        }

        device_class = class_map.get(request.device_class.upper())
        if not device_class:
            raise HTTPException(
                status_code=422, detail="Invalid device class. Must be I, II, III, or IV."
            )

        # Create minimal objects for pathway calculation
        classification = ClassificationResult(
            device_class=device_class,
            rationale="API request",
            is_samd=request.is_software,
        )

        device_info = DeviceInfo(
            name="API Device",
            description="Device from API request",
            intended_use="Pathway calculation",
            is_software=request.is_software,
            manufacturer_name="API",
        )

        pathway = get_pathway(
            classification,
            device_info,
            request.has_mdel,
            request.has_qms_certificate,
        )

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
                "start_date": str(pathway.timeline.start_date),
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pathway error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/checklist")
async def create_checklist_endpoint(request: ChecklistRequest):
    """
    Generate a regulatory checklist for a device.

    Returns categorized checklist items.
    """
    try:
        class_map = {
            "I": DeviceClass.CLASS_I,
            "II": DeviceClass.CLASS_II,
            "III": DeviceClass.CLASS_III,
            "IV": DeviceClass.CLASS_IV,
        }

        device_class = class_map.get(request.device_class.upper())
        if not device_class:
            raise HTTPException(
                status_code=422, detail="Invalid device class. Must be I, II, III, or IV."
            )

        classification = ClassificationResult(
            device_class=device_class,
            rationale="API request",
            is_samd=request.device_info.is_software,
        )

        device_info = DeviceInfo(
            name=request.device_info.name,
            description=request.device_info.description,
            intended_use=request.device_info.intended_use,
            is_software=request.device_info.is_software,
            manufacturer_name=request.device_info.manufacturer_name,
        )

        checklist = generate_checklist(
            classification,
            device_info,
            request.include_optional,
        )

        # Export as JSON-serializable dict
        return {
            "name": checklist.name,
            "device_class": checklist.device_class.value,
            "total_items": checklist.total_items,
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
                    "dependencies": item.dependencies,
                }
                for item in checklist.items
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Checklist error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/search")
async def search_documents_endpoint(request: SearchRequest):
    """
    Search regulatory documents.

    Returns relevant document excerpts with sources.
    """
    try:
        results = retrieve(
            query=request.query,
            top_k=request.top_k,
            filter_category=request.category,
        )

        return {
            "query": request.query,
            "results": [
                {
                    "content": r.content,
                    "source": r.source,
                    "score": r.score,
                    "metadata": r.metadata,
                }
                for r in results
            ],
        }

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Chat with the regulatory agent.

    Supports conversational interactions about regulatory requirements.
    """
    try:
        if _agent is None:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        response = _agent.chat(request.message)

        return ChatResponse(
            response=response,
            session_id=request.session_id or "default",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/chat/reset")
async def reset_chat_endpoint():
    """Reset the chat conversation."""
    if _agent:
        _agent.reset()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
