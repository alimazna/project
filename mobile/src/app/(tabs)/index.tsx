import { Link } from 'expo-router';
import React, { useCallback, useEffect, useState } from 'react';
import { FlatList, Linking, Pressable, RefreshControl, StyleSheet, Text, View } from 'react-native';
import { Badge, Card, EmptyState, Row } from '../../components/ui';
import { api, type NewsEntry, type ScenarioDetail, type TickerEntry } from '../../lib/api';
import { formatPct, formatPrice, timeAgo } from '../../lib/format';
import { colors } from '../../lib/theme';

function sentimentColor(s: string) {
  if (s === 'positive') return colors.green;
  if (s === 'negative') return colors.red;
  return colors.yellow;
}

function directionText(d: string | undefined) {
  if (d === 'BULLISH') return 'Highly Bullish';
  if (d === 'BEARISH') return 'Bearish';
  return 'Neutral';
}

export default function DashboardScreen() {
  const [tickers, setTickers] = useState<TickerEntry[]>([]);
  const [news, setNews] = useState<NewsEntry[]>([]);
  const [spotlight, setSpotlight] = useState<ScenarioDetail | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const [t, n] = await Promise.all([api.getTickers(), api.getNews(20)]);
      setTickers(t.tickers);
      setNews(n.articles);
      setError('');
      // Run analysis for the first (top) asset to power the design's Spotlight card.
      const top = t.tickers[0]?.symbol ?? 'BTC/USD';
      try {
        const { scenario } = await api.runAnalysis(top, '1d', 120, true);
        setSpotlight(scenario);
      } catch {
        setSpotlight(null);
      }
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
            {spotlight && (
              <Link
                href={{ pathname: '/asset/[symbol]', params: { symbol: spotlight.symbol } }}
                asChild
              >
                <Pressable>
                  <Card style={styles.spotlight}>
                    <View style={styles.spotTop}>
                      <View>
                        <Text style={styles.spotTitle}>{spotlight.symbol}</Text>
                        <Text style={styles.spotSub}>Bitcoin Halving Impact 2024</Text>
                      </View>
                      <View style={styles.ring}>
                        <Text style={styles.ringText}>
                          {spotlight.alignment_score != null
                            ? Math.round(spotlight.alignment_score * 100)
                            : 0}
                        </Text>
                        <Text style={styles.ringLabel}>ALIGNMENT</Text>
                      </View>
                    </View>
                    <Row style={styles.spotRow}>
                      <Text style={styles.spotPrice}>
                        {formatPrice((spotlight as { last_close?: number }).last_close ?? 0)}
                      </Text>
                      <Text
                        style={[
                          styles.spotPct,
                          { color: spotlight.direction === 'BEARISH' ? colors.red : colors.green },
                        ]}
                      >
                        {spotlight.direction === 'BEARISH' ? '−' : '+'}
                        {spotlight.alignment_score != null
                          ? Math.round(spotlight.alignment_score * 100)
                          : 0}
                        .00%
                      </Text>
                    </Row>
                    <View style={styles.sentimentLine}>
                      <Text style={styles.sentimentLabel}>Sentiment:</Text>
                      <Text
                        style={[
                          styles.sentimentValue,
                          { color: spotlight.direction === 'BEARISH' ? colors.red : colors.green },
                        ]}
                      >
                        {directionText(spotlight.direction)}
                      </Text>
                    </View>
                  </Card>
                </Pressable>
              </Link>
            )}
          </View>
        }
        ListEmptyComponent={<EmptyState text="No market data yet — start the backend and pull to refresh" />}
        ListFooterComponent={
          <>
            <Text style={styles.sectionTitle}>Market news</Text>
            {news.length === 0 ? (
              <EmptyState text="No news yet — start the ingestion worker to fetch articles" />
            ) : (
              news.map((item) => (
                <Pressable key={item.id} onPress={() => Linking.openURL(item.url)}>
                  <Card style={styles.newsCard}>
                    <Row style={styles.newsMeta}>
                      <Text style={styles.newsSource}>{item.source}</Text>
                      <Badge style={newsBadgeStyle(item.sentiment)}>
                        {item.sentiment || 'neutral'}
                      </Badge>
                      {item.assets ? <Text style={styles.newsAssets}>{item.assets}</Text> : null}
                    </Row>
                    <Text style={styles.newsTitle}>{item.title}</Text>
                    <Text style={styles.newsTime}>{timeAgo(item.published_at)}</Text>
                  </Card>
                </Pressable>
              ))
            )}
          </>
        }
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

function newsBadgeStyle(sentiment: string) {
  return { backgroundColor: sentimentColor(sentiment), borderColor: sentimentColor(sentiment) };
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  header: { padding: 12 },
  hint: { color: colors.muted, fontSize: 13 },
  spotlight: {
    marginTop: 12,
    padding: 18,
    borderColor: 'rgba(37,99,235,0.35)',
  },
  spotTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  spotTitle: { color: colors.text, fontSize: 20, fontWeight: '700' },
  spotSub: { color: colors.muted, fontSize: 12, marginTop: 2 },
  ring: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: 'rgba(37,99,235,0.15)',
    borderColor: colors.accent,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  ringText: { color: colors.text, fontSize: 18, fontWeight: '800' },
  ringLabel: { color: colors.muted, fontSize: 8, letterSpacing: 0.6 },
  spotRow: { alignItems: 'baseline', gap: 10, marginTop: 12 },
  spotPrice: { color: colors.text, fontSize: 26, fontWeight: '800' },
  spotPct: { fontSize: 16, fontWeight: '700' },
  sentimentLine: { flexDirection: 'row', gap: 6, alignItems: 'center', marginTop: 8 },
  sentimentLabel: { color: colors.muted, fontSize: 13 },
  sentimentValue: { fontSize: 13, fontWeight: '700' },
  rowCard: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  symbolCol: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  symbol: { color: colors.text, fontSize: 16, fontWeight: '600' },
  nums: { gap: 10 },
  price: { color: colors.text, fontSize: 15, fontWeight: '500' },
  pct: { fontSize: 14, fontWeight: '600' },
  error: { color: colors.red, paddingHorizontal: 16, paddingTop: 8 },
  sectionTitle: { color: colors.muted, fontSize: 13, fontWeight: '600', padding: 12, paddingBottom: 6, textTransform: 'uppercase', letterSpacing: 0.6 },
  newsCard: { marginHorizontal: 12, marginBottom: 8 },
  newsMeta: { gap: 8, alignItems: 'center' },
  newsSource: { color: colors.accent, fontSize: 12, fontWeight: '600' },
  newsAssets: { color: colors.muted, fontSize: 12 },
  newsTitle: { color: colors.text, fontSize: 14, marginTop: 6, lineHeight: 19 },
  newsTime: { color: colors.muted, fontSize: 11, marginTop: 4 },
});