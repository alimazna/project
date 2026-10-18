import { useEffect, useRef } from 'react'
import {
  ColorType,
  CrosshairMode,
  createChart,
  type HistogramData,
  type IChartApi,
  type ISeriesApi,
  type LineData,
  type UTCTimestamp,
} from 'lightweight-charts'
import type { CandleEntry } from '../lib/api'

export interface ChartLevel {
  price: number
  label: string
  color: string
}

interface CandleChartProps {
  candles: CandleEntry[]
  height?: number
  levels?: ChartLevel[]
}

function toUTC(iso: string): UTCTimestamp {
  return Math.floor(new Date(iso).getTime() / 1000) as UTCTimestamp
}

export function CandleChart({ candles, height = 360, levels = [] }: CandleChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const candleRef = useRef<ISeriesApi<'Candlestick'> | null>(null)
  const volumeRef = useRef<ISeriesApi<'Histogram'> | null>(null)
  const lineRefs = useRef<ISeriesApi<'Line'>[]>([])

  useEffect(() => {
    const el = containerRef.current
    if (!el) return

    const chart = createChart(el, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#8b96a8',
        fontFamily: "'Inter', system-ui, sans-serif",
      },
      grid: {
        vertLines: { color: 'rgba(38, 47, 64, 0.5)' },
        horzLines: { color: 'rgba(38, 47, 64, 0.5)' },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: 'rgba(38, 47, 64, 0.8)' },
      timeScale: { borderColor: 'rgba(38, 47, 64, 0.8)', timeVisible: true },
    })

    candleRef.current = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    })
    volumeRef.current = chart.addHistogramSeries({
      priceScaleId: '',
      priceFormat: { type: 'volume' },
    })
    volumeRef.current.priceScale().applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } })

    chartRef.current = chart

    const onResize = () => chart.applyOptions({ width: el.clientWidth })
    onResize()
    const ro = new ResizeObserver(onResize)
    ro.observe(el)

    return () => {
      ro.disconnect()
      chart.remove()
      chartRef.current = null
      candleRef.current = null
      volumeRef.current = null
      lineRefs.current = []
    }
  }, [height])

  useEffect(() => {
    if (!candleRef.current || !volumeRef.current) return
    candleRef.current.setData(
      candles.map((c) => ({
        time: toUTC(c.open_time),
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      })),
    )
    volumeRef.current?.setData(
      candles.map((c, i) => {
        const prev = candles[i - 1]?.close ?? c.open
        const up = c.close >= prev
        return {
          time: toUTC(c.open_time),
          value: c.volume,
          color: up ? 'rgba(34,197,94,0.35)' : 'rgba(239,68,68,0.35)',
        } as HistogramData
      }),
    )
    chartRef.current?.timeScale().fitContent()
  }, [candles])

  useEffect(() => {
    if (!chartRef.current) return
    for (const s of lineRefs.current) chartRef.current.removeSeries(s)
    lineRefs.current = []

    const lines = levels
      .filter((lv) => Number.isFinite(lv.price) && lv.price > 0)
      .map((lv) => {
        const series = chartRef.current!.addLineSeries({
          color: lv.color,
          lineWidth: 1,
          lineStyle: 2,
          lastValueVisible: false,
          crosshairMarkerVisible: false,
          priceLineVisible: false,
        })
        series.setData(
          candles.map((c) => ({ time: toUTC(c.open_time), value: lv.price } as LineData)),
        )
        series.createPriceLine({
          price: lv.price,
          color: lv.color,
          lineWidth: 1,
          lineStyle: 2,
          axisLabelVisible: true,
          title: lv.label,
        })
        return series
      })
    lineRefs.current = lines
  }, [levels, candles])

  return <div ref={containerRef} style={{ width: '100%' }} aria-label="Price chart" />
}