// Progress-state pill badge — shared by the weekly check-in result card and
// the home hub (extracted from checkin.tsx so both render identically).
import { StyleSheet, Text, View } from 'react-native';

import type { ProgressState } from '@/lib/api';
import { colors, font, radius, space } from '@/lib/theme';

const STATE_LABEL: Record<ProgressState, string> = {
  ahead: 'Ahead of schedule 💪',
  on_track: 'Right on track ✅',
  behind: 'A bit behind — keep going',
  evolving: 'Your future self is leveling up ✨',
};

const STATE_COLOR: Record<ProgressState, string> = {
  ahead: colors.primary,
  on_track: colors.secondary,
  behind: colors.accent,
  evolving: colors.primary,
};

export function StateBadge({ state }: { state: ProgressState }) {
  const color = STATE_COLOR[state];
  return (
    <View style={[styles.badge, { borderColor: color }]}>
      <Text style={[styles.text, { color }]}>{STATE_LABEL[state]}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: 'flex-start',
    borderWidth: 1,
    borderRadius: radius.pill,
    paddingHorizontal: space.md,
    paddingVertical: space.xs,
    marginBottom: space.md,
  },
  text: { fontSize: font.sm, fontWeight: '700' },
});
