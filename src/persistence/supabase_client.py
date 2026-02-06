"""
Supabase client initialization and access.

This module provides lazy-initialized Supabase clients for database operations.
No network calls are made at import time - clients are created on first use.

Usage:
    from src.persistence import get_supabase_client

    # Get client (raises SupabaseNotConfiguredError if env vars missing)
    client = get_supabase_client()

    # Query example (not implemented in MVP - for future use)
    # response = client.table("organizations").select("*").execute()

Environment Variables Required:
    SUPABASE_URL: Your Supabase project URL (e.g., https://xxx.supabase.co)
    SUPABASE_ANON_KEY: Anon/public key for client-side operations

Optional:
    SUPABASE_SERVICE_ROLE_KEY: Service role key for server-side admin operations
                                (bypasses RLS - use with caution)
"""

from functools import lru_cache
from typing import Any

from configs.settings import settings


class SupabaseNotConfiguredError(Exception):
    """Raised when Supabase credentials are not configured."""

    def __init__(self, message: str = "Supabase is not configured"):
        self.message = message
        super().__init__(self.message)


def _validate_supabase_config() -> None:
    """
    Validate that required Supabase configuration is present.

    Raises:
        SupabaseNotConfiguredError: If SUPABASE_URL or SUPABASE_ANON_KEY is missing.
    """
    if not settings.supabase_url:
        raise SupabaseNotConfiguredError(
            "SUPABASE_URL environment variable is not set. "
            "Set it to your Supabase project URL (e.g., https://xxx.supabase.co)"
        )
    if not settings.supabase_anon_key:
        raise SupabaseNotConfiguredError(
            "SUPABASE_ANON_KEY environment variable is not set. "
            "Set it to your Supabase anon/public key."
        )


@lru_cache(maxsize=1)
def get_supabase_client() -> Any:
    """
    Get a Supabase client using the anon key.

    This client respects Row Level Security (RLS) policies and should be used
    for most operations where the user context matters.

    The client is lazily initialized on first call and cached for reuse.
    No network calls are made until this function is called.

    Returns:
        supabase.Client: Initialized Supabase client.

    Raises:
        SupabaseNotConfiguredError: If required environment variables are missing.
        ImportError: If supabase-py package is not installed.

    Example:
        client = get_supabase_client()
        # client.table("organizations").select("*").execute()
    """
    _validate_supabase_config()

    try:
        import supabase  # type: ignore

    except ImportError as e:
        raise ImportError(
            "supabase-py package is not installed. " "Install it with: pip install supabase"
        ) from e

    _supabase: Any = supabase  # type: ignore
    create_client = _supabase.create_client
    client = create_client(
        settings.supabase_url,
        settings.supabase_anon_key,
    )
    return client


@lru_cache(maxsize=1)
def get_supabase_admin_client() -> Any:
    """
    Get a Supabase client using the service role key.

    WARNING: This client BYPASSES Row Level Security (RLS) policies.
    Only use for server-side admin operations where RLS bypass is required.
    Never expose this client or the service role key to client-side code.

    The client is lazily initialized on first call and cached for reuse.
    No network calls are made until this function is called.

    Returns:
        supabase.Client: Initialized Supabase admin client.

    Raises:
        SupabaseNotConfiguredError: If required environment variables are missing,
                                    including the service role key.
        ImportError: If supabase-py package is not installed.

    Example:
        admin_client = get_supabase_admin_client()
        # admin_client.table("ai_runs").insert({...}).execute()
    """
    _validate_supabase_config()

    if not settings.supabase_service_role_key:
        raise SupabaseNotConfiguredError(
            "SUPABASE_SERVICE_ROLE_KEY environment variable is not set. "
            "This key is required for admin operations that bypass RLS. "
            "If you don't need RLS bypass, use get_supabase_client() instead."
        )

    try:
        import supabase  # type: ignore

    except ImportError as e:
        raise ImportError(
            "supabase-py package is not installed. " "Install it with: pip install supabase"
        ) from e

    _supabase: Any = supabase  # type: ignore
    create_client = _supabase.create_client
    client = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )
    return client


def is_supabase_available() -> bool:
    """
    Check if Supabase is configured and available.

    This does NOT make a network call - it only checks if the required
    environment variables are set.

    Returns:
        bool: True if SUPABASE_URL and SUPABASE_ANON_KEY are configured.
    """
    return settings.supabase_configured
