import React, { useState, useEffect } from 'react'
import { api } from '../hooks/useApi'

const DEPT_COLORS = ['#1A3A6B', '#8A6A10', '#1A5C3A', '#4A2A7A']
const MONO = "'DM Mono', monospace"
const T = { t1: '#0A1628', t2: '#3A4A5A', t3: '#8090A4' }

function C2Card({ children, extra = {} }) {
  return <div style={{ background: '#FFFFFF', border: '1px solid #D4DCE8', borderRadius: 4, boxShadow: '0 2px 8px rgba(10,22,40,0.10)', padding: '18px 20px', ...extra }}>{children}</div>
}
function SHdr({ children }) {
  return <div className="sec-lbl">{children}</div>
}

function NumberedPoint({ num, color, title, body }) {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', marginBottom: 16 }}>
      <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 24, height: 24, borderRadius: '50%', background: `${color}22`, border: `1px solid ${color}44`, color, fontWeight: 700, fontSize: 11, marginRight: 10, flexShrink: 0, fontFamily: MONO }}>{num}</span>
      <div>
        <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 4, color: '#0A1628' }}>{title}</div>
        <div style={{ fontSize: 13, color: '#3A4A5A', lineHeight: '1.8' }}>{body}</div>
      </div>
    </div>
  )
}

function GradeScale({ pinName }) {
  const rows = [
    ['S','850+', 'Exceptional — optimal allocation & strategy synergy','#FFD700'],
    ['A','700–849','Strong — well-balanced resource decisions',          '#1A5C3A'],
    ['B','550–699','Solid — good fundamentals, room to optimise',       '#5B8DEF'],
    ['C','400–549','Average — missed key allocation trade-offs',        '#8A6A10'],
    ['D','250–399','Weak — significant resource misallocation',         '#E07C3A'],
    ['F','<250',   'Failing — critical under-investment or poor strategy','#B03030'],
  ]
  return (
    <div style={{ background: '#FFFFFF', border: '1px solid #D4DCE8', borderRadius: 4, boxShadow: '0 2px 8px rgba(10,22,40,0.10)', padding: '14px 16px', marginBottom: 14 }}>
      <div className="sec-lbl">{pinName} Grade Scale</div>
      {rows.map(([g, rng, desc, gc]) => (
        <div key={g} style={{ display: 'flex', alignItems: 'center', marginBottom: 6 }}>
          <span style={{ display: 'inline-block', width: 22, height: 22, borderRadius: 4, background: gc, color: g === 'S' ? '#1a1a2e' : 'white', textAlign: 'center', fontWeight: 800, fontSize: 11, lineHeight: '22px', marginRight: 10 }}>{g}</span>
          <span style={{ fontFamily: MONO, fontSize: 11, color: '#6A7A8A', marginRight: 12, width: 66, display: 'inline-block' }}>{rng}</span>
          <span style={{ fontSize: 11, color: '#3A4A5A' }}>{desc}</span>
        </div>
      ))}
    </div>
  )
}

function InfoLine({ label, value }) {
  return <div style={{ fontSize: 13, marginBottom: 8, color: '#3A4A5A' }}><span style={{ fontWeight: 700, color: '#0A1628' }}>{label}</span> {value}</div>
}
function ConstraintRow({ label, color, body }) {
  return (
    <div style={{ fontSize: 13, lineHeight: '1.8', marginBottom: 10 }}>
      <span style={{ fontWeight: 700, color: color || T.t1 }}>{label}</span>
      <span style={{ color: '#3A4A5A' }}>{body}</span>
    </div>
  )
}

