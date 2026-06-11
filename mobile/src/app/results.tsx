import { router } from 'expo-router';
import { Image, StyleSheet, Text, View } from 'react-native';

import { Button, Card, Screen } from '@/components/ui';
import { showAlert } from '@/lib/alert';
import { Projection, useStore } from '@/lib/store';
import { colors, font, radius, space } from '@/lib/theme';

function confidenceLabel(score: number) {
  if (score >= 0.75) return { text: 'HIGH', color: colors.primary };
  if (score >= 0.5) return { text: 'MEDIUM', color: colors.accent };
  return { text: 'LOW', color: colors.destructive };
}

function StatRow({ label, before, after, delta }: {
  label: string; before: string; after: string; delta: string;
}) {
  return (
    <View style={styles.statRow}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={styles.statVals}>
        {before} <Text style={{ color: colors.muted }}>→</Text> {after}
      </Text>
      <Text style={styles.statDelta}>{delta}</Text>
    </View>
  );
}

export default function ResultsScreen() {
  const result = useStore((s) => s.result);
  const reset = useStore((s) => s.reset);

  if (!result) {
    return (
      <Screen>
        <View style={styles.empty}>
          <Text style={styles.emptyText}>No result yet.</Text>
          <Button title="Start Over" onPress={() => { reset(); router.replace('/'); }} />
        </View>
      </Screen>
    );
  }

  const p: Projection = result.projection;
  const conf = confidenceLabel(p.confidence_score);

  return (
    <Screen scroll>
      <Text style={styles.title}>Your {p.months}-month projection</Text>

      <View style={styles.compare}>
        <View style={styles.col}>
          <Text style={styles.colLabel}>NOW</Text>
          <Image source={{ uri: result.before_url }} style={styles.img} resizeMode="cover" />
        </View>
        <View style={styles.col}>
          <Text style={[styles.colLabel, { color: colors.primary }]}>
            {p.months} MONTH{p.months === 1 ? '' : 'S'}
          </Text>
          <Image source={{ uri: result.after_url }} style={styles.img} resizeMode="cover" />
        </View>
      </View>

      <View style={[styles.confBadge, { borderColor: conf.color }]}>
        <Text style={[styles.confText, { color: conf.color }]}>
          {conf.text} CONFIDENCE · {Math.round(p.confidence_score * 100)}%
        </Text>
      </View>

      <Card style={styles.cardGap}>
        <StatRow label="Weight"
          before={`${p.weight_before_lb} lb`} after={`${p.weight_after_lb} lb`}
          delta={`${p.weight_delta_lb > 0 ? '+' : ''}${p.weight_delta_lb} lb`} />
        <StatRow label="Body fat"
          before={`${p.bf_before}%`} after={`${p.bf_after}%`}
          delta={`${p.bf_delta > 0 ? '+' : ''}${p.bf_delta}%`} />
        <StatRow label="Lean mass"
          before="" after={`${p.lean_delta_lb > 0 ? '+' : ''}${p.lean_delta_lb} lb`}
          delta="" />
        <Text style={styles.range}>
          Likely weight change: {p.confidence_lo_lb} to {p.confidence_hi_lb} lb
        </Text>
      </Card>

      {(p.insights.length > 0 || p.warnings.length > 0) && (
        <Card style={styles.cardGap}>
          <Text style={styles.why}>Why this projection</Text>
          {p.insights.map((t, i) => (
            <Text key={`i${i}`} style={styles.insight}>✓ {t}</Text>
          ))}
          {p.warnings.map((t, i) => (
            <Text key={`w${i}`} style={styles.warning}>⚠ {t}</Text>
          ))}
        </Card>
      )}

      <Button title="Start tracking my progress" onPress={() => router.push('/home')} />
      {/* The /avatar route is built in the 3D-avatar branch. Until it merges, show a
          friendly notice so the button never dead-ends. Then switch to:
          onPress={() => router.push('/avatar')} */}
      <Button
        title="See your body in 3D"
        variant="ghost"
        onPress={() => showAlert('Coming soon', 'Your interactive 3D body view is on the way.')}
      />
      <Button title="Try a Different Plan" variant="ghost" onPress={() => router.replace('/horizon')} />
      <Button title="Start Over" variant="ghost" onPress={() => { reset(); router.replace('/'); }} />
      <View style={{ height: space.xl }} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { color: colors.foreground, fontSize: font['2xl'], fontWeight: '800', marginVertical: space.md },
  compare: { flexDirection: 'row', gap: space.sm },
  col: { flex: 1 },
  colLabel: { color: colors.muted, fontSize: font.xs, fontWeight: '700', letterSpacing: 1, marginBottom: space.xs },
  img: { width: '100%', aspectRatio: 0.62, borderRadius: radius.md, backgroundColor: colors.surface },
  confBadge: { alignSelf: 'flex-start', borderWidth: 1, borderRadius: radius.pill, paddingHorizontal: space.md, paddingVertical: space.xs, marginTop: space.md },
  confText: { fontSize: font.sm, fontWeight: '800', letterSpacing: 0.5 },
  cardGap: { marginTop: space.md },
  statRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: space.sm, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.border },
  statLabel: { color: colors.muted, fontSize: font.base, width: 90 },
  statVals: { color: colors.foreground, fontSize: font.base, fontWeight: '600', flex: 1 },
  statDelta: { color: colors.primary, fontSize: font.base, fontWeight: '700' },
  range: { color: colors.muted, fontSize: font.sm, marginTop: space.sm },
  why: { color: colors.foreground, fontSize: font.lg, fontWeight: '700', marginBottom: space.sm },
  insight: { color: colors.primary, fontSize: font.sm, lineHeight: 22, marginBottom: space.xs },
  warning: { color: colors.accent, fontSize: font.sm, lineHeight: 22, marginBottom: space.xs },
  empty: { flex: 1, justifyContent: 'center' },
  emptyText: { color: colors.muted, fontSize: font.lg, marginBottom: space.md, textAlign: 'center' },
});
