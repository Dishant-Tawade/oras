import React, { useState, useMemo } from 'react'
import { InfoTooltip } from './MetricInfo'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import YearNarrativePanel from './YearNarrativePanel'


// Animated count-up
function AnimatedNum({ value, duration = 1400, prefix = '', suffix = '' }) {
  const [display, setDisplay] = React.useState(value)
  const prevRef = React.useRef(value)
  React.useEffect(() => {
    const from = prevRef.current ?? 0
    const to = value ?? 0
    if (from === to || to == null) return
    prevRef.current = to
    const start = Date.now()
    const tick = () => {
      const p = Math.min((Date.now() - start) / duration, 1)
      const ease = 1 - Math.pow(1 - p, 3)
      setDisplay(Math.round(from + (to - from) * ease))
      if (p < 1) requestAnimationFrame(tick)
      else setDisplay(to)
    }
    requestAnimationFrame(tick)
  }, [value])
  return <span>{prefix}{display != null ? display.toLocaleString() : '—'}{suffix}</span>
}

const DEPT_COLORS = { 'R&D': '#1A3A6B', 'Sales': '#8A6A10', 'Operations': '#1A5C3A', 'Marketing': '#4A2A7A' }
const DEPT_NAMES  = ['R&D', 'Sales', 'Operations', 'Marketing']
const GRADE_COLORS = { S: '#FFD700', A: '#1A5C3A', B: '#5B8DEF', C: '#8A6A10', D: '#E07C3A', F: '#B03030' }
const MONO = "'DM Mono', monospace"
const T = { t1: '#0A1628', t2: '#3A4A5A', t3: '#8090A4' }

function fmtCur(val, sym, suffix) {
  sym = sym || '$'; suffix = suffix || 'K'
  if (val === null || val === undefined) return `${sym}0${suffix}`
  const abs = Math.abs(val); const neg = val < 0 ? '-' : ''
  if (suffix === 'K') return `${neg}${sym}${Math.round(abs / 1e3).toLocaleString()}K`
  if (suffix === 'L') { if (abs >= 1e7) return `${neg}${sym}${(abs / 1e7).toFixed(1)}Cr`; return `${neg}${sym}${Math.round(abs / 1e5).toLocaleString()}L` }
  return `${neg}${sym}${(abs / 1e6).toFixed(2)}M`
}

function C2Card({ children, extra = {} }) {
  return <div style={{ background: '#FFFFFF', border: '1px solid #D4DCE8', borderRadius: 4, boxShadow: '0 2px 8px rgba(10,22,40,0.10)', boxShadow: '0 1px 6px rgba(10,22,40,0.06)', padding: '18px 20px', marginBottom: 12, ...extra }}>{children}</div>
}
function SHdr({ children, tip }) {
  return <div className="sec-lbl" style={{ display: 'inline-flex', alignItems: 'center' }}>{children}{tip && <InfoTooltip text={tip} />}</div>
}
function KpiCard({ label, value, accent, sub, tip }) {
  const col = accent || T.t1
  return (
    <div className="kpi-hover" style={{ padding: '10px 12px', borderRadius: 4, background: '#FFFFFF', border: '1px solid #D4DCE8', borderLeft: `3px solid ${col}` }}>
      <div style={{ fontSize: 10, fontWeight: 600, color: '#6A7A8A', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 2, display: 'flex', alignItems: 'center' }}>{label}{tip && <InfoTooltip text={tip} />}</div>
      <div style={{ fontSize: 17, fontWeight: 700, color: col, fontFamily: MONO, letterSpacing: '-0.5px' }}>{value}</div>
      {sub && <div style={{ fontSize: 10, color: '#6A7A8A', marginTop: 1 }}>{sub}</div>}
    </div>
  )
}

