// Magic-link sign-in screen.
// User enters email → supabase sends a sign-in link → tapping the link returns
// to the app with a session (supabase-js + detectSessionInUrl handles the rest).
import { router } from 'expo-router';
import { useState } from 'react';
import {
  ActivityIndicator,
  Keyboard,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { Button, Screen } from '@/components/ui';
import { supabase } from '@/lib/supabase';
import { colors, font, radius, space } from '@/lib/theme';

function getEmailRedirectTo(): string {
  if (typeof window !== 'undefined' && typeof window.location !== 'undefined') {
    // On web, send the user back to the app's current origin.
    return window.location.origin;
  }
  // On native, use the app's custom scheme so the OS routes the link back.
  return 'mobile://';
}

export default function SignInScreen() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSend() {
    const trimmed = email.trim().toLowerCase();
    if (!trimmed) {
      setError('Please enter your email address.');
      return;
    }
    Keyboard.dismiss();
    setLoading(true);
    setError(null);

    const { error: sbError } = await supabase.auth.signInWithOtp({
      email: trimmed,
      options: {
        emailRedirectTo: getEmailRedirectTo(),
      },
    });

    setLoading(false);
    if (sbError) {
      setError(sbError.message);
      return;
    }
    setSent(true);
  }

  if (sent) {
    return (
      <Screen>
        <View style={styles.center}>
          <Text style={styles.title}>Check your email</Text>
          <Text style={styles.body}>
            We sent a sign-in link to{'\n'}
            <Text style={styles.emailHighlight}>{email.trim().toLowerCase()}</Text>
          </Text>
          <Text style={styles.hint}>Tap the link in that email to sign in.</Text>
          <TouchableOpacity
            style={styles.resetBtn}
            onPress={() => {
              setSent(false);
              setEmail('');
            }}>
            <Text style={styles.resetBtnText}>Use a different email</Text>
          </TouchableOpacity>
          <Button
            title="Back"
            variant="ghost"
            onPress={() => router.back()}
          />
        </View>
      </Screen>
    );
  }

  return (
    <Screen>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.flex}>
        <View style={styles.center}>
          <Text style={styles.title}>Sign in</Text>
          <Text style={styles.body}>
            Enter your email and we'll send you a magic link — no password needed.
          </Text>

          <TextInput
            style={[styles.input, error ? styles.inputError : null]}
            placeholder="you@example.com"
            placeholderTextColor={colors.muted}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="email-address"
            textContentType="emailAddress"
            value={email}
            onChangeText={(t) => {
              setEmail(t);
              if (error) setError(null);
            }}
            onSubmitEditing={handleSend}
            returnKeyType="send"
            editable={!loading}
          />

          {error && <Text style={styles.errorText}>{error}</Text>}

          {loading ? (
            <ActivityIndicator
              style={styles.spinner}
              size="large"
              color={colors.primary}
            />
          ) : (
            <Button title="Send me a sign-in link" onPress={handleSend} />
          )}

          <Button
            title="Back"
            variant="ghost"
            onPress={() => router.back()}
          />
        </View>
      </KeyboardAvoidingView>
    </Screen>
  );
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
  },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: space.lg,
  },
  title: {
    color: colors.foreground,
    fontSize: font['2xl'],
    fontWeight: '800',
    marginBottom: space.sm,
  },
  body: {
    color: colors.muted,
    fontSize: font.base,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: space.lg,
  },
  emailHighlight: {
    color: colors.foreground,
    fontWeight: '700',
  },
  hint: {
    color: colors.muted,
    fontSize: font.sm,
    textAlign: 'center',
    marginTop: space.sm,
    marginBottom: space.lg,
  },
  input: {
    width: '100%',
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    paddingHorizontal: space.md,
    paddingVertical: space.sm + 4,
    color: colors.foreground,
    fontSize: font.base,
    marginBottom: space.md,
  },
  inputError: {
    borderColor: colors.destructive,
  },
  errorText: {
    color: colors.destructive,
    fontSize: font.sm,
    marginBottom: space.md,
    textAlign: 'center',
  },
  spinner: {
    marginVertical: space.md,
  },
  resetBtn: {
    marginTop: space.sm,
    marginBottom: space.lg,
  },
  resetBtnText: {
    color: colors.secondary,
    fontSize: font.base,
    fontWeight: '600',
  },
});
