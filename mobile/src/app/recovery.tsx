import Slider from '@react-native-community/slider';
import { router } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { Button, Card, Chip, Label, Screen, Step, Subtitle, Title } from '@/components/ui';
import { Genetic, useStore } from '@/lib/store';
import { colors, font, space } from '@/lib/theme';

const GENETIC: { key: Genetic; label: string }[] = [
  { key: 'low', label: 'Hard gainer' },
  { key: 'average', label: 'Average' },
  { key: 'high', label: 'Easy gainer' },
];

export default function RecoveryScreen() {
  const stats = useStore((s) => s.stats);
  const setStats = useStore((s) => s.setStats);

  const [sleep, setSleep] = useState(stats.sleepHrs);
  const [stress, setStress] = useState(stats.stress);
  const [genetic, setGenetic] = useState<Genetic>(stats.geneticPotential);

  function next() {
    setStats({ sleepHrs: sleep, stress, geneticPotential: genetic });
    router.push('/horizon');
  }

  return (
    <Screen scroll>
      <Step n={4} total={5} />
      <Title>Recovery</Title>
      <Subtitle>Sleep, stress, and genetics shape how much of your effort sticks.</Subtitle>

      <Card style={styles.section}>
        <Label tight>Sleep — {sleep.toFixed(1)} hrs / night</Label>
        <Slider minimumValue={4} maximumValue={10} step={0.5} value={sleep} onValueChange={setSleep}
          minimumTrackTintColor={colors.primary} maximumTrackTintColor={colors.border} thumbTintColor={colors.primary} />

        <Label>Daily stress — {stress}/10</Label>
        <Slider minimumValue={1} maximumValue={10} step={1} value={stress} onValueChange={setStress}
          minimumTrackTintColor={colors.primary} maximumTrackTintColor={colors.border} thumbTintColor={colors.primary} />
        <Text style={styles.hint}>1 = very relaxed · 10 = constantly stressed</Text>
      </Card>

      <Card style={styles.section}>
        <Label tight>How easily do you build muscle?</Label>
        <View style={styles.row}>
          {GENETIC.map((g) => (
            <Chip key={g.key} label={g.label} selected={genetic === g.key} onPress={() => setGenetic(g.key)} />
          ))}
        </View>
        <Text style={styles.hint}>Best guess is fine — this only nudges the estimate.</Text>
      </Card>

      <Button title="Continue" onPress={next} />
      <View style={{ height: space.xl }} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', flexWrap: 'wrap', marginTop: space.xs },
  section: { marginTop: space.md },
  hint: { color: colors.muted, fontSize: font.xs, marginTop: space.xs },
});
