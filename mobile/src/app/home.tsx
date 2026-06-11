import { router } from 'expo-router';
import { useCallback, useState } from 'react';
import { ActivityIndicator, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useFocusEffect } from 'expo-router';

import { Button, Card, Screen, Subtitle, Title } from '@/components/ui';
import { showAlert } from '@/lib/alert';
import { getProgress, type ProgressSummary } from '@/lib/api';
import { ensureSession } from '@/lib/supabase';
import { colors, font, leading, radius, space, weight } from '@/lib/theme';

function relDate(iso: string | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export default function HomeScreen() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [data, setData] = useState<ProgressSummary | null>(null);
  const [error, setError] = useState<string | undefined>();
  const [noAuth, setNoAuth] = useState(false);

  const load = useCallback(async () => {
    setError(undefined);
    const session = await ensureSession();
    if (!session) {
      setNoAuth(true);
      setLoading(false);
      return;
    }
    setNoAuth(false);
    try {
      setData(await getProgress());
    } catch (e: any) {
      setError(e?.message ?? 'Could not load your progress.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  if (loading) {
    return (
      <Screen>
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      </Screen>
    );
  }

  if (noAuth) {
    return (
      <Screen>
        <View style={styles.center}>
          <Text style={styles.muted}>Couldn&apos;t start a session.</Text>
          <Text style={styles.fine}>
            Anonymous sign-in may be disabled in Supabase. Once it&apos;s on, tracking works automatically.
          </Text>
          <View style={styles.stretch}>
            <Button title="Retry" onPress={() => { setLoading(true); load(); }} />
          </View>
        </View>
      </Screen>
    );
  }

  const streak = data?.streak_weeks ?? 0;
  const hasAvatar = Boolean(data?.latest_avatar);
  const checkins = data?.checkins ?? [];

  return (
    <Screen>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => { setRefreshing(true); load(); }}
            tintColor={colors.primary}
          />
        }>
        <Title>Your progress</Title>
        <Subtitle>Log your workouts to keep your streak alive — and keep your avatar honest.</Subtitle>

        {/* Streak hero */}
        <Card style={styles.streakCard}>
          <Text style={styles.streakNum}>{streak}</Text>
          <Text style={styles.streakLabel}>
            week{streak === 1 ? '' : 's'} {streak > 0 ? 'on a streak 🔥' : '— start one today'}
          </Text>
          {data?.last_checkin_at ? (
            <Text style={styles.streakSub}>Last check-in {relDate(data.last_checkin_at)}</Text>
          ) : null}
        </Card>

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <Button title="Log a workout" onPress={() => router.push('/checkin')} />
        <Button
          title={hasAvatar ? 'See your body in 3D' : 'Create your avatar first'}
          variant="ghost"
          onPress={() => {
            // The /avatar route lives on the 3D-avatar branch. Once it merges, switch to
            // router.push('/avatar') so this opens the interactive viewer.
            if (hasAvatar) showAlert('Coming soon', 'Your interactive 3D body view is on the way.');
            else showAlert('No avatar yet', 'Generate your avatar to start tracking your transformation.');
          }}
        />

        {/* Recent history */}
        <Text style={styles.sectionHead}>Recent check-ins</Text>
        {checkins.length === 0 ? (
          <Card>
            <Text style={styles.muted}>No check-ins yet. Your first one starts the streak.</Text>
          </Card>
        ) : (
          <Card>
            {checkins.map((c, i) => (
              <View key={c.id} style={[styles.row, i === checkins.length - 1 && styles.rowLast]}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.rowTitle}>
                    {c.workouts_done} workout{c.workouts_done === 1 ? '' : 's'}
                  </Text>
                  {c.note ? <Text style={styles.rowNote}>{c.note}</Text> : null}
                </View>
                {c.rebake_triggered ? <Text style={styles.badge}>avatar updated</Text> : null}
                <Text style={styles.rowDate}>{relDate(c.created_at)}</Text>
              </View>
            ))}
          </Card>
        )}

        <View style={{ height: space.xl }} />
      </ScrollView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  scroll: { flexGrow: 1, paddingTop: space.sm },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: space.md },
  stretch: { alignSelf: 'stretch' },
  muted: { color: colors.muted, fontSize: font.base, textAlign: 'center' },
  fine: { color: colors.faint, fontSize: font.sm, textAlign: 'center', lineHeight: font.sm * leading.normal },
  error: { color: colors.destructive, fontSize: font.sm, marginTop: space.sm },
  streakCard: { alignItems: 'center', marginTop: space.md, paddingVertical: space.lg },
  streakNum: { color: colors.primary, fontSize: 64, fontWeight: weight.heavy, letterSpacing: -2, lineHeight: 68 },
  streakLabel: { color: colors.foreground, fontSize: font.lg, fontWeight: weight.bold, marginTop: space.xs },
  streakSub: { color: colors.muted, fontSize: font.sm, marginTop: space.sm },
  sectionHead: { color: colors.foreground, fontSize: font.lg, fontWeight: weight.bold, marginTop: space.xl, marginBottom: space.sm },
  row: { flexDirection: 'row', alignItems: 'center', paddingVertical: space.sm, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.border },
  rowLast: { borderBottomWidth: 0 },
  rowTitle: { color: colors.foreground, fontSize: font.base, fontWeight: weight.semibold },
  rowNote: { color: colors.muted, fontSize: font.sm, marginTop: 2 },
  rowDate: { color: colors.muted, fontSize: font.sm, marginLeft: space.sm },
  badge: { color: colors.primary, fontSize: font.xs, fontWeight: weight.bold, marginRight: space.sm },
});
