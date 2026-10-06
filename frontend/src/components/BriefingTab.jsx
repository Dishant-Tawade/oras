import React, { useState, useEffect } from 'react'
import { api } from '../hooks/useApi'

const DEPT_COLORS = ['#1A3A6B', '#8A6A10', '#1A5C3A', '#4A2A7A']
const DEPT_COLORS_L = ['#80B0D8', '#8A6A10', '#228B57', '#B090D8']
const SEG_COLOR_LIST = ['#1A5C3A', '#1A3A6B', '#8A6A10', '#4A2A7A']
const MONO = "'DM Mono', monospace"
const T = { t1: '#0A1628', t2: '#3A4A5A', t3: '#8090A4' }

function C2Card({ children, extra = {} }) {
  return <div style={{ background: '#FFFFFF', border: '1px solid #D4DCE8', borderRadius: 4, boxShadow: '0 2px 8px rgba(10,22,40,0.10)', padding: '18px 20px', ...extra }}>{children}</div>
}
function SHdr({ children }) {
  return <div className="sec-lbl">{children}</div>
}
function KpiCard({ label, value, accent, sub }) {
  const col = accent || T.t1
  return (
    <div className="kpi-hover" style={{ padding: '10px 12px', borderRadius: 4, background: '#F5F7FA', border: '1px solid #E0E6EF', borderLeft: `3px solid ${col}` }}>
      <div style={{ fontSize: 10, fontWeight: 600, color: '#6A7A8A', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: 16, fontWeight: 700, color: col, fontFamily: MONO, letterSpacing: '-0.5px' }}>{value}</div>
      {sub && <div style={{ fontSize: 10, color: '#6A7A8A', marginTop: 1 }}>{sub}</div>}
    </div>
  )
}

function fmtK(val, sym, suffix) {
  sym = sym || '$'; suffix = suffix || 'K'
  if (!val && val !== 0) return `${sym}0${suffix}`
  const abs = Math.abs(val)
  if (suffix === 'K') return `${sym}${Math.round(abs / 1e3).toLocaleString()}K`
  if (suffix === 'L') { if (abs >= 1e7) return `${sym}${(abs / 1e7).toFixed(1)}Cr`; return `${sym}${Math.round(abs / 1e5).toLocaleString()}L` }
  return `${sym}${(abs / 1e6).toFixed(2)}M`
}


// Renders **bold** markdown inline
function RichText({ text }) {
  if (!text) return null
  const parts = text.split('**')
  return (
    <span>
      {parts.map((part, i) =>
        i % 2 === 1
          ? <strong key={i} style={{ color: '#0A1628', fontWeight: 700 }}>{part}</strong>
          : <span key={i}>{part}</span>
      )}
    </span>
  )
}

function WorldSection({ sb }) {
  if (!sb?.world_body && !sb?.market_body) return null
  return (
    <C2Card>
      <SHdr>Simulation World</SHdr>
      {sb.world_body && <div style={{ fontSize: 13, color: '#3A4A5A', lineHeight: '1.8', marginBottom: 16 }}><RichText text={sb.world_body} /></div>}
      {sb.market_body && <><SHdr>The Market</SHdr><div style={{ fontSize: 13, color: '#3A4A5A', lineHeight: '1.8' }}><RichText text={sb.market_body} /></div></>}
    </C2Card>
  )
}

