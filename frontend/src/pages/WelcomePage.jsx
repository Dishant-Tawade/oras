import React, { useEffect, useRef, useState } from 'react'

// Animated market data ticker strip
const TICKERS = [
  { sym: 'R&D', val: '+18.4%', up: true },
  { sym: 'OPS', val: '+7.2%', up: true },
  { sym: 'MKT', val: '+12.9%', up: true },
  { sym: 'SLS', val: '-3.1%', up: false },
  { sym: 'VPI', val: '847', up: true },
  { sym: 'YR3', val: '$52.4M', up: true },
  { sym: 'SHARE', val: '8.4%', up: true },
  { sym: 'MARGIN', val: '22.1%', up: true },
  { sym: 'CAPEX', val: '$18.2M', up: false },
  { sym: 'EBITDA', val: '+31%', up: true },
]

function Ticker() {
  return (
    <div style={{ overflow: 'hidden', borderTop: '1px solid #D4DCE8', borderBottom: '1px solid #D4DCE8', background: '#F5F7FA', height: 32, display: 'flex', alignItems: 'center' }}>
      <div style={{ display: 'flex', animation: 'tickerScroll 20s linear infinite', whiteSpace: 'nowrap', gap: 0 }}>
        {[...TICKERS, ...TICKERS, ...TICKERS].map((t, i) => (
          <span key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '0 24px', fontSize: 11, fontFamily: "'DM Mono',monospace", fontWeight: 600, borderRight: '1px solid rgba(13,31,60,0.08)' }}>
            <span style={{ color: '#6A7A8A', letterSpacing: '0.08em' }}>{t.sym}</span>
            <span style={{ color: t.up ? '#1A5C3A' : '#B03030' }}>{t.val}</span>
            <span style={{ fontSize: 8, color: t.up ? '#1A5C3A' : '#B03030' }}>{t.up ? '▲' : '▼'}</span>
          </span>
        ))}
      </div>
      <style>{`@keyframes tickerScroll{from{transform:translateX(0)}to{transform:translateX(-33.33%)}}`}</style>
    </div>
  )
}

// Animated counter
function Counter({ target, prefix = '', suffix = '', delay = 0, duration = 1800 }) {
  const [val, setVal] = useState(0)
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const t = setTimeout(() => {
      setVisible(true)
      const start = Date.now()
      const tick = () => {
        const p = Math.min((Date.now() - start) / duration, 1)
        const ease = 1 - Math.pow(1 - p, 3)
        setVal(Math.round(target * ease))
        if (p < 1) requestAnimationFrame(tick)
      }
      requestAnimationFrame(tick)
    }, delay)
    return () => clearTimeout(t)
  }, [target, delay, duration])
  return (
    <span style={{ opacity: visible ? 1 : 0, transition: 'opacity 0.3s' }}>
      {prefix}{val.toLocaleString()}{suffix}
    </span>
  )
}

// Floating particle
function Particle({ x, y, delay, duration }) {
  return (
    <div style={{
      position: 'absolute', left: `${x}%`, top: `${y}%`,
      width: 3, height: 3, borderRadius: '50%',
      background: 'rgba(184,147,42,0.35)',
      animation: `particleDrift ${duration}s ${delay}s ease-in infinite`,
      pointerEvents: 'none',
    }} />
  )
}

