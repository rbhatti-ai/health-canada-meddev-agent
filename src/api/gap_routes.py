"""
Gap Detection & Readiness Assessment API Routes.

Sprint 3c — Exposes gap detection engine and readiness assessment
via REST endpoints. All outputs use regulatory-safe language.

Endpoints:
    GET /api/v1/gaps/{device_version_id}          — full gap report
    GET /api/v1/gaps/{device_version_id}/critical  — critical gaps only
    GET /api/v1/readiness/{device_version_id}      — readiness assessment
    GET /api/v1/rules                              — list all gap rules
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.core.gap_engine import get_gap_engine
from src.core.readiness import get_readiness_assessment
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["gap-detection"])


# =============================================================================
# Response Models
# =============================================================================


class GapFindingResponse(BaseModel):
    """API response model for a single gap finding."""

    rule_id: str = Field(..., description="Rule identifier (e.g. GAP-001)")
    rule_name: str = Field(..., description="Human-readable rule name")
    severity: str = Field(..., description="Finding severity: critical, major, minor, info")
    category: str = Field(
        ..., description="Finding category: coverage, completeness, consistency, evidence_strength"
    )
    description: str = Field(..., description="What was found")
    entity_type: str = Field(..., description="Entity type involved")
    entity_id: str = Field(default="", description="Entity ID if applicable")
    remediation: str = Field(..., description="Suggested remediation")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional details")


class GapReportResponse(BaseModel):
    """API response model for a full gap report."""

    device_version_id: str = Field(..., description="Device version evaluated")
    evaluated_at: str = Field(..., description="ISO timestamp of evaluation")
    rules_executed: int = Field(..., description="Number of rules executed")
    total_findings: int = Field(..., description="Total findings count")
    critical_count: int = Field(..., description="Critical severity count")
    major_count: int = Field(..., description="Major severity count")
    minor_count: int = Field(..., description="Minor severity count")
    info_count: int = Field(..., description="Info severity count")
    findings: list[GapFindingResponse] = Field(default_factory=list, description="All findings")


class CriticalGapsResponse(BaseModel):
    """API response model for critical gaps only."""

    device_version_id: str = Field(..., description="Device version evaluated")
    critical_count: int = Field(..., description="Number of critical findings")
    critical_findings: list[GapFindingResponse] = Field(
        default_factory=list, description="Critical findings only"
    )


class CategoryScoreResponse(BaseModel):
    """API response model for a category score."""

    category: str = Field(..., description="Score category name")
    score: float = Field(..., description="Category score (0.0-1.0)")
    finding_count: int = Field(..., description="Findings in this category")
    critical_count: int = Field(..., description="Critical findings in this category")
    assessment: str = Field(..., description="Regulatory-safe assessment text")


class ReadinessReportResponse(BaseModel):
    """API response model for readiness assessment."""

    device_version_id: str = Field(..., description="Device version evaluated")
    overall_readiness_score: float = Field(..., description="Overall readiness score (0.0-1.0)")
    category_scores: list[CategoryScoreResponse] = Field(
        default_factory=list, description="Per-category scores"
    )
    critical_blockers: list[GapFindingResponse] = Field(
        default_factory=list, description="Critical blocking findings"
    )
    summary: str = Field(..., description="Regulatory-safe summary text")


class GapRuleResponse(BaseModel):
    """API response model for a gap rule definition."""

    id: str = Field(..., description="Rule identifier")
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="What the rule checks")
    severity: str = Field(..., description="Default severity")
    category: str = Field(..., description="Rule category")
    version: int = Field(..., description="Rule version")
    enabled: bool = Field(..., description="Whether rule is active")


class RulesListResponse(BaseModel):
    """API response model for rules listing."""

    total_rules: int = Field(..., description="Total number of rules")
    enabled_rules: int = Field(..., description="Number of enabled rules")
    rules: list[GapRuleResponse] = Field(default_factory=list, description="All rules")


# =============================================================================
# Endpoints
# =============================================================================


@router.get(
    "/gaps/{device_version_id}",
    response_model=GapReportResponse,
    summary="Run full gap analysis",
    description="Evaluates all gap detection rules against a device version "
    "and returns findings with severity and remediation.",
)
async def get_gap_report(device_version_id: str) -> GapReportResponse:
    """Run full gap analysis for a device version."""
    try:
        engine = get_gap_engine()
        report = engine.evaluate(device_version_id)

        findings = []
        for f in report.findings:
            findings.append(
                GapFindingResponse(
                    rule_id=f.rule_id,
                    rule_name=f.rule_name,
                    severity=f.severity,
                    category=f.category,
                    description=f.description,
                    entity_type=f.entity_type or "",
                    entity_id=f.entity_id or "",
                    remediation=f.remediation,
                    details=f.details if hasattr(f, "details") and f.details else {},
                )
            )

        return GapReportResponse(
            device_version_id=report.device_version_id,
            evaluated_at=report.evaluated_at,
            rules_executed=report.rules_executed,
            total_findings=report.total_findings,
            critical_count=report.critical_count,
            major_count=report.major_count,
            minor_count=report.minor_count,
            info_count=report.info_count,
            findings=findings,
        )

    except ValueError as e:
        logger.warning(f"Invalid request for gap report: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Gap analysis failed for {device_version_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Gap analysis failed: {type(e).__name__}",
        ) from None


@router.get(
    "/gaps/{device_version_id}/critical",
    response_model=CriticalGapsResponse,
    summary="Get critical gaps only",
    description="Returns only critical-severity findings for a device version.",
)
async def get_critical_gaps(device_version_id: str) -> CriticalGapsResponse:
    """Get critical gaps only for a device version."""
    try:
        engine = get_gap_engine()
        report = engine.evaluate(device_version_id)

        critical = []
        for f in report.critical_findings:
            critical.append(
                GapFindingResponse(
                    rule_id=f.rule_id,
                    rule_name=f.rule_name,
                    severity=f.severity,
                    category=f.category,
                    description=f.description,
                    entity_type=f.entity_type or "",
                    entity_id=f.entity_id or "",
                    remediation=f.remediation,
                    details=f.details if hasattr(f, "details") and f.details else {},
                )
            )

        return CriticalGapsResponse(
            device_version_id=report.device_version_id,
            critical_count=report.critical_count,
            critical_findings=critical,
        )

    except ValueError as e:
        logger.warning(f"Invalid request for critical gaps: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Critical gap analysis failed for {device_version_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Critical gap analysis failed: {type(e).__name__}",
        ) from None


@router.get(
    "/readiness/{device_version_id}",
    response_model=ReadinessReportResponse,
    summary="Run readiness assessment",
    description="Evaluates regulatory readiness for a device version. "
    "Returns scores, blockers, and a regulatory-safe summary.",
)
async def get_readiness_report(device_version_id: str) -> ReadinessReportResponse:
    """Run readiness assessment for a device version."""
    try:
        assessment = get_readiness_assessment()
        report = assessment.assess(device_version_id)

        category_scores = []
        for cs in report.category_scores:
            category_scores.append(
                CategoryScoreResponse(
                    category=cs.category,
                    score=cs.score,
                    finding_count=cs.finding_count,
                    critical_count=cs.critical_count,
                    assessment=cs.assessment,
                )
            )

        blockers = []
        for f in report.critical_blockers:
            blockers.append(
                GapFindingResponse(
                    rule_id=f.rule_id,
                    rule_name=f.rule_name,
                    severity=f.severity,
                    category=f.category,
                    description=f.description,
                    entity_type=f.entity_type or "",
                    entity_id=f.entity_id or "",
                    remediation=f.remediation,
                    details=f.details if hasattr(f, "details") and f.details else {},
                )
            )

        return ReadinessReportResponse(
            device_version_id=device_version_id,
            overall_readiness_score=report.overall_readiness_score,
            category_scores=category_scores,
            critical_blockers=blockers,
            summary=report.summary,
        )

    except ValueError as e:
        logger.warning(f"Invalid request for readiness: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Readiness assessment failed for {device_version_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Readiness assessment failed: {type(e).__name__}",
        ) from None


@router.get(
    "/rules",
    response_model=RulesListResponse,
    summary="List all gap detection rules",
    description="Returns all configured gap detection rules with their metadata.",
)
async def list_rules() -> RulesListResponse:
    """List all gap detection rules."""
    try:
        engine = get_gap_engine()
        rules = engine.get_rules()

        rule_responses = []
        for r in rules:
            rule_responses.append(
                GapRuleResponse(
                    id=r.id,
                    name=r.name,
                    description=r.description,
                    severity=r.severity,
                    category=r.category,
                    version=r.version,
                    enabled=r.enabled,
                )
            )

        enabled_count = sum(1 for r in rules if r.enabled)

        return RulesListResponse(
            total_rules=len(rules),
            enabled_rules=enabled_count,
            rules=rule_responses,
        )

    except Exception as e:
        logger.error(f"Failed to list rules: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list rules: {type(e).__name__}",
        ) from None
