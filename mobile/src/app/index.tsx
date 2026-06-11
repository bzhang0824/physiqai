// Welcome / root gate. A signed-in user with an avatar lands on /home (their
// Tamagotchi hub); everyone else gets the onboarding funnel. The gate lives
// HERE (not _layout) so deep links like /avatar?job=… are never intercepted.
// Navigation happens only in an effect, after hydration + auth resolve —
// during static export this renders the brand splash (SSR-safe).
import { router } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { Button, Screen } from '@/components/ui';
import { getLatestAvatar } from '@/lib/api';
import { useStore } from '@/lib/store';
import { colors, font, space, weight } from '@/lib/theme';

export default function Welcome() {
  const reset = useStore((s) => s.reset);
  const session = useStore((s) => s.session);
  const authReady = useStore((s) => s.authReady);
  const hasHydrated = useStore((s) => s.hasHydrated);
  const lastAvatarJob = useStore((s) => s.lastAvatarJob);
  const setLastAvatarJob = useStore((s) => s.setLastAvatarJob);

  // deciding=true until we know whether to redirect — prevents a flash of the
  // welcome funnel for returning users.
  const [deciding, setDeciding] = useState(true);
  const decidedRef = useRef(false);

  useEffect(() => {
    if (!hasHydrated || !authReady || decidedRef.current) return;
    decidedRef.current = true;

    if (!session) {
      setDeciding(false); // signed out → welcome funnel
      return;
    }
    if (lastAvatarJob) {
      router.replace('/home'); // fast path: known avatar on this device
      return;
    }
    // Signed in but no local job — ask the server once.
    getLatestAvatar()
      .then((latest) => {
        if (latest) {
          setLastAvatarJob(latest.job);
          router.replace('/home');
        } else {
          setDeciding(false); // signed in, no avatar → run the funnel
        }
      })
      .catch(() => setDeciding(false));
  }, [hasHydrated, authReady, session, lastAvatarJob, setLastAvatarJob]);

  if (deciding) {
    return (
      <Screen>
        <View style={styles.splash}>
          <Text style={styles.kicker}>
            PHYSIQ<Text style={{ color: colors.primary }}>AI</Text>
          </Text>
        </View>
      </Screen>
    );
  }

  return (
    <Screen>
      <View style={styles.container}>
        <View style={styles.hero}>
          <Text style={styles.kicker}>PHYSIQ<Text style={{ color: colors.primary }}>AI</Text></Text>
          <Text style={styles.title}>See your{'\n'}future physique.</Text>
          <Text style={styles.sub}>
            A realistic, science-backed look at where your body is actually heading —
            with your real face. Not fantasy.
          </Text>
        </View>
        <View>
          <Button
            title="Get Started"
            onPress={() => {
              reset();
              router.push('/consent');
            }}
          />
          {session && (
            <Button
              title="Go to my dashboard"
              variant="ghost"
              onPress={() => router.push('/home')}
            />
          )}
          <Text style={styles.fine}>Science-based · Personalized · Your photo stays private</Text>
        </View>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'space-between', paddingVertical: space.xl },
  splash: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  hero: { flex: 1, justifyContent: 'center' },
  kicker: { color: colors.foreground, fontSize: font.lg, fontWeight: weight.heavy, letterSpacing: 2, marginBottom: space.lg },
  title: { color: colors.foreground, fontSize: font['4xl'], fontWeight: weight.heavy, lineHeight: 44, marginBottom: space.md },
  sub: { color: colors.muted, fontSize: font.lg, lineHeight: 26 },
  fine: { color: colors.muted, fontSize: font.xs, textAlign: 'center', marginTop: space.md },
});
