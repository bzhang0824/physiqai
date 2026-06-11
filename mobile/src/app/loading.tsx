import { router } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { Button, Screen } from '@/components/ui';
import { transform } from '@/lib/api';
import { useStore } from '@/lib/store';
import { colors, font, space, weight } from '@/lib/theme';

const MESSAGES = [
  'Analyzing your physique…',
  'Running the physiology engine…',
  'Calculating a realistic trajectory…',
  'Rendering your future self…',
  'Locking in your real face…',
];

export default function LoadingScreen() {
  const photoUri = useStore((s) => s.photoUri);
  const stats = useStore((s) => s.stats);
  const setResult = useStore((s) => s.setResult);
  const setError = useStore((s) => s.setError);
  const [msg, setMsg] = useState(0);
  const [failed, setFailed] = useState<string | undefined>();
  const started = useRef(false);

  useEffect(() => {
    const id = setInterval(() => setMsg((m) => (m + 1) % MESSAGES.length), 4000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    (async () => {
      if (!photoUri) {
        setFailed('No photo selected.');
        return;
      }
      try {
        const result = await transform(photoUri, stats);
        setResult(result);
        setError(undefined);
        router.replace('/results');
      } catch (e: any) {
        setFailed(e?.message ?? 'Generation failed.');
        setError(e?.message);
      }
    })();
  }, [photoUri, stats, setResult, setError]);

  return (
    <Screen>
      <View style={styles.center}>
        {failed ? (
          <>
            <Text style={styles.err}>Something went wrong</Text>
            <Text style={styles.errDetail}>{failed}</Text>
            <Text style={styles.hint}>
              Make sure the backend is running and the app&apos;s API URL points to it.
            </Text>
            <View style={styles.stretch}>
              <Button title="Try Again" onPress={() => router.replace('/horizon')} />
              <Button title="Start Over" variant="ghost" onPress={() => router.replace('/')} />
            </View>
          </>
        ) : (
          <>
            <ActivityIndicator size="large" color={colors.primary} />
            <Text style={styles.msg}>{MESSAGES[msg]}</Text>
            <Text style={styles.sub}>This usually takes about 30–40 seconds.</Text>
          </>
        )}
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: space.lg },
  stretch: { alignSelf: 'stretch' },
  msg: { color: colors.foreground, fontSize: font.xl, fontWeight: weight.bold, marginTop: space.xl, textAlign: 'center' },
  sub: { color: colors.muted, fontSize: font.base, marginTop: space.sm },
  err: { color: colors.destructive, fontSize: font['2xl'], fontWeight: weight.heavy, marginBottom: space.sm },
  errDetail: { color: colors.foreground, fontSize: font.base, textAlign: 'center', marginBottom: space.md },
  hint: { color: colors.muted, fontSize: font.sm, textAlign: 'center', marginBottom: space.lg },
});
