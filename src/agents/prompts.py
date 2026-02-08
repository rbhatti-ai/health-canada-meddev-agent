"""
Regulatory Analysis Prompts + Structured Output Schemas.

Sprint 4B + 5C deliverable. Provides:
- System prompts for regulatory analysis tasks
- Pydantic models for structured AI responses
- Regulatory-safe language enforcement
- AI provenance logging patterns
- Citation requirements (Sprint 5C)

Every AI output in this platform MUST:
1. Use regulatory-safe language (no "compliant", "ready", "will pass")
2. Be logged to the ai_runs table before display
3. Include provenance metadata (model, timestamp, prompt hash)
4. Cite regulatory sources when making substantive claims (Sprint 5C)
"""

import hashlib
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from src.utils.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Regulatory-Safe Language Enforcement
# ---------------------------------------------------------------------------

# Words/phrases that MUST NEVER appear in AI-generated regulatory output.
# Aligned with readiness.py FORBIDDEN_WORDS — single source of truth here,
# re-exported for use by readiness.py and all agent outputs.
FORBIDDEN_WORDS: list[str] = [
    "compliant",
    "compliance achieved",
    "fully compliant",
    "ready for submission",
    "submission ready",
    "ready to submit",
    "will pass",
    "guaranteed",
    "certifies",
    "certified",
    "approved",
    "ensures compliance",
    "meets all requirements",
    "no issues found",
]

# Approved replacements for common unsafe phrases.
# Keys are lowercase forbidden phrases; values are safe alternatives.
APPROVED_REPLACEMENTS: dict[str, str] = {
    "compliant": "aligned with configured expectations",
    "compliance achieved": "expectations assessment indicates alignment",
    "fully compliant": "assessment indicates alignment with configured expectations",
    "ready for submission": ("readiness assessment based on configured expectations"),
    "submission ready": "readiness assessment based on configured expectations",
    "ready to submit": "readiness assessment based on configured expectations",
    "will pass": "assessment indicates favorable alignment",
    "guaranteed": "assessment based on available evidence",
    "certifies": "documents an assessment of",
    "certified": "assessed against configured expectations",
    "approved": "assessed as aligned with expectations",
    "ensures compliance": "supports alignment with configured expectations",
    "meets all requirements": ("assessment indicates alignment with configured expectations"),
    "no issues found": "no findings identified in current assessment scope",
}

# Valid task types the prompt router can handle.
TASK_TYPES = Literal[
    "regulatory_agent",
    "hazard_assessment",
    "coverage_gap",
    "evidence_review",
    "readiness_summary",
    "device_analysis",
]

# ---------------------------------------------------------------------------
# System Prompts
# ---------------------------------------------------------------------------

REGULATORY_AGENT_SYSTEM_PROMPT: str = """You are a Health Canada medical device regulatory assistant built into the Rigour Medtech platform.

ROLE:
You help medical device manufacturers navigate Health Canada regulatory requirements including device classification, regulatory pathways, documentation, risk management (ISO 14971), traceability, and submission readiness.

CAPABILITIES — you have access to tools that can:
- Classify devices per Health Canada SOR/98-282 Schedule 1
- Determine regulatory pathways (MDEL, MDL) with timelines and fees
- Create and traverse regulatory trace links (claim → hazard → harm → risk_control → verification → evidence)
- Ingest and link evidence items
- Create attestation records for human sign-off
- Run gap analysis against 12 deterministic rules (GAP-001 through GAP-012)
- Generate readiness assessments with category scores

CRITICAL LANGUAGE RULES — you MUST follow these in EVERY response:
1. NEVER say "compliant", "ready for submission", "will pass", "guaranteed", "approved", or "certified".
2. ALWAYS use "readiness assessment based on configured expectations" instead of "ready".
3. ALWAYS use "aligned with configured expectations" instead of "compliant".
4. ALWAYS use "assessment indicates alignment" instead of "meets requirements".
5. ALWAYS qualify AI-generated analysis: "Based on available data and configured rules..."
6. ALWAYS remind users that regulatory decisions require human expert review.
7. NEVER claim that using this tool replaces professional regulatory consultation.

CITATION REQUIREMENTS (Sprint 5C) — for all substantive claims:
8. ALWAYS cite regulatory sources using the format: [Document, Section] (e.g., [SOR/98-282, s.32(2)(c)]).
9. When referencing gap findings, include the citation from the finding (e.g., "per [ISO 14971:2019, 7]").
10. NEVER fabricate citations — only cite sources that exist in the platform's regulatory reference registry.
11. For device classification, cite the specific Schedule 1 rule (e.g., [SOR/98-282, Schedule 1, Rule 11]).
12. When citing guidance documents, use format: [GUI-XXXX] (e.g., [GUI-0098]).

RESPONSE STRUCTURE:
- Lead with the most actionable information.
- Cite specific gap rule IDs (e.g., GAP-001) when referencing findings.
- Provide severity levels (critical, major, minor, info) for all findings.
- Include remediation suggestions where applicable.
- End with recommended next steps.

AI PROVENANCE:
Every analysis you produce is logged with: model identifier, timestamp, input hash, and output hash. This ensures auditability and traceability per regulatory requirements."""

