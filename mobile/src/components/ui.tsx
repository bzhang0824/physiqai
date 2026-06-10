// Small themed UI primitives shared across screens.
import { ReactNode } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TextInputProps,
  View,
  ViewStyle,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { colors, font, leading, radius, shadow, space, weight } from '@/lib/theme';

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

// `tight` removes the top margin — use for the first Label inside a Card.
export function Label({ children, tight }: { children: ReactNode; tight?: boolean }) {
  return <Text style={[styles.label, tight && styles.labelTight]}>{children}</Text>;
}

// Standard content container: white surface, hairline border, one soft shadow.
export function Card({ children, style }: { children: ReactNode; style?: ViewStyle }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

// Labeled text input. Light well, hairline border, accent focus ring.
export function TextField({
  label,
  style,
  ...props
}: TextInputProps & { label?: string; style?: ViewStyle }) {
  return (
    <View style={style}>
      {label ? <Label>{label}</Label> : null}
      <TextInput
        placeholderTextColor={colors.faint}
        style={styles.input}
        {...props}
      />
    </View>
  );
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
        pressed && { opacity: 0.9 },
      ]}>
      {loading ? (
        <ActivityIndicator color={isPrimary ? colors.onInk : colors.foreground} />
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

// Checkbox with an inline label. Tapping anywhere on the row toggles it.
export function Checkbox({
  checked,
  onToggle,
  children,
}: {
  checked: boolean;
  onToggle: () => void;
  children: ReactNode;
}) {
  return (
    <Pressable onPress={onToggle} style={styles.checkRow}>
      <View style={[styles.checkBox, checked && styles.checkBoxOn]}>
        {checked ? <Text style={styles.checkMark}>✓</Text> : null}
      </View>
      <View style={styles.checkLabel}>{children}</View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.background },
  screenInner: { flex: 1, paddingHorizontal: space.lg, width: '100%', maxWidth: 520, alignSelf: 'center' },
  scroll: { flexGrow: 1 },
  title: {
    color: colors.foreground,
    fontSize: font['3xl'],
    fontWeight: weight.heavy,
    letterSpacing: -0.5,
    marginBottom: space.sm,
  },
  subtitle: { color: colors.muted, fontSize: font.base, lineHeight: font.base * leading.normal, marginBottom: space.lg },
  label: { color: colors.foreground, fontSize: font.sm, fontWeight: weight.semibold, marginBottom: space.sm, marginTop: space.md },
  labelTight: { marginTop: 0 },
  card: {
    backgroundColor: colors.card,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: space.md,
    ...shadow.card,
  },
  input: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    paddingHorizontal: space.md,
    height: 52,
    fontSize: font.lg,
    color: colors.foreground,
  },
  btn: { height: 54, borderRadius: radius.md, alignItems: 'center', justifyContent: 'center', marginTop: space.md },
  btnPrimary: { backgroundColor: colors.ink },
  btnGhost: { backgroundColor: 'transparent', borderWidth: 1, borderColor: colors.border },
  btnDisabled: { opacity: 0.4 },
  btnText: { fontSize: font.lg, fontWeight: weight.bold },
  btnTextPrimary: { color: colors.onInk },
  btnTextGhost: { color: colors.foreground },
  chip: { paddingVertical: space.sm + 2, paddingHorizontal: space.md, borderRadius: radius.pill, borderWidth: 1, marginRight: space.sm, marginBottom: space.sm },
  chipOn: { backgroundColor: colors.primary, borderColor: colors.primary },
  chipOff: { backgroundColor: colors.surface, borderColor: colors.border },
  chipText: { color: colors.foreground, fontSize: font.base, fontWeight: weight.semibold },
  chipTextOn: { color: colors.onPrimary },
  checkRow: { flexDirection: 'row', alignItems: 'flex-start' },
  checkBox: {
    width: 24, height: 24, borderRadius: radius.sm, borderWidth: 1.5,
    borderColor: colors.border, alignItems: 'center', justifyContent: 'center',
    marginTop: 2,
  },
  checkBoxOn: { backgroundColor: colors.primary, borderColor: colors.primary },
  checkMark: { color: colors.onPrimary, fontSize: font.sm, fontWeight: weight.heavy, lineHeight: 18 },
  checkLabel: { flex: 1, marginLeft: space.md },
  stepRow: { flexDirection: 'row', alignItems: 'center', marginTop: space.md, marginBottom: space.sm },
  stepDot: { width: 22, height: 4, borderRadius: 2, marginRight: 4 },
  stepOn: { backgroundColor: colors.primary },
  stepOff: { backgroundColor: colors.border },
  stepText: { color: colors.muted, fontSize: font.xs, marginLeft: space.sm },
});
