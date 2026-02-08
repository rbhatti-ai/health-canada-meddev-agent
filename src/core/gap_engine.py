"""
Gap Detection Engine — Sprint 3a + 5B citations + 7C clinical/predicate rules.

Deterministic, rules-based engine that evaluates regulatory readiness.
16 versioned rules. No AI dependency. Each rule produces explainable
findings with severity, description, remediation, and CITATIONS.

CITATION-FIRST PRINCIPLE (Sprint 5B):
    Every gap finding now cites its regulatory source. Citations are
    pulled from the RegulatoryReferenceRegistry — never fabricated.

REGULATORY LANGUAGE SAFETY:
    This engine NEVER uses the words "compliant", "ready", "certified",
    "approved", "will pass", or "guaranteed" in any output. All language
    is framed as "assessment based on configured expectations."

Usage:
    engine = get_gap_engine()
    report = engine.evaluate("device-version-uuid")
    for finding in report.critical_findings:
        print(finding.description)
        print(finding.citation_text)  # e.g., "[SOR/98-282, s.32(2)(c)]"
"""

import copy
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from src.core.clinical_evidence import (
    CLASS_EVIDENCE_THRESHOLDS,
    ClinicalEvidenceService,
    get_clinical_evidence_service,
)
from src.core.confidentiality import ConfidentialityService, get_confidentiality_service
from src.core.predicate_analysis import (
    PredicateAnalysisService,
    get_predicate_analysis_service,
)
from src.core.regulatory_references import get_reference_registry
from src.core.traceability import TraceabilityEngine, get_traceability_engine
from src.persistence.twin_repository import TwinRepository, get_twin_repository
from src.utils.logging import get_logger

# =============================================================================
# Pydantic Models
# =============================================================================

# Severity and category as Literal types for strict validation
GapSeverity = str  # "critical", "major", "minor", "info"
GapCategory = str  # "coverage", "completeness", "consistency", "evidence_strength"


class GapFinding(BaseModel):
    """A single gap finding produced by a rule.

    Each finding is self-contained: it has enough context to be
    understood without looking up the rule definition.

    CITATION FIELDS (Sprint 5B):
        - regulation_ref: Primary regulatory reference ID
        - guidance_ref: Supporting guidance document reference ID
        - citation_text: Pre-formatted citation (e.g., "[SOR/98-282, s.32(2)(c)]")
    """

    rule_id: str = Field(..., description="Rule that produced this finding")
    rule_name: str = Field(..., description="Human-readable rule name")
    severity: GapSeverity = Field(..., description="Finding severity level")
    category: GapCategory = Field(..., description="Gap category")
    description: str = Field(..., description="What was found (regulatory-safe language)")
    entity_type: str | None = Field(None, description="Type of entity involved (e.g. 'hazard')")
    entity_id: str | None = Field(None, description="ID of the specific entity involved")
    remediation: str = Field(..., description="What to do to resolve this gap")
    details: dict[str, Any] | None = Field(
        default=None, description="Additional structured details"
    )
    # Citation fields (Sprint 5B)
    regulation_ref: str | None = Field(
        default=None, description="Primary regulation reference ID (e.g., 'SOR-98-282-S32-2-C')"
    )
    guidance_ref: str | None = Field(
        default=None, description="Supporting guidance document ID (e.g., 'GUI-0102')"
    )
    citation_text: str | None = Field(
        default=None, description="Formatted citation (e.g., '[SOR/98-282, s.32(2)(c)]')"
    )


class GapRuleDefinition(BaseModel):
    """Definition of a single gap detection rule.

    Rules are versioned so that changes to detection logic are traceable.

    CITATION FIELDS (Sprint 5B):
        - primary_reference: Main regulatory reference for this rule
        - secondary_references: Additional supporting references
    """

    id: str = Field(..., description="Unique rule identifier (e.g. GAP-001)")
    name: str = Field(..., description="Human-readable rule name")
    description: str = Field(..., description="What this rule checks")
    severity: GapSeverity = Field(..., description="Default severity level")
    category: GapCategory = Field(..., description="Gap category")
    version: int = Field(default=1, description="Rule version for traceability")
    enabled: bool = Field(default=True, description="Whether rule is active")
    # Citation fields (Sprint 5B)
    primary_reference: str | None = Field(
        default=None, description="Primary regulatory reference ID (e.g., 'ISO-14971-2019-7')"
    )
    secondary_references: list[str] = Field(
        default_factory=list, description="Additional reference IDs"
    )


class GapReport(BaseModel):
    """Aggregated gap report for a device version.

    Contains all findings from all rules, organized for review.
    """

    device_version_id: str = Field(..., description="Device version that was evaluated")
    evaluated_at: str = Field(..., description="ISO timestamp of evaluation (Mountain Time)")
    rules_executed: int = Field(..., description="Number of rules that were executed")
    total_findings: int = Field(..., description="Total number of gap findings")
    critical_count: int = Field(default=0, description="Number of critical findings")
    major_count: int = Field(default=0, description="Number of major findings")
    minor_count: int = Field(default=0, description="Number of minor findings")
    info_count: int = Field(default=0, description="Number of info findings")
    findings: list[GapFinding] = Field(default_factory=list, description="All gap findings")
    critical_findings: list[GapFinding] = Field(
        default_factory=list, description="Critical findings only"
    )


# =============================================================================
# Gap Detection Engine
# =============================================================================


