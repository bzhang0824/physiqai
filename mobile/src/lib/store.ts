// Device-local app state. Non-avatar state is session-only (no persistence).
// Avatar identity fields (userKey + lastAvatarJob) are persisted via zustand/persist
// backed by @react-native-async-storage/async-storage on all platforms.
// On web, AsyncStorage is localStorage-backed (no prefix — key stored verbatim).
// Hydration is async; components must gate on `hasHydrated` before reading persisted fields.
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { Session } from '@supabase/supabase-js';
import { create } from 'zustand';
import { createJSONStorage, persist, type StateStorage } from 'zustand/middleware';

// Expo Router statically renders the bundle in Node, where AsyncStorage's web
// backend (localStorage) does not exist — use an inert storage there. Real
// browsers and native both have `window`.
const _ssrNoopStorage: StateStorage = {
  getItem: () => null,
  setItem: () => undefined,
  removeItem: () => undefined,
};
const _persistStorage = () =>
  typeof window === 'undefined' ? _ssrNoopStorage : AsyncStorage;

// ── Tiny unique-ID generator (no external deps) ───────────────────────────────
function genKey(): string {
  const arr = new Uint8Array(9);
  if (typeof globalThis !== 'undefined' && globalThis.crypto?.getRandomValues) {
    globalThis.crypto.getRandomValues(arr);
  } else {
    for (let i = 0; i < arr.length; i++) arr[i] = Math.floor(Math.random() * 256);
  }
  return Array.from(arr, (b) => b.toString(16).padStart(2, '0')).join('');
}

// ── Domain types ──────────────────────────────────────────────────────────────
export type Sex = 'M' | 'F';
export type Goal = 'fat_loss' | 'recomp' | 'muscle_gain';
export type Experience = 'beginner' | 'intermediate' | 'advanced';
export type Level = 'low' | 'moderate' | 'high';
export type Intensity = 'light' | 'moderate' | 'intense';
export type LeanPref = 'standard' | 'lean_bulk' | 'aggressive_bulk';
export type Tracking = 'weighing' | 'app' | 'eyeballing' | 'none';
export type Genetic = 'low' | 'average' | 'high';

export interface Stats {
  // About you
  age: number;
  sex: Sex;
  heightIn: number; // total inches
  weightLb: number;
  bfPct: number;
  bfMeasured: boolean; // false = estimated via body-type picker
  experience: Experience;
  // Training
  volume: Level;
  intensity: Intensity;
  daysPerWeek: number;
  cardioDays: number;
  focusGroups: string[];
  // Nutrition
  goal: Goal;
  leanPreference: LeanPref;
  proteinLevel: Level;
  trackingMethod: Tracking;
  // Recovery
  sleepHrs: number;
  stress: number; // 1-10, higher = more stress
  geneticPotential: Genetic;
  // The ask
  weeks: number;
}

export interface Projection {
  direction: string;
  months: number;
  weight_before_lb: number;
  weight_after_lb: number;
  weight_delta_lb: number;
  bf_before: number;
  bf_after: number;
  bf_delta: number;
  lean_delta_lb: number;
  confidence_score: number;
  confidence_lo_lb: number;
  confidence_hi_lb: number;
  measurements_cm: Record<string, number>;
  warnings: string[];
  insights: string[];
}

export interface TransformResult {
  job: string;
  before_url: string;
  after_url: string;
  projection: Projection;
  face_locked: boolean;
  seconds: number;
  prompt: string;
}

// ── Avatar types (mirrors GET /avatar/{job} response) ────────────────────────
export type AvatarStatusEnum =
  | 'queued'
  | 'after_still'
  | 'orbiting'
  | 'matting'
  | 'extracting'
  | 'done'
  | 'failed';

export interface AvatarFrames {
  count: number;
  base_url: string; // absolute URL ending in /frames_mobile
  ext: string;      // "webp"
}

export interface AvatarStatus {
  job: string;
  status: AvatarStatusEnum;
  progress_pct: number;
  error: string | null;
  projection: Projection | null;
  after_url: string | null;
  frames: AvatarFrames | null;
  master_url: string | null;
  created_at: string;
}

