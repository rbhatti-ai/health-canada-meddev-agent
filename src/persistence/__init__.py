"""Persistence layer for Supabase database integration."""

from src.persistence.supabase_client import (
    SupabaseNotConfiguredError,
    get_supabase_admin_client,
    get_supabase_client,
)

__all__ = [
    "get_supabase_client",
    "get_supabase_admin_client",
    "SupabaseNotConfiguredError",
]
