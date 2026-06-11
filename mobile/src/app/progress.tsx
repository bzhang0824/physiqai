// Progress dashboard: streak, last check-in, weight/bf, recent check-in history,
// and CTAs to check in + view the latest avatar.
import { router } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { Button, Screen } from '@/components/ui';
import { type CheckinEntry, type ProgressSummary, getProgress } from '@/lib/api';
import { useStore } from '@/lib/store';
import { colors, font, radius, space } from '@/lib/theme';

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtDate(iso: string | null): string {
  if (!iso) return 'Never';
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return iso;
  }
}

function fmtRelativeDate(iso: string): string {
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const days = Math.floor(diff / 86_400_000);
    if (days === 0) return 'Today';
    if (days === 1) return 'Yesterday';
    if (days < 7) return `${days}d ago`;
    const weeks = Math.floor(days / 7);
    return `${weeks}w ago`;
  } catch {
    return iso;
  }
}

// ── Stat tile ─────────────────────────────────────────────────────────────────

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.tile}>
      <Text style={styles.tileVal}>{value}</Text>
      <Text style={styles.tileLabel}>{label}</Text>
    </View>
  );
}

// ── Checkin row ───────────────────────────────────────────────────────────────

function CheckinRow({ entry }: { entry: CheckinEntry }) {
  return (
    <View style={styles.checkinRow}>
      <Text style={styles.checkinDate}>{fmtRelativeDate(entry.created_at)}</Text>
      <View style={styles.checkinMeta}>
        {entry.weight_lb != null && (
          <Text style={styles.checkinStat}>{entry.weight_lb} lb</Text>
        )}
        {entry.bf_pct != null && (
          <Text style={styles.checkinStat}>{entry.bf_pct}% bf</Text>
        )}
        {entry.workouts_done != null && (
          <Text style={styles.checkinStat}>{entry.workouts_done} workouts</Text>
        )}
        {entry.rebake_triggered && (
          <Text style={styles.rebakeBadge}>avatar updated</Text>
        )}
      </View>
      {entry.note ? <Text style={styles.checkinNote}>{entry.note}</Text> : null}
    </View>
  );
}

// ── Main screen ───────────────────────────────────────────────────────────────

