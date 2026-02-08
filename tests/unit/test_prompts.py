"""
Tests for src/agents/prompts.py — Sprint 4B.

Covers:
- Prompt construction and routing
- Regulatory-safe language enforcement (forbidden words)
- Language sanitization (replacement of forbidden words)
- Structured output schema validation
- AI provenance record creation
- Score interpretation
- Edge cases and error handling
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.agents.prompts import (
    APPROVED_REPLACEMENTS,
    COVERAGE_GAP_PROMPT,
    DEVICE_ANALYSIS_PROMPT,
    EVIDENCE_REVIEW_PROMPT,
    FORBIDDEN_WORDS,
    HAZARD_ASSESSMENT_PROMPT,
    READINESS_SUMMARY_PROMPT,
    REGULATORY_AGENT_SYSTEM_PROMPT,
    AIProvenance,
    CoverageGapInterpretation,
    EvidenceReviewResponse,
    HazardAssessmentResponse,
    ReadinessSummaryResponse,
    RegulatoryAnalysisResponse,
    build_contextualized_prompt,
    check_forbidden_words,
    compute_hash,
    create_ai_provenance,
    get_available_task_types,
    get_prompt_for_task,
    interpret_readiness_score,
    provenance_to_db_dict,
    sanitize_ai_output,
    validate_regulatory_language,
)

# ===================================================================
# Test: Forbidden Words List
# ===================================================================


class TestForbiddenWords:
    """Tests for the FORBIDDEN_WORDS constant."""

    def test_forbidden_words_is_nonempty(self) -> None:
        """FORBIDDEN_WORDS must contain entries."""
        assert len(FORBIDDEN_WORDS) > 0

    def test_forbidden_words_contains_core_terms(self) -> None:
        """Core forbidden terms must be present."""
        core_terms = [
            "compliant",
            "ready for submission",
            "will pass",
            "guaranteed",
            "approved",
        ]
        for term in core_terms:
            assert term in FORBIDDEN_WORDS, f"Missing core forbidden term: {term}"

    def test_approved_replacements_cover_all_forbidden_words(self) -> None:
        """Every forbidden word must have an approved replacement."""
        for word in FORBIDDEN_WORDS:
            assert (
                word in APPROVED_REPLACEMENTS
            ), f"No approved replacement for forbidden word: '{word}'"

    def test_replacements_do_not_contain_forbidden_words(self) -> None:
        """Approved replacements must not themselves contain forbidden words."""
        for forbidden, replacement in APPROVED_REPLACEMENTS.items():
            violations = check_forbidden_words(replacement)
            assert (
                violations == []
            ), f"Replacement for '{forbidden}' contains forbidden words: {violations}"


# ===================================================================
# Test: Language Safety — check_forbidden_words
# ===================================================================


class TestCheckForbiddenWords:
    """Tests for check_forbidden_words function."""

    def test_clean_text_returns_empty(self) -> None:
        """Clean text should produce no violations."""
        result = check_forbidden_words("Readiness assessment based on configured expectations.")
        assert result == []

    def test_detects_single_forbidden_word(self) -> None:
        """Should detect a single forbidden word."""
        result = check_forbidden_words("The device is compliant with standards.")
        assert "compliant" in result

    def test_detects_multiple_forbidden_words(self) -> None:
        """Should detect multiple forbidden words."""
        result = check_forbidden_words("The device is compliant and ready for submission.")
        assert "compliant" in result
        assert "ready for submission" in result

    def test_case_insensitive_detection(self) -> None:
        """Detection should be case-insensitive."""
        result = check_forbidden_words("The device is COMPLIANT.")
        assert "compliant" in result

    def test_empty_text_returns_empty(self) -> None:
        """Empty text should produce no violations."""
        assert check_forbidden_words("") == []

    def test_none_safe_empty_text(self) -> None:
        """None-like empty string returns no violations."""
        assert check_forbidden_words("") == []

    def test_detects_phrase_forbidden_words(self) -> None:
        """Should detect multi-word forbidden phrases."""
        result = check_forbidden_words("This will pass regulatory review.")
        assert "will pass" in result

    def test_detects_meets_all_requirements(self) -> None:
        """Should detect 'meets all requirements'."""
        result = check_forbidden_words("The submission meets all requirements for approval.")
        assert "meets all requirements" in result


# ===================================================================
# Test: Language Sanitization — sanitize_ai_output
# ===================================================================


class TestSanitizeAiOutput:
    """Tests for sanitize_ai_output function."""

    def test_replaces_compliant(self) -> None:
        """Should replace 'compliant' with approved alternative."""
        result = sanitize_ai_output("The device is compliant.")
        assert "compliant" not in result.lower()
        assert "aligned with configured expectations" in result

    def test_replaces_ready_for_submission(self) -> None:
        """Should replace 'ready for submission'."""
        result = sanitize_ai_output("The device is ready for submission.")
        assert "ready for submission" not in result.lower()
        assert "readiness assessment based on configured expectations" in result

    def test_replaces_will_pass(self) -> None:
        """Should replace 'will pass'."""
        result = sanitize_ai_output("This will pass the review.")
        assert "will pass" not in result.lower()
        assert "assessment indicates favorable alignment" in result

    def test_handles_empty_text(self) -> None:
        """Empty text should pass through unchanged."""
        assert sanitize_ai_output("") == ""

    def test_clean_text_unchanged(self) -> None:
        """Text without forbidden words should pass through unchanged."""
        clean = "Readiness assessment based on configured expectations."
        assert sanitize_ai_output(clean) == clean

    def test_replaces_multiple_forbidden_words(self) -> None:
        """Should replace multiple forbidden words in one pass."""
        text = "The device is compliant and guaranteed to pass."
        result = sanitize_ai_output(text)
        assert "compliant" not in result.lower()
        assert "guaranteed" not in result.lower()

    def test_result_is_clean_after_sanitization(self) -> None:
        """After sanitization, no forbidden words should remain."""
        text = "Compliant, approved, and meets all requirements."
        result = sanitize_ai_output(text)
        violations = check_forbidden_words(result)
        assert violations == [], f"Sanitized text still has violations: {violations}"


# ===================================================================
# Test: validate_regulatory_language
# ===================================================================


class TestValidateRegulatoryLanguage:
    """Tests for the validate_regulatory_language function."""

    def test_safe_text_returns_is_safe_true(self) -> None:
        """Safe text should return is_safe=True."""
        result = validate_regulatory_language("Assessment indicates alignment with expectations.")
        assert result["is_safe"] is True
        assert result["violations"] == []
        assert result["violation_count"] == 0

    def test_unsafe_text_returns_is_safe_false(self) -> None:
        """Unsafe text should return is_safe=False with violations."""
        result = validate_regulatory_language("The device is compliant.")
        assert result["is_safe"] is False
        assert "compliant" in result["violations"]
        assert result["violation_count"] > 0

    def test_sanitized_text_provided_when_unsafe(self) -> None:
        """When unsafe, sanitized_text should have replacements applied."""
        result = validate_regulatory_language("The device is compliant.")
        assert "compliant" not in result["sanitized_text"].lower()

    def test_original_text_preserved(self) -> None:
        """Original text should always be preserved."""
        original = "The device is compliant."
        result = validate_regulatory_language(original)
        assert result["original_text"] == original


# ===================================================================
# Test: Prompt Router
# ===================================================================


class TestPromptRouter:
    """Tests for prompt routing functions."""

    def test_get_prompt_for_all_valid_types(self) -> None:
        """All valid task types should return a non-empty prompt."""
        for task_type in get_available_task_types():
            prompt = get_prompt_for_task(task_type)
            assert isinstance(prompt, str)
            assert len(prompt) > 100, f"Prompt for {task_type} is too short"

    def test_get_prompt_invalid_type_raises_value_error(self) -> None:
        """Invalid task type should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown task type"):
            get_prompt_for_task("nonexistent_task")

    def test_available_task_types_returns_all(self) -> None:
        """Should return all 6 task types."""
        types = get_available_task_types()
        assert len(types) == 6
        expected = {
            "regulatory_agent",
            "hazard_assessment",
            "coverage_gap",
            "evidence_review",
            "readiness_summary",
            "device_analysis",
        }
        assert set(types) == expected

    def test_regulatory_agent_prompt_has_language_rules(self) -> None:
        """Master system prompt must contain language rules."""
        prompt = get_prompt_for_task("regulatory_agent")
        assert "NEVER" in prompt
        assert "compliant" in prompt.lower()
        assert "readiness assessment" in prompt.lower()

    def test_all_prompts_reference_language_safety(self) -> None:
        """Every prompt should include language safety rules."""
        for task_type in get_available_task_types():
            prompt = get_prompt_for_task(task_type)
            assert (
                "LANGUAGE RULES" in prompt or "CRITICAL LANGUAGE RULES" in prompt
            ), f"Prompt '{task_type}' missing language rules section"


