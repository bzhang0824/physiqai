// Supabase client + session bootstrap for the mobile app.
// Anonymous-first auth: every device gets a Supabase user with zero friction,
// which gives us a JWT to call the authed backend (/progress, /avatar).
// NOTE: requires "Anonymous sign-ins" enabled in the Supabase project
// (Dashboard → Authentication → Sign In / Providers). Until then signInAnonymously
// returns an error and ensureSession() resolves to null.
import 'react-native-url-polyfill/auto';

import AsyncStorage from '@react-native-async-storage/async-storage';
import { createClient, type Session } from '@supabase/supabase-js';
import Constants from 'expo-constants';

const extra = Constants.expoConfig?.extra as
  | { supabaseUrl?: string; supabaseAnonKey?: string }
  | undefined;

const SUPABASE_URL = extra?.supabaseUrl ?? '';
const SUPABASE_ANON_KEY = extra?.supabaseAnonKey ?? '';

// Expo Web renders on the server (Node) where `window` is undefined. AsyncStorage's
// web build touches `window`, and supabase-js reads storage at init — which would
// crash SSR. This adapter falls back to in-memory storage when there's no `window`,
// and uses AsyncStorage (native storage / localStorage) on the real client.
const memoryStore: Record<string, string> = {};
const isServer = typeof window === 'undefined';
const ssrSafeStorage = {
  getItem: (key: string) =>
    isServer ? Promise.resolve(memoryStore[key] ?? null) : AsyncStorage.getItem(key),
  setItem: (key: string, value: string) => {
    if (isServer) {
      memoryStore[key] = value;
      return Promise.resolve();
    }
    return AsyncStorage.setItem(key, value);
  },
  removeItem: (key: string) => {
    if (isServer) {
      delete memoryStore[key];
      return Promise.resolve();
    }
    return AsyncStorage.removeItem(key);
  },
};

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    storage: ssrSafeStorage,
    autoRefreshToken: !isServer,
    persistSession: true,
    detectSessionInUrl: false, // no OAuth redirect handling in the app
  },
});

/**
 * Ensure the device has a Supabase session, creating an anonymous one if needed.
 * Returns the session, or null if anonymous sign-in is disabled / fails.
 */
export async function ensureSession(): Promise<Session | null> {
  const { data: existing } = await supabase.auth.getSession();
  if (existing.session) return existing.session;

  const { data, error } = await supabase.auth.signInAnonymously();
  if (error) {
    console.warn('[supabase] anonymous sign-in failed:', error.message);
    return null;
  }
  return data.session;
}

/** Current access token (JWT) for Authorization headers, or null. */
export async function getAccessToken(): Promise<string | null> {
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

/** Whether Supabase is configured (URL + key present). */
export function isSupabaseConfigured(): boolean {
  return Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);
}