HAZARD_ASSESSMENT_PROMPT: str = """You are analyzing hazard and risk management data for a medical device regulatory submission.

CONTEXT:
You have access to the device's regulatory twin data including:
- Identified hazards and their severity
- Linked harms (potential patient/user injuries)
- Risk controls and their verification status
- Trace links showing the hazard → harm → control → verification chain

TASK:
Analyze the hazard data provided and produce a structured assessment covering:
1. Completeness of hazard identification (are all foreseeable hazards captured?)
2. Risk chain integrity (does every hazard have linked harms, controls, and verification?)
3. Residual risk assessment (are controls adequate for each hazard severity?)
4. Gaps requiring attention (unmitigated hazards, unverified controls)

LANGUAGE RULES:
- NEVER say the risk management is "complete" or "compliant".
- Use "current assessment scope" and "based on configured expectations".
- Flag items as "identified for review" not "failing" or "non-compliant".
- Severity: use critical / major / minor / info classifications.

CITATION RULES:
- Cite ISO 14971:2019 sections for risk management requirements (e.g., [ISO 14971:2019, 6] for risk analysis).
- Reference SOR/98-282 s.10 for safety and effectiveness requirements.
- Include citations from gap findings when referencing them.

Provide your assessment in a structured format with clear sections."""

COVERAGE_GAP_PROMPT: str = """You are interpreting a gap analysis report for a medical device regulatory submission.

CONTEXT:
The gap analysis was produced by a deterministic rules engine (12 rules, GAP-001 through GAP-012) that evaluates regulatory readiness against configured expectations. The report includes findings with severity levels and remediation suggestions.

TASK:
Interpret the gap report for a regulatory affairs professional and:
1. Prioritize findings by regulatory impact (which gaps block submission?)
2. Group related findings (e.g., multiple evidence gaps may have a common root cause)
3. Suggest a remediation sequence (what to fix first for maximum impact)
4. Identify patterns (systemic issues vs. isolated findings)

LANGUAGE RULES:
- Reference findings by rule ID (e.g., "GAP-001: Unmitigated hazards").
- NEVER say the device "fails" a rule — say "finding identified under rule GAP-XXX".
- NEVER say "non-compliant" — say "finding identified for review".
- Use "based on the current rule set and available data" to qualify all conclusions.
- Distinguish between critical blockers and improvement opportunities.

CITATION RULES:
- Include the regulatory citation from each gap finding (e.g., "GAP-001 [ISO 14971:2019, 7]").
- When grouping findings, cite the common regulatory source.
- Reference guidance documents for remediation guidance (e.g., [GUI-0102] for clinical evidence).

Structure your interpretation with clear priorities and actionable next steps."""

