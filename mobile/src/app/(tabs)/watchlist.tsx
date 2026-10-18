import { Link } from 'expo-router';
import React, { useCallback, useEffect, useState } from 'react';
import { FlatList, RefreshControl, StyleSheet, Text, View } from 'react-native';
import { Button, Card, EmptyState, Row } from '../../components/ui';
import { api, type Watchlist } from '../../lib/api';
import { colors } from '../../lib/theme';

export default function WatchlistScreen() {
  const [lists, setLists] = useState<Watchlist[]>([]);
  const [selected, setSelected] = useState<Watchlist | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const { watchlists } = await api.getWatchlists();
      setLists(watchlists);
      setSelected((prev) => {
        if (prev) {
          const upd = watchlists.find((w) => w.id === prev.id);
          if (upd) return upd;
        }
        return watchlists.find((w) => w.is_default) ?? watchlists[0] ?? null;
      });
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load watchlist');
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

  const symbols = selected?.symbols ?? [];

  return (
    <View style={styles.screen}>
      {error !== '' && <Text style={styles.error}>{error}</Text>}
      <FlatList
        data={symbols}
        keyExtractor={(s) => s}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.muted} />}
        ListHeaderComponent={
          <View style={styles.header}>
            <Row style={{ gap: 8, flexWrap: 'wrap' }}>
              {lists.map((w) => (
                <Button
                  key={w.id}
                  title={w.name}
                  variant={selected?.id === w.id ? 'primary' : 'ghost'}
                  onPress={() => setSelected(w)}
                  style={{ flexShrink: 1 }}
                />
              ))}
            </Row>
            <Text style={styles.hint}>
              {selected && selected.id > 0
                ? 'Symbols in this watchlist — tap to analyze.'
                : 'No list selected.'}
            </Text>
          </View>
        }
        ListEmptyComponent={<EmptyState text="Add symbols from an asset page to build your watchlist" />}
        renderItem={({ item }) => (
          <Link href={{ pathname: '/asset/[symbol]', params: { symbol: item } }} asChild>
            <Card style={styles.rowCard}>
              <Text style={styles.symbol}>{item}</Text>
              <Text style={styles.chevron}>›</Text>
            </Card>
          </Link>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  header: { padding: 12, gap: 8 },
  hint: { color: colors.muted, fontSize: 13 },
  rowCard: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  symbol: { color: colors.text, fontSize: 16, fontWeight: '600' },
  chevron: { color: colors.muted, fontSize: 20 },
  error: { color: colors.red, paddingHorizontal: 16, paddingTop: 8 },
});