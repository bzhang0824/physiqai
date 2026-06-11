import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Button, Card, Label, Screen, Subtitle, TextField, Title } from '@/components/ui';
import { showAlert } from '@/lib/alert';
import { postProgress } from '@/lib/api';
import { colors, font, radius, space, weight } from '@/lib/theme';

function Stepper({ value, onChange }: { value: number; onChange: (n: number) => void }) {
  return (
    <View style={styles.stepper}>
      <Pressable
        style={[styles.stepBtn, value <= 0 && styles.stepBtnOff]}
        onPress={() => onChange(Math.max(0, value - 1))}>
        <Text style={styles.stepSign}>−</Text>
      </Pressable>
      <Text style={styles.stepVal}>{value}</Text>
      <Pressable style={styles.stepBtn} onPress={() => onChange(Math.min(21, value + 1))}>
        <Text style={styles.stepSign}>+</Text>
      </Pressable>
    </View>
  );
}

export default function CheckinScreen() {
  const [workouts, setWorkouts] = useState(1);
  const [weightLb, setWeightLb] = useState('');
  const [bfPct, setBfPct] = useState('');
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function submit() {
    setSubmitting(true);
    try {
      const res = await postProgress({
        workouts_done: workouts,
        weight_lb: weightLb ? Number(weightLb) : undefined,
        bf_pct: bfPct ? Number(bfPct) : undefined,
        note: note.trim() || undefined,
      });
      const msg = res.rebake_triggered
        ? `Logged! You're on a ${res.streak_weeks}-week streak — and your avatar is updating to match your progress.`
        : `Logged! You're on a ${res.streak_weeks}-week streak. Keep it going.`;
      showAlert('Nice work 💪', msg, [{ text: 'Done', onPress: () => router.replace('/home') }]);
    } catch (e: any) {
      const detail = e?.message ?? 'Could not save your check-in.';
      if (detail.toLowerCase().includes('avatar')) {
        showAlert('Create your avatar first', 'Generate your avatar, then you can track progress against it.');
      } else {
        showAlert('Something went wrong', detail);
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Screen scroll>
      <Title>Log your workout</Title>
      <Subtitle>How many sessions since your last check-in? Add today&apos;s numbers if you have them.</Subtitle>

      <Card style={styles.section}>
        <Label tight>Workouts completed</Label>
        <Stepper value={workouts} onChange={setWorkouts} />
      </Card>

      <Card style={styles.section}>
        <Label tight>Today&apos;s numbers (optional)</Label>
        <View style={styles.fieldRow}>
          <TextField
            label="Weight"
            value={weightLb}
            onChangeText={setWeightLb}
            keyboardType="decimal-pad"
            placeholder="lb"
            style={styles.half}
          />
          <View style={{ width: space.md }} />
          <TextField
            label="Body fat"
            value={bfPct}
            onChangeText={setBfPct}
            keyboardType="decimal-pad"
            placeholder="%"
            style={styles.half}
          />
        </View>
        <TextField
          label="Note"
          value={note}
          onChangeText={setNote}
          placeholder="How did it go?"
          multiline
        />
      </Card>

      <Button
        title={submitting ? 'Saving…' : 'Log it'}
        onPress={submit}
        loading={submitting}
        disabled={submitting}
      />
      <Button title="Cancel" variant="ghost" onPress={() => router.back()} />
      <View style={{ height: space.xl }} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  section: { marginTop: space.md },
  fieldRow: { flexDirection: 'row' },
  half: { flex: 1 },
  stepper: { flexDirection: 'row', alignItems: 'center', marginTop: space.sm },
  stepBtn: {
    width: 52, height: 52, borderRadius: radius.md, borderWidth: 1, borderColor: colors.border,
    backgroundColor: colors.surface, alignItems: 'center', justifyContent: 'center',
  },
  stepBtnOff: { opacity: 0.4 },
  stepSign: { color: colors.foreground, fontSize: font['2xl'], fontWeight: weight.bold, lineHeight: 30 },
  stepVal: { color: colors.foreground, fontSize: font['3xl'], fontWeight: weight.heavy, minWidth: 80, textAlign: 'center' },
});
