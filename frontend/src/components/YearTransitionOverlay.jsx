import React, { useEffect, useState } from 'react'

// YearTransitionOverlay — full-screen flourish when a new year starts.
export default function YearTransitionOverlay({ year, subtitle, onComplete, persist = false, lockProgress = { locked: 0, total: 0 } }) {
  // We render in three phases to drive the CSS animation: enter — opacity 0→1, year text scales from 0.7
  // → 1 hold — full opacity, year settled leave.
  const [phase, setPhase] = useState('enter')

  // [YT-DIAG] Confirms the overlay actually mounts/renders for each year.
  // Remove once the year-on-year animation is confirmed working.
  console.log('[YT] overlay render — year=%s persist=%s phase=%s', year, persist, phase)

  // Enter → hold (always runs regardless of persist)
  useEffect(() => {
    const t = setTimeout(() => setPhase('hold'), 350)
    return () => clearTimeout(t)
  }, [])

  // Stable ref for onComplete so timer_tick re-renders in the parent (which create a new inline arrow
  // function every render) don't reset the leave timers on every second.
  const onCompleteRef = React.useRef(onComplete)
  useEffect(() => { onCompleteRef.current = onComplete }, [onComplete])

  // Hold → leave → onComplete: only runs when persist is false AND we're in hold
  useEffect(() => {
    if (persist || phase !== 'hold') return
    const t1 = setTimeout(() => setPhase('leave'), 1500)
    const t2 = setTimeout(() => onCompleteRef.current?.(), 1900)
    return () => { clearTimeout(t1); clearTimeout(t2) }
  }, [persist, phase])

  const overlayOpacity = phase === 'leave' ? 0 : 1
  const yearScale      = phase === 'enter' ? 0.7 : 1
  const yearOpacity    = phase === 'enter' ? 0 : 1

  return (
    <div
      aria-hidden="true"
      style={{
        position: 'fixed', inset: 0,
        background: 'radial-gradient(ellipse at center, #0F1F38 0%, #050B17 100%)',
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        zIndex: 9000, // above tab content, below toasts/modals
        opacity: overlayOpacity,
        transition: 'opacity 380ms ease-out',
        pointerEvents: 'none', // never block clicks — animation is purely decorative
      }}
    >
      {/* Top eyebrow */}
      <div
        style={{
          fontSize: 10, color: 'rgba(212,170,64,0.85)',
          fontFamily: "'DM Mono', monospace",
          letterSpacing: '0.28em', fontWeight: 800,
          marginBottom: 18,
          opacity: yearOpacity,
          transition: 'opacity 320ms ease-out 80ms',
        }}
      >
        ADVANCING TO
      </div>

      {/* Large year text */}
      <div
        style={{
          fontSize: 96, color: '#FFFFFF',
          fontWeight: 900, lineHeight: 1,
          letterSpacing: '-0.02em',
          fontFamily: 'system-ui, -apple-system, sans-serif',
          transform: `scale(${yearScale})`,
          opacity: yearOpacity,
          transition: 'transform 480ms cubic-bezier(0.16, 1, 0.3, 1), opacity 360ms ease-out',
          textShadow: '0 4px 24px rgba(212,170,64,0.30)',
        }}
      >
        YEAR {year}
      </div>

      {/* Gold accent line */}
      <div
        style={{
          width: phase === 'enter' ? 0 : 80,
          height: 3, background: '#D4AA40',
          borderRadius: 2, marginTop: 14,
          transition: 'width 520ms cubic-bezier(0.16, 1, 0.3, 1) 180ms',
        }}
      />

      {/* Subtitle / waiting status */}
      <div
        style={{
          fontSize: persist ? 18 : 14,
          color: persist ? 'rgba(255,255,255,0.80)' : 'rgba(255,255,255,0.65)',
          marginTop: 22, fontWeight: 500, letterSpacing: '0.02em',
          opacity: phase === 'enter' ? 0 : 1,
          transform: phase === 'enter' ? 'translateY(6px)' : 'translateY(0)',
          transition: 'opacity 400ms ease-out 220ms, transform 400ms ease-out 220ms',
          textAlign: 'center',
          lineHeight: 1.5,
        }}
      >
        {persist ? (
          lockProgress.total > 0 ? (
            <>
              <span style={{ color: '#D4AA40', fontWeight: 700 }}>{lockProgress.locked}</span>
              <span style={{ color: 'rgba(255,255,255,0.55)' }}> of </span>
              <span style={{ color: '#FFFFFF', fontWeight: 700 }}>{lockProgress.total}</span>
              {' '}teams locked in
              {lockProgress.total - lockProgress.locked > 0 && (
                <> · waiting for{' '}
                  <span style={{ color: '#D4AA40', fontWeight: 700 }}>
                    {lockProgress.total - lockProgress.locked}
                  </span> more
                </>
              )}
            </>
          ) : 'Waiting for other teams to lock in…'
        ) : (subtitle || 'Market outcomes calculated')}
      </div>

      {/* Animated waiting dots — only shown while persisting */}
      {persist && (
        <div style={{ display: 'flex', gap: 6, marginTop: 20,
                      opacity: phase === 'enter' ? 0 : 1,
                      transition: 'opacity 400ms ease-out 400ms' }}>
          {[0, 160, 320].map(delay => (
            <span key={delay} style={{
              width: 7, height: 7, borderRadius: '50%',
              background: '#D4AA40', display: 'inline-block',
              animation: `bounceDot 1.2s ${delay}ms ease-in-out infinite`,
            }} />
          ))}
        </div>
      )}
    </div>
  )
}
