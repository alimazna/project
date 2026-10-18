import React, { useCallback, useEffect, useState } from 'react';
import {
  FlatList,
  RefreshControl,
  StyleSheet,
  Switch,
  Text,
  View,
} from 'react-native';
import { Button, Card, EmptyState, Field, Row } from '../../components/ui';
import { api, type UserAlert } from '../../lib/api';
import { formatPrice, timeAgo } from '../../lib/format';
import { colors } from '../../lib/theme';

const KINDS = ['price_above', 'price_below', 'volume_spike'] as const;

export default function AlertsScreen() {
  const [alerts, setAlerts] = useState<UserAlert[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const [kind, setKind] = useState<string>(KINDS[0]);
  const [symbol, setSymbol] = useState('');
  const [value, setValue] = useState('');
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const { alerts: a } = await api.getAlerts();
      setAlerts(a);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load alerts');
    }
  }, []);

  useEffect(() => {
    (async () => {
      await load();
    })().catch(() => undefined);
  }, [load]);

  async function onRefresh() {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }

  async function onCreate() {
    if (!symbol.trim()) return;
    setBusy(true);
    setError('');
    try {
      await api.createAlert(symbol.trim(), kind, value ? Number(value) : undefined);
      setSymbol('');
      setValue('');
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create alert');
    } finally {
      setBusy(false);
    }
  }

  async function onToggle(a: UserAlert) {
    try {
      await api.updateAlert(a.id, { is_active: !a.is_active });
      setAlerts((prev) =>
        prev.map((x) => (x.id === a.id ? { ...x, is_active: !a.is_active } : x)),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update alert');
    }
  }

  async function onDelete(a: UserAlert) {
    try {
      await api.deleteAlert(a.id);
      setAlerts((prev) => prev.filter((x) => x.id !== a.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete alert');
    }
  }

  return (
    <View style={styles.screen}>
      {error !== '' && <Text style={styles.error}>{error}</Text>}
      <FlatList
        data={alerts}
        keyExtractor={(a) => String(a.id)}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.muted} />}
        ListHeaderComponent={
          <View style={styles.header}>
            <Text style={styles.hint}>Alerts evaluate on every new candle and fire once per cooldown window.</Text>
            <Card>
              <Text style={styles.createTitle}>New alert</Text>
              <Field label="Symbol (e.g. BTC/USD)" value={symbol} onChangeText={setSymbol} autoCapitalize="characters" />
              <Field label="Condition" value={kind} onChangeText={setKind} autoCapitalize="sentences" />
              <Field label="Threshold price" value={value} onChangeText={setValue} keyboardType="numeric" />
              <Button title="Create alert" onPress={onCreate} loading={busy} />
            </Card>
          </View>
        }
        ListEmptyComponent={<EmptyState text="No alerts yet — create one above" />}
        renderItem={({ item }) => (
          <Card>
            <Row style={styles.topRow}>
              <Text style={styles.symbol}>{item.symbol}</Text>
              <Switch
                value={item.is_active}
                onValueChange={() => onToggle(item)}
                trackColor={{ true: colors.accent, false: colors.border }}
              />
            </Row>
            <Text style={styles.condition}>
              {item.kind} {item.value != null ? `@ ${formatPrice(item.value)}` : ''}
            </Text>
            <Row style={styles.meta}>
              <Text style={styles.muted}>
                {item.is_active ? 'Active' : 'Paused'}
                {item.last_fired_at ? ` · last fired ${timeAgo(item.last_fired_at)}` : ''}
              </Text>
              <Button title="Delete" variant="danger" onPress={() => onDelete(item)} style={{ flexShrink: 1 }} />
            </Row>
          </Card>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  header: { padding: 12, gap: 8 },
  hint: { color: colors.muted, fontSize: 13 },
  createTitle: { color: colors.text, fontSize: 16, fontWeight: '600', marginBottom: 8 },
  error: { color: colors.red, paddingHorizontal: 16, paddingTop: 8 },
  topRow: { justifyContent: 'space-between', marginBottom: 6 },
  symbol: { color: colors.text, fontSize: 16, fontWeight: '700' },
  condition: { color: colors.muted, fontSize: 14, marginBottom: 8 },
  meta: { justifyContent: 'space-between', alignItems: 'center' },
  muted: { color: colors.muted, fontSize: 13 },
});