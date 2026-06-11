// Drag-spin photoreal turntable viewer — extracted verbatim from avatar.tsx so
// the home hub can embed the same spin. Web gotchas preserved: the frame image
// must keep pointerEvents:'none' (the browser's native image-drag otherwise
// hijacks the pointer stream and the Pan gesture never fires) and the gesture
// runs with runOnJS(true).
import { Image } from 'expo-image';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Dimensions,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';

import { AvatarFrames } from '@/lib/store';
import { colors, font, radius, space } from '@/lib/theme';

// ── Constants ─────────────────────────────────────────────────────────────────
const PX_PER_FRAME = 5;
const COAST_DECAY = 0.95;
const COAST_THRESHOLD = 0.05;

// ── Angle badge helper ────────────────────────────────────────────────────────
export function angleBadge(idx: number, n: number): string {
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
export function frameUrl(baseUrl: string, i: number, ext: string): string {
  return `${baseUrl}/f${String(i).padStart(3, '0')}.${ext}`;
}

// ── Drag-spin viewer ──────────────────────────────────────────────────────────
export function SpinViewer({
  frames,
  height,
  posterUrl,
  showHint = true,
}: {
  frames: AvatarFrames;
  height?: number;
  // Optional after-still shown while frames prefetch (first paint must never
  // wait on all frames — hard-won lesson from the standalone viewer).
  posterUrl?: string | null;
  showHint?: boolean;
}) {
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
  // Stage height: tall portrait crop (slightly taller than width) by default.
  const stageHeight = height ?? Math.min(screenWidth * 1.3, 520);
  const currentUrl = urls[displayIdx] ?? urls[0];

  if (!ready) {
    if (posterUrl) {
      // Poster-first render: show the still immediately, frames stream behind it.
      return (
        <View style={[styles.stage, { height: stageHeight }]}>
          <Image
            source={{ uri: posterUrl }}
            style={styles.frameImg}
            contentFit="contain"
            cachePolicy="memory-disk"
          />
          <View style={styles.posterOverlay} pointerEvents="none">
            <ActivityIndicator size="small" color="#FFFFFF" />
            <Text style={styles.posterText}>
              loading spin… {loadedCount}/{N}
            </Text>
          </View>
        </View>
      );
    }
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
          {showHint && (
            <View style={styles.hint} pointerEvents="none">
              <Text style={styles.hintText}>drag to rotate · flick to spin</Text>
            </View>
          )}
        </View>
      </GestureDetector>
    </View>
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
  posterOverlay: {
    position: 'absolute',
    bottom: 12,
    left: 0,
    right: 0,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: space.sm,
  },
  posterText: {
    color: '#FFFFFF',
    fontSize: font.xs,
    fontWeight: '600',
  },
});
