import Slider from '@react-native-community/slider';
import { router } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { Button, Card, Chip, Label, Screen, Step, Subtitle, Title } from '@/components/ui';
import { Intensity, Level, useStore } from '@/lib/store';
import { colors, space } from '@/lib/theme';

const VOLUME: { key: Level; label: string }[] = [
  { key: 'low', label: 'Low (~6 sets)' },
  { key: 'moderate', label: 'Moderate (~12)' },
  { key: 'high', label: 'High (~20)' },
];
const INTENSITY: { key: Intensity; label: string }[] = [
  { key: 'light', label: 'Easy' },
  { key: 'moderate', label: 'Solid' },
  { key: 'intense', label: 'Near failure' },
];
const MUSCLES = ['Chest', 'Back', 'Shoulders', 'Arms', 'Legs', 'Core', 'Glutes'];

export default function TrainingScreen() {
  const stats = useStore((s) => s.stats);
  const setStats = useStore((s) => s.setStats);

  const [volume, setVolume] = useState<Level>(stats.volume);
  const [intensity, setIntensity] = useState<Intensity>(stats.intensity);
  const [days, setDays] = useState(stats.daysPerWeek);
  const [cardio, setCardio] = useState(stats.cardioDays);
  const [focus, setFocus] = useState<string[]>(stats.focusGroups);

  const toggle = (m: string) =>
    setFocus((f) => (f.includes(m) ? f.filter((x) => x !== m) : [...f, m]));

  function next() {
    setStats({
      volume, intensity, daysPerWeek: days, cardioDays: cardio,
      focusGroups: focus.map((m) => m.toLowerCase()),
    });
    router.push('/nutrition');
  }

  return (
    <Screen scroll>
      <Step n={2} total={5} />
      <Title>Your training</Title>
      <Subtitle>How you actually train drives how much your body can change.</Subtitle>

      <Card style={styles.section}>
        <Label tight>Weekly volume per muscle</Label>
        <View style={styles.row}>
          {VOLUME.map((v) => (
            <Chip key={v.key} label={v.label} selected={volume === v.key} onPress={() => setVolume(v.key)} />
          ))}
        </View>

        <Label>Effort / intensity</Label>
        <View style={styles.row}>
          {INTENSITY.map((v) => (
            <Chip key={v.key} label={v.label} selected={intensity === v.key} onPress={() => setIntensity(v.key)} />
          ))}
        </View>
      </Card>

      <Card style={styles.section}>
        <Label tight>Lifting days / week — {days}</Label>
        <Slider minimumValue={1} maximumValue={7} step={1} value={days} onValueChange={setDays}
          minimumTrackTintColor={colors.primary} maximumTrackTintColor={colors.border} thumbTintColor={colors.primary} />

        <Label>Cardio days / week — {cardio}</Label>
        <Slider minimumValue={0} maximumValue={7} step={1} value={cardio} onValueChange={setCardio}
          minimumTrackTintColor={colors.primary} maximumTrackTintColor={colors.border} thumbTintColor={colors.primary} />
      </Card>

      <Card style={styles.section}>
        <Label tight>Focus areas (optional)</Label>
        <View style={styles.row}>
          {MUSCLES.map((m) => (
            <Chip key={m} label={m} selected={focus.includes(m)} onPress={() => toggle(m)} />
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
