-- =============================================================================
-- Supabase Schema v0: Regulatory Twin Foundation + AI Provenance
-- =============================================================================
--
-- This schema establishes the foundation for:
-- 1. Multi-tenant organization structure
-- 2. Product/device version tracking (Regulatory Twin)
-- 3. AI run provenance logging (required by governing architecture)
--
-- APPLY THIS IN: Supabase Dashboard > SQL Editor > New Query > Paste & Run
--
-- Row Level Security (RLS) is enabled on all tables.
-- Policies restrict access based on organization membership.
-- =============================================================================

-- Enable UUID extension (required for uuid_generate_v4())
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- TABLE: organizations
-- =============================================================================
-- Top-level tenant entity. All data is scoped to an organization.

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see organizations they are members of
CREATE POLICY "Users can view their organizations"
    ON organizations
    FOR SELECT
    USING (
        id IN (
            SELECT org_id FROM org_members WHERE user_id = auth.uid()
        )
    );

-- =============================================================================
-- TABLE: org_members
-- =============================================================================
-- Junction table linking users to organizations with roles.

CREATE TABLE IF NOT EXISTS org_members (
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,  -- References auth.users(id) in Supabase Auth
    role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (org_id, user_id)
);

-- Index for user lookups
CREATE INDEX IF NOT EXISTS idx_org_members_user_id ON org_members(user_id);

-- Enable RLS
ALTER TABLE org_members ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see memberships for orgs they belong to
CREATE POLICY "Users can view org memberships they belong to"
    ON org_members
    FOR SELECT
    USING (
        org_id IN (
            SELECT org_id FROM org_members WHERE user_id = auth.uid()
        )
    );

-- =============================================================================
-- TABLE: products
-- =============================================================================
-- Medical device products within an organization.

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for org-scoped queries
CREATE INDEX IF NOT EXISTS idx_products_org_id ON products(org_id);

-- Enable RLS
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see products in their organizations
CREATE POLICY "Users can view products in their organizations"
    ON products
    FOR SELECT
    USING (
        org_id IN (
            SELECT org_id FROM org_members WHERE user_id = auth.uid()
        )
    );

-- Policy: Users can insert products in their organizations
CREATE POLICY "Users can insert products in their organizations"
    ON products
    FOR INSERT
    WITH CHECK (
        org_id IN (
            SELECT org_id FROM org_members WHERE user_id = auth.uid()
        )
    );

-- =============================================================================
-- TABLE: device_versions
-- =============================================================================
-- Versioned snapshots of device regulatory data (the "Regulatory Twin").
-- The regulatory_twin_json column stores the full structured device profile.

CREATE TABLE IF NOT EXISTS device_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    version_label TEXT NOT NULL,  -- e.g., "1.0.0", "draft-2024-02-06"
    regulatory_twin_json JSONB NOT NULL DEFAULT '{}',  -- Full device profile snapshot
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Index for product-scoped queries
CREATE INDEX IF NOT EXISTS idx_device_versions_product_id ON device_versions(product_id);

-- Enable RLS
ALTER TABLE device_versions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view device versions for products in their organizations
CREATE POLICY "Users can view device versions in their organizations"
    ON device_versions
    FOR SELECT
    USING (
        product_id IN (
            SELECT p.id FROM products p
            INNER JOIN org_members om ON p.org_id = om.org_id
            WHERE om.user_id = auth.uid()
        )
    );

-- Policy: Users can insert device versions for products in their organizations
CREATE POLICY "Users can insert device versions in their organizations"
    ON device_versions
    FOR INSERT
    WITH CHECK (
        product_id IN (
            SELECT p.id FROM products p
            INNER JOIN org_members om ON p.org_id = om.org_id
            WHERE om.user_id = auth.uid()
        )
    );

-- =============================================================================
-- TABLE: ai_runs
-- =============================================================================
-- Provenance logging for all AI-generated outputs.
-- Required by governing architecture for auditability and human-in-the-loop.

CREATE TABLE IF NOT EXISTS ai_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,  -- User who initiated the AI run
    model TEXT NOT NULL,  -- e.g., "claude-3-5-sonnet-20241022"
    prompt_hash TEXT,  -- SHA256 hash of the prompt for deduplication/tracking
    inputs_json JSONB NOT NULL DEFAULT '{}',  -- Structured inputs to the AI
    output_text TEXT NOT NULL,  -- Raw AI output
    citations_json JSONB DEFAULT '[]',  -- Extracted citations/references
    confidence TEXT,  -- Confidence level if applicable (e.g., "high", "0.85")
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Human-in-the-loop approval fields
    approved_by UUID,  -- User who approved this output (NULL = not yet approved)
    approved_at TIMESTAMPTZ  -- When approval occurred
);

-- Index for org-scoped queries
CREATE INDEX IF NOT EXISTS idx_ai_runs_org_id ON ai_runs(org_id);

-- Index for user's runs
CREATE INDEX IF NOT EXISTS idx_ai_runs_user_id ON ai_runs(user_id);

-- Index for approval status queries
CREATE INDEX IF NOT EXISTS idx_ai_runs_approved_at ON ai_runs(approved_at);

-- Enable RLS
ALTER TABLE ai_runs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view AI runs in their organizations
CREATE POLICY "Users can view AI runs in their organizations"
    ON ai_runs
    FOR SELECT
    USING (
        org_id IN (
            SELECT org_id FROM org_members WHERE user_id = auth.uid()
        )
    );

-- Policy: Users can insert AI runs in their organizations
CREATE POLICY "Users can insert AI runs in their organizations"
    ON ai_runs
    FOR INSERT
    WITH CHECK (
        org_id IN (
            SELECT org_id FROM org_members WHERE user_id = auth.uid()
        )
    );

-- Policy: Users can update AI runs they created (for approval workflow)
CREATE POLICY "Users can update AI runs in their organizations"
    ON ai_runs
    FOR UPDATE
    USING (
        org_id IN (
            SELECT org_id FROM org_members WHERE user_id = auth.uid()
        )
    )
    WITH CHECK (
        org_id IN (
            SELECT org_id FROM org_members WHERE user_id = auth.uid()
        )
    );

-- =============================================================================
-- VERIFICATION QUERY (run after applying schema)
-- =============================================================================
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public'
-- AND table_name IN ('organizations', 'org_members', 'products', 'device_versions', 'ai_runs');
