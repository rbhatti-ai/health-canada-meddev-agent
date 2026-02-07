"""
Persistence layer for Regulatory Twin entities.

CRUD operations for all 10 regulatory twin tables.
Follows the same best-effort pattern as ai_runs_logger.py:
  - Never crashes the app on DB failure
  - Returns None/empty on failure
  - Uses existing supabase_client.py

Also supports direct psycopg2 for local Postgres dev.

Sprint 1c — 2026-02-07
"""

from __future__ import annotations

import logging
import os
import subprocess
from typing import Any
from uuid import UUID

from src.core.regulatory_twin import (
    Claim,
    EvidenceItem,
    Harm,
    Hazard,
    IntendedUse,
    LabelingAsset,
    RegulatoryTwinBase,
    RiskControl,
    SubmissionTarget,
    ValidationTest,
    VerificationTest,
)
from src.persistence.supabase_client import get_supabase_client, is_supabase_available

logger = logging.getLogger(__name__)


# =========================================================================
# Local Postgres helper (for dev without Supabase)
# =========================================================================


def _psql_query(query: str) -> list[dict[str, Any]]:
    """Run a psql query and return rows as dicts. Dev-only helper."""
    try:
        result = subprocess.run(
            [
                "psql",
                "-U",
                os.getenv("PGUSER", "meddev"),
                "-d",
                os.getenv("PGDATABASE", "meddev_agent"),
                "-t",
                "-A",
                "-c",
                query,
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            logger.warning("psql error: %s", result.stderr.strip())
            return []
        return _parse_psql_output(result.stdout.strip(), query)
    except Exception as exc:
        logger.warning("psql failed: %s", exc)
        return []


def _parse_psql_output(output: str, query: str) -> list[dict[str, Any]]:
    """Parse psql -t -A output into list of dicts."""
    if not output:
        return []
    # For INSERT ... RETURNING, the output is pipe-delimited
    # For SELECT, same format
    rows = []
    for line in output.strip().split("\n"):
        if not line or line.startswith("("):
            continue
        rows.append(line)
    return [{"raw": row} for row in rows]


def _is_local_postgres_available() -> bool:
    """Check if local Postgres is available (for dev)."""
    try:
        result = subprocess.run(
            [
                "psql",
                "-U",
                os.getenv("PGUSER", "meddev"),
                "-d",
                os.getenv("PGDATABASE", "meddev_agent"),
                "-t",
                "-A",
                "-c",
                "SELECT 1;",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0 and result.stdout.strip() == "1"
    except Exception:
        return False


# =========================================================================
# Generic CRUD (works with any RegulatoryTwinBase subclass)
# =========================================================================


class TwinRepository:
    """Generic repository for all regulatory twin entities.

    Supports both Supabase (production) and local Postgres (dev).
    All operations are best-effort: never crash, return None on failure.
    """

    def __init__(self) -> None:
        self._use_supabase = is_supabase_available()
        self._use_local = not self._use_supabase and _is_local_postgres_available()

    @property
    def is_available(self) -> bool:
        """Check if any DB backend is available."""
        return self._use_supabase or self._use_local

    # -----------------------------------------------------------------
    # CREATE
    # -----------------------------------------------------------------

    def create(self, table: str, model: RegulatoryTwinBase) -> dict[str, Any] | None:
        """Insert a record. Returns the inserted row dict or None on failure."""
        if not self.is_available:
            logger.warning("No DB available for create on %s", table)
            return None

        data = model.to_db_dict()

        if self._use_supabase:
            return self._supabase_insert(table, data)
        return self._local_insert(table, data)

    # -----------------------------------------------------------------
    # READ (by ID)
    # -----------------------------------------------------------------

    def get_by_id(self, table: str, record_id: UUID | str) -> dict[str, Any] | None:
        """Get a single record by ID. Returns dict or None."""
        if not self.is_available:
            return None

        rid = str(record_id)
        if self._use_supabase:
            return self._supabase_get_by_id(table, rid)
        return self._local_get_by_id(table, rid)

    # -----------------------------------------------------------------
    # READ (filtered)
    # -----------------------------------------------------------------

    def get_by_org(self, table: str, organization_id: UUID | str) -> list[dict[str, Any]]:
        """Get all records for an organization."""
        if not self.is_available:
            return []

        oid = str(organization_id)
        if self._use_supabase:
            return self._supabase_get_by_field(table, "organization_id", oid)
        return self._local_get_by_field(table, "organization_id", oid)

    def get_by_device_version(
        self, table: str, device_version_id: UUID | str
    ) -> list[dict[str, Any]]:
        """Get all records for a device version."""
        if not self.is_available:
            return []

        dvid = str(device_version_id)
        if self._use_supabase:
            return self._supabase_get_by_field(table, "device_version_id", dvid)
        return self._local_get_by_field(table, "device_version_id", dvid)

    def get_by_field(self, table: str, field: str, value: str) -> list[dict[str, Any]]:
        """Get records matching a field value."""
        if not self.is_available:
            return []

        if self._use_supabase:
            return self._supabase_get_by_field(table, field, value)
        return self._local_get_by_field(table, field, value)

    # -----------------------------------------------------------------
    # UPDATE (by ID)
    # -----------------------------------------------------------------

    def update(
        self, table: str, record_id: UUID | str, updates: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update a record by ID. Returns updated row or None."""
        if not self.is_available:
            return None

        rid = str(record_id)
        # Convert UUID values to strings
        clean: dict[str, Any] = {}
        for k, v in updates.items():
            clean[k] = str(v) if isinstance(v, UUID) else v

        if self._use_supabase:
            return self._supabase_update(table, rid, clean)
        return self._local_update(table, rid, clean)

    # -----------------------------------------------------------------
    # COUNT
    # -----------------------------------------------------------------

    def count(self, table: str, organization_id: UUID | str | None = None) -> int:
        """Count records, optionally filtered by org."""
        if not self.is_available:
            return 0

        if self._use_supabase:
            return self._supabase_count(table, str(organization_id) if organization_id else None)
        return self._local_count(table, str(organization_id) if organization_id else None)

    # =================================================================
    # Supabase backend
    # =================================================================

    def _supabase_insert(self, table: str, data: dict[str, Any]) -> dict[str, Any] | None:
        try:
            sb = get_supabase_client()
            res = sb.table(table).insert(data).execute()
            rows = getattr(res, "data", None)
            return rows[0] if rows else None
        except Exception as exc:
            logger.warning("Supabase insert %s failed: %s", table, exc)
            return None

    def _supabase_get_by_id(self, table: str, rid: str) -> dict[str, Any] | None:
        try:
            sb = get_supabase_client()
            res = sb.table(table).select("*").eq("id", rid).execute()
            rows = getattr(res, "data", None)
            return rows[0] if rows else None
        except Exception as exc:
            logger.warning("Supabase get %s/%s failed: %s", table, rid, exc)
            return None

    def _supabase_get_by_field(self, table: str, field: str, value: str) -> list[dict[str, Any]]:
        try:
            sb = get_supabase_client()
            res = sb.table(table).select("*").eq(field, value).execute()
            return getattr(res, "data", None) or []
        except Exception as exc:
            logger.warning("Supabase query %s.%s failed: %s", table, field, exc)
            return []

    def _supabase_update(
        self, table: str, rid: str, updates: dict[str, Any]
    ) -> dict[str, Any] | None:
        try:
            sb = get_supabase_client()
            res = sb.table(table).update(updates).eq("id", rid).execute()
            rows = getattr(res, "data", None)
            return rows[0] if rows else None
        except Exception as exc:
            logger.warning("Supabase update %s/%s failed: %s", table, rid, exc)
            return None

    def _supabase_count(self, table: str, org_id: str | None) -> int:
        try:
            sb = get_supabase_client()
            q = sb.table(table).select("id", count="exact")
            if org_id:
                q = q.eq("organization_id", org_id)
            res = q.execute()
            return getattr(res, "count", 0) or 0
        except Exception as exc:
            logger.warning("Supabase count %s failed: %s", table, exc)
            return 0

    # =================================================================
    # Local Postgres backend (dev only)
    # =================================================================

    def _local_insert(self, table: str, data: dict[str, Any]) -> dict[str, Any] | None:
        try:
            import json as json_mod

            cols = ", ".join(data.keys())
            vals = []
            for v in data.values():
                if isinstance(v, list | dict):
                    vals.append(f"'{json_mod.dumps(v)}'::jsonb")
                elif isinstance(v, str):
                    escaped = v.replace("'", "''")
                    vals.append(f"'{escaped}'")
                elif isinstance(v, bool):
                    vals.append("true" if v else "false")
                elif v is None:
                    vals.append("NULL")
                else:
                    vals.append(str(v))

            vals_str = ", ".join(vals)
            query = f"INSERT INTO public.{table} ({cols}) VALUES ({vals_str}) RETURNING id;"
            rows = _psql_query(query)
            if rows:
                return {"id": rows[0].get("raw", ""), **data}
            return None
        except Exception as exc:
            logger.warning("Local insert %s failed: %s", table, exc)
            return None

    def _local_get_by_id(self, table: str, rid: str) -> dict[str, Any] | None:
        try:
            query = f"SELECT row_to_json(t) FROM public.{table} t WHERE id = '{rid}';"
            rows = _psql_query(query)
            if rows:
                import json as json_mod

                result: dict[str, Any] = json_mod.loads(rows[0].get("raw", "{}"))
                return result
            return None
        except Exception as exc:
            logger.warning("Local get %s/%s failed: %s", table, rid, exc)
            return None

    def _local_get_by_field(self, table: str, field: str, value: str) -> list[dict[str, Any]]:
        try:
            import json as json_mod

            query = f"SELECT row_to_json(t) FROM public.{table} t " f"WHERE {field} = '{value}';"
            rows = _psql_query(query)
            results: list[dict[str, Any]] = [
                json_mod.loads(r.get("raw", "{}")) for r in rows if r.get("raw")
            ]
            return results
        except Exception as exc:
            logger.warning("Local query %s.%s failed: %s", table, field, exc)
            return []

    def _local_update(self, table: str, rid: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        try:
            set_parts = []
            for k, v in updates.items():
                if isinstance(v, str):
                    escaped = v.replace("'", "''")
                    set_parts.append(f"{k} = '{escaped}'")
                elif v is None:
                    set_parts.append(f"{k} = NULL")
                else:
                    set_parts.append(f"{k} = {v}")
            set_str = ", ".join(set_parts)
            query = f"UPDATE public.{table} SET {set_str} WHERE id = '{rid}' RETURNING id;"
            rows = _psql_query(query)
            return {"id": rid, **updates} if rows else None
        except Exception as exc:
            logger.warning("Local update %s/%s failed: %s", table, rid, exc)
            return None

    def _local_count(self, table: str, org_id: str | None) -> int:
        try:
            where = f" WHERE organization_id = '{org_id}'" if org_id else ""
            query = f"SELECT COUNT(*) FROM public.{table}{where};"
            rows = _psql_query(query)
            if rows:
                return int(rows[0].get("raw", "0"))
            return 0
        except Exception as exc:
            logger.warning("Local count %s failed: %s", table, exc)
            return 0


# =========================================================================
# Convenience functions (typed wrappers)
# =========================================================================

_repo: TwinRepository | None = None


def get_twin_repository() -> TwinRepository:
    """Get or create the singleton repository."""
    global _repo  # noqa: PLW0603
    if _repo is None:
        _repo = TwinRepository()
    return _repo


# ----- IntendedUse -----
def create_intended_use(model: IntendedUse) -> dict[str, Any] | None:
    return get_twin_repository().create("intended_uses", model)


def get_intended_uses_for_device(device_version_id: UUID | str) -> list[dict[str, Any]]:
    return get_twin_repository().get_by_device_version("intended_uses", device_version_id)


# ----- Claim -----
def create_claim(model: Claim) -> dict[str, Any] | None:
    return get_twin_repository().create("claims", model)


def get_claims_for_device(device_version_id: UUID | str) -> list[dict[str, Any]]:
    return get_twin_repository().get_by_device_version("claims", device_version_id)


# ----- Hazard -----
def create_hazard(model: Hazard) -> dict[str, Any] | None:
    return get_twin_repository().create("hazards", model)


def get_hazards_for_device(device_version_id: UUID | str) -> list[dict[str, Any]]:
    return get_twin_repository().get_by_device_version("hazards", device_version_id)


# ----- Harm -----
def create_harm(model: Harm) -> dict[str, Any] | None:
    return get_twin_repository().create("harms", model)


def get_harms_for_hazard(hazard_id: UUID | str) -> list[dict[str, Any]]:
    return get_twin_repository().get_by_field("harms", "hazard_id", str(hazard_id))


# ----- RiskControl -----
def create_risk_control(model: RiskControl) -> dict[str, Any] | None:
    return get_twin_repository().create("risk_controls", model)


def get_risk_controls_for_hazard(hazard_id: UUID | str) -> list[dict[str, Any]]:
    return get_twin_repository().get_by_field("risk_controls", "hazard_id", str(hazard_id))


# ----- VerificationTest -----
def create_verification_test(model: VerificationTest) -> dict[str, Any] | None:
    return get_twin_repository().create("verification_tests", model)


def get_verification_tests_for_device(device_version_id: UUID | str) -> list[dict[str, Any]]:
    return get_twin_repository().get_by_device_version("verification_tests", device_version_id)


# ----- ValidationTest -----
def create_validation_test(model: ValidationTest) -> dict[str, Any] | None:
    return get_twin_repository().create("validation_tests", model)


def get_validation_tests_for_device(device_version_id: UUID | str) -> list[dict[str, Any]]:
    return get_twin_repository().get_by_device_version("validation_tests", device_version_id)


# ----- EvidenceItem -----
def create_evidence_item(model: EvidenceItem) -> dict[str, Any] | None:
    return get_twin_repository().create("evidence_items", model)


def get_evidence_items_for_device(device_version_id: UUID | str) -> list[dict[str, Any]]:
    return get_twin_repository().get_by_device_version("evidence_items", device_version_id)


# ----- LabelingAsset -----
def create_labeling_asset(model: LabelingAsset) -> dict[str, Any] | None:
    return get_twin_repository().create("labeling_assets", model)


def get_labeling_assets_for_device(device_version_id: UUID | str) -> list[dict[str, Any]]:
    return get_twin_repository().get_by_device_version("labeling_assets", device_version_id)


# ----- SubmissionTarget -----
def create_submission_target(model: SubmissionTarget) -> dict[str, Any] | None:
    return get_twin_repository().create("submission_targets", model)


def get_submission_targets_for_device(device_version_id: UUID | str) -> list[dict[str, Any]]:
    return get_twin_repository().get_by_device_version("submission_targets", device_version_id)
