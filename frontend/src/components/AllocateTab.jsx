import React, { useState, useEffect, useMemo, useRef } from 'react'
import { api } from '../hooks/useApi'
import {
  getDept, fmtCur, inputDivisor,
  AllocationDonut, DonutLegend,
  StrategyOptions, ThrottledRange,
  HoldToSealButton, DeptInput,
  
  AllocateSharedStyles,
} from './allocate/shared'

// AllocateTab — clean, professional layout Layout hierarchy (top → bottom): 1.

function NewsCard({ item }) {
  const isPos = item.sentiment === 'positive'
  const isNeg = item.sentiment === 'negative'
  const dept = item.department || item.dept || ''
  const dc = getDept(dept)
  return (
    <div className={`news-card ${isPos ? 'news-positive' : isNeg ? 'news-negative' : 'news-neutral'}`}>
      {dept && <span style={{ fontSize: 9, fontWeight: 700, color: dc.colorL, textTransform: 'uppercase', letterSpacing: '0.10em', display: 'block', marginBottom: 3 }}>{dept}</span>}
      <span style={{ fontWeight: 600, color: isPos ? '#1A5C3A' : isNeg ? '#8A2020' : '#8090A4', marginRight: 4 }}>
        {isPos ? '▲' : isNeg ? '▼' : '●'}
      </span>
      <span style={{ color: '#3A4A5A' }}>{item.headline || item.title || String(item)}</span>
    </div>
  )
}


/* ── Modal helpers ──────────────────────────────────────────────────────── */
function ChecklistItem({ ok, label, optional }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, color: ok ? '#3A4A5A' : (optional ? '#8A6A10' : '#8A2020') }}>
      {ok ? (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
          <circle cx="12" cy="12" r="10" fill="#EAF4EE" stroke="#1A6B45" strokeWidth="1.5" />
          <path d="M8 12l3 3 5-6" stroke="#1A6B45" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      ) : (
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
          <circle cx="12" cy="12" r="10" fill={optional ? '#FBF5E6' : '#FAEBEB'} stroke={optional ? '#8A6A10' : '#8A2020'} strokeWidth="1.5" />
          <path d="M12 7v6" stroke={optional ? '#8A6A10' : '#8A2020'} strokeWidth="2" strokeLinecap="round" />
          <circle cx="12" cy="16.5" r="1" fill={optional ? '#8A6A10' : '#8A2020'} />
        </svg>
      )}
      <span>{label}</span>
    </div>
  )
}

function MiniDonut({ depts, budget, totalSpend }) {
  const SIZE = 88, R = 36, C = 2 * Math.PI * R, cx = SIZE / 2, cy = SIZE / 2
  const ringTotal = Math.max(budget, totalSpend) || 1
  let cursor = 0
  const arcs = depts.map(d => {
    const len = C * (d.value / ringTotal)
    const offset = -cursor; cursor += len
    return { ...d, len, offset }
  })
  return (
    <svg width={SIZE} height={SIZE}>
      <circle cx={cx} cy={cy} r={R} fill="none" stroke="#EEF1F6" strokeWidth="9" />
      <g transform={`rotate(-90 ${cx} ${cy})`}>
        {arcs.map(a => (
          <circle key={a.name} cx={cx} cy={cy} r={R} fill="none"
            stroke={a.color} strokeWidth="9"
            strokeDasharray={`${a.len} ${C - a.len}`} strokeDashoffset={a.offset} />
        ))}
      </g>
      <text x={cx} y={cy + 4} textAnchor="middle" style={{ fontFamily: "'DM Mono',monospace", fontSize: 11, fontWeight: 800, fill: '#0A1628' }}>
        {budget > 0 ? `${Math.round((totalSpend / budget) * 100)}%` : '—'}
      </text>
    </svg>
  )
}


