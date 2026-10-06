import React, { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../App'
import { api, adminFetch } from '../hooks/useApi'
import { FolderOpen } from '@phosphor-icons/react'
import Header, { AuxiLogo } from '../components/Header'
import AdminEventFeed from '../components/AdminEventFeed'

const MONO = "'DM Mono', monospace"
const T = { t1: '#0A1628', t2: '#3A4A5A', t3: '#8090A4' }

function C2Card({ title, children }) {
  return (
    <div style={{ background: '#FFFFFF', border: '1px solid #D4DCE8', borderRadius: 4, boxShadow: '0 1px 6px rgba(10,22,40,0.06)', padding: '18px 20px', marginBottom: 12 }}>
      {title && <div className="sec-lbl">{title}</div>}
      {children}
    </div>
  )
}

export default function AdminPage() {
  const { logout } = useAuth()
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState('')
  const [msg, setMsg] = useState({ text: '', ok: true })
  const [scenarios, setScenarios] = useState([])
  const [activeScenario, setActiveScenario] = useState(null)
  const [selectedCountry, setSelectedCountry] = useState('')
  const [selectedIndustry, setSelectedIndustry] = useState('')
  const [newUser, setNewUser] = useState({ username: '', password: '', team_key: '' })
  const [addingUser, setAddingUser] = useState(false)
  const [bulkUploading, setBulkUploading] = useState(false)
  const [bulkMsg, setBulkMsg] = useState('')
  const bulkInputRef = React.useRef(null)

  const showMsg = (text, ok = true) => { setMsg({ text, ok }); setTimeout(() => setMsg({ text: '', ok: true }), 4000) }

  const refresh = useCallback(async () => {
    try { const data = await api.adminStatus(); setStatus(data) }
    catch (e) { console.error('Admin refresh failed:', e) }
    finally { setLoading(false) }
  }, [])

  const loadScenarios = useCallback(async () => {
    try {
      const [regRes, activeRes] = await Promise.all([
        adminFetch('/api/admin/scenarios').then(r => r.json()),
        adminFetch('/api/admin/active-scenario').then(r => r.json()),
      ])
      const list = regRes.scenarios || []
      setScenarios(list); setActiveScenario(activeRes)
      setSelectedCountry(activeRes.country || 'us'); setSelectedIndustry(activeRes.industry || 'ev')
    } catch (e) { console.error('Failed to load scenarios:', e) }
  }, [])

  useEffect(() => {
    refresh(); loadScenarios()
    const id = setInterval(refresh, 5000)
    return () => clearInterval(id)
  }, [refresh, loadScenarios])

  const handleBulkUpload = async (e) => {
    const file = e.target.files?.[0]; if (!file) return
    setBulkUploading(true); setBulkMsg('')
    try {
      const formData = new FormData(); formData.append('file', file)
      const res = await adminFetch('/api/admin/bulk-add-users', { method: 'POST', body: formData }).then(r => r.json())
      if (res.status === 'ok') { await refresh(); setBulkMsg(`Added ${res.added} user(s).${res.errors?.length ? ` ${res.errors.length} row(s) skipped.` : ''}`) }
      else setBulkMsg(res.error || 'Upload failed')
    } catch (err) { setBulkMsg(`Upload failed: ${err.message}`) }
    finally { setBulkUploading(false); if (bulkInputRef.current) bulkInputRef.current.value = '' }
  }

  const act = async (key, fn, confirm_msg) => {
    if (confirm_msg && !window.confirm(confirm_msg)) return
    setActionLoading(key)
    try { await fn(); await refresh(); showMsg('Done.') }
    catch (e) { showMsg(`Error: ${e.message}`, false) }
    finally { setActionLoading('') }
  }

  const handleApplyScenario = async () => {
    if (!selectedCountry || !selectedIndustry) { showMsg('Select a country and industry', false); return }
    setActionLoading('scenario')
    try {
      const res = await api.setScenario(selectedCountry, selectedIndustry)
      if (res.status === 'ok') { await api.setPhase('playing'); await loadScenarios(); await refresh(); showMsg(`Scenario set: ${selectedCountry.toUpperCase()} / ${selectedIndustry}`) }
      else showMsg(res.error || 'Failed to set scenario', false)
    } catch (e) { showMsg(`Error: ${e.message}`, false) }
    finally { setActionLoading('') }
  }

  const handleAddUser = async () => {
    if (!newUser.username || !newUser.password || !newUser.team_key) { showMsg('Fill in all fields', false); return }
    setAddingUser(true)
    try {
      const res = await adminFetch('/api/admin/add-user', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(newUser) }).then(r => r.json())
      if (res.status === 'ok') { setNewUser({ username: '', password: '', team_key: '' }); await refresh(); showMsg('User added.') }
      else showMsg(res.error || 'Failed to add user', false)
    } catch (e) { showMsg(`Error: ${e.message}`, false) }
    finally { setAddingUser(false) }
  }

  const handleDeleteUser = async (username, team_key) => {
    if (!window.confirm(`Delete user "${username}"?`)) return
    try {
      const res = await adminFetch('/api/admin/delete-user', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, team_key }) }).then(r => r.json())
      if (res.status === 'ok') { await refresh(); showMsg('User deleted.') } else showMsg(res.error || 'Failed', false)
    } catch (e) { showMsg(`Error: ${e.message}`, false) }
  }

  const handleKickUser = async (username, team_key) => {
    try {
      const res = await adminFetch('/api/admin/kick-user', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, team_key }) }).then(r => r.json())
      if (res.status === 'ok') {
        showMsg(`${username} has been kicked.`)
        // Immediately mark this user offline locally — don't wait for backend poll
        setStatus(prev => prev ? {
          ...prev,
          sessions: (prev.sessions || []).map(s =>
            s.username === username && s.team_key === team_key ? { ...s, active: false } : s
          )
        } : prev)
        await new Promise(r => setTimeout(r, 800))
        await refresh()
      } else showMsg(res.error || 'Failed', false)
    } catch (e) { showMsg(`Error: ${e.message}`, false) }
  }

  const handleKickAll = async () => {
    try {
      const res = await adminFetch('/api/admin/kick-all-users', { method: 'POST', headers: { 'Content-Type': 'application/json' } }).then(r => r.json())
      if (res.status === 'ok') {
        showMsg(`Kicked ${res.kicked} user(s).`)
        setStatus(prev => prev ? {
          ...prev,
          sessions: (prev.sessions || []).map(s => ({ ...s, active: false }))
        } : prev)
        await new Promise(r => setTimeout(r, 800))
        await refresh()
      } else showMsg(res.error || 'Failed', false)
    } catch (e) { showMsg(`Error: ${e.message}`, false) }
  }

  const handleMassDelete = async () => {
    if (!window.confirm('Delete ALL non-admin users? This cannot be undone.')) return
    try {
      const res = await adminFetch('/api/admin/mass-delete-users', { method: 'POST', headers: { 'Content-Type': 'application/json' } }).then(r => r.json())
      if (res.status === 'ok') { await refresh(); showMsg(`Deleted ${res.deleted} user(s).`) } else showMsg(res.error || 'Failed', false)
    } catch (e) { showMsg(`Error: ${e.message}`, false) }
  }

  const handleResetTeam = async (team_key) => {
    if (!window.confirm(`Reset game state for team "${team_key}"?`)) return
    try {
      const res = await adminFetch('/api/admin/reset-team', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ team_key }) }).then(r => r.json())
      if (res.status === 'ok') { await refresh(); showMsg(`Reset ${team_key}.`) } else showMsg(res.error || 'Failed', false)
    } catch (e) { showMsg(`Error: ${e.message}`, false) }
  }

  const countries = [...new Map(scenarios.map(s => [s.country, { code: s.country, name: s.country_name || s.country.toUpperCase() }])).values()]
  const industries = [...new Map(scenarios.filter(s => s.country === selectedCountry).map(s => [s.industry, { code: s.industry, name: s.label?.split('—')[1]?.trim() || s.industry }])).values()]

  if (loading) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', zIndex: 2 }}>
      <p style={{ color: '#6A7A8A', fontFamily: MONO, fontSize: 12 }}>Loading admin dashboard...</p>
    </div>
  )

  const isPaused = status?.paused || false
  const allTeams = status?.teams || []
  const pending = status?.pending_teams || []
  const completed = status?.completed_teams || []
  const sessions = (status?.sessions || []).filter(s => s.team_key !== '__admin__')
  const distinctTeamCount = new Set(allTeams.map(u => u.team_key)).size
  const onlineCount = sessions.filter(s => s.active).length

  const headerRight = (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <button className="btn btn-g btn-sm" onClick={async () => { await refresh(); await loadScenarios() }}>
        <svg width="11" height="11" viewBox="0 0 16 16" fill="none"><path d="M13.5 8A5.5 5.5 0 112.5 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/><path d="M13.5 4v4h-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>
        Refresh
      </button>
      <button className="btn btn-d btn-sm" onClick={logout}>Logout</button>
      <AuxiLogo />
    </div>
  )

  return (
    <div style={{ minHeight: '100vh', background: '#F0F2F5', display: 'flex', flexDirection: 'column', fontFamily: "'DM Sans',sans-serif", position: 'relative', zIndex: 2 }}>
      <Header
        left={
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <svg width="18" height="18" viewBox="0 0 32 32" fill="none"><path d="M16 3L29 16L16 29L3 16Z" stroke="rgba(91,191,116,0.65)" strokeWidth="1.5" fill="none"/><circle cx="16" cy="16" r="2.5" fill="rgba(91,191,116,0.8)"/></svg>
            <div>
              <div style={{ fontSize: 18, fontWeight: 900, letterSpacing: '0.22em', color: '#0A1628' }}>ORAS</div>
              <div style={{ fontSize: 9, color: '#6A7A8A', letterSpacing: '0.14em', fontFamily: MONO, textTransform: 'uppercase', marginTop: 1 }}>Admin Dashboard</div>
            </div>
          </div>
        }
        right={headerRight}
      />

      {/* Status strip */}
      <div style={{ background: '#F0F2F5', borderBottom: '1px solid #D4DCE8', padding: '0 28px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 52, flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {[
            { label: 'Teams', val: distinctTeamCount },
            { label: 'Players', val: allTeams.length },
            { label: 'Online', val: onlineCount },
            { label: 'Complete', val: completed.length },
          ].map(({ label, val }) => (
            <div key={label} style={{ background: '#F0F2F5', border: '1px solid #E0E6EF', borderRadius: 4, padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 10, color: '#6A7A8A', fontFamily: MONO, textTransform: 'uppercase', letterSpacing: '0.08em' }}>{label}</span>
              <span style={{ fontSize: 12, fontWeight: 700, color: '#0A1628', fontFamily: MONO }}>{val}</span>
            </div>
          ))}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginLeft: 4 }}>
            <div style={{ width: 7, height: 7, borderRadius: '50%', background: isPaused ? '#B03030' : '#1A5C3A', animation: isPaused ? 'none' : 'orasPulse 2.2s ease infinite' }} />
            <span style={{ fontSize: 10, fontWeight: 700, color: isPaused ? '#B03030' : '#1A5C3A', fontFamily: MONO, letterSpacing: '0.08em' }}>{isPaused ? 'PAUSED' : 'ACTIVE'}</span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <button className="btn btn-w btn-sm" onClick={() => act('pause', () => api.pause(!isPaused))} disabled={actionLoading === 'pause'}>
            {isPaused ? 'Resume' : 'Pause'}
          </button>
          <button className="btn btn-d btn-sm" onClick={() => {
            if (onlineCount > 0) { showMsg(`Cannot reset: ${onlineCount} player(s) currently logged in.`, false); return }
            act('reset', async () => {
              await api.resetGame()
              await api.setPhase('playing')
              // Optimistically mark all sessions offline
              setStatus(prev => prev ? {
                ...prev,
                sessions: (prev.sessions || []).map(s => ({ ...s, active: false }))
              } : prev)
              await new Promise(r => setTimeout(r, 800))
              await refresh()
            }, 'Reset all game state for all teams? Players will be kicked and returned to Year 1. This cannot be undone.')
          }} disabled={actionLoading === 'reset'}>Reset All</button>
          <button className="btn btn-d btn-sm" onClick={handleMassDelete} disabled={actionLoading === 'mass-delete'}>Delete All Users</button>
          <button className="btn btn-w btn-sm" onClick={handleKickAll}>Kick All</button>
        </div>
      </div>

      {/* Toast */}
      {msg.text && (
        <div style={{ position: 'fixed', bottom: 24, left: '50%', transform: 'translateX(-50%)', background: msg.ok ? '#1A5C3A' : '#B03030', color: 'white', padding: '12px 28px', borderRadius: 4, fontSize: 13, fontWeight: 600, zIndex: 1000, backdropFilter: 'blur(12px)', WebkitBackdropFilter: 'blur(12px)' }}>
          {msg.text}
        </div>
      )}

      {/* Content */}
      <div style={{ padding: '18px 28px', maxWidth: 1100, margin: '0 auto', width: '100%' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>

          {/* LEFT */}
          <div>
            {/* Stats + Year dist */}
            <C2Card title="Status">
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 8, marginBottom: 14 }}>
                {[
                  { label: 'Teams', val: distinctTeamCount, col: '#1A5C3A' },
                  { label: 'Players', val: allTeams.length, col: '#1A5C3A' },
                  { label: 'Online', val: onlineCount, col: '#1A3A6B' },
                  { label: 'Completed', val: completed.length, col: '#8A6A10' },
                ].map(({ label, val, col }) => (
                  <div key={label} style={{ padding: '10px 12px', background: '#F0F2F5', border: '1px solid #E0E6EF', borderRadius: 4, textAlign: 'center' }}>
                    <div style={{ fontSize: 9, color: '#6A7A8A', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 4, fontFamily: MONO }}>{label}</div>
                    <div style={{ fontSize: 20, fontWeight: 700, color: col, fontFamily: MONO }}>{val}</div>
                  </div>
                ))}
              </div>
              {distinctTeamCount > 0 && (() => {
                const total = distinctTeamCount
                const dist = {}
                pending.forEach(p => { const y = p.years_locked ?? 0; dist[y] = (dist[y] || 0) + 1 })
                completed.forEach(() => { dist[5] = (dist[5] || 0) + 1 })
                return (
                  <div>
                    <div className="sec-lbl">Teams by Year</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                      {[1,2,3,4,5].map(y => {
                        const count = dist[y] || 0; if (count === 0) return null
                        const pct = (count / total) * 100
                        return (
                          <div key={y} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ fontSize: 10, fontWeight: 700, color: '#6A7A8A', fontFamily: MONO, width: 48, flexShrink: 0 }}>{y === 0 ? 'None' : y === 5 ? 'Done' : `${y} done`}</span>
                            <div style={{ flex: 1, height: 4, background: '#FFFFFF', borderRadius: 2, overflow: 'hidden' }}>
                              <div style={{ height: '100%', width: `${pct}%`, background: y === 5 ? '#B8932A' : '#1A3A6B', borderRadius: 2, transition: 'width .4s ease' }} />
                            </div>
                            <span style={{ fontSize: 10, fontWeight: 700, color: '#3A4A5A', fontFamily: MONO, width: 36, textAlign: 'right', flexShrink: 0 }}>{count}/{total}</span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )
              })()}
            </C2Card>

            {/* Scenario */}
            <C2Card title="Scenario">
              {activeScenario && (
                <div style={{ marginBottom: 12, padding: '7px 11px', background: 'rgba(26,107,69,0.06)', borderRadius: 4, border: '1px solid rgba(61,153,88,0.20)', fontSize: 12 }}>
                  <span style={{ color: '#6A7A8A', fontWeight: 600, fontFamily: MONO }}>Active: </span>
                  <span style={{ color: '#1A3A6B', fontWeight: 700 }}>{activeScenario.label || `${activeScenario.country?.toUpperCase()} / ${activeScenario.industry}`}</span>
                </div>
              )}
              <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: 12 }}>
                <div style={{ flex: 1, minWidth: 110 }}>
                  <div style={{ fontSize: 10, color: '#6A7A8A', marginBottom: 4, fontWeight: 600, fontFamily: MONO, textTransform: 'uppercase', letterSpacing: '0.1em' }}>Country</div>
                  <select value={selectedCountry} onChange={e => { setSelectedCountry(e.target.value); setSelectedIndustry('') }} style={{ width: '100%', padding: '8px 10px', borderRadius: 4, fontSize: 12 }}>
                    <option value="">— Select —</option>
                    {countries.map(c => <option key={c.code} value={c.code}>{c.name}</option>)}
                  </select>
                </div>
                <div style={{ flex: 1, minWidth: 110 }}>
                  <div style={{ fontSize: 10, color: '#6A7A8A', marginBottom: 4, fontWeight: 600, fontFamily: MONO, textTransform: 'uppercase', letterSpacing: '0.1em' }}>Industry</div>
                  <select value={selectedIndustry} onChange={e => setSelectedIndustry(e.target.value)} disabled={!selectedCountry} style={{ width: '100%', padding: '8px 10px', borderRadius: 4, fontSize: 12, opacity: !selectedCountry ? 0.4 : 1 }}>
                    <option value="">— Select —</option>
                    {industries.map(i => <option key={i.code} value={i.code}>{i.name || i.code}</option>)}
                  </select>
                </div>
                <button className="btn btn-p btn-sm" onClick={handleApplyScenario} disabled={actionLoading === 'scenario' || !selectedCountry || !selectedIndustry} style={{ padding: '9px 14px' }}>
                  {actionLoading === 'scenario' ? 'Applying...' : 'Apply'}
                </button>
              </div>
              {scenarios.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                  {scenarios.map(s => {
                    const isActive = activeScenario && s.country === activeScenario.country && s.industry === activeScenario.industry
                    return (
                      <button key={s.scenario_id} onClick={() => { setSelectedCountry(s.country); setSelectedIndustry(s.industry) }} style={{ padding: '3px 9px', fontSize: 10, borderRadius: 5, border: `1px solid ${isActive ? 'rgba(61,153,88,0.40)' : '#D4DCE8'}`, background: isActive ? 'rgba(212,170,64,0.18)' : 'rgba(15,40,75,0.50)', color: isActive ? '#D4AA40' : 'rgba(255,255,255,0.55)', cursor: 'pointer', fontFamily: MONO, fontWeight: isActive ? 700 : 400 }}>
                        {s.country.toUpperCase()} · {s.industry}
                      </button>
                    )
                  })}
                </div>
              )}
            </C2Card>

            {/* Leaderboard */}
            {(status?.leaderboard || []).length > 0 && (
              <C2Card title="Leaderboard">
                {status.leaderboard.map((e, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ width: 22, height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: 5, fontSize: 11, fontWeight: 700, fontFamily: MONO, background: i === 0 ? 'rgba(91,191,116,0.20)' : '#E0E6EF', border: `1px solid ${i === 0 ? 'rgba(91,191,116,0.30)' : '#D4DCE8'}`, color: i === 0 ? '#1A5C3A' : T.t3 }}>{i + 1}</span>
                      <span style={{ fontSize: 13, fontWeight: 600, color: '#0A1628' }}>{e.team_key || e.team}</span>
                      {e.year != null && <span style={{ fontSize: 10, color: '#6A7A8A', fontFamily: MONO }}>Yr {e.year}</span>}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      {e.grade && <span className="tag tag-g" style={{ fontSize: 9 }}>{e.grade}</span>}
                      <span style={{ fontFamily: MONO, fontWeight: 700, color: '#1A5C3A', fontSize: 13 }}>{(e.vpi ?? e.score)?.toFixed(0) || '—'}</span>
                    </div>
                  </div>
                ))}
                <div style={{ fontSize: 10, color: '#6A7A8A', marginTop: 8, paddingTop: 8, borderTop: '1px solid #E8ECF2', fontFamily: MONO }}>Scores computed via Monte Carlo across all locked years</div>
              </C2Card>
            )}
          </div>

          {/* RIGHT */}
          <div>
            {/* Add User */}
            <C2Card title="Add User">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 10 }}>
                {[
                  { key: 'username', placeholder: 'Username', type: 'text' },
                  { key: 'password', placeholder: 'Password', type: 'password' },
                  { key: 'team_key', placeholder: 'Team key (e.g. team_blue)', type: 'text' },
                ].map(f => (
                  <input key={f.key} type={f.type} value={newUser[f.key]} onChange={e => setNewUser(u => ({ ...u, [f.key]: e.target.value }))} placeholder={f.placeholder} style={{ padding: '8px 12px', borderRadius: 4, fontSize: 13, width: '100%', boxSizing: 'border-box' }} />
                ))}
              </div>
              <button className="btn btn-p btn-sm" onClick={handleAddUser} disabled={addingUser} style={{ padding: '9px 18px', fontSize: 13 }}>
                {addingUser ? 'Adding...' : '+ Add User'}
              </button>
            </C2Card>

            {/* Bulk Upload */}
            <C2Card title="Bulk Add Users">
              <div style={{ fontSize: 12, color: '#3A4A5A', marginBottom: 10, lineHeight: 1.6 }}>
                Upload a <strong style={{ color: '#0A1628' }}>.xlsx</strong> file with columns: <code style={{ background: '#FFFFFF', padding: '1px 5px', borderRadius: 3, fontSize: 11, fontFamily: MONO }}>Username</code>, <code style={{ background: '#FFFFFF', padding: '1px 5px', borderRadius: 3, fontSize: 11, fontFamily: MONO }}>Password</code>, <code style={{ background: '#FFFFFF', padding: '1px 5px', borderRadius: 3, fontSize: 11, fontFamily: MONO }}>Team Key</code>.
              </div>
              <div
                onClick={() => bulkInputRef.current?.click()}
                style={{ border: '2px dashed #C0CCE0', borderRadius: 4, padding: '18px', textAlign: 'center', cursor: 'pointer', background: '#F0F2F5', marginBottom: 10, transition: 'border-color .2s' }}
                onMouseEnter={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.35)'}
                onMouseLeave={e => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.18)'}
              >
                <div style={{ marginBottom: 6, display: 'flex', justifyContent: 'center' }}>
                  <FolderOpen size={22} weight="duotone" color="rgba(255,255,255,0.28)" />
                </div>
                <div style={{ fontSize: 12, color: '#6A7A8A' }}>{bulkUploading ? 'Processing...' : 'Click to browse or drop an .xlsx file'}</div>
              </div>
              <input ref={bulkInputRef} type="file" accept=".xlsx" onChange={handleBulkUpload} style={{ display: 'none' }} />
              {bulkMsg && (
                <div style={{ fontSize: 12, padding: '8px 12px', borderRadius: 4, marginTop: 4, background: bulkMsg.includes('error') || bulkMsg.includes('failed') ? 'rgba(220,80,80,0.10)' : 'rgba(26,180,90,0.10)', color: bulkMsg.includes('error') || bulkMsg.includes('failed') ? '#E89090' : '#4DD890', fontWeight: 600 }}>
                  {bulkMsg}
                </div>
              )}
            </C2Card>

            {/* Teams & Users */}
            <C2Card title="Teams & Users">
              {allTeams.length === 0 && <div style={{ fontSize: 12, color: '#6A7A8A' }}>No users registered yet.</div>}
              {Object.entries(
                allTeams.reduce((acc, u) => { const tk = u.team_key || 'unknown'; if (!acc[tk]) acc[tk] = []; acc[tk].push(u); return acc }, {})
              ).map(([teamKey, members]) => {
                const progress = pending.find(p => p.team_key === teamKey)
                const yearsLocked = Math.min(progress?.years_locked ?? (completed.includes(teamKey) ? 5 : 0), 5)
                const isComplete = completed.includes(teamKey)
                const activeSess = sessions.filter(s => s.team_key === teamKey && s.active)
                return (
                  <div key={teamKey} style={{ marginBottom: 10, padding: '12px 14px', background: '#FFFFFF', border: '1px solid #D4DCE8', borderRadius: 4, boxShadow: '0 1px 4px rgba(10,22,40,0.05)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                        <span style={{ fontSize: 13, fontWeight: 700, color: '#1A5C3A' }}>{teamKey}</span>
                        {isComplete && <span className="tag tag-g" style={{ fontSize: 9 }}>DONE</span>}
                        {activeSess.length > 0 && <span className="tag tag-b" style={{ fontSize: 9 }}>ONLINE {activeSess.length}</span>}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{ width: 72, height: 4, background: '#E0E6EF', borderRadius: 2, overflow: 'hidden' }}>
                          <div style={{ height: '100%', background: '#1A3A6B', borderRadius: 2, width: `${(yearsLocked / 5) * 100}%` }} />
                        </div>
                        <span style={{ fontSize: 10, color: '#6A7A8A', fontFamily: MONO }}>{yearsLocked}/5</span>
                        <button className="btn btn-w btn-sm" style={{ padding: '3px 8px', fontSize: 10 }} onClick={() => handleResetTeam(teamKey)}>Reset</button>
                      </div>
                    </div>
                    {members.map(u => {
                      const userSess = sessions.find(s => s.username === u.username && s.team_key === u.team_key)
                      const isOnline = userSess?.active === true
                      return (
                        <div key={u.username} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '5px 0', borderTop: '1px solid #E8ECF2' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <div style={{ width: 6, height: 6, borderRadius: '50%', flexShrink: 0, background: isOnline ? '#1A5C3A' : '#D4DCE8', animation: isOnline ? 'dotPulse 2.2s ease infinite' : 'none' }} />
                            <span style={{ fontSize: 12, color: '#3A4A5A' }}>{u.username}</span>
                            {isOnline && <span style={{ fontSize: 8, fontWeight: 700, color: '#1A5C3A', letterSpacing: '0.08em', fontFamily: MONO }}>ONLINE</span>}
                          </div>
                          <div style={{ display: 'flex', gap: 5 }}>
                            <button className="btn btn-w btn-sm" style={{ padding: '3px 8px', fontSize: 10, opacity: 1, cursor: 'pointer' }} onClick={() => handleKickUser(u.username, u.team_key)}>Kick</button>
                            <button className="btn btn-d btn-sm" style={{ padding: '3px 8px', fontSize: 10, opacity: isOnline ? 0.35 : 1, cursor: isOnline ? 'not-allowed' : 'pointer' }} onClick={() => !isOnline && handleDeleteUser(u.username, u.team_key)} disabled={isOnline}>Delete</button>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )
              })}
            </C2Card>
          </div>
        </div>
      </div>

      <AdminEventFeed />
    </div>
  )
}
