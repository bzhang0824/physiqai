// Terms of Service — in-app scrollable route.
// Exports to static terms.html on the web build.
import { StyleSheet, Text, View } from 'react-native';

import { Card, Screen, Title } from '@/components/ui';
import { TERMS_SECTIONS } from '@/lib/legalContent';
import { colors, font, leading, space, weight } from '@/lib/theme';

export default function TermsScreen() {
  return (
    <Screen scroll>
      {/* DRAFT banner */}
      <Card style={styles.draftBanner}>
        <Text style={styles.draftText}>
          DRAFT — beta policy, not yet reviewed by counsel.
        </Text>
      </Card>

      <Title>Terms of Service</Title>
      <Text style={styles.updated}>Last updated: June 2026 (beta)</Text>

      {TERMS_SECTIONS.map((section) => (
        <View key={section.heading} style={styles.section}>
          <Text style={styles.sectionHeading}>{section.heading}</Text>
          <Text style={styles.body}>{section.body}</Text>
        </View>
      ))}

      <View style={{ height: space.xl }} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  draftBanner: {
    backgroundColor: '#FEF3C7',
    borderColor: '#F59E0B',
    marginBottom: space.md,
  },
  draftText: {
    color: '#92400E',
    fontSize: font.sm,
    fontWeight: weight.semibold,
    textAlign: 'center',
  },
  updated: {
    color: colors.muted,
    fontSize: font.sm,
    marginBottom: space.lg,
  },
  section: {
    marginBottom: space.lg,
  },
  sectionHeading: {
    color: colors.foreground,
    fontSize: font.lg,
    fontWeight: weight.semibold,
    marginBottom: space.xs,
  },
  body: {
    color: colors.foreground,
    fontSize: font.base,
    lineHeight: font.base * leading.normal,
  },
});
