"""
ai_runs_logger.py

Writes AI provenance records to Supabase table: public.ai_runs

Design goals:
- Zero impact on existing MVP flows if Supabase is not configured
- Never crash the app due to logging failure (best-effort)
- Keep payloads JSON-serializable and small by default
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from src.persistence.supabase_client import get_supabase_client, is_supabase_available


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _stable_prompt_hash(prompt: str) -> str:
    # Stable hash for prompt/system-instructions (no secrets)
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def _json_safe(obj: Any) -> Any:
    """
    Ensure JSON-serializable.
    Falls back to string for unknown types.
    """
    try:
        json.dumps(obj)
        return obj
    except TypeError:
        return str(obj)


@dataclass(frozen=True)
class AIRunRecord:
    organization_id: str
    user_id: str | None

    provider: str
    model: str
    prompt: str  # used only to hash; not stored verbatim unless you choose to

    # Optional links
    device_id: str | None = None
    submission_id: str | None = None
    document_id: str | None = None
    conversation_id: str | None = None

    # Optional provider metadata
    request_id: str | None = None

    # Content
    inputs_json: Any = None
    output_text: str = ""
    citations_json: Any = None
    confidence: str | None = None
    warnings_json: Any = None

    # Approval workflow
    approved_by: str | None = None
    approved_at: str | None = None  # ISO string


def log_ai_run_best_effort(record: AIRunRecord) -> bool:
    """
    Best-effort insert into ai_runs. Returns True if inserted, False otherwise.
    Never raises.
    """
    if not is_supabase_available():
        return False

    try:
        sb = get_supabase_client()

        payload = {
            "organization_id": record.organization_id,
            "user_id": record.user_id,
            "device_id": record.device_id,
            "submission_id": record.submission_id,
            "document_id": record.document_id,
            "conversation_id": record.conversation_id,
            "provider": record.provider,
            "model": record.model,
            "prompt_hash": _stable_prompt_hash(record.prompt),
            "request_id": record.request_id,
            "inputs_json": _json_safe(record.inputs_json if record.inputs_json is not None else {}),
            "output_text": record.output_text or "",
            "citations_json": _json_safe(
                record.citations_json if record.citations_json is not None else []
            ),
            "confidence": record.confidence,
            "warnings_json": _json_safe(
                record.warnings_json if record.warnings_json is not None else []
            ),
            "approved_by": record.approved_by,
            "approved_at": record.approved_at,
            # created_at is default now() in DB; but keeping an app timestamp is sometimes useful
            # If your table has created_at default, you can omit this.
            # "created_at": _utc_now_iso(),
        }

        res = sb.table("ai_runs").insert(payload).execute()
        # Supabase python client returns data on success; keep it simple:
        return bool(getattr(res, "data", None))
    except Exception:
        return False
