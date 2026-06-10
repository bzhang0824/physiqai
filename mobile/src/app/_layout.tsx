import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import { ensureSession } from '@/lib/supabase';
import { colors } from '@/lib/theme';

export default function RootLayout() {
  // Establish an anonymous Supabase session early so authed calls are ready.
  useEffect(() => {
    ensureSession().catch(() => {});
  }, []);

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
          <Stack.Screen name="home" options={{ headerShown: false }} />
          <Stack.Screen name="checkin" />
        </Stack>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
