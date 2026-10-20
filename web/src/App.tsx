import { NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { brandParts } from './lib/config'
import { Account } from './pages/Account'
import { Admin } from './pages/Admin'
import { Alerts } from './pages/Alerts'
import { AssetDetail } from './pages/AssetDetail'
import { Dashboard } from './pages/Dashboard'
import { Landing } from './pages/Landing'
import { Login } from './pages/Login'
import { Register } from './pages/Register'
import { Plans } from './pages/Plans'
import { Scanner } from './pages/Scanner'
import { Scenarios } from './pages/Scenarios'
import { WatchlistPage } from './pages/Watchlist'

// Mobile bottom-nav items (mirror UI USER design's tab bar)
const TAB_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: '◧' },
  { to: '/watchlist', label: 'Watchlist', icon: '★' },
  { to: '/scenarios', label: 'Scenarios', icon: '⚑' },
  { to: '/alerts', label: 'Alerts', icon: '🔔' },
]

export function App() {
  const { pathname } = useLocation()
  const isAppPage = pathname !== '/' && pathname !== '/plans' && pathname !== '/login'

  return (
    <div className="app-shell">
      <header className="app-header">
        <NavLink to="/" className="brand">
          {(() => {
            const [head, tail] = brandParts()
            return (
              <>
                {head}
                {tail && <span>{tail}</span>}
              </>
            )
          })()}
        </NavLink>
        <nav className="app-nav">
          <NavLink to="/">Home</NavLink>
          <NavLink to="/plans">Pricing</NavLink>
          <NavLink to="/dashboard">App</NavLink>
          <NavLink to="/scanner">Scanner</NavLink>
          <NavLink to="/scenarios">Scenarios</NavLink>
          <NavLink to="/watchlist">Watchlist</NavLink>
          <NavLink to="/alerts">Alerts</NavLink>
          <NavLink to="/account">Account</NavLink>
          <NavLink to="/admin">Admin</NavLink>
          <NavLink to="/login">Sign in</NavLink>
          <span className="live-line">
            <span className="live-dot" />
            live
          </span>
        </nav>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/plans" element={<Plans />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/asset/:symbol" element={<AssetDetail />} />
          <Route path="/scanner" element={<Scanner />} />
          <Route path="/scenarios" element={<Scenarios />} />
          <Route path="/watchlist" element={<WatchlistPage />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/account" element={<Account />} />
          <Route path="/admin" element={<Admin />} />
        </Routes>
      </main>

      {isAppPage && (
        <nav className="mobile-tabbar" aria-label="Mobile navigation">
          {TAB_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === '/dashboard'}>
              <span className="tab-ico">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
      )}
    </div>
  )
}