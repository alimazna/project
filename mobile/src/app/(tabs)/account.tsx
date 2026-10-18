import React, { useCallback, useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Switch, Text } from 'react-native';
import { Button, Card, EmptyState, Row } from '../../components/ui';
import { useAuth } from '../../context/AuthContext';
import { api, type DeviceEntry, type NotifPref } from '../../lib/api';
import { registerForPush } from '../../lib/notifications';
import { colors } from '../../lib/theme';

export default function AccountScreen() {
  const { user, signOut, refreshUser } = useAuth();
  const [devices, setDevices] = useState<DeviceEntry[]>([]);
  const [prefs, setPrefs] = useState<NotifPref[]>([]);
  const [pushStatus, setPushStatus] = useState('');
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const [{ devices: d }, { preferences: p }] = await Promise.all([
        api.getDevices(),
        api.getNotificationPreferences(),
      ]);
      setDevices(d);
      setPrefs(p);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load account data');
    }
  }, []);

  useEffect(() => {
    (async () => {
      await load();
      await refreshUser();
    })().catch(() => undefined);
  }, [load, refreshUser]);

  async function onRegisterPush() {
    setPushStatus('requesting…');
    const result = await registerForPush();
    setPushStatus(
      result.status === 'registered'
        ? 'This device is registered for push notifications.'
        : `Push not registered (${result.status}${result.reason ? `: ${result.reason}` : ''}). Expo push needs a development build on a physical device.`,
    );
    await load();
  }

  async function onTogglePref(index: number, enabled: boolean) {
    const next = prefs.map((p, i) => (i === index ? { ...p, enabled } : p));
    setPrefs(next);
    try {
      const { preferences } = await api.setNotificationPreferences(next);
      setPrefs(preferences);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update preferences');
    }
  }

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <Card>
        <Text style={styles.title}>{user?.display_name || user?.email || 'Account'}</Text>
        <Text style={styles.muted}>{user?.email}</Text>
        {user?.roles?.length ? (
          <Row style={styles.roles}>
            {user.roles.map((r) => (
              <Text key={r} style={styles.role}>
                {r}
              </Text>
            ))}
          </Row>
        ) : null}
      </Card>

      <Card>
        <Text style={styles.sectionTitle}>Push notifications</Text>
        <Row style={styles.pushRow}>
          <Text style={styles.muted}>{pushStatus || 'Register this device to receive alert pushes.'}</Text>
          <Button title="Register device" onPress={onRegisterPush} />
        </Row>
        {devices.length === 0 ? (
          <EmptyState text="No devices registered yet" />
        ) : (
          devices.map((d) => (
            <Row key={d.id} style={styles.deviceRow}>
              <Text style={styles.device}>{d.platform} ({d.provider})</Text>
              <Text style={styles.mutedSmall}>{d.push_token.slice(0, 16)}…</Text>
            </Row>
          ))
        )}
      </Card>

      <Card>
        <Text style={styles.sectionTitle}>Notification preferences</Text>
        {prefs.length === 0 ? (
          <EmptyState text="No preferences configured" />
        ) : (
          prefs.map((p, i) => (
            <Row key={`${p.category}:${p.channel}`} style={styles.prefRow}>
              <Text style={styles.prefText}>
                {p.category} · {p.channel}
              </Text>
              <Switch
                value={p.enabled}
                onValueChange={(v) => onTogglePref(i, v)}
                trackColor={{ true: colors.accent, false: colors.border }}
              />
            </Row>
          ))
        )}
      </Card>

      {error !== '' && <Text style={styles.error}>{error}</Text>}

      <Button title="Sign out" variant="danger" onPress={() => signOut()} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 16 },
  title: { color: colors.text, fontSize: 20, fontWeight: '700' },
  muted: { color: colors.muted, fontSize: 13 },
  mutedSmall: { color: colors.muted, fontSize: 12 },
  roles: { marginTop: 8, gap: 6, flexWrap: 'wrap' },
  role: {
    color: colors.accent,
    borderColor: colors.accent,
    borderWidth: 1,
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    fontSize: 11,
  },
  sectionTitle: { color: colors.text, fontSize: 16, fontWeight: '600', marginBottom: 8 },
  pushRow: { justifyContent: 'space-between', alignItems: 'center' },
  deviceRow: { justifyContent: 'space-between', paddingVertical: 6 },
  device: { color: colors.text, fontSize: 14, fontWeight: '500' },
  prefRow: { justifyContent: 'space-between', alignItems: 'center', paddingVertical: 4 },
  prefText: { color: colors.text, fontSize: 14, textTransform: 'capitalize' },
  error: { color: colors.red, marginTop: 12 },
});