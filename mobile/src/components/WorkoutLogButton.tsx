// One-tap "I worked out today" — the daily habit layer under the weekly
// check-in. Optimistic UI with a session-scoped undo; engine-free by design
// (the weekly check-in owns streaks/projections/rebakes).
import { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { logWorkout, undoWorkout, type WorkoutSummary } from '@/lib/api';
import { showAlert } from '@/lib/alert';
import { colors, font, radius, space, weight } from '@/lib/theme';

export function WorkoutLogButton({ initial }: { initial?: WorkoutSummary }) {
  const [weekDays, setWeekDays] = useState<boolean[]>(
    initial?.week_days ?? Array<boolean>(7).fill(false)
  );
  const [weekCount, setWeekCount] = useState(initial?.week_count ?? 0);
  const [todayLogId, setTodayLogId] = useState<string | null>(
    initial?.today_log_id ?? null
  );
  // Undo is only offered for a log created in THIS session — a log that was
  // already there on load is presumed intentional.
  const [sessionLogId, setSessionLogId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const logged = todayLogId != null;

  async function handleLog() {
    if (busy || logged) return;
    setBusy(true);
    const prevDays = weekDays;
    const prevCount = weekCount;
    // Optimistic flip — instant feedback, revert on failure.
    const optimistic = [...weekDays];
    optimistic[optimistic.length - 1] = true;
    setWeekDays(optimistic);
    setWeekCount(prevCount + 1);
    setTodayLogId('pending');
    try {
      const r = await logWorkout();
      setTodayLogId(r.id);
      setWeekCount(r.week_count);
      setWeekDays(r.week_days);
      if (!r.already_logged) setSessionLogId(r.id);
    } catch (e: unknown) {
      setWeekDays(prevDays);
      setWeekCount(prevCount);
      setTodayLogId(null);
      showAlert(
        'Could not log workout',
        e instanceof Error ? e.message : 'Please try again.'
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleUndo() {
    if (!sessionLogId || busy) return;
    setBusy(true);
    try {
      const r = await undoWorkout(sessionLogId);
      setTodayLogId(null);
      setSessionLogId(null);
      setWeekCount(r.week_count);
      setWeekDays((d) => {
        const nd = [...d];
        nd[nd.length - 1] = false;
        return nd;
      });
    } catch (e: unknown) {
      showAlert('Could not undo', e instanceof Error ? e.message : 'Please try again.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <Pressable
      onPress={handleLog}
      disabled={logged || busy}
      style={[styles.card, logged && styles.cardLogged]}
    >
      <View style={styles.mainRow}>
        {busy && !logged ? (
          <ActivityIndicator size="small" color={colors.primary} />
        ) : (
          <Text style={styles.titleText}>
            {logged ? `✓ Logged · ${weekCount} this week` : 'I worked out today 💪'}
          </Text>
        )}
        {logged && sessionLogId ? (
          <Pressable onPress={handleUndo} hitSlop={8}>
            <Text style={styles.undo}>Undo</Text>
          </Pressable>
        ) : null}
      </View>
      <View style={styles.dotRow}>
        {weekDays.map((on, i) => (
          <View
            key={i}
            style={[
              styles.dot,
              on &&
                (i === weekDays.length - 1 ? styles.dotToday : styles.dotPast),
            ]}
          />
        ))}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: space.md,
    marginBottom: space.sm,
  },
  cardLogged: {
    borderColor: colors.primary,
    backgroundColor: colors.primarySoft,
  },
  mainRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: space.sm,
  },
  titleText: {
    color: colors.foreground,
    fontSize: font.base,
    fontWeight: weight.bold,
  },
  undo: {
    color: colors.muted,
    fontSize: font.sm,
    fontWeight: weight.semibold,
    textDecorationLine: 'underline',
  },
  dotRow: { flexDirection: 'row', gap: space.sm },
  dot: {
    width: 10,
    height: 10,
    borderRadius: radius.pill,
    backgroundColor: colors.border,
  },
  dotPast: { backgroundColor: '#86d3a5' },
  dotToday: { backgroundColor: colors.primary },
});
