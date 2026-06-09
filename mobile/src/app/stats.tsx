import Slider from '@react-native-community/slider';
import { router } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, Text, TextInput, View } from 'react-native';

import { Button, Chip, Label, Screen, Subtitle, Title } from '@/components/ui';
import { Experience, Goal, Sex, useStore } from '@/lib/store';
import { colors, font, radius, space } from '@/lib/theme';

const GOALS: { key: Goal; label: string }[] = [
  { key: 'fat_loss', label: 'Cut' },
  { key: 'recomp', label: 'Recomp' },
  { key: 'muscle_gain', label: 'Build' },
];
const EXPERIENCE: { key: Experience; label: string }[] = [
  { key: 'beginner', label: 'Beginner' },
  { key: 'intermediate', label: 'Intermediate' },
  { key: 'advanced', label: 'Advanced' },
];

function NumField({ label, value, onChange, suffix }: {
  label: string; value: string; onChange: (v: string) => void; suffix?: string;
}) {
  return (
    <View style={{ flex: 1 }}>
      <Label>{label}</Label>
      <View style={styles.inputWrap}>
        <TextInput
          style={styles.input}
          value={value}
          onChangeText={onChange}
          keyboardType="number-pad"
          placeholderTextColor={colors.muted}
        />
        {suffix ? <Text style={styles.suffix}>{suffix}</Text> : null}
      </View>
    </View>
  );
}

export default function StatsScreen() {
  const stats = useStore((s) => s.stats);
  const setStats = useStore((s) => s.setStats);

  const [age, setAge] = useState(String(stats.age));
  const [ft, setFt] = useState(String(Math.floor(stats.heightIn / 12)));
  const [inch, setInch] = useState(String(stats.heightIn % 12));
  const [weight, setWeight] = useState(String(stats.weightLb));
  const [sex, setSex] = useState<Sex>(stats.sex);
  const [bf, setBf] = useState(stats.bfPct);
  const [experience, setExperience] = useState<Experience>(stats.experience);
  const [goal, setGoal] = useState<Goal>(stats.goal);

  const valid =
    Number(age) > 0 && Number(weight) > 0 && Number(ft) > 0 && Number(inch) >= 0;

  function next() {
    setStats({
      age: Number(age),
      sex,
      heightIn: Number(ft) * 12 + Number(inch),
      weightLb: Number(weight),
      bfPct: Math.round(bf),
      experience,
      goal,
    });
    router.push('/horizon');
  }

  return (
    <Screen scroll>
      <Title>About you</Title>
      <Subtitle>The more accurate these are, the more honest your projection.</Subtitle>

      <Label>Sex</Label>
      <View style={styles.row}>
        <Chip label="Male" selected={sex === 'M'} onPress={() => setSex('M')} />
        <Chip label="Female" selected={sex === 'F'} onPress={() => setSex('F')} />
      </View>

      <View style={styles.fieldRow}>
        <NumField label="Age" value={age} onChange={setAge} />
        <View style={{ width: space.md }} />
        <NumField label="Weight" value={weight} onChange={setWeight} suffix="lb" />
      </View>

      <Label>Height</Label>
      <View style={styles.fieldRow}>
        <NumField label="" value={ft} onChange={setFt} suffix="ft" />
        <View style={{ width: space.md }} />
        <NumField label="" value={inch} onChange={setInch} suffix="in" />
      </View>

      <Label>Body fat — {Math.round(bf)}%</Label>
      <Slider
        minimumValue={5}
        maximumValue={40}
        step={1}
        value={bf}
        onValueChange={setBf}
        minimumTrackTintColor={colors.primary}
        maximumTrackTintColor={colors.border}
        thumbTintColor={colors.primary}
      />
      <Text style={styles.hint}>Estimate is fine — lowers confidence slightly vs. a DEXA/caliper number.</Text>

      <Label>Training experience</Label>
      <View style={styles.row}>
        {EXPERIENCE.map((e) => (
          <Chip key={e.key} label={e.label} selected={experience === e.key} onPress={() => setExperience(e.key)} />
        ))}
      </View>

      <Label>Goal</Label>
      <View style={styles.row}>
        {GOALS.map((g) => (
          <Chip key={g.key} label={g.label} selected={goal === g.key} onPress={() => setGoal(g.key)} />
        ))}
      </View>

      <Button title="Continue" onPress={next} disabled={!valid} />
      <View style={{ height: space.xl }} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: space.sm },
  fieldRow: { flexDirection: 'row' },
  inputWrap: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: colors.card,
    borderRadius: radius.md, borderWidth: 1, borderColor: colors.border, paddingHorizontal: space.md,
  },
  input: { flex: 1, color: colors.foreground, fontSize: font.lg, height: 52 },
  suffix: { color: colors.muted, fontSize: font.base, marginLeft: space.sm },
  hint: { color: colors.muted, fontSize: font.xs, marginTop: space.xs },
});
