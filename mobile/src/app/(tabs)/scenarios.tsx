import { Link } from 'expo-router';
import React, { useCallback, useEffect, useState } from 'react';
import { FlatList, RefreshControl, StyleSheet, Text, View } from 'react-native';
import { Badge, Card, EmptyState, Row } from '../../components/ui';
import { api, type ScenarioDetail } from '../../lib/api';
import { timeAgo } from '../../lib/format';
import { colors } from '../../lib/theme';

function directionColor(direction: ScenarioDetail['direction']) {
  if (direction === 'BULLISH') return colors.green;
  if (direction === 'BEARISH') return colors.red;
  return colors.yellow;
}

export default function ScenariosScreen() {
  const [scenarios, setScenarios] = useState<ScenarioDetail[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const { scenarios: s } = await api.getScenarios(undefined, 20);
      setScenarios(s);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analyses');
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
        data={scenarios}
        keyExtractor={(s) => String(s.id)}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.muted} />}
        ListHeaderComponent={
          <Text style={styles.hint}>
            Past deterministic technical analyses. Use the asset page to run a fresh one.
          </Text>
        }
        ListEmptyComponent={<EmptyState text="No analyses yet — run one from an asset page" />}
        renderItem={({ item }) => (
          <Link href={{ pathname: '/analysis/[id]', params: { id: String(item.id) } }} asChild>
            <Card>
              <Row style={styles.topRow}>
                <Text style={styles.symbol}>
                  {item.symbol} · {item.timeframe}
                </Text>
                <Badge color={directionColor(item.direction)}>{item.direction}</Badge>
              </Row>
              <Row style={styles.meta}>
                <Text style={styles.muted}>Alignment {item.alignment_score}%</Text>
                <Text style={styles.dot}>·</Text>
                <Text style={styles.muted}>{item.status}</Text>
                <Text style={styles.dot}>·</Text>
                <Text style={styles.muted}>{timeAgo(item.created_at)}</Text>
              </Row>
              <Text style={styles.evidence}>
                {item.evidence.bullish ?? 0} bullish / {item.evidence.bearish ?? 0} bearish signals
              </Text>
              {item.open_window ? (
                <Text style={styles.window}>Trading window: {item.open_window}</Text>
              ) : null}
              {item.advisor_tips && item.advisor_tips.length > 0 ? (
                <Text numberOfLines={1} style={styles.tip}>
                  ⚡ {item.advisor_tips[0]}
                </Text>
              ) : null}
            </Card>
          </Link>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  hint: { color: colors.muted, paddingHorizontal: 16, paddingTop: 8, fontSize: 13 },
  topRow: { justifyContent: 'space-between', marginBottom: 8 },
  symbol: { color: colors.text, fontSize: 17, fontWeight: '700' },
  meta: { gap: 6, marginBottom: 6 },
  muted: { color: colors.muted, fontSize: 13 },
  dot: { color: colors.muted },
  evidence: { color: colors.text, fontSize: 13 },
  window: { color: colors.yellow, fontSize: 12, marginTop: 6, fontWeight: '600' },
  tip: { color: colors.accent, fontSize: 12, marginTop: 4 },
  error: { color: colors.red, paddingHorizontal: 16, paddingTop: 8 },
});