// Main WelcomePage
export default function WelcomePage({ onEnter }) {
  const canvasRef = useRef(null)
  const [phase, setPhase] = useState(0) // 0=loading, 1=lines, 2=wordmark, 3=full

  useEffect(() => {
    const t1 = setTimeout(() => setPhase(1), 200)
    const t2 = setTimeout(() => setPhase(2), 900)
    const t3 = setTimeout(() => setPhase(3), 1600)
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3) }
  }, [])

  // Canvas: animated connection lines between nodes
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    let raf

    const resize = () => {
      canvas.width = canvas.offsetWidth
      canvas.height = canvas.offsetHeight
    }
    resize()
    window.addEventListener('resize', resize)

    const nodes = Array.from({ length: 18 }, (_, i) => ({
      x: (Math.random() * 0.85 + 0.075) * canvas.width,
      y: (Math.random() * 0.85 + 0.075) * canvas.height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      r: Math.random() * 2 + 1.5,
    }))

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // Move nodes
      nodes.forEach(n => {
        n.x += n.vx; n.y += n.vy
        if (n.x < 40 || n.x > canvas.width - 40) n.vx *= -1
        if (n.y < 40 || n.y > canvas.height - 40) n.vy *= -1
      })

      // Draw edges
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[i].x - nodes[j].x
          const dy = nodes[i].y - nodes[j].y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < 160) {
            const alpha = (1 - dist / 160) * 0.12
            ctx.strokeStyle = `rgba(26,58,107,${alpha})`
            ctx.lineWidth = 0.8
            ctx.beginPath()
            ctx.moveTo(nodes[i].x, nodes[i].y)
            ctx.lineTo(nodes[j].x, nodes[j].y)
            ctx.stroke()
          }
        }
      }

      // Draw nodes
      nodes.forEach(n => {
        ctx.beginPath()
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2)
        ctx.fillStyle = 'rgba(26,58,107,0.30)'
        ctx.fill()
      })

      raf = requestAnimationFrame(draw)
    }
    draw()
    return () => { cancelAnimationFrame(raf); window.removeEventListener('resize', resize) }
  }, [])

  const particles = Array.from({ length: 12 }, (_, i) => ({
    x: 10 + i * 8, y: 20 + (i % 3) * 20,
    delay: i * 0.4, duration: 4 + i * 0.3,
  }))

  return (
    <div style={{ minHeight: '100vh', background: '#F0F2F5', display: 'flex', flexDirection: 'column', position: 'relative', overflow: 'hidden', zIndex: 2 }}>

      {/* Canvas background */}
      <canvas ref={canvasRef} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none', zIndex: 0 }} />

      {/* Floating particles */}
      {particles.map((p, i) => <Particle key={i} {...p} />)}

      {/* Gold top border */}
      <div style={{ height: 3, background: 'linear-gradient(90deg, transparent, #B8932A 30%, #D4AA40 50%, #B8932A 70%, transparent)', flexShrink: 0, position: 'relative', zIndex: 2 }} />

      {/* Ticker */}
      <div style={{ position: 'relative', zIndex: 2 }}>
        <Ticker />
      </div>

      {/* Main content */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '40px 24px', position: 'relative', zIndex: 2 }}>

        {/* Auxi Studios */}
        <div style={{ marginBottom: 44, opacity: phase >= 1 ? 1 : 0, transition: 'opacity 0.6s ease', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '16px 32px', background: '#FFFFFF', border: '1px solid #D4DCE8', borderRadius: 14, boxShadow: '0 4px 24px rgba(10,22,40,0.10), 0 1px 4px rgba(10,22,40,0.06)' }}>
            <img src="/auxi-logo.png" alt="Auxi Studios" style={{ height: 48, filter: 'brightness(0) opacity(0.85)' }} />
            <div style={{ width: 1, height: 38, background: '#D4DCE8' }} />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <span style={{ fontSize: 22, fontWeight: 900, letterSpacing: '0.18em', color: '#0A1628', fontFamily: "'DM Mono',monospace", textTransform: 'uppercase', lineHeight: 1 }}>AUXI</span>
              <span style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.38em', color: '#8090A4', fontFamily: "'DM Mono',monospace", textTransform: 'uppercase' }}>STUDIOS</span>
            </div>
          </div>
          <div style={{ fontSize: 10, letterSpacing: '0.18em', color: '#A0AABA', fontFamily: "'DM Mono',monospace", textTransform: 'uppercase' }}>Presents</div>
        </div>

        {/* Decorative lines */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 28, opacity: phase >= 1 ? 1 : 0, transition: 'opacity 0.5s ease' }}>
          <div style={{ height: 1, background: 'linear-gradient(90deg, transparent, #B8932A)', width: phase >= 1 ? 80 : 0, transition: 'width 0.8s ease 0.3s', }} />
          <div style={{ width: 6, height: 6, background: '#B8932A', borderRadius: '50%', transform: phase >= 2 ? 'scale(1)' : 'scale(0)', transition: 'transform 0.4s ease 0.8s' }} />
          <div style={{ height: 1, background: 'linear-gradient(90deg, #B8932A, transparent)', width: phase >= 1 ? 80 : 0, transition: 'width 0.8s ease 0.3s' }} />
        </div>

        {/* ORAS wordmark — cinematic reveal */}
        <div style={{ textAlign: 'center', marginBottom: 16 }}>
          <h1 style={{
            fontFamily: "'DM Sans', sans-serif",
            fontSize: 'clamp(72px, 14vw, 140px)',
            fontWeight: 900,
            letterSpacing: phase >= 2 ? '0.15em' : '0.5em',
            color: '#0A1628',
            lineHeight: 1,
            opacity: phase >= 2 ? 1 : 0,
            transition: 'opacity 0.8s ease 0.2s, letter-spacing 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.2s',
            textShadow: '0 2px 20px rgba(10,22,40,0.08)',
            position: 'relative',
          }}>
            ORAS
            {/* Shimmer overlay on the text */}
            <span style={{
              position: 'absolute', inset: 0,
              background: 'linear-gradient(105deg, transparent 40%, rgba(255,255,255,0.7) 50%, transparent 60%)',
              backgroundSize: '200% 100%',
              animation: phase >= 3 ? 'shimmer 3s ease 0.5s 1 forwards' : 'none',
              WebkitBackgroundClip: 'text',
              backgroundClip: 'text',
              pointerEvents: 'none',
            }} aria-hidden />
          </h1>

          {/* Gold underline */}
          <div style={{
            height: 3, borderRadius: 2,
            background: 'linear-gradient(90deg, transparent, #B8932A, #D4AA40, #B8932A, transparent)',
            width: phase >= 3 ? '100%' : '0%',
            transition: 'width 0.9s cubic-bezier(0.16, 1, 0.3, 1) 0.4s',
            margin: '10px auto 0',
          }} />
        </div>

        {/* Tagline */}
        <p style={{
          fontSize: 15, fontWeight: 500, letterSpacing: '0.22em',
          color: '#6A7A8A', textTransform: 'uppercase',
          fontFamily: "'DM Mono',monospace",
          opacity: phase >= 3 ? 1 : 0,
          transform: phase >= 3 ? 'translateY(0)' : 'translateY(10px)',
          transition: 'opacity 0.6s ease 0.7s, transform 0.6s ease 0.7s',
          marginBottom: 56,
        }}>
          Resource Allocation Simulator
        </p>

        {/* Stats row */}
        <div style={{
          display: 'flex', gap: 2, marginBottom: 52,
          opacity: phase >= 3 ? 1 : 0,
          transform: phase >= 3 ? 'translateY(0)' : 'translateY(20px)',
          transition: 'opacity 0.6s ease 0.9s, transform 0.6s ease 0.9s',
        }}>
          {[
            { label: 'Simulation Years', target: 5, suffix: '' },
            { label: 'Departments', target: 4, suffix: '' },
            { label: 'Scenarios', target: 20, suffix: '+' },
            { label: 'Decision Points', target: 40, suffix: '+' },
          ].map((s, i) => (
            <div key={i} style={{ padding: '18px 28px', background: '#F5F7FA', border: '1px solid #D4DCE8', borderRadius: i === 0 ? '10px 0 0 10px' : i === 3 ? '0 10px 10px 0' : 0, borderRight: i < 3 ? 'none' : '1px solid #D8E0EC', textAlign: 'center', minWidth: 120, boxShadow: '0 2px 8px rgba(13,31,60,0.06)' }}>
              <div style={{ fontSize: 28, fontWeight: 900, fontFamily: "'DM Mono',monospace", color: '#0A1628', lineHeight: 1 }}>
                {phase >= 3 ? <Counter target={s.target} suffix={s.suffix} delay={i * 120 + 900} /> : '0'}
              </div>
              <div style={{ fontSize: 10, color: '#6A7A8A', letterSpacing: '0.12em', textTransform: 'uppercase', marginTop: 5, fontFamily: "'DM Mono',monospace" }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Enter button */}
        <div style={{
          opacity: phase >= 3 ? 1 : 0,
          transform: phase >= 3 ? 'translateY(0)' : 'translateY(20px)',
          transition: 'opacity 0.6s ease 1.1s, transform 0.6s ease 1.1s',
        }}>
          <button
            onClick={onEnter}
            style={{
              padding: '18px 64px',
              background: 'linear-gradient(140deg, #0D1F3C, #1A3356)',
              color: 'white',
              border: '1px solid rgba(13,31,60,0.15)',
              borderRadius: 100,
              fontSize: 16, fontWeight: 700, letterSpacing: '0.12em',
              cursor: 'pointer', fontFamily: "'DM Sans',sans-serif",
              boxShadow: '0 4px 20px rgba(13,31,60,0.25)',
              animation: 'ctaPulse 3s ease-in-out 2s infinite',
              transition: 'transform 0.18s, box-shadow 0.18s',
              textTransform: 'uppercase',
            }}
            onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-3px) scale(1.02)'; e.currentTarget.style.boxShadow = '0 10px 32px rgba(13,31,60,0.40)' }}
            onMouseLeave={e => { e.currentTarget.style.transform = 'none'; e.currentTarget.style.boxShadow = '0 4px 20px rgba(13,31,60,0.25)' }}
          >
            Enter Platform
          </button>
          <div style={{ textAlign: 'center', marginTop: 12, fontSize: 11, color: '#B0BACA', fontFamily: "'DM Mono',monospace", letterSpacing: '0.08em' }}>
            Strategic Business Simulation · Auxi Studios
          </div>
        </div>
      </div>

      {/* Bottom ticker */}
      <div style={{ position: 'relative', zIndex: 2 }}>
        <Ticker />
      </div>

      {/* Gold bottom border */}
      <div style={{ height: 3, background: 'linear-gradient(90deg, transparent, #B8932A 30%, #D4AA40 50%, #B8932A 70%, transparent)', flexShrink: 0, position: 'relative', zIndex: 2 }} />
    </div>
  )
}
