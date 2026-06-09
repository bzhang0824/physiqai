import { router } from 'expo-router';
import { StyleSheet, Text, View } from 'react-native';

import { Button, Screen } from '@/components/ui';
import { useStore } from '@/lib/store';
import { colors, font, space } from '@/lib/theme';

export default function Welcome() {
  const reset = useStore((s) => s.reset);

  return (
    <Screen>
      <View style={styles.container}>
        <View style={styles.hero}>
          <Text style={styles.kicker}>PHYSIQ<Text style={{ color: colors.primary }}>AI</Text></Text>
          <Text style={styles.title}>See your{'\n'}future physique.</Text>
          <Text style={styles.sub}>
            A realistic, science-backed look at where your body is actually heading —
            with your real face. Not fantasy.
          </Text>
        </View>
        <View>
          <Button
            title="Get Started"
            onPress={() => {
              reset();
              router.push('/photo');
            }}
          />
          <Text style={styles.fine}>Science-based · Personalized · Your photo stays private</Text>
        </View>
      </View>
    </Screen>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'space-between', paddingVertical: space.xl },
  hero: { flex: 1, justifyContent: 'center' },
  kicker: { color: colors.foreground, fontSize: font.lg, fontWeight: '800', letterSpacing: 2, marginBottom: space.lg },
  title: { color: colors.foreground, fontSize: font['4xl'], fontWeight: '900', lineHeight: 44, marginBottom: space.md },
  sub: { color: colors.muted, fontSize: font.lg, lineHeight: 26 },
  fine: { color: colors.muted, fontSize: font.xs, textAlign: 'center', marginTop: space.md },
});
