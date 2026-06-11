// Avatar screen: shows generation progress, then a drag-spin photoreal turntable
// (the spin itself lives in components/SpinViewer so the home hub can embed it).
import { useLocalSearchParams, router } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { SpinViewer } from '@/components/SpinViewer';
import { Button, Screen } from '@/components/ui';
import { getAvatarStatus, getLatestAvatar, refreshAvatar, startAvatar } from '@/lib/api';
import { AvatarStatus, useStore } from '@/lib/store';
import { colors, font, radius, space } from '@/lib/theme';

// ── Constants ─────────────────────────────────────────────────────────────────
const POLL_INTERVAL_MS = 3000;

// ── Stage label map ───────────────────────────────────────────────────────────
const STAGE_LABELS: Record<string, string> = {
  queued: 'Warming up…',
  after_still: 'Sculpting your future physique…',
  orbiting: 'Filming your 360° turntable…',
  matting: 'Lifting you off the background…',
  extracting: 'Preparing your spin…',
};

// ── Progress view ─────────────────────────────────────────────────────────────
function ProgressView({
  status,
  onRetry,
}: {
  status: AvatarStatus | undefined;
  onRetry: () => void;
}) {
  const label =
    status?.status && status.status !== 'failed'
      ? (STAGE_LABELS[status.status] ?? 'Working…')
      : 'Starting up…';
  const pct = status?.progress_pct ?? 0;

  if (status?.status === 'failed') {
    return (
      <View style={styles.center}>
        <Text style={styles.errTitle}>Generation failed</Text>
        <Text style={styles.errDetail}>{status.error ?? 'Unknown error'}</Text>
        <Button title="Retry" onPress={onRetry} />
      </View>
    );
  }

  return (
    <View style={styles.center}>
      <ActivityIndicator size="large" color={colors.primary} />
      <Text style={styles.stageLabel}>{label}</Text>
      <View style={styles.progressTrack}>
        <View style={[styles.progressFill, { width: `${pct}%` }]} />
      </View>
      <Text style={styles.pctText}>{pct}%</Text>
      <Text style={styles.timeNote}>~6 minutes — feel free to keep the app open</Text>
    </View>
  );
}

