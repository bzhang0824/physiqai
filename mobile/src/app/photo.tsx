// Guided 3-shot capture: front + side + back. Photo quality is the #1 lever on
// avatar accuracy (spike finding: non-selfie, arms-at-sides, full-body, good
// light ≈ 30% better output), and the side/back shots feed the morph stage as
// proportion ground truth. Progressive disclosure keeps it from feeling like
// three chores at once.
import * as ImagePicker from 'expo-image-picker';
import { router } from 'expo-router';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';

import { Button, Card, Screen, Subtitle, Title } from '@/components/ui';
import { useStore, type PhotoAngle } from '@/lib/store';
import { colors, font, radius, space, weight } from '@/lib/theme';

const CHECKLIST = [
  'Whole body in frame, head to feet',
  'Arms relaxed at your sides',
  'Bright, even lighting',
  'Fitted clothing (shows your real shape)',
];

const SLOTS: Array<{
  angle: PhotoAngle;
  label: string;
  guidance: string;
  preferLibrary?: boolean;
}> = [
  {
    angle: 'front',
    label: 'Front',
    guidance:
      'Face the camera. Prop your phone up and use the self-timer if you can — it beats a mirror selfie.',
  },
  {
    angle: 'side',
    label: 'Side',
    guidance: 'Turn 90° so your profile faces the camera. Arms relaxed.',
  },
  {
    angle: 'back',
    label: 'Back',
    guidance:
      "Face away from the camera. Back shots can't be selfies — use your camera app's self-timer (or a friend), then pick it from your Library.",
    preferLibrary: true,
  },
];

export default function PhotoScreen() {
  const photos = useStore((s) => s.photos);
  const setPhoto = useStore((s) => s.setPhoto);

  const captured = SLOTS.filter((s) => photos[s.angle]).length;
  const allSet = captured === SLOTS.length;
  // First slot without a photo is the active one; earlier slots show thumbnails.
  const activeIdx = SLOTS.findIndex((s) => !photos[s.angle]);

  async function pick(angle: PhotoAngle, source: 'library' | 'camera') {
    const opts: ImagePicker.ImagePickerOptions = { quality: 0.9, allowsEditing: false };
    const res =
      source === 'camera'
        ? await ImagePicker.launchCameraAsync(opts)
        : await ImagePicker.launchImageLibraryAsync({ ...opts, mediaTypes: ['images'] });
    if (!res.canceled && res.assets?.[0]?.uri) setPhoto(angle, res.assets[0].uri);
  }

  return (
    <Screen scroll>
      <Title>Add your photos</Title>
      <Subtitle>
        Three angles — front, side and back — so your avatar matches your real
        proportions, not a guess.
      </Subtitle>

      <Card style={styles.checklistCard}>
        {CHECKLIST.map((item) => (
          <View key={item} style={styles.checkRow}>
            <Text style={styles.checkMark}>✓</Text>
            <Text style={styles.checkText}>{item}</Text>
          </View>
        ))}
      </Card>

      <Text style={styles.progress}>
        {allSet ? 'All 3 photos added' : `Photo ${captured + 1} of 3`}
      </Text>

      {SLOTS.map((slot, i) => {
        const uri = photos[slot.angle];
        const isActive = i === activeIdx;
        const isLocked = !uri && !isActive;

        return (
          <Card
            key={slot.angle}
            style={StyleSheet.flatten([styles.slot, isLocked && styles.slotLocked])}
          >
            <View style={styles.slotHeader}>
              <Text style={styles.slotLabel}>
                {i + 1} · {slot.label}
              </Text>
              {uri ? <Text style={styles.slotDone}>✓ added</Text> : null}
            </View>

            {uri ? (
              <>
                <Image source={{ uri }} style={styles.preview} resizeMode="cover" />
                <Pressable onPress={() => pick(slot.angle, slot.preferLibrary ? 'library' : 'camera')}>
                  <Text style={styles.retake}>Retake</Text>
                </Pressable>
              </>
            ) : isActive ? (
              <>
                <Text style={styles.guidance}>{slot.guidance}</Text>
                <View style={styles.row}>
                  <View style={{ flex: 1, marginRight: space.sm }}>
                    <Button
                      title="Library"
                      variant={slot.preferLibrary ? 'primary' : 'ghost'}
                      onPress={() => pick(slot.angle, 'library')}
                    />
                  </View>
                  <View style={{ flex: 1, marginLeft: space.sm }}>
                    <Button
                      title="Camera"
                      variant={slot.preferLibrary ? 'ghost' : 'primary'}
                      onPress={() => pick(slot.angle, 'camera')}
                    />
                  </View>
                </View>
              </>
            ) : (
              <Text style={styles.lockedText}>{slot.guidance}</Text>
            )}
          </Card>
        );
      })}

      <Button title="Continue" onPress={() => router.push('/stats')} disabled={!allSet} />
      <View style={{ height: space.xl }} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  checklistCard: { marginBottom: space.md },
  checkRow: { flexDirection: 'row', alignItems: 'center', paddingVertical: 3 },
  checkMark: {
    color: colors.primary,
    fontSize: font.sm,
    fontWeight: weight.bold,
    width: 22,
  },
  checkText: { color: colors.foreground, fontSize: font.sm, flex: 1 },
  progress: {
    color: colors.muted,
    fontSize: font.sm,
    fontWeight: weight.semibold,
    marginBottom: space.sm,
  },
  slot: { marginBottom: space.md },
  slotLocked: { opacity: 0.45 },
  slotHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: space.xs,
  },
  slotLabel: {
    color: colors.foreground,
    fontSize: font.base,
    fontWeight: weight.bold,
  },
  slotDone: { color: colors.primary, fontSize: font.sm, fontWeight: weight.semibold },
  guidance: { color: colors.muted, fontSize: font.sm, marginBottom: space.md },
  lockedText: { color: colors.muted, fontSize: font.sm },
  preview: {
    width: '100%',
    height: 280,
    borderRadius: radius.md,
    marginBottom: space.sm,
  },
  retake: {
    color: colors.primary,
    fontSize: font.sm,
    fontWeight: weight.semibold,
    alignSelf: 'flex-start',
    paddingVertical: space.xs,
  },
  row: { flexDirection: 'row' },
});
