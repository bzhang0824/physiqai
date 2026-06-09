import { router } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { Button, Chip, Screen, Step, Subtitle, Title } from '@/components/ui';
import { useStore } from '@/lib/store';
import { space } from '@/lib/theme';

const HORIZONS = [
  { weeks: 4, label: '4 weeks' },
  { weeks: 12, label: '12 weeks' },
  { weeks: 26, label: '6 months' },
  { weeks: 52, label: '1 year' },
];

export default function HorizonScreen() {
  const stats = useStore((s) => s.stats);
  const setStats = useStore((s) => s.setStats);
  const [weeks, setWeeks] = useState(stats.weeks);

  return (
    <Screen>
      <View style={styles.container}>
        <View style={{ flex: 1, justifyContent: 'center' }}>
          <Step n={5} total={5} />
          <Title>When do you want to see yourself?</Title>
          <Subtitle>Pick a time horizon. We&apos;ll project a realistic result for that point.</Subtitle>
          <View style={styles.chips}>
            {HORIZONS.map((h) => (
              <Chip
                key={h.weeks}
                label={h.label}
                selected={weeks === h.weeks}
                onPress={() => setWeeks(h.weeks)}
                style={styles.chip}
              />
            ))}
          </View>
        </View>
        <Button
          title="Generate My Transformation"
          onPress={() => {
            setStats({ weeks });
            router.push('/loading');
          }}
        />
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'space-between', paddingVertical: space.xl },
  chips: { flexDirection: 'row', flexWrap: 'wrap', marginTop: space.md },
  chip: { minWidth: 120 },
});
