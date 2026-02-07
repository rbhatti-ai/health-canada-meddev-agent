"""
Tests for RLS migration: artifacts, artifact_links, attestations policies.

Tests validate:
- Migration SQL file exists and is well-formed
- Idempotency patterns (DROP IF EXISTS, IF NOT EXISTS)
- Auth guard pattern (to_regprocedure check)
- All 9 org-scoped tables covered with ENABLE RLS
- SELECT + INSERT policies for all evidence tables
- Org scoping via users.organization_id (NOT org_members)
- EXECUTE $pol$ dynamic SQL pattern (matches ai_runs migration)
- created_by / attested_by guards on INSERT policies
- SQL safety (no DROP TABLE, TRUNCATE, DELETE, GRANT ALL)
- Clean file structure (no shell artifacts)
- Integration: local Postgres RLS flags correct after migration
- Integration: 0 policies in local Postgres (no auth.uid())
"""

import subprocess
from pathlib import Path

import pytest

# =============================================================================
# Migration file path
# =============================================================================

MIGRATION_FILE = Path(__file__).parent.parent.parent / (
    "scripts/migrations/2026-02-06_rls_policies_artifacts_attestations.sql"
)
SCHEMA_FILE = Path(__file__).parent.parent.parent / "scripts/supabase_schema_v0.sql"


# =============================================================================
# FILE EXISTENCE + STRUCTURE
# =============================================================================


