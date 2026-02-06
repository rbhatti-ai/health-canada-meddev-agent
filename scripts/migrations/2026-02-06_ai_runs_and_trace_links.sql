-- =============================================================================
-- Migration: AI Provenance + Traceability Foundation
-- Date: 2026-02-06
-- SAFE FOR EXISTING SUPABASE PROJECT
-- Uses gen_random_uuid() (Supabase default)
-- Compatible with users.role enum via role::text casting
-- =============================================================================


-- ============================================================
-- AI RUNS (Regulatory-grade provenance logging)
-- ============================================================

create table if not exists ai_runs (
  id uuid primary key default gen_random_uuid(),

  organization_id uuid not null references organizations(id) on delete cascade,
  user_id uuid references users(id) on delete set null,

  device_id uuid references devices(id) on delete set null,
  submission_id uuid references submissions(id) on delete set null,
  document_id uuid references documents(id) on delete set null,
  conversation_id uuid references ai_conversations(id) on delete set null,

  provider text not null,
  model text not null,
  prompt_hash text not null,
  request_id text,

  inputs_json jsonb not null default '{}'::jsonb,
  output_text text not null default '',
  citations_json jsonb not null default '[]'::jsonb,
  confidence text,
  warnings_json jsonb not null default '[]'::jsonb,

  approved_by uuid references users(id) on delete set null,
  approved_at timestamptz,

  created_at timestamptz not null default now()
);

create index if not exists idx_ai_runs_org_id on ai_runs(organization_id);
create index if not exists idx_ai_runs_user_id on ai_runs(user_id);
create index if not exists idx_ai_runs_device_id on ai_runs(device_id);
create index if not exists idx_ai_runs_submission_id on ai_runs(submission_id);
create index if not exists idx_ai_runs_conversation_id on ai_runs(conversation_id);
create index if not exists idx_ai_runs_created_at on ai_runs(created_at);

alter table ai_runs enable row level security;

drop policy if exists "Users can view org ai runs" on ai_runs;
create policy "Users can view org ai runs"
on ai_runs for select
to public
using (
  organization_id in (
    select u.organization_id
    from users u
    where u.id = auth.uid()
  )
);

drop policy if exists "Users can insert org ai runs" on ai_runs;
create policy "Users can insert org ai runs"
on ai_runs for insert
to public
with check (
  organization_id in (
    select u.organization_id
    from users u
    where u.id = auth.uid()
  )
  and (user_id is null or user_id = auth.uid())
);

drop policy if exists "Users can update org ai runs" on ai_runs;
create policy "Users can update org ai runs"
on ai_runs for update
to public
using (
  organization_id in (
    select u.organization_id
    from users u
    where u.id = auth.uid()
  )
)
with check (
  organization_id in (
    select u.organization_id
    from users u
    where u.id = auth.uid()
  )
);



-- ============================================================
-- TRACE LINKS (Requirement ↔ Evidence graph)
-- ============================================================

create table if not exists trace_links (
  id uuid primary key default gen_random_uuid(),

  organization_id uuid not null references organizations(id) on delete cascade,
  created_by uuid references users(id) on delete set null,

  source_type text not null,
  source_id uuid not null,
  target_type text not null,
  target_id uuid not null,

  relationship text not null,
  rationale text,
  metadata jsonb not null default '{}'::jsonb,

  created_at timestamptz not null default now()
);

create index if not exists idx_trace_links_org_id on trace_links(organization_id);
create index if not exists idx_trace_links_source on trace_links(source_type, source_id);
create index if not exists idx_trace_links_target on trace_links(target_type, target_id);
create index if not exists idx_trace_links_created_at on trace_links(created_at);

alter table trace_links enable row level security;

drop policy if exists "Users can view org trace links" on trace_links;
create policy "Users can view org trace links"
on trace_links for select
to public
using (
  organization_id in (
    select u.organization_id
    from users u
    where u.id = auth.uid()
  )
);

drop policy if exists "Users can insert org trace links" on trace_links;
create policy "Users can insert org trace links"
on trace_links for insert
to public
with check (
  organization_id in (
    select u.organization_id
    from users u
    where u.id = auth.uid()
  )
  and (created_by is null or created_by = auth.uid())
);

drop policy if exists "Users can update org trace links" on trace_links;
create policy "Users can update org trace links"
on trace_links for update
to public
using (
  organization_id in (
    select u.organization_id
    from users u
    where u.id = auth.uid()
  )
)
with check (
  organization_id in (
    select u.organization_id
    from users u
    where u.id = auth.uid()
  )
);

drop policy if exists "Admins/managers can delete org trace links" on trace_links;
create policy "Admins/managers can delete org trace links"
on trace_links for delete
to public
using (
  organization_id in (
    select u.organization_id
    from users u
    where u.id = auth.uid()
      and (u.role::text in ('admin','manager'))
  )
);