EVIDENCE_REVIEW_PROMPT: str = """You are reviewing evidence items linked to a medical device regulatory submission.

CONTEXT:
You have access to evidence items including their:
- Type (clinical, pre-clinical, bench testing, literature, risk analysis, etc.)
- Strength rating (strong, moderate, weak, insufficient)
- Linked entities (which claims, controls, or tests they support)
- Attestation status (whether human review has been completed)

TASK:
Review the evidence portfolio and assess:
1. Evidence coverage — are all claims and controls supported by evidence?
2. Evidence strength — is the evidence strength appropriate for the device class?
3. Evidence gaps — what evidence is missing or insufficient?
4. Attestation status — which evidence items need human sign-off?

LANGUAGE RULES:
- NEVER say evidence "proves" anything — say "supports" or "provides indication".
- NEVER say the evidence portfolio is "sufficient" — say "assessment of evidence alignment based on configured expectations".
- Use "identified for strengthening" not "inadequate" or "failing".
- Qualify all assessments: "Based on available evidence items and configured rules..."

CITATION RULES:
- Cite SOR/98-282 s.32(4) for evidence requirements.
- Reference GUI-0102 for clinical evidence guidance.
- For Class III/IV devices, cite SOR/98-282 s.32(2)(c) for clinical data requirements.

Provide a structured assessment with clear priorities for evidence strengthening."""

READINESS_SUMMARY_PROMPT: str = """You are generating a human-readable readiness summary for a medical device regulatory submission.

CONTEXT:
You have a ReadinessReport containing:
- Overall readiness score (0.0 to 1.0)
- Category scores (coverage, completeness, consistency, evidence_strength)
- Gap findings with severity levels
- Critical blockers list

TASK:
Generate a clear, actionable summary that:
1. States the overall readiness assessment in regulatory-safe language
2. Highlights critical blockers that must be resolved
3. Provides category-by-category assessment
4. Recommends prioritized next steps
5. Notes the assessment scope and limitations

CRITICAL LANGUAGE RULES:
- NEVER use "ready", "compliant", "approved", "will pass", or "guaranteed".
- ALWAYS frame as: "Readiness assessment based on configured expectations."
- Score interpretation: 0.8+ = "favorable alignment", 0.5-0.8 = "partial alignment with findings requiring attention", <0.5 = "significant findings identified requiring remediation".
- ALWAYS include: "This assessment is generated by automated rules and requires human expert review before any regulatory decision."

CITATION RULES:
- Cite the primary regulatory sources for critical blockers.
- Reference specific SOR/98-282 sections for missing requirements.
- Include GUI document citations for remediation guidance.

Keep the summary concise but comprehensive. Use professional regulatory language throughout."""

DEVICE_ANALYSIS_PROMPT: str = """You are conducting a comprehensive regulatory analysis of a medical device.

CONTEXT:
You will use multiple tools in sequence to build a complete picture:
1. Device classification (Health Canada SOR/98-282)
2. Regulatory pathway determination (MDEL/MDL)
3. Trace link analysis (claim → evidence chain)
4. Gap analysis (12 deterministic rules)
5. Readiness assessment (scoring + summary)

TASK:
Conduct a systematic analysis and produce a unified report covering:
1. Device classification and regulatory pathway
2. Traceability status (completeness of regulatory chains)
3. Gap analysis findings (prioritized by severity)
4. Overall readiness assessment
5. Recommended next steps

WORKFLOW:
- Start with classification to establish device class and pathway
- Use trace chain and coverage tools to assess regulatory linkage
- Run gap analysis for systematic rule evaluation
- Generate readiness assessment for overall scoring
- Synthesize all findings into a coherent narrative

LANGUAGE RULES:
- All language rules from the master system prompt apply.
- NEVER claim the analysis is "comprehensive" or "complete" — say "based on current data and configured rules".
- Frame the entire output as an assessment, not a determination.
- Include: "This analysis requires review by a qualified regulatory professional."

CITATION RULES (carry forward from master prompt):
- Cite SOR/98-282 Schedule 1 rules for classification.
- Include citations from gap findings.
- Reference guidance documents for pathway information.
- Cite ISO standards for risk management findings.

Produce a structured report with clear sections and actionable recommendations."""


# ---------------------------------------------------------------------------
# Structured Output Schemas (Pydantic Models)
# ---------------------------------------------------------------------------


