-- =============================================================================
-- MIGRATION: RLS Policies for artifacts, artifact_links, attestations
-- Also: enable RLS on tables that should have it but currently don't
-- =============================================================================
-- Author:    Claude (AI-assisted) + Moin Bhatti
-- Date:      2026-02-06
-- Ticket:    Handoff TODO-1 (add RLS policies for evidence tables)
-- Idempotent: YES (uses DROP POLICY IF EXISTS, ENABLE RLS is idempotent)
-- Safe for:  Local Postgres (no auth schema) + Supabase (with auth schema)
-- Pattern:   users.organization_id (single-org, per handoff decision)
-- SQL style: EXECUTE $pol$...$pol$ (matches ai_runs migration pattern)
-- =============================================================================

BEGIN;

-- Ensure pgcrypto is available
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =============================================================================
-- STEP 1: Enable RLS on all org-scoped tables (unconditional, idempotent)
-- =============================================================================
-- These are safe to run even if RLS is already enabled.
-- RLS is enabled OUTSIDE the guard so it applies in ALL environments.
-- Without policies, the table owner can still read/write (local dev scenario).

ALTER TABLE public.organizations    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.org_members      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.products         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.device_versions  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_runs          ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.trace_links      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.artifacts        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.artifact_links   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.attestations     ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- STEP 2: Create Supabase-only RLS policies (guarded)
-- =============================================================================
-- Policies depend on auth.uid() which only exists in Supabase.
-- Guard: only create if auth.uid() function is resolvable.
-- Pattern: EXECUTE $pol$...$pol$ dynamic SQL (matches ai_runs migration)

DO $$
BEGIN
    -- Guard: skip policy creation if auth.uid() does not exist
    IF to_regprocedure('auth.uid()') IS NULL THEN
        RAISE NOTICE '[RLS-MIGRATION] auth.uid() not found — skipping policy creation (expected in local dev)';
        RETURN;
    END IF;

    RAISE NOTICE '[RLS-MIGRATION] auth.uid() found — creating Supabase RLS policies';

    -- =========================================================================
    -- ARTIFACTS — direct org scoping via artifacts.organization_id
    -- =========================================================================

    EXECUTE 'DROP POLICY IF EXISTS "artifacts_select_org" ON public.artifacts';
    EXECUTE 'DROP POLICY IF EXISTS "artifacts_insert_org" ON public.artifacts';
    EXECUTE 'DROP POLICY IF EXISTS "artifacts_update_org" ON public.artifacts';

    EXECUTE $pol$
      CREATE POLICY "artifacts_select_org"
      ON public.artifacts FOR SELECT
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
      CREATE POLICY "artifacts_insert_org"
      ON public.artifacts FOR INSERT
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

    EXECUTE $pol$
      CREATE POLICY "artifacts_update_org"
      ON public.artifacts FOR UPDATE
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

    -- =========================================================================
    -- ARTIFACT_LINKS — direct org scoping via artifact_links.organization_id
    -- =========================================================================

    EXECUTE 'DROP POLICY IF EXISTS "artifact_links_select_org" ON public.artifact_links';
    EXECUTE 'DROP POLICY IF EXISTS "artifact_links_insert_org" ON public.artifact_links';

    EXECUTE $pol$
      CREATE POLICY "artifact_links_select_org"
      ON public.artifact_links FOR SELECT
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
      CREATE POLICY "artifact_links_insert_org"
      ON public.artifact_links FOR INSERT
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

    -- =========================================================================
    -- ATTESTATIONS — direct org scoping via attestations.organization_id
    -- =========================================================================

    EXECUTE 'DROP POLICY IF EXISTS "attestations_select_org" ON public.attestations';
    EXECUTE 'DROP POLICY IF EXISTS "attestations_insert_org" ON public.attestations';

    EXECUTE $pol$
      CREATE POLICY "attestations_select_org"
      ON public.attestations FOR SELECT
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
      CREATE POLICY "attestations_insert_org"
      ON public.attestations FOR INSERT
      TO public
      WITH CHECK (
        organization_id IN (
          SELECT u.organization_id
          FROM public.users u
          WHERE u.id = auth.uid()
        )
        AND (attested_by IS NULL OR attested_by = auth.uid())
      )
    $pol$;

    -- =========================================================================
    -- AI_RUNS — refresh policies (idempotent, matches existing pattern)
    -- =========================================================================

    EXECUTE 'DROP POLICY IF EXISTS "ai_runs_select_org" ON public.ai_runs';
    EXECUTE 'DROP POLICY IF EXISTS "ai_runs_insert_org" ON public.ai_runs';

    EXECUTE $pol$
      CREATE POLICY "ai_runs_select_org"
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
      CREATE POLICY "ai_runs_insert_org"
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

    -- =========================================================================
    -- TRACE_LINKS — refresh policies (idempotent, matches existing pattern)
    -- =========================================================================

    EXECUTE 'DROP POLICY IF EXISTS "trace_links_select_org" ON public.trace_links';
    EXECUTE 'DROP POLICY IF EXISTS "trace_links_insert_org" ON public.trace_links';

    EXECUTE $pol$
      CREATE POLICY "trace_links_select_org"
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
      CREATE POLICY "trace_links_insert_org"
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

    RAISE NOTICE '[RLS-MIGRATION] All policies created successfully';

END $$;

-- =============================================================================
-- STEP 3: Verify (informational, does not fail)
-- =============================================================================
DO $$
DECLARE
    rls_count INTEGER;
    policy_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO rls_count
    FROM pg_tables
    WHERE schemaname = 'public'
      AND tablename IN (
        'organizations','org_members','products','device_versions',
        'ai_runs','trace_links','artifacts','artifact_links','attestations'
      )
      AND rowsecurity = true;

    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public';

    RAISE NOTICE '[RLS-VERIFY] Tables with RLS enabled: % / 9', rls_count;
    RAISE NOTICE '[RLS-VERIFY] Total policies: %', policy_count;
END $$;

COMMIT;
