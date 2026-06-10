// Device-local app state (no persistence, no auth — per the thin-slice plan).
import { create } from 'zustand';

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

interface AppState {
  photoUri?: string;
  stats: Stats;
  result?: TransformResult;
  error?: string;
  consentAccepted: boolean; // user agreed to photo processing (BIPA-style consent)
  consentAt?: string; // ISO timestamp of acceptance
  setPhoto: (uri: string) => void;
  setStats: (patch: Partial<Stats>) => void;
  setResult: (r?: TransformResult) => void;
  setError: (e?: string) => void;
  acceptConsent: () => void;
  reset: () => void;
}

export const useStore = create<AppState>((set) => ({
  stats: DEFAULT_STATS,
  consentAccepted: false,
  setPhoto: (uri) => set({ photoUri: uri }),
  setStats: (patch) => set((s) => ({ stats: { ...s.stats, ...patch } })),
  setResult: (result) => set({ result }),
  setError: (error) => set({ error }),
  acceptConsent: () => set({ consentAccepted: true, consentAt: new Date().toISOString() }),
  reset: () =>
    set({ photoUri: undefined, result: undefined, error: undefined, stats: DEFAULT_STATS }),
}));