class CitedFinding(BaseModel):
    """A finding with regulatory citation (Sprint 5C).

    All substantive findings should include citations to regulatory sources.
    """

    rule_id: str = Field(..., description="Gap rule ID (e.g., GAP-001)")
    severity: str = Field(..., description="Finding severity (critical/major/minor/info)")
    description: str = Field(..., description="Finding description")
    regulation_ref: str | None = Field(default=None, description="Primary regulation reference ID")
    guidance_ref: str | None = Field(default=None, description="Guidance document reference ID")
    citation_text: str | None = Field(
        default=None, description="Formatted citation (e.g., [SOR/98-282, s.32(2)(c)])"
    )
    remediation: str | None = Field(default=None, description="Remediation suggestion")


class RegulatoryAnalysisResponse(BaseModel):
    """Standard structured response from any regulatory analysis task."""

    task_type: str = Field(..., description="Type of analysis performed")
    summary: str = Field(..., description="Human-readable summary of the analysis")
    findings: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of findings, each with rule_id, severity, description",
    )
    cited_findings: list[CitedFinding] = Field(
        default_factory=list,
        description="Findings with regulatory citations (Sprint 5C)",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Prioritized list of recommended actions",
    )
    primary_citations: list[str] = Field(
        default_factory=list,
        description="Primary regulatory citations used in this analysis (Sprint 5C)",
    )
    confidence_qualifier: str = Field(
        default="Based on available data and configured rules",
        description="Qualifier for the analysis confidence",
    )
    requires_human_review: bool = Field(
        default=True,
        description="Whether human expert review is required",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (timestamps, versions, etc.)",
    )

    @field_validator("summary")
    @classmethod
    def summary_must_be_regulatory_safe(cls, v: str) -> str:
        """Validate that the summary contains no forbidden words."""
        violations = check_forbidden_words(v)
        if violations:
            raise ValueError(f"Summary contains forbidden regulatory language: {violations}")
        return v


class HazardAssessmentResponse(BaseModel):
    """Structured response for hazard assessment analysis."""

    device_version_id: str = Field(..., description="Device version being assessed")
    total_hazards: int = Field(default=0, description="Total hazards evaluated")
    unmitigated_count: int = Field(default=0, description="Hazards without linked risk controls")
    incomplete_chains: int = Field(default=0, description="Hazard→harm→control chains with breaks")
    assessment_text: str = Field(..., description="Narrative assessment of hazard management")
    findings: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Specific findings from the assessment",
    )
    cited_findings: list[CitedFinding] = Field(
        default_factory=list,
        description="Findings with regulatory citations (Sprint 5C)",
    )
    primary_citations: list[str] = Field(
        default_factory=list,
        description="Primary regulatory citations (Sprint 5C)",
    )
    remediation_priorities: list[str] = Field(
        default_factory=list,
        description="Ordered list of remediation priorities",
    )

    @field_validator("assessment_text")
    @classmethod
    def assessment_must_be_safe(cls, v: str) -> str:
        """Validate regulatory-safe language in assessment text."""
        violations = check_forbidden_words(v)
        if violations:
            raise ValueError(f"Assessment contains forbidden language: {violations}")
        return v


class CoverageGapInterpretation(BaseModel):
    """Structured response for coverage gap report interpretation."""

    device_version_id: str = Field(..., description="Device version analyzed")
    total_findings: int = Field(default=0, description="Total findings in the gap report")
    critical_count: int = Field(default=0, description="Number of critical findings")
    major_count: int = Field(default=0, description="Number of major findings")
    interpretation: str = Field(..., description="Narrative interpretation of the gap report")
    cited_findings: list[CitedFinding] = Field(
        default_factory=list,
        description="Findings with regulatory citations (Sprint 5C)",
    )
    priority_groups: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Findings grouped by priority/theme",
    )
    remediation_sequence: list[str] = Field(
        default_factory=list,
        description="Recommended order of remediation",
    )
    systemic_patterns: list[str] = Field(
        default_factory=list,
        description="Identified systemic issues across findings",
    )
    primary_citations: list[str] = Field(
        default_factory=list,
        description="Primary regulatory citations (Sprint 5C)",
    )

    @field_validator("interpretation")
    @classmethod
    def interpretation_must_be_safe(cls, v: str) -> str:
        """Validate regulatory-safe language."""
        violations = check_forbidden_words(v)
        if violations:
            raise ValueError(f"Interpretation contains forbidden language: {violations}")
        return v