function SegmentsSection({ segments }) {
  if (!segments?.length) return null
  return (
    <C2Card>
      <SHdr>Consumer Segments</SHdr>
      {segments.map((seg, i) => {
        const col = SEG_COLOR_LIST[i % SEG_COLOR_LIST.length]
        return (
          <div key={seg.key || i} style={{ borderLeft: `3px solid ${col}`, background: `${col}0A`, borderRadius: 4, padding: '12px 14px', marginBottom: 8, border: `1px solid ${col}22`, borderLeftWidth: 3, borderLeftColor: col }}>
            <div style={{ marginBottom: 4, display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <span style={{ fontWeight: 700, fontSize: 13, color: col }}>{seg.label}</span>
              {seg.market_weight > 0 && <span style={{ fontSize: 10, color: '#6A7A8A', fontFamily: MONO }}>{Math.round(seg.market_weight * 100)}% of market</span>}
            </div>
            {seg.description && <div style={{ fontSize: 12, color: '#3A4A5A', lineHeight: '1.6' }}>{seg.description}</div>}
          </div>
        )
      })}
    </C2Card>
  )
}

function CompanySection({ scenario }) {
  const sb = scenario?.storyboard || {}
  const sym = scenario?.currency_symbol || '$'
  const suffix = scenario?.small_number_suffix || 'K'
  const largeSuffix = scenario?.large_number_suffix || 'M'
  const inflMin = scenario?.financials?.inflation_min
  const inflMax = scenario?.financials?.inflation_max
  const inflStr = inflMin != null ? `Inflates ${(inflMin * 100).toFixed(0)}–${(inflMax * 100).toFixed(0)}%/yr` : ''
  return (
    <C2Card extra={{ height: '100%', boxSizing: 'border-box' }}>
      <SHdr>Your Company</SHdr>
      <div style={{ fontSize: 20, fontWeight: 700, color: '#0A1628' }}>{scenario?.company_name}</div>
      {scenario?.company_location && <div style={{ fontSize: 12, color: '#6A7A8A', marginTop: 3, marginBottom: 4 }}>{scenario.company_location}</div>}
      {sb.company_body && <div style={{ fontSize: 13, color: '#3A4A5A', lineHeight: '1.8', marginBottom: 14, marginTop: 8 }}><RichText text={sb.company_body} /></div>}
      {(scenario?.total_budget || scenario?.fixed_costs) && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 8, marginBottom: 10 }}>
          {scenario.fixed_costs > 0 && <KpiCard label="Fixed Costs" value={fmtK(scenario.fixed_costs, sym, suffix)} accent="#B06020" sub={inflStr} />}
          {scenario.total_budget > 0 && <KpiCard label="Starting Budget" value={fmtK(scenario.total_budget, sym, suffix)} accent="#1A6B45" sub="±3% of profit/yr" />}
        </div>
      )}
      {suffix && (
        <div style={{ fontSize: 11, color: '#8A6A10', fontWeight: 600, padding: '6px 10px', background: 'rgba(192,120,56,0.08)', borderRadius: 4, borderLeft: '3px solid rgba(192,120,56,0.40)' }}>
          All monetary values in {sym}...{suffix} ({suffix === 'K' ? 'thousands' : suffix === 'L' ? 'lakhs' : 'millions'}). Example: {sym}60,000{suffix} = {sym}60 {largeSuffix === 'M' ? 'million' : largeSuffix === 'Cr' ? 'crore' : 'billion'}.
        </div>
      )}
    </C2Card>
  )
}

function ProductSection({ scenario }) {
  const sb = scenario?.storyboard || {}
  const sym = scenario?.currency_symbol || '$'
  return (
    <C2Card extra={{ height: '100%', boxSizing: 'border-box' }}>
      <SHdr>The Product</SHdr>
      {scenario?.product_name && <div style={{ fontSize: 17, fontWeight: 700, color: '#0A1628', marginBottom: 8 }}>{scenario.product_name}</div>}
      {sb.product_body && <div style={{ fontSize: 13, color: '#3A4A5A', lineHeight: '1.8', marginBottom: 12 }}><RichText text={sb.product_body} /></div>}
      {(scenario?.unit_price > 0 || scenario?.year1_capacity > 0) && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 8 }}>
          {scenario.unit_price > 0 && <KpiCard label={scenario.unit_price_label || 'Unit Price'} value={`${sym}${scenario.unit_price.toLocaleString()}`} accent="#80B0D8" />}
          {scenario.year1_capacity > 0 && <KpiCard label="Yr 1 Capacity" value={`${scenario.year1_capacity.toLocaleString()} ${scenario.capacity_unit || 'units'}`} accent="#228B57" />}
        </div>
      )}
    </C2Card>
  )
}

function RoleSection({ scenario }) {
  const sb = scenario?.storyboard || {}
  return (
    <C2Card>
      <SHdr>Your Role</SHdr>
      {scenario?.role_title && <div style={{ fontSize: 17, fontWeight: 700, color: '#0A1628', marginBottom: 8 }}>{scenario.role_title}</div>}
      {sb.role_body && <div style={{ fontSize: 13, color: '#3A4A5A', lineHeight: '1.8' }}><RichText text={sb.role_body} /></div>}
    </C2Card>
  )
}