// ── Default stats ─────────────────────────────────────────────────────────────
const DEFAULT_STATS: Stats = {
  age: 25,
  sex: 'M',
  heightIn: 70,
  weightLb: 175,
  bfPct: 18,
  bfMeasured: false,
  experience: 'intermediate',
  volume: 'moderate',
  intensity: 'moderate',
  daysPerWeek: 4,
  cardioDays: 2,
  focusGroups: [],
  goal: 'fat_loss',
  leanPreference: 'lean_bulk',
  proteinLevel: 'moderate',
  trackingMethod: 'none',
  sleepHrs: 7.5,
  stress: 5,
  geneticPotential: 'average',
  weeks: 26,
};

// ── Auth state (not persisted — supabase-js owns session persistence) ────────
export interface AuthUser {
  id: string;
  email: string;
}

interface AuthState {
  session: Session | null;
  user: AuthUser | null;
  authReady: boolean; // false until the initial getSession() resolves
  setSession: (session: Session | null) => void;
  setUser: (user: AuthUser | null) => void;
  setAuthReady: (ready: boolean) => void;
}

// ── Photo capture (front required; side/back improve avatar accuracy) ────────
export type PhotoAngle = 'front' | 'side' | 'back';
export type Photos = Partial<Record<PhotoAngle, string>>;

// ── Session state (not persisted) ────────────────────────────────────────────
interface SessionState {
  photos: Photos;
  stats: Stats;
  result?: TransformResult;
  error?: string;
  avatarStatus?: AvatarStatus;
  consentAccepted: boolean; // user agreed to photo processing (BIPA-style consent)
  consentAt?: string; // ISO timestamp of acceptance
  setPhoto: (angle: PhotoAngle, uri: string) => void;
  clearPhoto: (angle: PhotoAngle) => void;
  setStats: (patch: Partial<Stats>) => void;
  setResult: (r?: TransformResult) => void;
  setError: (e?: string) => void;
  setAvatarStatus: (s?: AvatarStatus) => void;
  acceptConsent: () => void;
  reset: () => void; // does NOT clear userKey / lastAvatarJob / consent
}

// ── Persisted state (survives reload) ────────────────────────────────────────
interface PersistedState {
  userKey: string;
  lastAvatarJob?: string;
  hasHydrated: boolean;
  setLastAvatarJob: (job: string | undefined) => void;
}

// ── Combined store ────────────────────────────────────────────────────────────
type AppState = AuthState & SessionState & PersistedState;

// The persisted slice wraps only what should survive reloads.
// We use two separate create() calls composed by merging — but the cleanest
// approach in zustand v5 is a single store with persist partializing only the
// persisted keys.
export const useStore = create<AppState>()(
  persist(
    (set) => ({
      // auth — supabase-js persists the session; we just mirror it here for reactive reads
      session: null,
      user: null,
      authReady: false,
      setSession: (session) =>
        set({
          session,
          user: session?.user
            ? { id: session.user.id, email: session.user.email ?? '' }
            : null,
        }),
      setUser: (user) => set({ user }),
      setAuthReady: (authReady) => set({ authReady }),
      // session
      photos: {},
      stats: DEFAULT_STATS,
      consentAccepted: false,
      setPhoto: (angle, uri) =>
        set((s) => ({ photos: { ...s.photos, [angle]: uri } })),
      clearPhoto: (angle) =>
        set((s) => {
          const photos = { ...s.photos };
          delete photos[angle];
          return { photos };
        }),
      setStats: (patch) => set((s) => ({ stats: { ...s.stats, ...patch } })),
      setResult: (result) => set({ result }),
      setError: (error) => set({ error }),
      setAvatarStatus: (avatarStatus) => set({ avatarStatus }),
      acceptConsent: () =>
        set({ consentAccepted: true, consentAt: new Date().toISOString() }),
      reset: () =>
        set({ photos: {}, result: undefined, error: undefined, stats: DEFAULT_STATS }),
      // persisted
      userKey: genKey(),
      lastAvatarJob: undefined,
      hasHydrated: false,
      setLastAvatarJob: (job) => set({ lastAvatarJob: job }),
    }),
    {
      name: 'physiqai-persist',
      storage: createJSONStorage(_persistStorage),
      // Persist identity + consent — both should survive reloads (never re-nag consent).
      partialize: (state) => ({
        userKey: state.userKey,
        lastAvatarJob: state.lastAvatarJob,
        consentAccepted: state.consentAccepted,
        consentAt: state.consentAt,
      }),
      onRehydrateStorage: () => () => {
        useStore.setState({ hasHydrated: true });
      },
    }
  )
);