class EvidenceReviewResponse(BaseModel):
    """Structured response for evidence portfolio review."""

    device_version_id: str = Field(..., description="Device version analyzed")
    total_evidence_items: int = Field(default=0, description="Total evidence items reviewed")
    strong_count: int = Field(default=0, description="Evidence items rated strong")
    weak_count: int = Field(default=0, description="Evidence items rated weak or insufficient")
    cited_findings: list[CitedFinding] = Field(
        default_factory=list,
        description="Findings with regulatory citations (Sprint 5C)",
    )
    primary_citations: list[str] = Field(
        default_factory=list,
        description="Primary regulatory citations (Sprint 5C)",
    )
    unattested_count: int = Field(default=0, description="Evidence items without human attestation")
    assessment_text: str = Field(..., description="Narrative assessment of evidence portfolio")
    coverage_gaps: list[str] = Field(
        default_factory=list,
        description="Claims or controls without supporting evidence",
    )
    strengthening_priorities: list[str] = Field(
        default_factory=list,
        description="Evidence items recommended for strengthening",
    )

    @field_validator("assessment_text")
    @classmethod
    def assessment_must_be_safe(cls, v: str) -> str:
        """Validate regulatory-safe language."""
        violations = check_forbidden_words(v)
        if violations:
            raise ValueError(f"Assessment contains forbidden language: {violations}")
        return v


class ReadinessSummaryResponse(BaseModel):
    """Structured response for readiness summary generation."""

    device_version_id: str = Field(..., description="Device version assessed")
    overall_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall readiness score (0.0-1.0)"
    )
    score_interpretation: str = Field(..., description="Human-readable score interpretation")
    category_assessments: dict[str, str] = Field(
        default_factory=dict,
        description="Per-category narrative assessments",
    )
    critical_blockers: list[str] = Field(
        default_factory=list,
        description="Critical items that must be resolved",
    )
    cited_blockers: list[CitedFinding] = Field(
        default_factory=list,
        description="Critical blockers with regulatory citations (Sprint 5C)",
    )
    recommended_actions: list[str] = Field(
        default_factory=list,
        description="Prioritized actions for the team",
    )
    primary_citations: list[str] = Field(
        default_factory=list,
        description="Primary regulatory citations (Sprint 5C)",
    )
    summary_text: str = Field(..., description="Full narrative summary")
    disclaimer: str = Field(
        default=(
            "This assessment is generated by automated rules and requires "
            "human expert review before any regulatory decision."
        ),
        description="Required disclaimer for all readiness outputs",
    )

    @field_validator("summary_text")
    @classmethod
    def summary_must_be_safe(cls, v: str) -> str:
        """Validate regulatory-safe language."""
        violations = check_forbidden_words(v)
        if violations:
            raise ValueError(f"Summary contains forbidden language: {violations}")
        return v

    @field_validator("score_interpretation")
    @classmethod
    def interpretation_must_be_safe(cls, v: str) -> str:
        """Validate regulatory-safe language in score interpretation."""
        violations = check_forbidden_words(v)
        if violations:
            raise ValueError(f"Score interpretation contains forbidden language: {violations}")
        return v


