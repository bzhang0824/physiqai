import Slider from '@react-native-community/slider';
import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { Button, Chip, Label, Screen, Step, Subtitle, Title } from '@/components/ui';
import { Experience, Sex, useStore } from '@/lib/store';
import { colors, font, radius, space } from '@/lib/theme';

const EXPERIENCE: { key: Experience; label: string }[] = [
  { key: 'beginner', label: 'Beginner' },
  { key: 'intermediate', label: 'Intermediate' },
  { key: 'advanced', label: 'Advanced' },
];

// Body-type picker -> estimated bf% midpoint, by sex.
const BODY_TYPES: Record<Sex, { label: string; desc: string; bf: number }[]> = {
  M: [
    { label: 'Lean', desc: 'Visible abs, vascular', bf: 10 },
    { label: 'Fit', desc: 'Some definition', bf: 15 },
    { label: 'Average', desc: 'Soft midsection', bf: 20 },
    { label: 'Higher', desc: 'Round midsection', bf: 27 },
  ],
  F: [
    { label: 'Lean', desc: 'Athletic, defined', bf: 18 },
    { label: 'Fit', desc: 'Toned', bf: 23 },
    { label: 'Average', desc: 'Soft', bf: 28 },
    { label: 'Higher', desc: 'Fuller', bf: 34 },
  ],
};

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
  const [sex, setSex] = useState<Sex>(stats.sex);
  const [bodyIdx, setBodyIdx] = useState<number>(() => {
    const arr = BODY_TYPES[stats.sex];
    const i = arr.findIndex((b) => b.bf === stats.bfPct);
    return i >= 0 ? i : 1;
  });
  const [measured, setMeasured] = useState(stats.bfMeasured);
  const [measuredBf, setMeasuredBf] = useState(stats.bfPct);
  const [experience, setExperience] = useState<Experience>(stats.experience);

  const valid = Number(age) > 0 && Number(weight) > 0 && Number(ft) > 0 && Number(inch) >= 0;
  const bfPct = measured ? Math.round(measuredBf) : BODY_TYPES[sex][bodyIdx].bf;

  function next() {
    setStats({
      age: Number(age), sex, heightIn: Number(ft) * 12 + Number(inch),
      weightLb: Number(weight), bfPct, bfMeasured: measured, experience,
    });
    router.push('/training');
  }

  return (
    <Screen scroll>
      <Step n={1} total={5} />
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

      <Label>Body type {measured ? '' : `(~${bfPct}% body fat)`}</Label>
      {!measured && (
        <View style={styles.bodyGrid}>
          {BODY_TYPES[sex].map((b, i) => (
            <Pressable key={b.label} onPress={() => setBodyIdx(i)}
              style={[styles.bodyCard, bodyIdx === i ? styles.bodyOn : styles.bodyOff]}>
              <Text style={[styles.bodyLabel, bodyIdx === i && { color: colors.primary }]}>{b.label}</Text>
              <Text style={styles.bodyDesc}>{b.desc}</Text>
              <Text style={styles.bodyBf}>~{b.bf}%</Text>
            </Pressable>
          ))}
        </View>
      )}
      {measured && (
        <View>
          <Label>Measured body fat — {Math.round(measuredBf)}%</Label>
          <Slider minimumValue={4} maximumValue={45} step={1} value={measuredBf}
            onValueChange={setMeasuredBf} minimumTrackTintColor={colors.primary}
            maximumTrackTintColor={colors.border} thumbTintColor={colors.primary} />
        </View>
      )}
      <Pressable onPress={() => setMeasured((m) => !m)}>
        <Text style={styles.toggle}>
          {measured ? '← Use the body-type picker instead' : 'I have a measured number (DEXA / calipers) →'}
        </Text>
      </Pressable>

      <Label>Training experience</Label>
      <View style={styles.row}>
        {EXPERIENCE.map((e) => (
          <Chip key={e.key} label={e.label} selected={experience === e.key} onPress={() => setExperience(e.key)} />
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
  inputWrap: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.card,
    borderRadius: radius.md, borderWidth: 1, borderColor: colors.border, paddingHorizontal: space.md },
  input: { flex: 1, color: colors.foreground, fontSize: font.lg, height: 52 },
  suffix: { color: colors.muted, fontSize: font.base, marginLeft: space.sm },
  bodyGrid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' },
  bodyCard: { width: '48%', borderRadius: radius.md, borderWidth: 1, padding: space.md, marginBottom: space.sm },
  bodyOn: { borderColor: colors.primary, backgroundColor: '#10231a' },
  bodyOff: { borderColor: colors.border, backgroundColor: colors.card },
  bodyLabel: { color: colors.foreground, fontSize: font.lg, fontWeight: '700' },
  bodyDesc: { color: colors.muted, fontSize: font.xs, marginTop: 2 },
  bodyBf: { color: colors.muted, fontSize: font.sm, marginTop: space.xs, fontWeight: '600' },
  toggle: { color: colors.secondary, fontSize: font.sm, marginTop: space.sm, marginBottom: space.sm },
});
