// Progress check-in screen: log this week's stats, show result + streak.
// Gated on Supabase session — redirects to /signin if unauthenticated.
import { router } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { Button, Screen } from '@/components/ui';
import {
  type CheckinResult,
  type ProgressState,
  postProgress,
} from '@/lib/api';
import { useStore } from '@/lib/store';
import { colors, font, radius, space } from '@/lib/theme';

// ── helpers ───────────────────────────────────────────────────────────────────

function parseOptionalFloat(raw: string): number | undefined {
  const trimmed = raw.trim();
  if (!trimmed) return undefined;
  const n = parseFloat(trimmed);
  return Number.isFinite(n) ? n : undefined;
}

function parseOptionalInt(raw: string): number | undefined {
  const trimmed = raw.trim();
  if (!trimmed) return undefined;
  const n = parseInt(trimmed, 10);
  return Number.isFinite(n) ? n : undefined;
}

function fmtDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return iso;
  }
}

// ── State badge ───────────────────────────────────────────────────────────────

const STATE_LABEL: Record<ProgressState, string> = {
  ahead: 'Ahead of schedule 💪',
  on_track: 'Right on track ✅',
  behind: 'A bit behind — keep going',
  evolving: 'Your future self is leveling up ✨',
};

const STATE_COLOR: Record<ProgressState, string> = {
  ahead: colors.primary,
  on_track: colors.secondary,
  behind: colors.accent,
  evolving: colors.primary,
};

// ── Stepper ───────────────────────────────────────────────────────────────────

function Stepper({
  label,
  value,
  onChange,
  min = 0,
  max = 14,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
}) {
  return (
    <View style={styles.stepperRow}>
      <Text style={styles.stepperLabel}>{label}</Text>
      <View style={styles.stepperControls}>
        <Pressable
          onPress={() => onChange(Math.max(min, value - 1))}
          style={styles.stepperBtn}>
          <Text style={styles.stepperBtnText}>−</Text>
        </Pressable>
        <Text style={styles.stepperVal}>{value}</Text>
        <Pressable
          onPress={() => onChange(Math.min(max, value + 1))}
          style={styles.stepperBtn}>
          <Text style={styles.stepperBtnText}>+</Text>
        </Pressable>
      </View>
    </View>
  );
}

// ── NumericInput ──────────────────────────────────────────────────────────────

function NumericInput({
  label,
  placeholder,
  value,
  onChangeText,
  unit,
}: {
  label: string;
  placeholder: string;
  value: string;
  onChangeText: (v: string) => void;
  unit?: string;
}) {
  return (
    <View style={styles.fieldWrap}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={value}
          onChangeText={onChangeText}
          placeholder={placeholder}
          placeholderTextColor={colors.muted}
          keyboardType="decimal-pad"
          returnKeyType="done"
        />
        {unit ? <Text style={styles.unit}>{unit}</Text> : null}
      </View>
    </View>
  );
}

// ── Result card ───────────────────────────────────────────────────────────────

function ResultCard({ result }: { result: CheckinResult }) {
  const stateColor = STATE_COLOR[result.state];
  const proj = result.projection;
  const baked = result.baked_projection;

  return (
    <View style={styles.resultCard}>
      {/* Streak */}
      <Text style={styles.streak}>
        {result.streak_weeks > 0 ? `🔥 ${result.streak_weeks}-week streak` : 'First check-in!'}
      </Text>

      {/* State badge */}
      <View style={[styles.stateBadge, { borderColor: stateColor }]}>
        <Text style={[styles.stateText, { color: stateColor }]}>
          {STATE_LABEL[result.state]}
        </Text>
      </View>

      {/* Projection comparison */}
      <View style={styles.projRow}>
        <View style={styles.projCol}>
          <Text style={styles.projHead}>Projected</Text>
          <Text style={styles.projVal}>{proj.bf_after.toFixed(1)}% bf</Text>
          <Text style={styles.projSub}>{proj.weight_after_lb} lb</Text>
        </View>
        <Text style={styles.projArrow}>vs</Text>
        <View style={styles.projCol}>
          <Text style={styles.projHead}>Avatar target</Text>
          <Text style={styles.projVal}>{baked.bf_after.toFixed(1)}% bf</Text>
          <Text style={styles.projSub}>{baked.weight_after_lb} lb</Text>
        </View>
      </View>

      {/* Rebake CTA or logged message */}
      {result.rebake_triggered && result.rebake_job ? (
        <Button
          title="See your avatar update"
          onPress={() =>
            router.push({ pathname: '/avatar', params: { job: result.rebake_job! } })
          }
        />
      ) : (
        <Text style={styles.loggedNote}>
          Logged. Your avatar updates when your trajectory shifts — keep logging.
        </Text>
      )}
    </View>
  );
}

