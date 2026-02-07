"""
Unit and integration tests for the Regulatory Twin Core Entities migration.

Tests validate:
  - File existence and structure
  - All 10 tables created with correct columns
  - CHECK constraints on status/type/severity fields
  - Versioning columns (version, supersedes_id) on all mutable tables
  - Organization scoping (organization_id on all tables)
  - RLS enablement on all 10 tables
  - Supabase auth guard pattern
  - EXECUTE $pol$ pattern for policies
  - Idempotency (IF NOT EXISTS, DROP POLICY IF EXISTS)
  - SQL safety (no DROP TABLE, TRUNCATE, DELETE FROM, GRANT ALL)
  - Index creation
  - Transaction wrapper (BEGIN/COMMIT)

Migration: scripts/migrations/2026-02-07_regulatory_twin_core.sql
"""

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
MIGRATION_FILE = REPO_ROOT / "scripts" / "migrations" / "2026-02-07_regulatory_twin_core.sql"

TWIN_TABLES = [
    "intended_uses",
    "claims",
    "hazards",
    "harms",
    "risk_controls",
    "verification_tests",
    "validation_tests",
    "evidence_items",
    "labeling_assets",
    "submission_targets",
]

VERSIONED_TABLES = [
    "intended_uses",
    "claims",
    "hazards",
    "risk_controls",
    "verification_tests",
    "validation_tests",
    "evidence_items",
    "labeling_assets",
]

STATUS_TABLES = [
    "claims",
    "evidence_items",
    "labeling_assets",
    "submission_targets",
    "risk_controls",
]


@pytest.fixture(scope="module")
def migration_content() -> str:
    """Read migration file content once for the module."""
    assert MIGRATION_FILE.exists(), f"Migration file not found: {MIGRATION_FILE}"
    return MIGRATION_FILE.read_text()


