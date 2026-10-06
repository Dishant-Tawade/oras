import React from 'react'

const MONO = "'DM Mono', monospace"

// Sentiment → visual mapping.
const SENTIMENT_STYLE = {
  positive: {
    color: '#1A5C3A',
    bg:    'rgba(26,92,58,0.05)',
    border:'#C2DDC9',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
        <path d="M5 14l4-4 4 4 6-7" stroke="currentColor" strokeWidth="2"
              strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M14 7h5v5" stroke="currentColor" strokeWidth="2"
              strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
  },
  negative: {
    color: '#B03030',
    bg:    'rgba(176,48,48,0.05)',
    border:'#E6C4C4',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
        <path d="M5 10l4 4 4-4 6 7" stroke="currentColor" strokeWidth="2"
              strokeLinecap="round" strokeLinejoin="round"/>
        <path d="M14 17h5v-5" stroke="currentColor" strokeWidth="2"
              strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    ),
  },
  neutral: {
    color: '#3A4A5A',
    bg:    'rgba(58,74,90,0.04)',
    border:'#D4DCE8',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="2" fill="currentColor"/>
      </svg>
    ),
  },
  warning: {
    color: '#8A6A10',
    bg:    'rgba(184,147,42,0.07)',
    border:'#E5D49A',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
        <path d="M12 3l9 16H3L12 3z" stroke="currentColor" strokeWidth="1.8"
              strokeLinejoin="round" fill="none"/>
        <line x1="12" y1="10" x2="12" y2="14" stroke="currentColor"
              strokeWidth="1.8" strokeLinecap="round"/>
        <circle cx="12" cy="17" r="0.9" fill="currentColor"/>
      </svg>
    ),
  },
}

// YearNarrativePanel — renders a list of sentiment-tagged sentences describing the most recently
// locked year.
export default function YearNarrativePanel({ narrative, year }) {
  if (!narrative || narrative.length === 0) return null

  return (
    <div
      style={{
        background: '#FFFFFF',
        border: '1px solid #D4DCE8',
        borderLeft: '3px solid #B8932A',
        borderRadius: 4,
        padding: '16px 20px',
        marginBottom: 14,
        boxShadow: '0 2px 8px rgba(10,22,40,0.05)',
        animation: 'narrativeIn 320ms ease-out',
      }}
    >
      <div style={{
        display: 'flex', alignItems: 'baseline', justifyContent: 'space-between',
        marginBottom: 10,
      }}>
        <div style={{
          fontSize: 10, color: '#8090A4', fontFamily: MONO,
          letterSpacing: '0.20em', fontWeight: 800, textTransform: 'uppercase',
        }}>
          What just happened?
        </div>
        {year != null && (
          <div style={{
            fontSize: 10, color: '#B8932A', fontFamily: MONO,
            letterSpacing: '0.16em', fontWeight: 700,
          }}>
            YEAR {year}
          </div>
        )}
      </div>

      <ul style={{ listStyle: 'none', margin: 0, padding: 0,
                   display: 'flex', flexDirection: 'column', gap: 8 }}>
        {narrative.map((s, i) => {
          const style = SENTIMENT_STYLE[s.sentiment] || SENTIMENT_STYLE.neutral
          return (
            <li
              key={i}
              style={{
                display: 'flex', alignItems: 'flex-start', gap: 10,
                padding: '8px 12px',
                background: style.bg,
                border: `1px solid ${style.border}`,
                borderRadius: 3,
                animation: `narrativeItemIn 320ms ease-out`,
                animationDelay: `${i * 60}ms`,
                animationFillMode: 'backwards',
              }}
            >
              <span style={{
                color: style.color, flexShrink: 0, display: 'inline-flex',
                alignItems: 'center', marginTop: 1,
              }}>
                {style.icon}
              </span>
              <span style={{
                fontSize: 13, color: '#1A2A3A', lineHeight: 1.5,
              }}>
                {s.text}
              </span>
            </li>
          )
        })}
      </ul>

      <style>{`
        @keyframes narrativeIn {
          from { opacity: 0; transform: translateY(6px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes narrativeItemIn {
          from { opacity: 0; transform: translateX(-4px); }
          to   { opacity: 1; transform: translateX(0); }
        }
      `}</style>
    </div>
  )
}
