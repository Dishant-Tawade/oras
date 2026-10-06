import React, { useState } from 'react'
import { api } from '../hooks/useApi'
import { OrasMark } from '../components/Header'

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [teamKey, setTeamKey]   = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const [showAdmin, setShowAdmin] = useState(false)
  const [adminUser, setAdminUser] = useState('')
  const [adminPass, setAdminPass] = useState('')
  const [adminError, setAdminError] = useState('')
  const [adminLoading, setAdminLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault(); setError(''); setLoading(true)
    try {
      const res = await api.login(username, password, teamKey)
      if (res.status === 'ok') onLogin(res)
      else setError(res.error || 'Login failed')
    } catch { setError('Connection error — please try again') }
    finally { setLoading(false) }
  }

  const handleAdminLogin = async (e) => {
    e.preventDefault(); setAdminError(''); setAdminLoading(true)
    try {
      const res = await api.login(adminUser, adminPass, '')
      if (res.status === 'ok' && res.is_admin) onLogin(res)
      else setAdminError(res.error || 'Invalid admin credentials')
    } catch { setAdminError('Connection error') }
    finally { setAdminLoading(false) }
  }

  const inp = { width: '100%', padding: '11px 14px', borderRadius: 4, fontSize: 13, outline: 'none' }
  const lbl = { fontSize: 10, fontWeight: 700, letterSpacing: '0.12em', textTransform: 'uppercase', color: '#6A7A8A', display: 'block', marginBottom: 5, fontFamily: "'DM Mono',monospace" }

  return (
    <div style={{ minHeight: '100vh', background: '#F0F2F5', display: 'flex', position: 'relative', zIndex: 2 }}>
      {/* Left panel — decorative navy */}
      <div className="login-left-panel" style={{ width: '42%', minWidth: 320, background: 'linear-gradient(160deg, #0D1F3C 0%, #1A3356 60%, #0D2845 100%)', display: 'flex', flexDirection: 'column', padding: '48px', position: 'relative', overflow: 'hidden' }}>
        {/* Subtle grid on left panel */}
        <div style={{ position: 'absolute', inset: 0, backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.04) 1px, transparent 1px)', backgroundSize: '28px 28px', pointerEvents: 'none' }} />
        {/* Gold accent line */}
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: 'linear-gradient(90deg, #B8932A, #D4AA40, #B8932A)' }} />

        {/* Logo */}
        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
            <OrasMark size={24} />
            <div style={{ width: 1, height: 28, background: 'rgba(255,255,255,0.15)', margin: '0 4px' }} />
            <div style={{ fontSize: 26, fontWeight: 900, letterSpacing: '0.22em', color: '#ffffff' }}>ORAS</div>
          </div>
          <div style={{ fontSize: 9, color: 'rgba(255,255,255,0.50)', letterSpacing: '0.18em', fontFamily: "'DM Mono',monospace", textTransform: 'uppercase', marginLeft: 3 }}>Resource Allocation Simulator</div>
        </div>

        {/* Mid content */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', position: 'relative', zIndex: 1 }}>
          <div style={{ width: 40, height: 3, background: '#B8932A', marginBottom: 28, borderRadius: 2 }} />
          <h2 style={{ fontSize: 32, fontWeight: 800, color: '#ffffff', lineHeight: 1.25, marginBottom: 16 }}>
            Strategic<br/>Business<br/>Simulation
          </h2>
          <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.60)', lineHeight: 1.8, maxWidth: 280 }}>
            Allocate capital across departments, navigate market dynamics, and maximise your Value Performance Index over a 5-year horizon.
          </p>

          {/* Feature list */}
          <div style={{ marginTop: 36, display: 'flex', flexDirection: 'column', gap: 12 }}>
            {['5-Year simulation horizon', 'Real-time competitive analysis', 'Multi-team competition mode', 'Monte Carlo risk scoring'].map((f, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 6, height: 6, background: '#B8932A', borderRadius: '50%', flexShrink: 0 }} />
                <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.72)', letterSpacing: '0.02em' }}>{f}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Auxi bottom */}
        <div style={{ position: 'relative', zIndex: 1, display: 'flex', alignItems: 'center', gap: 8, opacity: 0.75 }}>
          <img src="/auxi-logo.png" alt="Auxi Studios" style={{ height: 18, filter: 'invert(1) brightness(1.2)' }} />
          <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.85)', letterSpacing: '0.18em', fontFamily: "'DM Mono',monospace", textTransform: 'uppercase' }}>Auxi Studios</span>
        </div>
      </div>

      {/* Right panel — login form */}
      <div className="login-right-panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '48px 56px', background: '#FFFFFF' }}>
        <div style={{ width: '100%', maxWidth: 380 }}>
          <div style={{ marginBottom: 36 }}>
            <h1 style={{ fontSize: 28, fontWeight: 900, color: '#0A1628', marginBottom: 8, letterSpacing: '-0.01em' }}>Sign in</h1>
            <p style={{ fontSize: 14, color: '#4A5A6A' }}>Enter your credentials to access ORAS</p>
          </div>

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <label style={lbl}>Username</label>
              <input style={inp} type="text" value={username} onChange={e => setUsername(e.target.value)} placeholder="your_name" autoFocus autoComplete="off" />
            </div>
            <div>
              <label style={lbl}>Password</label>
              <input style={inp} type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" />
            </div>
            <div>
              <label style={lbl}>Team Key</label>
              <input style={inp} type="text" value={teamKey} onChange={e => setTeamKey(e.target.value)} placeholder="TEAM-XXX" autoComplete="off" />
            </div>

            {error && (
              <div style={{ background: '#FAEBEB', border: '1px solid #E0B0B0', borderRadius: 4, padding: '10px 14px', fontSize: 13, color: '#8A2020', fontWeight: 600 }}>
                {error}
              </div>
            )}

            <button
              type="submit"
              className="btn btn-p"
              disabled={loading || !username || !password || !teamKey}
              style={{ width: '100%', padding: '14px', fontSize: 14, marginTop: 4, borderRadius: 10 }}
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          {/* Admin toggle */}
          <div style={{ marginTop: 24 }}>
            <button
              onClick={() => setShowAdmin(v => !v)}
              style={{ background: 'none', border: 'none', fontSize: 12, color: '#B0BACA', cursor: 'pointer', fontFamily: "'DM Sans',sans-serif", letterSpacing: '0.04em', width: '100%', textAlign: 'center', padding: '6px 0' }}
            >
              Admin access
            </button>
            <div className={`admin-panel-wrap${showAdmin ? ' open' : ''}`}>
              <div style={{ background: '#F0F2F5', border: '1px solid #D4DCE8', borderRadius: 4, padding: '16px 18px', marginTop: 8, display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div style={{ fontSize: 9, fontWeight: 700, color: '#6A7A8A', textTransform: 'uppercase', letterSpacing: '0.16em', fontFamily: "'DM Mono',monospace" }}>Admin Access</div>
                <form onSubmit={handleAdminLogin} style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
                  <input style={{ ...inp, fontSize: 12 }} type="text" value={adminUser} onChange={e => setAdminUser(e.target.value)} placeholder="Admin username" />
                  <input style={{ ...inp, fontSize: 12 }} type="password" value={adminPass} onChange={e => setAdminPass(e.target.value)} placeholder="Admin password" />
                  {adminError && <div style={{ fontSize: 12, color: '#8A2020', fontWeight: 600 }}>{adminError}</div>}
                  <button type="submit" className="btn btn-w btn-sm" disabled={adminLoading || !adminUser || !adminPass} style={{ fontSize: 13, padding: '9px', fontWeight: 700, width: '100%' }}>
                    {adminLoading ? 'Signing in...' : 'Sign In as Admin'}
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