function GoalSection({ scenario, departments }) {
  const pin = scenario?.performance_index_name || 'VPI'
  const piFull = scenario?.performance_index_full || 'Value Performance Index'
  const numPeriods = 5
  const deptNames = departments.map(d => d.name)
  const deptStr = deptNames.length > 1
    ? deptNames.slice(0,-1).join(', ') + `, and ${deptNames[deptNames.length-1]}`
    : deptNames[0] || 'departments'
  return (
    <C2Card>
      <SHdr>Your Goal</SHdr>
      <div style={{ fontSize: 13, color: '#3A4A5A', lineHeight: '1.8', marginBottom: 12 }}>
        You are the {scenario?.company?.role_title || 'Chief Resource Officer'} at {scenario?.company_name}. Over {numPeriods} years, you allocate the company's annual operating budget across {deptNames.length} departments ({deptStr}) and choose a strategic direction for each department every year.
      </div>
      <div style={{ fontSize: 13, color: '#3A4A5A', lineHeight: '1.8' }}>
        Your objective is to maximise the {piFull} ({pin}), a composite score that measures how well you balance profitability and market position. The simulation ends after Year {numPeriods}, and your final {pin} determines your grade.
      </div>
    </C2Card>
  )
}

function ScoringSection({ scenario }) {
  const pin = scenario?.performance_index_name || 'VPI'
  const piFull = scenario?.performance_index_full || 'Value Performance Index'
  const mkt = scenario?.market_label || 'the market'
  return (
    <C2Card>
      <SHdr>{pin} Scoring</SHdr>
      <div style={{ fontSize: 13, color: '#3A4A5A', lineHeight: '1.8', marginBottom: 14 }}>
        The {piFull} ({pin}) is scored from 0 to 1000+ based on two equally weighted components:
      </div>
      <NumberedPoint num="1" color="#1A6B45" title="Risk-Adjusted Profit (50%)" body="Consistent earnings score higher than volatile boom-and-bust results, even if the average is the same. If your profit swings wildly between years, the volatility penalty drags your score down." />
      <NumberedPoint num="2" color="#80B0D8" title="Market Share (50%)" body={`Your average share of ${mkt} across all 5 years. Market share is driven by product appeal, market reach shaped by your strategic sub-decisions, and brand equity accumulated from sustained investment.`} />
      <GradeScale pinName={pin} />
      <div style={{ fontSize: 13, color: '#3A4A5A', lineHeight: '1.8' }}>
        Scores can exceed 1000 for truly exceptional performance. The {pin} updates after every locked year.
      </div>
    </C2Card>
  )
}

function BudgetSection({ scenario }) {
  return (
    <C2Card>
      <SHdr>Budget Constraints</SHdr>
      <div style={{ marginBottom: 12 }}>
        <InfoLine label="Starting Budget:" value="Set per scenario, displayed on the Briefing tab" />
        <InfoLine label="Budget Growth:" value="3% of prior year's profit is added (or subtracted if a loss) to the next year's budget" />
        <InfoLine label="Fixed Costs:" value={`Inflate ${scenario?.financials?.inflation_min ? (scenario.financials.inflation_min*100).toFixed(0) : '2'}–${scenario?.financials?.inflation_max ? (scenario.financials.inflation_max*100).toFixed(0) : '5'}% annually`} />
      </div>
      <div style={{ fontWeight: 700, fontSize: 12, color: '#0A1628', marginBottom: 10, fontFamily: MONO, textTransform: 'uppercase', letterSpacing: '0.1em' }}>Key Constraints</div>
      <ConstraintRow label="±30% Rate-of-Change Cap " color="#B06020" body="Each department's budget can only change by ±30% from the previous year. Year 1 decisions are strategically important." />
      <ConstraintRow label="Underuse Penalty " color="#B03030" body="Leaving more than 15% of your budget unallocated triggers a progressive financial penalty." />
      <ConstraintRow label="Minimum Spend Inflation " color={T.t1} body="Each department has a minimum required budget that inflates with costs each year." />
      <ConstraintRow label="Overspend Diminishing Returns " color="#80B0D8" body="Each department has a sweet spot. Spending beyond it yields diminishing returns." />
      <ConstraintRow label="Operations Over-Capacity Penalty " color="#228B57" body="If Operations is massively over-funded relative to Sales, the excess capacity is wasted." />
    </C2Card>
  )
}

