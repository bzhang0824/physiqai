-- PhysiqAI — daily workout log (quick-log for tamagotchi accountability streak).
-- One row per manual log entry (note optional). Read via RLS; writes via service role.

create table if not exists public.workout_logs (
  id         uuid        primary key default gen_random_uuid(),
  user_id    uuid        not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  note       text
);

create index if not exists workout_logs_user_created_idx
  on public.workout_logs (user_id, created_at desc);

alter table public.workout_logs enable row level security;

drop policy if exists "own workout logs read" on public.workout_logs;
create policy "own workout logs read" on public.workout_logs
  for select using (auth.uid() = user_id);