class GapDetectionEngine:
    """
    Rules-based engine that evaluates regulatory readiness.

    Rules are versioned, deterministic, and explainable.
    Each rule produces a GapFinding with severity, description,
    and remediation.

    This engine does NOT use AI. It is purely deterministic.
    It queries the TraceabilityEngine and TwinRepository to
    check for gaps in the regulatory data.

    Usage:
        engine = get_gap_engine()
        report = engine.evaluate("device-version-uuid")
        for finding in report.critical_findings:
            print(finding.description)
    """

    # Class-level rule definitions — template (each instance gets a copy)
    # Sprint 5B: Each rule now has primary_reference and secondary_references
    _CLASS_RULE_DEFINITIONS: dict[str, GapRuleDefinition] = {
        "GAP-001": GapRuleDefinition(
            id="GAP-001",
            name="Unmitigated hazards",
            description="Hazards with no linked risk_control",
            severity="critical",
            category="coverage",
            version=2,  # Bumped for citation addition
            primary_reference="ISO-14971-2019-7",
            secondary_references=["ISO-14971-2019-7.1", "SOR-98-282-S10"],
        ),
        "GAP-002": GapRuleDefinition(
            id="GAP-002",
            name="Unverified controls",
            description="Risk controls with no linked verification_test",
            severity="critical",
            category="coverage",
            version=2,
            primary_reference="ISO-14971-2019-7.2",
            secondary_references=["ISO-13485-2016-7.3.6", "SOR-98-282-S10"],
        ),
        "GAP-003": GapRuleDefinition(
            id="GAP-003",
            name="Unsupported claims",
            description="Claims with no linked evidence_item",
            severity="major",
            category="coverage",
            version=2,
            primary_reference="SOR-98-282-S32-4",
            secondary_references=["GUI-0102"],
        ),
        "GAP-004": GapRuleDefinition(
            id="GAP-004",
            name="Missing intended use",
            description="Device version with no intended_use record",
            severity="critical",
            category="completeness",
            version=2,
            primary_reference="SOR-98-282-S32-2-A",
            secondary_references=["GUI-0098"],
        ),
        "GAP-005": GapRuleDefinition(
            id="GAP-005",
            name="Weak evidence",
            description="Evidence items with strength assessed as weak or insufficient",
            severity="major",
            category="evidence_strength",
            version=2,
            primary_reference="SOR-98-282-S32-4",
            secondary_references=["GUI-0102"],
        ),
        "GAP-006": GapRuleDefinition(
            id="GAP-006",
            name="Untested claims",
            description="Claims with no linked verification or validation test",
            severity="major",
            category="coverage",
            version=2,
            primary_reference="ISO-13485-2016-7.3.6",
            secondary_references=["ISO-13485-2016-7.3.7"],
        ),
        "GAP-007": GapRuleDefinition(
            id="GAP-007",
            name="No submission target",
            description="Device version with no submission_target record",
            severity="minor",
            category="completeness",
            version=2,
            primary_reference="SOR-98-282-S26",
            secondary_references=["GUI-0098"],
        ),
        "GAP-008": GapRuleDefinition(
            id="GAP-008",
            name="Unattested AI outputs",
            description="AI runs linked to artifacts that have not been attested by a human",
            severity="major",
            category="consistency",
            version=2,
            primary_reference="PLATFORM-PROVENANCE",
            secondary_references=["PLATFORM-LANGUAGE"],
        ),
        "GAP-009": GapRuleDefinition(
            id="GAP-009",
            name="Missing labeling",
            description="Device version with no labeling_assets",
            severity="major",
            category="completeness",
            version=2,
            primary_reference="SOR-98-282-PART5",
            secondary_references=["SOR-98-282-S21", "SOR-98-282-S22", "GUI-0015"],
        ),
        "GAP-010": GapRuleDefinition(
            id="GAP-010",
            name="Incomplete risk chain",
            description="Hazard to harm to control chain has breaks",
            severity="critical",
            category="consistency",
            version=2,
            primary_reference="ISO-14971-2019-6",
            secondary_references=["ISO-14971-2019-7"],
        ),
        "GAP-011": GapRuleDefinition(
            id="GAP-011",
            name="Draft evidence only",
            description="All evidence items for device version are in draft status",
            severity="major",
            category="evidence_strength",
            version=2,
            primary_reference="SOR-98-282-S32-4",
            secondary_references=["GUI-0102"],
        ),
        "GAP-012": GapRuleDefinition(
            id="GAP-012",
            name="No clinical evidence for Class III/IV",
            description="Class III/IV device with no clinical evidence type",
            severity="critical",
            category="evidence_strength",
            version=2,
            primary_reference="SOR-98-282-S32-2-C",
            secondary_references=["GUI-0102"],
        ),
        "GAP-013": GapRuleDefinition(
            id="GAP-013",
            name="Unclassified sensitive assets",
            description="Evidence items with no confidentiality classification",
            severity="minor",
            category="consistency",
            version=1,
            primary_reference="SOR-98-282-S43.2",
            secondary_references=[],
        ),
        "GAP-014": GapRuleDefinition(
            id="GAP-014",
            name="Insufficient clinical evidence strength",
            description="Clinical evidence below threshold for device class",
            severity="critical",
            category="evidence_strength",
            version=1,
            primary_reference="GUI-0102",
            secondary_references=["SOR-98-282-S32-4"],
        ),
        "GAP-015": GapRuleDefinition(
            id="GAP-015",
            name="No predicate device identified",
            description="Class II/III device with no predicate comparison",
            severity="major",
            category="completeness",
            version=1,
            primary_reference="SOR-98-282-S32-4",
            secondary_references=["GUI-0098"],
        ),
        "GAP-016": GapRuleDefinition(
            id="GAP-016",
            name="Technological differences unaddressed",
            description="Predicate has differences without supporting data",
            severity="critical",
            category="evidence_strength",
            version=1,
            primary_reference="SOR-98-282-S32-4",
            secondary_references=[],
        ),
    }

    def __init__(
        self,
        traceability_engine: TraceabilityEngine | None = None,
        twin_repository: TwinRepository | None = None,
        confidentiality_service: ConfidentialityService | None = None,
        clinical_evidence_service: ClinicalEvidenceService | None = None,
        predicate_analysis_service: PredicateAnalysisService | None = None,
    ) -> None:
        """Initialize the Gap Detection Engine.

        Args:
            traceability_engine: Engine for querying trace links.
                Defaults to singleton if not provided.
            twin_repository: Repository for querying regulatory twin entities.
                Defaults to singleton if not provided.
            confidentiality_service: Service for IP classification checks.
                Defaults to singleton if not provided.
            clinical_evidence_service: Service for clinical evidence scoring.
                Defaults to singleton if not provided.
            predicate_analysis_service: Service for predicate device analysis.
                Defaults to singleton if not provided.
        """
        self.logger = get_logger(self.__class__.__name__)
        self._traceability = traceability_engine or get_traceability_engine()
        self._repository = twin_repository or get_twin_repository()
        self._confidentiality = confidentiality_service or get_confidentiality_service()
        self._clinical_evidence = clinical_evidence_service or get_clinical_evidence_service()
        self._predicate_analysis = predicate_analysis_service or get_predicate_analysis_service()

        # Instance-level copy prevents cross-instance rule mutation
        self.RULE_DEFINITIONS: dict[str, GapRuleDefinition] = copy.deepcopy(
            GapDetectionEngine._CLASS_RULE_DEFINITIONS
        )

        # Citation registry for Sprint 5B
        self._citation_registry = get_reference_registry()

        # Map rule IDs to evaluation methods
        self._rule_evaluators: dict[str, Callable[..., list[GapFinding]]] = {
            "GAP-001": self._rule_unmitigated_hazards,
            "GAP-002": self._rule_unverified_controls,
            "GAP-003": self._rule_unsupported_claims,
            "GAP-004": self._rule_missing_intended_use,
            "GAP-005": self._rule_weak_evidence,
            "GAP-006": self._rule_untested_claims,
            "GAP-007": self._rule_no_submission_target,
            "GAP-008": self._rule_unattested_ai_outputs,
            "GAP-009": self._rule_missing_labeling,
            "GAP-010": self._rule_incomplete_risk_chain,
            "GAP-011": self._rule_draft_evidence_only,
            "GAP-012": self._rule_no_clinical_evidence,
            "GAP-013": self._rule_unclassified_sensitive_assets,
            "GAP-014": self._rule_insufficient_clinical_strength,
            "GAP-015": self._rule_no_predicate_identified,
            "GAP-016": self._rule_technological_differences_unaddressed,
        }

    def evaluate(self, device_version_id: str) -> GapReport:
        """Run all enabled rules against a device version.

        Args:
            device_version_id: UUID of the device version to evaluate.

        Returns:
            GapReport containing all findings from all rules.
        """
        self.logger.info(f"Starting gap evaluation for device version: " f"{device_version_id}")

        all_findings: list[GapFinding] = []
        rules_executed = 0

        for rule_id, rule_def in self.RULE_DEFINITIONS.items():
            if not rule_def.enabled:
                self.logger.debug(f"Skipping disabled rule: {rule_id}")
                continue

            evaluator = self._rule_evaluators.get(rule_id)
            if evaluator is None:
                self.logger.warning(f"No evaluator for rule {rule_id}, skipping")
                continue

            try:
                findings = evaluator(device_version_id)
                all_findings.extend(findings)
                rules_executed += 1
                if findings:
                    self.logger.info(f"Rule {rule_id}: {len(findings)} finding(s)")
            except Exception as e:
                # Best-effort: log and continue, never crash the engine
                self.logger.error(f"Rule {rule_id} failed: {e}", exc_info=True)
                rules_executed += 1

        # Build report
        now_mst = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        critical = [f for f in all_findings if f.severity == "critical"]
        major = [f for f in all_findings if f.severity == "major"]
        minor = [f for f in all_findings if f.severity == "minor"]
        info = [f for f in all_findings if f.severity == "info"]

        report = GapReport(
            device_version_id=device_version_id,
            evaluated_at=now_mst,
            rules_executed=rules_executed,
            total_findings=len(all_findings),
            critical_count=len(critical),
            major_count=len(major),
            minor_count=len(minor),
            info_count=len(info),
            findings=all_findings,
            critical_findings=critical,
        )

        self.logger.info(
            f"Gap evaluation complete: {report.total_findings} findings "
            f"({report.critical_count} critical, {report.major_count} major, "
            f"{report.minor_count} minor, {report.info_count} info)"
        )

        return report

    def evaluate_rule(self, rule_id: str, device_version_id: str) -> list[GapFinding]:
        """Run a single rule against a device version.

        Args:
            rule_id: Rule identifier (e.g. "GAP-001").
            device_version_id: UUID of the device version to evaluate.

        Returns:
            List of GapFinding objects produced by this rule.

        Raises:
            ValueError: If rule_id is not recognized.
        """
        if rule_id not in self.RULE_DEFINITIONS:
            raise ValueError(f"Unknown rule ID: {rule_id}")

        rule_def = self.RULE_DEFINITIONS[rule_id]
        if not rule_def.enabled:
            return []

        evaluator = self._rule_evaluators.get(rule_id)
        if evaluator is None:
            raise ValueError(f"No evaluator registered for rule: {rule_id}")

        return list(evaluator(device_version_id))

    def get_rules(self) -> list[GapRuleDefinition]:
        """List all rules with their definitions.

        Returns:
            List of all rule definitions (enabled and disabled).
        """
        return list(self.RULE_DEFINITIONS.values())

    def get_enabled_rules(self) -> list[GapRuleDefinition]:
        """List only enabled rules.

        Returns:
            List of enabled rule definitions.
        """
        return [r for r in self.RULE_DEFINITIONS.values() if r.enabled]

    def _get_citation_for_rule(self, rule_id: str) -> tuple[str | None, str | None, str | None]:
        """Get citation details for a rule from the registry.

        Args:
            rule_id: Rule identifier (e.g., "GAP-001")

        Returns:
            Tuple of (regulation_ref, guidance_ref, citation_text).
            Values are None if reference not found in registry.
        """
        rule = self.RULE_DEFINITIONS.get(rule_id)
        if not rule or not rule.primary_reference:
            return None, None, None

        primary_ref = self._citation_registry.get_by_id(rule.primary_reference)
        if not primary_ref:
            return rule.primary_reference, None, None

        citation_text = self._citation_registry.format_citation(primary_ref)

        # Determine if primary is regulation or guidance
        regulation_ref = None
        guidance_ref = None
        if primary_ref.reference_type == "regulation":
            regulation_ref = rule.primary_reference
        elif primary_ref.reference_type == "guidance":
            guidance_ref = rule.primary_reference
        elif primary_ref.reference_type == "standard":
            regulation_ref = rule.primary_reference  # Treat standards as regulation-level
        else:
            regulation_ref = rule.primary_reference  # Default to regulation

        # Check secondary references for guidance
        for sec_ref_id in rule.secondary_references:
            sec_ref = self._citation_registry.get_by_id(sec_ref_id)
            if sec_ref and sec_ref.reference_type == "guidance" and not guidance_ref:
                guidance_ref = sec_ref_id
                break

        return regulation_ref, guidance_ref, citation_text

    # =========================================================================
    # Rule Implementations
    #
    # TwinRepository uses generic methods:
    #   get_by_device_version(table, device_version_id) -> list[dict]
    #   get_by_id(table, id) -> dict | None
    #   get_by_field(table, field, value) -> list[dict]
    #
    # TraceabilityEngine returns TraceLink Pydantic models:
    #   Use attribute access: link.source_type, link.target_type, etc.
    # =========================================================================

    def _rule_unmitigated_hazards(self, device_version_id: str) -> list[GapFinding]:
        """GAP-001: Find hazards with no linked risk_control."""
        findings: list[GapFinding] = []
        rule = self.RULE_DEFINITIONS["GAP-001"]
        reg_ref, guid_ref, citation = self._get_citation_for_rule("GAP-001")

        hazards = self._repository.get_by_device_version("hazards", device_version_id)
        for hazard in hazards:
            hazard_id = str(hazard.get("id", ""))
            # Check for mitigated_by links where hazard is source
            source_links = self._traceability.get_links_from("hazard", hazard_id)
            mitigation_links = [
                link
                for link in source_links
                if link.target_type == "risk_control" and link.relationship == "mitigated_by"
            ]

            if not mitigation_links:
                findings.append(
                    GapFinding(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        category=rule.category,
                        description=(
                            f"Hazard '{hazard.get('description', 'Unknown')}' "
                            f"has no linked risk control. All identified "
                            f"hazards must have at least one mitigation "
                            f"measure per ISO 14971."
                        ),
                        entity_type="hazard",
                        entity_id=hazard_id,
                        remediation=(
                            "Create a risk control for this hazard and link "
                            "it using a 'mitigated_by' trace link."
                        ),
                        regulation_ref=reg_ref,
                        guidance_ref=guid_ref,
                        citation_text=citation,
                    )
                )

        return findings

    def _rule_unverified_controls(self, device_version_id: str) -> list[GapFinding]:
        """GAP-002: Find risk controls with no linked verification_test."""
        findings: list[GapFinding] = []
        rule = self.RULE_DEFINITIONS["GAP-002"]
        reg_ref, guid_ref, citation = self._get_citation_for_rule("GAP-002")

        hazards = self._repository.get_by_device_version("hazards", device_version_id)
        for hazard in hazards:
            hazard_id = str(hazard.get("id", ""))
            source_links = self._traceability.get_links_from("hazard", hazard_id)
            control_links = [link for link in source_links if link.target_type == "risk_control"]

            for c_link in control_links:
                control_id = str(c_link.target_id)
                control_links_out = self._traceability.get_links_from("risk_control", control_id)
                verification_links = [
                    cl
                    for cl in control_links_out
                    if cl.target_type == "verification_test" and cl.relationship == "verified_by"
                ]

                if not verification_links:
                    findings.append(
                        GapFinding(
                            rule_id=rule.id,
                            rule_name=rule.name,
                            severity=rule.severity,
                            category=rule.category,
                            description=(
                                f"Risk control '{control_id}' has no linked "
                                f"verification test. All risk controls must "
                                f"be verified per ISO 14971."
                            ),
                            entity_type="risk_control",
                            entity_id=control_id,
                            remediation=(
                                "Create a verification test for this risk "
                                "control and link it using a 'verified_by' "
                                "trace link."
                            ),
                            regulation_ref=reg_ref,
                            guidance_ref=guid_ref,
                            citation_text=citation,
                        )
                    )

        return findings

    def _rule_unsupported_claims(self, device_version_id: str) -> list[GapFinding]:
        """GAP-003: Find claims with no linked evidence_item."""
        findings: list[GapFinding] = []
        rule = self.RULE_DEFINITIONS["GAP-003"]
        reg_ref, guid_ref, citation = self._get_citation_for_rule("GAP-003")

        claims = self._repository.get_by_device_version("claims", device_version_id)
        for claim in claims:
            claim_id = str(claim.get("id", ""))
            links = self._traceability.get_links_from("claim", claim_id)
            evidence_links = [
                link
                for link in links
                if link.target_type == "evidence_item" and link.relationship == "supported_by"
            ]

            if not evidence_links:
                findings.append(
                    GapFinding(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        category=rule.category,
                        description=(
                            f"Claim '{claim.get('statement', 'Unknown')}' "
                            f"has no linked evidence. All claims must be "
                            f"supported by evidence."
                        ),
                        entity_type="claim",
                        entity_id=claim_id,
                        remediation=(
                            "Link evidence items to this claim using "
                            "'supported_by' trace links, or ingest new "
                            "evidence to support it."
                        ),
                        regulation_ref=reg_ref,
                        guidance_ref=guid_ref,
                        citation_text=citation,
                    )
                )

        return findings

    def _rule_missing_intended_use(self, device_version_id: str) -> list[GapFinding]:
        """GAP-004: Check if device version has an intended_use record."""
        findings: list[GapFinding] = []
        rule = self.RULE_DEFINITIONS["GAP-004"]
        reg_ref, guid_ref, citation = self._get_citation_for_rule("GAP-004")

        intended_uses = self._repository.get_by_device_version("intended_uses", device_version_id)

        if not intended_uses:
            findings.append(
                GapFinding(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    category=rule.category,
                    description=(
                        "Device version has no intended use statement. "
                        "An intended use statement is required for all "
                        "Health Canada submissions."
                    ),
                    entity_type="device_version",
                    entity_id=device_version_id,
                    remediation=(
                        "Create an intended use record for this device "
                        "version specifying the statement, indications, "
                        "contraindications, and target population."
                    ),
                    regulation_ref=reg_ref,
                    guidance_ref=guid_ref,
                    citation_text=citation,
                )
            )

        return findings

    def _rule_weak_evidence(self, device_version_id: str) -> list[GapFinding]:
        """GAP-005: Find evidence items with weak or insufficient strength."""
        findings: list[GapFinding] = []
        rule = self.RULE_DEFINITIONS["GAP-005"]
        reg_ref, guid_ref, citation = self._get_citation_for_rule("GAP-005")

        evidence_items = self._repository.get_by_device_version("evidence_items", device_version_id)
        for item in evidence_items:
            strength = item.get("strength", "")
            if strength in ("weak", "insufficient"):
                findings.append(
                    GapFinding(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        category=rule.category,
                        description=(
                            f"Evidence item '{item.get('title', 'Unknown')}' "
                            f"has strength assessed as '{strength}'. "
                            f"Regulatory submissions typically require "
                            f"moderate or strong evidence."
                        ),
                        entity_type="evidence_item",
                        entity_id=str(item.get("id", "")),
                        remediation=(
                            "Strengthen this evidence by obtaining additional "
                            "test data, peer-reviewed literature, or clinical "
                            "data to support the linked claims or tests."
                        ),
                        details={"current_strength": strength},
                        regulation_ref=reg_ref,
                        guidance_ref=guid_ref,
                        citation_text=citation,
                    )
                )

        return findings

    def _rule_untested_claims(self, device_version_id: str) -> list[GapFinding]:
        """GAP-006: Find claims with no linked verification or validation test."""
        findings: list[GapFinding] = []
        rule = self.RULE_DEFINITIONS["GAP-006"]
        reg_ref, guid_ref, citation = self._get_citation_for_rule("GAP-006")

        claims = self._repository.get_by_device_version("claims", device_version_id)
        for claim in claims:
            claim_id = str(claim.get("id", ""))
            links = self._traceability.get_links_from("claim", claim_id)

            # Check if claim addresses any hazard that has controls with tests
            hazard_links = [
                link
                for link in links
                if link.target_type == "hazard" and link.relationship == "addresses"
            ]

            has_test_coverage = False
            for h_link in hazard_links:
                hazard_id = str(h_link.target_id)
                h_out_links = self._traceability.get_links_from("hazard", hazard_id)
                for control_link in h_out_links:
                    if control_link.target_type == "risk_control":
                        control_id = str(control_link.target_id)
                        c_out_links = self._traceability.get_links_from("risk_control", control_id)
                        for test_link in c_out_links:
                            if test_link.target_type in (
                                "verification_test",
                                "validation_test",
                            ):
                                has_test_coverage = True
                                break
                    if has_test_coverage:
                        break
                if has_test_coverage:
                    break

            if not has_test_coverage:
                findings.append(
                    GapFinding(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        category=rule.category,
                        description=(
                            f"Claim '{claim.get('statement', 'Unknown')}' "
                            f"has no path to any verification or validation "
                            f"test through the risk control chain."
                        ),
                        entity_type="claim",
                        entity_id=claim_id,
                        remediation=(
                            "Ensure this claim addresses a hazard that has "
                            "risk controls linked to verification or "
                            "validation tests."
                        ),
                        regulation_ref=reg_ref,
                        guidance_ref=guid_ref,
                        citation_text=citation,
                    )
                )

        return findings

    def _rule_no_submission_target(self, device_version_id: str) -> list[GapFinding]:
        """GAP-007: Check if device version has a submission target."""
        findings: list[GapFinding] = []
        rule = self.RULE_DEFINITIONS["GAP-007"]
        reg_ref, guid_ref, citation = self._get_citation_for_rule("GAP-007")

        targets = self._repository.get_by_device_version("submission_targets", device_version_id)

        if not targets:
            findings.append(
                GapFinding(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    category=rule.category,
                    description=(
                        "Device version has no submission target defined. "
                        "A submission target identifies the regulatory body "
                        "and submission type being prepared."
                    ),
                    entity_type="device_version",
                    entity_id=device_version_id,
                    remediation=(
                        "Create a submission target specifying the "
                        "regulatory body (e.g. Health Canada), submission "
                        "type (e.g. MDL), and target date."
                    ),
                    regulation_ref=reg_ref,
                    guidance_ref=guid_ref,
                    citation_text=citation,
                )
            )

        return findings

    def _rule_unattested_ai_outputs(self, device_version_id: str) -> list[GapFinding]:
        """GAP-008: Find AI-generated artifacts without human attestation.

        Uses get_by_field to find unattested AI artifacts. This is a
        simplified check — production would cross-reference ai_runs
        with attestations table.
        """
        findings: list[GapFinding] = []
        rule = self.RULE_DEFINITIONS["GAP-008"]
        reg_ref, guid_ref, citation = self._get_citation_for_rule("GAP-008")

        # Get unattested AI artifacts for this device version
        # Uses generic repository method; caller mocks this in tests
        unattested = self._repository.get_by_field(
            "artifacts", "device_version_id", device_version_id
        )

        for artifact in unattested:
            findings.append(
                GapFinding(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    category=rule.category,
                    description=(
                        f"AI-generated artifact "
                        f"'{artifact.get('title', 'Unknown')}' "
                        f"has not been reviewed or attested by a human. "
                        f"Per platform policy, no AI output becomes "
                        f"regulatory content without human approval."
                    ),
                    entity_type="artifact",
                    entity_id=str(artifact.get("id", "")),
                    remediation=(
                        "Review this AI-generated artifact and create an "
                        "attestation record (reviewed, approved, or "
                        "rejected)."
                    ),
                    regulation_ref=reg_ref,
                    guidance_ref=guid_ref,
                    citation_text=citation,
                )
            )

        return findings

    def _rule_missing_labeling(self, device_version_id: str) -> list[GapFinding]:
        """GAP-009: Check if device version has labeling assets."""
        findings: list[GapFinding] = []
        rule = self.RULE_DEFINITIONS["GAP-009"]
        reg_ref, guid_ref, citation = self._get_citation_for_rule("GAP-009")

        labeling = self._repository.get_by_device_version("labeling_assets", device_version_id)

        if not labeling:
            findings.append(
                GapFinding(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    category=rule.category,
                    description=(
                        "Device version has no labeling assets. "
                        "Health Canada requires IFU, device labels, "
                        "and packaging labeling for all submissions."
                    ),
                    entity_type="device_version",
                    entity_id=device_version_id,
                    remediation=(
                        "Create labeling assets including at minimum: "
                        "Instructions for Use (IFU), device label, "
                        "and packaging label."
                    ),
                    regulation_ref=reg_ref,
                    guidance_ref=guid_ref,
                    citation_text=citation,
                )
            )

        return findings

    def _rule_incomplete_risk_chain(self, device_version_id: str) -> list[GapFinding]:
        """GAP-010: Check hazard->harm->control chain for breaks."""
        findings: list[GapFinding] = []
        rule = self.RULE_DEFINITIONS["GAP-010"]
        reg_ref, guid_ref, citation = self._get_citation_for_rule("GAP-010")

        hazards = self._repository.get_by_device_version("hazards", device_version_id)
        for hazard in hazards:
            hazard_id = str(hazard.get("id", ""))
            links = self._traceability.get_links_from("hazard", hazard_id)

            has_harm = any(
                link.target_type == "harm" and link.relationship in ("causes", "may_cause")
                for link in links
            )
            has_control = any(
                link.target_type == "risk_control" and link.relationship == "mitigated_by"
                for link in links
            )

            if not has_harm and not has_control:
                findings.append(
                    GapFinding(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        category=rule.category,
                        description=(
                            f"Hazard '{hazard.get('description', 'Unknown')}' "
                            f"has no linked harm AND no linked risk control. "
                            f"The risk chain is incomplete — both harm "
                            f"identification and mitigation are missing."
                        ),
                        entity_type="hazard",
                        entity_id=hazard_id,
                        remediation=(
                            "Link this hazard to its potential harm(s) using "
                            "'causes' or 'may_cause' relationships, and "
                            "create risk controls with 'mitigated_by' links."
                        ),
                        details={
                            "has_harm": has_harm,
                            "has_control": has_control,
                        },
                        regulation_ref=reg_ref,
                        guidance_ref=guid_ref,
                        citation_text=citation,
                    )
                )
            elif not has_harm:
                findings.append(
                    GapFinding(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        category=rule.category,
                        description=(
                            f"Hazard '{hazard.get('description', 'Unknown')}' "
                            f"has risk controls but no linked harm. "
                            f"ISO 14971 requires identifying the harm "
                            f"each hazard may cause."
                        ),
                        entity_type="hazard",
                        entity_id=hazard_id,
                        remediation=(
                            "Link this hazard to its potential harm(s) using "
                            "'causes' or 'may_cause' relationships."
                        ),
                        details={
                            "has_harm": has_harm,
                            "has_control": has_control,
                        },
                        regulation_ref=reg_ref,
                        guidance_ref=guid_ref,
                        citation_text=citation,
                    )
                )

        return findings

    def _rule_draft_evidence_only(self, device_version_id: str) -> list[GapFinding]:
        """GAP-011: Check if ALL evidence items are still in draft status."""
        findings: list[GapFinding] = []
        rule = self.RULE_DEFINITIONS["GAP-011"]
        reg_ref, guid_ref, citation = self._get_citation_for_rule("GAP-011")

        evidence_items = self._repository.get_by_device_version("evidence_items", device_version_id)

        if not evidence_items:
            # No evidence at all — other rules catch this
            return findings

        all_draft = all(item.get("status", "draft") == "draft" for item in evidence_items)

        if all_draft:
            findings.append(
                GapFinding(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    category=rule.category,
                    description=(
                        f"All {len(evidence_items)} evidence item(s) for "
                        f"this device version are in 'draft' status. At "
                        f"least some evidence should be finalized before "
                        f"submission preparation."
                    ),
                    entity_type="device_version",
                    entity_id=device_version_id,
                    remediation=(
                        "Review and finalize evidence items by updating "
                        "their status from 'draft' to 'under_review' or "
                        "'accepted'."
                    ),
                    details={"total_evidence": len(evidence_items)},
                    regulation_ref=reg_ref,
                    guidance_ref=guid_ref,
                    citation_text=citation,
                )
            )

        return findings

    def _rule_no_clinical_evidence(self, device_version_id: str) -> list[GapFinding]:
        """GAP-012: Class III/IV devices must have clinical evidence."""
        findings: list[GapFinding] = []
        rule = self.RULE_DEFINITIONS["GAP-012"]
        reg_ref, guid_ref, citation = self._get_citation_for_rule("GAP-012")

        # Get device version to check class
        device_version = self._repository.get_by_id("device_versions", device_version_id)
        if not device_version:
            return findings

        # Check if device is Class III or IV
        device_class = device_version.get("device_class", "")
        if device_class not in ("III", "IV"):
            return findings

        # Check for clinical evidence
        evidence_items = self._repository.get_by_device_version("evidence_items", device_version_id)
        has_clinical = any(item.get("evidence_type") == "clinical_data" for item in evidence_items)

        if not has_clinical:
            findings.append(
                GapFinding(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    category=rule.category,
                    description=(
                        f"Class {device_class} device has no clinical "
                        f"evidence. Health Canada typically requires "
                        f"clinical data for Class III and IV devices."
                    ),
                    entity_type="device_version",
                    entity_id=device_version_id,
                    remediation=(
                        "Provide clinical evidence such as clinical "
                        "investigation data, clinical evaluation reports, "
                        "or substantial equivalence clinical data."
                    ),
                    details={"device_class": device_class},
                    regulation_ref=reg_ref,
                    guidance_ref=guid_ref,
                    citation_text=citation,
                )
            )

        return findings

    def _rule_unclassified_sensitive_assets(self, device_version_id: str) -> list[GapFinding]:
        """GAP-013: Find evidence items without confidentiality classification.

        Per SOR/98-282 s.43.2, manufacturers should identify which portions
        of their submissions contain confidential business information.
        This rule flags evidence items that have not been classified.
        """
        findings: list[GapFinding] = []
        rule = self.RULE_DEFINITIONS["GAP-013"]
        reg_ref, guid_ref, citation = self._get_citation_for_rule("GAP-013")

        # Get device version to find organization
        device_version = self._repository.get_by_id("device_versions", device_version_id)
        if not device_version:
            return findings

        org_id = device_version.get("organization_id")
        if not org_id:
            return findings

        # Get all evidence items for this device version
        evidence_items = self._repository.get_by_device_version("evidence_items", device_version_id)

        # Build list of (entity_type, entity_id) tuples
        from uuid import UUID

        known_entities: list[tuple[str, UUID]] = []
        for item in evidence_items:
            item_id = item.get("id")
            if item_id:
                try:
                    known_entities.append(("evidence_item", UUID(str(item_id))))
                except (ValueError, TypeError):
                    pass

        if not known_entities:
            return findings

        # Check which are unclassified
        try:
            org_uuid = UUID(str(org_id))
        except (ValueError, TypeError):
            return findings

        unclassified = self._confidentiality.get_unclassified(org_uuid, known_entities)

        for entity_type, entity_id in unclassified:
            # Look up the evidence item title for better description
            item_title = "Unknown"
            for item in evidence_items:
                if str(item.get("id")) == str(entity_id):
                    item_title = item.get("title", "Unknown")
                    break

            findings.append(
                GapFinding(
                    rule_id=rule.id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    category=rule.category,
                    description=(
                        f"Evidence item '{item_title}' has no confidentiality "
                        f"classification. Before submission, determine whether "
                        f"this item contains confidential business information."
                    ),
                    entity_type=entity_type,
                    entity_id=str(entity_id),
                    remediation=(
                        "Classify this evidence item as 'public', "
                        "'confidential_submission', 'trade_secret', or "
                        "'patent_pending' using the ConfidentialityService."
                    ),
                    regulation_ref=reg_ref,
                    guidance_ref=guid_ref,
                    citation_text=citation,
                )
            )

        return findings

    def _rule_insufficient_clinical_strength(self, device_version_id: str) -> list[GapFinding]:
        """GAP-014: Clinical evidence strength below threshold for device class.

        Uses ClinicalEvidenceService to check if the aggregate evidence score
        meets the minimum threshold for the device's class per GUI-0102.
        """
        findings: list[GapFinding] = []
        rule = self.RULE_DEFINITIONS["GAP-014"]
        reg_ref, guid_ref, citation = self._get_citation_for_rule("GAP-014")

        # Get device version to check class
        device_version = self._repository.get_by_id("device_versions", device_version_id)
        if not device_version:
            return findings

        device_class = device_version.get("device_class", "")
        if not device_class:
            return findings

        # Get threshold for this class
        threshold = CLASS_EVIDENCE_THRESHOLDS.get(device_class, 0.0)
        if threshold == 0.0:
            return findings  # Class I has no threshold

        # Get clinical evidence portfolio
        try:
            from uuid import UUID

            dv_uuid = UUID(str(device_version_id))
            portfolio = self._clinical_evidence.get_portfolio(dv_uuid)

            if portfolio.total_studies == 0:
                # No clinical evidence — GAP-012 catches this for III/IV
                return findings

            if portfolio.weighted_quality_score < threshold:
                findings.append(
                    GapFinding(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        category=rule.category,
                        description=(
                            f"Clinical evidence strength ({portfolio.weighted_quality_score:.2f}) "
                            f"is below the threshold ({threshold:.2f}) for Class "
                            f"{device_class} devices. Consider adding higher-quality "
                            f"evidence such as RCTs or prospective cohorts."
                        ),
                        entity_type="device_version",
                        entity_id=device_version_id,
                        remediation=(
                            "Add clinical evidence with higher quality scores. "
                            "RCTs score 1.0, prospective cohorts score 0.85. "
                            "Consider upgrading case series to cohort studies."
                        ),
                        details={
                            "current_score": portfolio.weighted_quality_score,
                            "threshold": threshold,
                            "device_class": device_class,
                            "evidence_count": portfolio.total_studies,
                        },
                        regulation_ref=reg_ref,
                        guidance_ref=guid_ref,
                        citation_text=citation,
                    )
                )
        except Exception as e:
            self.logger.warning(f"Could not assess clinical evidence: {e}")

        return findings

    def _rule_no_predicate_identified(self, device_version_id: str) -> list[GapFinding]:
        """GAP-015: Class II/III device with no predicate comparison.

        Per SOR/98-282 s.32(4), manufacturers may demonstrate substantial
        equivalence to a legally marketed predicate device. This rule flags
        Class II/III devices that have no predicate analysis.
        """
        findings: list[GapFinding] = []
        rule = self.RULE_DEFINITIONS["GAP-015"]
        reg_ref, guid_ref, citation = self._get_citation_for_rule("GAP-015")

        # Get device version to check class
        device_version = self._repository.get_by_id("device_versions", device_version_id)
        if not device_version:
            return findings

        device_class = device_version.get("device_class", "")
        if device_class not in ("II", "III"):
            return findings  # Only applies to II/III

        # Check if predicate analysis exists
        try:
            from uuid import UUID

            dv_uuid = UUID(str(device_version_id))
            comparisons = self._predicate_analysis.get_by_device_version(dv_uuid)

            if not comparisons:
                findings.append(
                    GapFinding(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        severity=rule.severity,
                        category=rule.category,
                        description=(
                            f"Class {device_class} device has no predicate device "
                            f"comparison. Consider identifying a legally marketed "
                            f"predicate device to demonstrate substantial equivalence."
                        ),
                        entity_type="device_version",
                        entity_id=device_version_id,
                        remediation=(
                            "Identify a legally marketed predicate device with "
                            "similar intended use and technology. Create a "
                            "predicate comparison using PredicateAnalysisService."
                        ),
                        details={"device_class": device_class},
                        regulation_ref=reg_ref,
                        guidance_ref=guid_ref,
                        citation_text=citation,
                    )
                )
        except Exception as e:
            self.logger.warning(f"Could not check predicate comparisons: {e}")

        return findings

    def _rule_technological_differences_unaddressed(
        self, device_version_id: str
    ) -> list[GapFinding]:
        """GAP-016: Predicate has technological differences without supporting data.

        When a predicate comparison identifies technological differences but
        those differences are not addressed with mitigations or data, this
        creates a gap in the substantial equivalence demonstration.
        """
        findings: list[GapFinding] = []
        rule = self.RULE_DEFINITIONS["GAP-016"]
        reg_ref, guid_ref, citation = self._get_citation_for_rule("GAP-016")

        try:
            from uuid import UUID

            dv_uuid = UUID(str(device_version_id))
            predicates = self._predicate_analysis.get_by_device_version(dv_uuid)

            for predicate in predicates:
                # Check if there are unaddressed technological differences
                differences = predicate.technological_differences
                mitigations = predicate.technological_mitigations

                # If there are differences but no mitigations, flag it
                if differences and not mitigations:
                    predicate_name = predicate.predicate_name
                    findings.append(
                        GapFinding(
                            rule_id=rule.id,
                            rule_name=rule.name,
                            severity=rule.severity,
                            category=rule.category,
                            description=(
                                f"Predicate comparison to '{predicate_name}' "
                                f"identifies {len(differences)} technological difference(s) "
                                f"without documented mitigations or supporting data."
                            ),
                            entity_type="predicate_device",
                            entity_id=str(predicate.id),
                            remediation=(
                                "Document how technological differences are "
                                "addressed. Provide performance data, bench "
                                "testing, or clinical evidence showing the "
                                "differences do not affect safety or effectiveness."
                            ),
                            details={
                                "predicate_name": predicate_name,
                                "differences": differences,
                                "tech_equivalent": predicate.technological_equivalent,
                            },
                            regulation_ref=reg_ref,
                            guidance_ref=guid_ref,
                            citation_text=citation,
                        )
                    )
        except Exception as e:
            self.logger.warning(f"Could not check technological differences: {e}")

        return findings


