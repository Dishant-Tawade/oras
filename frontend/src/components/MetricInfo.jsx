import React, { useState, useRef } from 'react'
import { createPortal } from 'react-dom'

// Metric definitions
export const METRIC_INFO = {
  // Performance Tab
  revenue:          "Total income generated from sales across all market segments this year, before costs are deducted.",
  marketShare:      "Your company's share of total industry sales volume this year, expressed as a percentage. Higher share signals stronger competitive position.",
  netProfit:        "Revenue minus all costs (spend + any penalties) for this year. Negative means you spent more than you earned.",
  profitMargin:     "Net profit as a percentage of revenue. A higher margin means you're keeping more of each dollar earned. Below 10% is a warning sign.",
  budgetUsed:       "Percentage of your available budget that was allocated and spent this year. Leaving more than 15% unspent triggers an underuse penalty.",
  cumulative:       "Sum of all net profits across every completed year so far. The long-run health of your company.",
  strategyMult:     "A multiplier applied to your score based on your sub-decisions (strategic directions). Positive means your choices synergised well; negative means misalignment. Repeating the same choice in consecutive years causes a 30% decay.",
  riskAdjScore:     "Monte Carlo simulation average minus two standard deviations — a conservative estimate of your profit under uncertainty. Penalises volatile strategies even if their average looks good.",
  avgMarketShare:   "Average of your market share percentages across all years completed so far. Used as 50% of your final VPI score.",
  vpi:              "Value Performance Index — your overall score from 0 to 1000+. Equally weighted between risk-adjusted profit (50%) and average market share (50%). This is your primary ranking metric.",
  grade:            "Letter grade derived from your VPI score: S (850+), A (700–849), B (550–699), C (400–549), D (250–399), F (<250).",
  deptSpend:        "Amount of your budget allocated to this department this year.",
  deptReturn:       "Revenue attributed to this department's activity this year. R&D returns are lagged — this year's R&D spend pays off next year.",
  deptEfficiency:   "Return divided by spend for this department. Values above 1.0 mean every dollar invested earned more than a dollar back. Colour-coded: green >2×, amber >1×, red <1×.",
  deptMomentum:     "A 0–4 internal state score representing how much accumulated capability this department has built up. Higher momentum amplifies future returns.",
  // Market Tab
  marketSharePie:   "Breakdown of total market sales by company for the selected year. Your team's slice shows how you rank against all AI competitors.",
  cumulativeProfit: "Running total of net profit over time for your team vs. each competitor. A rising line means consistent profitability; a flat or falling line signals trouble.",
  productSpecs:     "Key product attributes (e.g. range, efficiency, price) for your vehicle as they evolved year over year. ▲ indicates improvement vs. the prior year.",
  segmentLikability:"How appealing each company's product is to each customer segment, scored 0–100. Green >60, amber 40–60, red <40. Drives which segment buys from whom.",
  competitorData:   "Each competitor's profit and market share for the selected year, giving a snapshot of the competitive landscape.",
  leaderboard:      "Team ranking by VPI score. Updated after each year is locked by all teams.",
}

// Renders the tooltip via a portal into document.body so it is never clipped by a parent with
// overflow:hidden (cards, table cells, etc.).
export function InfoTooltip({ metricKey, text }) {
  const [visible, setVisible] = useState(false)
  const [pos, setPos] = useState({ x: 0, y: 0 })
  const btnRef = useRef(null)
  const tip = text || METRIC_INFO[metricKey] || 'No description available.'

  const TIP_W = 224

  function show() {
    if (!btnRef.current) return
    const r = btnRef.current.getBoundingClientRect()
    setPos({
      x: r.left + r.width / 2,
      y: r.top + window.scrollY,
    })
    setVisible(true)
  }

  function hide() { setVisible(false) }

  const tooltip = visible && createPortal(
    <span style={{
      position: 'absolute',
      top: pos.y - 6,
      left: Math.min(pos.x - TIP_W / 2, window.innerWidth - TIP_W - 12),
      transform: 'translateY(-100%)',
      background: '#1A2A3A', color: '#E8EDF4',
      fontSize: 11, lineHeight: 1.55, fontWeight: 400,
      padding: '8px 11px', borderRadius: 6,
      width: TIP_W, boxShadow: '0 4px 16px rgba(0,0,0,0.28)',
      zIndex: 99999, pointerEvents: 'none',
      whiteSpace: 'normal', textAlign: 'left',
    }}>
      {tip}
      <span style={{
        position: 'absolute', top: '100%',
        left: Math.max(10, Math.min(pos.x - Math.min(pos.x - TIP_W / 2, window.innerWidth - TIP_W - 12) - 5, TIP_W - 10)),
        width: 0, height: 0,
        borderLeft: '5px solid transparent',
        borderRight: '5px solid transparent',
        borderTop: '5px solid #1A2A3A',
      }} />
    </span>,
    document.body
  )

  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', marginLeft: 5, verticalAlign: 'middle' }}>
      <span
        ref={btnRef}
        onMouseEnter={show}
        onMouseLeave={hide}
        style={{
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          width: 14, height: 14, borderRadius: '50%',
          background: '#E8EDF4', border: '1px solid #C4CDD8',
          color: '#6A7A8A', fontSize: 9, fontWeight: 700,
          cursor: 'default', flexShrink: 0, lineHeight: 1,
          userSelect: 'none',
        }}
      >?</span>
      {tooltip}
    </span>
  )
}