# ===================================================================
# Test: build_contextualized_prompt
# ===================================================================


class TestBuildContextualizedPrompt:
    """Tests for contextualized prompt building."""

    def test_basic_prompt_without_context(self) -> None:
        """Should return base prompt without context."""
        result = build_contextualized_prompt("hazard_assessment")
        assert HAZARD_ASSESSMENT_PROMPT in result

    def test_adds_device_context(self) -> None:
        """Should append device context section."""
        ctx = {"device_class": "III", "device_name": "CardioMonitor Pro"}
        result = build_contextualized_prompt("hazard_assessment", device_context=ctx)
        assert "DEVICE CONTEXT" in result
        assert "device_class: III" in result
        assert "CardioMonitor Pro" in result

    def test_adds_additional_instructions(self) -> None:
        """Should append additional instructions."""
        result = build_contextualized_prompt(
            "coverage_gap",
            additional_instructions="Focus on GAP-001 and GAP-010.",
        )
        assert "ADDITIONAL INSTRUCTIONS" in result
        assert "GAP-001" in result

    def test_invalid_task_type_raises(self) -> None:
        """Invalid task type should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown task type"):
            build_contextualized_prompt("invalid_type")

    def test_both_context_and_instructions(self) -> None:
        """Should handle both context and instructions together."""
        result = build_contextualized_prompt(
            "evidence_review",
            device_context={"device_class": "IV"},
            additional_instructions="Prioritize clinical evidence.",
        )
        assert "DEVICE CONTEXT" in result
        assert "ADDITIONAL INSTRUCTIONS" in result
        assert "device_class: IV" in result
        assert "Prioritize clinical evidence" in result


# ===================================================================
# Test: Structured Output Schemas
# ===================================================================


class TestRegulatoryAnalysisResponse:
    """Tests for the RegulatoryAnalysisResponse schema."""

    def test_valid_response(self) -> None:
        """Should accept valid regulatory-safe response."""
        resp = RegulatoryAnalysisResponse(
            task_type="hazard_assessment",
            summary="Assessment indicates partial alignment with expectations.",
        )
        assert resp.task_type == "hazard_assessment"
        assert resp.requires_human_review is True

    def test_rejects_forbidden_summary(self) -> None:
        """Should reject summary containing forbidden words."""
        with pytest.raises(ValidationError, match="forbidden regulatory language"):
            RegulatoryAnalysisResponse(
                task_type="test",
                summary="The device is compliant with all standards.",
            )

    def test_defaults_populated(self) -> None:
        """Default fields should be populated correctly."""
        resp = RegulatoryAnalysisResponse(
            task_type="test",
            summary="Assessment based on configured expectations.",
        )
        assert resp.findings == []
        assert resp.recommendations == []
        assert resp.requires_human_review is True
        assert "Based on available data" in resp.confidence_qualifier


class TestHazardAssessmentResponse:
    """Tests for HazardAssessmentResponse schema."""

    def test_valid_hazard_response(self) -> None:
        """Should accept valid hazard assessment."""
        resp = HazardAssessmentResponse(
            device_version_id="dv-123",
            total_hazards=5,
            unmitigated_count=1,
            assessment_text="Assessment identifies one hazard requiring additional controls.",
        )
        assert resp.total_hazards == 5
        assert resp.unmitigated_count == 1

    def test_rejects_forbidden_assessment_text(self) -> None:
        """Should reject assessment containing forbidden words."""
        with pytest.raises(ValidationError, match="forbidden language"):
            HazardAssessmentResponse(
                device_version_id="dv-123",
                assessment_text="The risk management is fully compliant.",
            )


class TestCoverageGapInterpretation:
    """Tests for CoverageGapInterpretation schema."""

    def test_valid_gap_interpretation(self) -> None:
        """Should accept valid gap interpretation."""
        resp = CoverageGapInterpretation(
            device_version_id="dv-456",
            total_findings=12,
            critical_count=3,
            interpretation="Gap analysis identified 3 critical findings for review.",
        )
        assert resp.total_findings == 12

    def test_rejects_forbidden_interpretation(self) -> None:
        """Should reject interpretation with forbidden language."""
        with pytest.raises(ValidationError, match="forbidden language"):
            CoverageGapInterpretation(
                device_version_id="dv-456",
                interpretation="The device meets all requirements.",
            )


class TestEvidenceReviewResponse:
    """Tests for EvidenceReviewResponse schema."""

    def test_valid_evidence_review(self) -> None:
        """Should accept valid evidence review."""
        resp = EvidenceReviewResponse(
            device_version_id="dv-789",
            total_evidence_items=20,
            strong_count=15,
            weak_count=3,
            assessment_text="Evidence portfolio shows mixed strength across categories.",
        )
        assert resp.total_evidence_items == 20

    def test_rejects_forbidden_assessment(self) -> None:
        """Should reject assessment with forbidden language."""
        with pytest.raises(ValidationError, match="forbidden language"):
            EvidenceReviewResponse(
                device_version_id="dv-789",
                assessment_text="Evidence ensures compliance with all standards.",
            )


class TestReadinessSummaryResponse:
    """Tests for ReadinessSummaryResponse schema."""

    def test_valid_readiness_summary(self) -> None:
        """Should accept valid readiness summary."""
        resp = ReadinessSummaryResponse(
            device_version_id="dv-101",
            overall_score=0.75,
            score_interpretation="Partial alignment with configured expectations.",
            summary_text="Readiness assessment based on configured expectations identifies areas for improvement.",
        )
        assert resp.overall_score == 0.75
        assert "human expert review" in resp.disclaimer

    def test_rejects_forbidden_summary_text(self) -> None:
        """Should reject summary with forbidden language."""
        with pytest.raises(ValidationError, match="forbidden language"):
            ReadinessSummaryResponse(
                device_version_id="dv-101",
                overall_score=0.9,
                score_interpretation="Assessment indicates favorable alignment.",
                summary_text="The device is ready for submission.",
            )

    def test_rejects_forbidden_score_interpretation(self) -> None:
        """Should reject score_interpretation with forbidden language."""
        with pytest.raises(ValidationError, match="forbidden language"):
            ReadinessSummaryResponse(
                device_version_id="dv-101",
                overall_score=0.9,
                score_interpretation="The device is compliant.",
                summary_text="Assessment based on configured expectations.",
            )

    def test_score_bounds_enforced(self) -> None:
        """Score must be between 0.0 and 1.0."""
        with pytest.raises(ValidationError):
            ReadinessSummaryResponse(
                device_version_id="dv-101",
                overall_score=1.5,
                score_interpretation="Assessment indicates alignment.",
                summary_text="Assessment based on configured expectations.",
            )

    def test_default_disclaimer_present(self) -> None:
        """Default disclaimer must be present."""
        resp = ReadinessSummaryResponse(
            device_version_id="dv-101",
            overall_score=0.5,
            score_interpretation="Partial alignment identified.",
            summary_text="Assessment based on configured expectations.",
        )
        assert "automated rules" in resp.disclaimer
        assert "human expert review" in resp.disclaimer


# ===================================================================
# Test: AI Provenance
# ===================================================================


class TestAIProvenance:
    """Tests for AI provenance record creation."""

    def test_compute_hash_deterministic(self) -> None:
        """Same input should produce the same hash."""
        h1 = compute_hash("test input")
        h2 = compute_hash("test input")
        assert h1 == h2

    def test_compute_hash_differs_for_different_input(self) -> None:
        """Different inputs should produce different hashes."""
        h1 = compute_hash("input A")
        h2 = compute_hash("input B")
        assert h1 != h2

    def test_compute_hash_is_sha256(self) -> None:
        """Hash should be valid SHA-256 (64 hex chars)."""
        h = compute_hash("test")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_create_ai_provenance_basic(self) -> None:
        """Should create a valid provenance record."""
        prov = create_ai_provenance(
            model_id="claude-3-5-sonnet-20241022",
            task_type="hazard_assessment",
            input_text="Analyze hazards for device X",
            output_text="Assessment identifies 3 findings.",
        )
        assert prov.model_id == "claude-3-5-sonnet-20241022"
        assert prov.task_type == "hazard_assessment"
        assert len(prov.input_hash) == 64
        assert len(prov.output_hash) == 64
        assert prov.status == "success"
        assert prov.prompt_version == "4B.1"

    def test_create_ai_provenance_with_all_fields(self) -> None:
        """Should handle all optional fields."""
        prov = create_ai_provenance(
            model_id="gpt-4",
            task_type="coverage_gap",
            input_text="Analyze gaps",
            output_text="3 critical gaps found.",
            device_version_id="dv-123",
            organization_id="org-456",
            temperature=0.2,
            token_count=500,
            status="success",
            extra_metadata={"tools_invoked": ["run_gap_analysis"]},
        )
        assert prov.device_version_id == "dv-123"
        assert prov.organization_id == "org-456"
        assert prov.temperature == 0.2
        assert prov.token_count == 500
        assert prov.metadata == {"tools_invoked": ["run_gap_analysis"]}

    def test_create_ai_provenance_error_status(self) -> None:
        """Should handle error status with error message."""
        prov = create_ai_provenance(
            model_id="claude-3-5-sonnet-20241022",
            task_type="test",
            input_text="input",
            output_text="",
            status="error",
            error_message="LLM timeout after 30s",
        )
        assert prov.status == "error"
        assert prov.error_message == "LLM timeout after 30s"

    def test_provenance_timestamp_is_utc(self) -> None:
        """Timestamp should be in UTC ISO format."""
        prov = create_ai_provenance(
            model_id="test",
            task_type="test",
            input_text="in",
            output_text="out",
        )
        # Should be parseable as ISO datetime
        ts = datetime.fromisoformat(prov.timestamp_utc)
        assert ts.tzinfo is not None  # Must be timezone-aware

    def test_provenance_to_db_dict(self) -> None:
        """Should convert provenance to a flat dict for DB insertion."""
        prov = create_ai_provenance(
            model_id="claude-3-5-sonnet-20241022",
            task_type="hazard_assessment",
            input_text="test",
            output_text="result",
        )
        db_dict = provenance_to_db_dict(prov)
        assert isinstance(db_dict, dict)
        assert "model_id" in db_dict
        assert "input_hash" in db_dict
        assert "output_hash" in db_dict
        assert "timestamp_utc" in db_dict
        assert "id" not in db_dict  # Should not include auto-generated fields

    def test_provenance_invalid_status_rejected(self) -> None:
        """Invalid status should be rejected by Pydantic."""
        with pytest.raises(ValidationError):
            AIProvenance(
                model_id="test",
                task_type="test",
                input_hash="abc",
                output_hash="def",
                timestamp_utc="2026-01-01T00:00:00Z",
                status="unknown_status",  # type: ignore[arg-type]
            )


# ===================================================================
# Test: Score Interpretation
# ===================================================================


class TestInterpretReadinessScore:
    """Tests for readiness score interpretation."""

    def test_high_score_favorable(self) -> None:
        """Score >= 0.8 should indicate favorable alignment."""
        result = interpret_readiness_score(0.85)
        assert "favorable alignment" in result
        # Must be regulatory-safe
        assert check_forbidden_words(result) == []

    def test_medium_score_partial(self) -> None:
        """Score 0.5-0.8 should indicate partial alignment."""
        result = interpret_readiness_score(0.65)
        assert "partial alignment" in result
        assert check_forbidden_words(result) == []

    def test_low_score_significant_findings(self) -> None:
        """Score < 0.5 should indicate significant findings."""
        result = interpret_readiness_score(0.3)
        assert "significant findings" in result
        assert check_forbidden_words(result) == []

    def test_boundary_08(self) -> None:
        """Score exactly 0.8 should be favorable."""
        result = interpret_readiness_score(0.8)
        assert "favorable alignment" in result

    def test_boundary_05(self) -> None:
        """Score exactly 0.5 should be partial."""
        result = interpret_readiness_score(0.5)
        assert "partial alignment" in result

    def test_all_interpretations_are_regulatory_safe(self) -> None:
        """Every possible interpretation must be regulatory-safe."""
        scores = [0.0, 0.1, 0.25, 0.49, 0.5, 0.65, 0.79, 0.8, 0.9, 1.0]
        for score in scores:
            result = interpret_readiness_score(score)
            violations = check_forbidden_words(result)
            assert violations == [], f"Score {score} interpretation has violations: {violations}"


# ===================================================================
# Test: System Prompt Content Validation
# ===================================================================


class TestSystemPromptContent:
    """Tests for system prompt content integrity."""

    def test_master_prompt_no_forbidden_words(self) -> None:
        """Master system prompt itself should not use forbidden words
        in a way that could be copied into output."""
        # The prompt *mentions* forbidden words as instructions,
        # but the actual instructional text should be safe.
        # We verify the prompt references them as rules to follow.
        prompt = REGULATORY_AGENT_SYSTEM_PROMPT
        assert 'NEVER say "compliant"' in prompt or "NEVER" in prompt

    def test_all_prompts_include_never_instruction(self) -> None:
        """Every analysis prompt must include a NEVER instruction."""
        prompts = [
            HAZARD_ASSESSMENT_PROMPT,
            COVERAGE_GAP_PROMPT,
            EVIDENCE_REVIEW_PROMPT,
            READINESS_SUMMARY_PROMPT,
            DEVICE_ANALYSIS_PROMPT,
        ]
        for prompt in prompts:
            assert "NEVER" in prompt, f"Prompt missing NEVER instruction: {prompt[:50]}"

    def test_master_prompt_mentions_ai_provenance(self) -> None:
        """Master prompt must reference AI provenance logging."""
        assert "AI PROVENANCE" in REGULATORY_AGENT_SYSTEM_PROMPT
        assert (
            "ai_runs" in REGULATORY_AGENT_SYSTEM_PROMPT.lower()
            or "logged" in REGULATORY_AGENT_SYSTEM_PROMPT.lower()
        )

    def test_master_prompt_mentions_human_review(self) -> None:
        """Master prompt must require human expert review."""
        prompt = REGULATORY_AGENT_SYSTEM_PROMPT
        assert (
            "human expert review" in prompt.lower() or "regulatory professional" in prompt.lower()
        )

    def test_device_analysis_prompt_has_workflow(self) -> None:
        """Device analysis prompt must include workflow steps."""
        assert "WORKFLOW" in DEVICE_ANALYSIS_PROMPT
        assert "classification" in DEVICE_ANALYSIS_PROMPT.lower()
        assert "gap analysis" in DEVICE_ANALYSIS_PROMPT.lower()
        assert "readiness" in DEVICE_ANALYSIS_PROMPT.lower()