function DeptMechanicsSection({ departments }) {
  const deptNames = departments.map(d => d.name)
  const opsName = deptNames[2] || 'Operations'
  const salesName = deptNames[1] || 'Sales'
  return (
    <C2Card>
      <SHdr>Department Mechanics</SHdr>
      {departments.map((dept, i) => (
        <div key={dept.name} style={{ fontSize: 13, lineHeight: '1.8', marginBottom: 12 }}>
          <span style={{ fontWeight: 700, color: DEPT_COLORS[i % DEPT_COLORS.length], fontSize: 13 }}>{dept.name}</span>
          <span style={{ color: '#3A4A5A' }}> {dept.description || dept.background || ''}</span>
        </div>
      ))}
      <div style={{ padding: '12px 14px', background: 'rgba(61,122,88,0.08)', borderRadius: 4, borderLeft: '3px solid rgba(61,122,88,0.40)', marginTop: 10 }}>
        <div style={{ fontWeight: 700, fontSize: 12, color: '#1A5C3A', marginBottom: 6 }}>{opsName} ↔ {salesName} two-way coupling</div>
        <div style={{ fontSize: 12, color: '#3A4A5A', lineHeight: '1.6' }}>
          Under-invest in {opsName} and it caps {salesName} delivery. Over-invest in {opsName} far beyond {salesName} and the excess capacity is wasted (severe penalty kicks in beyond 150% of {salesName} returns).
        </div>
      </div>
    </C2Card>
  )
}

function StrategySection() {
  const points = [
    ['Revenue Ceiling', 'Some strategies raise the maximum revenue a department can generate while others lower it in exchange for easier returns.'],
    ['Investment Difficulty', 'Some strategies require heavier investment before returns materialise. A strategy with a high ceiling but high difficulty is a high-risk, high-reward bet.'],
    ['Synergies', 'Certain strategies in one department grant bonuses to other departments. Aligning department strategies compounds returns.'],
    ['Diminishing Synergy Returns', 'Synergy bonuses decay by 30% for each consecutive year with the same sub-decision. Year 1 grants full bonus, Year 2 grants 70%, Year 3 grants 49%.'],
    ['Segment Impact', 'Each strategy option shows its impact on consumer segments. Positive indicators mean that segment responds well.'],
  ]
  return (
    <C2Card extra={{ height: '100%', boxSizing: 'border-box' }}>
      <SHdr>Strategic Directions & Synergies</SHdr>
      <div style={{ fontSize: 13, color: '#3A4A5A', lineHeight: '1.8', marginBottom: 12 }}>
        Each year, you choose a strategic direction for every department. These sub-decisions modify the department's own return curve and can create cross-department synergy bonuses.
      </div>
      {points.map(([label, body]) => (
        <div key={label} style={{ fontSize: 13, lineHeight: '1.8', marginBottom: 8 }}>
          <span style={{ fontWeight: 700, color: '#0A1628' }}>{label} </span>
          <span style={{ color: '#3A4A5A' }}>{body}</span>
        </div>
      ))}
      <div style={{ padding: '12px 14px', background: 'rgba(176,96,32,0.06)', borderRadius: 4, borderLeft: '3px solid rgba(176,96,32,0.30)', marginTop: 12 }}>
        <div style={{ fontWeight: 700, fontSize: 12, color: '#8A6A10', marginBottom: 6 }}>Sub-decision effects COMPOUND</div>
        <div style={{ fontSize: 12, color: '#3A4A5A', lineHeight: '1.8' }}>
          When all departments are aligned, segment modifiers compound — if three departments penalise the same segment, the combined effect can reduce revenue from that group by 50% or more. Conversely, aligning multiple departments toward the same segment creates a powerful compounding bonus.
        </div>
      </div>
    </C2Card>
  )
}

