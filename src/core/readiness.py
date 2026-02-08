"""
Readiness Assessment — Sprint 3b.

Aggregates gap findings into a structured readiness assessment with
scoring dimensions. Consumes GapReport from GapDetectionEngine.
Pure deterministic logic — no AI dependency.

REGULATORY LANGUAGE SAFETY:
    This module NEVER uses the words "compliant", "ready", "certified",
    "approved", "will pass", or "guaranteed" in any output. All language
    is framed as "assessment based on configured expectations."

Usage:
    assessment = get_readiness_assessment()
    report = assessment.assess("device-version-uuid")
    print(report.overall_readiness_score)
    print(report.summary)
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from src.core.gap_engine import (
    GapDetectionEngine,
    GapFinding,
    GapReport,
    get_gap_engine,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)

# =============================================================================
# Constants
# =============================================================================

# Mountain Time zone for all timestamps
_MST = ZoneInfo("America/Edmonton")

# Severity weights for scoring (higher = worse)
# A single critical finding has maximum impact on the score
SEVERITY_WEIGHTS: dict[str, float] = {
    "critical": 1.0,
    "major": 0.6,
    "minor": 0.2,
    "info": 0.0,
}

# Categories used in gap detection — scores computed per category
GAP_CATEGORIES: list[str] = [
    "coverage",
    "completeness",
    "consistency",
    "evidence_strength",
]

# Penalty per finding, scaled by severity weight.
# With a base penalty of 0.15, it takes ~7 major findings to bring
# a category score to 0.0 (7 * 0.6 * 0.15 = 0.63 → clamp).
# A single critical finding applies 0.15 * 1.0 = 0.15 penalty.
BASE_PENALTY_PER_FINDING: float = 0.15

# =============================================================================
# Forbidden language — regulatory safety
# =============================================================================

FORBIDDEN_WORDS: frozenset[str] = frozenset(
    {
        "compliant",
        "compliance",
        "ready",
        "readiness",
        "certified",
        "approved",
        "approval",
        "will pass",
        "guaranteed",
        "guarantee",
        "ensures compliance",
        "meets requirements",
        "submission ready",
        "audit ready",
    }
)

# NOTE: "readiness" appears in the class name ReadinessAssessment for
# developer clarity, but NEVER in user-facing output text. The summary
# uses "assessment" terminology only.


def _check_regulatory_safe(text: str) -> bool:
    """Check that text does not contain forbidden regulatory language.

    Returns True if text is safe, False if it contains forbidden words.
    """
    lower = text.lower()
    for word in FORBIDDEN_WORDS:
        if word in lower:
            return False
    return True


# =============================================================================
# Pydantic Models
# =============================================================================


class CategoryScore(BaseModel):
    """Score for a single gap category (e.g., coverage, completeness)."""

    category: str = Field(..., description="Gap category name")
    score: float = Field(
        ..., ge=0.0, le=1.0, description="Score from 0.0 (poor) to 1.0 (no findings)"
    )
    finding_count: int = Field(default=0, description="Number of findings in this category")
    critical_count: int = Field(
        default=0, description="Number of critical findings in this category"
    )
    assessment: str = Field(
        ..., description="Human-readable assessment of this category (regulatory-safe)"
    )


class ReadinessReport(BaseModel):
    """Structured readiness assessment report.

    REGULATORY LANGUAGE SAFETY:
        The summary and all assessment text NEVER use forbidden words.
        All language is framed as "assessment based on configured expectations."
    """

    device_version_id: str = Field(..., description="Device version that was assessed")
    assessed_at: str = Field(..., description="ISO timestamp of assessment (Mountain Time)")
    overall_readiness_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall score from 0.0 (many gaps) to 1.0 (no findings detected)",
    )
    category_scores: list[CategoryScore] = Field(
        default_factory=list, description="Per-category scores"
    )
    gap_report: GapReport | None = Field(None, description="Underlying gap report (full findings)")
    critical_blockers: list[GapFinding] = Field(
        default_factory=list,
        description="Critical findings that represent significant gaps",
    )
    total_findings: int = Field(default=0, description="Total findings across all categories")
    summary: str = Field(
        ...,
        description="Human-readable summary using regulatory-safe language",
    )


# =============================================================================
# Readiness Assessment Service
# =============================================================================


class ReadinessAssessment:
    """
    Aggregates gap findings into a readiness assessment with scoring.

    NEVER says "compliant", "ready", "certified", "approved", or "will pass."
    ALWAYS says "assessment based on configured expectations."

    Scoring methodology:
        - Each gap category starts at 1.0 (no findings = perfect score)
        - Each finding applies a penalty: BASE_PENALTY * severity_weight
        - Scores are clamped to [0.0, 1.0]
        - Overall score = weighted average of category scores
        - Any critical finding is flagged as a blocker

    Best-effort pattern:
        - Logs errors but never crashes
        - Returns a valid (possibly empty) report on any failure
    """

    def __init__(
        self,
        gap_engine: GapDetectionEngine | None = None,
    ) -> None:
        self._gap_engine = gap_engine
        self._logger = get_logger(self.__class__.__name__)

    @property
    def gap_engine(self) -> GapDetectionEngine:
        """Lazy-load gap engine (singleton)."""
        if self._gap_engine is None:
            self._gap_engine = get_gap_engine()
        return self._gap_engine

    def assess(self, device_version_id: str) -> ReadinessReport:
        """Run full readiness assessment for a device version.

        1. Runs GapDetectionEngine.evaluate() to get GapReport
        2. Computes per-category scores
        3. Identifies critical blockers
        4. Generates regulatory-safe summary

        Args:
            device_version_id: UUID of the device version to assess

        Returns:
            ReadinessReport with scores, findings, and summary
        """
        try:
            self._logger.info(
                "Starting readiness assessment",
                device_version_id=device_version_id,
            )

            # Step 1: Get gap report
            gap_report = self.gap_engine.evaluate(device_version_id)

            # Step 2: Build the report from findings
            return self.assess_from_report(gap_report)

        except Exception as e:
            self._logger.error(
                "Readiness assessment failed — returning empty report",
                error=str(e),
                device_version_id=device_version_id,
            )
            return self._empty_report(device_version_id)

    def assess_from_report(self, gap_report: GapReport) -> ReadinessReport:
        """Build readiness assessment from an existing GapReport.

        This is the core scoring logic, separated from the gap evaluation
        step so it can be tested independently.

        Args:
            gap_report: A GapReport (from GapDetectionEngine)

        Returns:
            ReadinessReport with scores, findings, and summary
        """
        try:
            # Step 1: Compute per-category scores
            category_scores = self._compute_category_scores(gap_report.findings)

            # Step 2: Compute overall score
            overall_score = self._compute_overall_score(category_scores)

            # Step 3: Identify critical blockers
            critical_blockers = [f for f in gap_report.findings if f.severity == "critical"]

            # Step 4: Generate summary
            summary = self._generate_summary(
                overall_score=overall_score,
                category_scores=category_scores,
                critical_blockers=critical_blockers,
                total_findings=gap_report.total_findings,
            )

            now_mst = datetime.now(_MST).isoformat()

            return ReadinessReport(
                device_version_id=gap_report.device_version_id,
                assessed_at=now_mst,
                overall_readiness_score=overall_score,
                category_scores=category_scores,
                gap_report=gap_report,
                critical_blockers=critical_blockers,
                total_findings=gap_report.total_findings,
                summary=summary,
            )

        except Exception as e:
            self._logger.error(
                "assess_from_report failed — returning empty report",
                error=str(e),
            )
            return self._empty_report(gap_report.device_version_id)

    def _compute_category_scores(self, findings: list[GapFinding]) -> list[CategoryScore]:
        """Compute a score for each gap category.

        Categories with no findings get a perfect 1.0 score.
        Each finding applies a penalty based on severity weight.
        """
        # Group findings by category
        by_category: dict[str, list[GapFinding]] = {cat: [] for cat in GAP_CATEGORIES}
        for finding in findings:
            cat = finding.category
            if cat in by_category:
                by_category[cat].append(finding)
            else:
                # Unknown category — still track it
                by_category[cat] = [finding]

        scores: list[CategoryScore] = []
        for category in sorted(by_category.keys()):
            cat_findings = by_category[category]
            score = self._score_category(cat_findings)
            critical_count = sum(1 for f in cat_findings if f.severity == "critical")

            assessment_text = self._category_assessment_text(
                category, score, len(cat_findings), critical_count
            )

            scores.append(
                CategoryScore(
                    category=category,
                    score=score,
                    finding_count=len(cat_findings),
                    critical_count=critical_count,
                    assessment=assessment_text,
                )
            )

        return scores

    def _score_category(self, findings: list[GapFinding]) -> float:
        """Score a single category based on its findings.

        Starts at 1.0, subtracts penalty per finding.
        Clamped to [0.0, 1.0].
        """
        if not findings:
            return 1.0

        total_penalty = 0.0
        for finding in findings:
            weight = SEVERITY_WEIGHTS.get(finding.severity, 0.0)
            total_penalty += BASE_PENALTY_PER_FINDING * weight

        score = 1.0 - total_penalty
        return max(0.0, min(1.0, score))

    def _compute_overall_score(self, category_scores: list[CategoryScore]) -> float:
        """Compute overall readiness score from category scores.

        Simple average of all category scores. If no categories,
        returns 1.0 (no findings = perfect).
        """
        if not category_scores:
            return 1.0

        total = sum(cs.score for cs in category_scores)
        avg = total / len(category_scores)
        return round(max(0.0, min(1.0, avg)), 4)

    def _category_assessment_text(
        self,
        category: str,
        score: float,
        finding_count: int,
        critical_count: int,
    ) -> str:
        """Generate regulatory-safe assessment text for a category."""
        cat_display = category.replace("_", " ").title()

        if finding_count == 0:
            return f"{cat_display}: No findings detected based on configured expectations."

        if critical_count > 0:
            return (
                f"{cat_display}: {finding_count} finding(s) detected, "
                f"including {critical_count} critical. "
                f"Assessment score: {score:.2f}. "
                f"Significant gaps identified based on configured expectations."
            )

        if score >= 0.8:
            return (
                f"{cat_display}: {finding_count} finding(s) detected. "
                f"Assessment score: {score:.2f}. "
                f"Minor gaps identified based on configured expectations."
            )

        return (
            f"{cat_display}: {finding_count} finding(s) detected. "
            f"Assessment score: {score:.2f}. "
            f"Notable gaps identified based on configured expectations."
        )

    def _generate_summary(
        self,
        overall_score: float,
        category_scores: list[CategoryScore],
        critical_blockers: list[GapFinding],
        total_findings: int,
    ) -> str:
        """Generate regulatory-safe summary text.

        NEVER uses forbidden words. All language framed as assessment.
        """
        parts: list[str] = []

        # Opening
        parts.append(
            f"Assessment based on configured expectations. "
            f"Overall assessment score: {overall_score:.2f}."
        )

        # Findings overview
        if total_findings == 0:
            parts.append("No gaps detected across evaluated dimensions.")
        else:
            parts.append(
                f"{total_findings} finding(s) detected across "
                f"{len(category_scores)} evaluated dimension(s)."
            )

        # Critical blockers
        if critical_blockers:
            blocker_count = len(critical_blockers)
            parts.append(
                f"{blocker_count} critical finding(s) identified "
                f"that represent significant gaps requiring attention."
            )

        # Category highlights (only categories with findings)
        cats_with_findings = [cs for cs in category_scores if cs.finding_count > 0]
        if cats_with_findings:
            worst = min(cats_with_findings, key=lambda cs: cs.score)
            parts.append(
                f"Lowest scoring dimension: "
                f"{worst.category.replace('_', ' ').title()} "
                f"({worst.score:.2f})."
            )

        summary = " ".join(parts)

        # Safety check — should never fail, but belt-and-suspenders
        if not _check_regulatory_safe(summary):
            self._logger.error(
                "SAFETY VIOLATION: Generated summary contains forbidden language",
                summary=summary,
            )
            summary = (
                "Assessment based on configured expectations. "
                f"Overall assessment score: {overall_score:.2f}. "
                f"{total_findings} finding(s) detected."
            )

        return summary

    def _empty_report(self, device_version_id: str) -> ReadinessReport:
        """Return a safe empty report (used on errors)."""
        now_mst = datetime.now(_MST).isoformat()
        return ReadinessReport(
            device_version_id=device_version_id,
            assessed_at=now_mst,
            overall_readiness_score=0.0,
            category_scores=[],
            gap_report=None,
            critical_blockers=[],
            total_findings=0,
            summary=(
                "Assessment could not be completed. "
                "No score is available based on configured expectations."
            ),
        )


# =============================================================================
# Singleton
# =============================================================================

_readiness_assessment: ReadinessAssessment | None = None


def get_readiness_assessment() -> ReadinessAssessment:
    """Get or create the singleton ReadinessAssessment instance."""
    global _readiness_assessment
    if _readiness_assessment is None:
        _readiness_assessment = ReadinessAssessment()
    return _readiness_assessment