class AIProvenance(BaseModel):
    """
    AI provenance record for audit trail.

    Every AI output MUST have a provenance record logged to ai_runs
    BEFORE the output is displayed to the user.
    """

    model_id: str = Field(
        ..., description="LLM model identifier (e.g., claude-3-5-sonnet-20241022)"
    )
    task_type: str = Field(..., description="Type of task performed")
    input_hash: str = Field(..., description="SHA-256 hash of the input prompt")
    output_hash: str = Field(..., description="SHA-256 hash of the generated output")
    prompt_version: str = Field(default="4B.1", description="Version of the prompt template used")
    timestamp_utc: str = Field(..., description="UTC timestamp of generation (ISO 8601)")
    device_version_id: str | None = Field(
        default=None, description="Device version ID if applicable"
    )
    organization_id: str | None = Field(default=None, description="Organization ID for scoping")
    temperature: float = Field(default=0.1, description="LLM temperature setting")
    token_count: int | None = Field(default=None, description="Total tokens consumed if available")
    status: Literal["success", "error", "filtered"] = Field(
        default="success", description="Outcome of the AI generation"
    )
    error_message: str | None = Field(
        default=None, description="Error details if status is 'error'"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (e.g., tools invoked, chain steps)",
    )


# ---------------------------------------------------------------------------
# Language Safety Functions
# ---------------------------------------------------------------------------


def check_forbidden_words(text: str) -> list[str]:
    """
    Check text for forbidden regulatory language.

    Args:
        text: The text to check.

    Returns:
        List of forbidden words/phrases found. Empty list if safe.
    """
    if not text:
        return []

    text_lower = text.lower()
    violations: list[str] = []

    for word in FORBIDDEN_WORDS:
        if word.lower() in text_lower:
            violations.append(word)

    return violations


def sanitize_ai_output(text: str) -> str:
    """
    Replace forbidden language with approved alternatives.

    Performs case-insensitive replacement while attempting to
    preserve the original casing style. Falls back to lowercase
    replacement if the original case cannot be matched.

    Args:
        text: The AI-generated text to sanitize.

    Returns:
        Sanitized text with all forbidden phrases replaced.
    """
    if not text:
        return text

    sanitized = text

    # Sort replacements by length (longest first) to avoid partial matches
    sorted_replacements = sorted(
        APPROVED_REPLACEMENTS.items(), key=lambda x: len(x[0]), reverse=True
    )

    for forbidden, replacement in sorted_replacements:
        # Case-insensitive search and replace
        lower_text = sanitized.lower()
        idx = lower_text.find(forbidden.lower())
        while idx != -1:
            # Replace the found instance
            sanitized = sanitized[:idx] + replacement + sanitized[idx + len(forbidden) :]
            # Search again from after the replacement
            lower_text = sanitized.lower()
            idx = lower_text.find(forbidden.lower(), idx + len(replacement))

    return sanitized


def validate_regulatory_language(text: str) -> dict[str, Any]:
    """
    Validate text for regulatory-safe language and return a detailed report.

    Args:
        text: The text to validate.

    Returns:
        Dict with 'is_safe', 'violations', and 'sanitized_text' keys.
    """
    violations = check_forbidden_words(text)
    return {
        "is_safe": len(violations) == 0,
        "violations": violations,
        "violation_count": len(violations),
        "sanitized_text": sanitize_ai_output(text) if violations else text,
        "original_text": text,
    }


# ---------------------------------------------------------------------------
# Prompt Router & Builders
# ---------------------------------------------------------------------------

# Map of task type → system prompt
_PROMPT_MAP: dict[str, str] = {
    "regulatory_agent": REGULATORY_AGENT_SYSTEM_PROMPT,
    "hazard_assessment": HAZARD_ASSESSMENT_PROMPT,
    "coverage_gap": COVERAGE_GAP_PROMPT,
    "evidence_review": EVIDENCE_REVIEW_PROMPT,
    "readiness_summary": READINESS_SUMMARY_PROMPT,
    "device_analysis": DEVICE_ANALYSIS_PROMPT,
}


def get_prompt_for_task(task_type: str) -> str:
    """
    Get the system prompt for a given task type.

    Args:
        task_type: One of the valid TASK_TYPES.

    Returns:
        The system prompt string.

    Raises:
        ValueError: If task_type is not recognized.
    """
    prompt = _PROMPT_MAP.get(task_type)
    if prompt is None:
        valid_types = list(_PROMPT_MAP.keys())
        raise ValueError(f"Unknown task type '{task_type}'. Valid types: {valid_types}")
    return prompt


