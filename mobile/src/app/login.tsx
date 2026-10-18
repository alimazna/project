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
import { API_BASE } from '../lib/api';
import { colors } from '../lib/theme';

export default function LoginScreen() {
  const { signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function onSubmit() {
    setBusy(true);
    setError('');
    try {
      await signIn(email.trim(), password);
      router.replace('/(tabs)');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
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
        <Text style={styles.logo}>TrendCipher</Text>
        <Text style={styles.tagline}>Explainable crypto market intelligence</Text>
        <Text style={styles.base}>API: {API_BASE}</Text>

        {error !== '' && <Text style={styles.error}>{error}</Text>}

        <Field
          label="Email"
          value={email}
          onChangeText={setEmail}
          placeholder="you@example.com"
          keyboardType="email-address"
        />
        <Field
          label="Password"
          value={password}
          onChangeText={setPassword}
          placeholder="••••••••"
          secure
        />

        <Button title="Sign in" onPress={onSubmit} loading={busy} />
        <View style={styles.linkRow}>
          <Text style={styles.muted}>No account?</Text>
          <Link href="/register" style={styles.link}>
            Create one
          </Link>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bg },
  container: { padding: 24, justifyContent: 'center', flexGrow: 1 },
  logo: { color: colors.text, fontSize: 32, fontWeight: '700' },
  tagline: { color: colors.muted, fontSize: 14, marginBottom: 32 },
  base: { color: colors.muted, fontSize: 11, marginBottom: 24 },
  error: { color: colors.red, marginBottom: 12 },
  linkRow: { flexDirection: 'row', marginTop: 16, justifyContent: 'center', gap: 6 },
  link: { color: colors.accent },
  muted: { color: colors.muted },
});