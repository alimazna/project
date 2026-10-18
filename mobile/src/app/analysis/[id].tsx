import { Redirect, useLocalSearchParams } from 'expo-router';
import React, { useCallback, useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { Card, Row, Stat } from '../../components/ui';
import { useAuth } from '../../context/AuthContext';
import { api, type ScenarioDetail } from '../../lib/api';
import { formatPrice } from '../../lib/format';
import { colors } from '../../lib/theme';

function directionColor(d: ScenarioDetail['direction']) {
  if (d === 'BULLISH') return colors.green;
  if (d === 'BEARISH') return colors.red;
  return colors.yellow;
}

export default function AnalysisDetailScreen() {
  const { accessToken, loading } = useAuth();
  const { id } = useLocalSearchParams<{ id: string }>();
  const [scenario, setScenario] = useState<ScenarioDetail | null>(null);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setError('');
    try {
      const { scenario: s } = await api.get<{ scenario: ScenarioDetail }>(
        `/analysis/scenarios/${id}`,
      );
      setScenario(s);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analysis');
    }
  }, [id]);

  useEffect(() => {
    (async () => {
      await load();
    })().catch(() => undefined);
  }, [load]);

  if (loading) {
    return (
      <View style={styles.screen}>
        <Text style={styles.muted}>Loading…</Text>
      </View>
    );
  }
  if (!accessToken) return <Redirect href="/login" />;

  if (!scenario) {
    return (
      <View style={styles.screen}>
        {error !== '' && <Text style={styles.error}>{error}</Text>}
        <Text style={styles.muted}>Loading…</Text>
      </View>
    );
  }

  const invalidation = scenario.invalidation ?? {};

  return (
    <ScrollView style={styles.screen} contentContainerStyle={styles.content}>
      <Card>
        <Row style={styles.topRow}>
          <Text style={styles.symbol}>
            {scenario.symbol} · {scenario.timeframe}
          </Text>
          <Text style={[styles.dir, { color: directionColor(scenario.direction) }]}>
            {scenario.direction}
          </Text>
        </Row>
        <Row style={styles.stats}>
          <Stat title="Alignment" value={`${scenario.alignment_score}%`} />
          <Stat title="Risk/Reward" value={scenario.risk_reward?.toFixed(2)} />
          <Stat title="Status" value={scenario.status} />
          <Stat title="Rule v" value={scenario.rule_version} />
        </Row>
        {(scenario.entry_low != null || scenario.entry_high != null) && (
          <Text style={styles.plan}>
            Entry {formatPrice(scenario.entry_low)} – {formatPrice(scenario.entry_high)} · Stop{' '}
            {formatPrice(scenario.stop_loss)}
          </Text>
        )}
        {Object.keys(invalidation).length > 0 && (
          <Text style={styles.invalidation}>
            Invalidation: {Object.entries(invalidation).map(([k, v]) => `${k}=${String(v)}`).join(' ')}
          </Text>
        )}
      </Card>

      <Card>
        <Text style={styles.sectionTitle}>Evidence</Text>
        <View style={styles.evidenceRow}>
          <Text style={styles.mutedBig}>Signals evaluated</Text>
          <Text style={styles.value}>{scenario.evidence?.signals_evaluated ?? '—'}</Text>
        </View>
        {(['bullish', 'bearish', 'neutral'] as const).map((k) => (
          <View key={k} style={styles.evidenceRow}>
            <Text style={styles.mutedBig}>{k}</Text>
            <Text style={styles.value}>{scenario.evidence?.[k] ?? 0}</Text>
          </View>
        ))}
        <View style={styles.evidenceRow}>
          <Text style={styles.mutedBig}>Weighted alignment</Text>
          <Text style={styles.value}>{scenario.evidence?.weighted_alignment?.toFixed(2) ?? '—'}</Text>
        </View>
      </Card>

      {Array.isArray(scenario.decisions) && scenario.decisions.length > 0 && (
        <Card>
          <Text style={styles.sectionTitle}>Decision matrix</Text>
          <Row style={[styles.matrixHead, styles.matrixRow]}>
            <Text style={[styles.matrixCell, styles.signalCol]}>Signal</Text>
            <Text style={styles.matrixCell}>Vote</Text>
            <Text style={styles.matrixCell}>Weight</Text>
            <Text style={styles.matrixCell}>Aligned</Text>
          </Row>
          {scenario.decisions.map((d, i) => (
            <View key={`${d.signal}-${i}`}>
              <Row style={styles.matrixRow}>
                <Text style={[styles.matrixCell, styles.signalCol, styles.signalText]}>{d.signal}</Text>
                <Text style={styles.matrixCell}>{d.vote}</Text>
                <Text style={styles.matrixCell}>{d.weight}</Text>
                <Text style={styles.matrixCell}>{d.aligned}</Text>
              </Row>
              {d.reason ? <Text style={styles.reason}>{d.reason}</Text> : null}
            </View>
          ))}
        </Card>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 16 },
  topRow: { justifyContent: 'space-between', marginBottom: 10 },
  symbol: { color: colors.text, fontSize: 20, fontWeight: '700' },
  dir: { fontSize: 16, fontWeight: '700' },
  stats: { marginBottom: 10 },
  plan: { color: colors.muted, fontSize: 13, marginTop: 4 },
  invalidation: { color: colors.yellow, fontSize: 13, marginTop: 4 },
  sectionTitle: { color: colors.text, fontSize: 16, fontWeight: '600', marginBottom: 10 },
  evidenceRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 4 },
  mutedBig: { color: colors.muted, fontSize: 14, textTransform: 'capitalize' },
  value: { color: colors.text, fontSize: 14, fontWeight: '500' },
  matrixHead: { borderBottomWidth: 1, borderBottomColor: colors.border, paddingBottom: 4, marginBottom: 4 },
  matrixRow: { justifyContent: 'space-between' },
  matrixCell: { color: colors.muted, fontSize: 13, flex: 1, textAlign: 'center' },
  signalCol: { textAlign: 'left', flex: 2 },
  signalText: { color: colors.text, fontWeight: '600' },
  reason: { color: colors.muted, fontSize: 12, marginTop: 4, marginBottom: 8 },
  error: { color: colors.red, marginBottom: 8 },
  muted: { color: colors.muted },
});