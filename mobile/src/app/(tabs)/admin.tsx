import { Redirect } from 'expo-router';
import React, { useCallback, useEffect, useState } from 'react';
import { FlatList, RefreshControl, StyleSheet, Text, View } from 'react-native';
import { Badge, Button, Card, EmptyState, Row } from '../../components/ui';
import { useAuth } from '../../context/AuthContext';
import { api, type AdminSymbol } from '../../lib/api';
import { colors } from '../../lib/theme';

export default function AdminSymbolsScreen() {
  const { accessToken, user, loading } = useAuth();
  const [symbols, setSymbols] = useState<AdminSymbol[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');

  const isAdmin = user?.roles?.some((r) => r === 'admin' || r === 'super_admin') ?? false;
  const isSuper = user?.roles?.includes('super_admin') ?? false;

  const load = useCallback(async () => {
    try {
      const { symbols: s } = await api.listAdminSymbols();
      setSymbols(s);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load symbols');
    }
  }, []);

  useEffect(() => {
    if (!isAdmin) return;
    (async () => {
      await load();
    })().catch(() => undefined);
  }, [isAdmin, load]);

  async function onRefresh() {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }

  async function toggle(s: AdminSymbol) {
    setBusy(s.symbol);
    setError('');
    try {
      await api.toggleAdminSymbol(s.symbol, !s.is_active);
      setSymbols((prev) =>
        prev.map((x) => (x.symbol === s.symbol ? { ...x, is_active: !x.is_active } : x)),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to toggle symbol');
    } finally {
      setBusy('');
    }
  }

  if (loading) return null;
  if (!accessToken) return <Redirect href="/login" />;
  if (!isAdmin) {
    return (
      <View style={styles.screen}>
        <Card>
          <EmptyState text="This screen is available to admins only." />
        </Card>
      </View>
    );
  }

  return (
    <View style={styles.screen}>
      {error !== '' && <Text style={styles.error}>{error}</Text>}
      <FlatList
        data={symbols}
        keyExtractor={(s) => s.symbol}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.muted} />}
        ListHeaderComponent={
          <Text style={styles.hint}>
            {isSuper
              ? 'Enable or disable supported trading symbols.'
              : 'Read-only — only super admins can mutate symbols.'}
          </Text>
        }
        ListEmptyComponent={<EmptyState text="No symbols yet — sync the catalog from the backend." />}
        renderItem={({ item }) => (
          <Card>
            <Row style={styles.row}>
              <View style={styles.symbolCol}>
                <Text style={styles.symbol}>{item.symbol}</Text>
                <Text style={styles.muted}>
                  {item.display_name || `${item.base}/${item.quote}`} · {item.provider}
                </Text>
              </View>
              <Badge color={item.is_active ? colors.green : colors.muted}>
                {item.is_active ? 'Active' : 'Inactive'}
              </Badge>
              {isSuper && (
                <Button
                  title={busy === item.symbol ? '…' : item.is_active ? 'Disable' : 'Enable'}
                  variant={item.is_active ? 'ghost' : 'primary'}
                  disabled={busy === item.symbol}
                  onPress={() => toggle(item)}
                />
              )}
            </Row>
          </Card>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  hint: { color: colors.muted, paddingHorizontal: 16, paddingTop: 8, fontSize: 13 },
  row: { justifyContent: 'space-between', alignItems: 'center' },
  symbolCol: { flex: 1, gap: 2 },
  symbol: { color: colors.text, fontSize: 16, fontWeight: '600' },
  muted: { color: colors.muted, fontSize: 12 },
  error: { color: colors.red, paddingHorizontal: 16, paddingTop: 8 },
});