// ── Main screen ───────────────────────────────────────────────────────────────
export default function AvatarScreen() {
  const params = useLocalSearchParams<{ start?: string; job?: string }>();
  const lastAvatarJob = useStore((s) => s.lastAvatarJob);
  const hasHydrated = useStore((s) => s.hasHydrated);
  const setLastAvatarJob = useStore((s) => s.setLastAvatarJob);
  const avatarStatus = useStore((s) => s.avatarStatus);
  const setAvatarStatus = useStore((s) => s.setAvatarStatus);
  const photos = useStore((s) => s.photos);
  const stats = useStore((s) => s.stats);
  const session = useStore((s) => s.session);

  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startedRef = useRef(false);
  const [noAvatar, setNoAvatar] = useState(false);

  // ── polling ────────────────────────────────────────────────────────────────
  const stopPoll = useCallback(() => {
    if (pollRef.current !== null) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const pollJob = useCallback(
    async (job: string) => {
      try {
        const s = await getAvatarStatus(job);
        setAvatarStatus(s);
        if (s.status === 'done' || s.status === 'failed') {
          stopPoll();
        }
      } catch {
        // swallow network errors; keep polling
      }
    },
    [setAvatarStatus, stopPoll]
  );

  const startPoll = useCallback(
    (job: string) => {
      stopPoll();
      // Immediate first check, then interval.
      pollJob(job);
      pollRef.current = setInterval(() => pollJob(job), POLL_INTERVAL_MS);
    },
    [pollJob, stopPoll]
  );

  // ── start a new generation ─────────────────────────────────────────────────
  const startGeneration = useCallback(async () => {
    if (!session) {
      router.replace('/signin');
      return;
    }
    if (!photos.front) {
      router.replace('/');
      return;
    }
    try {
      setAvatarStatus(undefined); // clear stale status
      const { job } = await startAvatar(photos, stats);
      setLastAvatarJob(job);
      startPoll(job);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Unknown error';
      setAvatarStatus({
        job: '',
        status: 'failed',
        progress_pct: 0,
        error: msg,
        projection: null,
        after_url: null,
        frames: null,
        master_url: null,
        created_at: new Date().toISOString(),
      });
    }
  }, [session, photos, stats, setAvatarStatus, setLastAvatarJob, startPoll]);

  // ── mount logic ────────────────────────────────────────────────────────────
  // Must wait for AsyncStorage hydration before reading persisted fields
  // (userKey, lastAvatarJob) — acting before hydration would see the in-memory
  // defaults and could trigger a duplicate generation.
  useEffect(() => {
    if (!hasHydrated) return;
    if (startedRef.current) return;
    startedRef.current = true;

    (async () => {
      // 0. Explicit deep-link to a specific job (?job=...) wins over everything.
      if (params.job) {
        setLastAvatarJob(params.job);
        startPoll(params.job);
        return;
      }

      // 1. start=1 = explicit intent to (re)generate for the plan just entered on
      //    results. This must take priority over showing a stale avatar — else a
      //    returning user who changed their plan would keep seeing their old one.
      //    Guard with should_rebake so an UNCHANGED plan shows the existing avatar
      //    instead of burning a fresh (paid) generation.
      if (params.start === '1') {
        try {
          const latest = await getLatestAvatar();
          if (latest && latest.status === 'done') {
            let changed = true;
            try {
              changed = (await refreshAvatar(latest.job, stats)).rebake_recommended;
            } catch {
              changed = true; // refresh check failed → safer to regenerate
            }
            if (!changed) {
              setAvatarStatus(latest);
              setLastAvatarJob(latest.job);
              return;
            }
          }
        } catch {
          // no existing avatar (404) — fall through to a fresh generation
        }
        startGeneration();
        return;
      }

      // 2. Already have an in-memory status that's done → show it.
      if (avatarStatus?.status === 'done') return;

      // 3. Resume a known job (status still in progress, or just persisted).
      if (lastAvatarJob) {
        startPoll(lastAvatarJob);
        return;
      }

      // 4. Try to load latest done avatar from the server.
      try {
        const latest = await getLatestAvatar();
        if (latest) {
          setAvatarStatus(latest);
          setLastAvatarJob(latest.job);
          if (latest.status !== 'done' && latest.status !== 'failed') {
            startPoll(latest.job);
          }
          return;
        }
      } catch {
        // ignore — fall through to empty state
      }

      // 5. Nothing to show and no intent to generate — explicit empty state
      // (never leave the user on an eternal "Starting up…" spinner).
      setNoAvatar(true);
    })();

    return stopPoll;
  }, [hasHydrated]); // eslint-disable-line react-hooks/exhaustive-deps

  const isDone = avatarStatus?.status === 'done' && avatarStatus.frames != null;

  if (noAvatar && !avatarStatus) {
    return (
      <Screen>
        <View style={styles.center}>
          <Text style={styles.title}>No avatar yet</Text>
          <Text style={styles.emptyDetail}>
            Generate your photoreal 3D future self — it takes about 6 minutes.
          </Text>
          <Button
            title="Generate my 3D avatar"
            onPress={() => {
              setNoAvatar(false);
              if (photos.front) {
                startGeneration();
              } else {
                // No photo in this session — run the normal flow first.
                router.replace('/');
              }
            }}
          />
          <Button
            title="Back to Results"
            variant="ghost"
            onPress={() => router.replace('/results')}
          />
          {session && (
            <Button
              title="Settings"
              variant="ghost"
              onPress={() => router.push('/settings')}
            />
          )}
        </View>
      </Screen>
    );
  }

  return (
    <Screen scroll={isDone}>
      {isDone ? (
        <>
          <Text style={styles.title}>Your future self in 3D</Text>
          <SpinViewer frames={avatarStatus.frames!} posterUrl={avatarStatus.after_url} />
          <View style={{ height: space.md }} />
          <Button
            title="Try a Different Plan"
            onPress={() => router.replace('/horizon')}
          />
          <Button
            title="Back to Results"
            variant="ghost"
            onPress={() => router.replace('/results')}
          />
          {session && (
            <Button
              title="Settings"
              variant="ghost"
              onPress={() => router.push('/settings')}
            />
          )}
          <View style={{ height: space.xl }} />
        </>
      ) : (
        <ProgressView
          status={avatarStatus}
          onRetry={() => {
            startedRef.current = false;
            startGeneration();
          }}
        />
      )}
    </Screen>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: space.lg,
  },
  title: {
    color: colors.foreground,
    fontSize: font['2xl'],
    fontWeight: '800',
    marginVertical: space.md,
  },
  // Progress
  stageLabel: {
    color: colors.foreground,
    fontSize: font.lg,
    fontWeight: '700',
    marginTop: space.lg,
    textAlign: 'center',
  },
  progressTrack: {
    width: '100%',
    maxWidth: 300,
    height: 4,
    backgroundColor: colors.border,
    borderRadius: radius.pill,
    marginTop: space.md,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: colors.primary,
    borderRadius: radius.pill,
  },
  pctText: {
    color: colors.muted,
    fontSize: font.sm,
    marginTop: space.xs,
  },
  timeNote: {
    color: colors.muted,
    fontSize: font.sm,
    textAlign: 'center',
    marginTop: space.md,
  },
  errTitle: {
    color: colors.destructive,
    fontSize: font['2xl'],
    fontWeight: '800',
    marginBottom: space.sm,
  },
  errDetail: {
    color: colors.foreground,
    fontSize: font.base,
    textAlign: 'center',
    marginBottom: space.md,
  },
  emptyDetail: {
    color: colors.muted,
    fontSize: font.base,
    textAlign: 'center',
    marginBottom: space.lg,
  },
});
