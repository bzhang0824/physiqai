import { router } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { Button, Card, Chip, Label, Screen, Step, Subtitle, Title } from '@/components/ui';
import { Goal, LeanPref, Level, Tracking, useStore } from '@/lib/store';
import { space } from '@/lib/theme';

const GOALS: { key: Goal; label: string }[] = [
  { key: 'fat_loss', label: 'Cut' },
  { key: 'recomp', label: 'Recomp' },
  { key: 'muscle_gain', label: 'Build' },
];
const LEAN: { key: LeanPref; label: string }[] = [
  { key: 'lean_bulk', label: 'Lean' },
  { key: 'standard', label: 'Standard' },
  { key: 'aggressive_bulk', label: 'Aggressive' },
];
const PROTEIN: { key: Level; label: string }[] = [
  { key: 'low', label: 'Low' },
  { key: 'moderate', label: 'Moderate' },
  { key: 'high', label: 'High' },
];
const TRACKING: { key: Tracking; label: string }[] = [
  { key: 'weighing', label: 'Weigh food' },
  { key: 'app', label: 'Track in app' },
  { key: 'eyeballing', label: 'Eyeball it' },
  { key: 'none', label: "Don't track" },
];

export default function NutritionScreen() {
  const stats = useStore((s) => s.stats);
  const setStats = useStore((s) => s.setStats);

  const [goal, setGoal] = useState<Goal>(stats.goal);
  const [lean, setLean] = useState<LeanPref>(stats.leanPreference);
  const [protein, setProtein] = useState<Level>(stats.proteinLevel);
  const [tracking, setTracking] = useState<Tracking>(stats.trackingMethod);

  function next() {
    setStats({ goal, leanPreference: lean, proteinLevel: protein, trackingMethod: tracking });
    router.push('/recovery');
  }

  return (
    <Screen scroll>
      <Step n={3} total={5} />
      <Title>Nutrition</Title>
      <Subtitle>Your goal and how you eat set the direction and the ceiling.</Subtitle>

      <Card style={styles.section}>
        <Label tight>Primary goal</Label>
        <View style={styles.row}>
          {GOALS.map((g) => (
            <Chip key={g.key} label={g.label} selected={goal === g.key} onPress={() => setGoal(g.key)} />
          ))}
        </View>

        {goal === 'muscle_gain' && (
          <>
            <Label>Bulk style</Label>
            <View style={styles.row}>
              {LEAN.map((l) => (
                <Chip key={l.key} label={l.label} selected={lean === l.key} onPress={() => setLean(l.key)} />
              ))}
            </View>
          </>
        )}
      </Card>

      <Card style={styles.section}>
        <Label tight>Protein intake</Label>
        <View style={styles.row}>
          {PROTEIN.map((p) => (
            <Chip key={p.key} label={p.label} selected={protein === p.key} onPress={() => setProtein(p.key)} />
          ))}
        </View>
      </Card>

      <Card style={styles.section}>
        <Label tight>How do you track food?</Label>
        <View style={styles.row}>
          {TRACKING.map((t) => (
            <Chip key={t.key} label={t.label} selected={tracking === t.key} onPress={() => setTracking(t.key)} />
          ))}
        </View>
      </Card>

      <Button title="Continue" onPress={next} />
      <View style={{ height: space.xl }} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', flexWrap: 'wrap', marginTop: space.xs },
  section: { marginTop: space.md },
});
