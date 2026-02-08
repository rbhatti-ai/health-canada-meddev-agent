"""
Traceability Engine — Core link management and chain traversal.

Creates, validates, and queries regulatory trace links using the
existing trace_links table. Supports:

Risk Management Chain:
  claim → hazard → risk_control → verification_test → evidence_item

Design Control Chain (ISO 13485 7.3):
  design_input → design_output → design_verification → evidence_item
  design_review → design_output

Design:
  - VALID_RELATIONSHIPS dict enforces allowed link types
  - Best-effort persistence (never crashes on DB failure)
  - Pydantic models for type safety and serialization
  - Chain traversal via recursive link following
  - Coverage reports per device version

Sprint 2a + 8B — 2026-02-07
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# =========================================================================
# Types (matching trace_links DB schema)
# =========================================================================

SourceTargetType = Literal[
    "claim",
    "hazard",
    "harm",
    "risk_control",
    "verification_test",
    "validation_test",
    "evidence_item",
    "artifact",
    "intended_use",
    # Design control types (ISO 13485 7.3)
    "design_input",
    "design_output",
    "design_review",
    "design_verification",
    "design_validation",
]

RelationshipType = Literal[
    "addresses",
    "supported_by",
    "causes",
    "may_cause",
    "mitigated_by",
    "verified_by",
    "validated_by",
    "documented_in",
    # Design control relationships (ISO 13485 7.3)
    "drives",
    "satisfies",
    "reviews",
]


# =========================================================================
# Pydantic Models
# =========================================================================


class TraceLink(BaseModel):
    """A single trace link between two regulatory entities.

    Maps directly to the trace_links DB table.
    """

    id: UUID | None = None
    organization_id: UUID
    created_by: UUID | None = None
    source_type: SourceTargetType
    source_id: UUID
    target_type: SourceTargetType
    target_id: UUID
    relationship: RelationshipType
    rationale: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    def to_db_dict(self) -> dict[str, Any]:
        """Convert to dict for DB insert (excludes None, converts UUID)."""
        data: dict[str, Any] = {}
        for field_name, value in self:
            if value is None:
                continue
            if field_name == "id":
                continue  # DB generates
            if field_name == "created_at":
                continue  # DB generates
            if isinstance(value, UUID):
                data[field_name] = str(value)
            elif isinstance(value, dict):
                data[field_name] = value
            else:
                data[field_name] = value
        return data

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> TraceLink:
        """Create from a DB row dict."""
        return cls(**{k: v for k, v in row.items() if k in cls.model_fields})


class TraceChainNode(BaseModel):
    """A single node in a trace chain."""

    entity_type: str
    entity_id: UUID
    relationship: str | None = None  # relationship TO this node
    children: list[TraceChainNode] = Field(default_factory=list)


class TraceChain(BaseModel):
    """Full trace chain from a root entity down to evidence."""

    root_type: str
    root_id: UUID
    nodes: list[TraceChainNode] = Field(default_factory=list)
    total_links: int = 0
    max_depth: int = 0


class ClaimCoverage(BaseModel):
    """Coverage summary for a single claim."""

    claim_id: UUID
    hazards: list[UUID] = Field(default_factory=list)
    risk_controls: list[UUID] = Field(default_factory=list)
    verification_tests: list[UUID] = Field(default_factory=list)
    validation_tests: list[UUID] = Field(default_factory=list)
    evidence_items: list[UUID] = Field(default_factory=list)
    has_hazard_link: bool = False
    has_control_link: bool = False
    has_test_link: bool = False
    has_evidence_link: bool = False


class CoverageReport(BaseModel):
    """Coverage report for all claims in a device version."""

    device_version_id: UUID
    claims: list[ClaimCoverage] = Field(default_factory=list)
    total_claims: int = 0
    claims_with_full_coverage: int = 0
    claims_with_partial_coverage: int = 0
    claims_with_no_coverage: int = 0
    coverage_percentage: float = 0.0


# =========================================================================
# Valid Relationships (enforced at application level)
# =========================================================================

VALID_RELATIONSHIPS: dict[tuple[str, str], list[str]] = {
    # Risk management chain
    ("claim", "hazard"): ["addresses"],
    ("claim", "evidence_item"): ["supported_by"],
    ("hazard", "harm"): ["causes", "may_cause"],
    ("hazard", "risk_control"): ["mitigated_by"],
    ("risk_control", "verification_test"): ["verified_by"],
    ("risk_control", "validation_test"): ["validated_by"],
    ("verification_test", "evidence_item"): ["supported_by"],
    ("validation_test", "evidence_item"): ["supported_by"],
    ("evidence_item", "artifact"): ["documented_in"],
    # Design control chain (ISO 13485 7.3)
    ("design_input", "design_output"): ["drives"],
    ("design_output", "design_input"): ["satisfies"],
    ("design_output", "design_verification"): ["verified_by"],
    ("design_output", "design_validation"): ["validated_by"],
    ("design_review", "design_output"): ["reviews"],
    ("design_verification", "evidence_item"): ["supported_by"],
    ("design_validation", "evidence_item"): ["supported_by"],
}


# =========================================================================
# Traceability Engine
# =========================================================================


class TraceabilityEngine:
    """Creates and queries regulatory trace links.

    Supports the full chain:
      claim → addresses → hazard
      hazard → mitigated_by → risk_control
      risk_control → verified_by → verification_test
      verification_test → supported_by → evidence_item
      evidence_item → documented_in → artifact

    All operations are best-effort: never crash on DB failure.
    Uses the TwinRepository pattern for dual Supabase/local Postgres support.
    """

    # Import here to avoid circular imports at module level
    TABLE = "trace_links"

    def __init__(self) -> None:
        from src.persistence.twin_repository import TwinRepository

        self._repo = TwinRepository()

    @property
    def is_available(self) -> bool:
        """Check if DB backend is available."""
        return self._repo.is_available

    # -----------------------------------------------------------------
    # VALIDATE
    # -----------------------------------------------------------------

    @staticmethod
    def validate_link(source_type: str, target_type: str, relationship: str) -> bool:
        """Check if the relationship is valid per VALID_RELATIONSHIPS.

        Returns True if the (source_type, target_type, relationship)
        combination is allowed.
        """
        key = (source_type, target_type)
        if key not in VALID_RELATIONSHIPS:
            return False
        return relationship in VALID_RELATIONSHIPS[key]

    @staticmethod
    def get_valid_relationships() -> dict[tuple[str, str], list[str]]:
        """Return the full VALID_RELATIONSHIPS dict."""
        return dict(VALID_RELATIONSHIPS)

    @staticmethod
    def get_valid_relationships_for_source(
        source_type: str,
    ) -> dict[str, list[str]]:
        """Get all valid target types and relationships for a source type."""
        result: dict[str, list[str]] = {}
        for (src, tgt), rels in VALID_RELATIONSHIPS.items():
            if src == source_type:
                result[tgt] = list(rels)
        return result

    # -----------------------------------------------------------------
    # CREATE
    # -----------------------------------------------------------------

    def create_link(
        self,
        organization_id: UUID | str,
        source_type: str,
        source_id: UUID | str,
        target_type: str,
        target_id: UUID | str,
        relationship: str,
        rationale: str | None = None,
        created_by: UUID | str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> TraceLink | None:
        """Create a trace link after validating the relationship.

        Returns the created TraceLink or None on failure/invalid link.
        """
        # Validate relationship
        if not self.validate_link(source_type, target_type, relationship):
            logger.warning(
                "Invalid trace link: %s -[%s]-> %s",
                source_type,
                relationship,
                target_type,
            )
            return None

        link = TraceLink(
            organization_id=UUID(str(organization_id)),
            source_type=source_type,  # type: ignore[arg-type]
            source_id=UUID(str(source_id)),
            target_type=target_type,  # type: ignore[arg-type]
            target_id=UUID(str(target_id)),
            relationship=relationship,  # type: ignore[arg-type]
            rationale=rationale,
            created_by=UUID(str(created_by)) if created_by else None,
            metadata=metadata or {},
        )

        data = link.to_db_dict()

        if not self.is_available:
            logger.warning("No DB available for create_link")
            return None

        try:
            result = (
                self._repo._supabase_insert(self.TABLE, data)
                if self._repo._use_supabase
                else self._repo._local_insert(self.TABLE, data)
            )
            if result:
                # Return the link with DB-assigned id
                link_dict = {**data, **result}
                return TraceLink.from_db_row(link_dict)
            return None
        except Exception as exc:
            logger.warning("create_link failed: %s", exc)
            return None

    # -----------------------------------------------------------------
    # READ
    # -----------------------------------------------------------------

    def get_link_by_id(self, link_id: UUID | str) -> TraceLink | None:
        """Get a single trace link by ID."""
        result = self._repo.get_by_id(self.TABLE, link_id)
        if result:
            try:
                return TraceLink.from_db_row(result)
            except Exception as exc:
                logger.warning("get_link_by_id parse failed: %s", exc)
        return None

    def get_links_from(self, source_type: str, source_id: UUID | str) -> list[TraceLink]:
        """Get all links FROM a given source entity."""
        if not self.is_available:
            return []

        try:
            # We need a compound query — source_type AND source_id
            # The generic repo only supports single-field queries,
            # so we use a custom approach
            rows = self._query_links("source_type", source_type, "source_id", str(source_id))
            return [TraceLink.from_db_row(r) for r in rows]
        except Exception as exc:
            logger.warning("get_links_from failed: %s", exc)
            return []

    def get_links_to(self, target_type: str, target_id: UUID | str) -> list[TraceLink]:
        """Get all links TO a given target entity."""
        if not self.is_available:
            return []

        try:
            rows = self._query_links("target_type", target_type, "target_id", str(target_id))
            return [TraceLink.from_db_row(r) for r in rows]
        except Exception as exc:
            logger.warning("get_links_to failed: %s", exc)
            return []

    def get_links_for_org(self, organization_id: UUID | str) -> list[TraceLink]:
        """Get all trace links for an organization."""
        rows = self._repo.get_by_field(self.TABLE, "organization_id", str(organization_id))
        try:
            return [TraceLink.from_db_row(r) for r in rows]
        except Exception as exc:
            logger.warning("get_links_for_org parse failed: %s", exc)
            return []

    # -----------------------------------------------------------------
    # CHAIN TRAVERSAL
    # -----------------------------------------------------------------

    def get_full_chain(
        self, entity_type: str, entity_id: UUID | str, max_depth: int = 10
    ) -> TraceChain:
        """Follow all links from an entity down to evidence/artifacts.

        Builds a tree of linked entities via breadth-first traversal.
        Stops at max_depth to prevent infinite loops.
        """
        root_id = UUID(str(entity_id))
        chain = TraceChain(
            root_type=entity_type,
            root_id=root_id,
        )

        if not self.is_available:
            return chain

        visited: set[tuple[str, str]] = set()
        nodes = self._traverse(entity_type, str(root_id), 0, max_depth, visited)
        chain.nodes = nodes
        chain.total_links = len(visited)
        chain.max_depth = self._compute_depth(nodes)

        return chain

    def _traverse(
        self,
        source_type: str,
        source_id: str,
        depth: int,
        max_depth: int,
        visited: set[tuple[str, str]],
    ) -> list[TraceChainNode]:
        """Recursive traversal of trace links."""
        if depth >= max_depth:
            return []

        key = (source_type, source_id)
        if key in visited:
            return []
        visited.add(key)

        links = self.get_links_from(source_type, source_id)
        nodes: list[TraceChainNode] = []

        for link in links:
            child_key = (link.target_type, str(link.target_id))
            if child_key in visited:
                continue

            children = self._traverse(
                link.target_type,
                str(link.target_id),
                depth + 1,
                max_depth,
                visited,
            )

            node = TraceChainNode(
                entity_type=link.target_type,
                entity_id=link.target_id,
                relationship=link.relationship,
                children=children,
            )
            nodes.append(node)

        return nodes

    def _compute_depth(self, nodes: list[TraceChainNode]) -> int:
        """Compute the maximum depth of a node tree."""
        if not nodes:
            return 0
        return 1 + max(self._compute_depth(n.children) for n in nodes)

    # -----------------------------------------------------------------
    # COVERAGE REPORT
    # -----------------------------------------------------------------

    def get_coverage_report(
        self, device_version_id: UUID | str, organization_id: UUID | str
    ) -> CoverageReport:
        """Generate a coverage report for a device version.

        For each claim, shows linked hazards, controls, tests, and evidence.
        """
        from src.persistence.twin_repository import get_twin_repository

        repo = get_twin_repository()
        dvid = str(device_version_id)

        report = CoverageReport(
            device_version_id=UUID(dvid),
        )

        # Get all claims for this device
        claims = repo.get_by_device_version("claims", dvid)
        report.total_claims = len(claims)

        for claim_row in claims:
            claim_id_str = claim_row.get("id", "")
            if not claim_id_str:
                continue

            claim_id = UUID(str(claim_id_str))
            coverage = self._get_claim_coverage(claim_id)
            report.claims.append(coverage)

            if (
                coverage.has_hazard_link
                and coverage.has_control_link
                and coverage.has_test_link
                and coverage.has_evidence_link
            ):
                report.claims_with_full_coverage += 1
            elif (
                coverage.has_hazard_link
                or coverage.has_control_link
                or coverage.has_test_link
                or coverage.has_evidence_link
            ):
                report.claims_with_partial_coverage += 1
            else:
                report.claims_with_no_coverage += 1

        if report.total_claims > 0:
            report.coverage_percentage = round(
                (report.claims_with_full_coverage / report.total_claims) * 100, 1
            )

        return report

    def _get_claim_coverage(self, claim_id: UUID) -> ClaimCoverage:
        """Get coverage details for a single claim."""
        coverage = ClaimCoverage(claim_id=claim_id)

        # Direct links from claim
        claim_links = self.get_links_from("claim", claim_id)

        for link in claim_links:
            if link.target_type == "hazard":
                coverage.hazards.append(link.target_id)
                coverage.has_hazard_link = True

                # Follow hazard → risk_control
                hazard_links = self.get_links_from("hazard", link.target_id)
                for hl in hazard_links:
                    if hl.target_type == "risk_control":
                        coverage.risk_controls.append(hl.target_id)
                        coverage.has_control_link = True

                        # Follow risk_control → tests
                        ctrl_links = self.get_links_from("risk_control", hl.target_id)
                        for cl in ctrl_links:
                            if cl.target_type == "verification_test":
                                coverage.verification_tests.append(cl.target_id)
                                coverage.has_test_link = True

                                # Follow test → evidence
                                test_links = self.get_links_from("verification_test", cl.target_id)
                                for tl in test_links:
                                    if tl.target_type == "evidence_item":
                                        coverage.evidence_items.append(tl.target_id)
                                        coverage.has_evidence_link = True

                            elif cl.target_type == "validation_test":
                                coverage.validation_tests.append(cl.target_id)
                                coverage.has_test_link = True

                                test_links = self.get_links_from("validation_test", cl.target_id)
                                for tl in test_links:
                                    if tl.target_type == "evidence_item":
                                        coverage.evidence_items.append(tl.target_id)
                                        coverage.has_evidence_link = True

            elif link.target_type == "evidence_item":
                coverage.evidence_items.append(link.target_id)
                coverage.has_evidence_link = True

        return coverage

    # -----------------------------------------------------------------
    # Internal helpers (compound queries)
    # -----------------------------------------------------------------

    def _query_links(
        self, field1: str, value1: str, field2: str, value2: str
    ) -> list[dict[str, Any]]:
        """Query trace_links with two field conditions.

        Uses Supabase .eq().eq() chaining or local psql WHERE clause.
        """
        if self._repo._use_supabase:
            return self._supabase_compound_query(field1, value1, field2, value2)
        return self._local_compound_query(field1, value1, field2, value2)

    def _supabase_compound_query(
        self, field1: str, value1: str, field2: str, value2: str
    ) -> list[dict[str, Any]]:
        """Supabase compound query on trace_links."""
        try:
            from src.persistence.supabase_client import get_supabase_client

            client = get_supabase_client()
            response = (
                client.table(self.TABLE).select("*").eq(field1, value1).eq(field2, value2).execute()
            )
            return response.data or []
        except Exception as exc:
            logger.warning("Supabase compound query failed: %s", exc)
            return []

    def _local_compound_query(
        self, field1: str, value1: str, field2: str, value2: str
    ) -> list[dict[str, Any]]:
        """Local Postgres compound query on trace_links."""
        try:
            import json as json_mod

            from src.persistence.twin_repository import _psql_query

            escaped1 = value1.replace("'", "''")
            escaped2 = value2.replace("'", "''")
            query = (
                f"SELECT row_to_json(t) FROM public.{self.TABLE} t "
                f"WHERE {field1} = '{escaped1}' AND {field2} = '{escaped2}';"
            )
            rows = _psql_query(query)
            results: list[dict[str, Any]] = [
                json_mod.loads(r.get("raw", "{}")) for r in rows if r.get("raw")
            ]
            return results
        except Exception as exc:
            logger.warning("Local compound query failed: %s", exc)
            return []


# =========================================================================
# Singleton
# =========================================================================

_engine: TraceabilityEngine | None = None


def get_traceability_engine() -> TraceabilityEngine:
    """Get or create the singleton TraceabilityEngine."""
    global _engine  # noqa: PLW0603
    if _engine is None:
        _engine = TraceabilityEngine()
    return _engine