function NewsSection() {
  return (
    <C2Card>
      <SHdr>News Events & External Shocks</SHdr>
      <div style={{ fontSize: 13, color: '#3A4A5A', lineHeight: '1.8', marginBottom: 12 }}>
        Each year, 1–2 department-targeted news events occur. These temporarily modify a specific department's return characteristics for that year only.
      </div>
      <div style={{ fontSize: 13, lineHeight: '1.8', marginBottom: 8 }}>
        <span style={{ fontWeight: 700, color: '#8A2020' }}>Negative events </span>
        <span style={{ color: '#3A4A5A' }}>make a department harder to earn returns from and/or lower its revenue ceiling.</span>
      </div>
      <div style={{ fontSize: 13, lineHeight: '1.8' }}>
        <span style={{ fontWeight: 700, color: '#1A5C3A' }}>Positive events </span>
        <span style={{ color: '#3A4A5A' }}>make a department temporarily more efficient. Adaptive reallocation in response to events separates good players from great ones.</span>
      </div>
    </C2Card>
  )
}

function PrinciplesSection() {
  const principles = [
    ['Year 1 matters more than you think', 'The rate-of-change cap means your initial allocation shapes all future years.'],
    ['Read the department descriptions carefully', 'Not all departments work the same way. Some have delayed effects, some cap other departments.'],
    ['Sub-decisions should be aligned', 'Conflicting strategies across departments cancel each other out.'],
    ['Consistency beats volatility', 'The scoring formula penalises profit swings. Steady growth scores higher than alternating huge profits and losses.'],
    ['Watch the news', 'External events change which departments need more or less investment.'],
    ["Don't ignore any department entirely", 'Every department has a minimum threshold below which returns collapse.'],
  ]
  return (
    <C2Card extra={{ height: '100%', boxSizing: 'border-box' }}>
      <SHdr>Strategy Principles</SHdr>
      <div style={{ fontSize: 13, color: '#3A4A5A', lineHeight: '1.8', marginBottom: 12 }}>Every scenario is different, but experienced players tend to keep these principles in mind:</div>
      {principles.map(([label, body]) => (
        <div key={label} style={{ fontSize: 13, lineHeight: '1.8', marginBottom: 8 }}>
          <span style={{ fontWeight: 700, color: '#0A1628' }}>{label} </span>
          <span style={{ color: '#3A4A5A' }}>{body}</span>
        </div>
      ))}
    </C2Card>
  )
}

export default function ObjectiveTab({ scenarioInfo: scenarioInfoProp }) {
  const [scenario, setScenario] = useState(scenarioInfoProp || null)
  useEffect(() => { if (!scenario) api.getScenarioInfo().then(setScenario).catch(() => {}) }, [])
  if (!scenario) return <div style={{ color: '#6A7A8A', padding: '32px 0', fontSize: 12, fontFamily: MONO }}>Loading objective...</div>
  const departments = scenario.departments || []
  return (
    <div className="tab-two-col" style={{ display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'stretch' }}>
      <div className="tab-col" style={{ flex: '1', minWidth: 340, display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div className="anim-fade-up anim-d1"><GoalSection scenario={scenario} departments={departments} /></div>
        <div className="anim-fade-up anim-d2"><ScoringSection scenario={scenario} /></div>
        <div className="anim-fade-up anim-d3"><NewsSection /></div>
        <div className="anim-fade-up anim-d4" style={{ display: 'flex', flexDirection: 'column', flex: 1 }}><PrinciplesSection /></div>
      </div>
      <div className="tab-col" style={{ flex: '1', minWidth: 340, display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div className="anim-fade-up anim-d1"><BudgetSection scenario={scenario} /></div>
        {departments.length > 0 && <div className="anim-fade-up anim-d2"><DeptMechanicsSection departments={departments} /></div>}
        <div className="anim-fade-up anim-d3" style={{ display: 'flex', flexDirection: 'column', flex: 1 }}><StrategySection /></div>
      </div>
    </div>
  )
}