function ObjectiveSection({ scenario }) {
  const sb = scenario?.storyboard || {}
  const pin = scenario?.performance_index_name || 'VPI'
  const piFull = scenario?.performance_index_full || 'Value Performance Index'
  const grades = [['S','#FFD700','850+'],['A','#1A5C3A','700+'],['B','#5B8DEF','550+'],['C','#8A6A10','400+'],['D','#E07C3A','250+'],['F','#B03030','<250']]
  return (
    <C2Card>
      <SHdr>Main Objective</SHdr>
      <div style={{ fontSize: 17, fontWeight: 700, color: '#0A1628', marginBottom: 10 }}>Maximise your {piFull} ({pin})</div>
      {sb.objective_body && <div style={{ fontSize: 13, color: '#3A4A5A', lineHeight: '1.8', marginBottom: 12 }}><RichText text={sb.objective_body} /></div>}
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 4, marginBottom: 10 }}>
        {grades.map(([g, gc, rng]) => (
          <React.Fragment key={g}>
            <span style={{ display: 'inline-block', width: 20, height: 20, borderRadius: 4, background: gc, color: g === 'S' ? '#1a1a2e' : 'white', textAlign: 'center', fontWeight: 800, fontSize: 11, lineHeight: '20px' }}>{g}</span>
            <span style={{ fontFamily: MONO, fontSize: 11, color: '#6A7A8A', marginRight: 6 }}>{rng}</span>
          </React.Fragment>
        ))}
      </div>
      <div style={{ fontSize: 11, color: '#1A5C3A', fontWeight: 600 }}>See the Objective tab for full scoring breakdown, constraints, and department mechanics.</div>
    </C2Card>
  )
}

