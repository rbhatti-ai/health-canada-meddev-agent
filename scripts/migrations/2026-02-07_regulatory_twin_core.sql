-- ============================================================================
-- Migration: Regulatory Twin Core Entities
-- Date:      2026-02-07
-- Author:    Sprint 1 — Evidence Ingestion, Traceability & Attestation
-- Depends:   2026-02-06_base_schema.sql
--            2026-02-06_ai_runs_and_trace_links.sql
--            2026-02-06_artifacts_and_attestations.sql
--            2026-02-06_rls_policies_artifacts_attestations.sql
--
-- Creates 10 tables for the Digital Regulatory Twin:
--   intended_uses, claims, hazards, harms, risk_controls,
--   verification_tests, validation_tests, evidence_items,
--   labeling_assets, submission_targets
--
-- Design decisions:
--   - All tables org-scoped (organization_id FK)
--   - All mutable tables have version + supersedes_id for immutable versioning
--   - All have created_by FK to public.users
--   - RLS enabled unconditionally on all tables
--   - Policies created only in Supabase (auth.uid() guard)
--   - Indexes on organization_id, device_version_id, created_by
-- ============================================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- TABLE 1: intended_uses
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.intended_uses (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    device_version_id uuid NOT NULL REFERENCES public.device_versions(id) ON DELETE CASCADE,
    statement       text NOT NULL,
    indications     jsonb NOT NULL DEFAULT '[]'::jsonb,
    contraindications jsonb NOT NULL DEFAULT '[]'::jsonb,
    target_population text,
    use_environment text,
    created_by      uuid REFERENCES public.users(id) ON DELETE SET NULL,
    version         integer NOT NULL DEFAULT 1,
    supersedes_id   uuid REFERENCES public.intended_uses(id) ON DELETE SET NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_intended_uses_org
    ON public.intended_uses(organization_id);
CREATE INDEX IF NOT EXISTS idx_intended_uses_device_version
    ON public.intended_uses(device_version_id);
CREATE INDEX IF NOT EXISTS idx_intended_uses_supersedes
    ON public.intended_uses(supersedes_id);

-- ============================================================================
-- TABLE 2: claims
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.claims (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    device_version_id uuid NOT NULL REFERENCES public.device_versions(id) ON DELETE CASCADE,
    claim_type      text NOT NULL,
    statement       text NOT NULL,
    evidence_basis  text,
    status          text NOT NULL DEFAULT 'draft',
    created_by      uuid REFERENCES public.users(id) ON DELETE SET NULL,
    version         integer NOT NULL DEFAULT 1,
    supersedes_id   uuid REFERENCES public.claims(id) ON DELETE SET NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT claims_status_chk CHECK (status IN (
        'draft', 'under_review', 'accepted', 'rejected', 'superseded'
    )),
    CONSTRAINT claims_type_chk CHECK (claim_type IN (
        'safety', 'performance', 'usability', 'biocompatibility',
        'sterility', 'shelf_life', 'software_performance', 'other'
    ))
);

CREATE INDEX IF NOT EXISTS idx_claims_org
    ON public.claims(organization_id);
CREATE INDEX IF NOT EXISTS idx_claims_device_version
    ON public.claims(device_version_id);
CREATE INDEX IF NOT EXISTS idx_claims_status
    ON public.claims(status);
CREATE INDEX IF NOT EXISTS idx_claims_supersedes
    ON public.claims(supersedes_id);

-- ============================================================================
-- TABLE 3: hazards
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.hazards (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    device_version_id uuid NOT NULL REFERENCES public.device_versions(id) ON DELETE CASCADE,
    hazard_category text NOT NULL,
    description     text NOT NULL,
    foreseeable_sequence text,
    severity        text,
    probability     text,
    risk_level_pre  text,
    created_by      uuid REFERENCES public.users(id) ON DELETE SET NULL,
    version         integer NOT NULL DEFAULT 1,
    supersedes_id   uuid REFERENCES public.hazards(id) ON DELETE SET NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT hazards_category_chk CHECK (hazard_category IN (
        'electrical', 'biological', 'chemical', 'mechanical',
        'thermal', 'radiation', 'software', 'use_error',
        'cybersecurity', 'environmental', 'other'
    )),
    CONSTRAINT hazards_severity_chk CHECK (severity IS NULL OR severity IN (
        'negligible', 'marginal', 'critical', 'catastrophic'
    )),
    CONSTRAINT hazards_probability_chk CHECK (probability IS NULL OR probability IN (
        'improbable', 'remote', 'occasional', 'probable', 'frequent'
    )),
    CONSTRAINT hazards_risk_level_pre_chk CHECK (risk_level_pre IS NULL OR risk_level_pre IN (
        'low', 'medium', 'high', 'unacceptable'
    ))
);

CREATE INDEX IF NOT EXISTS idx_hazards_org
    ON public.hazards(organization_id);
CREATE INDEX IF NOT EXISTS idx_hazards_device_version
    ON public.hazards(device_version_id);
CREATE INDEX IF NOT EXISTS idx_hazards_category
    ON public.hazards(hazard_category);
CREATE INDEX IF NOT EXISTS idx_hazards_supersedes
    ON public.hazards(supersedes_id);

-- ============================================================================
-- TABLE 4: harms
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.harms (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    hazard_id       uuid NOT NULL REFERENCES public.hazards(id) ON DELETE CASCADE,
    harm_type       text NOT NULL,
    description     text NOT NULL,
    severity        text NOT NULL,
    affected_population text,
    created_by      uuid REFERENCES public.users(id) ON DELETE SET NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT harms_type_chk CHECK (harm_type IN (
        'injury', 'death', 'misdiagnosis', 'delayed_treatment',
        'unnecessary_treatment', 'infection', 'tissue_damage',
        'psychological', 'financial', 'other'
    )),
    CONSTRAINT harms_severity_chk CHECK (severity IN (
        'negligible', 'marginal', 'critical', 'catastrophic'
    ))
);

CREATE INDEX IF NOT EXISTS idx_harms_org
    ON public.harms(organization_id);
CREATE INDEX IF NOT EXISTS idx_harms_hazard
    ON public.harms(hazard_id);

-- ============================================================================
-- TABLE 5: risk_controls
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.risk_controls (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    hazard_id       uuid NOT NULL REFERENCES public.hazards(id) ON DELETE CASCADE,
    control_type    text NOT NULL,
    description     text NOT NULL,
    risk_level_post text,
    implementation_status text NOT NULL DEFAULT 'planned',
    created_by      uuid REFERENCES public.users(id) ON DELETE SET NULL,
    version         integer NOT NULL DEFAULT 1,
    supersedes_id   uuid REFERENCES public.risk_controls(id) ON DELETE SET NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT risk_controls_type_chk CHECK (control_type IN (
        'inherent_safety', 'protective_measure', 'information_for_safety'
    )),
    CONSTRAINT risk_controls_risk_post_chk CHECK (risk_level_post IS NULL OR risk_level_post IN (
        'low', 'medium', 'high', 'unacceptable'
    )),
    CONSTRAINT risk_controls_impl_chk CHECK (implementation_status IN (
        'planned', 'in_progress', 'implemented', 'verified', 'retired'
    ))
);

CREATE INDEX IF NOT EXISTS idx_risk_controls_org
    ON public.risk_controls(organization_id);
CREATE INDEX IF NOT EXISTS idx_risk_controls_hazard
    ON public.risk_controls(hazard_id);
CREATE INDEX IF NOT EXISTS idx_risk_controls_impl
    ON public.risk_controls(implementation_status);
CREATE INDEX IF NOT EXISTS idx_risk_controls_supersedes
    ON public.risk_controls(supersedes_id);

-- ============================================================================
-- TABLE 6: verification_tests
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.verification_tests (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    device_version_id uuid NOT NULL REFERENCES public.device_versions(id) ON DELETE CASCADE,
    test_type       text NOT NULL,
    title           text NOT NULL,
    protocol_ref    text,
    acceptance_criteria text NOT NULL,
    result_summary  text,
    pass_fail       text,
    tested_at       timestamptz,
    created_by      uuid REFERENCES public.users(id) ON DELETE SET NULL,
    version         integer NOT NULL DEFAULT 1,
    supersedes_id   uuid REFERENCES public.verification_tests(id) ON DELETE SET NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT vt_type_chk CHECK (test_type IN (
        'bench', 'software', 'biocompatibility', 'electrical_safety',
        'emc', 'sterilization', 'packaging', 'shelf_life',
        'cybersecurity', 'other'
    )),
    CONSTRAINT vt_pass_fail_chk CHECK (pass_fail IS NULL OR pass_fail IN (
        'pass', 'fail', 'conditional', 'pending'
    ))
);

CREATE INDEX IF NOT EXISTS idx_verification_tests_org
    ON public.verification_tests(organization_id);
CREATE INDEX IF NOT EXISTS idx_verification_tests_device_version
    ON public.verification_tests(device_version_id);
CREATE INDEX IF NOT EXISTS idx_verification_tests_pass_fail
    ON public.verification_tests(pass_fail);
CREATE INDEX IF NOT EXISTS idx_verification_tests_supersedes
    ON public.verification_tests(supersedes_id);

-- ============================================================================
-- TABLE 7: validation_tests
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.validation_tests (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    device_version_id uuid NOT NULL REFERENCES public.device_versions(id) ON DELETE CASCADE,
    test_type       text NOT NULL,
    title           text NOT NULL,
    protocol_ref    text,
    acceptance_criteria text NOT NULL,
    result_summary  text,
    pass_fail       text,
    participant_count integer,
    tested_at       timestamptz,
    created_by      uuid REFERENCES public.users(id) ON DELETE SET NULL,
    version         integer NOT NULL DEFAULT 1,
    supersedes_id   uuid REFERENCES public.validation_tests(id) ON DELETE SET NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT val_type_chk CHECK (test_type IN (
        'usability', 'clinical_investigation', 'clinical_evaluation',
        'simulated_use', 'formative', 'summative', 'other'
    )),
    CONSTRAINT val_pass_fail_chk CHECK (pass_fail IS NULL OR pass_fail IN (
        'pass', 'fail', 'conditional', 'pending'
    ))
);

CREATE INDEX IF NOT EXISTS idx_validation_tests_org
    ON public.validation_tests(organization_id);
CREATE INDEX IF NOT EXISTS idx_validation_tests_device_version
    ON public.validation_tests(device_version_id);
CREATE INDEX IF NOT EXISTS idx_validation_tests_pass_fail
    ON public.validation_tests(pass_fail);
CREATE INDEX IF NOT EXISTS idx_validation_tests_supersedes
    ON public.validation_tests(supersedes_id);

-- ============================================================================
-- TABLE 8: evidence_items
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.evidence_items (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    device_version_id uuid NOT NULL REFERENCES public.device_versions(id) ON DELETE CASCADE,
    evidence_type   text NOT NULL,
    title           text NOT NULL,
    description     text,
    source_ref      text,
    artifact_id     uuid REFERENCES public.artifacts(id) ON DELETE SET NULL,
    strength        text NOT NULL DEFAULT 'moderate',
    status          text NOT NULL DEFAULT 'draft',
    created_by      uuid REFERENCES public.users(id) ON DELETE SET NULL,
    version         integer NOT NULL DEFAULT 1,
    supersedes_id   uuid REFERENCES public.evidence_items(id) ON DELETE SET NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ei_type_chk CHECK (evidence_type IN (
        'test_report', 'literature_review', 'clinical_data',
        'standard_reference', 'predicate_comparison', 'risk_analysis',
        'design_output', 'manufacturing_record', 'post_market_data',
        'expert_opinion', 'other'
    )),
    CONSTRAINT ei_strength_chk CHECK (strength IN (
        'strong', 'moderate', 'weak', 'insufficient'
    )),
    CONSTRAINT ei_status_chk CHECK (status IN (
        'draft', 'under_review', 'accepted', 'rejected', 'superseded'
    ))
);

CREATE INDEX IF NOT EXISTS idx_evidence_items_org
    ON public.evidence_items(organization_id);
CREATE INDEX IF NOT EXISTS idx_evidence_items_device_version
    ON public.evidence_items(device_version_id);
CREATE INDEX IF NOT EXISTS idx_evidence_items_artifact
    ON public.evidence_items(artifact_id);
CREATE INDEX IF NOT EXISTS idx_evidence_items_type
    ON public.evidence_items(evidence_type);
CREATE INDEX IF NOT EXISTS idx_evidence_items_status
    ON public.evidence_items(status);
CREATE INDEX IF NOT EXISTS idx_evidence_items_supersedes
    ON public.evidence_items(supersedes_id);

-- ============================================================================
-- TABLE 9: labeling_assets
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.labeling_assets (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    device_version_id uuid NOT NULL REFERENCES public.device_versions(id) ON DELETE CASCADE,
    asset_type      text NOT NULL,
    title           text NOT NULL,
    content_ref     text,
    language        text NOT NULL DEFAULT 'en',
    regulatory_market text,
    artifact_id     uuid REFERENCES public.artifacts(id) ON DELETE SET NULL,
    status          text NOT NULL DEFAULT 'draft',
    created_by      uuid REFERENCES public.users(id) ON DELETE SET NULL,
    version         integer NOT NULL DEFAULT 1,
    supersedes_id   uuid REFERENCES public.labeling_assets(id) ON DELETE SET NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT la_type_chk CHECK (asset_type IN (
        'ifu', 'label', 'packaging', 'e_labeling', 'quick_reference',
        'patient_information', 'surgical_technique', 'other'
    )),
    CONSTRAINT la_status_chk CHECK (status IN (
        'draft', 'under_review', 'accepted', 'rejected', 'superseded'
    )),
    CONSTRAINT la_market_chk CHECK (regulatory_market IS NULL OR regulatory_market IN (
        'CA', 'US', 'EU', 'UK', 'AU', 'JP', 'CN', 'other'
    ))
);

CREATE INDEX IF NOT EXISTS idx_labeling_assets_org
    ON public.labeling_assets(organization_id);
CREATE INDEX IF NOT EXISTS idx_labeling_assets_device_version
    ON public.labeling_assets(device_version_id);
CREATE INDEX IF NOT EXISTS idx_labeling_assets_artifact
    ON public.labeling_assets(artifact_id);
CREATE INDEX IF NOT EXISTS idx_labeling_assets_supersedes
    ON public.labeling_assets(supersedes_id);

-- ============================================================================
-- TABLE 10: submission_targets
-- ============================================================================
CREATE TABLE IF NOT EXISTS public.submission_targets (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
    device_version_id uuid NOT NULL REFERENCES public.device_versions(id) ON DELETE CASCADE,
    regulatory_body text NOT NULL,
    submission_type text NOT NULL,
    target_date     date,
    status          text NOT NULL DEFAULT 'planning',
    reference_number text,
    created_by      uuid REFERENCES public.users(id) ON DELETE SET NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT st_body_chk CHECK (regulatory_body IN (
        'health_canada', 'fda', 'eu_mdr', 'mhra', 'tga', 'pmda', 'nmpa', 'other'
    )),
    CONSTRAINT st_type_chk CHECK (submission_type IN (
        'mdl', '510k', 'de_novo', 'pma', 'ce_mark',
        'ukca', 'tga_inclusion', 'shonin', 'other'
    )),
    CONSTRAINT st_status_chk CHECK (status IN (
        'planning', 'preparing', 'submitted', 'under_review',
        'approved', 'rejected', 'withdrawn'
    ))
);

CREATE INDEX IF NOT EXISTS idx_submission_targets_org
    ON public.submission_targets(organization_id);
CREATE INDEX IF NOT EXISTS idx_submission_targets_device_version
    ON public.submission_targets(device_version_id);
CREATE INDEX IF NOT EXISTS idx_submission_targets_status
    ON public.submission_targets(status);

-- ============================================================================
-- RLS: Enable on all 10 tables (unconditional)
-- ============================================================================
ALTER TABLE public.intended_uses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.hazards ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.harms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.risk_controls ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.verification_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.validation_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evidence_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.labeling_assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.submission_targets ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- POLICIES: Supabase-only (guarded by auth.uid() existence)
-- ============================================================================
DO $$
BEGIN
    IF to_regprocedure('auth.uid()') IS NOT NULL THEN
        RAISE NOTICE '[RLS-MIGRATION] auth.uid() found — creating org-scoped policies';

        -- intended_uses
        EXECUTE $pol$DROP POLICY IF EXISTS intended_uses_select_org ON public.intended_uses$pol$;
        EXECUTE $pol$CREATE POLICY intended_uses_select_org ON public.intended_uses
            FOR SELECT USING (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
            )$pol$;
        EXECUTE $pol$DROP POLICY IF EXISTS intended_uses_insert_org ON public.intended_uses$pol$;
        EXECUTE $pol$CREATE POLICY intended_uses_insert_org ON public.intended_uses
            FOR INSERT WITH CHECK (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
                AND (created_by IS NULL OR created_by = auth.uid())
            )$pol$;
        EXECUTE $pol$DROP POLICY IF EXISTS intended_uses_update_org ON public.intended_uses$pol$;
        EXECUTE $pol$CREATE POLICY intended_uses_update_org ON public.intended_uses
            FOR UPDATE USING (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
            )$pol$;

        -- claims
        EXECUTE $pol$DROP POLICY IF EXISTS claims_select_org ON public.claims$pol$;
        EXECUTE $pol$CREATE POLICY claims_select_org ON public.claims
            FOR SELECT USING (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
            )$pol$;
        EXECUTE $pol$DROP POLICY IF EXISTS claims_insert_org ON public.claims$pol$;
        EXECUTE $pol$CREATE POLICY claims_insert_org ON public.claims
            FOR INSERT WITH CHECK (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
                AND (created_by IS NULL OR created_by = auth.uid())
            )$pol$;
        EXECUTE $pol$DROP POLICY IF EXISTS claims_update_org ON public.claims$pol$;
        EXECUTE $pol$CREATE POLICY claims_update_org ON public.claims
            FOR UPDATE USING (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
            )$pol$;

        -- hazards
        EXECUTE $pol$DROP POLICY IF EXISTS hazards_select_org ON public.hazards$pol$;
        EXECUTE $pol$CREATE POLICY hazards_select_org ON public.hazards
            FOR SELECT USING (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
            )$pol$;
        EXECUTE $pol$DROP POLICY IF EXISTS hazards_insert_org ON public.hazards$pol$;
        EXECUTE $pol$CREATE POLICY hazards_insert_org ON public.hazards
            FOR INSERT WITH CHECK (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
                AND (created_by IS NULL OR created_by = auth.uid())
            )$pol$;
        EXECUTE $pol$DROP POLICY IF EXISTS hazards_update_org ON public.hazards$pol$;
        EXECUTE $pol$CREATE POLICY hazards_update_org ON public.hazards
            FOR UPDATE USING (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
            )$pol$;

        -- harms
        EXECUTE $pol$DROP POLICY IF EXISTS harms_select_org ON public.harms$pol$;
        EXECUTE $pol$CREATE POLICY harms_select_org ON public.harms
            FOR SELECT USING (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
            )$pol$;
        EXECUTE $pol$DROP POLICY IF EXISTS harms_insert_org ON public.harms$pol$;
        EXECUTE $pol$CREATE POLICY harms_insert_org ON public.harms
            FOR INSERT WITH CHECK (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
                AND (created_by IS NULL OR created_by = auth.uid())
            )$pol$;

        -- risk_controls
        EXECUTE $pol$DROP POLICY IF EXISTS risk_controls_select_org ON public.risk_controls$pol$;
        EXECUTE $pol$CREATE POLICY risk_controls_select_org ON public.risk_controls
            FOR SELECT USING (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
            )$pol$;
        EXECUTE $pol$DROP POLICY IF EXISTS risk_controls_insert_org ON public.risk_controls$pol$;
        EXECUTE $pol$CREATE POLICY risk_controls_insert_org ON public.risk_controls
            FOR INSERT WITH CHECK (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
                AND (created_by IS NULL OR created_by = auth.uid())
            )$pol$;
        EXECUTE $pol$DROP POLICY IF EXISTS risk_controls_update_org ON public.risk_controls$pol$;
        EXECUTE $pol$CREATE POLICY risk_controls_update_org ON public.risk_controls
            FOR UPDATE USING (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
            )$pol$;

        -- verification_tests
        EXECUTE $pol$DROP POLICY IF EXISTS verification_tests_select_org ON public.verification_tests$pol$;
        EXECUTE $pol$CREATE POLICY verification_tests_select_org ON public.verification_tests
            FOR SELECT USING (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
            )$pol$;
        EXECUTE $pol$DROP POLICY IF EXISTS verification_tests_insert_org ON public.verification_tests$pol$;
        EXECUTE $pol$CREATE POLICY verification_tests_insert_org ON public.verification_tests
            FOR INSERT WITH CHECK (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
                AND (created_by IS NULL OR created_by = auth.uid())
            )$pol$;
        EXECUTE $pol$DROP POLICY IF EXISTS verification_tests_update_org ON public.verification_tests$pol$;
        EXECUTE $pol$CREATE POLICY verification_tests_update_org ON public.verification_tests
            FOR UPDATE USING (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
            )$pol$;

        -- validation_tests
        EXECUTE $pol$DROP POLICY IF EXISTS validation_tests_select_org ON public.validation_tests$pol$;
        EXECUTE $pol$CREATE POLICY validation_tests_select_org ON public.validation_tests
            FOR SELECT USING (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
            )$pol$;
        EXECUTE $pol$DROP POLICY IF EXISTS validation_tests_insert_org ON public.validation_tests$pol$;
        EXECUTE $pol$CREATE POLICY validation_tests_insert_org ON public.validation_tests
            FOR INSERT WITH CHECK (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
                AND (created_by IS NULL OR created_by = auth.uid())
            )$pol$;
        EXECUTE $pol$DROP POLICY IF EXISTS validation_tests_update_org ON public.validation_tests$pol$;
        EXECUTE $pol$CREATE POLICY validation_tests_update_org ON public.validation_tests
            FOR UPDATE USING (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
            )$pol$;

        -- evidence_items
        EXECUTE $pol$DROP POLICY IF EXISTS evidence_items_select_org ON public.evidence_items$pol$;
        EXECUTE $pol$CREATE POLICY evidence_items_select_org ON public.evidence_items
            FOR SELECT USING (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
            )$pol$;
        EXECUTE $pol$DROP POLICY IF EXISTS evidence_items_insert_org ON public.evidence_items$pol$;
        EXECUTE $pol$CREATE POLICY evidence_items_insert_org ON public.evidence_items
            FOR INSERT WITH CHECK (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
                AND (created_by IS NULL OR created_by = auth.uid())
            )$pol$;
        EXECUTE $pol$DROP POLICY IF EXISTS evidence_items_update_org ON public.evidence_items$pol$;
        EXECUTE $pol$CREATE POLICY evidence_items_update_org ON public.evidence_items
            FOR UPDATE USING (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
            )$pol$;

        -- labeling_assets
        EXECUTE $pol$DROP POLICY IF EXISTS labeling_assets_select_org ON public.labeling_assets$pol$;
        EXECUTE $pol$CREATE POLICY labeling_assets_select_org ON public.labeling_assets
            FOR SELECT USING (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
            )$pol$;
        EXECUTE $pol$DROP POLICY IF EXISTS labeling_assets_insert_org ON public.labeling_assets$pol$;
        EXECUTE $pol$CREATE POLICY labeling_assets_insert_org ON public.labeling_assets
            FOR INSERT WITH CHECK (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
                AND (created_by IS NULL OR created_by = auth.uid())
            )$pol$;
        EXECUTE $pol$DROP POLICY IF EXISTS labeling_assets_update_org ON public.labeling_assets$pol$;
        EXECUTE $pol$CREATE POLICY labeling_assets_update_org ON public.labeling_assets
            FOR UPDATE USING (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
            )$pol$;

        -- submission_targets
        EXECUTE $pol$DROP POLICY IF EXISTS submission_targets_select_org ON public.submission_targets$pol$;
        EXECUTE $pol$CREATE POLICY submission_targets_select_org ON public.submission_targets
            FOR SELECT USING (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
            )$pol$;
        EXECUTE $pol$DROP POLICY IF EXISTS submission_targets_insert_org ON public.submission_targets$pol$;
        EXECUTE $pol$CREATE POLICY submission_targets_insert_org ON public.submission_targets
            FOR INSERT WITH CHECK (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
                AND (created_by IS NULL OR created_by = auth.uid())
            )$pol$;
        EXECUTE $pol$DROP POLICY IF EXISTS submission_targets_update_org ON public.submission_targets$pol$;
        EXECUTE $pol$CREATE POLICY submission_targets_update_org ON public.submission_targets
            FOR UPDATE USING (
                organization_id IN (
                    SELECT u.organization_id FROM public.users u WHERE u.id = auth.uid()
                )
            )$pol$;

    ELSE
        RAISE NOTICE '[RLS-MIGRATION] auth.uid() not found — skipping policy creation (expected in local dev)';
    END IF;
END
$$;

-- ============================================================================
-- VERIFICATION: Report table and RLS counts
-- ============================================================================
DO $$
DECLARE
    rls_count integer;
    policy_count integer;
    twin_tables text[] := ARRAY[
        'intended_uses', 'claims', 'hazards', 'harms', 'risk_controls',
        'verification_tests', 'validation_tests', 'evidence_items',
        'labeling_assets', 'submission_targets'
    ];
    tbl text;
    rls_on integer := 0;
BEGIN
    FOREACH tbl IN ARRAY twin_tables LOOP
        SELECT COUNT(*) INTO rls_count
        FROM pg_tables
        WHERE schemaname = 'public' AND tablename = tbl AND rowsecurity = true;
        rls_on := rls_on + rls_count;
    END LOOP;

    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'public'
      AND tablename = ANY(twin_tables);

    RAISE NOTICE '[RLS-VERIFY] Regulatory Twin tables with RLS enabled: % / 10', rls_on;
    RAISE NOTICE '[RLS-VERIFY] Regulatory Twin policies: %', policy_count;
END
$$;

COMMIT;
