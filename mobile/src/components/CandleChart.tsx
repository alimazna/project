// Lightweight candlestick chart rendered with react-native-svg.
// (Native Android/iOS — the browser build uses TradingView lightweight-charts.)

import React, { useMemo } from 'react';
import { StyleSheet, View, useWindowDimensions } from 'react-native';
import Svg, { Line, Rect } from 'react-native-svg';
import { colors } from '../lib/theme';
import type { CandleEntry } from '../lib/api';

interface Props {
  candles: CandleEntry[];
  height?: number;
}

export default function CandleChart({ candles, height = 220 }: Props) {
  const { width } = useWindowDimensions();
  const data = useMemo(() => compute(candles, width), [candles, width]);

  if (!data) {
    return <View style={{ height }} />;
  }

  return (
    <View style={styles.wrap}>
      <Svg width={width - 32} height={height}>
        {data.candles.map((c, i) => (
          <CandleGlyph key={i} c={c} />
        ))}
      </Svg>
    </View>
  );
}

interface Glyph {
  x: number;
  bodyY: number;
  bodyH: number;
  wickTop: number;
  wickBottom: number;
  up: boolean;
}

function compute(candles: CandleEntry[], width: number): { candles: Glyph[] } | null {
  if (!candles.length) return null;
  const highs = candles.map((c) => c.high);
  const lows = candles.map((c) => c.low);
  const max = Math.max(...highs);
  const min = Math.min(...lows);
  const range = max - min || 1;
  const pad = 8;
  const chartW = width - 40;
  const chartH = 220 - pad * 2;
  const step = chartW / candles.length;
  const bodyW = Math.max(2, step * 0.6);

  const glyphs = candles.map((c, i) => {
    const x = i * step + bodyW / 2 + 4;
    const yFor = (v: number) => pad + ((max - v) / range) * chartH;
    const top = yFor(Math.max(c.open, c.close));
    const bot = yFor(Math.min(c.open, c.close));
    return {
      x,
      bodyY: top,
      bodyH: Math.max(1.5, bot - top),
      wickTop: yFor(c.high),
      wickBottom: yFor(c.low),
      up: c.close >= c.open,
    } satisfies Glyph;
  });
  return { candles: glyphs };
}

function CandleGlyph({ c }: { c: Glyph }) {
  const color = c.up ? colors.green : colors.red;
  return (
    <>
      <Line
        x1={c.x}
        y1={c.wickTop}
        x2={c.x}
        y2={c.wickBottom}
        stroke={color}
        strokeWidth={1}
      />
      <Rect
        x={c.x - 1.5}
        y={c.bodyY}
        width={3}
        height={c.bodyH}
        fill={color}
      />
    </>
  );
}

const styles = StyleSheet.create({
  wrap: { marginVertical: 4 },
});