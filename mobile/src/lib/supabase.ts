// Supabase client for PhysiqAI.
// URL and anon key are read from app.json extra (same pattern as apiUrl).
// The anon key is intentionally public — it only allows what RLS permits.
import AsyncStorage from '@react-native-async-storage/async-storage';
import { createClient, type SupportedStorage } from '@supabase/supabase-js';
import Constants from 'expo-constants';

const extra = Constants.expoConfig?.extra as
  | { supabaseUrl?: string; supabaseAnonKey?: string }
  | undefined;

const SUPABASE_URL =
  extra?.supabaseUrl ?? 'https://vfccjhijvkwknlgngvlg.supabase.co';
const SUPABASE_ANON_KEY = extra?.supabaseAnonKey ?? '';

// Expo Router statically renders the bundle in Node during web builds, where
// there is no window/localStorage. AsyncStorage's web backend calls localStorage
// at init (loadSession), which throws in that Node context. Use an inert storage
// when window is absent; the real browser + native both have a working storage.
const _isClient = typeof window !== 'undefined';
const _noopStorage: SupportedStorage = {
  getItem: async () => null,
  setItem: async () => {},
  removeItem: async () => {},
};

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    // Persist the session across app restarts via AsyncStorage (native) / localStorage (web).
    storage: _isClient ? AsyncStorage : _noopStorage,
    // No session work during SSR — only the real client persists/restores.
    persistSession: _isClient,
    autoRefreshToken: _isClient,
    // Required on web so supabase-js can parse the magic-link hash in the URL.
    detectSessionInUrl: _isClient,
  },
});
