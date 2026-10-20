import { Link } from 'react-router-dom'
import { appName } from '../lib/config'

export function Landing() {
  return (
    <section className="landing">
      {/* Hero — matches UI WEB.jpg */}
      <div className="hero hero-v2">
        <div className="chip-row">
          <span className="feature-chip">Real-time Processing</span>
          <span className="feature-chip blue">Advanced Forecasting</span>
          <span className="feature-chip green">Automated Insights</span>
        </div>
        <h1>
          Maximize Market Opportunity with <span className="emph">AI-Powered Intelligence</span>.
        </h1>
        <p className="lead">
          The predictive statistical platform for cryptocurrency traders. Analyze trends,
          anticipate moves, make smarter decisions — faster. Every signal remains fully
          auditable, never a black box.
        </p>
        <div className="hero-actions">
          <Link className="btn btn-primary btn-lg" to="/register">
            Get Started
          </Link>
          <Link className="btn btn-outline btn-lg" to="/dashboard">
            Watchlists
          </Link>
        </div>
        <div className="hero-stats">
          <div className="hero-stat">
            <strong>17K</strong>
            <span>Predictive Trends</span>
          </div>
          <div className="hero-stat">
            <strong>3023</strong>
            <span>Anomaly Growth</span>
          </div>
          <div className="hero-stat">
            <strong>57</strong>
            <span>News Impact</span>
          </div>
        </div>
      </div>

      {/* Features — matches Real-time Processing / Advanced Forecasting / Automated Insights */}
      <div className="feature-grid">
        <div className="card feature-card">
          <div className="icon-badge">⚡</div>
          <h3>Real-time Processing</h3>
          <p className="muted">
            Real-time processing to make smarter decisions. Live market data, news
            intelligence, and deterministic technical signals in one feed.
          </p>
        </div>
        <div className="card feature-card">
          <div className="icon-badge">📈</div>
          <h3>Advanced Forecasting</h3>
          <p className="muted">
            Leverage {appName()}'s advanced forecasting and AI analytics: entry zones,
            targets, stop-losses, and alignment scores you can audit.
          </p>
        </div>
        <div className="card feature-card">
          <div className="icon-badge">🤖</div>
          <h3>Automated Insights</h3>
          <p className="muted">
            Automated insights for actionable outcomes. Evidence-backed scenarios with
            source attribution — news is evidence, not prediction.
          </p>
        </div>
      </div>

      {/* Pricing — matches $30/month design */}
      <div className="plan-grid" style={{ marginTop: '2.5rem' }}>
        <div className="card pricing-popular">
          <h3>Pro</h3>
          <p className="price-tag">
            $30 <small>/month</small>
          </p>
          <ul className="plan-features">
            <li>Full market scanner (17+ assets)</li>
            <li>Explainable scenarios &amp; evidence cards</li>
            <li>News intelligence with source attribution</li>
            <li>Watchlists, alerts &amp; push notifications</li>
            <li>Rule-versioned, audit-proof analysis</li>
          </ul>
          <div style={{ marginTop: '1.2rem' }}>
            <Link className="btn btn-primary" to="/register">
              Start free trial
            </Link>
          </div>
        </div>
      </div>
    </section>
  )
}