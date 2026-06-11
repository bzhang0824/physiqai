// Home hub — the Tamagotchi screen. Your future self lives here: spinnable
// avatar front and center, streak, on-track state, countdown to the projected
// date, and the daily/weekly actions that make it evolve.
import { Image } from 'expo-image';
import { router } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Dimensions,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { SpinViewer } from '@/components/SpinViewer';
import { StateBadge } from '@/components/StateBadge';
import { WorkoutLogButton } from '@/components/WorkoutLogButton';
import { Button, Screen } from '@/components/ui';
import {
  type ProgressSummary,
  getAvatarStatus,
  getLatestAvatar,
  getProgress,
} from '@/lib/api';
import { type AvatarStatus, useStore } from '@/lib/store';
import { colors, font, radius, space, weight } from '@/lib/theme';

// Weeks remaining until the projection date the avatar was baked for.
function weeksToProjection(av: AvatarStatus): number | null {
  if (!av.projection?.months || !av.created_at) return null;
  try {
    const target =
      new Date(av.created_at).getTime() +
      av.projection.months * 30.44 * 86_400_000;
    return Math.ceil((target - Date.now()) / (7 * 86_400_000));
  } catch {
    return null;
  }
}

export default function HomeScreen() {
  const session = useStore((s) => s.session);
  const authReady = useStore((s) => s.authReady);
  const hasHydrated = useStore((s) => s.hasHydrated);
  const lastAvatarJob = useStore((s) => s.lastAvatarJob);
  const storeAvatar = useStore((s) => s.avatarStatus);
  const setAvatarStatus = useStore((s) => s.setAvatarStatus);
  const setLastAvatarJob = useStore((s) => s.setLastAvatarJob);

  const redirectedRef = useRef(false);
  useEffect(() => {
    if (!authReady) return;
    if (!session && !redirectedRef.current) {
      redirectedRef.current = true;
      router.replace('/signin');
    }
  }, [authReady, session]);

  const [progress, setProgress] = useState<ProgressSummary | null>(null);
  const [avatar, setAvatar] = useState<AvatarStatus | null>(
    storeAvatar?.status === 'done' ? storeAvatar : null
  );
  const [loading, setLoading] = useState(true);

  const loadedRef = useRef(false);
  useEffect(() => {
    if (!session || !hasHydrated || loadedRef.current) return;
    loadedRef.current = true;
    (async () => {
      const progressP = getProgress().catch(() => null);
      let av: AvatarStatus | null =
        storeAvatar?.status === 'done' ? storeAvatar : null;
      if (!av) {
        try {
          av = lastAvatarJob
            ? await getAvatarStatus(lastAvatarJob)
            : await getLatestAvatar();
          if (!av || av.status === 'failed') av = lastAvatarJob ? await getLatestAvatar() : av;
        } catch {
          av = null;
        }
      }
      if (av) {
        setAvatar(av);
        setAvatarStatus(av);
        setLastAvatarJob(av.job);
      }
      setProgress(await progressP);
      setLoading(false);
    })();
  }, [session, hasHydrated]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!authReady || !session) {
    return (
      <Screen>
        <View />
      </Screen>
    );
  }

  const screenWidth = Dimensions.get('window').width;
  const spinHeight = Math.min(screenWidth * 1.05, 420);
  const inProgress =
    avatar && avatar.status !== 'done' && avatar.status !== 'failed';
  const weeksLeft = avatar ? weeksToProjection(avatar) : null;
  const proj = avatar?.projection ?? null;
  const currentWeight = progress?.current_weight_lb ?? proj?.weight_before_lb ?? null;
  const currentBf = progress?.current_bf_pct ?? proj?.bf_before ?? null;

  return (
    <Screen scroll>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.kicker}>
          PHYSIQ<Text style={{ color: colors.primary }}>AI</Text>
        </Text>
        <View style={styles.headerRight}>
          {progress != null && progress.streak_weeks > 0 && (
            <View style={styles.streakChip}>
              <Text style={styles.streakText}>🔥 {progress.streak_weeks}w</Text>
            </View>
          )}
          <Pressable onPress={() => router.push('/settings')} hitSlop={8}>
            <Text style={styles.gear}>⚙</Text>
          </Pressable>
        </View>
      </View>

      {/* Centerpiece: the future self */}
      {loading ? (
        <View style={[styles.stagePlaceholder, { height: spinHeight }]}>
          <ActivityIndicator size="large" color={colors.primary} />
        </View>
      ) : avatar?.status === 'done' && avatar.frames ? (
        <Pressable
          onPress={() =>
            router.push({ pathname: '/avatar', params: { job: avatar.job } })
          }
        >
          <SpinViewer
            frames={avatar.frames}
            posterUrl={avatar.after_url}
            height={spinHeight}
          />
        </Pressable>
      ) : avatar?.status === 'done' && avatar.after_url ? (
        <Pressable
          onPress={() =>
            router.push({ pathname: '/avatar', params: { job: avatar.job } })
          }
        >
          <Image
            source={{ uri: avatar.after_url }}
            style={[styles.still, { height: spinHeight }]}
            contentFit="contain"
          />
        </Pressable>
      ) : inProgress ? (
        <Pressable
          onPress={() =>
            router.push({ pathname: '/avatar', params: { job: avatar!.job } })
          }
          style={[styles.stagePlaceholder, { height: spinHeight * 0.5 }]}
        >
          <ActivityIndicator size="small" color={colors.primary} />
          <Text style={styles.progressText}>
            Sculpting your future self… {avatar!.progress_pct}%
          </Text>
          <Text style={styles.progressSub}>tap to watch</Text>
        </Pressable>
      ) : (
        <View style={[styles.stagePlaceholder, { height: spinHeight * 0.55 }]}>
          <Text style={styles.emptyTitle}>No avatar yet</Text>
          <Text style={styles.emptySub}>
            Generate your photoreal 3D future self in about 6 minutes.
          </Text>
          <Button title="Create my avatar" onPress={() => router.push('/')} />
        </View>
      )}

      {/* State + countdown */}
      <View style={styles.stateRow}>
        {progress?.state ? <StateBadge state={progress.state} /> : <View />}
        {weeksLeft != null && (
          <Text style={styles.countdown}>
            {weeksLeft > 0
              ? `${weeksLeft} week${weeksLeft === 1 ? '' : 's'} to your projection`
              : 'Projection date reached 🎉'}
          </Text>
        )}
      </View>

      {/* Current vs projected */}
      {proj && (
        <View style={styles.projCard}>
          <View style={styles.projCol}>
            <Text style={styles.projHead}>Now</Text>
            {currentWeight != null && (
              <Text style={styles.projVal}>{Math.round(currentWeight)} lb</Text>
            )}
            {currentBf != null && (
              <Text style={styles.projSub}>{currentBf.toFixed(1)}% bf</Text>
            )}
          </View>
          <Text style={styles.projArrow}>→</Text>
          <View style={styles.projCol}>
            <Text style={styles.projHead}>Projected</Text>
            <Text style={styles.projVal}>{Math.round(proj.weight_after_lb)} lb</Text>
            <Text style={styles.projSub}>{proj.bf_after.toFixed(1)}% bf</Text>
          </View>
        </View>
      )}

      {/* Quick actions */}
      <WorkoutLogButton initial={progress?.workouts} />
      <Button title="Weekly check-in" onPress={() => router.push('/checkin')} />
      <Button
        title="Evolution timeline"
        variant="ghost"
        onPress={() => router.push('/evolution')}
      />
      <Button
        title="Progress dashboard"
        variant="ghost"
        onPress={() => router.push('/progress')}
      />
      <View style={{ height: space.xl }} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: space.sm,
    marginBottom: space.md,
  },
  kicker: {
    color: colors.foreground,
    fontSize: font.lg,
    fontWeight: weight.heavy,
    letterSpacing: 2,
  },
  headerRight: { flexDirection: 'row', alignItems: 'center', gap: space.md },
  streakChip: {
    backgroundColor: colors.primarySoft,
    borderRadius: radius.pill,
    paddingHorizontal: space.md,
    paddingVertical: space.xs,
  },
  streakText: {
    color: colors.primary,
    fontSize: font.sm,
    fontWeight: weight.bold,
  },
  gear: { fontSize: font.xl, color: colors.muted },
  stagePlaceholder: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
    padding: space.lg,
    marginBottom: space.sm,
  },
  still: { width: '100%', borderRadius: radius.lg, backgroundColor: '#000' },
  progressText: {
    color: colors.foreground,
    fontSize: font.base,
    fontWeight: weight.semibold,
    marginTop: space.md,
  },
  progressSub: { color: colors.muted, fontSize: font.sm, marginTop: space.xs },
  emptyTitle: {
    color: colors.foreground,
    fontSize: font.xl,
    fontWeight: weight.bold,
    marginBottom: space.xs,
  },
  emptySub: {
    color: colors.muted,
    fontSize: font.sm,
    textAlign: 'center',
    marginBottom: space.md,
  },
  stateRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: space.sm,
    flexWrap: 'wrap',
  },
  countdown: {
    color: colors.muted,
    fontSize: font.sm,
    fontWeight: weight.semibold,
    marginBottom: space.md,
  },
  projCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    backgroundColor: colors.card,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: space.md,
    marginBottom: space.md,
  },
  projCol: { alignItems: 'center' },
  projHead: {
    color: colors.muted,
    fontSize: font.xs,
    fontWeight: weight.bold,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    marginBottom: space.xs,
  },
  projVal: { color: colors.foreground, fontSize: font.xl, fontWeight: weight.heavy },
  projSub: { color: colors.muted, fontSize: font.sm, marginTop: 2 },
  projArrow: { color: colors.faint, fontSize: font['2xl'] },
});