function GradeReferenceChart({ currentGrade }) {
  const rows = [
    ['S', '850+',    'Exceptional — optimal allocation & strategy synergy', '#FFD700'],
    ['A', '700–849', 'Strong — well-balanced resource decisions',           '#1A5C3A'],
    ['B', '550–699', 'Solid — good fundamentals, room to optimise',        '#5B8DEF'],
    ['C', '400–549', 'Average — missed key allocation trade-offs',         '#8A6A10'],
    ['D', '250–399', 'Weak — significant resource misallocation',          '#E07C3A'],
    ['F', '<250',    'Failing — critical under-investment or poor strategy', '#B03030'],
  ]
  return (
    <div style={{ marginBottom: 12 }}>
      <div className="sec-lbl">Grade Reference</div>
      {rows.map(([g, rng, desc, gc]) => {
        const isCur = g === currentGrade
        return (
          <div key={g} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 10px', borderRadius: 4, marginBottom: 3, background: isCur ? `${gc}18` : 'rgba(15,40,75,0.30)', border: `1px solid ${isCur ? gc : 'rgba(255,255,255,0.06)'}` }}>
            <div style={{ width: 26, height: 26, borderRadius: 5, background: gc, color: g === 'S' ? '#1a1a2e' : 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: 12, flexShrink: 0 }}>{g}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <span style={{ fontWeight: 700, fontSize: 12, color: '#0A1628' }}>{rng}</span>
              <div style={{ fontSize: 11, color: '#3A4A5A', marginTop: 1 }}>{desc}</div>
            </div>
            {isCur && <div style={{ fontSize: 10, fontWeight: 700, color: gc, whiteSpace: 'nowrap', flexShrink: 0 }}>YOU</div>}
          </div>
        )
      })}
    </div>
  )
}

function VpiEvalCard({ gameState, sym, suffix, pin, piFull }) {
  const yearResults = gameState?.year_results || []
  const n = yearResults.length
  const [selectedYear, setSelectedYear] = useState(n)

  const vpiYears = useMemo(() => {
    if (!yearResults.length) return []
    return yearResults.map((yr, i) => {
      const profits = yearResults.slice(0, i + 1).map(r => r.profit)
      const cumProfit = profits.reduce((s, v) => s + v, 0)
      const sdMult = yr.subdecision_multiplier ?? 1.0
      const sdDelta = (sdMult - 1) * 100
      return { year: i + 1, vpi: yr.vpi ?? null, grade: yr.grade ?? null, ras: yr.ras ?? null, avgShare: yr.avg_share_vpi ?? yr.market_share ?? 0, cumProfit, sdDelta, sdMult }
    })
  }, [yearResults])

  const yr = useMemo(() => vpiYears.find(v => v.year === selectedYear) || vpiYears[vpiYears.length - 1], [vpiYears, selectedYear])
  if (!yr) return null

  const gc = GRADE_COLORS[yr.grade] || T.t1
  const sdSign = yr.sdDelta >= 0 ? '+' : ''

  return (
    <C2Card extra={{ border: `2px solid ${gc}40` }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
        <SHdr tip="Your overall performance evaluation for the selected year, including VPI score, letter grade, and supporting metrics.">Evaluation</SHdr>
        {vpiYears.length > 1 && (
          <select value={selectedYear} onChange={e => setSelectedYear(Number(e.target.value))} style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4, marginBottom: 10 }}>
            {vpiYears.map(v => <option key={v.year} value={v.year}>Year {v.year} — {pin}: {v.vpi} ({v.grade})</option>)}
          </select>
        )}
      </div>
      {/* Hero score */}
      <div style={{ textAlign: 'center', marginBottom: 16, padding: '20px 0' }}>
        <span style={{ fontSize: 48, fontWeight: 900, fontFamily: MONO, color: gc, letterSpacing: '-2px', lineHeight: 1 }}><AnimatedNum value={yr.vpi} duration={1600} /></span>
        <span style={{ fontSize: 30, fontWeight: 800, color: gc, marginLeft: 12 }}>{yr.grade}</span>
        <InfoTooltip metricKey="vpi" />
      </div>
      <div className="kpi-grid" style={{ marginBottom: 14 }}>
        <KpiCard label="Risk-Adj Score" value={yr.ras != null ? fmtCur(yr.ras, sym, suffix) : '—'} accent={yr.ras > 0 ? '#1A5C3A' : '#B03030'} sub="Monte Carlo avg − 2σ" tip="Monte Carlo simulation average minus two standard deviations — a conservative estimate of your profit under uncertainty. Penalises volatile strategies even if their average looks good." />
        <KpiCard label="Avg Mkt Share" value={`${yr.avgShare.toFixed(1)}%`} accent="#80B0D8" sub={`through year ${yr.year}`} tip="Average of your market share percentages across all years completed so far. Used as 50% of your final VPI score." />
        <KpiCard label="Cumulative Profit" value={fmtCur(yr.cumProfit, sym, suffix)} accent={yr.cumProfit > 0 ? '#1A5C3A' : '#B03030'} sub={`${yr.year}/5 years`} tip="Sum of all net profits across every completed year so far. The long-run health of your company." />
        <KpiCard label="Strategy Mult." value={`${sdSign}${yr.sdDelta.toFixed(1)}%`} accent={yr.sdDelta >= 0 ? '#1A5C3A' : '#B03030'} sub="Sub-decision impact" tip="A multiplier applied to your score based on your sub-decisions (strategic directions). Positive means your choices synergised well; negative means misalignment. Repeating the same choice in consecutive years causes a 30% decay." />
      </div>
      <GradeReferenceChart currentGrade={yr.grade} />
      <div style={{ fontSize: 11, color: '#3A4A5A', lineHeight: 1.6 }}>
        The {piFull} ({pin}) is scored 0–1000+ from two equally weighted components: risk-adjusted profit (50%) and average market share (50%).
      </div>
    </C2Card>
  )
}

