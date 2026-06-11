import Slider from '@react-native-community/slider';
import { router } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, Text, TextInput, View } from 'react-native';

import { BF_RANGE, BodySilhouette, bodyDescriptor } from '@/components/BodySilhouette';
import { Button, Card, Checkbox, Chip, Label, Screen, Step, Subtitle, Title } from '@/components/ui';
import { Experience, Sex, useStore } from '@/lib/store';
import { colors, font, radius, space } from '@/lib/theme';

const EXPERIENCE: { key: Experience; label: string }[] = [
  { key: 'beginner', label: 'Beginner' },
  { key: 'intermediate', label: 'Intermediate' },
  { key: 'advanced', label: 'Advanced' },
];

// Keep a stored bf% inside the slider's sex-specific range (clamped on sex switch).
function clampBf(sex: Sex, bf: number): number {
  const { lean, high } = BF_RANGE[sex];
  return Math.min(high, Math.max(lean, Math.round(bf)));
}

function NumField({ label, value, onChange, suffix }: {
  label: string; value: string; onChange: (v: string) => void; suffix?: string;
}) {
  return (
    <View style={{ flex: 1 }}>
      {label ? <Label>{label}</Label> : null}
      <View style={styles.inputWrap}>
        <TextInput style={styles.input} value={value} onChangeText={onChange}
          keyboardType="number-pad" placeholderTextColor={colors.muted} />
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
  const [sex, setSexState] = useState<Sex>(stats.sex);
  const [bfPct, setBfPct] = useState<number>(() => clampBf(stats.sex, stats.bfPct));
  const [measured, setMeasured] = useState(stats.bfMeasured);
  const [experience, setExperience] = useState<Experience>(stats.experience);

  // Body-fat ranges differ by sex; re-clamp the slider value when sex changes.
  function setSex(next: Sex) {
    setSexState(next);
    setBfPct((bf) => clampBf(next, bf));
  }

  const { lean, high } = BF_RANGE[sex];
  const descriptor = bodyDescriptor(sex, bfPct);
  const valid = Number(age) > 0 && Number(weight) > 0 && Number(ft) > 0 && Number(inch) >= 0;

  function next() {
    setStats({
      age: Number(age), sex, heightIn: Number(ft) * 12 + Number(inch),
      weightLb: Number(weight), bfPct: Math.round(bfPct), bfMeasured: measured, experience,
    });
    router.push('/training');
  }

  return (
    <Screen scroll>
      <Step n={1} total={5} />
      <Title>About you</Title>
      <Subtitle>The more accurate these are, the more honest your projection.</Subtitle>

      <Card style={styles.section}>
        <Label tight>Sex</Label>
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
      </Card>

      <Card style={styles.section}>
        <Label tight>Body type</Label>
        <View style={styles.bodyWrap}>
          <BodySilhouette sex={sex} bfPct={bfPct} size={120} />
          <Text style={styles.bodyLabel}>{descriptor.label}</Text>
          <Text style={styles.bodyDesc}>{descriptor.desc}</Text>
          <Text style={styles.bodyBf}>{measured ? `${Math.round(bfPct)}% body fat` : `~${Math.round(bfPct)}% body fat`}</Text>
        </View>
        <Slider minimumValue={lean} maximumValue={high} step={1} value={bfPct}
          onValueChange={setBfPct} minimumTrackTintColor={colors.primary}
          maximumTrackTintColor={colors.border} thumbTintColor={colors.primary} />
        <View style={styles.sliderEnds}>
          <Text style={styles.endLabel}>Lean</Text>
          <Text style={styles.endLabel}>Higher</Text>
        </View>
        <View style={styles.measuredRow}>
          <Checkbox checked={measured} onToggle={() => setMeasured((m) => !m)}>
            <Text style={styles.measuredText}>I&apos;ve had this measured (DEXA / calipers)</Text>
          </Checkbox>
        </View>
      </Card>

      <Card style={styles.section}>
        <Label tight>Training experience</Label>
        <View style={styles.row}>
          {EXPERIENCE.map((e) => (
            <Chip key={e.key} label={e.label} selected={experience === e.key} onPress={() => setExperience(e.key)} />
          ))}
        </View>
      </Card>

      <Button title="Continue" onPress={next} disabled={!valid} />
      <View style={{ height: space.xl }} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', flexWrap: 'wrap', marginTop: space.xs },
  section: { marginTop: space.md },
  fieldRow: { flexDirection: 'row' },
  inputWrap: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.surface,
    borderRadius: radius.md, borderWidth: 1, borderColor: colors.border, paddingHorizontal: space.md },
  input: { flex: 1, color: colors.foreground, fontSize: font.lg, height: 52 },
  suffix: { color: colors.muted, fontSize: font.base, marginLeft: space.sm },
  bodyWrap: { alignItems: 'center', marginTop: space.sm },
  bodyLabel: { color: colors.primary, fontSize: font.xl, fontWeight: '700', marginTop: space.sm },
  bodyDesc: { color: colors.muted, fontSize: font.sm, marginTop: 2 },
  bodyBf: { color: colors.foreground, fontSize: font.sm, marginTop: space.xs, fontWeight: '600' },
  sliderEnds: { flexDirection: 'row', justifyContent: 'space-between', marginTop: -space.xs },
  endLabel: { color: colors.muted, fontSize: font.xs },
  measuredRow: { marginTop: space.md },
  measuredText: { color: colors.muted, fontSize: font.sm },
});
