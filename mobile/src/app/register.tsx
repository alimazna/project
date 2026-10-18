import { Link, router } from 'expo-router';
import React, { useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Button, Field } from '../components/ui';
import { useAuth } from '../context/AuthContext';
import { colors } from '../lib/theme';

export default function RegisterScreen() {
  const { signUp } = useAuth();
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function onSubmit() {
    setBusy(true);
    setError('');
    try {
      await signUp(email.trim(), password, displayName.trim() || undefined);
      router.replace('/(tabs)');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setBusy(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>Create your account</Text>
        <Text style={styles.note}>
          The first registered user becomes the system administrator.
        </Text>

        {error !== '' && <Text style={styles.error}>{error}</Text>}

        <Field
          label="Display name (optional)"
          value={displayName}
          onChangeText={setDisplayName}
          autoCapitalize="words"
        />
        <Field
          label="Email"
          value={email}
          onChangeText={setEmail}
          placeholder="you@example.com"
          keyboardType="email-address"
        />
        <Field label="Password" value={password} onChangeText={setPassword} secure />

        <Button title="Create account" onPress={onSubmit} loading={busy} />
        <View style={styles.linkRow}>
          <Text style={styles.muted}>Already registered?</Text>
          <Link href="/login" style={styles.link}>
            Sign in
          </Link>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  container: { padding: 24, justifyContent: 'center', flexGrow: 1 },
  title: { color: colors.text, fontSize: 24, fontWeight: '700', marginBottom: 8 },
  note: { color: colors.muted, fontSize: 13, marginBottom: 24 },
  error: { color: colors.red, marginBottom: 12 },
  linkRow: { flexDirection: 'row', marginTop: 16, justifyContent: 'center', gap: 6 },
  link: { color: colors.accent },
  muted: { color: colors.muted },
});