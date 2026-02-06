-- =============================================================================
-- Migration: AI Provenance + Traceability Foundation (local-safe + Supabase-ready)
-- Date: 2026-02-06

-- Notes:
-- - Works in plain Postgres: policies are guarded (no auth schema required).
-- - Works in Supabase: enables RLS + policies using auth.uid().
-- - Uses gen_random_uuid() via pgcrypto.
-- =============================================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================
-- AI RUNS
-- ============================================================

CREATE TABLE IF NOT EXISTS public.ai_runs (
id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
user_id uuid REFERENCES public.users(id) ON DELETE SET NULL,

device_id uuid REFERENCES public.devices(id) ON DELETE SET NULL,
submission_id uuid REFERENCES public.submissions(id) ON DELETE SET NULL,
document_id uuid REFERENCES public.documents(id) ON DELETE SET NULL,
conversation_id uuid REFERENCES public.ai_conversations(id) ON DELETE SET NULL,

provider text NOT NULL,
model text NOT NULL,
prompt_hash text NOT NULL,
request_id text,

inputs_json jsonb NOT NULL DEFAULT '{}'::jsonb,
output_text text NOT NULL DEFAULT '',
citations_json jsonb NOT NULL DEFAULT '[]'::jsonb,
confidence text,
warnings_json jsonb NOT NULL DEFAULT '[]'::jsonb,

approved_by uuid REFERENCES public.users(id) ON DELETE SET NULL,
approved_at timestamptz,

created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ai_runs_org_id ON public.ai_runs(organization_id);
CREATE INDEX IF NOT EXISTS idx_ai_runs_user_id ON public.ai_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_runs_device_id ON public.ai_runs(device_id);
CREATE INDEX IF NOT EXISTS idx_ai_runs_submission_id ON public.ai_runs(submission_id);
CREATE INDEX IF NOT EXISTS idx_ai_runs_conversation_id ON public.ai_runs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_ai_runs_created_at ON public.ai_runs(created_at);

-- Supabase-only: enable RLS + policies if auth.uid() exists
DO $$
BEGIN
IF to_regprocedure('auth.uid()') IS NOT NULL THEN
ALTER TABLE public.ai_runs ENABLE ROW LEVEL SECURITY;

EXECUTE 'DROP POLICY IF EXISTS "Users can view org ai runs" ON public.ai_runs';
EXECUTE 'DROP POLICY IF EXISTS "Users can insert org ai runs" ON public.ai_runs';
EXECUTE 'DROP POLICY IF EXISTS "Users can update org ai runs" ON public.ai_runs';

EXECUTE $pol$
  CREATE POLICY "Users can view org ai runs"
  ON public.ai_runs FOR SELECT
  TO public
  USING (
    organization_id IN (
      SELECT u.organization_id
      FROM public.users u
      WHERE u.id = auth.uid()
    )
  )
$pol$;

EXECUTE $pol$
  CREATE POLICY "Users can insert org ai runs"
  ON public.ai_runs FOR INSERT
  TO public
  WITH CHECK (
    organization_id IN (
      SELECT u.organization_id
      FROM public.users u
      WHERE u.id = auth.uid()
    )
    AND (user_id IS NULL OR user_id = auth.uid())
  )
$pol$;

EXECUTE $pol$
  CREATE POLICY "Users can update org ai runs"
  ON public.ai_runs FOR UPDATE
  TO public
  USING (
    organization_id IN (
      SELECT u.organization_id
      FROM public.users u
      WHERE u.id = auth.uid()
    )
  )
  WITH CHECK (
    organization_id IN (
      SELECT u.organization_id
      FROM public.users u
      WHERE u.id = auth.uid()
    )
  )
$pol$;


END IF;
END $$;

-- ============================================================
-- TRACE LINKS
-- ============================================================

CREATE TABLE IF NOT EXISTS public.trace_links (
id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
created_by uuid REFERENCES public.users(id) ON DELETE SET NULL,

source_type text NOT NULL,
source_id uuid NOT NULL,
target_type text NOT NULL,
target_id uuid NOT NULL,

relationship text NOT NULL,
rationale text,
metadata jsonb NOT NULL DEFAULT '{}'::jsonb,

created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_trace_links_org_id ON public.trace_links(organization_id);
CREATE INDEX IF NOT EXISTS idx_trace_links_source ON public.trace_links(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_trace_links_target ON public.trace_links(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_trace_links_created_at ON public.trace_links(created_at);

-- Supabase-only: enable RLS + policies if auth.uid() exists
DO $$
BEGIN
IF to_regprocedure('auth.uid()') IS NOT NULL THEN
ALTER TABLE public.trace_links ENABLE ROW LEVEL SECURITY;

EXECUTE 'DROP POLICY IF EXISTS "Users can view org trace links" ON public.trace_links';
EXECUTE 'DROP POLICY IF EXISTS "Users can insert org trace links" ON public.trace_links';

EXECUTE $pol$
  CREATE POLICY "Users can view org trace links"
  ON public.trace_links FOR SELECT
  TO public
  USING (
    organization_id IN (
      SELECT u.organization_id
      FROM public.users u
      WHERE u.id = auth.uid()
    )
  )
$pol$;

EXECUTE $pol$
  CREATE POLICY "Users can insert org trace links"
  ON public.trace_links FOR INSERT
  TO public
  WITH CHECK (
    organization_id IN (
      SELECT u.organization_id
      FROM public.users u
      WHERE u.id = auth.uid()
    )
    AND (created_by IS NULL OR created_by = auth.uid())
  )
$pol$;


END IF;
END $$;

COMMIT;
