// Talks to the PhysiqAI backend. Base URL comes from app.json `extra.apiUrl`
// (one place to switch Simulator/web `localhost` <-> a physical phone's LAN IP).
import Constants from 'expo-constants';
import { Platform } from 'react-native';

import type { Stats, TransformResult } from './store';
import { getAccessToken } from './supabase';

const API_URL: string =
  (Constants.expoConfig?.extra as { apiUrl?: string } | undefined)?.apiUrl ??
  'http://localhost:8000';

export function apiBase() {
  return API_URL;
}

/** Pull a useful error message out of a failed backend response. */
async function errorDetail(res: Response): Promise<string> {
  let detail = `HTTP ${res.status}`;
  try {
    const j = await res.json();
    if (j?.detail) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
  } catch {
    // ignore parse errors
  }
  return detail;
}

/** JSON fetch with the current Supabase JWT attached. Throws on non-2xx. */
async function authedFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = await getAccessToken();
  if (!token) throw new Error('Not signed in. Please restart the app.');
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(init.headers ?? {}),
    },
  });
  if (!res.ok) throw new Error(await errorDetail(res));
  return (await res.json()) as T;
}

// ---- Progress / workout check-in API (backend /progress) -------------------

export interface Checkin {
  id: string;
  created_at: string;
  workouts_done: number;
  weight_lb?: number | null;
  bf_pct?: number | null;
  note?: string | null;
  rebake_triggered: boolean;
}

export interface ProgressSummary {
  streak_weeks: number;
  last_checkin_at: string | null;
  current_weight_lb: number | null;
  current_bf_pct: number | null;
  rebakes_used: number;
  checkins: Checkin[];
  latest_avatar: { job: string; status: string; frames: { count: number } | null } | null;
}

export interface CheckinInput {
  workouts_done: number;
  weight_lb?: number;
  bf_pct?: number;
  note?: string;
}

export interface CheckinResult {
  projection: Record<string, unknown>;
  baked_projection: Record<string, unknown>;
  rebake_recommended: boolean;
  reasons: string[];
  rebake_triggered: boolean;
  rebake_job: string | null;
  streak_weeks: number;
  state: string;
}

/** Fetch streak, check-in history, and latest avatar for the signed-in user. */
export function getProgress(): Promise<ProgressSummary> {
  return authedFetch<ProgressSummary>('/progress');
}

/** Log a workout check-in. Updates the streak and may trigger an avatar rebake. */
export function postProgress(body: CheckinInput): Promise<CheckinResult> {
  return authedFetch<CheckinResult>('/progress', { method: 'POST', body: JSON.stringify(body) });
}

// ---- Avatar API (backend /avatar) ------------------------------------------

export interface LatestAvatar {
  job: string | null;
  status: string | null;
  frame_count?: number | null;
  frame_base_url?: string | null;
  master_url?: string | null;
  after_url?: string | null;
}

/** Latest avatar job for the signed-in user (for the 3D avatar page). */
export function getLatestAvatar(): Promise<LatestAvatar> {
  return authedFetch<LatestAvatar>('/avatar/latest');
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
    form.append('photo', { uri: photoUri, name: 'photo.jpg', type: 'image/jpeg' } as any);
  }
}

export async function transform(photoUri: string, stats: Stats): Promise<TransformResult> {
  const form = new FormData();
  await appendPhoto(form, photoUri);
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

  const res = await fetch(`${API_URL}/transform`, { method: 'POST', body: form });
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j?.detail) detail = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
    } catch {
      // ignore parse errors
    }
    throw new Error(detail);
  }
  return (await res.json()) as TransformResult;
}
