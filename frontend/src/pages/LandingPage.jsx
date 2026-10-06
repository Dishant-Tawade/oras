import React from 'react'
import { useAuth } from '../App'
import { OrasMark, AuxiLogo } from '../components/Header'

export default function LandingPage({ onStart, onResume, gameActive, scenario, briefingRead }) {
  const { auth, logout } = useAuth()

  const budget = scenario?.total_budget
  const budgetLabel = budget ? `${scenario.currency_symbol || '$'}${Math.round(budget / 1e6)}${scenario.large_number_suffix || 'M'} Budget` : '$60M Budget'

  return (
    <div style={{ minHeight: '100vh', background: '#F0F2F5', display: 'flex', flexDirection: 'column', position: 'relative', zIndex: 2 }}>
      {/* Gold top strip */}
      <div style={{ height: 3, background: 'linear-gradient(90deg, transparent, #B8932A 30%, #D4AA40 50%, #B8932A 70%, transparent)', flexShrink: 0 }} />

      {/* Header */}
      <div className="landing-header" style={{ background: '#0A1628', padding: '0 40px', height: 60, display: 'flex', alignItems: 'center', justifyContent: 'space-between', boxShadow: '0 2px 16px rgba(10,22,40,0.20)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <OrasMark size={18} />
          <div style={{ width: 1, height: 22, background: 'rgba(255,255,255,0.18)', margin: '0 4px' }} />
          <div style={{ fontSize: 15, fontWeight: 900, letterSpacing: '0.22em', color: 'rgba(255,255,255,0.95)' }}>ORAS</div>
          <div className="landing-header-subtitle" style={{ fontSize: 9, color: '#6A7A8A', letterSpacing: '0.12em', fontFamily: "'DM Mono',monospace", textTransform: 'uppercase', marginLeft: 4 }}>Resource Allocation Simulator</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ fontSize: 12, color: '#6A7A8A', fontFamily: "'DM Mono',monospace" }}>
            {auth?.is_controller ? 'Controller' : 'Viewer'} · <strong style={{ color: '#3A4A5A' }}>{auth?.team_key}</strong> · {auth?.username}
          </span>
          <button className="btn btn-sm" onClick={logout} style={{ background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.25)', color: 'rgba(255,255,255,0.80)', borderRadius: 3, padding: '5px 12px', fontSize: 11, fontWeight: 700, cursor: 'pointer', fontFamily: "'DM Sans',sans-serif" }}>Log Out</button>
          <AuxiLogo />
        </div>
      </div>

      {/* Main content */}
      <div className="landing-content" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '60px 40px' }}>
        <div style={{ maxWidth: 760, width: '100%', textAlign: 'center' }}>

          {/* ORAS mark + wordmark */}
          <div className="anim-fade-up" style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16, marginBottom: 10 }}>
              <OrasMark size={40} />
              <div className="landing-wordmark" style={{ fontSize: 80, fontWeight: 900, letterSpacing: '0.12em', color: '#0A1628', lineHeight: 1 }}>ORAS</div>
            </div>
            {/* Gold underline */}
            <div style={{ height: 3, width: 80, background: '#B8932A', margin: '8px auto 0', borderRadius: 2 }} />
          </div>

          <p className="anim-fade-up anim-d1" style={{ fontSize: 13, letterSpacing: '0.20em', color: '#6A7A8A', textTransform: 'uppercase', fontFamily: "'DM Mono',monospace", marginBottom: 40 }}>
            Resource Allocation Simulator
          </p>

          {/* Scenario info pills */}
          {!gameActive && scenario && (
            <div className="anim-fade-up anim-d2" style={{ display: 'flex', gap: 8, justifyContent: 'center', flexWrap: 'wrap', marginBottom: 44 }}>
              {[
                { label: `${scenario.financials?.num_periods || 5}-Year Simulation` },
                { label: `${scenario.departments?.length || 4} Departments` },
                { label: budgetLabel },
                { label: scenario.company_name || 'Business Simulation' },
              ].map((p, i) => (
                <span key={i} style={{ padding: '6px 16px', background: '#F5F7FA', border: '1px solid #D4DCE8', borderRadius: 100, fontSize: 12, color: '#3A4A5A', fontFamily: "'DM Mono',monospace", fontWeight: 600, boxShadow: '0 1px 4px rgba(13,31,60,0.06)' }}>
                  {p.label}
                </span>
              ))}
            </div>
          )}

          {/* Welcome text */}
          {!gameActive && (
            <p className="anim-fade-up anim-d2" style={{ fontSize: 17, color: '#3A4A5A', lineHeight: 1.75, maxWidth: 560, margin: '0 auto 44px', fontWeight: 400 }}>
              Welcome. You're about to step into a strategic business simulation. We'll walk you through everything before it begins.
            </p>
          )}

          {/* CTA */}
          {gameActive ? (
            <div className="anim-fade-up anim-d3" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14 }}>
              <p style={{ fontSize: 15, color: '#3A4A5A', marginBottom: 8 }}>Your simulation is in progress. Jump back in or review the briefing.</p>
              <button
                onClick={onResume}
                style={{ padding: '18px 64px', background: '#0A1628', color: 'white', border: '1px solid rgba(13,31,60,0.15)', borderRadius: 100, fontSize: 17, fontWeight: 800, letterSpacing: '0.08em', cursor: 'pointer', fontFamily: "'DM Sans',sans-serif", boxShadow: '0 4px 20px rgba(13,31,60,0.22)', transition: 'transform 0.18s, box-shadow 0.18s' }}
                onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 10px 30px rgba(13,31,60,0.32)' }}
                onMouseLeave={e => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = '0 4px 20px rgba(13,31,60,0.22)' }}
              >
                Resume Simulation
              </button>
              <button onClick={briefingRead ? undefined : onStart} disabled={briefingRead} className="btn btn-g btn-sm" style={{ opacity: briefingRead ? 0.45 : 1 }}>
                {briefingRead ? 'Re-read Briefing (already read)' : 'Re-read Briefing'}
              </button>
            </div>
          ) : (
            <div className="anim-fade-up anim-d3">
              <button
                onClick={onStart}
                style={{ padding: '18px 64px', background: '#0A1628', color: 'white', border: '1px solid rgba(13,31,60,0.15)', borderRadius: 100, fontSize: 17, fontWeight: 800, letterSpacing: '0.08em', cursor: 'pointer', fontFamily: "'DM Sans',sans-serif", boxShadow: '0 4px 20px rgba(13,31,60,0.22)', transition: 'transform 0.18s, box-shadow 0.18s' }}
                onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 10px 30px rgba(13,31,60,0.32)' }}
                onMouseLeave={e => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = '0 4px 20px rgba(13,31,60,0.22)' }}
              >
                Start Simulation
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Bottom status bar */}
      <div className="landing-bottom-bar" style={{ background: '#F5F7FA', borderTop: '1px solid rgba(255,255,255,0.08)', padding: '12px 40px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div className="pdot" style={{ width: 6, height: 6 }} />
          <span style={{ fontSize: 11, color: '#6A7A8A', fontFamily: "'DM Mono',monospace" }}>
            {auth?.is_controller ? 'Controller' : 'Viewer'} · Team {auth?.team_key} · {auth?.username}
          </span>
        </div>
        <span style={{ fontSize: 11, color: '#B0BACA', fontFamily: "'DM Mono',monospace" }}>ORAS · Auxi Studios</span>
      </div>
    </div>
  )
}
