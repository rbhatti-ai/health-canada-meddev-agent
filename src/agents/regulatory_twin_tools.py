"""
Regulatory Twin Agent Tools — Sprint 4A

LangGraph-compatible tools wrapping all regulatory services:
- TraceabilityEngine (4 tools)
- EvidenceIngestionService (3 tools)
- AttestationService (3 tools)
- GapDetectionEngine (2 tools)
- ReadinessAssessment (1 tool)

Total: 13 tools

Each tool:
- Validates inputs before calling the service
- Returns structured dicts (serializable for LLM consumption)
- Handles errors gracefully (never crashes the agent)
- Uses regulatory-safe language in all descriptions

Per CLAUDE.md: Structure first, AI second.
Per architecture: Every AI output must be explainable.
"""

from typing import Any

from langchain_core.tools import tool

from src.utils.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Service accessor helpers (lazy imports to avoid circular deps)
# ---------------------------------------------------------------------------


def _get_traceability_engine() -> Any:
    """Lazy import to avoid circular dependencies at module load."""
    from src.core.traceability import get_traceability_engine

    return get_traceability_engine()


def _get_evidence_service() -> Any:
    """Lazy import to avoid circular dependencies at module load."""
    from src.core.evidence_ingestion import get_evidence_ingestion_service

    return get_evidence_ingestion_service()


def _get_attestation_service() -> Any:
    """Lazy import to avoid circular dependencies at module load."""
    from src.core.attestation_service import get_attestation_service

    return get_attestation_service()


def _get_gap_engine() -> Any:
    """Lazy import to avoid circular dependencies at module load."""
    from src.core.gap_engine import get_gap_engine

    return get_gap_engine()


def _get_readiness_assessment() -> Any:
    """Lazy import to avoid circular dependencies at module load."""
    from src.core.readiness import get_readiness_assessment

    return get_readiness_assessment()


# ---------------------------------------------------------------------------
# Error handling wrapper
# ---------------------------------------------------------------------------


