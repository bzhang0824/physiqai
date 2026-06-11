// Avatar screen: shows generation progress, then a drag-spin photoreal turntable.
// Logic ported from spike/viewer/index.html (img-swap approach, PX_PER_FRAME=5,
// flick-to-coast with v*=0.95 decay, angle badge with front/right/back/left).
import { Image } from 'expo-image';
import { useLocalSearchParams, router } from 'expo-router';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Dimensions,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';

import { Button, Screen } from '@/components/ui';
import { getAvatarStatus, getLatestAvatar, startAvatar } from '@/lib/api';
import { AvatarStatus, useStore } from '@/lib/store';
import { colors, font, radius, space } from '@/lib/theme';

// ── Constants ─────────────────────────────────────────────────────────────────
const PX_PER_FRAME = 5;
const COAST_DECAY = 0.95;
const COAST_THRESHOLD = 0.05;
const POLL_INTERVAL_MS = 3000;

// ── Stage label map ───────────────────────────────────────────────────────────
const STAGE_LABELS: Record<string, string> = {
  queued: 'Warming up…',
  after_still: 'Sculpting your future physique…',
  orbiting: 'Filming your 360° turntable…',
  matting: 'Lifting you off the background…',
  extracting: 'Preparing your spin…',
};

// ── Angle badge helper ────────────────────────────────────────────────────────
function angleBadge(idx: number, n: number): string {
  const deg = Math.round(((((idx % n) + n) % n) / n) * 360);
  const dir =
    deg < 45 || deg > 315
      ? 'front'
      : deg < 135
      ? 'right'
      : deg < 225
      ? 'back'
      : 'left';
  return `${dir} · ${deg}°`;
}

// ── Frame URL builder ─────────────────────────────────────────────────────────
function frameUrl(baseUrl: string, i: number, ext: string): string {
  return `${baseUrl}/f${String(i).padStart(3, '0')}.${ext}`;
}

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

