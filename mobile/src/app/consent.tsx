import { router } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { Button, Card, Checkbox, Screen, Subtitle, Title } from '@/components/ui';
import { PRIVACY_PATH, TERMS_PATH } from '@/lib/legal';
import { useStore } from '@/lib/store';
import { colors, font, leading, space } from '@/lib/theme';

const POINTS = [
  'We use your photo to generate a personalized image of your potential future physique.',
  'It is processed by an AI image model, with a face-lock step that keeps your real face.',
  'We do not sell your photo or share it for advertising.',
  'You can start over and discard your data at any time.',
];

export default function ConsentScreen() {
  const accepted = useStore((s) => s.consentAccepted);
  const acceptConsent = useStore((s) => s.acceptConsent);
  const [checked, setChecked] = useState(accepted);

  function next() {
    acceptConsent();
    router.push('/photo');
  }

  return (
    <Screen scroll>
      <Title>Your photo & privacy</Title>
      <Subtitle>Before we continue, here is exactly what happens with your photo.</Subtitle>

      <Card>
        {POINTS.map((p, i) => (
          <View key={i} style={[styles.point, i === POINTS.length - 1 && styles.pointLast]}>
            <Text style={styles.dot}>•</Text>
            <Text style={styles.pointText}>{p}</Text>
          </View>
        ))}
      </Card>

      <View style={styles.consentBox}>
        <Checkbox checked={checked} onToggle={() => setChecked((c) => !c)}>
          <Text style={styles.consentText}>
            I am 18 or older and I agree to the{' '}
            <Text style={styles.link} onPress={() => router.push(PRIVACY_PATH as any)}>
              Privacy Policy
            </Text>{' '}
            and{' '}
            <Text style={styles.link} onPress={() => router.push(TERMS_PATH as any)}>
              Terms of Service
            </Text>
            , and I consent to PhysiqAI processing my photo to create my projection.
          </Text>
        </Checkbox>
      </View>

      <Button title="Agree & Continue" onPress={next} disabled={!checked} />
      <View style={{ height: space.xl }} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  point: { flexDirection: 'row', marginBottom: space.sm },
  pointLast: { marginBottom: 0 },
  dot: { color: colors.primary, fontSize: font.base, marginRight: space.sm, lineHeight: font.base * leading.normal },
  pointText: { flex: 1, color: colors.foreground, fontSize: font.base, lineHeight: font.base * leading.normal },
  consentBox: { marginTop: space.lg },
  consentText: { color: colors.foreground, fontSize: font.sm, lineHeight: font.sm * leading.normal },
  link: { color: colors.primary, fontWeight: '700' },
});