def psql(query: str) -> str:
    """Run a psql query against local dev DB."""
    try:
        result = subprocess.run(
            ["psql", "-U", "meddev", "-d", "meddev_agent", "-t", "-A", "-c", query],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip()
    except Exception:
        return ""


@pytest.mark.unit
class TestMigrationFileExists:
    def test_migration_file_exists(self):
        assert MIGRATION_FILE.exists()

    def test_migration_file_not_empty(self, migration_content: str):
        assert len(migration_content) > 1000

    def test_starts_with_comment_header(self, migration_content: str):
        assert migration_content.strip().startswith("--")


@pytest.mark.unit
class TestTableCreation:
    @pytest.mark.parametrize("table", TWIN_TABLES)
    def test_table_creation_statement(self, migration_content: str, table: str):
        pattern = f"CREATE TABLE IF NOT EXISTS public.{table}"
        assert pattern in migration_content, f"Missing: {pattern}"

    def test_table_count(self, migration_content: str):
        count = migration_content.count("CREATE TABLE IF NOT EXISTS public.")
        assert count == 10, f"Expected 10 CREATE TABLE statements, got {count}"


@pytest.mark.unit
class TestOrganizationScoping:
    @pytest.mark.parametrize("table", TWIN_TABLES)
    def test_org_id_column(self, migration_content: str, table: str):
        table_start = migration_content.find(f"public.{table}")
        assert table_start != -1
        next_table = migration_content.find("CREATE TABLE", table_start + 1)
        if next_table == -1:
            next_table = len(migration_content)
        table_block = migration_content[table_start:next_table]
        assert "organization_id" in table_block, f"Table {table} missing organization_id"

    def test_org_fk_references(self, migration_content: str):
        count = migration_content.count("REFERENCES public.organizations(id) ON DELETE CASCADE")
        assert count >= 10, f"Expected >=10 org FK references, got {count}"


@pytest.mark.unit
class TestVersioning:
    @pytest.mark.parametrize("table", VERSIONED_TABLES)
    def test_version_column(self, migration_content: str, table: str):
        table_start = migration_content.find(f"public.{table}")
        next_table = migration_content.find("CREATE TABLE", table_start + 1)
        if next_table == -1:
            next_table = len(migration_content)
        table_block = migration_content[table_start:next_table]
        assert "version" in table_block, f"Table {table} missing version column"

    @pytest.mark.parametrize("table", VERSIONED_TABLES)
    def test_supersedes_id_column(self, migration_content: str, table: str):
        table_start = migration_content.find(f"public.{table}")
        next_table = migration_content.find("CREATE TABLE", table_start + 1)
        if next_table == -1:
            next_table = len(migration_content)
        table_block = migration_content[table_start:next_table]
        assert "supersedes_id" in table_block, f"Table {table} missing supersedes_id column"

    @pytest.mark.parametrize("table", VERSIONED_TABLES)
    def test_version_default(self, migration_content: str, table: str):
        table_start = migration_content.find(f"public.{table}")
        next_table = migration_content.find("CREATE TABLE", table_start + 1)
        if next_table == -1:
            next_table = len(migration_content)
        table_block = migration_content[table_start:next_table]
        assert "DEFAULT 1" in table_block, f"Table {table} version column missing DEFAULT 1"


@pytest.mark.unit
class TestCreatedByAudit:
    @pytest.mark.parametrize("table", TWIN_TABLES)
    def test_created_by_column(self, migration_content: str, table: str):
        table_start = migration_content.find(f"public.{table}")
        next_table = migration_content.find("CREATE TABLE", table_start + 1)
        if next_table == -1:
            next_table = len(migration_content)
        table_block = migration_content[table_start:next_table]
        assert "created_by" in table_block, f"Table {table} missing created_by column"


@pytest.mark.unit
class TestCheckConstraints:
    def test_claims_status_constraint(self, migration_content: str):
        assert "claims_status_chk" in migration_content

    def test_claims_type_constraint(self, migration_content: str):
        assert "claims_type_chk" in migration_content

    def test_hazards_category_constraint(self, migration_content: str):
        assert "hazards_category_chk" in migration_content

    def test_hazards_severity_constraint(self, migration_content: str):
        assert "hazards_severity_chk" in migration_content

    def test_hazards_probability_constraint(self, migration_content: str):
        assert "hazards_probability_chk" in migration_content

    def test_hazards_risk_level_pre_constraint(self, migration_content: str):
        assert "hazards_risk_level_pre_chk" in migration_content

    def test_harms_type_constraint(self, migration_content: str):
        assert "harms_type_chk" in migration_content

    def test_harms_severity_constraint(self, migration_content: str):
        assert "harms_severity_chk" in migration_content

    def test_risk_controls_type_constraint(self, migration_content: str):
        assert "risk_controls_type_chk" in migration_content

    def test_risk_controls_impl_constraint(self, migration_content: str):
        assert "risk_controls_impl_chk" in migration_content

    def test_verification_tests_type_constraint(self, migration_content: str):
        assert "vt_type_chk" in migration_content

    def test_verification_tests_pass_fail_constraint(self, migration_content: str):
        assert "vt_pass_fail_chk" in migration_content

    def test_validation_tests_type_constraint(self, migration_content: str):
        assert "val_type_chk" in migration_content

    def test_evidence_items_type_constraint(self, migration_content: str):
        assert "ei_type_chk" in migration_content

    def test_evidence_items_strength_constraint(self, migration_content: str):
        assert "ei_strength_chk" in migration_content

    def test_evidence_items_status_constraint(self, migration_content: str):
        assert "ei_status_chk" in migration_content

    def test_labeling_assets_type_constraint(self, migration_content: str):
        assert "la_type_chk" in migration_content

    def test_labeling_assets_status_constraint(self, migration_content: str):
        assert "la_status_chk" in migration_content

    def test_labeling_assets_market_constraint(self, migration_content: str):
        assert "la_market_chk" in migration_content

    def test_submission_targets_body_constraint(self, migration_content: str):
        assert "st_body_chk" in migration_content

    def test_submission_targets_type_constraint(self, migration_content: str):
        assert "st_type_chk" in migration_content

    def test_submission_targets_status_constraint(self, migration_content: str):
        assert "st_status_chk" in migration_content


@pytest.mark.unit
class TestRiskManagementChain:
    def test_harms_reference_hazards(self, migration_content: str):
        assert "REFERENCES public.hazards(id)" in migration_content

    def test_risk_controls_reference_hazards(self, migration_content: str):
        rc_start = migration_content.find("public.risk_controls")
        rc_block = migration_content[rc_start : rc_start + 2000]
        assert "REFERENCES public.hazards(id)" in rc_block

    def test_evidence_items_reference_artifacts(self, migration_content: str):
        ei_start = migration_content.find("public.evidence_items")
        ei_block = migration_content[ei_start : ei_start + 2000]
        assert "REFERENCES public.artifacts(id)" in ei_block


@pytest.mark.unit
class TestIndexCreation:
    @pytest.mark.parametrize("table", TWIN_TABLES)
    def test_org_index(self, migration_content: str, table: str):
        pattern = f"idx_{table}_org"
        assert pattern in migration_content, f"Missing org index: {pattern}"

    def test_total_index_count(self, migration_content: str):
        count = migration_content.count("CREATE INDEX IF NOT EXISTS")
        assert count >= 25, f"Expected >=25 indexes, got {count}"


@pytest.mark.unit
class TestRLSStatements:
    @pytest.mark.parametrize("table", TWIN_TABLES)
    def test_rls_enabled(self, migration_content: str, table: str):
        pattern = f"ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY"
        assert pattern in migration_content, f"Missing RLS: {pattern}"

    def test_rls_enable_count(self, migration_content: str):
        count = migration_content.count("ENABLE ROW LEVEL SECURITY")
        assert count == 10, f"Expected 10 ENABLE RLS statements, got {count}"


@pytest.mark.unit
class TestAuthGuardAndExecute:
    def test_auth_guard_present(self, migration_content: str):
        assert "to_regprocedure('auth.uid()')" in migration_content

    def test_guard_checks_not_null(self, migration_content: str):
        assert "IS NOT NULL" in migration_content

    def test_guard_skip_notice(self, migration_content: str):
        assert "skipping policy creation" in migration_content

    def test_uses_execute_keyword(self, migration_content: str):
        assert "EXECUTE" in migration_content

    def test_uses_pol_dollar_quoting(self, migration_content: str):
        assert "$pol$" in migration_content

    def test_execute_count(self, migration_content: str):
        count = migration_content.count("EXECUTE $pol$")
        assert count >= 50, f"Expected >=50 EXECUTE $pol$ calls, got {count}"


@pytest.mark.unit
class TestPolicyCoverage:
    @pytest.mark.parametrize("table", TWIN_TABLES)
    def test_select_policy(self, migration_content: str, table: str):
        pattern = f"{table}_select_org"
        assert pattern in migration_content, f"Missing SELECT policy: {pattern}"

    @pytest.mark.parametrize("table", TWIN_TABLES)
    def test_insert_policy(self, migration_content: str, table: str):
        pattern = f"{table}_insert_org"
        assert pattern in migration_content, f"Missing INSERT policy: {pattern}"

    @pytest.mark.parametrize("table", VERSIONED_TABLES)
    def test_update_policy_for_versioned(self, migration_content: str, table: str):
        pattern = f"{table}_update_org"
        assert pattern in migration_content, f"Missing UPDATE policy: {pattern}"


@pytest.mark.unit
class TestInsertGuards:
    def test_created_by_guard_count(self, migration_content: str):
        count = migration_content.count("created_by IS NULL OR created_by = auth.uid()")
        assert count >= 10, f"Expected >=10 created_by guards on INSERT policies, got {count}"


@pytest.mark.unit
class TestOrgScopingPattern:
    def test_uses_users_org_id(self, migration_content: str):
        assert "u.organization_id FROM public.users u WHERE u.id = auth.uid()" in (
            migration_content
        )

    def test_no_org_members(self, migration_content: str):
        policy_start = migration_content.find("ENABLE ROW LEVEL SECURITY")
        policy_section = migration_content[policy_start:]
        assert "org_members" not in policy_section


@pytest.mark.unit
class TestTransactionWrapper:
    def test_has_begin(self, migration_content: str):
        assert "BEGIN" in migration_content

    def test_has_commit(self, migration_content: str):
        assert "COMMIT" in migration_content


@pytest.mark.unit
class TestSQLSafety:
    def test_no_drop_table(self, migration_content: str):
        assert "DROP TABLE" not in migration_content

    def test_no_truncate(self, migration_content: str):
        assert "TRUNCATE" not in migration_content

    def test_no_delete_from(self, migration_content: str):
        assert "DELETE FROM" not in migration_content

    def test_no_grant_all(self, migration_content: str):
        assert "GRANT ALL" not in migration_content


@pytest.mark.unit
class TestIdempotency:
    def test_create_table_if_not_exists(self, migration_content: str):
        creates = migration_content.count("CREATE TABLE IF NOT EXISTS")
        raw_creates = migration_content.count("CREATE TABLE ")
        assert creates == raw_creates, "Some CREATE TABLE missing IF NOT EXISTS"

    def test_create_index_if_not_exists(self, migration_content: str):
        creates = migration_content.count("CREATE INDEX IF NOT EXISTS")
        raw_creates = migration_content.count("CREATE INDEX ")
        assert creates == raw_creates, "Some CREATE INDEX missing IF NOT EXISTS"

    def test_drop_policy_if_exists(self, migration_content: str):
        drops = migration_content.count("DROP POLICY IF EXISTS")
        assert drops >= 20, f"Expected >=20 DROP POLICY IF EXISTS, got {drops}"


@pytest.mark.unit
class TestVerificationBlock:
    def test_verification_notice(self, migration_content: str):
        assert "[RLS-VERIFY]" in migration_content

    def test_counts_twin_tables(self, migration_content: str):
        assert "Regulatory Twin tables with RLS enabled" in migration_content


@pytest.mark.unit
class TestDomainContent:
    def test_hazard_categories_include_cybersecurity(self, migration_content: str):
        assert "'cybersecurity'" in migration_content

    def test_risk_control_types_iso14971(self, migration_content: str):
        assert "'inherent_safety'" in migration_content
        assert "'protective_measure'" in migration_content
        assert "'information_for_safety'" in migration_content

    def test_evidence_types_comprehensive(self, migration_content: str):
        assert "'test_report'" in migration_content
        assert "'literature_review'" in migration_content
        assert "'clinical_data'" in migration_content
        assert "'predicate_comparison'" in migration_content

    def test_regulatory_bodies(self, migration_content: str):
        assert "'health_canada'" in migration_content
        assert "'fda'" in migration_content
        assert "'eu_mdr'" in migration_content

    def test_submission_types(self, migration_content: str):
        assert "'mdl'" in migration_content
        assert "'510k'" in migration_content
        assert "'de_novo'" in migration_content
        assert "'ce_mark'" in migration_content

    def test_severity_levels_iso14971(self, migration_content: str):
        assert "'negligible'" in migration_content
        assert "'marginal'" in migration_content
        assert "'critical'" in migration_content
        assert "'catastrophic'" in migration_content


@pytest.mark.integration
@pytest.mark.skipif(
    (
        subprocess.run(
            ["psql", "-U", "meddev", "-d", "meddev_agent", "-c", "SELECT 1"],
            capture_output=True,
            timeout=3,
        ).returncode
        != 0
        if shutil.which("psql")
        else True
    ),
    reason="Local Postgres not available",
)
class TestLocalPostgresState:
    @pytest.mark.parametrize("table", TWIN_TABLES)
    def test_table_exists(self, table: str):
        result = psql(
            f"SELECT COUNT(*) FROM pg_tables " f"WHERE schemaname='public' AND tablename='{table}';"
        )
        assert result == "1", f"Table {table} does not exist in local Postgres"

    @pytest.mark.parametrize("table", TWIN_TABLES)
    def test_rls_enabled(self, table: str):
        result = psql(
            f"SELECT rowsecurity FROM pg_tables "
            f"WHERE schemaname='public' AND tablename='{table}';"
        )
        assert result == "t", f"RLS not enabled on {table}: got '{result}'"

    def test_no_policies_locally(self):
        tables_str = ", ".join(f"'{t}'" for t in TWIN_TABLES)
        result = psql(
            f"SELECT COUNT(*) FROM pg_policies "
            f"WHERE schemaname='public' AND tablename IN ({tables_str});"
        )
        assert result == "0", f"Expected 0 policies locally for twin tables, got {result}"

    def test_total_rls_tables_in_db(self):
        result = psql(
            "SELECT COUNT(*) FROM pg_tables " "WHERE schemaname='public' AND rowsecurity=true;"
        )
        count = int(result) if result else 0
        assert count >= 19, f"Expected >=19 RLS-enabled tables total, got {count}"
