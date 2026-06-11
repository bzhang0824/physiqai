// Settings / Account — one place for account actions, legal links, and app info.
import Constants from 'expo-constants';
import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { Button, Card, Label, Screen, Subtitle, Title } from '@/components/ui';
import { showAlert } from '@/lib/alert';
import { deleteAccount } from '@/lib/api';
import { PRIVACY_PATH, TERMS_PATH } from '@/lib/legal';
import { useStore } from '@/lib/store';
import { supabase } from '@/lib/supabase';
import { colors, font, space, weight } from '@/lib/theme';

function LinkRow({ label, onPress, danger }: { label: string; onPress: () => void; danger?: boolean }) {
  return (
    <Pressable onPress={onPress} style={styles.row}>
      <Text style={[styles.rowLabel, danger && { color: colors.destructive }]}>{label}</Text>
      <Text style={[styles.chevron, danger && { color: colors.destructive }]}>›</Text>
    </Pressable>
  );
}

export default function SettingsScreen() {
  const session = useStore((s) => s.session);
  const email = useStore((s) => s.user?.email);
  const [busy, setBusy] = useState(false);

  async function handleSignOut() {
    await supabase.auth.signOut();
    router.replace('/');
  }

  function confirmDelete() {
    showAlert(
      'Delete account?',
      'This permanently deletes your account, avatar, and all check-ins. This cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Delete', style: 'destructive', onPress: runDelete },
      ],
    );
  }

  async function runDelete() {
    setBusy(true);
    try {
      await deleteAccount();
      await supabase.auth.signOut();
      showAlert('Account deleted', 'Your account and data have been removed.', [
        { text: 'OK', onPress: () => router.replace('/') },
      ]);
    } catch (e: any) {
      showAlert('Could not delete account', e?.message ?? 'Please try again in a moment.');
    } finally {
      setBusy(false);
    }
  }

  const version = Constants.expoConfig?.version ?? '1.0.0';

  return (
    <Screen scroll>
      <Title>Settings</Title>

      <Card style={styles.section}>
        <Label tight>Account</Label>
        {session ? (
          <>
            <Text style={styles.email}>{email || 'Signed in'}</Text>
            <Button title="Sign out" variant="ghost" onPress={handleSignOut} disabled={busy} />
            <LinkRow label={busy ? 'Deleting…' : 'Delete account'} onPress={confirmDelete} danger />
          </>
        ) : (
          <>
            <Subtitle>Sign in to save your avatar and progress across devices.</Subtitle>
            <Button title="Sign in" onPress={() => router.push('/signin')} />
          </>
        )}
      </Card>

      <Card style={styles.section}>
        <Label tight>Legal</Label>
        <LinkRow label="Privacy Policy" onPress={() => router.push(PRIVACY_PATH as any)} />
        <View style={styles.divider} />
        <LinkRow label="Terms of Service" onPress={() => router.push(TERMS_PATH as any)} />
      </Card>

      <Text style={styles.version}>PhysiqAI v{version}</Text>
      <Button title="Done" variant="ghost" onPress={() => router.back()} />
      <View style={{ height: space.xl }} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  section: { marginTop: space.md },
  email: { color: colors.foreground, fontSize: font.base, fontWeight: weight.semibold, marginTop: space.xs, marginBottom: space.md },
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingVertical: space.md },
  rowLabel: { color: colors.foreground, fontSize: font.base },
  chevron: { color: colors.faint, fontSize: font.xl, fontWeight: weight.regular },
  divider: { height: StyleSheet.hairlineWidth, backgroundColor: colors.border },
  version: { color: colors.faint, fontSize: font.sm, textAlign: 'center', marginTop: space.xl, marginBottom: space.sm },
});