def get_available_task_types() -> list[str]:
    """Return all available task types."""
    return list(_PROMPT_MAP.keys())


def build_contextualized_prompt(
    task_type: str,
    device_context: dict[str, Any] | None = None,
    additional_instructions: str | None = None,
) -> str:
    """
    Build a system prompt enriched with device-specific context.

    Args:
        task_type: The analysis task type.
        device_context: Optional device-specific data to inject.
        additional_instructions: Optional extra instructions to append.

    Returns:
        Complete system prompt string with context.

    Raises:
        ValueError: If task_type is not recognized.
    """
    base_prompt = get_prompt_for_task(task_type)

    parts = [base_prompt]

    if device_context:
        context_section = "\n\nDEVICE CONTEXT:\n"
        for key, value in device_context.items():
            context_section += f"- {key}: {value}\n"
        parts.append(context_section)

    if additional_instructions:
        parts.append(f"\nADDITIONAL INSTRUCTIONS:\n{additional_instructions}")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# AI Provenance Helpers
# ---------------------------------------------------------------------------


def compute_hash(text: str) -> str:
    """
    Compute SHA-256 hash of text for provenance tracking.

    Args:
        text: The text to hash.

    Returns:
        Hex-encoded SHA-256 hash string.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def create_ai_provenance(
    model_id: str,
    task_type: str,
    input_text: str,
    output_text: str,
    device_version_id: str | None = None,
    organization_id: str | None = None,
    temperature: float = 0.1,
    token_count: int | None = None,
    status: Literal["success", "error", "filtered"] = "success",
    error_message: str | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> AIProvenance:
    """
    Create an AI provenance record for audit logging.

    This MUST be called for every AI output BEFORE the output
    is displayed to the user.

    Args:
        model_id: LLM model identifier.
        task_type: Type of analysis task.
        input_text: The full input prompt sent to the LLM.
        output_text: The full output received from the LLM.
        device_version_id: Optional device version scope.
        organization_id: Optional organization scope.
        temperature: LLM temperature setting.
        token_count: Total tokens consumed if available.
        status: Outcome of the generation.
        error_message: Error details if status is 'error'.
        extra_metadata: Additional context to store.

    Returns:
        AIProvenance Pydantic model ready for persistence.
    """
    return AIProvenance(
        model_id=model_id,
        task_type=task_type,
        input_hash=compute_hash(input_text),
        output_hash=compute_hash(output_text),
        timestamp_utc=datetime.now(UTC).isoformat(),
        device_version_id=device_version_id,
        organization_id=organization_id,
        temperature=temperature,
        token_count=token_count,
        status=status,
        error_message=error_message,
        metadata=extra_metadata or {},
    )


def provenance_to_db_dict(provenance: AIProvenance) -> dict[str, Any]:
    """
    Convert an AIProvenance record to a dict suitable for ai_runs table insertion.

    Args:
        provenance: The AIProvenance record.

    Returns:
        Dict ready for database insertion (excludes id, created_at).
    """
    data = provenance.model_dump()
    # Convert metadata dict to JSON-compatible format
    # (Pydantic already handles this, but be explicit)
    return data


# ---------------------------------------------------------------------------
# Score Interpretation (consistent with readiness.py)
# ---------------------------------------------------------------------------


def interpret_readiness_score(score: float) -> str:
    """
    Interpret a readiness score using regulatory-safe language.

    Consistent with the readiness.py scoring system.

    Args:
        score: Readiness score between 0.0 and 1.0.

    Returns:
        Regulatory-safe interpretation string.
    """
    if score >= 0.8:
        return (
            "Assessment indicates favorable alignment with configured "
            "expectations. Review identified findings before proceeding."
        )
    elif score >= 0.5:
        return (
            "Assessment indicates partial alignment with configured "
            "expectations. Multiple findings require attention before "
            "advancing toward submission activities."
        )
    else:
        return (
            "Assessment indicates significant findings requiring "
            "remediation. Substantial work is identified before the "
            "device version aligns with configured expectations."
        )
