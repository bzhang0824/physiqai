-- PhysiqAI — initial schema (auth-backed avatar persistence)
-- Apply in Supabase SQL Editor (Dashboard → SQL Editor → New query → paste → Run),
-- or via psql with the project's connection string. Idempotent where practical.

-- ── profiles: one row per auth user (auto-created on signup) ────────────────────
create table if not exists public.profiles (
  id                 uuid primary key references auth.users(id) on delete cascade,
  email              text,
  created_at         timestamptz not null default now(),
  -- Beta spend control: how many avatar generations this user has kicked off.
  -- A future paywall checks/decrements credits; for the friends beta we cap on this.
  avatars_generated  int  not null default 0,
  avatar_limit       int  not null default 1   -- 1 free avatar per user in the beta
);

-- ── avatars: persistent record of every generated avatar ───────────────────────
create table if not exists public.avatars (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null references auth.users(id) on delete cascade,
  job           text not null,                 -- generation job id (file pipeline)
  status        text not null default 'queued',
  progress_pct  int  not null default 0,
  error         text,
  projection    jsonb,                         -- engine projection (same shape as /transform)
  inputs        jsonb,                         -- the 22 onboarding fields submitted
  frame_count   int,
  after_url     text,
  frame_base_url text,                         -- absolute base for /frames_mobile
  master_url    text,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create index if not exists avatars_user_created_idx
  on public.avatars (user_id, created_at desc);
create unique index if not exists avatars_job_idx
  on public.avatars (job);

-- ── Row-level security ─────────────────────────────────────────────────────────
-- Users may READ only their own rows. All writes go through the backend with the
-- service-role key, which bypasses RLS — so we intentionally add no write policy
-- for the `authenticated` role.
alter table public.profiles enable row level security;
alter table public.avatars  enable row level security;

drop policy if exists "own profile read" on public.profiles;
create policy "own profile read" on public.profiles
  for select using (auth.uid() = id);

drop policy if exists "own profile update" on public.profiles;
create policy "own profile update" on public.profiles
  for update using (auth.uid() = id);

drop policy if exists "own avatars read" on public.avatars;
create policy "own avatars read" on public.avatars
  for select using (auth.uid() = user_id);

-- ── Auto-create a profile row whenever a new auth user signs up ────────────────
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email)
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ── keep updated_at fresh on avatars ───────────────────────────────────────────
create or replace function public.touch_updated_at()
returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end;
$$;

drop trigger if exists avatars_touch_updated_at on public.avatars;
create trigger avatars_touch_updated_at
  before update on public.avatars
  for each row execute function public.touch_updated_at();