export default function ProgressScreen() {
  const session = useStore((s) => s.session);
  const authReady = useStore((s) => s.authReady);

  const redirectedRef = useRef(false);
  useEffect(() => {
    if (!authReady) return;
    if (!session && !redirectedRef.current) {
      redirectedRef.current = true;
      router.replace('/signin');
    }
  }, [authReady, session]);

  const [data, setData] = useState<ProgressSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!session) return;
    let cancelled = false;
    (async () => {
      try {
        const summary = await getProgress();
        if (!cancelled) setData(summary);
      } catch (e: unknown) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Could not load progress.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [session]);

  if (!authReady || !session) {
    return <Screen><View /></Screen>;
  }

  if (loading) {
    return (
      <Screen>
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      </Screen>
    );
  }

  if (error || !data) {
    return (
      <Screen>
        <View style={styles.center}>
          <Text style={styles.errorText}>{error ?? 'No data.'}</Text>
          <Button title="Retry" onPress={() => { setLoading(true); setError(null); }} />
        </View>
      </Screen>
    );
  }

  const recentCheckins = data.checkins.slice(0, 5);

  return (
    <Screen scroll>
      <Text style={styles.title}>Your Progress</Text>

      {/* Streak + overview tiles */}
      <View style={styles.tilesRow}>
        <StatTile
          label="Streak"
          value={data.streak_weeks > 0 ? `🔥 ${data.streak_weeks}w` : '—'}
        />
        <StatTile
          label="Last check-in"
          value={fmtDate(data.last_checkin_at)}
        />
      </View>

      <View style={styles.tilesRow}>
        {data.current_weight_lb != null && (
          <StatTile label="Weight" value={`${data.current_weight_lb} lb`} />
        )}
        {data.current_bf_pct != null && (
          <StatTile label="Body fat" value={`${data.current_bf_pct}%`} />
        )}
      </View>

      {/* Avatar CTA */}
      {data.latest_avatar && (
        <View style={styles.avatarCard}>
          <Text style={styles.avatarCardLabel}>Latest avatar</Text>
          <Text style={styles.avatarCardStatus}>
            {data.latest_avatar.status === 'done' ? 'Ready to spin' : data.latest_avatar.status}
          </Text>
          <Button
            title="View avatar"
            onPress={() =>
              router.push({
                pathname: '/avatar',
                params: { job: data.latest_avatar!.job },
              })
            }
          />
        </View>
      )}

      {/* Check-in CTA */}
      <Button title="Check in this week" onPress={() => router.push('/checkin')} />

      {/* Recent check-ins */}
      {recentCheckins.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent check-ins</Text>
          {recentCheckins.map((entry) => (
            <CheckinRow key={entry.id} entry={entry} />
          ))}
        </View>
      )}

      {recentCheckins.length === 0 && (
        <View style={styles.emptyState}>
          <Text style={styles.emptyText}>No check-ins yet. Log this week to start your streak.</Text>
        </View>
      )}

      <Button title="Settings" variant="ghost" onPress={() => router.push('/settings')} />
      <View style={{ height: space.xl }} />
    </Screen>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  title: {
    color: colors.foreground,
    fontSize: font['2xl'],
    fontWeight: '800',
    marginVertical: space.md,
  },
  tilesRow: {
    flexDirection: 'row',
    gap: space.sm,
    marginBottom: space.sm,
  },
  tile: {
    flex: 1,
    backgroundColor: colors.card,
    borderRadius: radius.md,
    padding: space.md,
    alignItems: 'center',
  },
  tileVal: {
    color: colors.foreground,
    fontSize: font.xl,
    fontWeight: '800',
    marginBottom: space.xs,
  },
  tileLabel: { color: colors.muted, fontSize: font.xs, fontWeight: '600' },
  avatarCard: {
    backgroundColor: colors.card,
    borderRadius: radius.lg,
    padding: space.md,
    marginTop: space.sm,
    marginBottom: space.sm,
    borderWidth: 1,
    borderColor: colors.secondary,
  },
  avatarCardLabel: {
    color: colors.muted,
    fontSize: font.xs,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: space.xs,
  },
  avatarCardStatus: {
    color: colors.foreground,
    fontSize: font.base,
    fontWeight: '600',
    marginBottom: space.xs,
  },
  section: { marginTop: space.lg },
  sectionTitle: {
    color: colors.foreground,
    fontSize: font.lg,
    fontWeight: '700',
    marginBottom: space.sm,
  },
  checkinRow: {
    backgroundColor: colors.card,
    borderRadius: radius.md,
    padding: space.md,
    marginBottom: space.sm,
  },
  checkinDate: {
    color: colors.muted,
    fontSize: font.xs,
    fontWeight: '600',
    marginBottom: space.xs,
  },
  checkinMeta: { flexDirection: 'row', flexWrap: 'wrap', gap: space.sm, marginBottom: space.xs },
  checkinStat: {
    color: colors.foreground,
    fontSize: font.sm,
    fontWeight: '600',
  },
  rebakeBadge: {
    color: colors.primary,
    fontSize: font.xs,
    fontWeight: '700',
    backgroundColor: 'rgba(34,197,94,0.12)',
    paddingHorizontal: space.sm,
    paddingVertical: 2,
    borderRadius: radius.pill,
  },
  checkinNote: {
    color: colors.muted,
    fontSize: font.sm,
    fontStyle: 'italic',
  },
  emptyState: {
    marginTop: space.lg,
    alignItems: 'center',
    paddingHorizontal: space.lg,
  },
  emptyText: {
    color: colors.muted,
    fontSize: font.base,
    textAlign: 'center',
    lineHeight: 22,
  },
  errorText: {
    color: colors.destructive,
    fontSize: font.base,
    marginBottom: space.md,
    textAlign: 'center',
  },
});