def _safe_call(tool_name: str, func: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """
    Wrap a service call with consistent error handling.

    Returns a dict with either the result or an error message.
    Agent tools must NEVER raise — they return error dicts instead.
    This prevents the LangGraph agent from crashing on service failures.
    """
    try:
        result = func(*args, **kwargs)
        return {"status": "success", "tool": tool_name, "result": result}
    except ValueError as e:
        logger.warning(f"Tool {tool_name} validation error: {e}")
        return {"status": "error", "tool": tool_name, "error": str(e)}
    except Exception as e:
        logger.error(f"Tool {tool_name} unexpected error: {e}")
        return {
            "status": "error",
            "tool": tool_name,
            "error": f"Unexpected error: {e}",
        }


# ===========================================================================
# TRACEABILITY ENGINE TOOLS (4)
# ===========================================================================


@tool
def create_trace_link(
    source_type: str,
    source_id: str,
    target_type: str,
    target_id: str,
    relationship: str,
    rationale: str,
    created_by: str,
    organization_id: str,
    device_version_id: str,
) -> dict[str, Any]:
    """
    Create a regulatory trace link between two entities.

    Trace links form the backbone of regulatory traceability:
    claim -> hazard -> risk_control -> verification_test -> evidence_item

    Valid relationships are enforced by the TraceabilityEngine.

    Args:
        source_type: Entity type of the source (e.g., 'claim', 'hazard')
        source_id: UUID of the source entity
        target_type: Entity type of the target (e.g., 'hazard', 'risk_control')
        target_id: UUID of the target entity
        relationship: The relationship type (e.g., 'addresses', 'mitigated_by')
        rationale: Human-readable reason for this link
        created_by: UUID of the user creating the link
        organization_id: UUID of the organization
        device_version_id: UUID of the device version
    """
    engine = _get_traceability_engine()

    def _execute() -> Any:
        link = engine.create_link(
            source_type=source_type,
            source_id=source_id,
            target_type=target_type,
            target_id=target_id,
            relationship=relationship,
            rationale=rationale,
            created_by=created_by,
            organization_id=organization_id,
            device_version_id=device_version_id,
        )
        # TraceLink is a Pydantic model — convert to dict for serialization
        if hasattr(link, "model_dump"):
            return link.model_dump()
        elif hasattr(link, "dict"):
            return link.dict()
        return link

    return _safe_call("create_trace_link", _execute)


@tool
def get_trace_chain(claim_id: str) -> dict[str, Any]:
    """
    Follow the full regulatory chain from a claim down to evidence.

    Traces: claim -> hazard -> risk_control -> verification/validation_test -> evidence_item

    This is critical for regulatory audits — it shows the complete
    traceability path from a regulatory claim to supporting evidence.

    Args:
        claim_id: UUID of the claim to trace from
    """
    engine = _get_traceability_engine()

    def _execute() -> Any:
        chain = engine.get_full_chain(claim_id)
        if hasattr(chain, "model_dump"):
            return chain.model_dump()
        elif hasattr(chain, "dict"):
            return chain.dict()
        elif isinstance(chain, dict):
            return chain
        return {"chain": str(chain)}

    return _safe_call("get_trace_chain", _execute)


@tool
def get_coverage_report(device_version_id: str) -> dict[str, Any]:
    """
    Generate a coverage report for a device version.

    For each claim, shows: linked hazards, controls, tests, and evidence.
    Identifies gaps in the regulatory traceability matrix.

    This is what a Health Canada reviewer would examine to verify
    that all claims are properly supported.

    Args:
        device_version_id: UUID of the device version to evaluate
    """
    engine = _get_traceability_engine()

    def _execute() -> Any:
        report = engine.get_coverage_report(device_version_id)
        if hasattr(report, "model_dump"):
            return report.model_dump()
        elif hasattr(report, "dict"):
            return report.dict()
        elif isinstance(report, dict):
            return report
        return {"report": str(report)}

    return _safe_call("get_coverage_report", _execute)


@tool
def validate_trace_relationship(
    source_type: str,
    target_type: str,
    relationship: str,
) -> dict[str, Any]:
    """
    Check if a proposed trace link relationship is valid.

    The regulatory chain has strict rules about which entity types
    can be linked and what relationship types are allowed.

    Use this BEFORE creating a link to verify it's valid.

    Args:
        source_type: Entity type of the source (e.g., 'claim')
        target_type: Entity type of the target (e.g., 'hazard')
        relationship: The proposed relationship (e.g., 'addresses')
    """
    engine = _get_traceability_engine()

    def _execute() -> Any:
        is_valid = engine.validate_link(source_type, target_type, relationship)
        return {
            "is_valid": is_valid,
            "source_type": source_type,
            "target_type": target_type,
            "relationship": relationship,
        }

    return _safe_call("validate_trace_relationship", _execute)


# ===========================================================================
# EVIDENCE INGESTION SERVICE TOOLS (3)
# ===========================================================================


@tool
def ingest_evidence(
    device_version_id: str,
    evidence_type: str,
    title: str,
    artifact_data: dict[str, Any],
    linked_to: dict[str, str],
    organization_id: str,
    created_by: str,
) -> dict[str, Any]:
    """
    Ingest an evidence item with its artifact and create a trace link.

    Workflow:
    1. Creates an artifact (file metadata + content hash)
    2. Creates an evidence_item (typed, with strength assessment)
    3. Creates a trace_link to the relevant claim/test/control

    Args:
        device_version_id: UUID of the device version
        evidence_type: Type of evidence (e.g., 'clinical', 'bench_test', 'literature')
        title: Title of the evidence item
        artifact_data: Dict with artifact metadata (type, title, storage_uri, etc.)
        linked_to: Dict with target info (target_type, target_id, relationship)
        organization_id: UUID of the organization
        created_by: UUID of the user
    """
    service = _get_evidence_service()

    def _execute() -> Any:
        result = service.ingest_evidence(
            device_version_id=device_version_id,
            evidence_type=evidence_type,
            title=title,
            artifact_data=artifact_data,
            linked_to=linked_to,
            organization_id=organization_id,
            created_by=created_by,
        )
        if hasattr(result, "model_dump"):
            return result.model_dump()
        elif hasattr(result, "dict"):
            return result.dict()
        elif isinstance(result, dict):
            return result
        return {"evidence": str(result)}

    return _safe_call("ingest_evidence", _execute)


@tool
def get_evidence_for_device(device_version_id: str) -> dict[str, Any]:
    """
    List all evidence items for a device version.

    Returns the complete evidence inventory — essential for
    understanding what evidence currently exists before identifying gaps.

    A Health Canada reviewer's first question is often:
    'Show me all your evidence.'

    Args:
        device_version_id: UUID of the device version
    """
    service = _get_evidence_service()

    def _execute() -> Any:
        evidence_list = service.get_evidence_for_device(device_version_id)
        # Convert each item to dict if needed
        results = []
        for item in evidence_list:
            if hasattr(item, "model_dump"):
                results.append(item.model_dump())
            elif hasattr(item, "dict"):
                results.append(item.dict())
            elif isinstance(item, dict):
                results.append(item)
            else:
                results.append({"item": str(item)})
        return {"device_version_id": device_version_id, "evidence_items": results}

    return _safe_call("get_evidence_for_device", _execute)


@tool
def find_unlinked_evidence(device_version_id: str) -> dict[str, Any]:
    """
    Find evidence items not connected to any claim, test, or control.

    Orphaned evidence is a regulatory risk — it exists but doesn't
    support any claim in the traceability matrix. This means either:
    1. A trace link is missing (needs to be created), or
    2. The evidence is irrelevant (should be reviewed)

    Args:
        device_version_id: UUID of the device version
    """
    service = _get_evidence_service()

    def _execute() -> Any:
        unlinked = service.get_unlinked_evidence(device_version_id)
        results = []
        for item in unlinked:
            if hasattr(item, "model_dump"):
                results.append(item.model_dump())
            elif hasattr(item, "dict"):
                results.append(item.dict())
            elif isinstance(item, dict):
                results.append(item)
            else:
                results.append({"item": str(item)})
        return {
            "device_version_id": device_version_id,
            "unlinked_count": len(results),
            "unlinked_items": results,
        }

    return _safe_call("find_unlinked_evidence", _execute)


# ===========================================================================
# ATTESTATION SERVICE TOOLS (3)
# ===========================================================================


@tool
def create_attestation(
    artifact_id: str,
    attested_by: str,
    attestation_type: str,
    note: str,
    organization_id: str,
) -> dict[str, Any]:
    """
    Create a human attestation (sign-off) on an artifact.

    Human-in-the-loop is REQUIRED per platform policy.
    No AI-generated regulatory artifact is final without human approval.

    Attestation types:
    - 'reviewed': Human reviewed the content
    - 'approved': Human approved for regulatory use
    - 'rejected': Human rejected, needs rework
    - 'acknowledged': Human saw it, no opinion

    Args:
        artifact_id: UUID of the artifact to attest
        attested_by: UUID of the user attesting
        attestation_type: One of: reviewed, approved, rejected, acknowledged
        note: Human-written note about the attestation
        organization_id: UUID of the organization
    """
    service = _get_attestation_service()

    def _execute() -> Any:
        attestation = service.attest_artifact(
            artifact_id=artifact_id,
            attested_by=attested_by,
            attestation_type=attestation_type,
            note=note,
            organization_id=organization_id,
        )
        if hasattr(attestation, "model_dump"):
            return attestation.model_dump()
        elif hasattr(attestation, "dict"):
            return attestation.dict()
        elif isinstance(attestation, dict):
            return attestation
        return {"attestation": str(attestation)}

    return _safe_call("create_attestation", _execute)


@tool
def get_pending_attestations(organization_id: str) -> dict[str, Any]:
    """
    Get all artifacts awaiting human review for an organization.

    These are items that have been created (possibly by AI) but
    have NOT yet been reviewed/approved by a human.

    Per regulatory requirements, these items cannot be used in
    a submission until attested.

    Args:
        organization_id: UUID of the organization
    """
    service = _get_attestation_service()

    def _execute() -> Any:
        pending = service.get_unattested_items(organization_id)
        # pending is typically a list of dicts already
        results = []
        for item in pending:
            if isinstance(item, dict):
                results.append(item)
            elif hasattr(item, "model_dump"):
                results.append(item.model_dump())
            elif hasattr(item, "dict"):
                results.append(item.dict())
            else:
                results.append({"item": str(item)})
        return {
            "organization_id": organization_id,
            "pending_count": len(results),
            "pending_items": results,
        }

    return _safe_call("get_pending_attestations", _execute)


@tool
def get_attestation_trail(artifact_id: str) -> dict[str, Any]:
    """
    Get the full attestation audit trail for an artifact.

    Shows the complete history of human reviews: who reviewed,
    when, what type of attestation, and their notes.

    This is essential for regulatory audits — Health Canada and
    ISO 13485 require full audit trails showing human oversight.

    Args:
        artifact_id: UUID of the artifact
    """
    service = _get_attestation_service()

    def _execute() -> Any:
        trail = service.get_attestation_audit_trail(artifact_id)
        results = []
        for item in trail:
            if hasattr(item, "model_dump"):
                results.append(item.model_dump())
            elif hasattr(item, "dict"):
                results.append(item.dict())
            elif isinstance(item, dict):
                results.append(item)
            else:
                results.append({"item": str(item)})
        return {
            "artifact_id": artifact_id,
            "attestation_count": len(results),
            "attestations": results,
        }

    return _safe_call("get_attestation_trail", _execute)


# ===========================================================================
# GAP DETECTION ENGINE TOOLS (2)
# ===========================================================================


@tool
def run_gap_analysis(device_version_id: str) -> dict[str, Any]:
    """
    Run a full gap analysis for a device version.

    Executes all 12 gap detection rules (GAP-001 through GAP-012)
    and returns a comprehensive report of findings with severities.

    Severity levels: critical, major, minor, info
    Categories: coverage, completeness, consistency, evidence_strength

    NOTE: This is a deterministic, rules-based analysis — not AI opinion.

    Args:
        device_version_id: UUID of the device version to evaluate
    """
    engine = _get_gap_engine()

    def _execute() -> Any:
        report = engine.evaluate(device_version_id)
        if hasattr(report, "model_dump"):
            return report.model_dump()
        elif hasattr(report, "dict"):
            return report.dict()
        elif isinstance(report, dict):
            return report
        return {"report": str(report)}

    return _safe_call("run_gap_analysis", _execute)


@tool
def get_critical_gaps(device_version_id: str) -> dict[str, Any]:
    """
    Get ONLY the critical gap findings for a device version.

    Critical gaps are submission blockers — items that MUST be
    resolved before a Health Canada submission can proceed.

    Examples of critical gaps:
    - Unmitigated hazards (GAP-001)
    - Unverified risk controls (GAP-002)
    - Missing intended use (GAP-004)
    - Incomplete risk chain (GAP-010)
    - No clinical evidence for Class III/IV (GAP-012)

    Args:
        device_version_id: UUID of the device version
    """
    engine = _get_gap_engine()

    def _execute() -> Any:
        report = engine.evaluate(device_version_id)
        # Extract critical findings from the report
        if hasattr(report, "critical_findings"):
            critical = report.critical_findings
        elif hasattr(report, "findings"):
            critical = [
                f
                for f in report.findings
                if (
                    (hasattr(f, "severity") and f.severity == "critical")
                    or (isinstance(f, dict) and f.get("severity") == "critical")
                )
            ]
        elif isinstance(report, dict):
            findings = report.get("findings", [])
            critical = [
                f for f in findings if (isinstance(f, dict) and f.get("severity") == "critical")
            ]
        else:
            critical = []

        # Serialize
        results = []
        for item in critical:
            if hasattr(item, "model_dump"):
                results.append(item.model_dump())
            elif hasattr(item, "dict"):
                results.append(item.dict())
            elif isinstance(item, dict):
                results.append(item)
            else:
                results.append({"finding": str(item)})

        return {
            "device_version_id": device_version_id,
            "critical_count": len(results),
            "critical_findings": results,
        }

    return _safe_call("get_critical_gaps", _execute)


# ===========================================================================
# READINESS ASSESSMENT TOOL (1)
# ===========================================================================


@tool
def get_readiness_assessment(device_version_id: str) -> dict[str, Any]:
    """
    Run a full readiness assessment for a device version.

    Combines gap analysis with scoring to produce:
    - overall_readiness_score (0.0 to 1.0)
    - category_scores (coverage, completeness, consistency, evidence_strength)
    - critical_blockers (items that must be resolved)
    - summary (regulatory-safe language)

    IMPORTANT: This assessment uses the phrase
    'Readiness assessment based on configured expectations.'
    It NEVER declares compliance or submission readiness.

    Args:
        device_version_id: UUID of the device version
    """
    assessment = _get_readiness_assessment()

    def _execute() -> Any:
        report = assessment.assess(device_version_id)
        if hasattr(report, "model_dump"):
            return report.model_dump()
        elif hasattr(report, "dict"):
            return report.dict()
        elif isinstance(report, dict):
            return report
        return {"report": str(report)}

    return _safe_call("get_readiness_assessment", _execute)


# ===========================================================================
# TOOL REGISTRY
# ===========================================================================

# All regulatory twin tools, ordered by service group
REGULATORY_TWIN_TOOLS = [
    # Traceability (4)
    create_trace_link,
    get_trace_chain,
    get_coverage_report,
    validate_trace_relationship,
    # Evidence (3)
    ingest_evidence,
    get_evidence_for_device,
    find_unlinked_evidence,
    # Attestation (3)
    create_attestation,
    get_pending_attestations,
    get_attestation_trail,
    # Gap Detection (2)
    run_gap_analysis,
    get_critical_gaps,
    # Readiness (1)
    get_readiness_assessment,
]


def get_regulatory_twin_tools() -> list:
    """
    Return all regulatory twin agent tools.

    These tools wrap Sprint 2 + Sprint 3 services for use
    by the LangGraph agent. Combined with the original 5 tools
    from src/agents/tools.py, the agent has 18 total tools.
    """
    return list(REGULATORY_TWIN_TOOLS)
