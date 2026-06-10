-- PhysiqAI — progress check-ins + tamagotchi evolution state.
-- A check-in is a weekly progress log (weight / body-fat / workouts done). It
-- recomputes the engine projection from the user's current state and, when the
-- projection has shifted enough (should_rebake), triggers the avatar to re-bake
-- so the future-self the user sees actually evolves with their real progress.

create table if not exists public.checkins (
  id                uuid primary key default gen_random_uuid(),
  user_id           uuid not null references auth.users(id) on delete cascade,
  created_at        timestamptz not null default now(),
  weight_lb         numeric,
  bf_pct            numeric,
  workouts_done     int not null default 0,   -- since the last check-in
  note              text,
  projection        jsonb,                     -- engine projection recomputed at this check-in
  rebake_triggered  boolean not null default false,
  rebake_job        text                       -- the avatar job spawned, if any
);

create index if not exists checkins_user_created_idx
  on public.checkins (user_id, created_at desc);

alter table public.checkins enable row level security;

drop policy if exists "own checkins read" on public.checkins;
create policy "own checkins read" on public.checkins
  for select using (auth.uid() = user_id);

-- Tamagotchi state lives on the profile.
alter table public.profiles add column if not exists streak_weeks      int not null default 0;
alter table public.profiles add column if not exists last_checkin_at   timestamptz;
alter table public.profiles add column if not exists current_weight_lb numeric;
alter table public.profiles add column if not exists current_bf_pct    numeric;
-- How many avatar re-bakes the user has spent (separate from the initial avatar_limit).
alter table public.profiles add column if not exists rebakes_used      int not null default 0;
