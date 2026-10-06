import React from 'react'
import { fmtCur } from './allocate/shared'

const MONO = "'DM Mono', monospace"

const QUARTILE_COLORS = {
  Q1: { bg: '#E7F3EC', border: '#1A5C3A', text: '#1A5C3A', label: 'TOP QUARTILE' },
  Q2: { bg: '#EAF0FA', border: '#1A3A6B', text: '#1A3A6B', label: 'SECOND QUARTILE' },
  Q3: { bg: '#FAF3E0', border: '#8A6A10', text: '#8A6A10', label: 'THIRD QUARTILE' },
  Q4: { bg: '#FAE8E5', border: '#B03030', text: '#B03030', label: 'FOURTH QUARTILE' },
}

function Section({ title, children }) {
  return (
    <div style={{
      background: '#FFFFFF',
      border: '1px solid #D4DCE8',
      borderRadius: 4,
      padding: '18px 22px',
      marginBottom: 14,
    }}>
      <div style={{
        fontSize: 10, fontFamily: MONO, color: '#8090A4',
        letterSpacing: '0.20em', fontWeight: 800,
        textTransform: 'uppercase', marginBottom: 12,
      }}>
        {title}
      </div>
      {children}
    </div>
  )
}

function RankingHero({ ranking, headline }) {
  if (!ranking) return null
  const q = QUARTILE_COLORS[ranking.quartile] || QUARTILE_COLORS.Q3
  return (
    <div style={{
      background: '#FFFFFF',
      border: '1px solid #D4DCE8',
      borderTop: `4px solid ${q.border}`,
      borderRadius: 4,
      padding: '24px 28px',
      marginBottom: 14,
      boxShadow: '0 2px 8px rgba(10,22,40,0.07)',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 20 }}>
        <div style={{ flex: 1 }}>
          <div style={{
            fontSize: 10, color: q.text, fontFamily: MONO,
            letterSpacing: '0.20em', fontWeight: 800, marginBottom: 6,
          }}>
            {q.label}
          </div>
          <div style={{
            fontSize: 20, fontWeight: 700, color: '#0A1628',
            lineHeight: 1.35, marginBottom: 12,
          }}>
            {headline || ''}
          </div>
          <div style={{ display: 'flex', gap: 24, alignItems: 'baseline' }}>
            <div>
              <div style={{ fontSize: 9, color: '#8090A4', fontFamily: MONO, letterSpacing: '0.16em', fontWeight: 700 }}>
                PLACE
              </div>
              <div style={{ fontSize: 28, fontWeight: 900, color: q.text, fontFamily: MONO, lineHeight: 1 }}>
                {ranking.place} <span style={{ fontSize: 14, color: '#8090A4', fontWeight: 700 }}>of {ranking.of}</span>
              </div>
            </div>
            <div>
              <div style={{ fontSize: 9, color: '#8090A4', fontFamily: MONO, letterSpacing: '0.16em', fontWeight: 700 }}>
                PERCENTILE
              </div>
              <div style={{ fontSize: 28, fontWeight: 900, color: q.text, fontFamily: MONO, lineHeight: 1 }}>
                {ranking.percentile}
                <span style={{ fontSize: 14, color: '#8090A4', fontWeight: 700 }}>%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function Trajectory({ trajectory }) {
  if (!trajectory || trajectory.length === 0) return null
  return (
    <Section title="Strategic Trajectory">
      <div className="final-trajectory-grid" style={{
        display: 'grid',
        gridTemplateColumns: `repeat(${trajectory.length}, 1fr)`,
        gap: 10,
      }}>
        {trajectory.map((t, i) => {
          const delta = t.vpi_delta
          const deltaColor = delta == null ? '#8090A4'
                            : delta > 0 ? '#1A5C3A' : delta < 0 ? '#B03030' : '#8090A4'
          return (
            <div key={i} style={{
              background: '#F5F7FA', border: '1px solid #E8ECF3',
              borderRadius: 4, padding: '12px 10px',
              position: 'relative',
            }}>
              <div style={{
                fontSize: 9, fontFamily: MONO, color: '#8090A4',
                letterSpacing: '0.16em', fontWeight: 700, marginBottom: 6,
              }}>
                YEAR {t.year}
              </div>
              <div style={{
                fontSize: 12, fontWeight: 700, color: '#0A1628',
                marginBottom: 4, minHeight: 18,
              }}>
                {t.dominant_dept || '—'}
              </div>
              <div style={{
                fontSize: 20, fontFamily: MONO, fontWeight: 900,
                color: '#1A3A6B', lineHeight: 1,
              }}>
                {t.vpi != null ? t.vpi : '—'}
              </div>
              {delta != null && (
                <div style={{
                  fontSize: 10, fontFamily: MONO, fontWeight: 700,
                  color: deltaColor, marginTop: 4,
                }}>
                  {delta > 0 ? '+' : ''}{delta}
                </div>
              )}
              {t.strategic_shift && (
                <div title="Strategic shift from previous year" style={{
                  position: 'absolute', top: 6, right: 6,
                  width: 16, height: 16, borderRadius: '50%',
                  background: '#B8932A', color: '#FFFFFF',
                  fontSize: 9, fontWeight: 800,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  ⇄
                </div>
              )}
            </div>
          )
        })}
      </div>
      <div style={{
        marginTop: 10, fontSize: 11, color: '#6A7A8A', fontStyle: 'italic',
      }}>
        Each year shows your dominant department and VPI for that year.
        <span style={{ marginLeft: 6, color: '#B8932A', fontWeight: 700 }}>⇄</span> marks years where your strategy shifted.
      </div>
    </Section>
  )
}

function BulletList({ items, color, emptyText }) {
  if (!items || items.length === 0) {
    return (
      <div style={{ fontSize: 12, color: '#8090A4', fontStyle: 'italic' }}>
        {emptyText}
      </div>
    )
  }
  return (
    <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 8 }}>
      {items.map((s, i) => (
        <li key={i} style={{
          display: 'flex', alignItems: 'flex-start', gap: 10,
          fontSize: 13, color: '#1A2A3A', lineHeight: 1.5,
        }}>
          <span style={{
            width: 6, height: 6, borderRadius: '50%', background: color,
            flexShrink: 0, marginTop: 7,
          }}/>
          <span>{s}</span>
        </li>
      ))}
    </ul>
  )
}

// FinalInsights — end-of-session readout.
export default function FinalInsights({ gameState, onContinue, onExit, scenarioInfo }) {
  const yr = gameState?.year_results || []
  const last = yr[yr.length - 1]
  const sym = scenarioInfo?.currency_symbol || '$'
  const suffix = scenarioInfo?.small_number_suffix || 'K'
  const insights = gameState?.final_insights

  const GRADE_COL = { S:'#8A6A10', A:'#1A5C3A', B:'#1A3A6B', C:'#8A6A10', D:'#8A6A10', F:'#8A2020' }
  const kpis = last ? [
    { label:'Final VPI',
      value: last.vpi ?? '—',
      color: GRADE_COL[last.grade] || '#1A3A6B',
      grade: last.grade },
    { label:'Market Share',
      value: last.market_share != null ? `${last.market_share.toFixed(1)}%` : '—',
      color: '#1A3A6B' },
    { label:'Net Profit Y5',
      value: last.profit != null
        ? `${last.profit >= 0 ? '+' : '-'}${fmtCur(Math.abs(last.profit), sym, suffix)}`
        : '—',
      color: last.profit >= 0 ? '#1A5C3A' : '#8A2020' },
  ] : []

  return (
    <div style={{
      minHeight: '100vh', background: '#F0F2F5',
      padding: '40px 20px 60px',
    }}>
      <div style={{ maxWidth: 880, margin: '0 auto' }}>
        {/* Hero — title + checkmark */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{
            width: 56, height: 56, borderRadius: '50%',
            background: '#EAF0FA', border: '2px solid #1A3A6B',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 18px',
          }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M20 6L9 17l-5-5" stroke="#1A3A6B" strokeWidth="2"
                    strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h1 style={{
            fontSize: 28, fontWeight: 900, color: '#0A1628',
            marginBottom: 6, letterSpacing: '-0.01em',
          }}>
            Simulation Complete
          </h1>
          <div style={{ width: 44, height: 3, background: '#B8932A', margin: '0 auto 10px', borderRadius: 2 }}/>
          <p style={{ fontSize: 14, color: '#3A4A5A' }}>
            All 5 years locked — your final readout is below.
          </p>
        </div>

        {/* Ranking hero — only renders if insights computed */}
        <RankingHero ranking={insights?.ranking} headline={insights?.headline}/>

        {/* KPI strip (always shown — same data as before) */}
        {kpis.length > 0 && (
          <div className="final-kpi-grid" style={{
            display: 'grid', gridTemplateColumns: 'repeat(3,1fr)',
            gap: 10, marginBottom: 14,
          }}>
            {kpis.map(k => (
              <div key={k.label} style={{
                background: '#FFFFFF', border: '1px solid #D4DCE8',
                borderTop: `3px solid ${k.color}`, borderRadius: 4,
                padding: '14px', boxShadow: '0 2px 8px rgba(10,22,40,0.06)',
              }}>
                <div style={{
                  fontSize: 9, color: '#8090A4', textTransform: 'uppercase',
                  letterSpacing: '0.16em', fontFamily: MONO, marginBottom: 6,
                }}>
                  {k.label}
                </div>
                <div style={{
                  fontSize: 24, fontWeight: 900, fontFamily: MONO,
                  color: k.color, lineHeight: 1,
                }}>
                  {k.value}
                </div>
                {k.grade && (
                  <div style={{
                    marginTop: 6, display: 'inline-block',
                    background: k.color, color: '#FFFFFF',
                    fontSize: 10, fontWeight: 800,
                    padding: '2px 8px', borderRadius: 3,
                  }}>
                    {k.grade}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Trajectory — only renders if insights computed */}
        <Trajectory trajectory={insights?.trajectory}/>

        {/* Strengths & gaps two-column */}
        {(insights?.strengths?.length || insights?.gaps?.length) && (
          <div className="final-kpi-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
            <Section title="Defining Strengths">
              <BulletList
                items={insights.strengths}
                color="#1A5C3A"
                emptyText="No consistent strengths emerged across the simulation."
              />
            </Section>
            <Section title="Defining Gaps">
              <BulletList
                items={insights.gaps}
                color="#B03030"
                emptyText="No consistent gaps — your performance was balanced across years."
              />
            </Section>
          </div>
        )}

        {/* vs top quartile */}
        {insights?.vs_top_quartile?.length > 0 && (
          <Section title="Compared to Top-Quartile Teams">
            <BulletList
              items={insights.vs_top_quartile}
              color="#8A6A10"
              emptyText=""
            />
          </Section>
        )}

        {/* Action buttons */}
        <div style={{ display: 'flex', gap: 10, justifyContent: 'center', marginTop: 20 }}>
          <button className="btn btn-p" onClick={onContinue} style={{ borderRadius: 3 }}>
            View detailed performance
          </button>
          <button className="btn btn-g" onClick={onExit} style={{ borderRadius: 3 }}>
            Main page
          </button>
        </div>
      </div>
    </div>
  )
}