export default function AllocateTab({ gameState, constraints, maxAllocatable, unallocatableBudget = 0, subDecisionOptions, isController, blocking, onLockYear, scenarioInfo, teamKey, username }) {
  const [sliderValues, setSliderValues] = useState({})
  const [subdecisions, setSubdecisions] = useState({})
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [locking, setLocking] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const draftTimer = useRef(null)
  useEffect(() => {
    if (!isController || !teamKey || Object.keys(sliderValues).length === 0) return
    if (draftTimer.current) clearTimeout(draftTimer.current)
    draftTimer.current = setTimeout(() => {
      const allocArray = constraints.map(c => sliderValues[c.dept_name] ?? c.default)
      api.saveDraft(teamKey, username || '', allocArray, subdecisions).catch(() => {})
    }, 500)
    return () => { if (draftTimer.current) clearTimeout(draftTimer.current) }
  }, [sliderValues, subdecisions, isController, teamKey, username, constraints])

  const sym    = scenarioInfo?.currency_symbol || '$'
  const suffix = scenarioInfo?.small_number_suffix || 'K'
  const div    = inputDivisor(suffix)
  const budget = gameState?.available_budget || 0
  const currentYear = gameState?.current_year || 1
  const completed = gameState?.completed || false
  const yearResults = gameState?.year_results || []
  const lockedSubdecisions = gameState?.locked_subdecisions || []

  const currentNews = useMemo(() => {
    const playerNews = (gameState?.player_news || []).filter(n => n.year === currentYear)
    if (playerNews.length > 0) return playerNews
    if (yearResults.length > 0) {
      const last = yearResults[yearResults.length - 1]
      return [...(last.dept_news || []).map(n => ({ ...n, department: n.dept })), ...(last.general_news || [])]
    }
    return []
  }, [gameState, currentYear, yearResults])

  // Hydrate slider values on mount / year change.
  useEffect(() => {
    if (constraints.length === 0) return
    const draft = gameState?.draft_allocations
    const hasValidDraft = Array.isArray(draft) && draft.length === constraints.length
    const vals = {}
    constraints.forEach((c, i) => {
      vals[c.dept_name] = hasValidDraft && typeof draft[i] === 'number' ? draft[i] : c.default
    })
    setSliderValues(vals)
    // We intentionally do NOT depend on gameState.draft_allocations so that user-typed values aren't
    // clobbered every time the WS pushes a fresh game state.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [constraints, currentYear])

  // Same pattern for sub-decisions: prefer the server-side draft for this year if present, else carry
  // forward last year's locked choices, else start empty.
  useEffect(() => {
    const draftSd = gameState?.draft_subdecisions
    if (draftSd && typeof draftSd === 'object' && Object.keys(draftSd).length > 0) {
      setSubdecisions({ ...draftSd })
      return
    }
    const prevSd = lockedSubdecisions
    if (prevSd && prevSd.length > 0) setSubdecisions({ ...prevSd[prevSd.length - 1] })
    else setSubdecisions({})
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentYear, subDecisionOptions])

  const totalSpend = useMemo(() => Object.values(sliderValues).reduce((s, v) => s + v, 0), [sliderValues])
  const remaining       = budget - totalSpend
  const overBudget      = remaining < 0
  // Structural gap: portion of budget unreachable due to ±30% dept caps.
  // Computed client-side from constraint maxima if not provided by server.
  const structuralGap   = unallocatableBudget > 0
    ? unallocatableBudget
    : (maxAllocatable != null ? Math.max(0, budget - maxAllocatable) : 0)
  // Allocatable remaining: budget the team could actually have spent but didn't
  const allocatableRemaining = Math.max(0, remaining - structuralGap)
  const cappedOut       = remaining > 0 && remaining <= structuralGap
  const unusedPct       = budget > 0 ? (allocatableRemaining / budget) * 100 : 0
  const penalty         = unusedPct > 15

  const depts = useMemo(() => constraints.map(c => {
    const dc = getDept(c.dept_name)
    return { name: c.dept_name, value: sliderValues[c.dept_name] ?? c.default, color: dc.color, colorL: dc.colorL }
  }), [constraints, sliderValues])

  const allStrategiesSet = constraints.every(c => subdecisions[c.dept_name])
  const canSeal = isController && !overBudget && allStrategiesSet && !(blocking?.length > 0) && !locking

  const handleSeal = async () => {
    if (!canSeal) return
    setLocking(true)
    const allocArray = constraints.map(c => sliderValues[c.dept_name] || c.default)
    try {
      await onLockYear(allocArray, subdecisions)
    } finally {
      setLocking(false)
      setConfirmOpen(false)
    }
  }

  if (completed) {
    // Post-completion view on the Allocate tab.
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '48px 0' }}>
        <div
          style={{
            background: '#FFFFFF',
            border: '1px solid #D4DCE8',
            borderLeft: '3px solid #B8932A',
            borderRadius: 4,
            boxShadow: '0 4px 16px rgba(10,22,40,0.18)',
            padding: '36px 48px',
            textAlign: 'center',
            maxWidth: 480,
          }}
        >
          <div style={{
            width: 44, height: 44, borderRadius: '50%',
            background: 'rgba(61,153,88,0.12)',
            border: '1px solid rgba(61,153,88,0.22)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 14px',
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M20 6L9 17L4 12" stroke="#1A6B45" strokeWidth="2.5"
                    strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <h2 style={{
            fontSize: 18, fontWeight: 700, color: '#0A1628', marginBottom: 8,
          }}>
            Simulation Complete
          </h2>
          <p style={{
            color: '#3A4A5A', fontSize: 13, lineHeight: 1.6, margin: 0,
          }}>
            All 5 years are locked. Switch to the <strong style={{ color: '#0A1628' }}>Performance</strong> tab for your results breakdown.
          </p>
        </div>
      </div>
    )
  }

  const numDepts = constraints.length
  const deptGridCols = numDepts <= 4 ? `repeat(${numDepts}, 1fr)` : 'repeat(4, 1fr)'

  return (
    <div style={{ display: 'flex', gap: 14 }}>
      <AllocateSharedStyles />

      {/* Sidebar */}
      {!sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(true)}
          style={{ position: 'absolute', zIndex: 10, background: '#FFFFFF', border: '1px solid #D4DCE8', borderRadius: 4, padding: '6px 10px', cursor: 'pointer', color: '#3A4A5A', fontSize: 11, fontFamily: "'DM Sans',sans-serif", display: 'flex', alignItems: 'center', gap: 5 }}
        >
          <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><rect x="2" y="3" width="5" height="10" rx="1" stroke="currentColor" strokeWidth="1.4" /><path d="M10 6l3 2-3 2" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" /></svg>
          News
        </button>
      )}

      {sidebarOpen && (
        <div style={{ width: 240, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div className="alloc-card" style={{ padding: '14px 16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <div className="alloc-section-label" style={{ marginBottom: 0 }}>Year {currentYear} News</div>
              <button onClick={() => setSidebarOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#6A7A8A', padding: 2, display: 'flex', alignItems: 'center' }} title="Collapse sidebar">
                <svg width="12" height="12" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /></svg>
              </button>
            </div>
            {currentNews.length === 0
              ? <div style={{ fontSize: 11, color: '#6A7A8A' }}>No news events this year.</div>
              : currentNews.map((item, i) => <NewsCard key={i} item={item} />)
            }
          </div>
          <div className="alloc-card" style={{ padding: '14px 16px' }}>
            <div className="alloc-section-label">Reference</div>
            {[
              'R&D returns appear year n+1',
              'Repeated strategies: synergy decays 30%/yr',
              'Over-funding Ops vs Sales wastes capacity',
              'Budget underuse >15% of allocatable budget triggers penalty',
            ].map((r, i) => (
              <div key={i} style={{ fontSize: 11, color: '#3A4A5A', lineHeight: 1.5, marginBottom: 6, paddingLeft: 8, borderLeft: '1px solid #D4DCE8' }}>{r}</div>
            ))}
          </div>
        </div>
      )}

      {/* Main panel */}
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 14 }}>

        {/* Header strip */}
        <div className="alloc-card alloc-card-emphasis" style={{ borderTop: '3px solid #B8932A', padding: '14px 20px' }}>
          <div>
            <div style={{ fontSize: 22, fontWeight: 800, color: '#0A1628', fontFamily: "'DM Mono',monospace", letterSpacing: '-0.5px', lineHeight: 1.1 }}>
              Year {currentYear}
              <span style={{ fontSize: 11, color: '#8090A4', fontWeight: 400, marginLeft: 10, letterSpacing: 0 }}>{5 - yearResults.length} years remaining</span>
            </div>
            <div style={{ fontSize: 13, color: '#6A7A8A', fontFamily: "'DM Mono',monospace", marginTop: 6 }}>
              Available budget <span style={{ color: '#0A1628', fontWeight: 700 }}>{fmtCur(budget, sym, suffix)}</span>
              {gameState?.fixed_costs > 0 && (
                <span style={{ fontSize: 11, color: '#6A7A8A', marginTop: 4, display: 'block' }}>
                  Fixed operating costs{' '}
                  <span style={{ color: '#8A6A10', fontWeight: 700 }}>{fmtCur(gameState.fixed_costs, sym, suffix)}</span>
                  {' '}— separate from your department budget, deducted from revenue automatically.
                </span>
              )}
            </div>
            {structuralGap > 0 && (
              <div style={{
                display: 'flex', flexDirection: 'column', gap: 6,
                marginTop: 10, padding: '10px 14px',
                background: '#FFF8EC', border: '1px solid #E8D6A0', borderRadius: 4,
              }}>
                {/* Top row: numbers at a glance */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
                    <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" stroke="#B8932A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    <line x1="12" y1="9" x2="12" y2="13" stroke="#B8932A" strokeWidth="2" strokeLinecap="round"/>
                    <line x1="12" y1="17" x2="12.01" y2="17" stroke="#B8932A" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                  <span style={{ fontSize: 14, fontWeight: 700, color: '#7A5A10', fontFamily: "'DM Mono',monospace" }}>
                    Max allocatable: <span style={{ color: '#0A1628', fontWeight: 800 }}>{fmtCur(budget - structuralGap, sym, suffix)}</span>
                    <span style={{ fontWeight: 400, color: '#8A6A10', marginLeft: 10 }}>({fmtCur(structuralGap, sym, suffix)} structurally unreachable · no penalty)</span>
                  </span>
                </div>
                {/* Disclaimer row */}
                <div style={{ fontSize: 12, color: '#7A5A10', lineHeight: 1.55, paddingLeft: 23 }}>
                  Each department's budget can only change by <strong>±30%</strong> from last year's allocation.
                  Given your previous year's spend mix, the combined ceilings add up to less than this year's total budget —
                  meaning some budget is impossible to allocate. You will <strong>not</strong> be penalised for this unspendable portion.
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Allocation overview — donut + legend */}
        <div className="alloc-card alloc-card-emphasis" style={{ padding: '24px 28px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 2 }}>
            <div className="alloc-section-label" style={{ marginBottom: 0 }}>Allocation Overview</div>
            <div style={{ fontSize: 13, fontFamily: "'DM Mono',monospace", fontWeight: 600,
              color: overBudget ? '#8A2020' : (penalty && !cappedOut) ? '#8A6A10' : '#1A5C3A' }}>
              {overBudget
                ? `Over budget by ${fmtCur(Math.abs(remaining), sym, suffix)}`
                : remaining === 0 && totalSpend > 0
                  ? 'Fully allocated'
                  : cappedOut
                    ? 'Dept. caps reached — no penalty'
                    : `${fmtCur(remaining, sym, suffix)} remaining`
              }
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 44, justifyContent: 'center', flexWrap: 'wrap' }}>
            <div style={{ flexShrink: 0 }}>
              <AllocationDonut
                depts={depts} budget={budget} totalSpend={totalSpend}
                sym={sym} suffix={suffix}
                overBudget={overBudget} penalty={penalty && !cappedOut} cappedOut={cappedOut}
              />
            </div>
            <div style={{ flexShrink: 0 }}>
              <DonutLegend depts={depts} totalSpend={totalSpend} budget={budget} sym={sym} suffix={suffix} overBudget={overBudget} />
            </div>
          </div>
        </div>

        {/* Department cards row */}
        <div>
          <div className="alloc-section-label" style={{ paddingLeft: 2 }}>Department Allocations</div>
          <div style={{ display: 'grid', gridTemplateColumns: deptGridCols, gap: 10 }}>
            {constraints.map(c => {
              const dc = getDept(c.dept_name)
              const sdData = subDecisionOptions[c.dept_name] || {}
              const sdOptions = sdData.options || {}
              const val = sliderValues[c.dept_name] ?? c.default
              const sliderPct = ((val - c.min) / (c.max - c.min)) * 100

              return (
                <div
                  key={c.dept_name}
                  className="alloc-card dept-card"
                  style={{
                    padding: '14px 14px 12px',
                    borderTop: `2px solid ${dc.color}`,
                    display: 'flex', flexDirection: 'column', gap: 10,
                  }}
                >
                  {/* Header: dept name */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                    <span style={{ fontSize: 12, fontWeight: 700, color: dc.colorL, letterSpacing: '0.02em' }}>
                      {c.dept_name}
                    </span>
                    {totalSpend > 0 && (
                      <span style={{ fontFamily: "'DM Mono',monospace", fontSize: 10, color: '#8090A4', fontWeight: 600 }}>
                        {((val / totalSpend) * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>

                  {/* R&D lag notice — only shown on the R&D card */}
                  {c.dept_name === 'R&D' && (
                    <div style={{
                      fontSize: 10, color: '#1A3A6B', background: 'rgba(26,58,107,0.07)',
                      border: '1px solid rgba(26,58,107,0.18)', borderRadius: 3,
                      padding: '3px 8px', display: 'inline-flex', alignItems: 'center', gap: 5,
                      fontWeight: 600, letterSpacing: '0.02em',
                    }}>
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none">
                        <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="2"/>
                        <path d="M12 7v5l3 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                      </svg>
                      Returns next year — spend now, revenue in Year {currentYear + 1}
                    </div>
                  )}

                  {/* Amount */}
                  {isController ? (
                    <DeptInput
                      val={val} div={div} deptCfg={dc} suffix={suffix}
                      sym={sym} min={c.min} max={c.max}
                      onChange={v => setSliderValues(p => ({ ...p, [c.dept_name]: v }))}
                    />
                  ) : (
                    <div style={{ fontFamily: "'DM Mono',monospace", fontSize: 16, fontWeight: 700, color: dc.colorL }}>
                      {fmtCur(val, sym, suffix)}
                    </div>
                  )}

                  {/* Slider */}
                  {isController && (
                    <div>
                      <ThrottledRange
                        min={c.min} max={c.max} step={c.step || div}
                        value={val}
                        onChange={v => setSliderValues(p => ({ ...p, [c.dept_name]: v }))}
                        className="alloc-slider"
                        style={{
                          '--dept-color': dc.color,
                          background: `linear-gradient(to right, ${dc.color} ${sliderPct}%, #E8ECF3 ${sliderPct}%)`,
                        }}
                      />
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: '#8090A4', fontFamily: "'DM Mono',monospace", marginTop: 4 }}>
                        <span>{fmtCur(c.min, sym, suffix)}</span>
                        <span>{fmtCur(c.max, sym, suffix)}</span>
                      </div>
                    </div>
                  )}

                  {/* Strategy */}
                  {isController && Object.keys(sdOptions).length > 0 && (
                    <div>
                      <div style={{ fontSize: 9, fontWeight: 700, color: '#8090A4', textTransform: 'uppercase', letterSpacing: '0.14em', marginBottom: 6, fontFamily: "'DM Mono',monospace" }}>
                        {sdData.label || 'Strategy'}
                      </div>
                      <StrategyOptions
                        options={sdOptions}
                        value={subdecisions[c.dept_name]}
                        onChange={key => setSubdecisions(p => ({ ...p, [c.dept_name]: key }))}
                        deptColor={dc.color}
                      />
                    </div>
                  )}

                  {!isController && (
                    <div style={{ fontSize: 11, color: '#8090A4', fontStyle: 'italic' }}>Viewer mode</div>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {isController && (() => {
          const lockedSd = gameState?.locked_subdecisions || []
          const prevSd = lockedSd.length > 0 ? lockedSd[lockedSd.length - 1] : null
          if (!prevSd) return null
          const repeats = Object.entries(subdecisions).filter(([dept, choice]) =>
            choice && choice !== '_placeholder' && prevSd[dept] === choice
          )
          if (repeats.length === 0) return null
          return (
            <div style={{ background: '#FFF8EC', border: '1px solid #E8C87A', borderLeft: '3px solid #B8932A', borderRadius: 4, padding: '10px 14px', display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0, marginTop: 1 }}>
                <path d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" stroke="#B8932A" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#7A5C10', marginBottom: 2 }}>Synergy decay warning</div>
                <div style={{ fontSize: 11, color: '#7A5C10', lineHeight: 1.55 }}>
                  {repeats.map(([dept]) => dept).join(', ')} {repeats.length === 1 ? 'uses' : 'use'} the same strategy as last year.
                  Held strategies lose ~30% of their pairing bonus each year as the market adapts.
                  Switching now would restore the full bonus.
                </div>
              </div>
            </div>
          )
        })()}

        {/* Footer: Seal action */}
        {isController && (
          <div className="alloc-card" style={{ padding: '14px 18px', display: 'flex', alignItems: 'center', gap: 16, justifyContent: 'space-between', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, minWidth: 0, flex: 1 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: '#0A1628' }}>Ready to seal Year {currentYear}?</div>
              <div style={{ fontSize: 11, color: '#6A7A8A', display: 'flex', gap: 14, flexWrap: 'wrap' }}>
                <span style={{ color: overBudget ? '#8A2020' : '#3A4A5A' }}>
                  {overBudget ? `Over by ${fmtCur(Math.abs(remaining), sym, suffix)}` : 'Within budget'}
                </span>
                <span style={{ color: allStrategiesSet ? '#3A4A5A' : '#8A2020' }}>
                  {allStrategiesSet ? 'All strategies set' : `${constraints.filter(c => !subdecisions[c.dept_name]).length} strategy left`}
                </span>
                {cappedOut && <span style={{ color: '#1A5C3A' }}>Dept. caps reached · no penalty</span>}
                {penalty && !cappedOut && <span style={{ color: '#8A6A10' }}>{unusedPct.toFixed(0)}% allocatable unused → penalty</span>}
              </div>
            </div>
            <button
              onClick={() => setConfirmOpen(true)}
              disabled={!canSeal}
              className="btn btn-gold"
              style={{ padding: '10px 22px', fontSize: 13, flexShrink: 0 }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ marginRight: 4 }}>
                <rect x="5" y="11" width="14" height="11" rx="2" stroke="rgba(255,255,255,0.7)" strokeWidth="1.6" />
                <path d="M8 11V7a4 4 0 018 0v4" stroke="rgba(255,255,255,0.7)" strokeWidth="1.6" strokeLinecap="round" />
                <circle cx="12" cy="16" r="1.5" fill="rgba(255,255,255,0.7)" />
              </svg>
              Review &amp; Seal
            </button>
          </div>
        )}
      </div>

      {/* Confirm modal */}
      {confirmOpen && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(10,22,40,0.55)', backdropFilter: 'blur(4px)', WebkitBackdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999, animation: 'allocFadeIn 0.18s ease both' }}>
          <div className="alloc-confirm-modal" style={{ background: '#FFFFFF', border: '1px solid #D4DCE8', borderTop: '3px solid #B8932A', borderRadius: 4, boxShadow: '0 12px 48px rgba(10,22,40,0.30)', padding: 24, maxWidth: 460, width: '100%', margin: '0 16px', animation: 'allocSlideUp 0.22s ease both' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
              <h3 style={{ fontSize: 16, fontWeight: 800, margin: 0, color: '#0A1628' }}>Seal Year {currentYear}</h3>
              <span style={{ fontFamily: "'DM Mono',monospace", fontSize: 9, color: '#8090A4', letterSpacing: '0.18em' }}>IRREVERSIBLE</span>
            </div>
            <p style={{ fontSize: 12, color: '#3A4A5A', marginBottom: 14, lineHeight: 1.55 }}>
              Once sealed, your allocation and strategies become this year's locked record.
            </p>

            <div style={{ display: 'flex', gap: 14, alignItems: 'center', background: '#F8FAFC', border: '1px solid #E8ECF3', borderRadius: 4, padding: '12px 14px', marginBottom: 12 }}>
              <div style={{ flexShrink: 0 }}>
                <MiniDonut depts={depts} budget={budget} totalSpend={totalSpend} />
              </div>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 4 }}>
                {constraints.map(c => {
                  const dc = getDept(c.dept_name)
                  const v = sliderValues[c.dept_name] ?? c.default
                  return (
                    <div key={c.dept_name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12 }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: 6, color: dc.colorL, fontWeight: 600 }}>
                        <span style={{ width: 6, height: 6, background: dc.color, borderRadius: '50%' }} />
                        {c.dept_name}
                      </span>
                      <span style={{ fontFamily: "'DM Mono',monospace", color: '#0A1628', fontWeight: 700 }}>
                        {fmtCur(v, sym, suffix)}
                      </span>
                    </div>
                  )
                })}
                <div style={{ borderTop: '1px solid #E8ECF3', marginTop: 4, paddingTop: 4, display: 'flex', justifyContent: 'space-between', fontSize: 12, fontWeight: 700 }}>
                  <span style={{ color: '#3A4A5A' }}>Total</span>
                  <span style={{ fontFamily: "'DM Mono',monospace", color: '#1A5C3A' }}>{fmtCur(totalSpend, sym, suffix)}</span>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 14 }}>
              <ChecklistItem ok={!overBudget} label={overBudget ? `Reduce by ${fmtCur(Math.abs(remaining), sym, suffix)}` : 'Within budget'} />
              {cappedOut
                ? <ChecklistItem ok={true} label='Dept. caps reached — no penalty applied' optional />
                : <ChecklistItem ok={!penalty} label={penalty ? `${unusedPct.toFixed(0)}% of allocatable budget unused → penalty` : 'No underuse penalty'} optional />
              }
              <ChecklistItem ok={allStrategiesSet} label={allStrategiesSet ? 'All strategies chosen' : 'Pick a strategy for every department'} />
              <ChecklistItem ok={!(blocking?.length > 0)} label={blocking?.length > 0 ? `Waiting: ${blocking.length} team(s)` : 'No teams holding'} />
            </div>

            <HoldToSealButton
              disabled={locking || !canSeal}
              year={currentYear}
              label={`Hold to Seal Year ${currentYear}`}
              onComplete={handleSeal}
            />
            <div style={{ display: 'flex', justifyContent: 'center', marginTop: 10 }}>
              <button onClick={() => setConfirmOpen(false)} disabled={locking} className="btn btn-g" style={{ padding: '7px 18px' }}>
                Back
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