// ── Main screen ───────────────────────────────────────────────────────────────

export default function CheckinScreen() {
  const session = useStore((s) => s.session);
  const authReady = useStore((s) => s.authReady);

  // Redirect if not authenticated
  const redirectedRef = useRef(false);
  useEffect(() => {
    if (!authReady) return;
    if (!session && !redirectedRef.current) {
      redirectedRef.current = true;
      router.replace('/signin');
    }
  }, [authReady, session]);

  // Form state
  const [weightRaw, setWeightRaw] = useState('');
  const [bfRaw, setBfRaw] = useState('');
  const [workouts, setWorkouts] = useState(0);
  const [note, setNote] = useState('');

  // Submission state
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CheckinResult | null>(null);
  const [noAvatarError, setNoAvatarError] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Validation
  const [fieldErrors, setFieldErrors] = useState<{ weight?: string; bf?: string }>({});

  function validate(): boolean {
    const errs: { weight?: string; bf?: string } = {};
    if (weightRaw.trim()) {
      const n = parseOptionalFloat(weightRaw);
      if (n === undefined || n <= 0 || n > 999) errs.weight = 'Enter a valid weight (e.g. 185)';
    }
    if (bfRaw.trim()) {
      const n = parseOptionalFloat(bfRaw);
      if (n === undefined || n <= 0 || n > 70) errs.bf = 'Enter a valid body-fat % (e.g. 18)';
    }
    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit() {
    if (!validate()) return;
    setLoading(true);
    setError(null);
    setNoAvatarError(false);
    try {
      const body = {
        weight_lb: parseOptionalFloat(weightRaw),
        bf_pct: parseOptionalFloat(bfRaw),
        workouts_done: workouts > 0 ? workouts : parseOptionalInt(String(workouts)),
        note: note.trim() || undefined,
      };
      const res = await postProgress(body);
      setResult(res);
    } catch (e: unknown) {
      if (e instanceof Error && (e as Error & { status?: number }).status === 409) {
        setNoAvatarError(true);
      } else {
        setError(e instanceof Error ? e.message : 'Something went wrong. Try again.');
      }
    } finally {
      setLoading(false);
    }
  }

  if (!authReady || !session) {
    // Waiting for auth bootstrap or redirecting
    return <Screen><View /></Screen>;
  }

  return (
    <Screen scroll>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={{ flex: 1 }}>
        <Text style={styles.title}>Log this week</Text>
        <Text style={styles.subtitle}>
          Track your progress — your avatar evolves as you hit your targets.
        </Text>

        {result ? (
          <ResultCard result={result} />
        ) : (
          <>
            <NumericInput
              label="Current weight"
              placeholder="185"
              value={weightRaw}
              onChangeText={(v) => { setWeightRaw(v); setFieldErrors((f) => ({ ...f, weight: undefined })); }}
              unit="lb"
            />
            {fieldErrors.weight ? <Text style={styles.fieldErr}>{fieldErrors.weight}</Text> : null}

            <NumericInput
              label="Body fat % (optional)"
              placeholder="18"
              value={bfRaw}
              onChangeText={(v) => { setBfRaw(v); setFieldErrors((f) => ({ ...f, bf: undefined })); }}
              unit="%"
            />
            {fieldErrors.bf ? <Text style={styles.fieldErr}>{fieldErrors.bf}</Text> : null}

            <Stepper
              label="Workouts this week"
              value={workouts}
              onChange={setWorkouts}
              min={0}
              max={14}
            />

            <View style={styles.fieldWrap}>
              <Text style={styles.fieldLabel}>Note (optional)</Text>
              <TextInput
                style={[styles.input, styles.noteInput]}
                value={note}
                onChangeText={setNote}
                placeholder="How did you feel this week?"
                placeholderTextColor={colors.muted}
                multiline
                numberOfLines={3}
                returnKeyType="default"
              />
            </View>

            {noAvatarError && (
              <View style={styles.noAvatarCard}>
                <Text style={styles.noAvatarText}>
                  Generate your future-self avatar first before logging progress.
                </Text>
                <Button
                  title="Go to my avatar"
                  onPress={() => router.replace('/avatar')}
                />
                <Button
                  title="Back to results"
                  variant="ghost"
                  onPress={() => router.replace('/results')}
                />
              </View>
            )}

            {error && <Text style={styles.errorText}>{error}</Text>}

            <Button
              title="Log this week"
              onPress={handleSubmit}
              loading={loading}
              disabled={loading}
            />
          </>
        )}

        {result && (
          <>
            <Button
              title="Log another week"
              variant="ghost"
              onPress={() => {
                setResult(null);
                setWeightRaw('');
                setBfRaw('');
                setWorkouts(0);
                setNote('');
              }}
            />
            <Button
              title="View progress dashboard"
              variant="ghost"
              onPress={() => router.push('/progress')}
            />
          </>
        )}

        <View style={{ height: space.xl }} />
      </KeyboardAvoidingView>
    </Screen>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles = StyleSheet.create({
  title: {
    color: colors.foreground,
    fontSize: font['2xl'],
    fontWeight: '800',
    marginVertical: space.md,
  },
  subtitle: {
    color: colors.muted,
    fontSize: font.base,
    lineHeight: 22,
    marginBottom: space.md,
  },
  fieldWrap: { marginTop: space.md },
  fieldLabel: {
    color: colors.foreground,
    fontSize: font.sm,
    fontWeight: '600',
    marginBottom: space.xs,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.card,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: space.md,
  },
  input: {
    flex: 1,
    height: 48,
    color: colors.foreground,
    fontSize: font.base,
  },
  noteInput: {
    height: 90,
    textAlignVertical: 'top',
    paddingTop: space.sm,
    backgroundColor: colors.card,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: space.md,
  },
  unit: {
    color: colors.muted,
    fontSize: font.base,
    marginLeft: space.xs,
  },
  fieldErr: {
    color: colors.destructive,
    fontSize: font.xs,
    marginTop: space.xs,
  },
  errorText: {
    color: colors.destructive,
    fontSize: font.sm,
    marginTop: space.md,
    textAlign: 'center',
  },
  // Stepper
  stepperRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: space.md,
    backgroundColor: colors.card,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: space.md,
    paddingVertical: space.sm,
  },
  stepperLabel: { color: colors.foreground, fontSize: font.sm, fontWeight: '600' },
  stepperControls: { flexDirection: 'row', alignItems: 'center', gap: space.md },
  stepperBtn: {
    width: 36,
    height: 36,
    borderRadius: radius.md,
    backgroundColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stepperBtnText: { color: colors.foreground, fontSize: font.lg, fontWeight: '700' },
  stepperVal: { color: colors.foreground, fontSize: font.lg, fontWeight: '700', minWidth: 28, textAlign: 'center' },
  // No avatar error card
  noAvatarCard: {
    backgroundColor: colors.card,
    borderRadius: radius.lg,
    padding: space.md,
    marginTop: space.md,
    borderWidth: 1,
    borderColor: colors.accent,
  },
  noAvatarText: {
    color: colors.foreground,
    fontSize: font.base,
    marginBottom: space.sm,
    textAlign: 'center',
  },
  // Result card
  resultCard: {
    backgroundColor: colors.card,
    borderRadius: radius.lg,
    padding: space.md,
    marginTop: space.md,
  },
  streak: {
    color: colors.foreground,
    fontSize: font.xl,
    fontWeight: '800',
    marginBottom: space.sm,
  },
  stateBadge: {
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderRadius: radius.pill,
    paddingHorizontal: space.md,
    paddingVertical: space.xs,
    marginBottom: space.md,
  },
  stateText: { fontSize: font.sm, fontWeight: '700' },
  projRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    marginBottom: space.md,
  },
  projCol: { alignItems: 'center', flex: 1 },
  projHead: { color: colors.muted, fontSize: font.xs, fontWeight: '700', letterSpacing: 0.5, marginBottom: space.xs },
  projVal: { color: colors.foreground, fontSize: font.xl, fontWeight: '800' },
  projSub: { color: colors.muted, fontSize: font.sm, marginTop: 2 },
  projArrow: { color: colors.muted, fontSize: font.base, fontWeight: '700', marginHorizontal: space.sm },
  loggedNote: {
    color: colors.muted,
    fontSize: font.sm,
    textAlign: 'center',
    lineHeight: 20,
    marginTop: space.sm,
  },
});