@pytest.mark.unit
class TestMigrationFileExists:
    """Verify migration file is present and non-empty."""

    def test_migration_file_exists(self) -> None:
        assert MIGRATION_FILE.exists(), f"Missing migration: {MIGRATION_FILE}"

    def test_migration_file_not_empty(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert len(content) > 100, "Migration file appears too short"


# =============================================================================
# IDEMPOTENCY PATTERNS
# =============================================================================


@pytest.mark.unit
class TestMigrationIdempotency:
    """Migration must be safe to run multiple times."""

    def test_uses_drop_policy_if_exists(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert (
            "DROP POLICY IF EXISTS" in content
        ), "Migration must use DROP POLICY IF EXISTS for idempotency"

    def test_uses_create_extension_if_not_exists(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert "CREATE EXTENSION IF NOT EXISTS" in content

    def test_no_shell_heredoc_text(self) -> None:
        """Migration must not contain accidental shell text."""
        content = MIGRATION_FILE.read_text()
        assert "cat >" not in content, "Shell heredoc text found in SQL file"
        assert "<<'SQL'" not in content, "Shell heredoc delimiter found in SQL file"
        assert "<<SQL" not in content, "Shell heredoc delimiter found in SQL file"


# =============================================================================
# AUTH GUARD PATTERN
# =============================================================================


@pytest.mark.unit
class TestAuthGuardPattern:
    """Policies must only be created when auth.uid() exists (Supabase)."""

    def test_contains_auth_guard(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert (
            "to_regprocedure" in content
        ), "Migration must guard policy creation with to_regprocedure check"

    def test_guard_checks_auth_uid(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert "auth.uid()" in content, "Migration must reference auth.uid() for Supabase guard"

    def test_guard_skips_when_null(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert "IS NULL" in content, "Guard must check IS NULL to skip in local Postgres"


# =============================================================================
# TABLE COVERAGE
# =============================================================================


@pytest.mark.unit
class TestRLSTableCoverage:
    """All org-scoped tables must have RLS enabled in migration."""

    REQUIRED_RLS_TABLES = [
        "organizations",
        "org_members",
        "products",
        "device_versions",
        "ai_runs",
        "trace_links",
        "artifacts",
        "artifact_links",
        "attestations",
    ]

    def test_rls_enabled_for_all_org_tables(self) -> None:
        content = MIGRATION_FILE.read_text()
        for table in self.REQUIRED_RLS_TABLES:
            assert (
                f"public.{table}" in content and "ENABLE ROW LEVEL SECURITY" in content
            ), f"RLS must be enabled for {table}"

    def test_enable_rls_statements_count(self) -> None:
        content = MIGRATION_FILE.read_text()
        count = content.count("ENABLE ROW LEVEL SECURITY")
        assert count >= 9, f"Expected at least 9 ENABLE RLS statements, found {count}"


# =============================================================================
# POLICY COVERAGE (evidence tables)
# =============================================================================


@pytest.mark.unit
class TestPolicyCoverage:
    """Verify policies exist for artifacts, artifact_links, attestations."""

    EVIDENCE_TABLES = ["artifacts", "artifact_links", "attestations"]

    def test_select_policies_for_evidence_tables(self) -> None:
        content = MIGRATION_FILE.read_text()
        for table in self.EVIDENCE_TABLES:
            assert f'"{table}_select_org"' in content, f"Missing SELECT policy for {table}"

    def test_insert_policies_for_evidence_tables(self) -> None:
        content = MIGRATION_FILE.read_text()
        for table in self.EVIDENCE_TABLES:
            assert f'"{table}_insert_org"' in content, f"Missing INSERT policy for {table}"

    def test_ai_runs_policies_present(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert '"ai_runs_select_org"' in content
        assert '"ai_runs_insert_org"' in content

    def test_trace_links_policies_present(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert '"trace_links_select_org"' in content
        assert '"trace_links_insert_org"' in content


# =============================================================================
# POLICY PATTERN (org scoping via users.organization_id)
# =============================================================================


@pytest.mark.unit
class TestPolicyOrgScopingPattern:
    """All policies must scope via users.organization_id per handoff decision."""

    def test_uses_users_organization_id(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert "u.organization_id" in content, "Policies must scope via users.organization_id"

    def test_uses_auth_uid_in_policies(self) -> None:
        content = MIGRATION_FILE.read_text()
        # Count occurrences of auth.uid() inside policy definitions
        count = content.count("auth.uid()")
        # At minimum: guard + multiple policy references
        assert (
            count >= 5
        ), f"Expected auth.uid() used in multiple policies, found {count} occurrences"

    def test_no_org_members_in_policies(self) -> None:
        """Per handoff decision: use users.organization_id, NOT org_members."""
        content = MIGRATION_FILE.read_text()
        # Policies should NOT reference org_members for scoping
        # (org_members is the future pattern, not current)
        policy_section = content.split("STEP 2")[1] if "STEP 2" in content else content
        # This is a soft check — we look for org_members in SELECT subqueries
        # within policy definitions. It's OK if org_members appears in
        # ENABLE RLS statements.
        lines_with_org_members = [
            line
            for line in policy_section.split("\n")
            if "org_members" in line and "SELECT" in line
        ]
        assert (
            len(lines_with_org_members) == 0
        ), "Policies should use users.organization_id, not org_members (per handoff)"

    def test_direct_org_id_for_artifact_links(self) -> None:
        """artifact_links has its own organization_id — must use direct scoping."""
        content = MIGRATION_FILE.read_text()
        # Find the artifact_links policy section
        al_start = content.find("ARTIFACT_LINKS")
        att_start = content.find("ATTESTATIONS")
        if al_start > 0 and att_start > al_start:
            al_section = content[al_start:att_start]
            # Should NOT contain nested subquery through artifacts table
            assert (
                "FROM public.artifacts" not in al_section
            ), "artifact_links should use direct organization_id, not nested through artifacts"

    def test_direct_org_id_for_attestations(self) -> None:
        """attestations has its own organization_id — must use direct scoping."""
        content = MIGRATION_FILE.read_text()
        # Find the attestations policy section
        att_start = content.find("ATTESTATIONS")
        ai_start = content.find("AI_RUNS", att_start) if att_start > 0 else -1
        if att_start > 0 and ai_start > att_start:
            att_section = content[att_start:ai_start]
            # Should NOT contain nested subquery through artifacts table
            assert (
                "FROM public.artifacts" not in att_section
            ), "attestations should use direct organization_id, not nested through artifacts"


# =============================================================================
# EXECUTE $pol$ PATTERN (matches ai_runs migration style)
# =============================================================================


@pytest.mark.unit
class TestExecutePolPattern:
    """Migration must use EXECUTE $pol$...$pol$ dynamic SQL for policies."""

    def test_uses_execute_keyword(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert "EXECUTE" in content, "Migration must use EXECUTE for dynamic policy SQL"

    def test_uses_pol_dollar_quoting(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert (
            "$pol$" in content
        ), "Migration must use $pol$ dollar-quoting (matches ai_runs pattern)"

    def test_execute_count_matches_policy_count(self) -> None:
        """Each policy should be created via EXECUTE $pol$."""
        content = MIGRATION_FILE.read_text()
        execute_count = content.count("EXECUTE $pol$")
        # At minimum: 5 tables x 2 policies (select+insert) = 10, plus UPDATE for artifacts
        assert (
            execute_count >= 10
        ), f"Expected at least 10 EXECUTE $pol$ blocks, found {execute_count}"


# =============================================================================
# INSERT POLICY GUARDS (created_by / attested_by)
# =============================================================================


@pytest.mark.unit
class TestInsertPolicyGuards:
    """INSERT policies must guard user identity columns."""

    def test_artifacts_insert_guards_created_by(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert (
            "created_by IS NULL OR created_by = auth.uid()" in content
        ), "artifacts INSERT policy must guard created_by"

    def test_attestations_insert_guards_attested_by(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert (
            "attested_by IS NULL OR attested_by = auth.uid()" in content
        ), "attestations INSERT policy must guard attested_by"

    def test_ai_runs_insert_guards_user_id(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert (
            "user_id IS NULL OR user_id = auth.uid()" in content
        ), "ai_runs INSERT policy must guard user_id"


# =============================================================================
# TRANSACTION WRAPPER
# =============================================================================


@pytest.mark.unit
class TestTransactionWrapper:
    """Migration should use BEGIN/COMMIT for atomicity."""

    def test_has_begin(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert "BEGIN;" in content, "Migration should wrap in BEGIN transaction"

    def test_has_commit(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert "COMMIT;" in content, "Migration should end with COMMIT"


# =============================================================================
# SQL SYNTAX SAFETY
# =============================================================================


@pytest.mark.unit
class TestSQLSafety:
    """SQL file must not contain dangerous patterns."""

    def test_no_drop_table(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert "DROP TABLE" not in content, "Migration must not DROP tables"

    def test_no_truncate(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert "TRUNCATE" not in content, "Migration must not TRUNCATE tables"

    def test_no_delete_from(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert "DELETE FROM" not in content, "Migration must not DELETE data"

    def test_no_grant_all(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert "GRANT ALL" not in content, "Migration must not GRANT ALL"

    def test_starts_with_comment_header(self) -> None:
        content = MIGRATION_FILE.read_text()
        assert content.strip().startswith("--"), "Migration should start with a comment header"

    def test_head_and_tail_clean(self) -> None:
        """First and last lines must be valid SQL (no shell artifacts)."""
        content = MIGRATION_FILE.read_text()
        lines = [line.strip() for line in content.strip().split("\n") if line.strip()]
        first = lines[0]
        last = lines[-1]
        assert (
            first.startswith("--") or first.startswith("CREATE") or first.startswith("ALTER")
        ), f"Unexpected first line: {first}"
        assert (
            last.endswith(";") or last.endswith("$$;") or last.startswith("--")
        ), f"Unexpected last line: {last}"


# =============================================================================
# LOCAL POSTGRES INTEGRATION (optional, skipped if psql unavailable)
# =============================================================================


@pytest.mark.integration
class TestLocalPostgresRLSState:
    """Verify RLS state in local Postgres after migration."""

    @staticmethod
    def _psql(query: str) -> str:
        """Run psql query against local dev DB. Skip if unavailable."""
        try:
            result = subprocess.run(
                ["psql", "-U", "meddev", "-d", "meddev_agent", "-t", "-A", "-c", query],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                pytest.skip(f"psql not available or DB not running: {result.stderr}")
            return result.stdout.strip()
        except FileNotFoundError:
            pytest.skip("psql not found on PATH")
        except subprocess.TimeoutExpired:
            pytest.skip("psql timed out")

    def test_rls_enabled_on_org_scoped_tables(self) -> None:
        """After migration, all org-scoped tables should have RLS enabled."""
        tables = [
            "organizations",
            "org_members",
            "products",
            "device_versions",
            "ai_runs",
            "trace_links",
            "artifacts",
            "artifact_links",
            "attestations",
        ]
        for table in tables:
            result = self._psql(
                f"SELECT rowsecurity FROM pg_tables "
                f"WHERE schemaname='public' AND tablename='{table}';"
            )
            assert result == "t", f"RLS not enabled on {table}: got '{result}'"

    def test_no_policies_in_local_postgres(self) -> None:
        """Local Postgres (no auth schema) should have 0 policies."""
        result = self._psql("SELECT COUNT(*) FROM pg_policies WHERE schemaname='public';")
        assert result == "0", f"Expected 0 policies in local Postgres (no auth.uid()), got {result}"