// ── Drag-spin viewer ──────────────────────────────────────────────────────────
function SpinViewer({ status }: { status: AvatarStatus }) {
  const frames = status.frames!;
  const N = frames.count;
  const urls = useMemo(
    () =>
      Array.from({ length: N }, (_, i) => frameUrl(frames.base_url, i, frames.ext)),
    [frames.base_url, frames.count, frames.ext] // eslint-disable-line react-hooks/exhaustive-deps
  );

  const [loadedCount, setLoadedCount] = useState(0);
  const [ready, setReady] = useState(false);

  // Float frame index — mutated directly in gesture callbacks, then used in rAF.
  const idxRef = useRef<number>(0);
  const velRef = useRef<number>(0);
  const rafRef = useRef<number | null>(null);
  const dragStartIdxRef = useRef<number>(0);
  // We display via state so React re-renders on change.
  const [displayIdx, setDisplayIdx] = useState(0);
  const [badge, setBadge] = useState('front · 0°');

  // Preload all frames via expo-image's static prefetch.
  useEffect(() => {
    let cancelled = false;
    let done = 0;
    const total = urls.length;

    // Batch prefetch in groups of 8 to avoid flooding the network.
    const BATCH = 8;
    async function prefetchBatch(start: number) {
      if (cancelled || start >= total) return;
      const batch = urls.slice(start, start + BATCH);
      await Image.prefetch(batch, 'disk');
      if (!cancelled) {
        done += batch.length;
        setLoadedCount(done);
        if (done >= total) setReady(true);
        else prefetchBatch(start + BATCH);
      }
    }
    prefetchBatch(0);
    return () => { cancelled = true; };
  }, [urls]);

  // rAF coast loop (runs outside React, mutates ref then schedules setState).
  const coast = useCallback(() => {
    idxRef.current += velRef.current;
    velRef.current *= COAST_DECAY;
    const i = ((Math.round(idxRef.current) % N) + N) % N;
    setDisplayIdx(i);
    setBadge(angleBadge(idxRef.current, N));
    if (Math.abs(velRef.current) > COAST_THRESHOLD) {
      rafRef.current = requestAnimationFrame(coast);
    } else {
      rafRef.current = null;
    }
  }, [N]);

  // Cancel coast on unmount.
  useEffect(
    () => () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    },
    []
  );

  // Pan gesture — horizontal drag maps 1:1 to frame offset.
  const pan = useMemo(
    () =>
      Gesture.Pan()
        .activeOffsetX([-10, 10])
        .failOffsetY([-5, 5])
        .runOnJS(true)
        .onBegin(() => {
          if (rafRef.current !== null) {
            cancelAnimationFrame(rafRef.current);
            rafRef.current = null;
          }
          dragStartIdxRef.current = idxRef.current;
          velRef.current = 0;
        })
        .onUpdate((e) => {
          const newIdx = dragStartIdxRef.current + e.translationX / PX_PER_FRAME;
          idxRef.current = newIdx;
          velRef.current = e.velocityX / (PX_PER_FRAME * 60); // velocity in frames/frame
          const i = ((Math.round(newIdx) % N) + N) % N;
          setDisplayIdx(i);
          setBadge(angleBadge(newIdx, N));
        })
        .onEnd((e) => {
          // Convert RNGH velocity (px/s) to frames/frame at ~60fps.
          const v = e.velocityX / (PX_PER_FRAME * 60);
          velRef.current = v;
          if (Math.abs(v) > COAST_THRESHOLD) {
            rafRef.current = requestAnimationFrame(coast);
          }
        }),
    [N, coast]
  );

  const screenWidth = Dimensions.get('window').width;
  // Stage height: tall portrait crop (slightly taller than width).
  const stageHeight = Math.min(screenWidth * 1.3, 520);
  const currentUrl = urls[displayIdx] ?? urls[0];

  if (!ready) {
    return (
      <View style={[styles.stage, { height: stageHeight }]}>
        <View style={styles.center}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>
            Loading {loadedCount}/{N} frames…
          </Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.spinRoot}>
      <GestureDetector gesture={pan}>
        <View style={[styles.stage, { height: stageHeight }]}>
          <Image
            source={{ uri: currentUrl }}
            style={styles.frameImg}
            contentFit="contain"
            // Already in cache — instant display, no flicker.
            cachePolicy="memory-disk"
          />
          {/* Angle badge */}
          <View style={styles.badge} pointerEvents="none">
            <Text style={styles.badgeText}>{badge}</Text>
          </View>
          {/* Drag hint — fades into irrelevance once user has interacted */}
          <View style={styles.hint} pointerEvents="none">
            <Text style={styles.hintText}>drag to rotate · flick to spin</Text>
          </View>
        </View>
      </GestureDetector>
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
  const photoUri = useStore((s) => s.photoUri);
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
    if (!photoUri) {
      router.replace('/');
      return;
    }
    try {
      setAvatarStatus(undefined); // clear stale status
      const { job } = await startAvatar(photoUri, stats);
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
  }, [session, photoUri, stats, setAvatarStatus, setLastAvatarJob, startPoll]);

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

      // 1. Already have an in-memory status that's done → show it.
      if (avatarStatus?.status === 'done') return;

      // 2. Resume a known job (status still in progress, or just persisted).
      if (lastAvatarJob) {
        startPoll(lastAvatarJob);
        return;
      }

      // 3. Try to load latest done avatar from the server.
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
        // ignore — fall through to start
      }

      // 4. start=1 means navigate from results with intent to generate.
      if (params.start === '1') {
        startGeneration();
        return;
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
              if (photoUri) {
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
          <SpinViewer status={avatarStatus} />
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
  // Spin viewer
  spinRoot: {
    width: '100%',
    // Prevent horizontal scroll bleed — the gesture needs pan-y pass-through.
    overflow: 'hidden',
  },
  stage: {
    width: '100%',
    backgroundColor: '#000000',
    borderRadius: radius.lg,
    overflow: 'hidden',
    position: 'relative',
  },
  frameImg: {
    width: '100%',
    height: '100%',
    // The frame is purely presentational. Without this, the browser's native
    // image-drag (dragstart) hijacks the pointer stream on web and the Pan
    // gesture on the stage never fires.
    pointerEvents: 'none',
  },
  badge: {
    position: 'absolute',
    top: 12,
    alignSelf: 'center',
    backgroundColor: 'rgba(20,20,24,0.85)',
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.pill,
    paddingHorizontal: space.md,
    paddingVertical: 5,
  },
  badgeText: {
    color: colors.muted,
    fontSize: font.xs,
    fontWeight: '600',
  },
  hint: {
    position: 'absolute',
    bottom: 12,
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  hintText: {
    color: colors.muted,
    fontSize: font.xs,
  },
  loadingText: {
    color: colors.muted,
    fontSize: font.sm,
    marginTop: space.md,
  },
});
