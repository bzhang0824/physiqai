import * as ImagePicker from 'expo-image-picker';
import { router } from 'expo-router';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';

import { Button, Screen, Subtitle, Title } from '@/components/ui';
import { useStore } from '@/lib/store';
import { colors, font, radius, space } from '@/lib/theme';

export default function PhotoScreen() {
  const photoUri = useStore((s) => s.photoUri);
  const setPhoto = useStore((s) => s.setPhoto);

  async function pick(source: 'library' | 'camera') {
    const opts: ImagePicker.ImagePickerOptions = { quality: 0.9, allowsEditing: false };
    const res =
      source === 'camera'
        ? await ImagePicker.launchCameraAsync(opts)
        : await ImagePicker.launchImageLibraryAsync({ ...opts, mediaTypes: ['images'] });
    if (!res.canceled && res.assets?.[0]?.uri) setPhoto(res.assets[0].uri);
  }

  return (
    <Screen scroll>
      <Title>Add a photo</Title>
      <Subtitle>A clear, front-facing photo with your body visible. Good lighting helps.</Subtitle>

      <Pressable style={styles.dropzone} onPress={() => pick('library')}>
        {photoUri ? (
          <Image source={{ uri: photoUri }} style={styles.preview} resizeMode="cover" />
        ) : (
          <Text style={styles.placeholder}>Tap to choose a photo</Text>
        )}
      </Pressable>

      <View style={styles.row}>
        <View style={{ flex: 1, marginRight: space.sm }}>
          <Button title="Library" variant="ghost" onPress={() => pick('library')} />
        </View>
        <View style={{ flex: 1, marginLeft: space.sm }}>
          <Button title="Camera" variant="ghost" onPress={() => pick('camera')} />
        </View>
      </View>

      <Button title="Continue" onPress={() => router.push('/stats')} disabled={!photoUri} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  dropzone: {
    height: 360,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
    marginBottom: space.md,
  },
  preview: { width: '100%', height: '100%' },
  placeholder: { color: colors.muted, fontSize: font.base },
  row: { flexDirection: 'row', marginBottom: space.sm },
});
