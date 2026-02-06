BEGIN;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS public.artifacts (
id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
created_by uuid REFERENCES public.users(id) ON DELETE SET NULL,
artifact_type text NOT NULL,
title text NOT NULL,
description text,
storage_uri text,
content_sha256 text,
content_mime text,
content_bytes bigint,
content_json jsonb NOT NULL DEFAULT '{}'::jsonb,
ai_run_id uuid REFERENCES public.ai_runs(id) ON DELETE SET NULL,
created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.artifact_links (
id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
created_by uuid REFERENCES public.users(id) ON DELETE SET NULL,
artifact_id uuid NOT NULL REFERENCES public.artifacts(id) ON DELETE CASCADE,
target_type text NOT NULL,
target_id uuid NOT NULL,
relationship text NOT NULL,
rationale text,
metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.attestations (
id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
organization_id uuid NOT NULL REFERENCES public.organizations(id) ON DELETE CASCADE,
artifact_id uuid REFERENCES public.artifacts(id) ON DELETE CASCADE,
artifact_link_id uuid REFERENCES public.artifact_links(id) ON DELETE CASCADE,
attested_by uuid REFERENCES public.users(id) ON DELETE SET NULL,
attestation_type text NOT NULL,
attestation_note text,
attestation_json jsonb NOT NULL DEFAULT '{}'::jsonb,
created_at timestamptz NOT NULL DEFAULT now(),
CONSTRAINT attestations_one_target_chk CHECK (
(artifact_id IS NOT NULL AND artifact_link_id IS NULL)
OR (artifact_id IS NULL AND artifact_link_id IS NOT NULL)
)
);

COMMIT;
