"""Persistence layer for Supabase database integration."""

from src.persistence.supabase_client import (
    get_supabase_client,
    get_supabase_admin_client,
    SupabaseNotConfiguredError,
)

__all__ = [
    "get_supabase_client",
    "get_supabase_admin_client",
    "SupabaseNotConfiguredError",
]
