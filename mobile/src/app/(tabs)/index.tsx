import { Link } from 'expo-router';
import React, { useCallback, useEffect, useState } from 'react';
import { FlatList, RefreshControl, StyleSheet, Text, View } from 'react-native';
import { Card, EmptyState, Row } from '../../components/ui';
import { api, type TickerEntry } from '../../lib/api';
import { formatPct, formatPrice } from '../../lib/format';
import { colors } from '../../lib/theme';

export default function DashboardScreen() {
  const [tickers, setTickers] = useState<TickerEntry[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const { tickers: t } = await api.getTickers();
      setTickers(t);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load market data');
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

  return (
    <View style={styles.screen}>
      {error !== '' && <Text style={styles.error}>{error}</Text>}
      <FlatList
        data={tickers}
        keyExtractor={(item) => item.symbol}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.muted} />}
        ListHeaderComponent={
          <View style={styles.header}>
            <Text style={styles.hint}>Live tickers from connected exchanges. Tap a symbol to analyze.</Text>
          </View>
        }
        ListEmptyComponent={<EmptyState text="No market data yet — start the backend and pull to refresh" />}
        renderItem={({ item }) => (
          <Link href={{ pathname: '/asset/[symbol]', params: { symbol: item.symbol } }} asChild>
            <Card style={styles.rowCard}>
              <View style={styles.symbolCol}>
                <Text style={styles.symbol}>{item.symbol}</Text>
              </View>
              <Row style={styles.nums}>
                <Text style={styles.price}>{formatPrice(item.last_price)}</Text>
                <Text
                  style={[
                    styles.pct,
                    { color: (item.change_24h_pct ?? 0) >= 0 ? colors.green : colors.red },
                  ]}
                >
                  {formatPct(item.change_24h_pct)}
                </Text>
              </Row>
            </Card>
          </Link>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  header: { padding: 12 },
  hint: { color: colors.muted, fontSize: 13 },
  rowCard: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  symbolCol: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  symbol: { color: colors.text, fontSize: 16, fontWeight: '600' },
  nums: { gap: 10 },
  price: { color: colors.text, fontSize: 15, fontWeight: '500' },
  pct: { fontSize: 14, fontWeight: '600' },
  error: { color: colors.red, paddingHorizontal: 16, paddingTop: 8 },
});