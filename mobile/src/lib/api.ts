// Talks to the PhysiqAI backend. Base URL comes from app.json `extra.apiUrl`
// (one place to switch Simulator/web `localhost` <-> a physical phone's LAN IP).
import Constants from 'expo-constants';
import { Platform } from 'react-native';

import { supabase } from './supabase';
import type { AvatarStatus, Projection, Stats, TransformResult } from './store';

const API_URL: string =
  (Constants.expoConfig?.extra as { apiUrl?: string } | undefined)?.apiUrl ??
  'http://localhost:8000';

export function apiBase() {
  return API_URL;
}

// Returns an Authorization header with the current Supabase JWT, or {} if
// the user is not signed in. Awaits supabase-js so the token is always fresh.
export async function authHeader(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (!token) return {};
  return { Authorization: `Bearer ${token}` };
}

export async function checkHealth(): Promise<boolean> {
  try {
    const r = await fetch(`${API_URL}/health`, { method: 'GET' });
    return r.ok;
  } catch {
    return false;
  }
}

async function appendPhoto(form: FormData, photoUri: string) {
  if (Platform.OS === 'web') {
    // On web the picker yields a blob/data URL; FormData needs a real Blob.
    const blob = await (await fetch(photoUri)).blob();
    form.append('photo', blob, 'photo.jpg');
  } else {
    // React Native accepts the {uri,name,type} shape directly.
    form.append('photo', { uri: photoUri, name: 'photo.jpg', type: 'image/jpeg' } as unknown as Blob);
  }
}

// ── Shared field builder — keeps /transform and /avatar in sync ───────────────
function appendStatsFields(form: FormData, stats: Stats) {
  const fields: Record<string, string> = {
    age: String(stats.age),
    sex: stats.sex,
    height_in: String(stats.heightIn),
    weight_lb: String(stats.weightLb),
    bf_pct: String(stats.bfPct),
    bf_method: stats.bfMeasured ? 'measured' : 'estimated',
    experience: stats.experience,
    goal: stats.goal,
    lean_preference: stats.leanPreference,
    volume: stats.volume,
    intensity: stats.intensity,
    days_per_week: String(stats.daysPerWeek),
    cardio_days: String(stats.cardioDays),
    focus_muscle_groups: stats.focusGroups.join(','),
    protein_level: stats.proteinLevel,
    tracking_method: stats.trackingMethod,
    sleep_hrs: String(stats.sleepHrs),
    stress: String(stats.stress),
    genetic_potential: stats.geneticPotential,
    weeks: String(stats.weeks),
  };
  for (const [k, v] of Object.entries(fields)) form.append(k, v);
}

// ── /transform ────────────────────────────────────────────────────────────────
export async function transform(photoUri: string, stats: Stats): Promise<TransformResult> {
  const form = new FormData();
  await appendPhoto(form, photoUri);
  appendStatsFields(form, stats);

  const res = await fetch(`${API_URL}/transform`, { method: 'POST', body: form });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = (await res.json()) as { detail?: string | unknown };
      if (j?.detail) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
    } catch {
      // ignore parse errors
    }
    throw new Error(detail);
  }
  return (await res.json()) as TransformResult;
}

// ── /avatar — start a new 3-D avatar generation job ──────────────────────────
export interface StartAvatarResult {
  job: string;
  status_url: string;
}

export async function startAvatar(
  photoUri: string,
  stats: Stats
): Promise<StartAvatarResult> {
  const form = new FormData();
  await appendPhoto(form, photoUri);
  appendStatsFields(form, stats);

  const res = await fetch(`${API_URL}/avatar`, {
    method: 'POST',
    body: form,
    headers: await authHeader(),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = (await res.json()) as { detail?: string | unknown };
      if (j?.detail) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return (await res.json()) as StartAvatarResult;
}

// ── GET /avatar/{job} ─────────────────────────────────────────────────────────
export async function getAvatarStatus(job: string): Promise<AvatarStatus> {
  const res = await fetch(`${API_URL}/avatar/${job}`, {
    headers: await authHeader(),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return (await res.json()) as AvatarStatus;
}

// ── GET /avatar/latest ───────────────────────────────────────────────────────
// Backend derives the user from the Authorization JWT — no userKey param.
export async function getLatestAvatar(): Promise<AvatarStatus | null> {
  const res = await fetch(`${API_URL}/avatar/latest`, {
    headers: await authHeader(),
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return (await res.json()) as AvatarStatus;
}

// ── POST /progress ────────────────────────────────────────────────────────────

export interface CheckinBody {
  weight_lb?: number;
  bf_pct?: number;
  workouts_done?: number;
  note?: string;
}

export type ProgressState = 'ahead' | 'on_track' | 'behind' | 'evolving';

export interface CheckinResult {
  projection: Projection;
  baked_projection: Projection;
  rebake_recommended: boolean;
  reasons: string[];
  rebake_triggered: boolean;
  rebake_job: string | null;
  streak_weeks: number;
  state: ProgressState;
}

export interface CheckinEntry {
  id: string;
  created_at: string;
  weight_lb: number | null;
  bf_pct: number | null;
  workouts_done: number | null;
  note: string | null;
  rebake_triggered: boolean;
}

export interface ProgressSummary {
  streak_weeks: number;
  last_checkin_at: string | null;
  current_weight_lb: number | null;
  current_bf_pct: number | null;
  rebakes_used: number;
  checkins: CheckinEntry[];
  latest_avatar: { job: string; status: string } | null;
}

export async function postProgress(body: CheckinBody): Promise<CheckinResult> {
  const res = await fetch(`${API_URL}/progress`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...(await authHeader()) },
    body: JSON.stringify(body),
  });
  if (res.status === 409) {
    const j = (await res.json()) as { detail?: string };
    throw Object.assign(new Error(j.detail ?? 'No avatar yet'), { status: 409 });
  }
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = (await res.json()) as { detail?: string | unknown };
      if (j?.detail) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
    } catch {
      // ignore parse errors
    }
    throw new Error(detail);
  }
  return (await res.json()) as CheckinResult;
}

export async function getProgress(): Promise<ProgressSummary> {
  const res = await fetch(`${API_URL}/progress`, {
    headers: await authHeader(),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return (await res.json()) as ProgressSummary;
}

// ── DELETE /account ───────────────────────────────────────────────────────────
// Permanently deletes the signed-in user's account + all their data. The caller
// should sign out locally afterward.
export async function deleteAccount(): Promise<void> {
  const res = await fetch(`${API_URL}/account`, {
    method: 'DELETE',
    headers: await authHeader(),
  });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = (await res.json()) as { detail?: string | unknown };
      if (j?.detail) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
    } catch {
      // ignore parse errors
    }
    throw new Error(detail);
  }
}

// ── POST /avatar/refresh ──────────────────────────────────────────────────────
export interface RefreshResult {
  rebake_recommended: boolean;
  reasons: string[];
  current_projection: Record<string, unknown>;
  baked_projection: Record<string, unknown>;
}

export async function refreshAvatar(job: string, stats: Stats): Promise<RefreshResult> {
  const form = new FormData();
  form.append('job', job);
  appendStatsFields(form, stats);

  const res = await fetch(`${API_URL}/avatar/refresh`, {
    method: 'POST',
    body: form,
    headers: await authHeader(),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return (await res.json()) as RefreshResult;
}
