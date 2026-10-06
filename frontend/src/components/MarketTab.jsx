import React, { useState, useMemo, useRef, useEffect } from 'react'
import { InfoTooltip } from './MetricInfo'
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

const DEPT_NAMES  = ['R&D', 'Sales', 'Operations', 'Marketing']
const COMP_COLORS = ['#7B8FA1', '#C0392B', '#B07D62', '#6B8E7B']
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
const chartTooltipStyle = {
  background: '#FFFFFF', border: '1px solid #D4DCE8',
  borderRadius: 4, fontSize: 12, color: '#0A1628',
}
const chartTooltipStyle2 = {
  background: 'rgba(91,191,116)', border: '1px solid #D4DCE8',
  borderRadius: 4, fontSize: 12, color: '#0A1628',
}

function CompetitorProfitChart({ yearResults, sym, suffix }) {
  const labels = yearResults.map((_, i) => `Yr${i + 1}`)
  let cumUser = 0
  const cumComp = {}
  const data = yearResults.map((yr, i) => {
    cumUser += yr.profit
    const row = { year: labels[i], You: cumUser }
    Object.entries(yr.competitor_profits || {}).forEach(([name, profit]) => {
      const short = name.split(' ')[0]
      cumComp[short] = (cumComp[short] || 0) + profit
      row[short] = cumComp[short]
    })
    return row
  })
  const compKeys = data.length ? Object.keys(data[data.length - 1]).filter(k => k !== 'year' && k !== 'You') : []
  const allKeys = ['You', ...compKeys]
  const colors = ['#1A5C3A', ...COMP_COLORS]
  return (
    <C2Card>
      <SHdr tip="Running total of net profit over time for your team versus each competitor. A rising line means consistent profitability; a flat or falling line signals trouble.">Cumulative Profit vs. Market</SHdr>
      {compKeys.length === 0 && <div style={{ fontSize: 11, color: '#6A7A8A', marginBottom: 8 }}>Competitor data appears after locking Year 1.</div>}
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data} margin={{ top: 4, right: 12, bottom: 0, left: 8 }}>
          <XAxis dataKey="year" tick={{ fill: T.t3, fontSize: 11 }} />
          <YAxis tickFormatter={v => fmtCur(v, sym, suffix)} tick={{ fill: T.t3, fontSize: 10 }} width={65} />
          <Tooltip contentStyle={chartTooltipStyle} formatter={(v, name) => [fmtCur(v, sym, suffix), name]} />
          <Legend wrapperStyle={{ fontSize: 11, color: '#3A4A5A' }} />
          {allKeys.map((key, i) => (
            <Line key={key} type="monotone" dataKey={key}
              stroke={colors[i % colors.length]}
              strokeWidth={key === 'You' ? 2.5 : 1.5}
              strokeDasharray={key === 'You' ? undefined : '5 3'}
              dot={{ r: key === 'You' ? 4 : 2, fill: colors[i % colors.length] }} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </C2Card>
  )
}

// Resolves vertical overlaps on one side of the pie by nudging labels apart
function MarketNarrativeCard({ yearResults }) {
  const n = yearResults.length
  const [selectedYear, setSelectedYear] = useState(n - 1)
  const yr = yearResults[Math.min(selectedYear, n - 1)]
  const insights = yr?.market_narrative
  if (!insights || insights.length === 0) return null

  const sentimentStyle = {
    positive: { border: '1px solid #B8D4BE', borderLeft: '3px solid #1A5C3A', background: '#F2F8F4' },
    warning:  { border: '1px solid #E8C87A', borderLeft: '3px solid #B8932A', background: '#FFF8EC' },
    neutral:  { border: '1px solid #D4DCE8', borderLeft: '3px solid #6A7A8A', background: '#F8FAFC' },
  }
  const sentimentIcon = {
    positive: <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><path d="M22 11.08V12a10 10 0 11-5.93-9.14" stroke="#1A5C3A" strokeWidth="2" strokeLinecap="round"/><polyline points="22 4 12 14.01 9 11.01" stroke="#1A5C3A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>,
    warning:  <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" stroke="#B8932A" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/><line x1="12" y1="9" x2="12" y2="13" stroke="#B8932A" strokeWidth="2" strokeLinecap="round"/><line x1="12" y1="17" x2="12.01" y2="17" stroke="#B8932A" strokeWidth="2" strokeLinecap="round"/></svg>,
    neutral:  <svg width="12" height="12" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="#6A7A8A" strokeWidth="2"/><line x1="12" y1="8" x2="12" y2="12" stroke="#6A7A8A" strokeWidth="2" strokeLinecap="round"/><line x1="12" y1="16" x2="12.01" y2="16" stroke="#6A7A8A" strokeWidth="2" strokeLinecap="round"/></svg>,
  }

  return (
    <C2Card>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <SHdr tip="What each competitor did this year — their budget focus, strategic choices, and segment positioning. Derived from the simulation, not inferable from the visible market data alone.">What Happened in the Market?</SHdr>
        {n > 1 && (
          <select value={selectedYear} onChange={e => setSelectedYear(Number(e.target.value))} style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4 }}>
            {yearResults.map((_, i) => <option key={i} value={i}>Year {i + 1}</option>)}
          </select>
        )}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {insights.map((insight, i) => (
          <div key={i} style={{ borderRadius: 4, padding: '10px 12px', ...(sentimentStyle[insight.sentiment] || sentimentStyle.neutral) }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
              {sentimentIcon[insight.sentiment] || sentimentIcon.neutral}
              <span style={{ fontSize: 11, fontWeight: 700, color: '#0A1628', textTransform: 'none', letterSpacing: 0 }}>
                {insight.name.split(' ')[0]}
              </span>
            </div>
            <div style={{ fontSize: 11, color: '#3A4A5A', lineHeight: 1.6 }}>{insight.text}</div>
          </div>
        ))}
      </div>
    </C2Card>
  )
}

function resolveOverlaps(labels, minGap) {
  if (labels.length === 0) return labels
  const sorted = [...labels].sort((a, b) => a.y - b.y)
  let changed = true
  let passes = 0
  while (changed && passes < 50) {
    changed = false
    passes++
    for (let i = 1; i < sorted.length; i++) {
      const prev = sorted[i - 1]
      const curr = sorted[i]
      const overlap = (prev.y + minGap) - curr.y
      if (overlap > 0) {
        prev.y -= overlap / 2
        curr.y += overlap / 2
        changed = true
      }
    }
  }
  return sorted
}

function MarketSharePie({ yearResults, sym, suffix }) {
  const n = yearResults.length
  const [selectedYear, setSelectedYear] = useState(n - 1)
  const yr = yearResults[Math.min(selectedYear, n - 1)]
  const shares = yr?.market_shares
  const pieData = useMemo(() => {
    if (shares && Object.keys(shares).length > 0) {
      return Object.entries(shares).map(([name, val]) => ({ name: name.split(' ')[0], value: parseFloat(val) || 0 })).sort((a, b) => b.value - a.value)
    }
    return DEPT_NAMES.map((name, i) => ({ name, value: yr?.dept_returns?.[i] ?? 0 }))
  }, [yr, shares])
  const isShareData = !!(shares && Object.keys(shares).length > 0)
  const pieColors = ['#1A5C3A', ...COMP_COLORS, '#4A2A7A', '#1A3A6B']

  const containerRef = useRef(null)
  const [containerWidth, setContainerWidth] = useState(400)
  useEffect(() => {
    if (!containerRef.current) return
    const ro = new ResizeObserver(entries => {
      for (const entry of entries) setContainerWidth(entry.contentRect.width)
    })
    ro.observe(containerRef.current)
    setContainerWidth(containerRef.current.offsetWidth)
    return () => ro.disconnect()
  }, [])

  const HEIGHT = 310
  const OUTER_R = 85
  const INNER_R = 32
  const CX = containerWidth / 2
  const CY = HEIGHT / 2
  const LABEL_R = OUTER_R + 30   // where leader line elbow point sits
  const ELBOW_LEN = 14           // horizontal run after elbow
  const MIN_GAP = 24             // minimum vertical gap between labels

  const customLabels = useMemo(() => {
    const RADIAN = Math.PI / 180
    const total = pieData.reduce((s, d) => s + d.value, 0)
    if (total === 0) return []
    let startAngle = 90  // matches recharts startAngle=90
    const raw = pieData.map((d, i) => {
      const sliceDeg = (d.value / total) * 360
      const midAngle = startAngle - sliceDeg / 2   // recharts goes clockwise from top
      startAngle -= sliceDeg
      const rad = midAngle * RADIAN
      // Pie edge point (leader line start)
      const ex = CX + (OUTER_R + 4) * Math.cos(rad)
      const ey = CY - (OUTER_R + 4) * Math.sin(rad)
      // Natural label anchor point
      const ax = CX + LABEL_R * Math.cos(rad)
      const ay = CY - LABEL_R * Math.sin(rad)
      const isRight = ax >= CX
      return {
        index: i,
        name: d.name,
        value: d.value,
        percent: d.value / total,
        color: pieColors[i % pieColors.length],
        ex, ey, ax, ay,
        isRight,
        y: ay,
      }
    })

    const leftItems = raw.filter(l => !l.isRight).map(l => ({ ...l }))
    const rightItems = raw.filter(l => l.isRight).map(l => ({ ...l }))
    const resolvedLeft = resolveOverlaps(leftItems, MIN_GAP)
    const resolvedRight = resolveOverlaps(rightItems, MIN_GAP)
    return [...resolvedLeft, ...resolvedRight]
  }, [pieData, isShareData, CX, CY, OUTER_R, LABEL_R, MIN_GAP])

  return (
    <C2Card extra={{ height: '100%', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <SHdr tip={isShareData ? "Breakdown of total market sales by company for the selected year. Your team's slice shows how you rank against all AI competitors." : "How your budget was split across departments in revenue terms for the selected year."} >{isShareData ? 'Market Share %' : 'Dept Revenue Split'}</SHdr>
        {n > 1 && (
          <select value={selectedYear} onChange={e => setSelectedYear(Number(e.target.value))} style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4, marginBottom: 10 }}>
            {yearResults.map((_, i) => <option key={i} value={i}>Year {i + 1}</option>)}
          </select>
        )}
      </div>
      {!isShareData && <div style={{ fontSize: 11, color: '#6A7A8A', marginBottom: 8 }}>Market share breakdown available after Year 1.</div>}
      <div ref={containerRef} style={{ position: 'relative', width: '100%', height: HEIGHT }}>
        <ResponsiveContainer width="100%" height={HEIGHT}>
          <PieChart>
            <Pie
              data={pieData}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={OUTER_R}
              innerRadius={INNER_R}
              label={false}
              labelLine={false}
              startAngle={90}
              endAngle={-270}
            >
              {pieData.map((_, i) => <Cell key={i} fill={pieColors[i % pieColors.length]} />)}
            </Pie>
            <Tooltip formatter={(v, name) => [isShareData ? `${parseFloat(v).toFixed(1)}%` : fmtCur(v, sym, suffix), name]} contentStyle={chartTooltipStyle2} />
          </PieChart>
        </ResponsiveContainer>
        <svg
          style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none', overflow: 'visible' }}
          width={containerWidth}
          height={HEIGHT}
        >
          {customLabels.map((lbl) => {
            const { index, name, value, percent, color, ex, ey, ax, isRight, y } = lbl
            const valTxt = isShareData ? `${value.toFixed(1)}%` : `${(percent * 100).toFixed(0)}%`
            const elbowX = isRight ? ax + ELBOW_LEN : ax - ELBOW_LEN
            const textX = isRight ? elbowX + 4 : elbowX - 4
            return (
              <g key={index}>
                {/* leader: pie edge → angled → elbow → horizontal run */}
                <polyline
                  points={`${ex.toFixed(1)},${ey.toFixed(1)} ${ax.toFixed(1)},${y.toFixed(1)} ${elbowX.toFixed(1)},${y.toFixed(1)}`}
                  fill="none"
                  stroke={color}
                  strokeWidth={1.2}
                  strokeOpacity={0.7}
                />
                <text x={textX} y={y - 4} textAnchor={isRight ? "start" : "end"} fontSize={11} fontWeight={700} fill={color}>{name}</text>
                <text x={textX} y={y + 9} textAnchor={isRight ? "start" : "end"} fontSize={10} fontWeight={500} fill="#6A7A8A">{valTxt}</text>
              </g>
            )
          })}
        </svg>
      </div>
    </C2Card>
  )
}

function ProductEvolutionCard({ yearResults }) {
  const hasSpecs = yearResults.some(yr => yr.product_specs && Object.keys(yr.product_specs).length > 0)
  if (!hasSpecs) {
    return (
      <C2Card>
        <SHdr tip="Key product attributes (e.g. range, efficiency, price) for your vehicle as they evolved year over year. ▲ indicates improvement vs. the prior year.">Product Spec Evolution</SHdr>
        <div style={{ fontSize: 12, color: '#6A7A8A' }}>Product spec data will appear here once included in year results.</div>
      </C2Card>
    )
  }
  const allKeys = [...new Set(yearResults.flatMap(yr => Object.keys(yr.product_specs || {})))]
  return (
    <C2Card>
      <SHdr tip="Key product attributes (e.g. range, efficiency, price) for your vehicle as they evolved year over year. ▲ indicates improvement vs. the prior year.">Product Spec Evolution</SHdr>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{ padding: '5px 8px', fontSize: 10, fontWeight: 600, color: '#6A7A8A', textTransform: 'uppercase', borderBottom: '1px solid #D4DCE8', textAlign: 'left' }}>Spec</th>
              {yearResults.map((_, i) => <th key={i} style={{ padding: '5px 8px', fontSize: 10, fontWeight: 600, color: '#6A7A8A', textTransform: 'uppercase', borderBottom: '1px solid #D4DCE8', textAlign: 'right' }}>Yr{i + 1}</th>)}
            </tr>
          </thead>
          <tbody>
            {allKeys.map(key => (
              <tr key={key} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                <td style={{ padding: '7px 8px', fontSize: 12, fontWeight: 600, color: '#0A1628' }}>{key}</td>
                {yearResults.map((yr, i) => {
                  const val = yr.product_specs?.[key]
                  const prev = i > 0 ? yearResults[i - 1]?.product_specs?.[key] : null
                  const up = prev != null && val > prev
                  return (
                    <td key={i} style={{ padding: '7px 8px', fontFamily: MONO, fontSize: 12, textAlign: 'right', color: up ? '#1A5C3A' : T.t2 }}>
                      {val != null ? (typeof val === 'number' ? val.toFixed(2) : val) : '—'}
                      {up && <span style={{ color: '#1A5C3A', fontSize: 9 }}> ▲</span>}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </C2Card>
  )
}

function SegmentLikabilityCard({ yearResults, scenarioInfo }) {
  const [selectedYear, setSelectedYear] = useState(yearResults.length - 1)
  const yr = yearResults[Math.min(selectedYear, yearResults.length - 1)]
  const likability = yr?.segment_likability
  const segments = scenarioInfo?.segments || []
  const segColors = scenarioInfo?.segment_colors || {}
  if (!likability || !Object.keys(likability).length) {
    return (
      <C2Card>
        <SHdr tip="How appealing each company's product is to each customer segment, scored 0–100. Green >60 means strong appeal, amber 40–60 is moderate, red <40 is weak. Drives which segment buys from whom.">Segment Likability</SHdr>
        <div style={{ fontSize: 12, color: '#6A7A8A' }}>Segment likability data will appear here once computed.</div>
      </C2Card>
    )
  }
  const segKeys = Object.keys(likability)
  const compNames = segKeys.length ? Object.keys(likability[segKeys[0]]) : []
  const defaultSegColors = ['#1A5C3A', '#1A3A6B', '#8A6A10', '#4A2A7A']
  function getSegColor(seg, i) { return segColors[seg] || defaultSegColors[i % defaultSegColors.length] }
  function getSegLabel(seg) { const found = segments.find(s => s.key === seg); return found?.label || seg }
  return (
    <C2Card>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <SHdr tip="How appealing each company's product is to each customer segment, scored 0–100. Green >60 means strong appeal, amber 40–60 is moderate, red <40 is weak. Drives which segment buys from whom.">Segment Likability</SHdr>
        {yearResults.length > 1 && (
          <select value={selectedYear} onChange={e => setSelectedYear(Number(e.target.value))} style={{ fontSize: 11, padding: '3px 8px', borderRadius: 4, marginBottom: 10 }}>
            {yearResults.map((_, i) => <option key={i} value={i}>Year {i + 1}</option>)}
          </select>
        )}
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{ padding: '6px 8px', fontSize: 10, fontWeight: 600, color: '#6A7A8A', textTransform: 'uppercase', borderBottom: '1px solid #D4DCE8', textAlign: 'left' }}>Segment</th>
              {compNames.map(n => <th key={n} style={{ padding: '6px 8px', fontSize: 10, fontWeight: 600, color: '#6A7A8A', textTransform: 'uppercase', borderBottom: '1px solid #D4DCE8', textAlign: 'center' }}>{n.split(' ')[0]}</th>)}
            </tr>
          </thead>
          <tbody>
            {segKeys.map((seg, si) => {
              const col = getSegColor(seg, si)
              return (
                <tr key={seg} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '8px 8px', fontSize: 12, fontWeight: 700, color: col }}>{getSegLabel(seg)}</td>
                  {compNames.map(n => {
                    const v = likability[seg]?.[n] ?? 0
                    const pct = Math.round(v)
                    const bg = v > 60 ? 'rgba(61,153,88,0.12)' : v > 40 ? 'rgba(192,120,56,0.10)' : 'rgba(176,72,72,0.10)'
                    const textCol = v > 60 ? '#1A5C3A' : v > 40 ? '#8A6A10' : '#B03030'
                    return (
                      <td key={n} style={{ padding: '8px 8px', textAlign: 'center' }}>
                        <span style={{ fontFamily: MONO, fontSize: 12, fontWeight: 700, color: textCol, background: bg, padding: '3px 8px', borderRadius: 5, display: 'inline-block' }}>{pct}%</span>
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

function LeaderboardCard({ leaderboard, pin }) {
  if (!leaderboard?.length) return null
  return (
    <C2Card extra={{ height: '100%', boxSizing: 'border-box' }}>
      <SHdr tip="Team ranking by VPI score. Updated after each year is locked by all teams. VPI is equally weighted between risk-adjusted profit (50%) and average market share (50%).">Leaderboard — {pin || 'VPI'}</SHdr>
      {leaderboard.map((entry, i) => (
        <div key={i} className='lb-row' style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            {/* Rank badge per spec */}
            <span style={{
              width: 22, height: 22, display: 'flex', alignItems: 'center', justifyContent: 'center',
              borderRadius: 5, fontSize: 11, fontWeight: 700, fontFamily: MONO,
              background: i === 0 ? 'rgba(91,191,116,0.20)' : '#E0E6EF',
              border: `1px solid ${i === 0 ? 'rgba(91,191,116,0.30)' : '#D4DCE8'}`,
              color: i === 0 ? '#1A5C3A' : T.t3,
            }}>{i + 1}</span>
            <span style={{ fontSize: 13, fontWeight: 600, color: '#0A1628' }}>{entry.team_key || entry.team}</span>
          </div>
          <span style={{ fontFamily: MONO, fontWeight: 700, color: '#1A5C3A', fontSize: 13 }}>
            {(entry.vpi ?? entry.score)?.toFixed(1) || '—'}
          </span>
        </div>
      ))}
    </C2Card>
  )
}

export default function MarketTab({ gameState, scenarioInfo, leaderboard }) {
  const yearResults = gameState?.year_results || []
  const sym    = scenarioInfo?.currency_symbol || '$'
  const suffix = scenarioInfo?.small_number_suffix || 'K'
  const pin    = scenarioInfo?.performance_index_name || 'VPI'
  if (!yearResults.length) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '60px 0' }}>
        <div style={{ background: '#FFFFFF',  border: '1px solid #D4DCE8', borderRadius: 4, padding: '36px 44px', maxWidth: 420, textAlign: 'center' }}>
          <div style={{ width: 52, height: 52, borderRadius: '50%', background: '#F5F7FA', border: '1px solid #D4DCE8', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 18px' }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="9" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5"/>
              <path d="M12 8v4l3 3" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </div>
          <div style={{ fontSize: 15, fontWeight: 700, color: '#3A4A5A', marginBottom: 8 }}>Market Data Unlocks After Year 1</div>
          <div style={{ fontSize: 13, color: '#6A7A8A', lineHeight: 1.7 }}>
            Lock Year 1 to see market share breakdown, competitor profit comparison, and the team leaderboard.
          </div>
        </div>
      </div>
    )
  }
  return (
    <div className="tab-two-col" style={{ display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'stretch' }}>
      <div className="tab-col" style={{ flex: 1, minWidth: 340, display: 'flex', flexDirection: 'column' }}>
        <MarketNarrativeCard yearResults={yearResults} />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <MarketSharePie yearResults={yearResults} sym={sym} suffix={suffix} />
        </div>
      </div>
      <div className="tab-col" style={{ flex: 1, minWidth: 340, display: 'flex', flexDirection: 'column' }}>
        <ProductEvolutionCard yearResults={yearResults} />
        <SegmentLikabilityCard yearResults={yearResults} scenarioInfo={scenarioInfo} />
        <CompetitorProfitChart yearResults={yearResults} sym={sym} suffix={suffix} />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <LeaderboardCard leaderboard={leaderboard} pin={pin} />
        </div>
      </div>
    </div>
  )
}