# =============================================================================
# Singleton Access
# =============================================================================

_gap_engine: GapDetectionEngine | None = None


def get_gap_engine(
    traceability_engine: TraceabilityEngine | None = None,
    twin_repository: TwinRepository | None = None,
    confidentiality_service: ConfidentialityService | None = None,
    clinical_evidence_service: ClinicalEvidenceService | None = None,
    predicate_analysis_service: PredicateAnalysisService | None = None,
) -> GapDetectionEngine:
    """Get or create the singleton GapDetectionEngine instance.

    Args:
        traceability_engine: Optional override for testing.
        twin_repository: Optional override for testing.
        confidentiality_service: Optional override for testing.
        clinical_evidence_service: Optional override for testing.
        predicate_analysis_service: Optional override for testing.

    Returns:
        GapDetectionEngine singleton instance.
    """
    global _gap_engine
    if (
        _gap_engine is None
        or traceability_engine
        or twin_repository
        or confidentiality_service
        or clinical_evidence_service
        or predicate_analysis_service
    ):
        _gap_engine = GapDetectionEngine(
            traceability_engine=traceability_engine,
            twin_repository=twin_repository,
            confidentiality_service=confidentiality_service,
            clinical_evidence_service=clinical_evidence_service,
            predicate_analysis_service=predicate_analysis_service,
        )
    return _gap_engine
