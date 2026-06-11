// Evolution timeline — every version of your avatar as your body changes.
// The most motivating artifact we have: watch yourself evolve, bake by bake.
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { Button, Screen } from '@/components/ui';
import { type AvatarListEntry, listAvatars } from '@/lib/api';
import { useStore } from '@/lib/store';
import { colors, font, radius, space, weight } from '@/lib/theme';

function fmtDate(iso: string): string {
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

function EntryCard({
  entry,
  isLatest,
  isFirst,
}: {
  entry: AvatarListEntry;
  isLatest: boolean;
  isFirst: boolean;
}) {
  const done = entry.status === 'done';
  const stats =
    entry.weight_lb != null
      ? `${Math.round(entry.weight_lb)} lb${entry.bf_pct != null ? ` · ${entry.bf_pct.toFixed(0)}% bf` : ''}`
      : null;
  const proj = entry.projection;

  const body = (
    <View style={styles.card}>
      <View style={styles.thumbWrap}>
        {entry.after_url ? (
          <Image
            source={{ uri: entry.after_url }}
            style={styles.thumb}
            contentFit="cover"
          />
        ) : (
          <View style={[styles.thumb, styles.thumbEmpty]}>
            <Text style={styles.thumbEmptyText}>
              {done ? '—' : 'evolving…'}
            </Text>
          </View>
        )}
      </View>
      <View style={styles.meta}>
        <View style={styles.chipRow}>
          {isLatest && <Text style={styles.chipLatest}>Latest</Text>}
          {isFirst && !isLatest && <Text style={styles.chipDay1}>Day 1</Text>}
          {!done && <Text style={styles.chipBaking}>baking…</Text>}
        </View>
        <Text style={styles.date}>{fmtDate(entry.created_at)}</Text>
        {stats && <Text style={styles.stats}>{stats}</Text>}
        {proj && (
          <Text style={styles.proj}>
            → {Math.round(proj.weight_after_lb)} lb · {proj.bf_after.toFixed(0)}%
            in {proj.months} mo
          </Text>
        )}
        {done && <Text style={styles.tapHint}>tap to spin</Text>}
      </View>
    </View>
  );

  if (!done) return body;
  return (
    <Pressable
      onPress={() =>
        router.push({ pathname: '/avatar', params: { job: entry.job } })
      }
    >
      {body}
    </Pressable>
  );
}

export default function EvolutionScreen() {
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

  const [entries, setEntries] = useState<AvatarListEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!session) return;
    let cancelled = false;
    (async () => {
      try {
        const list = await listAvatars();
        if (!cancelled) setEntries(list);
      } catch (e: unknown) {
        if (!cancelled)
          setError(e instanceof Error ? e.message : 'Could not load your timeline.');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [session]);

  if (!authReady || !session) {
    return (
      <Screen>
        <View />
      </Screen>
    );
  }

  return (
    <Screen scroll>
      <Text style={styles.title}>Your evolution</Text>
      <Text style={styles.subtitle}>
        Every version of your future self, newest first.
      </Text>

      {entries == null && !error && (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      )}

      {error && (
        <View style={styles.center}>
          <Text style={styles.errorText}>{error}</Text>
          <Button title="Back" variant="ghost" onPress={() => router.back()} />
        </View>
      )}

      {entries != null && entries.length === 0 && (
        <View style={styles.center}>
          <Text style={styles.emptyText}>
            No avatars yet — generate your first future self to start the
            timeline.
          </Text>
          <Button title="Generate my avatar" onPress={() => router.push('/')} />
        </View>
      )}

      {entries != null &&
        entries.map((e, i) => (
          <EntryCard
            key={e.job}
            entry={e}
            isLatest={i === 0}
            isFirst={i === entries.length - 1}
          />
        ))}

      {entries != null && entries.length === 1 && (
        <View style={styles.footerCard}>
          <Text style={styles.footerText}>
            Check in weekly — when your real trajectory shifts, your avatar
            re-bakes and a new version lands here.
          </Text>
          <Button title="Check in" onPress={() => router.push('/checkin')} />
        </View>
      )}
      <View style={{ height: space.xl }} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: {
    color: colors.foreground,
    fontSize: font['2xl'],
    fontWeight: weight.heavy,
    marginTop: space.md,
  },
  subtitle: {
    color: colors.muted,
    fontSize: font.sm,
    marginBottom: space.lg,
  },
  center: { alignItems: 'center', paddingVertical: space.xxl, gap: space.md },
  card: {
    flexDirection: 'row',
    backgroundColor: colors.card,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: space.sm,
    marginBottom: space.md,
  },
  thumbWrap: { marginRight: space.md },
  thumb: {
    width: 110,
    height: 146,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
  },
  thumbEmpty: { alignItems: 'center', justifyContent: 'center' },
  thumbEmptyText: { color: colors.faint, fontSize: font.sm },
  meta: { flex: 1, justifyContent: 'center' },
  chipRow: { flexDirection: 'row', gap: space.sm, marginBottom: space.xs },
  chipLatest: {
    color: colors.primary,
    backgroundColor: colors.primarySoft,
    fontSize: font.xs,
    fontWeight: weight.bold,
    paddingHorizontal: space.sm,
    paddingVertical: 2,
    borderRadius: radius.pill,
    overflow: 'hidden',
  },
  chipDay1: {
    color: colors.muted,
    backgroundColor: colors.surface,
    fontSize: font.xs,
    fontWeight: weight.bold,
    paddingHorizontal: space.sm,
    paddingVertical: 2,
    borderRadius: radius.pill,
    overflow: 'hidden',
  },
  chipBaking: {
    color: colors.secondary,
    fontSize: font.xs,
    fontWeight: weight.bold,
  },
  date: { color: colors.muted, fontSize: font.xs, fontWeight: weight.semibold },
  stats: {
    color: colors.foreground,
    fontSize: font.lg,
    fontWeight: weight.bold,
    marginTop: 2,
  },
  proj: { color: colors.primary, fontSize: font.sm, fontWeight: weight.semibold, marginTop: 2 },
  tapHint: { color: colors.faint, fontSize: font.xs, marginTop: space.xs },
  errorText: {
    color: colors.destructive,
    fontSize: font.base,
    textAlign: 'center',
  },
  emptyText: {
    color: colors.muted,
    fontSize: font.base,
    textAlign: 'center',
    lineHeight: 22,
  },
  footerCard: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: space.md,
    gap: space.sm,
  },
  footerText: { color: colors.muted, fontSize: font.sm, lineHeight: 20 },
});
