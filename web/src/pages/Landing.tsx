import { Link } from 'react-router-dom'
import { appName } from '../lib/config'

const NEWS = [
  { title: 'Bitcoin Halving Impact: New Analysis', meta: '12 months ago · 8.5k' },
  { title: 'Regulation Updates', meta: '19 hours ago · 6.9k' },
  { title: 'Altcoin Market Shifts', meta: '4 hours ago · 8.5k' },
]

const ANALYTICS = ['Segment Analysis', 'Volume Anomaly', 'Correlation Matrix']

export function Landing() {
  return (
    <section className="landing">
      {/* ===== Marketing nav (mirrors WEP.jpg) ===== */}
      <nav className="mkt-nav" aria-label="Marketing navigation">
        <div className="mkt-nav-left">
          <Link to="/plans">Features</Link>
          <Link to="/plans">Pricing</Link>
          <Link to="/dashboard">Demo</Link>
          <Link to="/login">Blog</Link>
        </div>
        <div className="mkt-nav-right">
          <Link to="/">Home</Link>
          <Link to="/plans">About</Link>
          <Link to="/dashboard">App</Link>
          <Link to="/plans">Pricing</Link>
          <Link className="btn btn-primary btn-sm" to="/register">
            Get Started Free
          </Link>
        </div>
      </nav>

      {/* ===== Hero split ===== */}
      <div className="landing-grid">
        {/* Left column */}
        <div className="landing-left">
          <div className="hero-eyebrow">{appName()} Home</div>
          <h1>
            Maximize Market Opportunity with <span className="emph">AI-Powered Intelligence</span>.
          </h1>
          <p className="lead">
            The predictive statistical platform for cryptocurrency traders. Analyze trends,
            anticipate moves, make smarter decisions, faster.
          </p>
          <div className="hero-actions">
            <Link className="btn btn-primary btn-lg" to="/dashboard">
              Download App
            </Link>
            <Link className="btn btn-outline btn-lg" to="/register">
              Go Pro
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
          <div className="analytics-row">
            {ANALYTICS.map((a) => (
              <span className="analytics-tag" key={a}>
                {a}
              </span>
            ))}
          </div>
        </div>

        {/* Right column */}
        <div className="landing-right">
          <h2 className="panel-title">Pricing Plans</h2>
          <div className="pricing-cards">
            <div className="plan-card-w">
              <h3>Basic</h3>
              <p className="price-tag">
                $0 <small>/month</small>
              </p>
              <ul className="plan-features">
                <li>Essential Analytics</li>
                <li>5 Watchlists</li>
                <li>Back Reports</li>
                <li>Prolt Reports</li>
              </ul>
              <Link className="btn btn-outline btn-block" to="/register">
                Get Basic
              </Link>
            </div>
            <div className="plan-card-w pricing-popular">
              <h3>Pro</h3>
              <p className="price-tag">
                $199 <small>/month</small>
              </p>
              <ul className="plan-features">
                <li>Advanced Predictions</li>
                <li>Unlimited Watchlists</li>
                <li>Full AI Insights</li>
                <li>Priority Support</li>
              </ul>
              <Link className="btn btn-primary btn-block" to="/register">
                Go Pro
              </Link>
            </div>
          </div>

          {/* Store + live market */}
          <div className="store-row">
            <a className="store-btn" href="#">
              Google Play
            </a>
            <a className="store-btn" href="#">
              App Store
            </a>
          </div>

          <div className="market-card">
            <div className="market-tabs">
              <span className="market-tab active">Mobile App</span>
              <span className="market-tab">App</span>
              <span className="market-tab">Live Market &amp; News</span>
            </div>
            <div className="market-body">
              <div>
                <span className="pairs">BTC/USD</span>
                <span className="pairs-sub">
                  Core Trends <span className="spark-up">▲ 8.85%</span>
                </span>
                <svg
                  className="sparkline"
                  viewBox="0 0 160 60"
                  preserveAspectRatio="none"
                  aria-hidden="true"
                >
                  <defs>
                    <linearGradient id="sparkfill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#2563eb" stopOpacity="0.35" />
                      <stop offset="100%" stopColor="#2563eb" stopOpacity="0.02" />
                    </linearGradient>
                  </defs>
                  <path
                    d="M0 46 L18 42 L34 47 L50 36 L66 40 L84 28 L100 32 L118 18 L136 22 L160 6 L160 60 L0 60 Z"
                    fill="url(#sparkfill)"
                  />
                  <path
                    d="M0 46 L18 42 L34 47 L50 36 L66 40 L84 28 L100 32 L118 18 L136 22 L160 6"
                    fill="none"
                    stroke="#2563eb"
                    strokeWidth="2"
                  />
                </svg>
              </div>
              <div className="news-scroll">
                <h3 className="news-title">News</h3>
                <ul className="news-list">
                  {NEWS.map((n) => (
                    <li key={n.title}>
                      <strong>{n.title}</strong>
                      <span>{n.meta}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ===== Feature chips ===== */}
      <div className="chip-row" style={{ marginTop: '2.4rem' }}>
        <span className="feature-chip">Real-time Processing</span>
        <span className="feature-chip blue">Advanced Forecasting</span>
        <span className="feature-chip green">Automated Insights</span>
      </div>

      {/* ===== Feature cards ===== */}
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

      {/* ===== Footer ===== */}
      <footer className="landing-footer">
        <div className="footer-cols">
          <div className="footer-col">
            <h4>About</h4>
            <a href="#">About</a>
            <a href="#">Features</a>
            <a href="#">Resources</a>
          </div>
          <div className="footer-col">
            <h4>Features</h4>
            <a href="#">Blogs</a>
            <a href="#">Users</a>
            <a href="#">Events</a>
            <a href="#">Contact</a>
          </div>
          <div className="footer-col">
            <h4>Solotions</h4>
            <a href="#">Pricing</a>
            <a href="#">Contact Us</a>
          </div>
          <div className="footer-col">
            <h4>{appName()}</h4>
            <p className="muted">
              An AI-powered statistical analytics platform. Real-time processing, advanced
              forecasting, and automated insights for better decisions.
            </p>
          </div>
        </div>
        <p className="footer-bottom">
          Copyright © 2024 TrendCipher · Design in {appName()}
        </p>
      </footer>
    </section>
  )
}