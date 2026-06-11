import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { supabase } from '@/lib/supabase';
import { useStore } from '@/lib/store';
import { colors } from '@/lib/theme';

export default function RootLayout() {
  const setSession = useStore((s) => s.setSession);
  const setAuthReady = useStore((s) => s.setAuthReady);

  useEffect(() => {
    // Resolve the initial session (covers page-reload on web and app-launch on native).
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setAuthReady(true);
    });

    // Keep the store in sync with supabase-js auth events (sign-in, sign-out,
    // token refresh, magic-link callback, etc.).
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      // Mark ready on first event too (covers race where getSession is slow).
      setAuthReady(true);
    });

    return () => listener.subscription.unsubscribe();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <GestureHandlerRootView style={{ flex: 1, backgroundColor: colors.background }}>
      <SafeAreaProvider>
        <StatusBar style="dark" />
        <Stack
          screenOptions={{
            headerStyle: { backgroundColor: colors.background },
            headerTintColor: colors.foreground,
            headerShadowVisible: false,
            contentStyle: { backgroundColor: colors.background },
            headerTitle: '',
          }}>
          <Stack.Screen name="index" options={{ headerShown: false }} />
          <Stack.Screen name="consent" />
          <Stack.Screen name="photo" />
          <Stack.Screen name="stats" />
          <Stack.Screen name="training" />
          <Stack.Screen name="nutrition" />
          <Stack.Screen name="recovery" />
          <Stack.Screen name="horizon" />
          <Stack.Screen name="loading" options={{ headerShown: false, gestureEnabled: false }} />
          <Stack.Screen name="results" options={{ headerShown: false }} />
          <Stack.Screen name="avatar" options={{ headerShown: false }} />
          <Stack.Screen name="signin" options={{ headerShown: false }} />
          <Stack.Screen name="checkin" options={{ headerShown: false }} />
          <Stack.Screen name="home" options={{ headerShown: false }} />
          <Stack.Screen name="evolution" />
          <Stack.Screen name="progress" options={{ headerShown: false }} />
          <Stack.Screen name="settings" options={{ headerShown: false }} />
          <Stack.Screen name="privacy" />
          <Stack.Screen name="terms" />
        </Stack>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
