import { Redirect, useLocalSearchParams, useRouter } from 'expo-router';
import React, { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Button, Card, Row, Stat } from '../../components/ui';
import CandleChart from '../../components/CandleChart';
import { useAuth } from '../../context/AuthContext';
import { api, type CandleEntry, type ScenarioDetail } from '../../lib/api';
import { formatPrice } from '../../lib/format';
import { colors } from '../../lib/theme';

const INTERVALS = ['1h', '4h', '1d', '1w'] as const;

export default function AssetScreen() {
  const { accessToken, loading } = useAuth();
  const { symbol } = useLocalSearchParams<{ symbol: string }>();
  const router = useRouter();
  const sym = symbol ?? '';

  const [interval, setInterval] = useState<string>('1d');
  const [candles, setCandles] = useState<CandleEntry[]>([]);
  const [scenario, setScenario] = useState<ScenarioDetail | null>(null);
  const [loadingChart, setLoadingChart] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');
  const [watchlistAdd, setWatchlistAdd] = useState('');

  const loadCandles = useCallback(async () => {
    setLoadingChart(true);
    setError('');
    try {
      const { candles: c } = await api.getCandles(sym, interval, 150);
      setCandles(c);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load candles');
    } finally {
      setLoadingChart(false);
    }
  }, [sym, interval]);

  useEffect(() => {
    if (!sym) return;
    (async () => {
      await loadCandles();
    })().catch(() => undefined);
  }, [sym, loadCandles]);

  async function runAnalysis() {
    setRunning(true);
    setError('');
    try {
      const { scenario: s } = await api.runAnalysis(sym, interval);
      setScenario(s);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setRunning(false);
    }
  }

  async function addToWatchlist() {
    setError('');
    try {
      const { watchlists } = await api.getWatchlists();
      const target = watchlists.find((w) => w.is_default) ?? watchlists[0];
      if (!target) {
        setError('No watchlist exists yet — create one on the web or via API.');
        return;
      }
      await api.put(`/watchlists/${target.id}`, {
        symbols: [...new Set([...target.symbols, sym])],
      });
      setWatchlistAdd('Added to your watchlist.');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update watchlist');
    }
  }

  if (loading) return null;
  if (!accessToken) return <Redirect href="/login" />;

  const last = candles[candles.length - 1];

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <Row style={styles.titleRow}>
        <Text style={styles.symbol}>{sym}</Text>
        {last ? (
          <Text style={styles.price}>{formatPrice(last.close)}</Text>
        ) : null}
      </Row>

      <Row style={styles.intervalRow}>
        {INTERVALS.map((iv) => (
          <Button
            key={iv}
            title={iv}
            variant={interval === iv ? 'primary' : 'ghost'}
            onPress={() => setInterval(iv)}
            style={{ flexShrink: 1 }}
          />
        ))}
      </Row>

      {loadingChart ? (
        <ActivityIndicator color={colors.accent} style={{ margin: 24 }} />
      ) : (
        <CandleChart candles={candles} />
      )}

      <Card>
        <Row style={styles.actionRow}>
          <Button title={running ? 'Analyzing…' : 'Run analysis'} onPress={runAnalysis} loading={running} />
          <Button title="Add to watchlist" variant="ghost" onPress={addToWatchlist} />
        </Row>
        {watchlistAdd !== '' && <Text style={styles.ok}>{watchlistAdd}</Text>}
        {error !== '' && <Text style={styles.error}>{error}</Text>}

        {scenario ? (
          <View style={styles.result}>
            <Row style={styles.resultTop}>
              <Text style={styles.resultTitle}>Scenario</Text>
              <Text style={styles.resultDir}>{scenario.direction}</Text>
            </Row>
            <Row style={styles.stats}>
              <Stat title="Alignment" value={`${scenario.alignment_score}%`} />
              <Stat title="Risk/Reward" value={scenario.risk_reward?.toFixed(2)} />
              <Stat title="Status" value={scenario.status} />
              <Stat title="Rule" value={scenario.rule_version} />
            </Row>
            <Text style={styles.hint}>
              Explained decisions and evidence are available in the full analysis view.
            </Text>
            {scenario.id ? (
              <Button
                title="Open full analysis"
                onPress={() => router.push({ pathname: '/analysis/[id]', params: { id: String(scenario.id) } })}
              />
            ) : null}
          </View>
        ) : null}
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 16 },
  titleRow: { justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  symbol: { color: colors.text, fontSize: 24, fontWeight: '700' },
  price: { color: colors.text, fontSize: 20, fontWeight: '600' },
  intervalRow: { marginBottom: 8, gap: 6 },
  actionRow: { justifyContent: 'flex-start', gap: 8 },
  result: { marginTop: 16 },
  resultTop: { justifyContent: 'space-between', marginBottom: 10 },
  resultTitle: { color: colors.text, fontSize: 16, fontWeight: '600' },
  resultDir: { color: colors.accent, fontSize: 15, fontWeight: '700' },
  stats: { marginBottom: 8 },
  hint: { color: colors.muted, fontSize: 12, marginBottom: 12 },
  ok: { color: colors.green, marginTop: 8 },
  error: { color: colors.red, marginTop: 8 },
});