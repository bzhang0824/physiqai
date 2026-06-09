// Small themed UI primitives shared across screens.
import { ReactNode } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  ViewStyle,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors, font, radius, space } from '@/lib/theme';

export function Screen({ children, scroll }: { children: ReactNode; scroll?: boolean }) {
  const inner = (
    <View style={styles.screenInner}>{children}</View>
  );
  return (
    <SafeAreaView style={styles.screen} edges={['top', 'bottom']}>
      {scroll ? (
        <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
          {inner}
        </ScrollView>
      ) : (
        inner
      )}
    </SafeAreaView>
  );
}

export function Step({ n, total }: { n: number; total: number }) {
  return (
    <View style={styles.stepRow}>
      {Array.from({ length: total }).map((_, i) => (
        <View key={i} style={[styles.stepDot, i < n ? styles.stepOn : styles.stepOff]} />
      ))}
      <Text style={styles.stepText}>
        Step {n} of {total}
      </Text>
    </View>
  );
}

export function Title({ children }: { children: ReactNode }) {
  return <Text style={styles.title}>{children}</Text>;
}

export function Subtitle({ children }: { children: ReactNode }) {
  return <Text style={styles.subtitle}>{children}</Text>;
}

export function Label({ children }: { children: ReactNode }) {
  return <Text style={styles.label}>{children}</Text>;
}

export function Button({
  title,
  onPress,
  variant = 'primary',
  disabled,
  loading,
}: {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'ghost';
  disabled?: boolean;
  loading?: boolean;
}) {
  const isPrimary = variant === 'primary';
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled || loading}
      style={({ pressed }) => [
        styles.btn,
        isPrimary ? styles.btnPrimary : styles.btnGhost,
        (disabled || loading) && styles.btnDisabled,
        pressed && { opacity: 0.85 },
      ]}>
      {loading ? (
        <ActivityIndicator color={isPrimary ? '#04210F' : colors.foreground} />
      ) : (
        <Text style={[styles.btnText, isPrimary ? styles.btnTextPrimary : styles.btnTextGhost]}>
          {title}
        </Text>
      )}
    </Pressable>
  );
}

export function Chip({
  label,
  selected,
  onPress,
  style,
}: {
  label: string;
  selected: boolean;
  onPress: () => void;
  style?: ViewStyle;
}) {
  return (
    <Pressable
      onPress={onPress}
      style={[styles.chip, selected ? styles.chipOn : styles.chipOff, style]}>
      <Text style={[styles.chipText, selected && styles.chipTextOn]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  screenInner: { flex: 1, paddingHorizontal: space.lg, width: '100%', maxWidth: 520, alignSelf: 'center' },
  scroll: { flexGrow: 1 },
  title: { color: colors.foreground, fontSize: font['3xl'], fontWeight: '800', marginBottom: space.sm },
  subtitle: { color: colors.muted, fontSize: font.base, lineHeight: 24, marginBottom: space.lg },
  label: { color: colors.foreground, fontSize: font.sm, fontWeight: '600', marginBottom: space.sm, marginTop: space.md },
  btn: { height: 54, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center', marginTop: space.md },
  btnPrimary: { backgroundColor: colors.primary },
  btnGhost: { backgroundColor: 'transparent', borderWidth: 1, borderColor: colors.border },
  btnDisabled: { opacity: 0.4 },
  btnText: { fontSize: font.lg, fontWeight: '700' },
  btnTextPrimary: { color: '#04210F' },
  btnTextGhost: { color: colors.foreground },
  chip: { paddingVertical: space.sm + 2, paddingHorizontal: space.md, borderRadius: radius.pill, borderWidth: 1, marginRight: space.sm, marginBottom: space.sm },
  chipOn: { backgroundColor: colors.primary, borderColor: colors.primary },
  chipOff: { backgroundColor: colors.card, borderColor: colors.border },
  chipText: { color: colors.foreground, fontSize: font.base, fontWeight: '600' },
  chipTextOn: { color: '#04210F' },
  stepRow: { flexDirection: 'row', alignItems: 'center', marginTop: space.md, marginBottom: space.sm },
  stepDot: { width: 22, height: 4, borderRadius: 2, marginRight: 4 },
  stepOn: { backgroundColor: colors.primary },
  stepOff: { backgroundColor: colors.border },
  stepText: { color: colors.muted, fontSize: font.xs, marginLeft: space.sm },
});
