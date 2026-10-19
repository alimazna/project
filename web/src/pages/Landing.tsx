import { Link } from 'react-router-dom'
import { appName } from '../lib/config'

export function Landing() {
  return (
    <section className="landing">
      <div className="hero">
        <h1>Explainable crypto market intelligence</h1>
        <p className="lead">
          {appName()} fuses news intelligence with deterministic technical analysis to
          produce conditional, traceable scenarios — entry zones, targets, and stop-losses
          you can audit, not a black-box signal.
        </p>
        <div className="hero-actions">
          <Link className="btn btn-primary" to="/register">
            Try the app free
          </Link>
          <Link className="btn btn-outline" to="/plans">
            View pricing
          </Link>
        </div>
      </div>

      <div className="feature-grid">
        <div className="card">
          <h3>News intelligence</h3>
          <p>
            Collects and classifies crypto and macro news from public RSS feeds,
            deduplicates stories, maps them to assets, and records source attribution.
          </p>
        </div>
        <div className="card">
          <h3>Deterministic analysis</h3>
          <p>
            EMA, RSI, ATR, trend structure and volume — computed on closed candles only,
            rule-versioned, and reproducible with identical inputs.
          </p>
        </div>
        <div className="card">
          <h3>Explainable scenarios</h3>
          <p>
            Bullish, bearish, neutral or insufficient-data states with entry zones,
            take-profits, invalidation levels, and the exact evidence used.
          </p>
        </div>
        <div className="card">
          <h3>No black boxes</h3>
          <p>
            News is evidence, not fact. Scores are alignment scores — never implied
            win rates or guaranteed profits.
          </p>
        </div>
      </div>
    </section>
  )
}