function DepartmentsSection({ departments, subDecisions, segments, segmentColors, sym, suffix }) {
  const [expanded, setExpanded] = useState({})
  const toggle = (name) => setExpanded(prev => ({ ...prev, [name]: !prev[name] }))
  const segMeta = {}
  ;(segments || []).forEach(seg => { segMeta[seg.key] = { label: seg.label || seg.key, color: (segmentColors || {})[seg.key] || T.t3 } })
  return (
    <C2Card>
      <SHdr>Departments & Strategic Directions</SHdr>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {(departments || []).map((dept, i) => {
          const col = DEPT_COLORS[i % DEPT_COLORS.length]
          const colL = DEPT_COLORS_L[i % DEPT_COLORS_L.length]
          const sd = subDecisions?.[dept.name]
          const sdItems = sd?.options ? Object.entries(sd.options) : []
          const isOpen = !!expanded[dept.name]
          return (
            <div key={dept.name} style={{ background: '#FFFFFF', border: '1px solid #D4DCE8', borderRadius: 4, boxShadow: '0 2px 8px rgba(10,22,40,0.10)', overflow: 'hidden' }}>
              <button
                onClick={() => toggle(dept.name)}
                style={{ width: '100%', display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', background: 'none', border: 'none', borderLeft: `3px solid ${col}`, cursor: 'pointer', textAlign: 'left' }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: colL, marginBottom: 2 }}>{dept.name}</div>
                  {(dept.min_spend > 0 || dept.max_spend > 0) && (
                    <div style={{ fontSize: 10, color: '#6A7A8A', fontFamily: MONO }}>
                      {fmtK(dept.min_spend, sym, suffix)} – {fmtK(dept.max_spend, sym, suffix)}
                      {sdItems.length > 0 && <span style={{ marginLeft: 8 }}>· {sdItems.length} strategies</span>}
                    </div>
                  )}
                </div>
                <svg width="13" height="13" viewBox="0 0 14 14" fill="none" style={{ flexShrink: 0, transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s ease', color: '#6A7A8A' }}>
                  <path d="M2 5L7 10L12 5" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
              {isOpen && (
                <div style={{ padding: '0 16px 16px 20px', borderTop: '1px solid rgba(255,255,255,0.07)' }}>
                  {(dept.background || dept.description) && (
                    <div style={{ fontSize: 12, color: '#3A4A5A', lineHeight: '1.7', margin: '12px 0 10px' }}>{dept.background || dept.description}</div>
                  )}
                  {sdItems.length > 0 && (
                    <div>
                      <div style={{ fontSize: 10, fontWeight: 700, color: '#6A7A8A', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 8, fontFamily: MONO }}>{sd.label || 'Strategic Direction'} — choose one per year</div>
                      {sdItems.map(([key, opt]) => {
                        const mults = opt.segment_multipliers || {}
                        const hasMultipliers = Object.keys(mults).length > 0
                        return (
                          <div key={key} style={{ marginBottom: 8, padding: '10px 12px', borderRadius: 4, background: '#F5F7FA', border: '1px solid #E0E6EF' }}>
                            <div style={{ fontWeight: 700, fontSize: 12, color: colL, marginBottom: 4 }}>{opt.label || key}</div>
                            {opt.description && <div style={{ fontSize: 11, color: '#3A4A5A', lineHeight: '1.6', marginBottom: hasMultipliers ? 8 : 0 }}>{opt.description}</div>}
                            {hasMultipliers && (
                              <div>
                                <div style={{ fontSize: 9, fontWeight: 600, color: '#6A7A8A', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 4, fontFamily: MONO }}>Consumer segment impact:</div>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                                  {Object.entries(mults).map(([seg, mult]) => {
                                    const delta = ((mult - 1) * 100).toFixed(0)
                                    const sign = mult >= 1 ? '+' : ''
                                    const meta = segMeta[seg] || { label: seg, color: '#6A7A8A' }
                                    return (
                                      <span key={seg} style={{ fontSize: 10, fontWeight: 700, fontFamily: MONO, background: `${meta.color}14`, color: meta.color, border: `1px solid ${meta.color}30`, padding: '3px 9px', borderRadius: 5 }}>
                                        {meta.label}: {sign}{delta}%
                                      </span>
                                    )
                                  })}
                                </div>
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </C2Card>
  )
}

function CompetitorsSection({ competitors }) {
  if (!competitors?.length) return null
  return (
    <C2Card>
      <SHdr>Market Competitors</SHdr>
      {competitors.map((comp, i) => (
        <div key={i} style={{ background: '#FFFFFF', border: '1px solid #D4DCE8', borderRadius: 4, boxShadow: '0 2px 8px rgba(10,22,40,0.10)', padding: '12px 14px', marginBottom: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 8, marginBottom: 4 }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#0A1628' }}>{comp.name}</div>
            {comp.archetype && <span className="tag tag-g" style={{ fontSize: 9 }}>{comp.archetype}</span>}
          </div>
          {(comp.industry || comp.location) && (
            <div style={{ fontSize: 11, color: '#6A7A8A', marginBottom: 6 }}>
              {[comp.industry, comp.location, comp.founded ? `Est. ${comp.founded}` : null].filter(Boolean).join('  ·  ')}
            </div>
          )}
          {comp.description && <div style={{ fontSize: 12, color: '#3A4A5A', lineHeight: '1.6' }}>{comp.description}</div>}
          {comp.spending_tendency && (
            <div style={{ fontSize: 11, fontStyle: 'italic', color: '#6A7A8A', marginTop: 6, paddingTop: 6, borderTop: '1px solid rgba(255,255,255,0.07)' }}>
              Known for: {comp.spending_tendency}
            </div>
          )}
        </div>
      ))}
    </C2Card>
  )
}

export default function BriefingTab({ gameState, scenarioInfo: scenarioInfoProp }) {
  const [scenario, setScenario] = useState(scenarioInfoProp || null)
  const [competitors, setCompetitors] = useState([])

  useEffect(() => {
    if (!scenario) api.getScenarioInfo().then(setScenario).catch(() => {})
  }, [])

  useEffect(() => {
    if (gameState?.play_seed) {
      api.getCompetitors(gameState.play_seed).then(d => setCompetitors(d.competitors || [])).catch(() => {})
    }
  }, [gameState?.play_seed])

  if (!scenario) {
    return <div style={{ color: '#6A7A8A', padding: '32px 0', fontSize: 12, fontFamily: MONO }}>Loading briefing...</div>
  }

  const sb = scenario.storyboard || {}
  const departments = scenario.departments || []
  const segments = scenario.segments || []
  const subDecisions = scenario.sub_decisions || {}

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div className="tab-two-col" style={{ display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'stretch' }}>
        {/* Left */}
        <div className="tab-col" style={{ flex: '1', minWidth: 340, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="anim-fade-up anim-d1"><WorldSection sb={sb} /></div>
          {segments.length > 0 && <div className="anim-fade-up anim-d2"><SegmentsSection segments={segments} /></div>}
          <div className="anim-fade-up anim-d3" style={{ display: 'flex', flexDirection: 'column', flex: 1 }}><CompanySection scenario={scenario} /></div>
        </div>
        {/* Right */}
        <div className="tab-col" style={{ flex: '1', minWidth: 340, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="anim-fade-up anim-d1"><RoleSection scenario={scenario} /></div>
          <div className="anim-fade-up anim-d2"><ObjectiveSection scenario={scenario} /></div>
          {competitors.length > 0 && <div className="anim-fade-up anim-d3"><CompetitorsSection competitors={competitors} /></div>}
          <div className="anim-fade-up anim-d4" style={{ display: 'flex', flexDirection: 'column', flex: 1 }}><ProductSection scenario={scenario} /></div>
        </div>
      </div>
      {departments.length > 0 && (
        <div className="anim-fade-up anim-d3">
          <DepartmentsSection departments={departments} subDecisions={subDecisions} segments={segments} segmentColors={scenario?.segment_colors} sym={scenario?.currency_symbol || '$'} suffix={scenario?.small_number_suffix || 'K'} />
        </div>
      )}
    </div>
  )
}
