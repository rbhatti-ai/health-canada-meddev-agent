"""
Unit tests for Supabase foundation.

Tests:
1. Config loads Supabase env vars correctly
2. SQL schema file exists and contains expected table definitions
3. Supabase client module handles missing config gracefully
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest


class TestSupabaseConfig:
    """Tests for Supabase configuration in settings."""

    def test_supabase_config_fields_exist(self):
        """Verify Supabase config fields are defined in Settings class."""
        from configs.settings import Settings

        # Check that the fields exist in the model
        field_names = Settings.model_fields.keys()
        assert "supabase_url" in field_names
        assert "supabase_anon_key" in field_names
        assert "supabase_service_role_key" in field_names

    def test_supabase_configured_property_false_when_not_set(self):
        """Verify supabase_configured returns False when env vars not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Import fresh settings with cleared env
            from configs.settings import Settings

            settings = Settings(
                supabase_url=None,
                supabase_anon_key=None,
            )
            assert settings.supabase_configured is False

    def test_supabase_configured_property_true_when_set(self):
        """Verify supabase_configured returns True when both URL and anon key set."""
        from configs.settings import Settings

        settings = Settings(
            supabase_url="https://test-project.supabase.co",
            supabase_anon_key="test-anon-key",
        )
        assert settings.supabase_configured is True

    def test_supabase_configured_false_when_only_url_set(self):
        """Verify supabase_configured returns False when only URL is set."""
        from configs.settings import Settings

        settings = Settings(
            supabase_url="https://test-project.supabase.co",
            supabase_anon_key=None,
        )
        assert settings.supabase_configured is False


class TestSupabaseClient:
    """Tests for Supabase client module."""

    def test_supabase_not_configured_error_exists(self):
        """Verify SupabaseNotConfiguredError is importable."""
        from src.persistence.supabase_client import SupabaseNotConfiguredError

        error = SupabaseNotConfiguredError("test message")
        assert str(error) == "test message"

    def test_is_supabase_available_returns_bool(self):
        """Verify is_supabase_available returns boolean."""
        from src.persistence.supabase_client import is_supabase_available

        result = is_supabase_available()
        assert isinstance(result, bool)

    def test_get_supabase_client_raises_when_not_configured(self):
        """Verify get_supabase_client raises when config missing."""
        from src.persistence.supabase_client import (
            get_supabase_client,
            SupabaseNotConfiguredError,
        )

        # Clear the cache to ensure fresh call
        get_supabase_client.cache_clear()

        with patch("src.persistence.supabase_client.settings") as mock_settings:
            mock_settings.supabase_url = None
            mock_settings.supabase_anon_key = None

            with pytest.raises(SupabaseNotConfiguredError) as exc_info:
                get_supabase_client()

            assert "SUPABASE_URL" in str(exc_info.value)

    def test_get_supabase_admin_client_raises_when_service_key_missing(self):
        """Verify get_supabase_admin_client raises when service role key missing."""
        from src.persistence.supabase_client import (
            get_supabase_admin_client,
            SupabaseNotConfiguredError,
        )

        # Clear the cache to ensure fresh call
        get_supabase_admin_client.cache_clear()

        with patch("src.persistence.supabase_client.settings") as mock_settings:
            mock_settings.supabase_url = "https://test.supabase.co"
            mock_settings.supabase_anon_key = "test-anon-key"
            mock_settings.supabase_service_role_key = None

            with pytest.raises(SupabaseNotConfiguredError) as exc_info:
                get_supabase_admin_client()

            assert "SUPABASE_SERVICE_ROLE_KEY" in str(exc_info.value)


class TestSupabaseSchema:
    """Tests for Supabase SQL schema file."""

    @pytest.fixture
    def schema_path(self) -> Path:
        """Get path to schema file."""
        repo_root = Path(__file__).parent.parent.parent
        return repo_root / "scripts" / "supabase_schema_v0.sql"

    def test_schema_file_exists(self, schema_path: Path):
        """Verify SQL schema file exists."""
        assert schema_path.exists(), f"Schema file not found at {schema_path}"

    def test_schema_contains_organizations_table(self, schema_path: Path):
        """Verify schema defines organizations table."""
        content = schema_path.read_text()
        assert "CREATE TABLE IF NOT EXISTS organizations" in content

    def test_schema_contains_org_members_table(self, schema_path: Path):
        """Verify schema defines org_members table."""
        content = schema_path.read_text()
        assert "CREATE TABLE IF NOT EXISTS org_members" in content

    def test_schema_contains_products_table(self, schema_path: Path):
        """Verify schema defines products table."""
        content = schema_path.read_text()
        assert "CREATE TABLE IF NOT EXISTS products" in content

    def test_schema_contains_device_versions_table(self, schema_path: Path):
        """Verify schema defines device_versions table."""
        content = schema_path.read_text()
        assert "CREATE TABLE IF NOT EXISTS device_versions" in content

    def test_schema_contains_ai_runs_table(self, schema_path: Path):
        """Verify schema defines ai_runs table."""
        content = schema_path.read_text()
        assert "CREATE TABLE IF NOT EXISTS ai_runs" in content

    def test_schema_enables_rls_on_all_tables(self, schema_path: Path):
        """Verify RLS is enabled on all tables."""
        content = schema_path.read_text()

        expected_rls = [
            "ALTER TABLE organizations ENABLE ROW LEVEL SECURITY",
            "ALTER TABLE org_members ENABLE ROW LEVEL SECURITY",
            "ALTER TABLE products ENABLE ROW LEVEL SECURITY",
            "ALTER TABLE device_versions ENABLE ROW LEVEL SECURITY",
            "ALTER TABLE ai_runs ENABLE ROW LEVEL SECURITY",
        ]

        for rls_statement in expected_rls:
            assert rls_statement in content, f"Missing RLS: {rls_statement}"

    def test_schema_contains_uuid_extension(self, schema_path: Path):
        """Verify schema enables UUID extension."""
        content = schema_path.read_text()
        assert 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"' in content

    def test_schema_contains_regulatory_twin_json_column(self, schema_path: Path):
        """Verify device_versions has regulatory_twin_json JSONB column."""
        content = schema_path.read_text()
        assert "regulatory_twin_json JSONB" in content

    def test_schema_contains_ai_runs_approval_fields(self, schema_path: Path):
        """Verify ai_runs has human-in-the-loop approval fields."""
        content = schema_path.read_text()
        assert "approved_by UUID" in content
        assert "approved_at TIMESTAMPTZ" in content

    def test_schema_contains_required_indexes(self, schema_path: Path):
        """Verify schema creates required indexes."""
        content = schema_path.read_text()

        expected_indexes = [
            "idx_org_members_user_id",
            "idx_products_org_id",
            "idx_device_versions_product_id",
            "idx_ai_runs_org_id",
        ]

        for index_name in expected_indexes:
            assert index_name in content, f"Missing index: {index_name}"