function StrategyCard({ gameState }) {
  const yearResults = gameState?.year_results || []
  const lockedSd = gameState?.locked_subdecisions || []
  if (!lockedSd.length) return null
  return (
    <C2Card>
      <SHdr tip="The sub-decisions your team locked in each year, and the resulting strategy multiplier applied to your VPI score. Repeating the same choice in consecutive years causes a 30% synergy decay.">Strategic Directions</SHdr>
      {lockedSd.map((sdDict, i) => {
        if (!sdDict || !Object.keys(sdDict).length) return null
        const yr = yearResults[i]
        const sdMult = yr?.subdecision_multiplier ?? 1.0
        const sdDelta = (sdMult - 1) * 100
        const sdSign = sdDelta >= 0 ? '+' : ''
        return (
          <div key={i} style={{ marginBottom: 12, paddingBottom: 12, borderBottom: '1px solid #E0E6EF' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <span style={{ fontWeight: 700, fontSize: 12, color: '#6A7A8A', fontFamily: MONO }}>Year {i + 1}</span>
              {yr && <span style={{ fontSize: 11, fontWeight: 700, color: sdDelta >= 0 ? '#1A5C3A' : '#B03030', fontFamily: MONO }}>×{sdMult.toFixed(3)} ({sdSign}{sdDelta.toFixed(1)}%)</span>}
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
              {Object.entries(sdDict).map(([dept, key]) => {
                const col = DEPT_COLORS[dept] || '#1A5C3A'
                return (
                  <span key={dept} style={{ fontSize: 11, padding: '3px 10px', borderRadius: 5, background: '#F5F7FA', border: '1px solid #E0E6EF' }}>
                    <span style={{ fontWeight: 700, color: col }}>{dept}:</span> <span style={{ color: '#3A4A5A' }}>{key}</span>
                  </span>
                )
              })}
            </div>
          </div>
        )
      })}
    </C2Card>
  )
}

function DeptTable({ gameState, sym, suffix }) {
  const yearResults = gameState?.year_results || []
  const locked = gameState?.locked_allocations || []
  const n = yearResults.length
  const [selectedYear, setSelectedYear] = useState(n - 1)
  if (!n) return null
  const yr = Math.min(selectedYear, n - 1)
  const result = yearResults[yr]
  const alloc  = locked[yr] || []
  const th = { padding: '5px 8px', fontSize: 10, fontWeight: 600, color: '#6A7A8A', textTransform: 'uppercase', letterSpacing: '.4px', borderBottom: '1px solid #D4DCE8' }
  const rows = DEPT_NAMES.map((name, d) => {
    const spend = alloc[d] ?? 0
    const ret   = result.dept_returns?.[d] ?? 0
    const eff   = spend > 0 ? ret / spend : 0
    const mom   = result.dept_state?.[d] ?? 0
    const barPct = Math.min(mom / 4 * 100, 100)
    const col = DEPT_COLORS[name] || '#1A5C3A'
    const note = name === 'R&D' ? ' (lagged)' : ''
    let trend = null
    if (yr > 0 && locked[yr - 1]) {
      const prevSpend = locked[yr - 1][d] ?? 0
      const prevRet = yearResults[yr - 1]?.dept_returns?.[d] ?? 0
      const prevEff = prevSpend > 0 ? prevRet / prevSpend : 0
      if (prevEff > 0) {
        const dp = (eff - prevEff) / prevEff * 100
        if (dp > 2) trend = <span style={{ color: '#1A5C3A', fontSize: 10 }}> ▲{dp.toFixed(0)}%</span>
        else if (dp < -2) trend = <span style={{ color: '#8A2020', fontSize: 10 }}> ▼{Math.abs(dp).toFixed(0)}%</span>
      }
    }
    return (
      <tr key={name} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
        <td style={{ padding: '7px 8px', fontSize: 13 }}>
          <span style={{ fontWeight: 600, color: col }}>{name}</span>
          <span style={{ fontSize: 10, color: '#6A7A8A' }}>{note}</span>
        </td>
        <td style={{ fontFamily: MONO, fontSize: 12, padding: '7px 8px', textAlign: 'right', color: '#3A4A5A' }}>{fmtCur(spend, sym, suffix)}</td>
        <td style={{ fontFamily: MONO, fontSize: 12, padding: '7px 8px', textAlign: 'right', color: '#3A4A5A' }}>{fmtCur(ret, sym, suffix)}</td>
        <td style={{ padding: '7px 8px', textAlign: 'right' }}>
          <span style={{ fontFamily: MONO, fontSize: 12, fontWeight: 600, color: eff > 2 ? '#1A5C3A' : eff > 1 ? '#8A6A10' : '#B03030' }}>{sym}{eff.toFixed(2)}</span>
          {trend}
        </td>
        <td style={{ padding: '7px 6px' }}>
          <div style={{ width: 50, height: 4, background: '#D4DCE8', borderRadius: 2, overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${barPct}%`, background: col, borderRadius: 2 }} />
          </div>
        </td>
      </tr>
    )
  })
  return (
    <C2Card>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
        <SHdr tip="Year-by-year breakdown of each department's spend, revenue return, efficiency ratio, and momentum state.">Department Performance</SHdr>
        {n > 1 && (
          <select value={yr} onChange={e => setSelectedYear(Number(e.target.value))} style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4, marginBottom: 10 }}>
            {yearResults.map((_, i) => <option key={i} value={i}>Year {i + 1}</option>)}
          </select>
        )}
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {[
                { h: 'Dept',      tip: null },
                { h: 'Spend',     tip: 'Amount of your budget allocated to this department this year.' },
                { h: 'Return',    tip: 'Revenue attributed to this department this year. R&D returns are lagged — this year\'s R&D spend pays off next year.' },
                { h: `${sym}/$ In`, tip: 'Return divided by spend. Above 1.0 means every dollar invested earned more than a dollar back. Green >2×, amber >1×, red <1×.' },
                { h: 'Momentum',  tip: 'A 0–4 internal capability score for this department. Higher momentum amplifies future returns.' },
              ].map(({ h, tip }, i) => (
                <th key={h} style={{ ...th, textAlign: i === 0 ? 'left' : i === 4 ? 'left' : 'right' }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 2 }}>{h}{tip && <InfoTooltip text={tip} />}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>
      </div>
      <div style={{ fontSize: 11, color: '#8A6A10', fontWeight: 500, marginTop: 8 }}>R&D returns shown are from prior year's investment (lagged by 1 year).</div>
    </C2Card>
  )
}

function ProfitComparisonTable({ gameState, sym, suffix }) {
  const yearResults = gameState?.year_results || []
  if (!yearResults.length) return null
  const userProfits = yearResults.map(r => r.profit)
  const competitorNames = yearResults[0]?.competitor_profits ? Object.keys(yearResults[0].competitor_profits) : []
  const th = { padding: '6px 8px', fontSize: 9, fontWeight: 600, color: '#6A7A8A', textTransform: 'uppercase', letterSpacing: '.4px', borderBottom: '1px solid #D4DCE8' }
  function yoyArrow(series, idx) {
    if (idx === 0 || !series[idx - 1]) return null
    const pct = (series[idx] - series[idx - 1]) / Math.abs(series[idx - 1]) * 100
    if (pct > 1) return <span style={{ color: '#1A5C3A', fontSize: 9, fontWeight: 600 }}> ▲{pct.toFixed(0)}%</span>
    if (pct < -1) return <span style={{ color: '#8A2020', fontSize: 9, fontWeight: 600 }}> ▼{Math.abs(pct).toFixed(0)}%</span>
    return null
  }
  return (
    <C2Card>
      <SHdr tip="Year-by-year net profit for your team versus each AI competitor. ▲/▼ arrows show year-over-year change.">Profit Comparison</SHdr>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{ ...th, textAlign: 'left' }}>Year</th>
              <th style={{ ...th, textAlign: 'right' }}>You</th>
              {competitorNames.map(n => <th key={n} style={{ ...th, textAlign: 'right' }}>{n.split(' ')[0]}</th>)}
            </tr>
          </thead>
          <tbody>
            {yearResults.map((yr, i) => {
              const isLatest = i === yearResults.length - 1
              return (
              <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', background: isLatest ? '#EAF0FA' : 'transparent', borderRadius: isLatest ? 7 : 0 }}>
                <td style={{ padding: '6px 8px', fontSize: 13, fontWeight: 600, color: isLatest ? '#0A1628' : '#6A7A8A' }}>Yr{i + 1}</td>
                <td style={{ padding: '6px 8px', textAlign: 'right' }}>
                  <span style={{ fontFamily: MONO, fontSize: 12, fontWeight: isLatest ? 700 : 400, color: userProfits[i] >= 0 ? '#1A5C3A' : '#B03030' }}>{fmtCur(userProfits[i], sym, suffix)}</span>
                  {yoyArrow(userProfits, i)}
                </td>
                {competitorNames.map(n => {
                  const cProfit = yr.competitor_profits?.[n] ?? 0
                  const prevProfit = i > 0 ? (yearResults[i - 1].competitor_profits?.[n] ?? 0) : 0
                  const pct = i > 0 && prevProfit ? (cProfit - prevProfit) / Math.abs(prevProfit) * 100 : 0
                  return (
                    <td key={n} style={{ padding: '6px 8px', textAlign: 'right' }}>
                      <span style={{ fontFamily: MONO, fontSize: 12, color: '#6A7A8A' }}>{fmtCur(cProfit, sym, suffix)}</span>
                      {i > 0 && Math.abs(pct) > 1 && <span style={{ color: pct > 0 ? '#1A5C3A' : '#B03030', fontSize: 9, fontWeight: 600 }}> {pct > 0 ? '▲' : '▼'}{Math.abs(pct).toFixed(0)}%</span>}
                    </td>
                  )
                })}
              </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </C2Card>
  )
}

function YearSummaryKpis({ gameState, sym, suffix, pin }) {
  const yearResults = gameState?.year_results || []
  if (!yearResults.length) return null
  const lat = yearResults[yearResults.length - 1]
  const n = yearResults.length
  const rev = lat.total_revenue; const prof = lat.profit
  const margin = rev > 0 ? (prof / rev) * 100 : 0
  const cum = yearResults.reduce((s, r) => s + r.profit, 0)
  const spend = lat.total_spend; const bgt = lat.available_budget || gameState?.available_budget || 1
  const unusedPct = bgt > 0 ? ((bgt - spend) / bgt) * 100 : 0
  const pen = lat.underuse_penalty ?? 0
  const share = lat.market_share ?? 0
  const sdMult = lat.subdecision_multiplier ?? 1.0
  const sdDelta = (sdMult - 1) * 100
  const sdSign = sdDelta >= 0 ? '+' : ''
  return (
    <C2Card>
      <SHdr>Year {n} Summary</SHdr>
      {/* Hero KPIs — 3 large glass cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10, marginBottom: 14 }}>
        <div style={{ background: '#FFFFFF', border: '1px solid #D4DCE8', borderRadius: 4, boxShadow: '0 2px 8px rgba(10,22,40,0.10)', boxShadow: '0 2px 12px rgba(13,31,60,0.07)', padding: 22, textAlign: 'center' }}>
          <div style={{ fontSize: 28, fontWeight: 900, fontFamily: "'DM Mono',monospace", lineHeight: 1, color: '#1A5C3A' }}>{fmtCur(rev, sym, suffix)}</div>
          <div style={{ fontSize: 9, color: '#6A7A8A', textTransform: 'uppercase', letterSpacing: '0.14em', marginTop: 6, fontFamily: "'DM Mono',monospace", display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}>Revenue<InfoTooltip metricKey="revenue" /></div>
        </div>
        <div style={{ background: '#FFFFFF', border: '1px solid #D4DCE8', borderRadius: 4, boxShadow: '0 2px 8px rgba(10,22,40,0.10)', boxShadow: '0 2px 12px rgba(13,31,60,0.07)', padding: 22, textAlign: 'center' }}>
          <div style={{ fontSize: 28, fontWeight: 900, fontFamily: "'DM Mono',monospace", lineHeight: 1, color: '#80B0E8' }}>{`${share.toFixed(1)}%`}</div>
          <div style={{ fontSize: 9, color: '#6A7A8A', textTransform: 'uppercase', letterSpacing: '0.14em', marginTop: 6, fontFamily: "'DM Mono',monospace", display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}>Market Share<InfoTooltip metricKey="marketShare" /></div>
        </div>
        <div style={{ background: '#FFFFFF', border: '1px solid #D4DCE8', borderRadius: 4, boxShadow: '0 2px 8px rgba(10,22,40,0.10)', boxShadow: '0 2px 12px rgba(13,31,60,0.07)', padding: 22, textAlign: 'center' }}>
          <div style={{ fontSize: 28, fontWeight: 900, fontFamily: "'DM Mono',monospace", lineHeight: 1, color: prof >= 0 ? '#228B57' : '#B03030' }}>{fmtCur(prof, sym, suffix)}</div>
          <div style={{ fontSize: 9, color: '#6A7A8A', textTransform: 'uppercase', letterSpacing: '0.14em', marginTop: 6, fontFamily: "'DM Mono',monospace", display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}>Net Profit Y{n}<InfoTooltip metricKey="netProfit" /></div>
        </div>
      </div>
      {/* Secondary KPI grid */}
      {/* Secondary KPI grid */}
      <div className="kpi-grid">
        <KpiCard label="Profit Margin" value={`${margin.toFixed(1)}%`} accent={margin > 20 ? '#1A5C3A' : '#8A6A10'} tip="Net profit as a percentage of revenue. A higher margin means you're keeping more of each dollar earned. Below 10% is a warning sign." />
        <KpiCard label="Budget Used" value={`${(100 - unusedPct).toFixed(0)}%`} accent={unusedPct < 15 ? '#1A5C3A' : '#B03030'} sub={pen > 0 ? `${fmtCur(pen, sym, suffix)} penalty` : null} tip="Percentage of your available budget that was allocated and spent this year. Leaving more than 15% unspent triggers an underuse penalty." />
        <KpiCard label="Cumulative Profit" value={fmtCur(cum, sym, suffix)} accent={cum >= 0 ? '#1A5C3A' : '#B03030'} sub={`${n}/5 yrs`} tip="Sum of all net profits across every completed year so far. The long-run health of your company." />
        <KpiCard label="Strategy Mult." value={`${sdSign}${sdDelta.toFixed(1)}%`} accent={sdDelta >= 0 ? '#1A5C3A' : '#B03030'} sub="Sub-decision impact" tip="A multiplier applied to your score based on your sub-decisions (strategic directions). Positive means your choices synergised well; negative means misalignment. Repeating the same choice in consecutive years causes a 30% decay." />
      </div>
    </C2Card>
  )
}

function DeptReturnChart({ yearResults, sym, suffix }) {
  if (!yearResults.length) return null
  const lat = yearResults[yearResults.length - 1]
  if (!lat.dept_returns) return null
  const data = lat.dept_returns.map((val, d) => ({ name: DEPT_NAMES[d] || `Dept ${d}`, value: val }))
  return (
    <C2Card>
      <SHdr tip="Revenue attributed to each department for the most recent year. R&D returns are lagged — this year's R&D spend pays off next year.">Department Returns — Year {yearResults.length}</SHdr>
      <ResponsiveContainer width="100%" height={130}>
        <BarChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 8 }}>
          <XAxis dataKey="name" tick={{ fill: '#8090A4', fontSize: 10 }} />
          <YAxis tickFormatter={v => fmtCur(v, sym, suffix)} tick={{ fill: '#8090A4', fontSize: 10 }} />
          <Tooltip formatter={v => fmtCur(v, sym, suffix)} contentStyle={{ background: 'rgba(91,191,116)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: 4, fontSize: 12, color: '#0A1628' }} />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((_, d) => <Cell key={d} fill={Object.values(DEPT_COLORS)[d] || '#1A5C3A'} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </C2Card>
  )
}

export default function PerformanceTab({ gameState, scenarioInfo }) {
  const yearResults = gameState?.year_results || []
  const sym    = scenarioInfo?.currency_symbol || '$'
  const suffix = scenarioInfo?.small_number_suffix || 'K'
  const pin    = scenarioInfo?.performance_index_name || 'VPI'
  const piFull = scenarioInfo?.performance_index_full || 'Value Performance Index'

  if (!yearResults.length) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '60px 0' }}>
        <div style={{ background: '#FFFFFF',  border: '1px solid #D4DCE8', borderRadius: 4, padding: '36px 44px', maxWidth: 420, textAlign: 'center' }}>
          <div style={{ width: 52, height: 52, borderRadius: '50%', background: '#F5F7FA', border: '1px solid #D4DCE8', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 18px' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M3 3v18h18" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" strokeLinecap="round"/>
              <path d="M7 16l4-4 4 4 4-6" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div style={{ fontSize: 15, fontWeight: 700, color: '#3A4A5A', marginBottom: 8 }}>No Results Yet</div>
          <div style={{ fontSize: 13, color: '#6A7A8A', lineHeight: 1.7 }}>
            Lock Year 1 to see your performance data — VPI score, market share, and department returns will appear here.
          </div>
        </div>
      </div>
    )
  }

  // Pull the latest year's narrative (if any).
  const latestYearIdx = yearResults.length
  const latestNarrative = yearResults[yearResults.length - 1]?.narrative

  return (
    <div>
      <YearNarrativePanel narrative={latestNarrative} year={latestYearIdx} />
      <div className="tab-two-col" style={{ display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'flex-start' }}>
        <div className="tab-col" style={{ flex: 1, minWidth: 340, display: 'flex', flexDirection: 'column' }}>
          <YearSummaryKpis gameState={gameState} sym={sym} suffix={suffix} pin={pin} />
          <DeptReturnChart yearResults={yearResults} sym={sym} suffix={suffix} />
          <DeptTable gameState={gameState} sym={sym} suffix={suffix} />
          <ProfitComparisonTable gameState={gameState} sym={sym} suffix={suffix} />
        </div>
        <div className="tab-col" style={{ flex: 1, minWidth: 340, display: 'flex', flexDirection: 'column' }}>
          <VpiEvalCard gameState={gameState} sym={sym} suffix={suffix} pin={pin} piFull={piFull} />
          <StrategyCard gameState={gameState} />
        </div>
      </div>
    </div>
  )
}
