import { NavLink, Route, Routes } from 'react-router-dom'
import { AssetDetail } from './pages/AssetDetail'
import { Dashboard } from './pages/Dashboard'
import { Landing } from './pages/Landing'
import { Login } from './pages/Login'
import { Register } from './pages/Register'
import { Plans } from './pages/Plans'
import { Scanner } from './pages/Scanner'
import { Scenarios } from './pages/Scenarios'

export function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <NavLink to="/" className="brand">
          Trend<span>Cipher</span>
        </NavLink>
        <nav className="app-nav">
          <NavLink to="/">Home</NavLink>
          <NavLink to="/plans">Pricing</NavLink>
          <NavLink to="/dashboard">App</NavLink>
          <NavLink to="/scanner">Scanner</NavLink>
          <NavLink to="/scenarios">Scenarios</NavLink>
          <NavLink to="/login">Sign in</NavLink>
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
        </Routes>
      </main>
    </div>
  )
}