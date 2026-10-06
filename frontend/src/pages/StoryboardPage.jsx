import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import { useAuth } from '../App'
import { api } from '../hooks/useApi'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import {
  getDept, fmtCur, inputDivisor,
  AllocationDonut, DonutLegend,
  
  HoldToSealButton, 
  DepartmentCard,
  AllocateSharedStyles,
} from '../components/allocate/shared'

const MONO = "'DM Mono',monospace"
const SANS = "'DM Sans',sans-serif"

// Helpers
function fmtTime(s) {
  const m = Math.floor(Math.max(0, s) / 60)
  const sec = Math.max(0, s) % 60
  return `${m}:${String(sec).padStart(2, '0')}`
}

function renderInline(line) {
  const parts = line.split('**')
  return parts.map((part, i) =>
    i % 2 === 1
      ? <strong key={i} style={{ color: '#0a1628', fontWeight: 800 }}>{part}</strong>
      : <span key={i}>{part}</span>
  )
}

function RichText({ text, style = {} }) {
  if (!text) return null
  const lines = text.split('\n')
  // Group consecutive bullet lines into a single <ul>
  const nodes = []
  let bulletGroup = []
  const flushBullets = (key) => {
    if (bulletGroup.length === 0) return
    nodes.push(
      <ul key={`ul-${key}`} style={{ margin: '2px 0 6px 0', paddingLeft: 20, textAlign: 'left' }}>
        {bulletGroup.map((b, bi) => (
          <li key={bi} style={{ marginBottom: 2 }}>{renderInline(b)}</li>
        ))}
      </ul>
    )
    bulletGroup = []
  }
  lines.forEach((line, li) => {
    if (!line.trim()) {
      flushBullets(li)
    } else if (line.trimStart().startsWith('* ')) {
      bulletGroup.push(line.trimStart().slice(2))
    } else {
      flushBullets(li)
      nodes.push(
        <p key={li} style={{ margin: '0 0 6px 0' }}>{renderInline(line)}</p>
      )
    }
  })
  flushBullets('end')
  return <div style={style}>{nodes}</div>
}

// Typewriter
function useTypewriter(text, active, speed = 14) {
  const [idx, setIdx] = useState(0)
  const rafRef = useRef(null)
  const lastRef = useRef(0)

  useEffect(() => {
    if (!active || !text) { setIdx(text?.length || 0); return }
    setIdx(0); lastRef.current = 0
    const tick = (now) => {
      if (now - lastRef.current >= speed) {
        lastRef.current = now
        setIdx(i => {
          if (i >= text.length) return i
          return i + 1
        })
      }
      rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current) }
  }, [text, active, speed])

  return { displayed: text ? text.slice(0, idx) : '', done: idx >= (text?.length || 0) }
}

// ORAS mark SVG
function OrasMark({ size = 16 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none">
      <path d="M16 3L29 16L16 29L3 16Z" stroke="rgba(255,255,255,.4)" strokeWidth="1.5" fill="none"/>
      <circle cx="16" cy="3"  r="2" fill="#b8932a"/>
      <circle cx="29" cy="16" r="2" fill="#b8932a"/>
      <circle cx="16" cy="29" r="2" fill="#b8932a"/>
      <circle cx="3"  cy="16" r="2" fill="#b8932a"/>
      <circle cx="16" cy="16" r="2.5" fill="white"/>
    </svg>
  )
}

// Style mapping for the slide router (BlueprintSlide vs PortraitSlide vs special).
const SLIDE_STYLES = {
  welcome:     'portrait',     // NEW: pre-storyboard welcome from the team
  world:       'blueprint',
  market:      'blueprint',
  company:     'blueprint',
  product:     'blueprint',
  departments: 'blueprint',
  role:        'envelope',
  mandate:     'blueprint',    // NEW: post-appointment, before departments
  objective:   'portrait',
  competitors: 'portrait',
  practice:    'practice',     // NEW: full-bleed sandbox allocation surface
  mechanics:   'portrait',     // NEW: mechanics summary before ready
  ready:       'portrait',
}

// Slide types where mechanics are first introduced — the Skip button on the nav advances to the *next*
// slide in this set rather than the final slide.

// APPOINTMENT ENVELOPE — Slide 6 (role)
// Three-act interactive: drag to slice → letter emerges → stamp confirmed
function AppointmentSlide({ slide, step, total, onNext, onBack, onSkip, isLast, scenario }) {
  // Act state: 'sealed' | 'slicing' | 'opened' | 'typing' | 'stamped'
  const [act, setAct] = useState('sealed')
  const [cutPct, setCutPct] = useState(0)
  const [typedChars, setTypedChars] = useState(0)
  const [stampVisible, setStampVisible] = useState(false)

  const envelopeRef = useRef(null)
  const isDragging  = useRef(false)
  const cutPctRef   = useRef(0)
  const rafRef      = useRef(null)

  // Derived scenario data — same palette as the rest of the deck
  const companyName = scenario?.company_name || 'Voltex Motors'
  const roleTitle   = scenario?.company?.role_title || scenario?.role_title || 'VP of Finance & Strategy'
  const playerName  = 'Appointee'
  const today       = new Date()
  const dateStr     = today.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })

  const letterLines = [
    { text: companyName.toUpperCase(), style: 'company' },
    { text: scenario?.company?.location || 'Austin, Texas', style: 'sub' },
    { text: '', style: 'spacer' },
    { text: dateStr, style: 'date' },
    { text: '', style: 'spacer' },
    { text: 'LETTER OF APPOINTMENT', style: 'heading' },
    { text: '', style: 'spacer' },
    { text: `Dear ${playerName},`, style: 'body' },
    { text: '', style: 'spacer' },
    { text: `The Board of Directors is pleased to appoint you to the position of ${roleTitle} effective immediately. You will assume full authority over the allocation of our annual operating budget across all four strategic departments for the duration of our five-year launch window.`, style: 'body' },
    { text: '', style: 'spacer' },
    { text: 'Your decisions are consequential and irrevocable. We have every confidence in your judgement.', style: 'body' },
    { text: '', style: 'spacer' },
    { text: 'Yours sincerely,', style: 'body' },
    { text: '', style: 'spacer' },
    { text: 'The Board', style: 'sig' },
    { text: companyName, style: 'sig-co' },
  ]

  const totalLetterChars = letterLines.reduce((s, l) => s + l.text.length, 0)

  // Drag handlers
  const getLocalX = useCallback((clientX) => {
    if (!envelopeRef.current) return 0
    const rect = envelopeRef.current.getBoundingClientRect()
    return Math.max(0, Math.min(1, (clientX - rect.left) / rect.width))
  }, [])

  const handlePointerDown = useCallback((e) => {
    if (act !== 'sealed' && act !== 'slicing') return
    isDragging.current = true
    setAct('slicing')
    e.currentTarget.setPointerCapture(e.pointerId)
  }, [act])

  const triggerOpen = useCallback(() => {
    if (!isDragging.current) return   // already triggered
    isDragging.current = false
    let p = cutPctRef.current
    const finish = () => {
      p = Math.min(100, p + 4)
      cutPctRef.current = p
      setCutPct(p)
      if (p < 100) { rafRef.current = requestAnimationFrame(finish) }
      else { setTimeout(() => setAct('opened'), 280) }
    }
    rafRef.current = requestAnimationFrame(finish)
  }, [])

  const handlePointerMove = useCallback((e) => {
    if (!isDragging.current) return
    const pct = getLocalX(e.clientX) * 100
    const next = Math.max(cutPctRef.current, pct)
    cutPctRef.current = next
    setCutPct(next)
    if (next >= 60) { triggerOpen() }
  }, [getLocalX, triggerOpen])

  const handlePointerUp = useCallback((e) => {
    if (!isDragging.current) return
    isDragging.current = false
    // If they released before hitting 60%, just leave the cut where it is
  }, [])

  // Typewriter
  useEffect(() => {
    if (act !== 'typing') return
    setTypedChars(0)
    let i = 0
    const tick = setInterval(() => {
      i += 2; setTypedChars(i)
      if (i >= totalLetterChars) {
        clearInterval(tick)
        setTimeout(() => setStampVisible(true), 600)
        setTimeout(() => setAct('stamped'), 900)
      }
    }, 12)
    return () => clearInterval(tick)
  }, [act, totalLetterChars])

  useEffect(() => {
    if (act !== 'opened') return
    const t = setTimeout(() => setAct('typing'), 900)
    return () => clearTimeout(t)
  }, [act])

  useEffect(() => () => { if (rafRef.current) cancelAnimationFrame(rafRef.current) }, [])

  // Letter renderer
  function renderLetter() {
    let charsLeft = typedChars
    return letterLines.map((line, i) => {
      if (charsLeft <= 0) return null
      if (line.style === 'spacer') { return <div key={i} style={{ height: 10 }} /> }
      const show = line.text.slice(0, charsLeft)
      charsLeft = Math.max(0, charsLeft - line.text.length)
      if (!show) return null
      // Letter typography uses the same MONO/navy/gold tokens as every other slide
      const styleMap = {
        company: { fontSize: 14, fontWeight: 900, letterSpacing: '.22em', color: '#0a1628', fontFamily: MONO, marginBottom: 1 },
        sub:     { fontSize: 9,  color: '#6a7a8a', letterSpacing: '.14em', fontFamily: MONO, marginBottom: 2 },
        date:    { fontSize: 10, color: '#6a7a8a', fontFamily: MONO },
        heading: { fontSize: 11, fontWeight: 800, letterSpacing: '.28em', color: '#b8932a', fontFamily: MONO },
        body:    { fontSize: 15, color: '#3a4a5a', lineHeight: 1.60, fontFamily: SANS, textAlign: 'justify' },
        sig:     { fontSize: 13, color: '#0a1628', fontFamily: SANS, fontStyle: 'italic' },
        'sig-co':{ fontSize: 9, color: '#6a7a8a', letterSpacing: '.14em', fontFamily: MONO, marginTop: 2 },
      }
      return (
        <div key={i} style={styleMap[line.style] || {}}>
          {show}
          {charsLeft === 0 && act === 'typing' && (
            <span style={{ display: 'inline-block', width: 7, height: 13, background: '#1a3a6b', verticalAlign: 'text-bottom', marginLeft: 2, animation: 'blink .7s step-end infinite' }} />
          )}
        </div>
      )
    })
  }

  const isOpen = act === 'opened' || act === 'typing' || act === 'stamped'

  return (
    <div style={{ flex: 1, display: 'flex', overflow: 'hidden', background: '#f0f4fa', position: 'relative' }}>

      {/* Engineering grid — same as BlueprintSlide */}
      <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
        <defs>
          <pattern id="appt-grid-sm" width="28" height="28" patternUnits="userSpaceOnUse">
            <path d="M28 0L0 0 0 28" fill="none" stroke="rgba(26,58,107,.07)" strokeWidth=".5"/>
          </pattern>
          <pattern id="appt-grid-lg" width="140" height="140" patternUnits="userSpaceOnUse">
            <path d="M140 0L0 0 0 140" fill="none" stroke="rgba(26,58,107,.12)" strokeWidth="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#appt-grid-sm)"/>
        <rect width="100%" height="100%" fill="url(#appt-grid-lg)"/>
      </svg>

      {/* Custom letter-opener cursor while slicing */}
      {(act === 'sealed' || act === 'slicing') && (
        <style>{`* { cursor: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='32' height='32' viewBox='0 0 32 32'%3E%3Cline x1='4' y1='28' x2='28' y2='4' stroke='%230a1628' stroke-width='2.5' stroke-linecap='round'/%3E%3Cpolygon points='28,4 22,8 24,10' fill='%230a1628'/%3E%3Cline x1='4' y1='28' x2='8' y2='24' stroke='%23b8932a' stroke-width='2' stroke-linecap='round'/%3E%3C/svg%3E") 4 28, crosshair !important; }`}</style>
      )}

      <style>{`
        @keyframes flapOpen   { from{transform:rotateX(0deg)} to{transform:rotateX(-160deg)} }
        @keyframes letterRise { from{transform:translateY(56px);opacity:0} to{transform:translateY(0);opacity:1} }
        @keyframes stampIn    { 0%{opacity:0;transform:rotate(-12deg) scale(1.6)} 65%{opacity:1;transform:rotate(-12deg) scale(.93)} 82%{transform:rotate(-12deg) scale(1.05)} 100%{transform:rotate(-12deg) scale(1)} }
        @keyframes hintBounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(5px)} }
        @keyframes hintFade   { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
      `}</style>

      {/* ── Left graphic zone: envelope stage ── */}
      <div style={{ flex: 1.2, position: 'relative', overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>

        {!isOpen ? (
          /* ACT 1 — Sealed */
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 24 }}>
            <div
              ref={envelopeRef}
              onPointerDown={handlePointerDown}
              onPointerMove={handlePointerMove}
              onPointerUp={handlePointerUp}
              style={{ position: 'relative', width: 560, height: 360, userSelect: 'none', touchAction: 'none' }}
            >
              <svg viewBox="0 0 560 360" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}>
                <defs>
                  {/* Layered paper-grain texture */}
                  <filter id="grain" x="0%" y="0%" width="100%" height="100%">
                    <feTurbulence type="fractalNoise" baseFrequency="0.68" numOctaves="4" seed="12" stitchTiles="stitch" result="noise"/>
                    <feColorMatrix type="saturate" values="0" in="noise" result="grey"/>
                    <feBlend in="SourceGraphic" in2="grey" mode="multiply"/>
                  </filter>
                  {/* Cut-edge glow */}
                  <filter id="cutGlow" x="-10%" y="-200%" width="120%" height="500%">
                    <feGaussianBlur stdDeviation="2" result="blur"/>
                    <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
                  </filter>
                  <linearGradient id="envBody" x1="0.15" y1="0" x2="0" y2="1">
                    <stop offset="0%"   stopColor="#ffffff"/>
                    <stop offset="60%"  stopColor="#f5f8fe"/>
                    <stop offset="100%" stopColor="#e8eef8"/>
                  </linearGradient>
                  {/* Left side fold — very subtle shadow */}
                  <linearGradient id="envLeft" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%"   stopColor="#dce5f3"/>
                    <stop offset="100%" stopColor="#edf1f9"/>
                  </linearGradient>
                  {/* Right side fold */}
                  <linearGradient id="envRight" x1="1" y1="0" x2="0" y2="0">
                    <stop offset="0%"   stopColor="#dce5f3"/>
                    <stop offset="100%" stopColor="#edf1f9"/>
                  </linearGradient>
                  {/* Bottom flap */}
                  <linearGradient id="envBottom" x1="0" y1="1" x2="0" y2="0">
                    <stop offset="0%"   stopColor="#d0dcee"/>
                    <stop offset="100%" stopColor="#e4ecf8"/>
                  </linearGradient>
                  {/* Top flap — just slightly darker than body */}
                  <linearGradient id="envFlap" x1="0.1" y1="0" x2="0" y2="1">
                    <stop offset="0%"   stopColor="#e8eef8"/>
                    <stop offset="100%" stopColor="#d8e2f2"/>
                  </linearGradient>
                  {/* Seal: deep navy radial with highlight */}
                  <radialGradient id="sealFill" cx="38%" cy="32%" r="65%">
                    <stop offset="0%"   stopColor="#223d6e"/>
                    <stop offset="100%" stopColor="#070d1a"/>
                  </radialGradient>
                  {/* Gold gradient for rings & tab */}
                  <linearGradient id="gold" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%"   stopColor="#dbb84a"/>
                    <stop offset="50%"  stopColor="#b8932a"/>
                    <stop offset="100%" stopColor="#8a6a14"/>
                  </linearGradient>
                  {/* Clip to envelope body */}
                  <clipPath id="envClip">
                    <rect x="10" y="40" width="540" height="310" rx="4"/>
                  </clipPath>
                </defs>

                {/* ── Stacked drop shadows ── */}
                <rect x="16" y="60" width="540" height="310" rx="4" fill="#0a1628" opacity=".10"/>
                <rect x="13" y="52" width="540" height="310" rx="4" fill="#0a1628" opacity=".06"/>

                {/* ── Envelope body ── */}
                <rect x="10" y="40" width="540" height="310" rx="4" fill="url(#envBody)" stroke="rgba(26,58,107,.18)" strokeWidth="1"/>

                {/* ── Inner fold panels (clipped) ── */}
                <g clipPath="url(#envClip)">
                  <polygon points="10,40 10,350 280,195"  fill="url(#envLeft)"   opacity=".6"/>
                  <polygon points="550,40 550,350 280,195" fill="url(#envRight)"  opacity=".6"/>
                  <polygon points="10,350 550,350 280,195" fill="url(#envBottom)" opacity=".75"/>

                  {/* Fold crease hairlines */}
                  <line x1="10"  y1="40"  x2="280" y2="195" stroke="rgba(26,58,107,.13)" strokeWidth="0.75"/>
                  <line x1="550" y1="40"  x2="280" y2="195" stroke="rgba(26,58,107,.13)" strokeWidth="0.75"/>
                  <line x1="10"  y1="350" x2="280" y2="195" stroke="rgba(26,58,107,.10)" strokeWidth="0.75"/>
                  <line x1="550" y1="350" x2="280" y2="195" stroke="rgba(26,58,107,.10)" strokeWidth="0.75"/>

                  {/* Paper grain overlay — adds texture to the white face */}
                  <rect x="10" y="40" width="540" height="310" fill="white" opacity=".25" filter="url(#grain)"/>

                  {/* Inner emboss highlight */}
                  <rect x="14" y="44" width="532" height="302" rx="2.5" fill="none" stroke="rgba(255,255,255,.65)" strokeWidth="1.2"/>
                </g>

                {/* ── Top flap — drawn over body ── */}
                <polygon points="10,40 550,40 280,210" fill="url(#envFlap)" stroke="rgba(26,58,107,.16)" strokeWidth="1"/>
                {/* Flap crease shadow */}
                <line x1="10" y1="40" x2="550" y2="40" stroke="rgba(26,58,107,.22)" strokeWidth="1.5"/>
                {/* Subtle highlight on flap edge */}
                <line x1="10" y1="40" x2="550" y2="40" stroke="rgba(255,255,255,.35)" strokeWidth="0.5" strokeDasharray="4 3"/>

                {/* ── Company & role text — lower face, above seal ── */}
                <text x="280" y="288" textAnchor="middle" fontSize="11" fill="rgba(10,22,40,.42)" fontFamily="'DM Mono',monospace" letterSpacing="4.5" fontWeight="600">
                  {companyName.toUpperCase()}
                </text>
                <text x="280" y="308" textAnchor="middle" fontSize="8.5" fill="rgba(10,22,40,.26)" fontFamily="'DM Mono',monospace" letterSpacing="2.5">
                  {roleTitle}
                </text>

                {/* ── Wax seal — clean, precise ── */}
                <g transform="translate(280,196)" style={{}}>
                  {/* Shadow beneath disc */}
                  <circle r="32" fill="rgba(10,22,40,.18)" transform="translate(0,3)"/>
                  {/* Thin gold outer ring */}
                  <circle r="32" fill="none" stroke="url(#gold)" strokeWidth="1.5" opacity=".7"/>
                  {/* Main disc */}
                  <circle r="30" fill="url(#sealFill)"/>
                  {/* Single clean inner ring */}
                  <circle r="25" fill="none" stroke="rgba(184,147,42,.45)" strokeWidth="0.8"/>
                  {/* ORAS diamond — clean strokes, no dots */}
                  <path d="M0,-13 L10,0 L0,11 L-10,0 Z" fill="none" stroke="url(#gold)" strokeWidth="1.4"/>
                  {/* Centre dot */}
                  <circle r="2.5" fill="#c9a02a"/>
                  {/* Top-left highlight — subtle dome effect */}
                  <path d="M-16,-10 A20,20 0 0,1 8,-18" fill="none" stroke="rgba(255,255,255,.18)" strokeWidth="5" strokeLinecap="round"/>
                </g>

                {/* ── Gold corner accent (top-left) ── */}
                <rect x="10" y="40" width="42" height="5" fill="url(#gold)" rx="0"/>
                <rect x="10" y="40" width="5"  height="26" fill="url(#gold)" opacity=".45"/>

                {/* ── Cut line with bright leading dot ── */}
                {cutPct > 0 && (
                  <g filter="url(#cutGlow)">
                    <line
                      x1="10" y1="40"
                      x2={10 + (cutPct / 100) * 540} y2="40"
                      stroke="#d4aa40" strokeWidth="2.5" strokeLinecap="round"
                    />
                    <circle cx={10 + (cutPct / 100) * 540} cy="40" r="3.5" fill="#e8c44a" opacity=".95"/>
                  </g>
                )}
              </svg>
            </div>

            {/* Hint label */}
            {act === 'sealed' && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, animation: 'hintFade .5s .4s both' }}>
                <svg style={{ animation: 'hintBounce 1.5s ease-in-out infinite', opacity: .55 }} width="32" height="32" viewBox="0 0 24 24" fill="none">
                  <path d="M5 9h14M5 9l7 4 7-4" stroke="#1a3a6b" strokeWidth="1.4" strokeLinecap="round"/>
                  <rect x="3" y="8" width="18" height="12" rx="1.5" stroke="#1a3a6b" strokeWidth="1.2" fill="none"/>
                </svg>
                <span style={{ fontSize: 15, color: '#3a4a5a', fontFamily: SANS, fontWeight: 600, letterSpacing: '.02em', textAlign: 'center', maxWidth: 380, lineHeight: 1.4 }}>
                  Click and slide across the top of the envelope to open
                </span>
              </div>
            )}
            {act === 'slicing' && cutPct < 60 && (
              <span style={{ fontSize: 13, color: '#b8932a', fontFamily: MONO, letterSpacing: '.12em', opacity: .9, fontWeight: 700 }}>
                {Math.round(cutPct)}% — KEEP GOING
              </span>
            )}
          </div>

        ) : (
          /* ACT 2 & 3 — Letter */
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 28, width: '100%', maxWidth: 740, padding: '0 24px' }}>
            {/* Shrunken opened envelope — left */}
            <div style={{ flexShrink: 0, width: 160, marginTop: 12 }}>
              <svg viewBox="0 0 160 120" style={{ width: '100%', filter: 'drop-shadow(0 3px 10px rgba(10,22,40,.10))' }}>
                <rect x="3" y="24" width="154" height="93" rx="2" fill="#f0f4fa" stroke="rgba(26,58,107,.12)" strokeWidth="1"/>
                {/* Flap open */}
                <polygon points="3,24 157,24 80,78" fill="#dce4f0"
                  style={{ transformOrigin: '80px 24px', animation: 'flapOpen .5s cubic-bezier(.4,0,.2,1) both' }}/>
                <line x1="3"   y1="24" x2="80"  y2="78" stroke="rgba(26,58,107,.10)" strokeWidth=".8"/>
                <line x1="157" y1="24" x2="80"  y2="78" stroke="rgba(26,58,107,.10)" strokeWidth=".8"/>
                {/* Gold cut line */}
                <line x1="3" y1="24" x2="157" y2="24" stroke="#b8932a" strokeWidth="1.5"/>
                {/* Navy seal stub */}
                <circle cx="80" cy="86" r="10" fill="#0a1628" opacity=".35"/>
              </svg>
            </div>

            {/* The letter itself — styled like the blueprint right panel */}
            <div style={{
              flex: 1,
              background: 'rgba(255,255,255,.97)',
              border: '1px solid rgba(26,58,107,.12)',
              borderRadius: 3,
              padding: '28px 32px',
              boxShadow: '-2px 0 20px rgba(10,22,40,.06), 0 8px 32px rgba(10,22,40,.08)',
              position: 'relative',
              animation: 'letterRise .5s .08s cubic-bezier(.4,0,.2,1) both',
              minHeight: 340,
              backdropFilter: 'blur(4px)',
            }}>
              <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: 'linear-gradient(90deg,#0a1628,#1a3a6b)', borderRadius: '3px 3px 0 0' }}/>
              <div style={{ position: 'absolute', top: 3, left: 0, right: 0, height: 1.5, background: '#b8932a', opacity: .7 }}/>

              <div style={{ paddingTop: 6 }}>
                {renderLetter()}
              </div>

              {/* CONFIRMED stamp — navy to match the system accent */}
              {stampVisible && (
                <div style={{
                  position: 'absolute', bottom: 28, right: 28,
                  animation: 'stampIn .32s cubic-bezier(.2,0,.3,1.4) both',
                  transformOrigin: 'center',
                }}>
                  <svg viewBox="0 0 200 64" width="200" height="64">
                    <rect x="3" y="3" width="194" height="58" rx="3" fill="none" stroke="#b91c1c" strokeWidth="3.5" opacity=".85"/>
                    <rect x="9" y="9" width="182" height="46" rx="1.5" fill="none" stroke="#b91c1c" strokeWidth="1" opacity=".35"/>
                    <text x="100" y="41" textAnchor="middle" fontSize="20" fontWeight="900" fill="#b91c1c" fontFamily="'DM Mono',monospace" letterSpacing="4" opacity=".88">CONFIRMED</text>
                  </svg>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* ── Right panel — matches BlueprintSlide panel exactly ── */}
      <div className="sb-portrait-panel" style={{ width: 460, flexShrink: 0, background: 'rgba(255,255,255,.95)', borderLeft: '1px solid rgba(26,58,107,.12)', display: 'flex', flexDirection: 'column', backdropFilter: 'blur(4px)', position: 'relative', zIndex: 2, boxShadow: '-2px 0 20px rgba(10,22,40,.06)' }}>

        {/* Panel header — identical markup to BlueprintSlide */}
        <div style={{ padding: '16px 24px 0', flexShrink: 0 }}>
          <div style={{ fontSize: 9, color: '#b8932a', letterSpacing: '.20em', fontFamily: MONO, textTransform: 'uppercase', marginBottom: 6 }}>
            Transmission {String(step + 1).padStart(2, '0')} · role
          </div>
          <h2 style={{ fontSize: 20, fontWeight: 900, color: '#0a1628', lineHeight: 1.2, margin: 0 }}>
            {slide?.title || 'Your Role'}
          </h2>
          <div style={{ height: 2, width: 32, background: '#1a3a6b', borderRadius: 1, marginTop: 8 }} />
        </div>

        {/* Body copy */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '10px 24px' }}>
          <RichText text={slide?.content || ''} style={{ fontSize: 15, color: '#3a4a5a', lineHeight: 1.60, textAlign: 'justify' }} />

          {/* Status line below the text — context-sensitive */}
          <div style={{ marginTop: 20, padding: '12px 14px', borderRadius: 3, background: act === 'stamped' ? 'rgba(26,58,107,.06)' : 'rgba(184,147,42,.06)', border: `1px solid ${act === 'stamped' ? 'rgba(26,58,107,.14)' : 'rgba(184,147,42,.20)'}`, transition: 'all .4s' }}>
            <div style={{ fontSize: 9, fontFamily: MONO, letterSpacing: '.18em', color: act === 'stamped' ? '#1a3a6b' : '#b8932a', fontWeight: 700, marginBottom: 4 }}>
              {act === 'stamped' ? '✓ APPOINTMENT CONFIRMED' : act === 'slicing' ? 'SLICING...' : act === 'typing' || act === 'opened' ? 'PROCESSING...' : 'ACTION REQUIRED'}
            </div>
            <div style={{ fontSize: 11, color: '#6a7a8a', fontFamily: SANS, lineHeight: 1.5 }}>
              {act === 'stamped'
                ? `${roleTitle} — ${companyName}`
                : 'Open the envelope to receive your appointment letter.'}
            </div>
          </div>
        </div>

        <div style={{ padding: '0 16px 16px', flexShrink: 0 }}>
          <div style={{ height: 1, background: '#e8ecf2', marginBottom: 14 }} />
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
            <button
              onClick={onBack}
              disabled={step === 0}
              style={{ visibility: step === 0 ? 'hidden' : 'visible', background: 'white', border: '1.5px solid #d4dce8', borderRadius: 6, padding: '9px 18px', fontSize: 12, fontWeight: 700, color: '#3a4a5a', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 5, fontFamily: SANS }}
            >
              <svg width="11" height="11" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"/></svg>
              Back
            </button>
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              {!isLast && (
                <button onClick={onSkip} style={{ background: '#f5f7fa', border: '1.5px solid #d0d8e4', borderRadius: 6, padding: '9px 16px', fontSize: 11, fontWeight: 600, color: '#6a7a8a', cursor: 'pointer', fontFamily: SANS }}>
                  Skip all
                </button>
              )}
              {!isLast && (
                <button
                  onClick={act === 'stamped' ? onNext : undefined}
                  style={{
                    background: act === 'stamped' ? '#1a3a6b' : 'rgba(26,58,107,.25)',
                    border: 'none',
                    borderRadius: 6,
                    padding: '9px 22px',
                    fontSize: 12,
                    fontWeight: 700,
                    color: 'white',
                    cursor: act === 'stamped' ? 'pointer' : 'not-allowed',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 5,
                    fontFamily: SANS,
                    boxShadow: act === 'stamped' ? '0 2px 10px rgba(26,58,107,.40)' : 'none',
                    transition: 'background .4s, box-shadow .4s',
                  }}
                >
                  {act === 'stamped' ? 'Accept & Continue' : 'Open envelope first'}
                  {act === 'stamped' && <svg width="11" height="11" viewBox="0 0 16 16" fill="none"><path d="M6 3l5 5-5 5" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"/></svg>}
                </button>
              )}
            </div>
          </div>
          {/* Progress dots — matches SlideNav exactly */}
          <div style={{ display: 'flex', gap: 3, marginTop: 12 }}>
            {Array.from({ length: total }, (_, i) => (
              <div key={i} style={{ flex: 1, height: 3, borderRadius: 2, background: i < step ? '#b8932a' : i === step ? '#1a3a6b' : '#e0e6ef', transition: 'background 0.3s' }} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// BLUEPRINT slides
function BlueprintSlide({ slide, displayed, done, step, total, onNext, onBack, onSkip, isLast, auth, onReady }) {
  const type = slide?.type || 'default'

  return (
    <div className="sb-blueprint-slide" style={{ flex: 1, display: 'flex', overflow: 'hidden', background: '#f0f4fa' }}>
      {/* Engineering grid background */}
      <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
        <defs>
          <pattern id="grid-sm" width="28" height="28" patternUnits="userSpaceOnUse">
            <path d="M28 0L0 0 0 28" fill="none" stroke="rgba(26,58,107,.07)" strokeWidth=".5"/>
          </pattern>
          <pattern id="grid-lg" width="140" height="140" patternUnits="userSpaceOnUse">
            <path d="M140 0L0 0 0 140" fill="none" stroke="rgba(26,58,107,.12)" strokeWidth="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid-sm)"/>
        <rect width="100%" height="100%" fill="url(#grid-lg)"/>
      </svg>

      {/* Graphic zone — left 55% */}
      <div className="sb-blueprint-graphic" style={{ flex: 1.2, position: 'relative', overflow: 'hidden' }}>
        <BlueprintGraphic type={type} slide={slide} />
      </div>

      {/* Panel — right */}
      <div className="sb-portrait-panel" style={{ width: 460, flexShrink: 0, background: 'rgba(255,255,255,.95)', borderLeft: '1px solid rgba(26,58,107,.12)', display: 'flex', flexDirection: 'column', backdropFilter: 'blur(4px)', position: 'relative', zIndex: 2, boxShadow: '-2px 0 20px rgba(10,22,40,.06)' }}>
        {/* Panel header */}
        <div style={{ padding: '16px 24px 0', flexShrink: 0 }}>
          <div style={{ fontSize: 9, color: '#b8932a', letterSpacing: '.20em', fontFamily: MONO, textTransform: 'uppercase', marginBottom: 6 }}>
            Transmission {String(step + 1).padStart(2, '0')} · {type}
          </div>
          <h2 style={{ fontSize: 20, fontWeight: 900, color: '#0a1628', lineHeight: 1.2, margin: 0 }}>{slide?.title}</h2>
          {slide?.subtitle && <div style={{ fontSize: 11, color: '#6a7a8a', fontFamily: MONO, marginTop: 5, lineHeight: 1.4 }}>{slide.subtitle}</div>}
          <div style={{ height: 2, width: 32, background: '#1a3a6b', borderRadius: 1, marginTop: 8 }} />
        </div>

        {/* Scrollable text */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '10px 24px' }}>
          <RichText text={displayed} style={{ fontSize: 15, color: '#3a4a5a', lineHeight: 1.60, textAlign: 'justify' }} />
          {!done && <span style={{ display: 'inline-block', width: 7, height: 14, background: '#1a3a6b', verticalAlign: 'text-bottom', marginLeft: 2, animation: 'blink .7s step-end infinite' }} />}
          {isLast && done && <FinalCTA auth={auth} onReady={onReady} />}
        </div>

        <SlideNav step={step} total={total} onNext={onNext} onBack={onBack} onSkip={onSkip} isLast={isLast} accent="#1a3a6b" />
      </div>
    </div>
  )
}

// Blueprint graphic per type
function BlueprintGraphic({ type, slide }) {
  const key = `${type}-graphic`
  if (type === 'product') return <ProductBlueprint key={key} />
  if (type === 'world')   return <WorldGlobe key={key} scenarioId={slide?.scenarioId} />
  if (type === 'market')  return <MarketPlot key={key} />
  if (type === 'company') return <CompanyChart key={key} />
  if (type === 'departments') return <DeptCircuit key={key} departments={slide?.departments} sym={slide?.sym} suffix={slide?.suffix} maxChangeRate={slide?.maxChangeRate} />
  if (type === 'role')    return <RoleColumns key={key} />
  if (type === 'mandate') return <MandateLedger key={key} budget={slide?.budget} numPeriods={slide?.numPeriods} sym={slide?.sym} suffix={slide?.suffix} />
  return <DefaultBlueprint key={key} />
}

// WorldGlobe — D3 geoOrthographic (real TopoJSON country outlines) Requires: npm install d3-geo
// topojson-client Both are lightweight and tree-shakeable; no full d3 bundle needed.
function WorldGlobe({ scenarioId }) {
  const svgRef    = useRef(null)
  const stateRef  = useRef({})   // mutable render state — avoids re-render loops
  const rafRef    = useRef(null)

  const SCENARIOS = {
    us_ev: { iso: '840', label: 'UNITED STATES',  lon: -98, lat: 38  },
    uk_ev: { iso: '826', label: 'UNITED KINGDOM', lon: -2,  lat: 54  },
    in_ev: { iso: '356', label: 'INDIA',           lon: 80,  lat: 22  },
    ca_ev: { iso: '124', label: 'CANADA',          lon: -96, lat: 60  },
  }

  useEffect(() => {
    const svg = svgRef.current
    if (!svg) return
    const parent = svg.parentElement
    let destroyed = false

    const loadWorldAtlas = () =>
      fetch('/world-atlas/countries-110m.json')
        .then(r => { if (!r.ok) throw new Error(`local atlas ${r.status}`); return r.json() })
        .catch(() => fetch('https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json').then(r => r.json()))

    Promise.all([
      import('d3-geo'),
      import('topojson-client'),
      loadWorldAtlas(),
    ]).then(([d3geo, topo, world]) => {
      if (destroyed) return

      // Data
      const countries = topo.feature(world, world.objects.countries)
      const borders   = topo.mesh(world, world.objects.countries, (a, b) => a !== b)
      const land      = topo.merge(world, world.objects.countries.geometries)
      const sphere    = { type: 'Sphere' }
      const graticule = d3geo.geoGraticule().step([20, 20])()

      // Dimensions
      const W = parent.offsetWidth
      const H = parent.offsetHeight
      const cx = W * 0.42
      const cy = H * 0.5
      const R  = Math.min(W, H) * 0.37

      svg.setAttribute('viewBox', `0 0 ${W} ${H}`)
      svg.setAttribute('width',  W)
      svg.setAttribute('height', H)

      // D3 projection
      const projection = d3geo.geoOrthographic()
        .scale(R)
        .translate([cx, cy])
        .clipAngle(90)
        .precision(0.3)

      const pathGen = d3geo.geoPath(projection)

      // SVG namespace helper
      const NS = 'http://www.w3.org/2000/svg'
      const el = (tag, attrs = {}, parent = svg) => {
        const e = document.createElementNS(NS, tag)
        Object.entries(attrs).forEach(([k, v]) => e.setAttribute(k, v))
        parent.appendChild(e)
        return e
      }

      svg.innerHTML = ''  // clear any previous content

      // Defs
      const defs = el('defs')
      const clipPath = el('clipPath', { id: 'wg-clip' }, defs)
      el('circle', { cx, cy, r: R }, clipPath)

      // Layers (all inside clip)
      const gClipped = el('g', { 'clip-path': 'url(#wg-clip)' })

      const elOcean    = el('path', { fill: '#c8d8ec', stroke: 'none' }, gClipped)
      const elGrat     = el('path', { fill: 'none', stroke: 'rgba(26,58,107,0.13)', 'stroke-width': '0.6' }, gClipped)
      const elLand     = el('path', { fill: 'rgba(26,58,107,0.12)', stroke: 'none' }, gClipped)
      const elHlFill   = el('path', { fill: 'rgba(184,147,42,0.28)', stroke: 'none' }, gClipped)
      const elHlStroke = el('path', { fill: 'none', stroke: '#b8932a', 'stroke-width': '2.2', 'stroke-linejoin': 'round' }, gClipped)
      const elBorders  = el('path', { fill: 'none', stroke: 'rgba(26,58,107,0.50)', 'stroke-width': '0.75', 'stroke-linejoin': 'round' }, gClipped)

      // Globe rim (outside clip so it sits on top cleanly)
      el('circle', { cx, cy, r: R, fill: 'none', stroke: '#1a3a6b', 'stroke-width': '1.8' })

      // Tick marks
      const tickG = el('g', { fill: 'none' })
      for (let i = 0; i < 72; i++) {
        const a   = (i / 72) * Math.PI * 2
        const maj = i % 6 === 0, mid = i % 3 === 0
        const len = maj ? 9 : mid ? 6 : 3
        el('line', {
          x1: cx + (R + 2) * Math.cos(a),        y1: cy + (R + 2) * Math.sin(a),
          x2: cx + (R + 2 + len) * Math.cos(a),  y2: cy + (R + 2 + len) * Math.sin(a),
          stroke: `rgba(26,58,107,${maj ? 0.45 : 0.22})`,
          'stroke-width': maj ? '1.2' : '0.7',
        }, tickG)
      }

      // Corner brackets
      const brkG = el('g', { stroke: 'rgba(26,58,107,0.28)', 'stroke-width': '1', fill: 'none' })
      const s = 12, d = 4
      ;[[36, 22], [W - 36, 22], [36, H - 22], [W - 36, H - 22]].forEach(([bx, by]) => {
        const sx = bx < W / 2 ? 1 : -1, sy = by < H / 2 ? 1 : -1
        el('path', { d: `M${bx + sx*(d+s)},${by + sy*d} L${bx + sx*d},${by + sy*d} L${bx + sx*d},${by + sy*(d+s)}` }, brkG)
      })

      // Header label
      const hdr = el('text', { x: '42', y: '20', 'font-family': MONO, 'font-size': '8', 'font-weight': '700', fill: 'rgba(26,58,107,0.38)', 'letter-spacing': '0.14em' })
      hdr.textContent = 'ORAS · SCENARIO WORLD MAP'

      // Callout panel
      const panelW = 200, panelH = 72
      const panelX = cx + R + 22, panelY = cy - panelH / 2
      const callG = el('g')
      el('rect', { x: panelX, y: panelY, width: panelW, height: panelH, rx: '4', fill: 'rgba(255,255,255,0.96)', stroke: 'rgba(26,58,107,0.18)', 'stroke-width': '0.8' }, callG)
      el('rect', { x: panelX, y: panelY, width: panelW, height: '3', rx: '1.5', fill: '#b8932a' }, callG)
      const regionLbl = el('text', { x: panelX + 14, y: panelY + 22, 'font-family': MONO, 'font-size': '9', 'font-weight': '700', fill: '#b8932a', 'letter-spacing': '0.16em' }, callG)
      regionLbl.textContent = 'SCENARIO REGION'
      const countryLbl = el('text', { x: panelX + 14, y: panelY + 52, 'font-family': MONO, 'font-size': '18', 'font-weight': '700', fill: '#0a1628' }, callG)

      // Connector + pin
      const connector = el('line', { stroke: 'rgba(184,147,42,0.40)', 'stroke-width': '0.8', 'stroke-dasharray': '3,3' })
      svg.insertBefore(connector, callG)
      const pinG    = el('g')
      const pinRing = el('circle', { r: '10', fill: 'none', stroke: 'rgba(184,147,42,0.35)', 'stroke-width': '1.2' }, pinG)
      const pinDot  = el('circle', { r: '4',  fill: '#b8932a' }, pinG)
      el('circle', { r: '2', fill: 'white' }, pinG)

      // Rotation state
      const state = stateRef.current
      state.rotLon    = 98
      state.rotLat    = -38
      state.targetLon = 98
      state.targetLat = -38
      state.hlIso     = '840'
      state.hlLonLat  = [-98, 38]
      state.pulseT    = 0
      state.scenario  = scenarioId || 'us_ev'

      // Apply initial scenario
      const sc0 = SCENARIOS[state.scenario] || SCENARIOS.us_ev
      state.hlIso     = sc0.iso
      state.hlLonLat  = [sc0.lon, sc0.lat]
      state.targetLon = -sc0.lon
      state.targetLat = -sc0.lat * 0.5
      countryLbl.textContent = sc0.label

      // Render loop
      function frame() {
        if (destroyed) return
        state.rotLon += (state.targetLon - state.rotLon) * 0.06
        state.rotLat += (state.targetLat - state.rotLat) * 0.06
        state.pulseT += 0.016

        projection.rotate([state.rotLon, state.rotLat])

        elOcean.setAttribute('d',    pathGen(sphere)    || '')
        elGrat.setAttribute('d',     pathGen(graticule) || '')
        elLand.setAttribute('d',     pathGen(land)      || '')
        elBorders.setAttribute('d',  pathGen(borders)   || '')

        const hlFeat = countries.features.find(f => f.id === state.hlIso)
        if (hlFeat) {
          elHlFill.setAttribute('d',   pathGen(hlFeat) || '')
          elHlStroke.setAttribute('d', pathGen(hlFeat) || '')

          // Pulse opacity on fill
          const pulse = 0.22 + Math.sin(state.pulseT * 2.8) * 0.09
          elHlFill.setAttribute('fill', `rgba(184,147,42,${pulse})`)
        }

        // Pin position via projection
        const pinXY = projection(state.hlLonLat)
        // Visibility: check dot product of rotated point with z-axis
        const rot    = projection.rotate()
        const dlon   = (state.hlLonLat[0] + rot[0]) * Math.PI / 180
        const dlat   = (state.hlLonLat[1] + (rot[1] || 0)) * Math.PI / 180
        const onFront = Math.cos(dlat) * Math.cos(dlon) > 0

        if (pinXY && onFront) {
          const [px, py] = pinXY
          pinG.setAttribute('display', '')
          connector.setAttribute('display', '')
          ;[pinRing, pinDot, pinG.lastChild].forEach(e => {
            e.setAttribute('cx', px)
            e.setAttribute('cy', py)
          })
          const pr = 4 + Math.sin(state.pulseT * 2.8) * 3
          pinRing.setAttribute('r', pr + 6)
          pinRing.setAttribute('stroke-opacity', Math.max(0, 0.45 - pr / 28))
          connector.setAttribute('x1', px)
          connector.setAttribute('y1', py)
          connector.setAttribute('x2', panelX)
          connector.setAttribute('y2', panelY + panelH / 2)
        } else {
          pinG.setAttribute('display', 'none')
          connector.setAttribute('display', 'none')
        }

        rafRef.current = requestAnimationFrame(frame)
      }
      rafRef.current = requestAnimationFrame(frame)

      // Drag to rotate
      let isDrag = false, dragX = 0, dragY = 0
      const onDown  = e => { isDrag = true;  dragX = e.clientX; dragY = e.clientY }
      const onUp    = ()  => { isDrag = false }
      const onMove  = e => {
        if (!isDrag) return
        state.targetLon += (e.clientX - dragX) * 0.4;  dragX = e.clientX
        state.targetLat -= (e.clientY - dragY) * 0.3;  dragY = e.clientY
        state.targetLat  = Math.max(-85, Math.min(85, state.targetLat))
      }
      const onTouchStart = e => { isDrag = true;  dragX = e.touches[0].clientX; dragY = e.touches[0].clientY }
      const onTouchMove  = e => {
        if (!isDrag) return
        state.targetLon += (e.touches[0].clientX - dragX) * 0.4;  dragX = e.touches[0].clientX
        state.targetLat -= (e.touches[0].clientY - dragY) * 0.3;  dragY = e.touches[0].clientY
      }
      svg.addEventListener('mousedown',  onDown)
      svg.addEventListener('touchstart', onTouchStart, { passive: true })
      svg.addEventListener('touchend',   onUp,         { passive: true })
      svg.addEventListener('touchmove',  onTouchMove,  { passive: true })
      window.addEventListener('mouseup',   onUp)
      window.addEventListener('mousemove', onMove)

      // Store updater so scenarioId changes can drive the globe
      stateRef.current._update = (key) => {
        const sc = SCENARIOS[key] || SCENARIOS.us_ev
        state.hlIso     = sc.iso
        state.hlLonLat  = [sc.lon, sc.lat]
        state.targetLon = -sc.lon
        state.targetLat = -sc.lat * 0.5
        countryLbl.textContent = sc.label
      }

      // Cleanup
      return () => {
        svg.removeEventListener('mousedown',  onDown)
        svg.removeEventListener('touchstart', onTouchStart)
        svg.removeEventListener('touchend',   onUp)
        svg.removeEventListener('touchmove',  onTouchMove)
        window.removeEventListener('mouseup',   onUp)
        window.removeEventListener('mousemove', onMove)
      }
    }).catch(err => console.error('WorldGlobe init failed:', err))

    return () => {
      destroyed = true
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, []) // eslint-disable-line

  // When scenarioId prop changes, tell the running loop to update
  useEffect(() => {
    if (stateRef.current._update && scenarioId) {
      stateRef.current._update(scenarioId)
    }
  }, [scenarioId])

  return (
    <svg
      ref={svgRef}
      style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', cursor: 'grab' }}
    />
  )
}

function MarketPlot() {
  const canvasRef = useRef(null)
  const stateRef  = useRef({ active: 0, hovering: -1, pulseT: 0 })
  const rafRef    = useRef(null)

  const SEGS = [
    { key: 'budget',      label: 'Budget-Conscious Families', short: 'Budget',      pct: 35, color: '#3D6B50',
      desc: 'Middle-income households seeking affordable EVs. Highly sensitive to sticker price and total cost of ownership.' },
    { key: 'tech',        label: 'Tech-Savvy Early Adopters',  short: 'Tech',        pct: 25, color: '#4A7B9D',
      desc: 'Affluent urban professionals who prioritise OTA updates, autonomous aids, connected apps, and digital UX.' },
    { key: 'performance', label: 'Performance Enthusiasts',    short: 'Performance', pct: 20, color: '#C27D3A',
      desc: 'Drivers who demand best-in-class range, acceleration, and dynamics. Willing to pay a premium.' },
    { key: 'fleet',       label: 'Fleet & Commercial Buyers',  short: 'Fleet',       pct: 20, color: '#8B6BAE',
      desc: 'Corporations, rideshare operators, and government agencies. Prioritise reliability and total cost of ownership.' },
  ]

  const [active, setActive] = React.useState(0)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    let destroyed = false

    const dpr = window.devicePixelRatio || 1

    function getCenter() { return [canvas.width / dpr * 0.5, canvas.height / dpr * 0.5] }
    function getR()      { return Math.min(canvas.width / dpr, canvas.height / dpr) * 0.44 }

    function segAngles() {
      let a = -Math.PI / 2
      return SEGS.map(s => {
        const start = a
        const span  = (s.pct / 100) * Math.PI * 2
        a += span
        return { start, end: a, mid: start + span / 2 }
      })
    }

    function draw() {
      if (destroyed) return
      const st = stateRef.current
      const ctx = canvas.getContext('2d')
      const w = canvas.width / dpr, h = canvas.height / dpr
      ctx.clearRect(0, 0, w, h)
      // transparent — grid SVG behind canvas handles background

      const [cx, cy] = getCenter()
      const R = getR()
      const angles = segAngles()
      const gap = 0.018

      SEGS.forEach((s, i) => {
        const ang     = angles[i]
        const isActive = i === st.active
        const isHover  = i === st.hovering
        const expand   = isActive ? 14 : isHover ? 7 : 0
        const mcx = Math.cos(ang.mid) * expand
        const mcy = Math.sin(ang.mid) * expand

        ctx.save()
        ctx.translate(mcx, mcy)
        ctx.beginPath()
        ctx.moveTo(cx, cy)
        ctx.arc(cx, cy, R + (isActive ? 10 : isHover ? 4 : 0), ang.start + gap, ang.end - gap)
        ctx.closePath()
        ctx.fillStyle = isActive ? s.color : isHover ? s.color + 'cc' : s.color + '66'
        ctx.fill()
        if (isActive) {
          ctx.strokeStyle = s.color
          ctx.lineWidth = 2
          ctx.stroke()
        }
        ctx.restore()

        const labelR = R * 0.68
        const lx = cx + Math.cos(ang.mid) * labelR
        const ly = cy + Math.sin(ang.mid) * labelR
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillStyle = isActive ? 'white' : 'rgba(255,255,255,.85)'
        ctx.font = `${isActive ? '700' : '400'} ${isActive ? 12 : 10}px DM Mono,monospace`
        ctx.fillText(s.short, lx, ly - 7)
        ctx.font = `700 ${isActive ? 15 : 12}px DM Mono,monospace`
        ctx.fillStyle = isActive ? 'white' : 'rgba(255,255,255,.7)'
        ctx.fillText(s.pct + '%', lx, ly + 8)
      })

      // Centre hole
      ctx.beginPath()
      ctx.arc(cx, cy, R * 0.30, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(240,244,250,.95)'
      ctx.fill()
      ctx.strokeStyle = 'rgba(26,58,107,.15)'
      ctx.lineWidth = 1
      ctx.stroke()

      const as = SEGS[st.active]
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillStyle = '#b8932a'
      ctx.font = '700 8px DM Mono,monospace'
      ctx.fillText('MARKET', cx, cy - 10)
      ctx.fillStyle = as.color
      ctx.font = '700 20px DM Mono,monospace'
      ctx.fillText(as.pct + '%', cx, cy + 8)

      st.pulseT += 0.02
      rafRef.current = requestAnimationFrame(draw)
    }

    function getHit(mx, my) {
      const [cx, cy] = getCenter()
      const R = getR()
      const dx = mx - cx, dy = my - cy
      const dist = Math.sqrt(dx * dx + dy * dy)
      if (dist < R * 0.30 || dist > R + 20) return -1
      let angle = Math.atan2(dy, dx)
      if (angle < -Math.PI / 2) angle += Math.PI * 2
      const angles = segAngles()
      for (let i = 0; i < SEGS.length; i++) {
        if (angle >= angles[i].start && angle < angles[i].end) return i
      }
      return -1
    }

    function toCanvasCoords(e) {
      const r  = canvas.getBoundingClientRect()
      return [(e.clientX - r.left), (e.clientY - r.top)]
    }

    const onResize = () => {
      const p = canvas.parentElement
      const w = p.offsetWidth
      const h = p.offsetHeight
      canvas.width  = w * dpr
      canvas.height = h * dpr
      canvas.style.width  = w + 'px'
      canvas.style.height = h + 'px'
      const ctx = canvas.getContext('2d')
      ctx.scale(dpr, dpr)
    }

    const onClick = e => {
      const [mx, my] = toCanvasCoords(e)
      const h = getHit(mx, my)
      if (h >= 0) { stateRef.current.active = h; setActive(h) }
    }

    const onMove = e => {
      const [mx, my] = toCanvasCoords(e)
      stateRef.current.hovering = getHit(mx, my)
      canvas.style.cursor = stateRef.current.hovering >= 0 ? 'pointer' : 'default'
    }

    const onLeave = () => { stateRef.current.hovering = -1 }

    onResize()
    window.addEventListener('resize', onResize)
    canvas.addEventListener('click',     onClick)
    canvas.addEventListener('mousemove', onMove)
    canvas.addEventListener('mouseleave', onLeave)
    draw()

    return () => {
      destroyed = true
      cancelAnimationFrame(rafRef.current)
      window.removeEventListener('resize', onResize)
      canvas.removeEventListener('click',      onClick)
      canvas.removeEventListener('mousemove',  onMove)
      canvas.removeEventListener('mouseleave', onLeave)
    }
  }, [])

  const seg = SEGS[active]

  return (
    <div style={{ position: 'absolute', inset: 0, background: '#f0f4fa', display: 'flex', flexDirection: 'column', overflow: 'hidden', fontFamily: MONO }}>

      {/* Engineering grid — matches BlueprintSlide */}
      <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
        <defs>
          <pattern id="mkt-grid-sm" width="28" height="28" patternUnits="userSpaceOnUse">
            <path d="M28 0L0 0 0 28" fill="none" stroke="rgba(26,58,107,.07)" strokeWidth=".5"/>
          </pattern>
          <pattern id="mkt-grid-lg" width="140" height="140" patternUnits="userSpaceOnUse">
            <path d="M140 0L0 0 0 140" fill="none" stroke="rgba(26,58,107,.12)" strokeWidth="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#mkt-grid-sm)"/>
        <rect width="100%" height="100%" fill="url(#mkt-grid-lg)"/>
      </svg>

      {/* Top label */}
      <div style={{ position: 'relative', zIndex: 2, padding: '14px 20px 0', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ fontSize: 8, color: 'rgba(184,147,42,.75)', letterSpacing: '.20em', fontFamily: MONO }}>
          ORAS · US EV ADDRESSABLE MARKET · CONSUMER SEGMENTS
        </div>
        <div style={{ fontSize: 8, color: 'rgba(26,58,107,.35)', letterSpacing: '.14em', fontFamily: MONO }}>
          CLICK SEGMENT TO EXPLORE
        </div>
      </div>

      {/* Canvas donut — fills remaining space */}
      <div style={{ flex: 1, position: 'relative', minHeight: 0 }}>
        <canvas ref={canvasRef} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}/>
        {/* Blueprint corner marks */}
        {[[{top:8,left:8},'M0,10 L0,0 L10,0'],[{top:8,right:8},'M14,10 L14,0 L4,0'],[{bottom:8,left:8},'M0,4 L0,14 L10,14'],[{bottom:8,right:8},'M14,4 L14,14 L4,14']].map(([pos,d],i)=>(
          <svg key={i} width="14" height="14" style={{ position:'absolute', ...pos, pointerEvents:'none' }}>
            <path d={d} fill="none" stroke="rgba(26,58,107,.25)" strokeWidth="1.5"/>
          </svg>
        ))}
      </div>

      <div style={{ flexShrink: 0, background: 'rgba(255,255,255,.96)', borderTop: '1px solid rgba(26,58,107,.12)', backdropFilter: 'blur(4px)', boxShadow: '0 -2px 16px rgba(10,22,40,.06)', position: 'relative', zIndex: 2 }}>
        <div style={{ height: 2, background: 'linear-gradient(90deg,#b8932a,#d4aa40)', opacity: .7 }}/>

        <div style={{ display: 'flex', alignItems: 'stretch', padding: '14px 20px', gap: 24 }}>

          {/* Segment identity */}
          <div style={{ flexShrink: 0, minWidth: 180 }}>
            <div style={{ fontSize: 8, color: '#b8932a', letterSpacing: '.20em', fontFamily: MONO, marginBottom: 5 }}>SELECTED SEGMENT</div>
            <div style={{ fontSize: 13, fontWeight: 900, color: '#0a1628', lineHeight: 1.2, marginBottom: 6 }}>{seg.label}</div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
              <div style={{ fontSize: 32, fontWeight: 700, color: seg.color, lineHeight: 1, transition: 'color .3s', fontFamily: MONO }}>{seg.pct}%</div>
              <div style={{ fontSize: 9, color: '#8090a4', letterSpacing: '.10em' }}>OF MARKET</div>
            </div>
            {/* Share bar */}
            <div style={{ height: 3, background: 'rgba(26,58,107,.08)', borderRadius: 2, marginTop: 8, overflow: 'hidden', width: 160 }}>
              <div style={{ height: '100%', width: `${seg.pct}%`, background: seg.color, borderRadius: 2, transition: 'width .5s cubic-bezier(.4,0,.2,1), background .3s' }}/>
            </div>
          </div>

          {/* Divider */}
          <div style={{ width: 1, background: 'rgba(26,58,107,.10)', flexShrink: 0 }}/>

          {/* Description */}
          <div style={{ flex: 1, display: 'flex', alignItems: 'center' }}>
            <div style={{ fontSize: 15, color: '#3a4a5a', lineHeight: 1.60, fontFamily: SANS, textAlign: 'justify' }}>{seg.desc}</div>
          </div>

          {/* Divider */}
          <div style={{ width: 1, background: 'rgba(26,58,107,.10)', flexShrink: 0 }}/>

          {/* All segments mini list */}
          <div style={{ flexShrink: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 6, minWidth: 140 }}>
            <div style={{ fontSize: 8, color: '#b8932a', letterSpacing: '.18em', fontFamily: MONO, marginBottom: 2 }}>ALL SEGMENTS</div>
            {SEGS.map((s, i) => (
              <div key={i} onClick={() => { stateRef.current.active = i; setActive(i) }}
                style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', padding: '2px 0' }}>
                <div style={{ width: 7, height: 7, borderRadius: '50%', background: i === active ? s.color : s.color + '66', flexShrink: 0, transition: 'background .2s', boxShadow: i === active ? `0 0 0 2px ${s.color}33` : 'none' }}/>
                <span style={{ fontSize: 10, color: i === active ? '#0a1628' : '#8090a4', fontWeight: i === active ? 700 : 400, letterSpacing: '.06em', fontFamily: MONO, transition: 'color .2s, font-weight .2s', flex: 1 }}>{s.short}</span>
                <span style={{ fontSize: 11, fontWeight: 700, color: i === active ? s.color : '#b0bac8', fontFamily: MONO, transition: 'color .2s' }}>{s.pct}%</span>
              </div>
            ))}
          </div>

        </div>
      </div>
    </div>
  )
}


function CompanyChart() {
  const ITEMS = [
    {
      id: 'sticky',
      label: 'Company Memo',
      title: 'From the outgoing CFO',
      body: `"$60M. Five years. Don't blow it all in Year 1. The Xeno has to ship AND it has to sell. Good luck."`,
      color: '#b8932a',
      x: 58, y: 48, w: 216, h: 156, rotate: -1.5,
      icon: (c) => (
        <g>
          <rect x="0" y="0" width="64" height="60" rx="1" fill={c + '28'} stroke={c} strokeWidth="1.2"/>
          <line x1="0" y1="15" x2="64" y2="15" stroke={c} strokeWidth=".8" opacity=".5"/>
          {[24,33,42,51].map(y => <line key={y} x1="6" y1={y} x2="58" y2={y} stroke={c} strokeWidth=".7" opacity=".4"/>)}
          <path d="M50,0 L64,14 L50,14 Z" fill={c} opacity=".4"/>
        </g>
      ),
    },
    {
      id: 'newspaper',
      label: 'Press Clipping',
      title: 'Austin Business Journal, 2024',
      body: '"Voltex Motors prices IPO above range at $18/share, raising $340M. The Austin EV startup that was founded just two years ago in a converted warehouse, now lists on NASDAQ as VLTX."',
      color: '#1a3a6b',
      x: 316, y: 44, w: 216, h: 156, rotate: 1.2,
      icon: (c) => (
        <g>
          <rect x="0" y="0" width="68" height="58" rx="1" fill="white" stroke={c} strokeWidth="1.2"/>
          <rect x="3" y="3" width="62" height="13" fill={c} opacity=".12"/>
          <text x="34" y="13" textAnchor="middle" fontSize="6.5" fontFamily="DM Mono,monospace" fill={c} fontWeight="800" opacity=".85">NASDAQ: VLTX</text>
          {[22,30,38,46,54].map(y => <line key={y} x1="4" y1={y} x2={y===22?52:64} y2={y} stroke={c} strokeWidth=".8" opacity=".3"/>)}
        </g>
      ),
    },
    {
      id: 'specsheet',
      label: 'Xeno Spec Sheet',
      title: 'Voltex Xeno — Product Brief',
      body: 'MSRP $42,000 · 75 kWh · 310 mi range · 4.1 sec 0-60 · Dual-motor AWD · OTA software stack · Year 1 capacity 18,000 units.',
      color: '#4A7B9D',
      x: 58, y: 222, w: 216, h: 156, rotate: -0.8,
      icon: (c) => (
        <g>
          <rect x="0" y="0" width="68" height="58" rx="1" fill="white" stroke={c} strokeWidth="1.2"/>
          <rect x="0" y="0" width="68" height="10" fill={c} opacity=".18"/>
          <text x="34" y="8" textAnchor="middle" fontSize="5.5" fontFamily="DM Mono,monospace" fill={c} fontWeight="800">VOLTEX XENO</text>
          {[['MSRP','$42,000'],['RANGE','310 mi'],['0-60','4.1 sec'],['BATTERY','75 kWh'],['Y1 CAP','18,000 u']].map(([k,v],i) => (
            <g key={k} transform={`translate(5,${14+i*8.5})`}>
              <text x="0" y="0" fontSize="4.5" fontFamily="DM Mono,monospace" fill={c} opacity=".6">{k}</text>
              <text x="62" y="0" textAnchor="end" fontSize="5" fontFamily="DM Mono,monospace" fill={c} fontWeight="700">{v}</text>
              <line x1="0" y1="2.5" x2="62" y2="2.5" stroke={c} strokeWidth=".4" opacity=".2"/>
            </g>
          ))}
        </g>
      ),
    },
    {
      id: 'chair',
      label: 'Empty Chair',
      title: `That's yours now.`,
      body: 'The previous CFO retired last quarter. You are stepping in ahead of the most consequential product launch in Voltex history. Five years. $60 million. Decide wisely.',
      color: '#8a2020',
      x: 316, y: 218, w: 216, h: 156, rotate: 0.8,
      icon: (c) => (
        <g>
          <rect x="14" y="0" width="42" height="28" rx="3" fill="none" stroke={c} strokeWidth="1.5"/>
          <rect x="10" y="31" width="50" height="16" rx="2" fill="none" stroke={c} strokeWidth="1.5"/>
          <line x1="15" y1="47" x2="12" y2="62" stroke={c} strokeWidth="1.5" strokeLinecap="round"/>
          <line x1="55" y1="47" x2="58" y2="62" stroke={c} strokeWidth="1.5" strokeLinecap="round"/>
          <line x1="15" y1="47" x2="55" y2="47" stroke={c} strokeWidth="1" opacity=".4"/>
          <path d="M10,31 L5,36 L5,46" stroke={c} strokeWidth="1.2" fill="none" strokeLinecap="round"/>
          <path d="M60,31 L65,36 L65,46" stroke={c} strokeWidth="1.2" fill="none" strokeLinecap="round"/>
          <text x="35" y="22" textAnchor="middle" fontSize="16" fontFamily="DM Mono,monospace" fill={c} fontWeight="900" opacity=".22">?</text>
        </g>
      ),
    },
  ]

  const [selected, setSelected] = React.useState(null)
  const [hovered, setHovered]   = React.useState(null)
  const sel = selected !== null ? ITEMS[selected] : null

  return (
    <div style={{ position: 'absolute', inset: 0, background: '#f0f4fa', display: 'flex', flexDirection: 'column', overflow: 'hidden', fontFamily: MONO }}>

      {/* Engineering grid */}
      <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
        <defs>
          <pattern id="cfo-sm" width="28" height="28" patternUnits="userSpaceOnUse">
            <path d="M28 0L0 0 0 28" fill="none" stroke="rgba(26,58,107,.07)" strokeWidth=".5"/>
          </pattern>
          <pattern id="cfo-lg" width="140" height="140" patternUnits="userSpaceOnUse">
            <path d="M140 0L0 0 0 140" fill="none" stroke="rgba(26,58,107,.12)" strokeWidth="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#cfo-sm)"/>
        <rect width="100%" height="100%" fill="url(#cfo-lg)"/>
      </svg>

      {/* Header */}
      <div style={{ flexShrink: 0, padding: '12px 20px 0', position: 'relative', zIndex: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <div style={{ fontSize: 8, color: 'rgba(184,147,42,.75)', letterSpacing: '.20em' }}>VOLTEX MOTORS · CFO OFFICE · AUSTIN TX</div>
        <div style={{ fontSize: 8, color: 'rgba(26,58,107,.30)', letterSpacing: '.14em' }}>CLICK ITEMS TO INSPECT</div>
      </div>

      {/* Desk SVG */}
      <div style={{ flex: 1, position: 'relative', zIndex: 2, minHeight: 0 }}>
        <svg viewBox="0 0 590 430" style={{ width: '100%', height: '100%' }}>
          <defs>
            <filter id="shadow-sm">
              <feDropShadow dx="0" dy="3" stdDeviation="6" floodColor="#0a1628" floodOpacity=".13"/>
            </filter>
            <filter id="shadow-hover">
              <feDropShadow dx="0" dy="6" stdDeviation="12" floodColor="#0a1628" floodOpacity=".20"/>
            </filter>
          </defs>

          {/* Desk surface */}
          <rect x="30" y="30" width="530" height="390" rx="4"
            fill="rgba(255,255,255,.55)" stroke="rgba(26,58,107,.14)" strokeWidth="1.2"/>
          {/* Desk edge shadow strip */}
          <rect x="30" y="406" width="530" height="8" rx="2" fill="rgba(26,58,107,.06)"/>
          {/* Inner desk margin */}
          <rect x="38" y="38" width="514" height="374" rx="3"
            fill="none" stroke="rgba(26,58,107,.06)" strokeWidth="1"/>

          {/* Desk items */}
          {ITEMS.map((item, i) => {
            const isHov = hovered === i
            const isSel = selected === i
            return (
              <g key={item.id}
                transform={`translate(${item.x},${item.y}) rotate(${isSel ? 0 : item.rotate},${item.w/2},${item.h/2})`}
                filter={isSel || isHov ? 'url(#shadow-hover)' : 'url(#shadow-sm)'}
                style={{ cursor: 'pointer', transition: 'filter .2s' }}
                onClick={() => setSelected(selected === i ? null : i)}
                onMouseEnter={() => setHovered(i)}
                onMouseLeave={() => setHovered(null)}>

                {/* Card background */}
                <rect x="0" y="0" width={item.w} height={item.h} rx="3"
                  fill={isSel ? 'white' : 'rgba(255,255,255,.88)'}
                  stroke={isSel ? item.color : isHov ? item.color + '80' : 'rgba(26,58,107,.12)'}
                  strokeWidth={isSel ? 1.5 : 1}/>

                {/* Colour accent bar at top */}
                <rect x="0" y="0" width={item.w} height="3" rx="0"
                  fill={item.color} opacity={isSel ? .9 : .5}/>

                {/* Icon centred upper half */}
                <g transform={`translate(${item.w/2 - 26},12)`}>
                  {item.icon(item.color)}
                </g>

                {/* Label */}
                <text x={item.w/2} y={item.h - 22} textAnchor="middle"
                  fontSize="8" fontFamily="DM Mono,monospace" fontWeight="700"
                  fill={item.color} letterSpacing=".12em" opacity={isSel ? 1 : .7}>
                  {item.label.toUpperCase()}
                </text>

                {/* Hover/selected underline */}
                {(isHov || isSel) && (
                  <line x1={item.w/2 - 20} y1={item.h - 12} x2={item.w/2 + 20} y2={item.h - 12}
                    stroke={item.color} strokeWidth="1.5" opacity=".6"/>
                )}
              </g>
            )
          })}
        </svg>
      </div>

      {/* Bottom detail panel — slides up when item selected */}
      <div style={{
        flexShrink: 0,
        background: 'rgba(255,255,255,.96)',
        borderTop: `2px solid ${sel ? sel.color : 'rgba(26,58,107,.10)'}`,
        backdropFilter: 'blur(4px)',
        boxShadow: '0 -2px 16px rgba(10,22,40,.06)',
        padding: sel ? '14px 24px 16px' : '10px 24px',
        transition: 'padding .2s, border-color .3s',
        position: 'relative', zIndex: 2,
        minHeight: sel ? 90 : 38,
      }}>
        {sel ? (
          <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
            <div style={{ flexShrink: 0 }}>
              <div style={{ fontSize: 10, color: sel.color, letterSpacing: '.20em', fontWeight: 700, marginBottom: 4 }}>
                {sel.label.toUpperCase()}
              </div>
              <div style={{ fontSize: 16, fontWeight: 900, color: '#0a1628', lineHeight: 1.2 }}>{sel.title}</div>
              <div style={{ height: 1.5, width: 28, background: '#b8932a', marginTop: 6 }}/>
            </div>
            <div style={{ flex: 1, fontSize: 15, color: '#3a4a5a', lineHeight: 1.65, fontFamily: SANS, fontStyle: sel.id === 'sticky' ? 'italic' : 'normal' }}>
              {sel.body}
            </div>
            <div onClick={() => setSelected(null)}
              style={{ flexShrink: 0, cursor: 'pointer', fontSize: 10, color: 'rgba(26,58,107,.35)', letterSpacing: '.10em', paddingTop: 2 }}>
              ✕ CLOSE
            </div>
          </div>
        ) : (
          <div style={{ fontSize: 8, color: 'rgba(26,58,107,.30)', letterSpacing: '.18em', textAlign: 'center' }}>
            CLICK ANY ITEM ON THE DESK TO INSPECT
          </div>
        )}
      </div>
    </div>
  )
}
function ProductBlueprint() {
  const mountRef = useRef(null)
  const rafRef   = useRef(null)

  useEffect(() => {
    const mount = mountRef.current
    if (!mount) return
    let destroyed = false
    let resumeTimer = null

    import('three').then((THREE) => {
      if (destroyed) return

      const W = mount.offsetWidth
      const H = mount.offsetHeight

      // Renderer — identical to preview
      const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false })
      renderer.setPixelRatio(Math.min(devicePixelRatio, 2))
      renderer.setSize(W, H)
      renderer.setClearColor(0x0b1a2e, 1)
      renderer.outputEncoding = THREE.sRGBEncoding
      renderer.toneMapping = THREE.ACESFilmicToneMapping
      renderer.toneMappingExposure = 1.2
      renderer.shadowMap.enabled = true
      renderer.shadowMap.type = THREE.PCFSoftShadowMap
      Object.assign(renderer.domElement.style, {
        position: 'absolute', top: '0', left: '0', width: '100%', height: '100%',
      })
      mount.appendChild(renderer.domElement)

      // Scene
      const scene = new THREE.Scene()

      // Camera
      const camera = new THREE.PerspectiveCamera(40, W / H, 0.01, 200)
      camera.position.set(4, 1.8, 4)

      // Lights — flat even blue, no dramatic shadows
      scene.add(new THREE.AmbientLight(0x7ab0ff, 3.0))
      const key = new THREE.DirectionalLight(0xaaddff, 1.5)
      key.position.set(5, 6, 4); scene.add(key)
      const fill = new THREE.DirectionalLight(0x7ab0ff, 1.5)
      fill.position.set(-5, 3, -2); scene.add(fill)
      const btm = new THREE.DirectionalLight(0x4488cc, 0.8)
      btm.position.set(0, -5, 0); scene.add(btm)

      // OrbitControls
      const controls = new OrbitControls(camera, renderer.domElement)
      controls.enableDamping   = true
      controls.dampingFactor   = 0.08
      controls.enablePan       = false
      controls.autoRotate      = true
      controls.autoRotateSpeed = 0.7
      controls.minDistance     = 1.5
      controls.maxDistance     = 14
      controls.maxPolarAngle   = Math.PI / 2 + 0.05
      controls.addEventListener('start', () => { controls.autoRotate = false; clearTimeout(resumeTimer) })
      controls.addEventListener('end',   () => { resumeTimer = setTimeout(() => { controls.autoRotate = true }, 3000) })

      // Load GLTF
      const loader = new GLTFLoader()
      loader.load('/car.gltf', (gltf) => {
        if (destroyed) return
        const model = gltf.scene

        model.traverse(child => {
          if (!child.isMesh) return
          child.frustumCulled = false
          // Blueprint material — completely flat, no specularity, pure technical drawing look
          const mats = Array.isArray(child.material) ? child.material : [child.material]
          mats.forEach(mat => {
            if (!mat) return
            mat.map = null; mat.normalMap = null; mat.roughnessMap = null
            mat.metalnessMap = null; mat.aoMap = null; mat.emissiveMap = null
            mat.envMap = null
            mat.color.set(0x0b1a2e)
            if (mat.emissive) mat.emissive.set(0x000000)
            if (mat.roughness !== undefined) mat.roughness = 1.0
            if (mat.metalness !== undefined) mat.metalness = 0.0
            if (mat.emissiveIntensity !== undefined) mat.emissiveIntensity = 0
            mat.needsUpdate = true
          })
          // Edge lines on static meshes only — bright cyan for technical drawing feel
          if (!child.isSkinnedMesh) {
            try {
              child.add(new THREE.LineSegments(
                new THREE.EdgesGeometry(child.geometry, 15),
                new THREE.LineBasicMaterial({ color: 0x4af0ff, transparent: true, opacity: 0.85 })
              ))
            } catch(e) {}
          }
        })

        scene.add(model)

        // Fit camera to model
        const box     = new THREE.Box3().setFromObject(model)
        const centre  = box.getCenter(new THREE.Vector3())
        const size    = box.getSize(new THREE.Vector3())
        const fitDist = Math.max(size.x, size.y, size.z) * 2.2

        camera.position.set(centre.x + fitDist * 0.55, centre.y + size.y * 0.35, centre.z + fitDist * 0.75)
        camera.near = fitDist * 0.01
        camera.far  = fitDist * 20
        camera.updateProjectionMatrix()
        controls.target.copy(centre)
        controls.update()

        // Play door animation in reverse — starts closed, opens outward
        if (gltf.animations?.length) {
          const mixer = new THREE.AnimationMixer(model)
          gltf.animations.forEach(clip => {
            const action = mixer.clipAction(clip)
            action.timeScale = -1          // play backwards
            action.time = clip.duration    // start at end (= closed position)
            action.play()
          })
          mount._mixer = mixer
        }

        // Floor grid at ground level
        const groundY = box.min.y + size.y * 0.01
        const gridMain = new THREE.GridHelper(size.x * 3, 30, 0x1a3a6b, 0x1a3a6b)
        gridMain.material.transparent = true; gridMain.material.opacity = 0.30
        gridMain.position.set(centre.x, groundY, centre.z); scene.add(gridMain)
        const gridSub = new THREE.GridHelper(size.x * 3, 120, 0x1a3a6b, 0x1a3a6b)
        gridSub.material.transparent = true; gridSub.material.opacity = 0.10
        gridSub.position.set(centre.x, groundY, centre.z); scene.add(gridSub)

      }, undefined, err => console.error('GLTF:', err))

      // Render loop
      const clock = new THREE.Clock()
      function animate() {
        if (destroyed) return
        rafRef.current = requestAnimationFrame(animate)
        const delta = clock.getDelta()
        if (mount._mixer) mount._mixer.update(delta)
        controls.update()
        renderer.render(scene, camera)
      }
      animate()

      // Resize
      const onResize = () => {
        const w = mount.offsetWidth, h = mount.offsetHeight
        renderer.setSize(w, h); camera.aspect = w / h; camera.updateProjectionMatrix()
      }
      window.addEventListener('resize', onResize)

      mount._cleanup = () => {
        destroyed = true
        cancelAnimationFrame(rafRef.current)
        clearTimeout(resumeTimer)
        window.removeEventListener('resize', onResize)
        controls.dispose(); renderer.dispose()
        if (mount.contains(renderer.domElement)) mount.removeChild(renderer.domElement)
      }
    }).catch(err => console.error('Three.js import failed:', err))

    return () => {
      destroyed = true
      cancelAnimationFrame(rafRef.current)
      if (mount._cleanup) mount._cleanup()
    }
  }, [])

  return (
    <div style={{ position: 'absolute', inset: 0, background: '#0b1a2e', overflow: 'hidden' }}>
      {/* CSS blueprint grid */}
      <div style={{
        position: 'absolute', inset: 0, pointerEvents: 'none',
        backgroundImage: `
          linear-gradient(rgba(26,58,107,0.22) 1px, transparent 1px),
          linear-gradient(90deg, rgba(26,58,107,0.22) 1px, transparent 1px),
          linear-gradient(rgba(26,58,107,0.08) 1px, transparent 1px),
          linear-gradient(90deg, rgba(26,58,107,0.08) 1px, transparent 1px)`,
        backgroundSize: '80px 80px, 80px 80px, 20px 20px, 20px 20px',
      }} />

      {/* Three.js canvas mount */}
      <div ref={mountRef} style={{ position: 'absolute', inset: 0 }} />

      {/* Overlay UI — pointer-events none so orbit controls work */}
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', fontFamily: MONO }}>

        {/* Top-left title */}
        <div style={{ position: 'absolute', top: 14, left: 16 }}>
          <div style={{ fontSize: 11, color: '#4a8fd4', letterSpacing: '.20em', marginBottom: 3 }}>VOLTEX MOTORS · AUSTIN TX</div>
          <div style={{ fontSize: 18, fontWeight: 700, color: 'rgba(255,255,255,.92)', letterSpacing: '.10em' }}>VOLTEX XENO</div>
          <div style={{ fontSize: 10, color: 'rgba(255,255,255,.28)', letterSpacing: '.14em', marginTop: 2 }}>VLTX-001 · EV COUPE · DWG: AAS-XN-004</div>
          <div style={{ marginTop: 7, height: 1, width: 120, background: 'rgba(74,143,212,.28)' }} />
        </div>

        {/* Top-right spec grid */}
        <div style={{ position: 'absolute', top: 14, right: 14, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 5 }}>
          {[
            { label: 'MSRP',      val: '$42,000'  },
            { label: 'EPA RANGE', val: '310 mi'   },
            { label: '0–60 MPH',  val: '4.1 sec'  },
            { label: 'BATTERY',   val: '75 kWh'   },
            { label: 'TOP SPEED', val: '145 mph'  },
            { label: 'Y1 TARGET', val: '18K units', gold: true },
          ].map((s, i) => (
            <div key={i} style={{
              padding: '6px 10px', borderRadius: 2,
              background: s.gold ? 'rgba(184,147,42,.12)' : 'rgba(11,26,46,.82)',
              border: `1px solid ${s.gold ? 'rgba(184,147,42,.35)' : 'rgba(74,143,212,.20)'}`,
            }}>
              <div style={{ fontSize: 9, color: s.gold ? '#b8932a' : 'rgba(74,143,212,.65)', letterSpacing: '.12em', marginBottom: 2 }}>{s.label}</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: s.gold ? '#d4aa40' : 'rgba(255,255,255,.85)' }}>{s.val}</div>
            </div>
          ))}
        </div>

        {/* Bottom-left dimensions */}
        <div style={{ position: 'absolute', bottom: 44, left: 16, display: 'flex', gap: 18 }}>
          {[['LENGTH','4,760 mm'],['WIDTH','1,920 mm'],['HEIGHT','1,445 mm'],['WHEELBASE','2,875 mm']].map(([l,v],i) => (
            <div key={i}>
              <div style={{ fontSize: 9, color: '#b8932a', letterSpacing: '.12em', marginBottom: 2 }}>{l}</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: 'rgba(255,255,255,.70)' }}>{v}</div>
            </div>
          ))}
        </div>

        {/* Bottom-right title block */}
        <div style={{
          position: 'absolute', bottom: 14, right: 14, minWidth: 200,
          background: 'rgba(11,26,46,.88)', border: '1px solid rgba(74,143,212,.20)',
          borderTop: '2px solid #b8932a', borderRadius: 2, padding: '9px 15px',
        }}>
          <div style={{ fontSize: 9, color: 'rgba(255,255,255,.26)', letterSpacing: '.12em', marginBottom: 3 }}>SCALE 1:25 · DATE: 2025 · DRW: E.CHEN</div>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'rgba(255,255,255,.82)', letterSpacing: '.10em', marginBottom: 4 }}>3-VIEW ENGINEERING BLUEPRINT</div>
          <div style={{ height: 1, background: 'rgba(74,143,212,.18)', marginBottom: 4 }} />
          <div style={{ fontSize: 9, color: 'rgba(184,147,42,.65)', letterSpacing: '.10em' }}>CONFIDENTIAL · VOLTEX MOTORS INC.</div>
        </div>

        {/* Drag hint */}
        <div style={{ position: 'absolute', bottom: 14, left: '50%', transform: 'translateX(-50%)', fontSize: 10, color: 'rgba(74,143,212,.50)', letterSpacing: '.14em' }}>
          DRAG TO ROTATE · SCROLL TO ZOOM
        </div>

        {/* Corner brackets */}
        {[[{top:7,left:7},'M0,12 L0,0 L12,0'],[{top:7,right:7},'M18,12 L18,0 L6,0'],[{bottom:7,left:7},'M0,6 L0,18 L12,18'],[{bottom:7,right:7},'M18,6 L18,18 L6,18']].map(([pos,d],i)=>(
          <svg key={i} width="18" height="18" style={{ position: 'absolute', ...pos }}>
            <path d={d} fill="none" stroke="rgba(74,143,212,0.40)" strokeWidth="1.2"/>
          </svg>
        ))}
      </div>
    </div>
  )
}

const DEPT_COLORS = {
  'R&D':        '#1E5A9C',
  'Sales':      '#B06020',
  'Operations': '#1A6B45',
  'Marketing':  '#5B3FA0',
}

// Angles for 4 orbiting nodes: top, right, bottom, left
const ORBIT_ANGLES = [-Math.PI/2, 0, Math.PI/2, Math.PI]

function DeptIcon({ name, color, size = 44 }) {
  const s = size
  if (name === 'R&D') return (
    <svg width={s} height={s} viewBox="0 0 44 44" fill="none">
      <circle cx="22" cy="22" r="5" fill={color}/>
      <ellipse cx="22" cy="22" rx="19" ry="7" stroke={color} strokeWidth="1.8" fill="none"/>
      <ellipse cx="22" cy="22" rx="19" ry="7" stroke={color} strokeWidth="1.8" fill="none" transform="rotate(60 22 22)"/>
      <ellipse cx="22" cy="22" rx="19" ry="7" stroke={color} strokeWidth="1.8" fill="none" transform="rotate(120 22 22)"/>
    </svg>
  )
  if (name === 'Sales') return (
    <svg width={s} height={s} viewBox="0 0 44 44" fill="none">
      <line x1="4" y1="38" x2="40" y2="38" stroke={color} strokeWidth="2"/>
      <rect x="6"  y="26" width="8" height="12" rx="1.5" fill={color} opacity="0.35"/>
      <rect x="18" y="18" width="8" height="20" rx="1.5" fill={color} opacity="0.6"/>
      <rect x="30" y="8"  width="8" height="30" rx="1.5" fill={color}/>
      <polyline points="10,28 22,18 34,8" stroke={color} strokeWidth="2" strokeLinecap="round" fill="none"/>
    </svg>
  )
  if (name === 'Operations') return (
    <svg width={s} height={s} viewBox="0 0 44 44" fill="none">
      <circle cx="22" cy="22" r="5" fill={color}/>
      <circle cx="22" cy="22" r="11" stroke={color} strokeWidth="4" fill="none"/>
      <circle cx="22" cy="22" r="18" stroke={color} strokeWidth="1.8" strokeDasharray="5 4" fill="none"/>
    </svg>
  )
  return (
    <svg width={s} height={s} viewBox="0 0 44 44" fill="none">
      <polygon points="10,12 10,32 30,38 30,6" fill={color} opacity="0.7"/>
      <rect x="2" y="15" width="10" height="10" rx="2" fill={color}/>
      <path d="M32,10 Q42,22 32,34" stroke={color} strokeWidth="2" strokeLinecap="round" fill="none"/>
      <path d="M35,6 Q48,22 35,38" stroke={color} strokeWidth="1.6" strokeLinecap="round" fill="none" opacity="0.5"/>
    </svg>
  )
}

function DeptCircuit({ departments, sym = '$', suffix = 'K', maxChangeRate = 0.30 }) {
  const [active, setActive] = useState(null)
  const containerRef = useRef(null)
  const [dims, setDims] = useState({ w: 600, h: 400 })

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver(([e]) => {
      setDims({ w: e.contentRect.width, h: e.contentRect.height })
    })
    ro.observe(el)
    setDims({ w: el.offsetWidth, h: el.offsetHeight })
    return () => ro.disconnect()
  }, [])

  const depts = departments?.length > 0 ? departments : [
    { name: 'R&D', background: '' },
    { name: 'Sales', background: '' },
    { name: 'Operations', background: '' },
    { name: 'Marketing', background: '' },
  ]

  const { w, h } = dims
  // Detail panel height when a rival is selected.
  const panelH = active !== null ? h * 0.44 : 0
  const usableH = h - panelH

  // Two size states: expanded (idle) vs compact (panel open)
  const expanded = active === null
  const sizeBase = expanded ? Math.min(w, h) : Math.min(w, usableH)

  const cx = w / 2
  const cy = expanded ? h * 0.48 : usableH * 0.48
  const orbitR = sizeBase * (expanded ? 0.28 : 0.26)
  const hubR   = sizeBase * (expanded ? 0.10 : 0.085)
  const nodeR  = sizeBase * (expanded ? 0.10 : 0.078)

  const activeDept = active !== null ? depts[active] : null
  const activeColor = activeDept ? (DEPT_COLORS[activeDept.name] || '#1a3a6b') : '#1a3a6b'

  return (
    <div ref={containerRef} style={{ position: 'absolute', inset: 0, overflow: 'hidden', background: '#f0f4fa' }}>

      {/* Blueprint grid — matches rest of storyboard */}
      <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
        <defs>
          <pattern id="dg-sm" width="28" height="28" patternUnits="userSpaceOnUse">
            <path d="M28 0L0 0 0 28" fill="none" stroke="rgba(26,58,107,.07)" strokeWidth=".5"/>
          </pattern>
          <pattern id="dg-lg" width="140" height="140" patternUnits="userSpaceOnUse">
            <path d="M140 0L0 0 0 140" fill="none" stroke="rgba(26,58,107,.12)" strokeWidth="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#dg-sm)"/>
        <rect width="100%" height="100%" fill="url(#dg-lg)"/>
      </svg>

      {/* ── SVG layer: orbit rings + spokes + crosshair ── */}
      <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
        {/* Outer orbit ring */}
        <circle cx={cx} cy={cy} r={orbitR}
          fill="none" stroke="rgba(26,58,107,.12)" strokeWidth="1" strokeDasharray="6 5"
        />
        {/* Inner faint ring */}
        <circle cx={cx} cy={cy} r={orbitR * 0.55}
          fill="none" stroke="rgba(26,58,107,.06)" strokeWidth="1"
        />
        {/* Tick marks on orbit ring */}
        {Array.from({ length: 48 }, (_, i) => {
          const a = (i / 48) * Math.PI * 2
          const maj = i % 12 === 0, mid = i % 4 === 0
          const len = maj ? 8 : mid ? 5 : 3
          const r1 = orbitR - 1, r2 = orbitR - 1 + len
          return (
            <line key={i}
              x1={cx + r1 * Math.cos(a)} y1={cy + r1 * Math.sin(a)}
              x2={cx + r2 * Math.cos(a)} y2={cy + r2 * Math.sin(a)}
              stroke={`rgba(26,58,107,${maj ? .30 : .12})`}
              strokeWidth={maj ? 1.2 : 0.7}
            />
          )
        })}
        {/* Spoke lines hub → node */}
        {depts.map((d, i) => {
          const angle = ORBIT_ANGLES[i]
          const nx = cx + orbitR * Math.cos(angle)
          const ny = cy + orbitR * Math.sin(angle)
          const color = DEPT_COLORS[d.name] || '#1a3a6b'
          const isActive = active === i
          return (
            <line key={i}
              x1={cx} y1={cy} x2={nx} y2={ny}
              stroke={isActive ? color : 'rgba(26,58,107,.14)'}
              strokeWidth={isActive ? 1.8 : 0.8}
              strokeDasharray={isActive ? 'none' : '4 5'}
              style={{ transition: 'stroke .4s, stroke-width .4s' }}
            />
          )
        })}
        {/* Hub crosshair */}
        <line x1={cx - hubR * 0.6} y1={cy} x2={cx + hubR * 0.6} y2={cy} stroke="rgba(184,147,42,.5)" strokeWidth="1"/>
        <line x1={cx} y1={cy - hubR * 0.6} x2={cx} y2={cy + hubR * 0.6} stroke="rgba(184,147,42,.5)" strokeWidth="1"/>
        {/* Corner brackets */}
        {[[28,18],[w-28,18],[28,h-18],[w-28,h-18]].map(([bx,by], bi) => {
          const sx = bx < w/2 ? 1 : -1, sy = by < h/2 ? 1 : -1
          const s2=10, d2=3
          return <path key={bi} d={`M${bx+sx*(d2+s2)},${by+sy*d2} L${bx+sx*d2},${by+sy*d2} L${bx+sx*d2},${by+sy*(d2+s2)}`}
            stroke="rgba(26,58,107,.22)" strokeWidth="1" fill="none"/>
        })}
      </svg>

      {/* ── Hub centre ── */}
      <div style={{
        position: 'absolute',
        left: cx - hubR, top: cy - hubR,
        width: hubR * 2, height: hubR * 2,
        borderRadius: '50%',
        background: active !== null
          ? `rgba(255,255,255,.97)`
          : 'rgba(255,255,255,.85)',
        border: `1.5px solid ${active !== null ? activeColor + 'aa' : 'rgba(184,147,42,.50)'}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        transition: 'left .5s cubic-bezier(.4,0,.2,1), top .5s cubic-bezier(.4,0,.2,1), width .5s cubic-bezier(.4,0,.2,1), height .5s cubic-bezier(.4,0,.2,1), border-color .4s, box-shadow .4s',
        boxShadow: active !== null
          ? `0 0 0 6px ${activeColor}14, 0 4px 24px rgba(26,58,107,.14)`
          : '0 0 0 6px rgba(184,147,42,.08), 0 4px 16px rgba(26,58,107,.10)',
      }}>
        {active === null ? (
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontFamily: MONO, fontSize: 11, color: '#b8932a', letterSpacing: '.14em', fontWeight: 700 }}>SELECT</div>
            <div style={{ fontFamily: MONO, fontSize: 9, color: 'rgba(26,58,107,.45)', letterSpacing: '.10em', marginTop: 3 }}>DEPT</div>
          </div>
        ) : (
          <DeptIcon name={activeDept.name} color={activeColor} size={Math.max(28, hubR * 0.85)}/>
        )}
      </div>

      {/* ── Orbit nodes ── */}
      {depts.map((d, i) => {
        const angle = ORBIT_ANGLES[i]
        const nx = cx + orbitR * Math.cos(angle)
        const ny = cy + orbitR * Math.sin(angle)
        const color = DEPT_COLORS[d.name] || '#1a3a6b'
        const isActive = active === i
        const isOther  = active !== null && !isActive

        // Range chip — shows the floor/ceiling per department. Pulled from the
        // scenario_info payload (min_spend/max_spend); falls back gracefully.
        const hasRange = (d.min_spend > 0 || d.max_spend > 0)

        return (
          <React.Fragment key={d.name}>
            <div
              onClick={() => setActive(isActive ? null : i)}
              style={{
                position: 'absolute',
                left: nx - nodeR, top: ny - nodeR,
                width: nodeR * 2, height: nodeR * 2,
                borderRadius: '50%',
                cursor: 'pointer',
                background: isActive
                  ? `rgba(255,255,255,1)`
                  : 'rgba(255,255,255,.80)',
                border: `${isActive ? 2 : 1.2}px solid ${isActive ? color : color + '50'}`,
                display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 5,
                transform: isActive ? 'scale(1.16)' : isOther ? 'scale(0.90)' : 'scale(1)',
                opacity: isOther ? 0.40 : 1,
                transition: 'left .5s cubic-bezier(.4,0,.2,1), top .5s cubic-bezier(.4,0,.2,1), width .5s cubic-bezier(.4,0,.2,1), height .5s cubic-bezier(.4,0,.2,1), transform .45s cubic-bezier(.4,0,.2,1), opacity .45s, border-color .4s, box-shadow .4s',
                boxShadow: isActive
                  ? `0 0 0 5px ${color}18, 0 8px 28px rgba(26,58,107,.18)`
                  : `0 2px 10px rgba(26,58,107,.08)`,
                zIndex: isActive ? 10 : 1,
              }}
            >
              <DeptIcon name={d.name} color={color} size={nodeR * 0.72}/>
              <div style={{
                fontFamily: MONO,
                fontSize: Math.max(7, nodeR * 0.165),
                fontWeight: 800,
                letterSpacing: '.12em',
                color: isActive ? color : 'rgba(26,58,107,.65)',
                textTransform: 'uppercase',
                transition: 'color .4s',
                textAlign: 'center',
                lineHeight: 1.1,
              }}>
                {d.name}
              </div>
            </div>
            {/* Min/max chip — positioned just below the node ring. */}
            {hasRange && (
              <div
                onClick={() => setActive(isActive ? null : i)}
                style={{
                  position: 'absolute',
                  left: nx - 50,
                  top: ny + nodeR + 6,
                  width: 100, textAlign: 'center',
                  fontFamily: MONO,
                  fontSize: 10,
                  fontWeight: 700,
                  color: isActive ? color : 'rgba(26,58,107,.55)',
                  letterSpacing: '.04em',
                  pointerEvents: 'auto',
                  cursor: 'pointer',
                  opacity: isOther ? 0.4 : 1,
                  transition: 'opacity .45s, color .4s, top .5s cubic-bezier(.4,0,.2,1), left .5s cubic-bezier(.4,0,.2,1)',
                  zIndex: 2,
                }}
              >
                {fmtCur(d.min_spend, sym, suffix)}–{fmtCur(d.max_spend, sym, suffix)}
              </div>
            )}
          </React.Fragment>
        )
      })}

      <div style={{
        position: 'absolute', left: 24, right: 24, bottom: 0,
        height: active !== null ? '52%' : '0%',
        transition: 'height .5s cubic-bezier(.4,0,.2,1)',
        overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', inset: 0,
          background: 'rgba(255,255,255,.97)',
          border: `1px solid rgba(26,58,107,.12)`,
          borderBottom: 'none',
          borderTop: `3px solid ${activeColor}`,
          padding: '14px 20px 16px',
          boxShadow: '0 -4px 20px rgba(26,58,107,.08)',
          transition: 'border-top-color .4s',
          overflow: 'auto',
        }}>
          {activeDept && (
            <div style={{ animation: 'fadeUp .3s ease both' }}>
              {/* Header */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                <div style={{ width: 3, height: 16, background: activeColor, borderRadius: 1, transition: 'background .4s' }}/>
                <div style={{ fontFamily: MONO, fontSize: 9, fontWeight: 800, color: activeColor, letterSpacing: '.20em', textTransform: 'uppercase', transition: 'color .4s' }}>
                  {activeDept.name}
                </div>
                {(activeDept.min_spend > 0 || activeDept.max_spend > 0) && (
                  <div style={{
                    marginLeft: 'auto',
                    fontFamily: MONO, fontSize: 10, fontWeight: 700,
                    color: 'rgba(26,58,107,.55)',
                    padding: '3px 9px',
                    background: 'rgba(26,58,107,.04)',
                    border: '1px solid rgba(26,58,107,.10)',
                    borderRadius: 3,
                    letterSpacing: '.02em',
                  }}>
                    Range: {fmtCur(activeDept.min_spend, sym, suffix)}–{fmtCur(activeDept.max_spend, sym, suffix)}
                  </div>
                )}
              </div>

              {/* Section 1: Background (flavor) */}
              {activeDept.background && (
                <div style={{ marginBottom: 10 }}>
                  <div style={{ fontFamily: MONO, fontSize: 8, fontWeight: 700, color: '#8090a4', letterSpacing: '.16em', textTransform: 'uppercase', marginBottom: 4 }}>
                    What the team does
                  </div>
                  <div style={{ fontSize: 15, color: '#3a4a5a', lineHeight: 1.60, fontFamily: SANS, textAlign: 'justify' }}>
                    {activeDept.background}
                  </div>
                </div>
              )}

              {activeDept.description && activeDept.description !== activeDept.background && (
                <div style={{ marginBottom: 10 }}>
                  <div style={{ fontFamily: MONO, fontSize: 8, fontWeight: 700, color: '#8090a4', letterSpacing: '.16em', textTransform: 'uppercase', marginBottom: 4 }}>
                    How it behaves
                  </div>
                  <div style={{ fontSize: 15, color: '#3a4a5a', lineHeight: 1.60, fontFamily: SANS, textAlign: 'justify' }}>
                    {activeDept.description}
                  </div>
                </div>
              )}

              {/* Section 3: Strategy options (one per year) */}
              {activeDept.strategy_options && activeDept.strategy_options.length > 0 && (
                <div>
                  <div style={{ fontFamily: MONO, fontSize: 8, fontWeight: 700, color: '#8090a4', letterSpacing: '.16em', textTransform: 'uppercase', marginBottom: 6 }}>
                    Strategic directions (pick one per year)
                  </div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {activeDept.strategy_options.map((opt) => (
                      <div
                        key={opt.key}
                        style={{
                          fontFamily: SANS,
                          padding: '6px 10px',
                          background: `${activeColor}10`,
                          border: `1px solid ${activeColor}40`,
                          borderRadius: 6,
                          flexShrink: 0,
                          maxWidth: 200,
                        }}
                      >
                        <div style={{ fontSize: 12, fontWeight: 700, color: activeColor, marginBottom: opt.description ? 3 : 0 }}>
                          {opt.label}
                        </div>
                        {opt.description && (
                          <div style={{ fontSize: 11, color: '#3a4a5a', lineHeight: 1.45, fontFamily: SANS }}>
                            {opt.description}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  {activeDept.strategy_options.some(o => Object.keys(o.synergy || {}).length > 0) && (
                    <div style={{ marginTop: 10 }}>
                      <div style={{ fontFamily: MONO, fontSize: 8, fontWeight: 700, color: '#8090a4', letterSpacing: '.16em', textTransform: 'uppercase', marginBottom: 5 }}>
                        Cross-dept synergies
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                        {activeDept.strategy_options
                          .filter(o => Object.keys(o.synergy || {}).length > 0)
                          .map(o => (
                            <div key={o.key} style={{ display: 'flex', alignItems: 'baseline', gap: 6, fontSize: 11, lineHeight: 1.4, color: '#3a4a5a' }}>
                              <span style={{ fontWeight: 700, color: activeColor, minWidth: 90 }}>
                                {o.label}
                              </span>
                              <span style={{ color: '#8090a4' }}>boosts</span>
                              {Object.entries(o.synergy).map(([dept, bonus], idx, arr) => (
                                <span key={dept} style={{ fontFamily: SANS, fontSize: 11 }}>
                                  <span style={{ fontWeight: 700, color: DEPT_COLORS[dept] || '#3a4a5a' }}>{dept}</span>
                                  <span style={{ color: '#1A6B45', fontFamily: MONO, fontWeight: 700, marginLeft: 3 }}>+{Math.round(bonus * 100)}%</span>
                                  {idx < arr.length - 1 && <span style={{ color: '#8090a4' }}>, </span>}
                                </span>
                              ))}
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div style={{
        position: 'absolute', right: 24, bottom: active !== null ? -100 : 14,
        fontFamily: MONO, fontSize: 9, color: 'rgba(26,58,107,.5)',
        letterSpacing: '.04em', maxWidth: 340, textAlign: 'right',
        transition: 'bottom .4s',
        pointerEvents: 'none',
      }}>
        Year 1 is unconstrained. Year 2+: each lever can shift at most ±{Math.round(maxChangeRate * 100)}% from the previous year's lock.
      </div>

    </div>
  )
}

function RoleColumns() {
  return (
    <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }} viewBox="0 0 520 320">
      <text x="40" y="40" fontSize="9" fontFamily={MONO} fill="rgba(26,58,107,.40)" letterSpacing=".18em">YOUR RESPONSIBILITIES</text>
      {[
        { label: 'ALLOCATE', sub: 'Budget across\n4 departments', h: 160, x: 60,  color: '#1a3a6b' },
        { label: 'DECIDE',   sub: 'Strategic direction\neach year',    h: 200, x: 200, color: '#b8932a' },
        { label: 'LOCK IN',  sub: 'Decisions are\npermanent',         h: 240, x: 340, color: '#1a5c3a' },
      ].map((col, i) => (
        <g key={i}>
          {/* Column rising from baseline */}
          <rect x={col.x} y={290 - col.h} width="100" height={col.h} rx="2"
            fill={`${col.color}08`} stroke={col.color} strokeWidth="1.2">
            <animate attributeName="height" from="0" to={col.h} dur=".8s" begin={`${.4 + i * .3}s`} fill="freeze"/>
            <animate attributeName="y" from="290" to={290 - col.h} dur=".8s" begin={`${.4 + i * .3}s`} fill="freeze"/>
          </rect>
          <text x={col.x + 50} y={285 - col.h} textAnchor="middle" fontSize="10" fontFamily={MONO} fontWeight="700" fill={col.color} opacity="0">
            <animate attributeName="opacity" from="0" to="1" dur=".4s" begin={`${1.0 + i * .3}s`} fill="freeze"/>
            {col.label}
          </text>
          <text x={col.x + 50} y={265 - col.h} textAnchor="middle" fontSize="8" fontFamily={MONO} fill="#6a7a8a" opacity="0">
            <animate attributeName="opacity" from="0" to="1" dur=".4s" begin={`${1.1 + i * .3}s`} fill="freeze"/>
            {col.sub.split('\n')[0]}
          </text>
          <text x={col.x + 50} y={253 - col.h} textAnchor="middle" fontSize="8" fontFamily={MONO} fill="#6a7a8a" opacity="0">
            <animate attributeName="opacity" from="0" to="1" dur=".4s" begin={`${1.2 + i * .3}s`} fill="freeze"/>
            {col.sub.split('\n')[1]}
          </text>
          {/* Height label */}
          <text x={col.x + 50} y={282} textAnchor="middle" fontSize="8" fontFamily={MONO} fill="rgba(26,58,107,.50)" opacity="0">
            <animate attributeName="opacity" from="0" to="1" dur=".4s" begin={`${1.4 + i * .3}s`} fill="freeze"/>
            Y1 → Y{i + 3}
          </text>
        </g>
      ))}
      {/* Baseline */}
      <line x1="40" y1="290" x2="480" y2="290" stroke="rgba(26,58,107,.25)" strokeWidth="1" strokeDasharray="500" strokeDashoffset="500">
        <animate attributeName="stroke-dashoffset" from="500" to="0" dur=".6s" fill="freeze"/>
      </line>
    </svg>
  )
}

function DefaultBlueprint() {
  return (
    <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }} viewBox="0 0 520 320">
      <circle cx="220" cy="160" r="80" fill="rgba(26,58,107,.06)" stroke="#1a3a6b" strokeWidth="1.2" strokeDasharray="503" strokeDashoffset="503">
        <animate attributeName="stroke-dashoffset" from="503" to="0" dur="1.5s" fill="freeze"/>
      </circle>
    </svg>
  )
}

// Five-year budget timeline.
function MandateLedger({ budget = 60_000_000, numPeriods = 5, sym = '$', suffix = 'K' }) {
  const [active, setActive] = useState(0)  // which year is highlighted

  // Pre-baked sample allocations across the five years.
  const SAMPLE_MIX = [
    [0.30, 0.25, 0.25, 0.20],  // Y1: balanced launch
    [0.28, 0.27, 0.25, 0.20],
    [0.25, 0.30, 0.25, 0.20],
    [0.22, 0.32, 0.26, 0.20],
    [0.20, 0.32, 0.28, 0.20],
  ]
  // Department palette (matches the rest of the deck)
  const DEPTS = [
    { name: 'R&D',        color: '#1A3A6B' },
    { name: 'Sales',      color: '#8A6A10' },
    { name: 'Operations', color: '#3D7A58' },
    { name: 'Marketing',  color: '#4A2A7A' },
  ]

  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', background: '#f0f4fa', padding: '32px 36px', display: 'flex', flexDirection: 'column' }}>
      {/* Grid background — matches other blueprint slides */}
      <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
        <defs>
          <pattern id="ml-sm" width="28" height="28" patternUnits="userSpaceOnUse">
            <path d="M28 0L0 0 0 28" fill="none" stroke="rgba(26,58,107,.07)" strokeWidth=".5"/>
          </pattern>
          <pattern id="ml-lg" width="140" height="140" patternUnits="userSpaceOnUse">
            <path d="M140 0L0 0 0 140" fill="none" stroke="rgba(26,58,107,.12)" strokeWidth="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#ml-sm)"/>
        <rect width="100%" height="100%" fill="url(#ml-lg)"/>
      </svg>

      <div style={{ position: 'relative', zIndex: 1, display: 'flex', flexDirection: 'column', height: '100%' }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 4 }}>
          <div style={{ fontSize: 11, color: 'rgba(184,147,42,.75)', letterSpacing: '.20em', fontFamily: MONO, textTransform: 'uppercase' }}>
            Annual budget cycle
          </div>
          <div style={{ fontSize: 11, color: 'rgba(26,58,107,.45)', letterSpacing: '.14em', fontFamily: MONO }}>
            CLICK A YEAR TO INSPECT
          </div>
        </div>

        {/* Big readout — current year + budget */}
        <div style={{ marginTop: 16, marginBottom: 18 }}>
          <div style={{ fontSize: 11, color: '#6a7a8a', fontFamily: MONO, letterSpacing: '.16em', textTransform: 'uppercase', fontWeight: 700 }}>
            Year {active + 1} of {numPeriods}
          </div>
          <div style={{ fontSize: 44, fontWeight: 900, color: '#0a1628', fontFamily: MONO, letterSpacing: '-1px', lineHeight: 1.05, marginTop: 2 }}>
            {fmtCur(budget, sym, suffix)}
          </div>
          <div style={{ fontSize: 13, color: '#6a7a8a', fontFamily: SANS, marginTop: 2 }}>
            Fresh budget. Allocate across four departments. Lock the year.
          </div>
        </div>

        {/* Year bars */}
        <div style={{ flex: 1, display: 'flex', gap: 14, alignItems: 'stretch', minHeight: 0 }}>
          {SAMPLE_MIX.slice(0, numPeriods).map((mix, yi) => {
            const isActive = active === yi
            const isPast = yi < active
            return (
              <button
                key={yi}
                onClick={() => setActive(yi)}
                style={{
                  flex: 1,
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'stretch',
                  padding: 0,
                  outline: 'none',
                  position: 'relative',
                }}
              >
                {/* Year label */}
                <div style={{
                  fontSize: 12, fontFamily: MONO, fontWeight: 700,
                  color: isActive ? '#b8932a' : '#6a7a8a',
                  letterSpacing: '.14em', textTransform: 'uppercase',
                  marginBottom: 6, textAlign: 'center',
                  transition: 'color .25s',
                }}>
                  Year {yi + 1}
                </div>

                {/* Stacked bar */}
                <div style={{
                  flex: 1,
                  position: 'relative',
                  borderRadius: 4,
                  overflow: 'hidden',
                  border: `1.5px solid ${isActive ? '#b8932a' : 'rgba(26,58,107,.18)'}`,
                  boxShadow: isActive ? '0 6px 22px rgba(184,147,42,.18)' : 'none',
                  opacity: isPast ? 0.55 : 1,
                  transition: 'border-color .25s, box-shadow .25s, opacity .25s',
                  display: 'flex',
                  flexDirection: 'column',
                  minHeight: 80,
                }}>
                  {DEPTS.map((d, di) => (
                    <div key={d.name} style={{
                      flex: mix[di],
                      background: d.color,
                      opacity: isActive ? 1 : 0.78,
                      transition: 'opacity .25s',
                    }} />
                  ))}
                  {/* Lock overlay for past years */}
                  {isPast && (
                    <div style={{
                      position: 'absolute', inset: 0,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      background: 'rgba(240,244,250,.55)',
                    }}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                        <rect x="5" y="11" width="14" height="11" rx="2" stroke="#0a1628" strokeWidth="1.6" fill="rgba(240,244,250,.9)"/>
                        <path d="M8 11V7a4 4 0 018 0v4" stroke="#0a1628" strokeWidth="1.6" strokeLinecap="round"/>
                      </svg>
                    </div>
                  )}
                </div>

                <div style={{
                  marginTop: 8, textAlign: 'center',
                  fontFamily: MONO, fontSize: 13, fontWeight: 700,
                  color: isActive ? '#0a1628' : '#6a7a8a',
                  letterSpacing: '.02em',
                  transition: 'color .25s',
                }}>
                  {fmtCur(budget, sym, suffix)}
                  {yi > 0 && (
                    <span style={{
                      display: 'block',
                      fontSize: 11,
                      color: isActive ? '#b8932a' : 'rgba(184,147,42,.55)',
                      fontWeight: 700,
                      marginTop: 2,
                      transition: 'color .25s',
                    }}>
                      + 3% of Y{yi} profit
                    </span>
                  )}
                </div>
              </button>
            )
          })}
        </div>

        {/* Department legend */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 18, marginTop: 18, flexWrap: 'wrap' }}>
          {DEPTS.map(d => (
            <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 12, height: 12, borderRadius: 2, background: d.color, display: 'inline-block' }}/>
              <span style={{ fontSize: 13, color: '#3a4a5a', fontFamily: SANS, fontWeight: 500 }}>{d.name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// PORTRAIT slides ── graphic left, content RIGHT

function MechanicsPortrait() {
  const items = [
    { icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="#1a3a6b" strokeWidth="1.6"/><path d="M12 7v5l3 3" stroke="#1a3a6b" strokeWidth="1.6" strokeLinecap="round"/></svg>
      ), label: 'TIMED', text: 'Each year has a fixed decision window' },
    { icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><rect x="5" y="11" width="14" height="11" rx="2" stroke="#1a3a6b" strokeWidth="1.6"/><path d="M8 11V7a4 4 0 018 0v4" stroke="#1a3a6b" strokeWidth="1.6" strokeLinecap="round"/></svg>
      ), label: 'IRREVERSIBLE', text: 'Sealed years cannot be revisited' },
    { icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3" stroke="#1a3a6b" strokeWidth="1.6"/><path d="M12 3v3M12 18v3M3 12h3M18 12h3" stroke="#1a3a6b" strokeWidth="1.6" strokeLinecap="round"/></svg>
      ), label: 'LIVE MULTIPLAYER', text: 'All teams advance simultaneously' },
    { icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2" stroke="#1a3a6b" strokeWidth="1.6" strokeLinecap="round"/><circle cx="9" cy="7" r="4" stroke="#1a3a6b" strokeWidth="1.6"/></svg>
      ), label: 'ONE CONTROLLER', text: 'One seat drives decisions per team' },
    { icon: (
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><line x1="12" y1="1" x2="12" y2="23" stroke="#1a3a6b" strokeWidth="1.6" strokeLinecap="round"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" stroke="#1a3a6b" strokeWidth="1.6" strokeLinecap="round"/></svg>
      ), label: 'THOUSANDS', text: '$60,000K = $60 million throughout' },
  ]
  return (
    <div style={{ width:'100%', height:'100%', background:'#f0f4fa', position:'relative', overflow:'hidden', display:'flex', alignItems:'center', justifyContent:'center', padding:'40px 36px' }}>
      <svg style={{ position:'absolute', inset:0, width:'100%', height:'100%', pointerEvents:'none' }}>
        <defs>
          <pattern id="mp-sm" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0L0 0 0 28" fill="none" stroke="rgba(26,58,107,.07)" strokeWidth=".5"/></pattern>
          <pattern id="mp-lg" width="140" height="140" patternUnits="userSpaceOnUse"><path d="M140 0L0 0 0 140" fill="none" stroke="rgba(26,58,107,.12)" strokeWidth="1"/></pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#mp-sm)"/>
        <rect width="100%" height="100%" fill="url(#mp-lg)"/>
      </svg>
      <div style={{ position:'relative', zIndex:1, width:'100%' }}>
        <div style={{ fontSize:9, color:'#b8932a', letterSpacing:'.22em', fontFamily:"'DM Mono',monospace", textTransform:'uppercase', fontWeight:700, marginBottom:20 }}>Quick Reference</div>
        <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
          {items.map(({ icon, label, text }) => (
            <div key={label} style={{ display:'flex', alignItems:'center', gap:18, background:'rgba(255,255,255,.90)', border:'1px solid rgba(26,58,107,.10)', borderLeft:'3px solid #b8932a', borderRadius:4, padding:'14px 18px' }}>
              <div style={{ flexShrink:0 }}>{icon}</div>
              <div>
                <div style={{ fontSize:10, fontWeight:800, color:'#b8932a', letterSpacing:'.16em', fontFamily:"'DM Mono',monospace", marginBottom:4 }}>{label}</div>
                <div style={{ fontSize:13, color:'#3a4a5a', lineHeight:1.45 }}>{text}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}


function PortraitSlide({ slide, displayed, done, step, total, onNext, onBack, onSkip, isLast, auth, onReady, competitors }) {
  const type = slide?.type || 'default'
  return (
    <div className="sb-portrait-slide" style={{ flex: 1, display: 'flex', overflow: 'hidden', background: '#f4f6fa' }}>
      {/* Left graphic zone — full height */}
      <div className="sb-portrait-graphic" style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        {type === 'competitors' ? <CompetitorPortrait competitors={competitors} />
          : type === 'objective' ? <ObjectivePortrait />
          : type === 'mechanics' ? <MechanicsPortrait />
          : <ReadyPortrait />}
      </div>
      {/* RIGHT text panel */}
      <div className="sb-portrait-panel" style={{ width: 460, flexShrink: 0, background: 'rgba(255,255,255,.95)', borderLeft: '1px solid rgba(26,58,107,.12)', display: 'flex', flexDirection: 'column', backdropFilter: 'blur(4px)', position: 'relative', zIndex: 2, boxShadow: '-2px 0 20px rgba(10,22,40,.06)' }}>
        <div style={{ padding: '16px 24px 0', flexShrink: 0 }}>
          <div style={{ fontSize: 9, color: '#b8932a', letterSpacing: '.20em', fontFamily: MONO, textTransform: 'uppercase', marginBottom: 6 }}>
            Transmission {String(step + 1).padStart(2, '0')} · {type}
          </div>
          <h2 style={{ fontSize: 20, fontWeight: 900, color: '#0a1628', lineHeight: 1.2, margin: 0 }}>{slide?.title}</h2>
          <div style={{ height: 2, width: 32, background: '#1a3a6b', borderRadius: 1, marginTop: 8 }} />
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px 24px' }}>
          <RichText text={displayed} style={{ fontSize: 15, color: '#3a4a5a', lineHeight: 1.60, textAlign: 'justify' }} />
          {!done && <span style={{ display: 'inline-block', width: 7, height: 13, background: '#1a3a6b', verticalAlign: 'text-bottom', marginLeft: 2, animation: 'blink .7s step-end infinite' }} />}
          {isLast && done && <FinalCTA auth={auth} onReady={onReady} />}
        </div>
        <SlideNav step={step} total={total} onNext={onNext} onBack={onBack} onSkip={onSkip} isLast={isLast} accent="#1a3a6b" />
      </div>
    </div>
  )
}

// Voltex's brand color used in the head-to-head ladder bars.
const COMPETITOR_VOLTEX_COLOR = '#1A3A6B'

// Single metric "ladder" — labelled bars for Voltex (top) and rival (bottom), plus a delta callout
// that says who's ahead and by how much.
function CompetitorLadder({ label, suffix, voltexVal, rivalVal, rivalColor, voltexLabel, rivalLabel, max, animKey }) {
  const vPct = Math.max(4, Math.min(100, (voltexVal / max) * 100))
  const rPct = Math.max(4, Math.min(100, (rivalVal  / max) * 100))
  const delta = rivalVal - voltexVal
  const ahead = delta > 0 ? 'rival' : delta < 0 ? 'voltex' : 'tied'
  const deltaText = ahead === 'tied'
    ? '◇ MATCHED'
    : ahead === 'rival'
      ? `▼ BEHIND BY ${Math.abs(delta)}${suffix}`
      : `▲ AHEAD BY ${Math.abs(delta)}${suffix}`
  const deltaColor = ahead === 'tied'
    ? '#b8932a'
    : ahead === 'rival' ? rivalColor : '#1F8050'
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {/* Metric header row */}
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 8 }}>
        <div style={{ fontSize: 10, fontWeight: 700, color: '#b8932a', letterSpacing: '.18em', fontFamily: MONO }}>{label}</div>
        <div style={{ fontSize: 10, fontWeight: 700, color: deltaColor, letterSpacing: '.10em', fontFamily: MONO, transition: 'color .25s' }}>{deltaText}</div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '76px 1fr 76px', gap: 10, alignItems: 'center' }}>
        {/* Voltex value */}
        <div style={{ fontSize: 14, fontWeight: 800, color: COMPETITOR_VOLTEX_COLOR, fontFamily: MONO, textAlign: 'right' }}>{voltexLabel}</div>
        <div style={{ position: 'relative', height: 22 }}>
          {/* Track */}
          <div style={{ position: 'absolute', top: 9, left: 0, right: 0, height: 4, background: 'rgba(26,58,107,.10)', borderRadius: 2 }}/>
          <div
            key={`v-${animKey}`}
            style={{
              position: 'absolute', top: 7, left: 0, height: 8,
              width: vPct + '%',
              background: `linear-gradient(90deg, ${COMPETITOR_VOLTEX_COLOR}55, ${COMPETITOR_VOLTEX_COLOR})`,
              borderRadius: 2,
              animation: 'growWidth .65s cubic-bezier(.4,0,.2,1) both',
              transformOrigin: 'left',
            }}
          />
          {/* Voltex marker */}
          <div style={{ position: 'absolute', top: 4, left: `calc(${vPct}% - 6px)`, width: 12, height: 12, background: COMPETITOR_VOLTEX_COLOR, borderRadius: '50%', border: '2px solid white', boxShadow: '0 0 0 1px rgba(26,58,107,.20)', transition: 'left .65s cubic-bezier(.4,0,.2,1)' }}/>
        </div>
        <div style={{ fontSize: 9, fontWeight: 700, color: 'rgba(26,58,107,.55)', letterSpacing: '.16em', fontFamily: MONO }}>VOLTEX</div>

        {/* Rival row */}
        <div style={{ fontSize: 14, fontWeight: 800, color: rivalColor, fontFamily: MONO, textAlign: 'right', transition: 'color .25s' }}>{rivalLabel}</div>
        <div style={{ position: 'relative', height: 22 }}>
          <div style={{ position: 'absolute', top: 9, left: 0, right: 0, height: 4, background: 'rgba(26,58,107,.10)', borderRadius: 2 }}/>
          <div
            key={`r-${animKey}`}
            style={{
              position: 'absolute', top: 7, left: 0, height: 8,
              width: rPct + '%',
              background: `linear-gradient(90deg, ${rivalColor}55, ${rivalColor})`,
              borderRadius: 2,
              animation: 'growWidth .65s cubic-bezier(.4,0,.2,1) both .08s',
              transformOrigin: 'left',
            }}
          />
          <div style={{ position: 'absolute', top: 4, left: `calc(${rPct}% - 6px)`, width: 12, height: 12, background: rivalColor, borderRadius: '50%', border: '2px solid white', boxShadow: '0 0 0 1px rgba(26,58,107,.20)', transition: 'left .65s cubic-bezier(.4,0,.2,1), background .25s' }}/>
        </div>
        <div style={{ fontSize: 9, fontWeight: 700, color: rivalColor, letterSpacing: '.16em', fontFamily: MONO, transition: 'color .25s' }}>RIVAL</div>
      </div>
    </div>
  )
}

function CompetitorPortrait({ competitors }) {
  const [active, setActive] = React.useState(0)
  // animKey is bumped each time the user picks a different rival, so the metric bars (which use it as a
  // key) re-mount and replay their grow-in animation.
  const [animKey, setAnimKey] = React.useState(0)
  const selectRival = i => {
    if (i === active) return
    setActive(i)
    setAnimKey(k => k + 1)
  }

  // Each competitor gets a distinct color and a unique sigil shape.
  // Tuned for white surfaces — saturated enough to read, not so loud they shout.
  const COLORS  = ['#C0392B', '#C27D3A', '#533AB7', '#0F6E56']
  const THREATS = ['1', '2', '3', '4']
  // Sigil glyphs: small, distinct SVG marks rendered per-rival
  const SIGILS = [
    // α — splintered shard (Solara-like, sharp & disruptive)
    (sz, c) => (
      <svg viewBox="0 0 32 32" width={sz} height={sz} style={{ overflow: 'visible' }}>
        <path d="M16 2 L28 12 L22 30 L10 30 L4 12 Z" fill="none" stroke={c} strokeWidth="1.6"/>
        <path d="M16 2 L16 30 M4 12 L28 12" stroke={c} strokeWidth="1" opacity=".55"/>
        <circle cx="16" cy="12" r="2.2" fill={c}/>
      </svg>
    ),
    // β — interlocked rings (Halo)
    (sz, c) => (
      <svg viewBox="0 0 32 32" width={sz} height={sz} style={{ overflow: 'visible' }}>
        <circle cx="13" cy="16" r="9" fill="none" stroke={c} strokeWidth="1.6"/>
        <circle cx="19" cy="16" r="9" fill="none" stroke={c} strokeWidth="1.6"/>
        <circle cx="16" cy="16" r="1.6" fill={c}/>
      </svg>
    ),
    // γ — concentric arrowheads (BrightDrive — fast & forward)
    (sz, c) => (
      <svg viewBox="0 0 32 32" width={sz} height={sz} style={{ overflow: 'visible' }}>
        <path d="M6 22 L16 8 L26 22" fill="none" stroke={c} strokeWidth="1.6"/>
        <path d="M9 26 L16 14 L23 26" fill="none" stroke={c} strokeWidth="1.4" opacity=".70"/>
        <path d="M12 30 L16 22 L20 30" fill="none" stroke={c} strokeWidth="1.2" opacity=".40"/>
      </svg>
    ),
    // δ — gear-fortress (Apex Legacy)
    (sz, c) => (
      <svg viewBox="0 0 32 32" width={sz} height={sz} style={{ overflow: 'visible' }}>
        <rect x="4" y="4" width="24" height="24" fill="none" stroke={c} strokeWidth="1.6"/>
        <rect x="10" y="10" width="12" height="12" fill="none" stroke={c} strokeWidth="1.2" opacity=".70"/>
        <line x1="4" y1="4" x2="10" y2="10" stroke={c} strokeWidth="1"/>
        <line x1="28" y1="4" x2="22" y2="10" stroke={c} strokeWidth="1"/>
        <line x1="4" y1="28" x2="10" y2="22" stroke={c} strokeWidth="1"/>
        <line x1="28" y1="28" x2="22" y2="22" stroke={c} strokeWidth="1"/>
        <circle cx="16" cy="16" r="1.6" fill={c}/>
      </svg>
    ),
  ]
  // Voltex's own sigil — six-point navy mark, used in the center header
  const VoltexSigil = ({ size = 30 }) => (
    <svg viewBox="0 0 32 32" width={size} height={size} style={{ overflow: 'visible' }}>
      <path d="M16 2 L24 9 L24 23 L16 30 L8 23 L8 9 Z" fill="none" stroke="#1A3A6B" strokeWidth="1.6"/>
      <path d="M16 8 L19 14 L16 16 L13 14 Z" fill="#1A3A6B"/>
      <path d="M16 16 L19 22 L13 22 Z" fill="none" stroke="#1A3A6B" strokeWidth="1.2"/>
    </svg>
  )

  const FALLBACK = [
    { name: 'Solara Automotive',       display_label: 'Silicon Valley EV Disruptor',  description: 'Software-first EV company with strong brand among tech adopters, challenged on manufacturing scale.', location: 'Palo Alto, USA',  founded: '2014', base_revenue: [280000000], budget: 60000000, spending_tendency: 'R&D and Marketing heavy: Bets on software innovation and brand' },
    { name: 'Halo Electric',            display_label: 'Premium European EV Brand',    description: 'Premium European EV brand with heritage of engineering excellence, expanding into mass-market coupe.', location: 'Munich, Germany', founded: '2010', base_revenue: [450000000], budget: 65000000, spending_tendency: 'Performance-obsessed: Pours R&D into powertrain and acceleration' },
    { name: 'BrightDrive Motors',       display_label: 'Low-Cost Chinese EV Challenger', description: 'Aggressive Chinese manufacturer with ultra-low-cost battery technology and rapid global expansion.', location: 'Shenzhen, China', founded: '2017', base_revenue: [350000000], budget: 40000000, spending_tendency: 'Cost-focused with heavy Operations spend: Competing on price' },
    { name: 'Apex Legacy Auto',         display_label: 'Legacy OEM in Transition',     description: 'Legacy automaker with large dealer network undergoing forced EV transition. Slow on software culture.', location: 'Detroit, USA',  founded: '1962', base_revenue: [320000000], budget: 90000000, spending_tendency: 'Heavy Operations and Sales investor with fleet-focused distribution' },
  ]

  const raw   = competitors?.length > 0 ? competitors.slice(0, 4) : FALLBACK
  const comps = raw.map((c, i) => {
    const revRaw = Array.isArray(c.base_revenue) && c.base_revenue[0] ? c.base_revenue[0] : (c.revenue || 300) * 1e6
    const rev    = Math.round(revRaw / 1e6)
    const bud    = c.budget ? Math.round(c.budget / 1e6) : Math.round(rev * 0.18)
    const yr     = 2025 - parseInt(c.founded || '2015')
    return { ...c, color: COLORS[i], threat: THREATS[i], sigil: SIGILS[i], rev, bud, yr }
  })

  const comp   = comps[active] || comps[0]
  const voltex = { rev: 40, bud: 60, yr: 3 }
  const maxRev = Math.max(...comps.map(c => c.rev), voltex.rev)
  const maxBud = Math.max(...comps.map(c => c.bud), voltex.bud)
  const maxYr  = Math.max(...comps.map(c => c.yr), 15)

  const Sigil = comp.sigil

  return (
    <div style={{
      position: 'absolute', inset: 0,
      background: '#f4f6fa',
      display: 'flex', flexDirection: 'column', overflow: 'hidden', fontFamily: MONO,
      color: '#0a1628',
    }}>
      {/* Top status strip */}
      <div style={{
        padding: '10px 18px',
        background: 'white',
        borderBottom: '1px solid rgba(26,58,107,.10)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#1F8050', boxShadow: '0 0 6px rgba(31,128,80,.55)', animation: 'cpPulse 1.6s ease-in-out infinite' }}/>
          <div style={{ fontSize: 9, color: '#b8932a', letterSpacing: '.24em', fontWeight: 700 }}>TACTICAL BRIEF</div>
          <div style={{ width: 1, height: 12, background: 'rgba(26,58,107,.18)' }}/>
          <div style={{ fontSize: 9, color: 'rgba(26,58,107,.55)', letterSpacing: '.18em' }}>COMPETITIVE LANDSCAPE</div>
        </div>
        <div style={{ fontSize: 9, color: 'rgba(26,58,107,.45)', letterSpacing: '.18em' }}>
          SELECT COMPETITOR · {String(active + 1).padStart(2, '0')} / {String(comps.length).padStart(2, '0')}
        </div>
      </div>

      {/* Body: dossier list (left) + duel panel (right) */}
      <div style={{ flex: 1, display: 'flex', minHeight: 0 }}>

        {/* DOSSIER LIST */}
        <div style={{
          width: 220, flexShrink: 0,
          background: 'white',
          borderRight: '1px solid rgba(26,58,107,.10)',
          display: 'flex', flexDirection: 'column',
        }}>
          {comps.map((c, i) => {
            const isActive = i === active
            const Glyph = c.sigil
            return (
              <div key={i}
                onClick={() => selectRival(i)}
                style={{
                  flex: 1, padding: '10px 14px 10px 16px',
                  cursor: 'pointer', position: 'relative',
                  display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 4,
                  borderBottom: '1px solid rgba(26,58,107,.06)',
                  transition: 'background .25s',
                  background: isActive ? `linear-gradient(90deg, ${c.color}10 0%, transparent 80%)` : 'transparent',
                  animation: `fadeUp .45s ease both ${i * .08}s`, opacity: 0,
                }}
              >
                {/* Active accent rail */}
                <div style={{
                  position: 'absolute', left: 0, top: 6, bottom: 6,
                  width: 3, background: isActive ? c.color : 'transparent',
                  transition: 'all .25s',
                }}/>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <div style={{
                    width: 30, height: 30, flexShrink: 0,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    border: `1px solid ${isActive ? c.color : 'rgba(26,58,107,.15)'}`,
                    background: isActive ? c.color + '0d' : 'rgba(26,58,107,.02)',
                    transition: 'all .25s',
                  }}>{Glyph(20, isActive ? c.color : 'rgba(26,58,107,.45)')}</div>
                  <div style={{ minWidth: 0, flex: 1 }}>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
                      <span style={{ fontSize: 9, fontWeight: 700, color: isActive ? c.color : 'rgba(26,58,107,.40)', letterSpacing: '.16em', transition: 'color .25s' }}>COMPETITOR</span>
                      <span style={{ fontSize: 14, fontWeight: 900, color: isActive ? c.color : 'rgba(26,58,107,.55)', fontFamily: MONO, transition: 'color .25s' }}>{c.threat}</span>
                    </div>
                    <div style={{ fontSize: 12, fontWeight: 700, color: isActive ? '#0a1628' : '#3a4a5a', lineHeight: 1.2, marginTop: 2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', fontFamily: SANS }}>{c.name}</div>
                  </div>
                </div>
                {/* Mini telemetry: revenue spark + location */}
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 2, paddingLeft: 40 }}>
                  <div style={{ display: 'flex', gap: 2, alignItems: 'flex-end' }}>
                    {[0,1,2,3,4].map(k => (
                      <div key={k} style={{
                        width: 5, height: (k + 1) * 2 + 2,
                        background: k < Math.round((c.rev / maxRev) * 5) ? (isActive ? c.color : 'rgba(26,58,107,.30)') : 'rgba(26,58,107,.08)',
                        transition: 'background .25s',
                      }}/>
                    ))}
                  </div>
                  <div style={{ fontSize: 9, color: 'rgba(26,58,107,.50)', letterSpacing: '.06em', fontFamily: MONO, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    ${c.rev}M · {c.location?.split(',')[0] || '—'}
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {/* DUEL PANEL */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, padding: '14px 20px 0' }}>

          {/* Versus header */}
          <div key={`hdr-${animKey}`} style={{
            display: 'grid', gridTemplateColumns: '1fr auto 1fr', alignItems: 'center', gap: 16,
            padding: '14px 18px',
            background: 'white',
            border: '1px solid rgba(26,58,107,.10)',
            borderRadius: 4,
            position: 'relative',
            animation: 'fadeUp .35s ease both',
          }}>
            {/* Voltex side */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ width: 42, height: 42, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(26,58,107,.18)', background: 'rgba(26,58,107,.03)', flexShrink: 0 }}>
                <VoltexSigil size={28}/>
              </div>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 9, color: '#b8932a', letterSpacing: '.20em', fontWeight: 700 }}>YOUR COMPANY</div>
                <div style={{ fontSize: 16, fontWeight: 900, color: '#0a1628', fontFamily: SANS, letterSpacing: '-.01em' }}>Voltex Motors</div>
                <div style={{ fontSize: 10, color: '#6a7a8a', marginTop: 1 }}>Austin, TX · Est. 2022</div>
              </div>
            </div>

            {/* VS marker */}
            <div style={{
              fontSize: 11, fontWeight: 900, color: '#b8932a',
              letterSpacing: '.16em', textAlign: 'center',
              padding: '6px 12px',
              border: '1px solid rgba(184,147,42,.40)',
              background: 'rgba(184,147,42,.06)',
              borderRadius: 2,
            }}>VS</div>

            {/* Rival side */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, justifyContent: 'flex-end', textAlign: 'right' }}>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 9, color: comp.color, letterSpacing: '.20em', fontWeight: 700, transition: 'color .25s' }}>{(comp.display_label || 'RIVAL').toUpperCase()}</div>
                <div style={{ fontSize: 16, fontWeight: 900, color: '#0a1628', fontFamily: SANS, letterSpacing: '-.01em' }}>{comp.name}</div>
                <div style={{ fontSize: 10, color: '#6a7a8a', marginTop: 1 }}>{comp.location} · Est. {comp.founded}</div>
              </div>
              <div style={{
                width: 42, height: 42,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                border: `1px solid ${comp.color}55`,
                background: comp.color + '0d',
                flexShrink: 0,
                transition: 'all .25s',
              }}>{Sigil(28, comp.color)}</div>
            </div>
          </div>

          {/* Metric ladders — fills available space */}
          <div style={{
            flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-evenly',
            padding: '18px 4px',
          }}>
            <CompetitorLadder label="BASE REVENUE" suffix="M" voltexVal={voltex.rev} rivalVal={comp.rev}
              rivalColor={comp.color} voltexLabel={'$' + voltex.rev + 'M'} rivalLabel={'$' + comp.rev + 'M'} max={maxRev} animKey={animKey}/>
            <CompetitorLadder label="ANNUAL BUDGET" suffix="M" voltexVal={voltex.bud} rivalVal={comp.bud}
              rivalColor={comp.color} voltexLabel={'$' + voltex.bud + 'M'} rivalLabel={'$' + comp.bud + 'M'} max={maxBud} animKey={animKey}/>
            <CompetitorLadder label="YEARS IN MARKET" suffix=" YRS" voltexVal={voltex.yr} rivalVal={comp.yr > 50 ? 50 : comp.yr}
              rivalColor={comp.color} voltexLabel={voltex.yr + ' yrs'} rivalLabel={(comp.yr > 50 ? '50+' : comp.yr) + ' yrs'} max={maxYr} animKey={animKey}/>
          </div>

          {/* Intelligence briefing */}
          <div key={`int-${animKey}`} style={{
            borderTop: '1px solid rgba(26,58,107,.10)',
            padding: '14px 4px 16px',
            position: 'relative',
            animation: 'fadeUp .35s ease both .05s',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <div style={{ width: 4, height: 4, background: comp.color, transition: 'background .25s' }}/>
              <div style={{ fontSize: 9, color: comp.color, fontWeight: 700, letterSpacing: '.20em', transition: 'color .25s' }}>INTELLIGENCE</div>
              <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg, ${comp.color}55, transparent)`, transition: 'background .25s' }}/>
            </div>
            <div style={{ fontSize: 15, color: '#3a4a5a', lineHeight: 1.60, fontFamily: SANS, textAlign: 'justify', marginBottom: 8 }}>{comp.description}</div>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
              <div style={{ fontSize: 10, color: comp.color, fontWeight: 700, letterSpacing: '.10em', flexShrink: 0, marginTop: 1, transition: 'color .25s' }}>DOCTRINE ▸</div>
              <div style={{ fontSize: 11, color: '#6a7a8a', lineHeight: 1.4, fontStyle: 'italic' }}>{comp.spending_tendency}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}


function ObjectivePortrait() {
  const canvasRef = useRef(null)
  const stateRef  = useRef({ needleFrac: 0.8, targetFrac: 0.8 })
  const rafRef    = useRef(null)
  const geomRef   = useRef({ W: 0, H: 0, x: 0, y: 0, r: 0, tw: 0 })
  const [activeZone, setActiveZone] = React.useState(4)

  const ZONES = [
    { label: 'F', range: '0-249',   color: '#C0392B', desc: 'Critical failure. Heavy losses, negligible market presence. The business is in freefall.' },
    { label: 'D', range: '250-399', color: '#E07B39', desc: 'Below threshold. Survival mode — revenue exists but growth is stalled and the brand barely registers.' },
    { label: 'C', range: '400-549', color: '#D4AC0D', desc: 'Acceptable. Profitable and present, but not punching its weight. Room for meaningful improvement.' },
    { label: 'B', range: '550-699', color: '#27AE60', desc: 'Good execution. A credible market force with healthy financials and consistent performance.' },
    { label: 'A', range: '700-849', color: '#1A3A6B', desc: 'Excellent. Strong profitability and real market share. The benchmark most teams should aim for.' },
    { label: 'S', range: '850+',    color: '#b8932a', desc: 'Exceptional. Elite-tier execution — sustained profitability and dominant market presence.' },
  ]
  // Each tuple is [startAngle, endAngle] in MATH convention (sin>0 = up, used by the label/needle code
  // below).
  const BOUNDS = [[Math.PI*1.0000,Math.PI*0.7500],[Math.PI*0.7500,Math.PI*0.6000],[Math.PI*0.6000,Math.PI*0.4500],[Math.PI*0.4500,Math.PI*0.3000],[Math.PI*0.3000,Math.PI*0.1500],[Math.PI*0.1500,Math.PI*0.0000]]
  // Canvas-convention version: each zone occupies its own 36° slice along the
  // top semicircle when drawn with anticlockwise=false (angle increasing).
  const arcAngle = a => (Math.PI * 2 - a) % (Math.PI * 2)

  // Fractional thresholds aligned with the new ZONES (0-1000 score → 0-1 frac).
  function getZone(f) { if(f<.25)return 0; if(f<.40)return 1; if(f<.55)return 2; if(f<.70)return 3; if(f<.85)return 4; return 5 }

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    let destroyed = false
    const dpr = window.devicePixelRatio || 1
    const st  = stateRef.current
    let W = 0, H = 0

    function resize() {
      const p = canvas.parentElement
      W = p.offsetWidth; H = p.offsetHeight
      canvas.width  = W * dpr; canvas.height = H * dpr
      canvas.style.width = W + 'px'; canvas.style.height = H + 'px'
    }

    function draw() {
      if (destroyed) return
      const ctx = canvas.getContext('2d')
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

      // Reserve room for outer labels (boundary numbers sit ~16px out plus their own glyph height) and for a
      // comfortable gap below the pivot so the hub sits clear of the bottom edge.
      const OUTER_LABEL_OFFSET = 16   // distance from outer ring to label centres
      const OUTER_LABEL_HEIGHT = 14   // half-height of the labels (vertical slack)
      const BOTTOM_RESERVE     = 24   // space below pivot for the hub
      const SIDE_PAD           = 36   // horizontal slack so '0' / '1k+' don't clip

      const x  = W / 2
      const y  = Math.max(60, H - BOTTOM_RESERVE)

      // Width-based cap: outer labels at ±r horizontally also need to fit.
      const widthCap  = Math.max(40, (W - SIDE_PAD * 2) * 0.5)
      // Height-based cap: r + ringHalf + labelOffset + labelHeight ≤ y We solve for r, allowing tw ≈ r *
      // 0.12 (capped 16..28) → use a safe upper bound for tw of 28 in this calc, then refine after.
      const heightCap = Math.max(40, y - 28 * 0.5 - OUTER_LABEL_OFFSET - OUTER_LABEL_HEIGHT)
      const r  = Math.min(widthCap, heightCap)
      const tw = Math.max(16, Math.min(28, r * 0.12))

      // Stash geometry for the mouse handler so it always uses the live values.
      geomRef.current = { W, H, x, y, r, tw }

      ctx.clearRect(0, 0, W, H)
      ctx.fillStyle = '#f4f6fa'; ctx.fillRect(0, 0, W, H)

      // 1. Track background — full top semicircle
      ctx.save()
      ctx.beginPath(); ctx.arc(x, y, r, Math.PI, 0, false)
      ctx.lineWidth = tw; ctx.strokeStyle = '#dde4ee'
      ctx.lineCap = 'butt'; ctx.stroke()
      ctx.restore()

      // 2.
      BOUNDS.forEach(([s, e], i) => {
        const cs = arcAngle(s), ce = arcAngle(e) || (Math.PI * 2)
        ctx.save()
        ctx.beginPath(); ctx.arc(x, y, r, cs, ce, false)
        ctx.lineWidth = tw
        ctx.strokeStyle = ZONES[i].color
        ctx.lineCap = 'butt'
        ctx.stroke()
        ctx.restore()
      })

      // 3. Active zone brighter highlight on top
      const az = getZone(st.needleFrac)
      const acs = arcAngle(BOUNDS[az][0]), ace = arcAngle(BOUNDS[az][1]) || (Math.PI * 2)
      ctx.save()
      ctx.beginPath(); ctx.arc(x, y, r, acs, ace, false)
      ctx.lineWidth = tw + 6
      ctx.strokeStyle = ZONES[az].color + '40'
      ctx.lineCap = 'butt'; ctx.stroke()
      ctx.beginPath(); ctx.arc(x, y, r, acs, ace, false)
      ctx.lineWidth = tw
      ctx.strokeStyle = ZONES[az].color
      ctx.lineCap = 'butt'; ctx.stroke()
      ctx.restore()

      // 4. Tick separator lines between zones — coloured to match zone boundary
      ctx.save()
      // Boundaries between zones: at fractions where one zone ends and next begins
      // Pair each boundary with the lighter of its two neighbours
      const BDRY = [
        { f: 0,     color: '#C0392B' },
        { f: 0.25,  color: '#E07B39' },
        { f: 0.40,  color: '#D4AC0D' },
        { f: 0.55,  color: '#27AE60' },
        { f: 0.70,  color: '#1A3A6B' },
        { f: 0.85,  color: '#b8932a' },
        { f: 1,     color: '#b8932a' },
      ]
      // Skip the 0 and 1 boundary (start/end of arc) — only draw interior separators
      BDRY.slice(1, -1).forEach(({ f, color }) => {
        const a = Math.PI * (1 - f)
        // Draw a bright white gap line, then a thin coloured line on top
        ctx.beginPath()
        ctx.moveTo(x + (r - tw*0.5 - 1) * Math.cos(a), y - (r - tw*0.5 - 1) * Math.sin(a))
        ctx.lineTo(x + (r + tw*0.5 + 1) * Math.cos(a), y - (r + tw*0.5 + 1) * Math.sin(a))
        ctx.strokeStyle = '#f4f6fa'; ctx.lineWidth = 4; ctx.stroke()
        ctx.strokeStyle = color + 'aa'; ctx.lineWidth = 1.5; ctx.stroke()
      })
      ctx.restore()

      // 5. Score boundary numbers — at real zone thresholds
      const LBLS = [
        { f: 0,     text: '0'   },
        { f: 0.25,  text: '250' },
        { f: 0.40,  text: '400' },
        { f: 0.55,  text: '550' },
        { f: 0.70,  text: '700' },
        { f: 0.85,  text: '850' },
        { f: 1,     text: '1k+' },
      ]
      LBLS.forEach(({ f, text }) => {
        const a  = Math.PI * (1 - f)
        const lr = r + tw * 0.5 + 18
        ctx.save()
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
        ctx.fillStyle = 'rgba(26,58,107,.50)'
        ctx.font = '600 10px DM Mono,monospace'
        ctx.fillText(text, x + lr * Math.cos(a), y - lr * Math.sin(a))
        ctx.restore()
      })

      // 6. Needle
      const na  = Math.PI * (1 - st.needleFrac)
      const ntx = x + (r - tw * 0.5 - 12) * Math.cos(na)
      const nty = y - (r - tw * 0.5 - 12) * Math.sin(na)
      ctx.save()
      ctx.shadowColor = 'rgba(10,22,40,.20)'; ctx.shadowBlur = 8; ctx.shadowOffsetY = 2
      ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(ntx, nty)
      ctx.strokeStyle = '#0a1628'; ctx.lineWidth = 4; ctx.lineCap = 'round'; ctx.stroke()
      ctx.restore()

      // 7. Hub
      ctx.save()
      ctx.beginPath(); ctx.arc(x, y, 16, 0, Math.PI*2); ctx.fillStyle = '#0a1628'; ctx.fill()
      ctx.beginPath(); ctx.arc(x, y,  8, 0, Math.PI*2); ctx.fillStyle = 'white';   ctx.fill()
      ctx.beginPath(); ctx.arc(x, y,  4, 0, Math.PI*2); ctx.fillStyle = ZONES[az].color; ctx.fill()
      ctx.restore()


    }

    function loop() {
      if (destroyed) return
      st.needleFrac += (st.targetFrac - st.needleFrac) * .07
      draw()
      setActiveZone(getZone(st.needleFrac))
      rafRef.current = requestAnimationFrame(loop)
    }

    const onMove = e => {
      const rect = canvas.getBoundingClientRect()
      const g = geomRef.current
      // Mouse position relative to the gauge pivot. In screen coords y grows
      // downward, so we flip to math coords where dy>0 means "above the pivot".
      const dx = e.clientX - rect.left - g.x
      const dy = g.y - (e.clientY - rect.top)
      // Only steer when the cursor is above the pivot (the gauge lives there).
      if (dy < -4) return
      const a = Math.atan2(Math.max(dy, 0.001), dx)
      st.targetFrac = Math.max(.01, Math.min(.99, 1 - a / Math.PI))
    }

    resize()
    window.addEventListener('resize', resize)
    canvas.addEventListener('mousemove', onMove)
    loop()

    return () => {
      destroyed = true
      cancelAnimationFrame(rafRef.current)
      window.removeEventListener('resize', resize)
      canvas.removeEventListener('mousemove', onMove)
    }
  }, [])

  const zone   = ZONES[activeZone]
  // Midpoints of each band — used when the user clicks a band chip to snap the
  // needle into that band. Must mirror the getZone() thresholds above.
  const jumpTo = i => { stateRef.current.targetFrac = [.125, .325, .475, .625, .775, .925][i] }

  return (
    <div style={{ position: 'absolute', inset: 0, background: '#f4f6fa', display: 'flex', flexDirection: 'column', overflow: 'hidden', fontFamily: MONO }}>

      {/* Top — gauge fills space */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '18px 16px 6px', position: 'relative', minHeight: 0 }}>
        <div style={{ fontSize: 8, color: 'rgba(184,147,42,.75)', letterSpacing: '.20em', alignSelf: 'flex-start', marginBottom: 8 }}>
          VALUE PERFORMANCE INDEX
        </div>
        <div style={{ textAlign: 'center', marginBottom: 4 }}>
          <div style={{ fontSize: 48, fontWeight: 700, lineHeight: 1, color: zone.color, transition: 'color .25s', fontFamily: MONO }}>
            {Math.round(stateRef.current.needleFrac * 1000)}
          </div>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'rgba(26,58,107,.70)', letterSpacing: '.10em', marginTop: 10, fontFamily: SANS }}>
            ↔ Hover gauge to explore
          </div>
        </div>
        <div style={{ width: '88%', maxWidth: 380, marginTop: 4, marginBottom: 4 }}>
          <div style={{ display: 'flex', borderRadius: 3, overflow: 'hidden', border: '1px solid rgba(26,58,107,.12)' }}>
            <div style={{
              flex: 1, padding: '5px 8px',
              background: 'rgba(26,58,107,.08)',
              borderRight: '1px solid rgba(26,58,107,.18)',
              display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 6,
            }}>
              <span style={{ fontSize: 9, fontFamily: MONO, fontWeight: 700, color: 'rgba(26,58,107,.65)', letterSpacing: '.12em' }}>PROFITABILITY</span>
              <span style={{ fontSize: 10, fontFamily: MONO, fontWeight: 800, color: '#0a1628' }}>50%</span>
            </div>
            <div style={{
              flex: 1, padding: '5px 8px',
              background: 'rgba(184,147,42,.10)',
              display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 6,
            }}>
              <span style={{ fontSize: 9, fontFamily: MONO, fontWeight: 700, color: 'rgba(184,147,42,.85)', letterSpacing: '.12em' }}>MARKET SHARE</span>
              <span style={{ fontSize: 10, fontFamily: MONO, fontWeight: 800, color: '#b8932a' }}>50%</span>
            </div>
          </div>
        </div>
        {/* Canvas fills remaining space */}
        <div style={{ flex: 1, width: '100%', position: 'relative', cursor: 'crosshair', minHeight: 180 }}>
          <canvas ref={canvasRef} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}/>
        </div>
      </div>

      {/* Bottom — VPI zones bar */}
      <div style={{ background: 'white', borderTop: '1px solid rgba(26,58,107,.10)', padding: '14px 18px 16px', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 10 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#b8932a', letterSpacing: '.18em' }}>VPI ZONES</div>
          <div style={{ fontSize: 12, fontWeight: 800, color: zone.color, letterSpacing: '.10em', transition: 'color .25s' }}>
            {zone.label} · {zone.range}
          </div>
        </div>

        {/* Horizontal segmented bar */}
        <div style={{ display: 'flex', gap: 5, marginBottom: 10 }}>
          {ZONES.map((z, i) => (
            <div
              key={i}
              onClick={() => jumpTo(i)}
              style={{
                flex: 1,
                cursor: 'pointer',
                padding: '10px 6px 9px',
                background: i === activeZone ? z.color : z.color + '22',
                border: `1px solid ${i === activeZone ? z.color : z.color + '55'}`,
                borderRadius: 4,
                transition: 'background .2s, border-color .2s',
                textAlign: 'center',
              }}
            >
              <div style={{
                fontSize: 13,
                fontWeight: 800,
                letterSpacing: '.08em',
                color: i === activeZone ? 'white' : z.color,
                transition: 'color .2s',
              }}>{z.label}</div>
              <div style={{
                fontSize: 11,
                fontWeight: 600,
                marginTop: 3,
                color: i === activeZone ? 'rgba(255,255,255,.90)' : z.color + 'aa',
                transition: 'color .2s',
              }}>{z.range}</div>
            </div>
          ))}
        </div>

        {/* Active zone description */}
        <div style={{ fontSize: 15, color: '#3a4a5a', lineHeight: 1.60, minHeight: 44, textAlign: 'justify' }}>{zone.desc}</div>
      </div>
    </div>
  )
}

function ReadyPortrait() {
  return (
    <div style={{ flex: 1, width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: 'linear-gradient(160deg, #0a1628 0%, #0d2040 60%, #0a1628 100%)', position: 'relative', overflow: 'hidden' }}>
      {/* Background grid */}
      <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
        <defs>
          <pattern id="rp-grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M40 0L0 0 0 40" fill="none" stroke="rgba(184,147,42,.06)" strokeWidth=".5"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#rp-grid)"/>
      </svg>

      {/* Radial glow behind emblem */}
      <div style={{ position: 'absolute', top: '28%', left: '50%', transform: 'translate(-50%,-50%)', width: 300, height: 300, background: 'radial-gradient(circle, rgba(184,147,42,0.10) 0%, transparent 70%)', pointerEvents: 'none' }} />

      {/* Main content — vertically centred */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px 40px', gap: 22, position: 'relative', zIndex: 1 }}>

        {/* ORAS emblem */}
        <div style={{ animation: 'fadeUp .6s ease both .1s', opacity: 0 }}>
          <OrasMark size={60} />
        </div>

        {/* Hero text */}
        <div style={{ textAlign: 'center', animation: 'fadeUp .6s ease both .3s', opacity: 0 }}>
          <div style={{ fontSize: 10, color: '#b8932a', letterSpacing: '.28em', fontFamily: MONO, marginBottom: 12 }}>THE CLOCK STARTS NOW</div>
          <div style={{ fontSize: 52, fontWeight: 900, color: 'white', lineHeight: 1.1, letterSpacing: '-.02em' }}>Five years.<br/><span style={{ color: '#b8932a' }}>Your call.</span></div>
        </div>

        {/* Divider */}
        <div style={{ width: 48, height: 2, background: 'rgba(184,147,42,0.40)', borderRadius: 2, animation: 'fadeUp .5s ease both .42s', opacity: 0 }} />

        {/* Context line */}
        <div style={{ textAlign: 'center', animation: 'fadeUp .6s ease both .45s', opacity: 0, maxWidth: 320 }}>
          <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.52)', lineHeight: 1.7, fontFamily: MONO, letterSpacing: '.03em' }}>
            Allocate <span style={{ color: '#d4aa40' }}>$60M</span> across four departments.<br/>
            Navigate a <span style={{ color: '#d4aa40' }}>$800B</span> market. Prove them wrong.
          </p>
        </div>

        {/* Timeline */}
        <div style={{ width: '100%', maxWidth: 340, animation: 'fadeUp .6s ease both .5s', opacity: 0 }}>
          <div style={{ position: 'relative', marginBottom: 14 }}>
            <div style={{ height: 2, background: 'rgba(255,255,255,.10)', position: 'relative', overflow: 'hidden', borderRadius: 2 }}>
              <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(90deg,#b8932a,#d4aa40)', animation: 'growWidth 1.4s ease both .8s', transformOrigin: 'left', transform: 'scaleX(0)' }} />
            </div>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            {['Y1', 'Y2', 'Y3', 'Y4', 'Y5'].map((y, i) => (
              <div key={i} style={{ textAlign: 'center', animation: `fadeUp .4s ease both ${.8 + i * .12}s`, opacity: 0 }}>
                <div style={{ width: i === 0 ? 14 : 9, height: i === 0 ? 14 : 9, borderRadius: '50%', background: i === 0 ? '#b8932a' : 'rgba(255,255,255,.15)', border: `2px solid ${i === 0 ? '#b8932a' : 'rgba(255,255,255,.30)'}`, margin: '0 auto 6px', boxShadow: i === 0 ? '0 0 14px rgba(184,147,42,.60)' : 'none' }} />
                <div style={{ fontSize: 10, fontFamily: MONO, color: i === 0 ? '#b8932a' : 'rgba(255,255,255,.40)', fontWeight: i === 0 ? 700 : 400 }}>{y}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Stat chips */}
        <div style={{ display: 'flex', gap: 8, animation: 'fadeUp .6s ease both 1.4s', opacity: 0, flexWrap: 'wrap', justifyContent: 'center' }}>
          {[['$60M', 'PER YEAR'], ['$800B', 'MARKET SIZE'], ['5', 'YEAR HORIZON'], ['4', 'DEPARTMENTS']].map(([val, lbl], i) => (
            <div key={i} style={{ padding: '10px 16px', background: 'rgba(184,147,42,.10)', border: '1px solid rgba(184,147,42,.28)', borderRadius: 6, textAlign: 'center', minWidth: 72 }}>
              <div style={{ fontSize: 18, fontWeight: 900, fontFamily: MONO, color: '#d4aa40', lineHeight: 1 }}>{val}</div>
              <div style={{ fontSize: 8, fontFamily: MONO, color: 'rgba(255,255,255,0.38)', letterSpacing: '.14em', marginTop: 4 }}>{lbl}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Final CTA
function FinalCTA({ auth, onReady, style = {} }) {
  return (
    <div style={{ marginTop: 18, ...style }}>
      <button
        style={{ width: '100%', padding: '14px', background: '#0a1628', color: 'white', border: 'none', borderRadius: 8, fontSize: 14, fontWeight: 800, cursor: 'pointer', fontFamily: SANS, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, boxShadow: '0 4px 16px rgba(10,22,40,.28)', letterSpacing: '.02em' }}
        onClick={() => {
          if (auth?.is_controller) {
            api.beginSimulation(auth.team_key, auth.username).catch(() => {})
          }
          onReady(auth)
        }}
      >
        Begin Simulation
        <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M6 3l5 5-5 5" stroke="white" strokeWidth="2.2" strokeLinecap="round"/></svg>
      </button>
      <div style={{ fontSize: 10, color: '#8090a4', textAlign: 'center', marginTop: 8, fontFamily: MONO }}>All briefing details remain in Background tab.</div>
    </div>
  )
}

// Slide navigation
function SlideNav({ step, total, onNext, onBack, onSkip, isLast, accent = '#0a1628', nextDisabled = false, nextLabel }) {
  return (
    <div style={{ padding: '0 16px 16px', flexShrink: 0 }}>
      <div style={{ height: 1, background: '#e8ecf2', marginBottom: 14 }} />
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
        <button
          onClick={onBack}
          disabled={step === 0}
          style={{
            visibility: step === 0 ? 'hidden' : 'visible',
            background: 'white',
            border: '1.5px solid #d4dce8',
            borderRadius: 6,
            padding: '9px 18px',
            fontSize: 12,
            fontWeight: 700,
            color: '#3a4a5a',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 5,
            fontFamily: SANS,
            transition: 'border-color .15s, background .15s',
          }}
        >
          <svg width="11" height="11" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"/></svg>
          Back
        </button>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          {!isLast && (
            <button
              onClick={onSkip}
              style={{
                background: '#f5f7fa',
                border: '1.5px solid #d0d8e4',
                borderRadius: 6,
                padding: '9px 16px',
                fontSize: 11,
                fontWeight: 600,
                color: '#6a7a8a',
                cursor: 'pointer',
                fontFamily: SANS,
              }}
            >
              Skip all
            </button>
          )}
          {!isLast && (
            <button
              onClick={nextDisabled ? undefined : onNext}
              style={{
                background: nextDisabled ? 'rgba(26,58,107,.25)' : accent,
                border: 'none',
                borderRadius: 6,
                padding: '9px 22px',
                fontSize: 12,
                fontWeight: 700,
                color: 'white',
                cursor: nextDisabled ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                fontFamily: SANS,
                boxShadow: nextDisabled ? 'none' : `0 2px 10px ${accent}40`,
                transition: 'background .3s, box-shadow .3s',
              }}
            >
              {nextLabel || 'Next'}
              {!nextDisabled && <svg width="11" height="11" viewBox="0 0 16 16" fill="none"><path d="M6 3l5 5-5 5" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"/></svg>}
            </button>
          )}
        </div>
      </div>
      {/* Progress dots */}
      <div style={{ display: 'flex', gap: 3, marginTop: 12 }}>
        {Array.from({ length: total }, (_, i) => (
          <div key={i} style={{ flex: 1, height: 3, borderRadius: 2, background: i < step ? '#b8932a' : i === step ? accent : '#e0e6ef', transition: 'background 0.3s' }} />
        ))}
      </div>
    </div>
  )
}

// Why this slide exists: by the time a player lands on the real Allocate tab, they've been told
// *about* the mechanics but never used them.
function PracticeSlide({ slide, step, total, onNext, onBack, onSkip, isLast, scenario }) {
  const sym    = scenario?.currency_symbol      || '$'
  const suffix = scenario?.small_number_suffix  || 'K'
  const div    = inputDivisor(suffix)
  const budget = scenario?.total_budget || 60_000_000
  const departments = scenario?.departments || []
  const subDecisions = scenario?.sub_decisions || {}

  // Build constraints from the scenario payload directly.
  const constraints = useMemo(() => {
    const n = Math.max(1, departments.length)
    const share = Math.floor(budget / n / div) * div   // even split, snapped to step
    return departments.map(d => {
      const min = d.min_spend || 0
      const max = d.max_spend || budget
      // Clamp the even share into [min, max]. If max < share, use max.
      const def = Math.min(max, Math.max(min, share))
      return {
        dept_name: d.name,
        min, max, default: def,
        step: div,
      }
    })
  }, [departments, budget, div])

  // Local state — no persistence, no API calls.
  const [sliderValues, setSliderValues] = useState(() => {
    const init = {}
    constraints.forEach(c => { init[c.dept_name] = c.default })
    return init
  })
  const [subdecisions, setSubdecisions] = useState({})
  const [sealed, setSealed] = useState(false)
  const [coachStep, setCoachStep] = useState(0)   // 0..4, 4 = dismissed
  const [resetKey, setResetKey] = useState(0)

  const totalSpend = useMemo(
    () => Object.values(sliderValues).reduce((s, v) => s + v, 0),
    [sliderValues]
  )
  // Match the live game's seal rules exactly (AllocateTab line 186): over-budget blocks seal;
  // under-budget is LEGAL (but flagged with a penalty colour in the donut, same as the live game).
  const overBudget = totalSpend > budget
  const underBudget = totalSpend < budget   // legal — used only for visual penalty cue
  const allStrategiesSet = constraints.every(c => {
    const opts = subDecisions[c.dept_name]?.options
    return !opts || Object.keys(opts).length === 0 || !!subdecisions[c.dept_name]
  })
  const canSeal = !sealed && !overBudget && allStrategiesSet

  const depts = useMemo(
    () => constraints.map(c => {
      const dc = getDept(c.dept_name)
      return { name: c.dept_name, value: sliderValues[c.dept_name] ?? c.default, color: dc.color }
    }),
    [constraints, sliderValues]
  )

  const handleReset = () => {
    const fresh = {}
    constraints.forEach(c => { fresh[c.dept_name] = c.default })
    setSliderValues(fresh)
    setSubdecisions({})
    setSealed(false)
    setResetKey(k => k + 1)
  }

  const handleSeal = () => { setSealed(true) }

  // Coach steps reference specific elements; we tag those elements with data attributes and the overlay
  // positions itself by querying for them.
  const COACH_STEPS = [
    { target: 'donut',    text: 'This is your annual budget. Your four allocations must add up to exactly this amount.' },
    { target: 'slider',   text: 'Move each slider between its floor and ceiling. Drag the thumb or type a number directly.' },
    { target: 'strategy', text: 'Pick one strategic direction for each department. Each choice shifts which customer segments you appeal to.' },
    { target: 'seal',     text: 'When the budget is exactly used and all four strategies are set, this button activates. Hold it to lock the year.' },
  ]
  const showCoach = coachStep < COACH_STEPS.length

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', background: '#f4f6fa', position: 'relative' }}>
      <AllocateSharedStyles />

      <div style={{
        background: 'linear-gradient(90deg, #b8932a 0%, #d4aa40 50%, #b8932a 100%)',
        color: 'white',
        padding: '8px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 16,
        flexShrink: 0,
        boxShadow: '0 2px 8px rgba(184,147,42,.30)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="white" strokeWidth="1.8" fill="rgba(255,255,255,.15)"/>
            <path d="M12 7v5l3 2" stroke="white" strokeWidth="1.8" strokeLinecap="round"/>
          </svg>
          <div style={{ fontFamily: MONO, fontSize: 11, fontWeight: 800, letterSpacing: '.20em', textTransform: 'uppercase' }}>
            Practice Round
          </div>
          <div style={{ fontFamily: SANS, fontSize: 12, fontWeight: 500, opacity: 0.92 }}>
            · Year 0 of {scenario?.num_periods || 5} · Decisions here don't affect your game
          </div>
        </div>
        <button
          onClick={handleReset}
          style={{
            background: 'rgba(255,255,255,.18)',
            border: '1px solid rgba(255,255,255,.40)',
            color: 'white',
            fontFamily: MONO,
            fontSize: 10,
            fontWeight: 700,
            letterSpacing: '.14em',
            textTransform: 'uppercase',
            padding: '5px 12px',
            borderRadius: 4,
            cursor: 'pointer',
          }}
        >
          ↺ Reset
        </button>
      </div>

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', minHeight: 0 }}>

        <div style={{ flex: 1.2, padding: '16px 24px 16px', display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0, gap: 12 }}>
          <div data-coach-target="donut" style={{
            display: 'flex',
            alignItems: 'center',
            gap: 20,
            padding: '12px 18px',
            background: 'white',
            border: '1px solid #D4DCE8',
            borderRadius: 4,
            boxShadow: '0 1px 3px rgba(10,22,40,.04)',
            position: 'relative',
            flexShrink: 0,
            // When this is the active coach target, lift above the dim layer (z-index 30) and outline in gold.
            zIndex: showCoach && COACH_STEPS[coachStep]?.target === 'donut' ? 31 : 'auto',
            outline: showCoach && COACH_STEPS[coachStep]?.target === 'donut' ? '3px solid #b8932a' : 'none',
            outlineOffset: 4,
            transition: 'outline-color .2s',
          }}>
            <AllocationDonut
              compact
              depts={depts} budget={budget} totalSpend={totalSpend}
              sym={sym} suffix={suffix}
              overBudget={overBudget} penalty={underBudget && !overBudget}
            />
            <DonutLegend
              depts={depts} totalSpend={totalSpend} budget={budget}
              sym={sym} suffix={suffix} overBudget={overBudget}
            />
          </div>

          <div
            key={`cards-${resetKey}`}
            data-coach-target="cards"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, minmax(0, 1fr))',
              gap: 8,
              flex: 1,
              minHeight: 0,
            }}
          >
            {constraints.map((c, i) => {
              const isActiveCoachTarget = showCoach && i === 0 && (
                COACH_STEPS[coachStep]?.target === 'slider' ||
                COACH_STEPS[coachStep]?.target === 'strategy'
              )
              return (
                <div
                  key={c.dept_name}
                  data-coach-target={i === 0 && coachStep === 1 ? 'slider' : (i === 0 && coachStep === 2 ? 'strategy' : null)}
                  style={{
                    position: 'relative',
                    // Lift above the coach dim layer so the spotlit card stays crisp.
                    zIndex: isActiveCoachTarget ? 31 : 'auto',
                    outline: isActiveCoachTarget ? '3px solid #b8932a' : 'none',
                    outlineOffset: 4,
                    borderRadius: 4,
                    transition: 'outline-color .2s',
                    background: 'white',  // ensures crisp render through the dim
                  }}
                >
                  <DepartmentCard
                    constraint={c}
                    subDecisionOptions={subDecisions[c.dept_name]}
                    value={sliderValues[c.dept_name] ?? c.default}
                    onValueChange={v => setSliderValues(p => ({ ...p, [c.dept_name]: v }))}
                    strategyValue={subdecisions[c.dept_name]}
                    onStrategyChange={key => setSubdecisions(p => ({ ...p, [c.dept_name]: key }))}
                    totalSpend={totalSpend}
                    sym={sym} suffix={suffix} div={div}
                    readOnly={sealed}
                    compact
                  />
                </div>
              )
            })}
          </div>

          <div style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            fontFamily: MONO, fontSize: 9, fontWeight: 600,
            color: 'rgba(26,58,107,.55)',
            letterSpacing: '.04em',
            paddingLeft: 2, paddingRight: 2,
            flexShrink: 0,
          }}>
            <span>
              <span style={{ color: 'rgba(26,58,107,.40)', marginRight: 6, letterSpacing: '.12em' }}>FLOORS:</span>
              {constraints.map((c, i) => (
                <span key={c.dept_name} style={{ marginRight: 10 }}>
                  {c.dept_name} {fmtCur(c.min, sym, suffix)}
                </span>
              ))}
            </span>
            <span style={{ color: 'rgba(26,58,107,.40)', fontStyle: 'italic' }}>
              Sliders enforce min/max — drag freely
            </span>
          </div>

          <div data-coach-target="seal" style={{
            marginTop: 12,
            position: 'relative',
            zIndex: showCoach && COACH_STEPS[coachStep]?.target === 'seal' ? 31 : 'auto',
            outline: showCoach && COACH_STEPS[coachStep]?.target === 'seal' ? '3px solid #b8932a' : 'none',
            outlineOffset: 4,
            borderRadius: 4,
            transition: 'outline-color .2s',
            background: 'white',
          }}>
            <HoldToSealButton
              key={`seal-${resetKey}`}
              disabled={!canSeal}
              onComplete={handleSeal}
              label={
                overBudget
                  ? `Over by ${fmtCur(totalSpend - budget, sym, suffix)} — reduce a slider`
                  : !allStrategiesSet
                    ? 'Pick a strategy for every department'
                    : underBudget
                      ? `Hold to Lock · ${fmtCur(budget - totalSpend, sym, suffix)} unspent (allowed)`
                      : 'Hold to Lock Year 1'
              }
              year={1}
            />
          </div>
        </div>

        {/* RIGHT — narrative panel */}
        <div style={{ width: 380, flexShrink: 0, background: 'rgba(255,255,255,.97)', borderLeft: '1px solid rgba(26,58,107,.12)', display: 'flex', flexDirection: 'column', boxShadow: '-2px 0 20px rgba(10,22,40,.06)' }}>
          {/* Panel header */}
          <div style={{ padding: '22px 24px 0', flexShrink: 0 }}>
            <div style={{ fontSize: 9, color: '#b8932a', letterSpacing: '.20em', fontFamily: MONO, textTransform: 'uppercase', marginBottom: 6 }}>
              Transmission {String(step + 1).padStart(2, '0')} · practice
            </div>
            <h2 style={{ fontSize: 20, fontWeight: 900, color: '#0a1628', lineHeight: 1.2, margin: 0 }}>{slide?.title || 'Practice Round'}</h2>
            <div style={{ height: 2, width: 32, background: '#1a3a6b', borderRadius: 1, marginTop: 8 }} />
          </div>

          {/* Panel body */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '16px 24px' }}>
            {!sealed ? (
              <RichText
                text={slide?.content || "Try one year. Move the sliders. Pick a strategy in each department. Lock it.\n\nNothing here counts. Get comfortable with the controls — when the real Year 1 starts, you'll have done this exactly once before."}
                style={{ fontSize: 15, color: '#3a4a5a', lineHeight: 1.60, textAlign: 'justify' }}
              />
            ) : (
              <div style={{ animation: 'fadeUp .35s ease both' }}>
                <div style={{
                  padding: 14,
                  background: 'rgba(184,147,42,.10)',
                  border: '1px solid rgba(184,147,42,.40)',
                  borderRadius: 4,
                  marginBottom: 14,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                      <rect x="5" y="11" width="14" height="11" rx="2" fill="#b8932a" stroke="#b8932a" strokeWidth="1.5"/>
                      <path d="M8 11V7a4 4 0 018 0v4" stroke="#b8932a" strokeWidth="1.6" strokeLinecap="round"/>
                      <circle cx="12" cy="16" r="1.5" fill="white"/>
                    </svg>
                    <div style={{ fontFamily: MONO, fontSize: 10, fontWeight: 800, color: '#b8932a', letterSpacing: '.18em', textTransform: 'uppercase' }}>
                      Year 1 Sealed
                    </div>
                  </div>
                  <div style={{ fontSize: 13, color: '#3a4a5a', lineHeight: 1.65 }}>
                    You just made a full turn. The real game has <strong style={{ color: '#0a1628' }}>{scenario?.num_periods || 5}</strong> of these, with a clock per year — and your decisions will stick.
                  </div>
                </div>
                <div style={{ fontSize: 13, color: '#3a4a5a', lineHeight: 1.75 }}>
                  Hit <strong style={{ color: '#0a1628' }}>Reset</strong> to try a different allocation, or <strong style={{ color: '#0a1628' }}>Continue</strong> when you're ready to begin.
                </div>
              </div>
            )}
          </div>

          <SlideNav
            step={step} total={total}
            onNext={showCoach ? undefined : onNext}
            onBack={onBack} onSkip={onSkip} isLast={isLast} accent="#1a3a6b"
            nextDisabled={showCoach}
            nextLabel={showCoach ? 'Complete tour first' : undefined}
          />
        </div>
      </div>

      {showCoach && (
        <>
          {/* Dim layer — non-blocking. */}
          <div style={{
            position: 'absolute',
            inset: 0,
            background: 'rgba(10,22,40,.38)',
            zIndex: 30,
            pointerEvents: 'none',
            animation: 'fadeUp .25s ease both',
          }} />

          <div style={{
            position: 'absolute',
            right: 16,
            top: 60,
            width: 340,
            background: 'white',
            borderRadius: 6,
            border: '2px solid #b8932a',
            boxShadow: '0 16px 48px rgba(10,22,40,.32)',
            padding: '16px 18px 14px',
            zIndex: 32,
            pointerEvents: 'auto',
            animation: 'fadeUp .25s ease both',
          }}>
            <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 10 }}>
              <div style={{ fontFamily: MONO, fontSize: 9, fontWeight: 800, color: '#b8932a', letterSpacing: '.20em', textTransform: 'uppercase' }}>
                Quick Tour · {coachStep + 1} of {COACH_STEPS.length}
              </div>
              <button
                onClick={() => setCoachStep(COACH_STEPS.length)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontFamily: MONO,
                  fontSize: 9,
                  fontWeight: 700,
                  color: '#8090a4',
                  letterSpacing: '.14em',
                  textTransform: 'uppercase',
                  cursor: 'pointer',
                  padding: 0,
                }}
              >
                Skip tour
              </button>
            </div>
            <div style={{ fontSize: 14, color: '#0a1628', lineHeight: 1.55, fontFamily: SANS, marginBottom: 16, fontWeight: 500 }}>
              {COACH_STEPS[coachStep].text}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
              <div style={{ display: 'flex', gap: 5 }}>
                {COACH_STEPS.map((_, i) => (
                  <div key={i} style={{
                    width: i === coachStep ? 22 : 8,
                    height: 4,
                    borderRadius: 2,
                    background: i <= coachStep ? '#b8932a' : '#e0e6ef',
                    transition: 'width .25s, background .25s',
                  }} />
                ))}
              </div>
              <button
                onClick={() => setCoachStep(s => s + 1)}
                style={{
                  background: '#0a1628',
                  border: 'none',
                  borderRadius: 6,
                  padding: '8px 18px',
                  fontSize: 12,
                  fontWeight: 700,
                  color: 'white',
                  cursor: 'pointer',
                  fontFamily: SANS,
                  display: 'flex', alignItems: 'center', gap: 6,
                  letterSpacing: '.02em',
                }}
              >
                {coachStep === COACH_STEPS.length - 1 ? 'Start Practicing' : 'Next'}
                <svg width="11" height="11" viewBox="0 0 16 16" fill="none"><path d="M6 3l5 5-5 5" stroke="white" strokeWidth="2.2" strokeLinecap="round"/></svg>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}


// Main StoryboardPage
export default function StoryboardPage({ onReady, auth: authProp, scenarioInfoProp, competitorsProp, sbRemaining: sbRemainingProp, sbExpired: sbExpiredProp, simulationBegun: simulationBegunProp }) {
  const { auth: authCtx } = useAuth()
  const auth = authProp || authCtx

  const [step, setStep]         = useState(0)
  const [dir, setDir]           = useState('right')
  const [scenario, setScenario] = useState(scenarioInfoProp || null)
  const [competitors, setCompetitors] = useState(competitorsProp || [])
  const [loading, setLoading]   = useState(!scenarioInfoProp)
  // sbRemaining, sbExpired, and simulationBegun come from the persistent WS
  // in App.jsx (useGameSocket). No local WS needed — one connection for all phases.
  const [simulationBegun, setSimulationBegun] = useState(simulationBegunProp ?? false)
  const [sbRemaining, setSbRemaining] = useState(sbRemainingProp ?? 1500)
  const [sbExpired, setSbExpired]     = useState(sbExpiredProp ?? false)
  const [typeActive, setTypeActive]   = useState(true)
  const [skipped, setSkipped]         = useState(false)
  const readyFired = useRef(false)  // prevent double-call
  // True only once a real (server-driven) storyboard countdown has been seen.
  // `sbRemaining === 0` is ambiguous: it means "timer expired" only if a timer
  // was actually running. After a reset, no storyboard timer is running, so the
  // socket reports 0 from the start — which must NOT be read as "expired", or
  // the storyboard is skipped the instant it mounts. This ref disambiguates.
  const sawTimerRef = useRef((sbRemainingProp ?? 0) > 0)

  // Sync from persistent WS props
  useEffect(() => {
    if (sbRemainingProp != null) {
      if (sbRemainingProp > 0) sawTimerRef.current = true
      setSbRemaining(sbRemainingProp)
    }
  }, [sbRemainingProp])
  useEffect(() => { if (sbExpiredProp)           setSbExpired(true) },             [sbExpiredProp])
  useEffect(() => { if (simulationBegunProp)     setSimulationBegun(true) },       [simulationBegunProp])

  // Sync scenario when prop arrives (App.jsx may still be fetching when we mount)
  useEffect(() => { if (scenarioInfoProp) { setScenario(scenarioInfoProp); setLoading(false) } }, [scenarioInfoProp])
  useEffect(() => { if (competitorsProp?.length > 0) setCompetitors(competitorsProp) }, [competitorsProp])

  useEffect(() => {
    if (sbRemaining <= 0) return
    const id = setInterval(() => setSbRemaining(r => Math.max(0, r - 1)), 1000)
    return () => clearInterval(id)
  }, [sbRemaining])

  useEffect(() => { if (sbExpired       && !readyFired.current) { readyFired.current = true; onReady(auth) } }, [sbExpired])       // eslint-disable-line
  useEffect(() => { if (simulationBegun && !readyFired.current) { readyFired.current = true; onReady(auth) } }, [simulationBegun]) // eslint-disable-line
  useEffect(() => { if (sbRemaining === 0 && sawTimerRef.current && !readyFired.current) { readyFired.current = true; onReady(auth) } }, [sbRemaining]) // eslint-disable-line

  useEffect(() => {
    // Only fetch if no prop was provided AND it hasn't arrived via the sync effect
    if (scenarioInfoProp) return
    api.getScenarioInfo().then(d => { setScenario(d); setLoading(false) }).catch(() => setLoading(false))
  }, []) // eslint-disable-line

  useEffect(() => {
    if (competitorsProp?.length > 0) return  // already have them from prop
    if (!auth?.team_key) return
    api.getGameState(auth.team_key)
      .then(data => { const seed = data?.game_state?.play_seed; if (seed) return api.getCompetitors(seed) })
      .then(data => { if (data?.competitors) setCompetitors(data.competitors) })
      .catch(() => {})
  }, [auth?.team_key]) // eslint-disable-line

  const slides = useMemo(() => {
    if (!scenario) return []
    const sb = scenario.storyboard || {}
    const sym    = scenario.currency_symbol || '$'
    const suffix = scenario.small_number_suffix || 'K'
    const budget = scenario.total_budget || 60_000_000
    const numPeriods = scenario.num_periods || 5

    // Attach each department's strategy options (from sub_decisions) directly to the department object.
    const subDecisions = scenario.sub_decisions || {}
    // Helper: derive a short chip label from a long full label.
    const toShortLabel = (full) => {
      if (!full) return ''
      const first = String(full).split(/ & | \(/)[0].trim()
      if (first.length > 18) return first.split(/\s+/).slice(0, 2).join(' ')
      return first
    }
    const departmentsEnriched = (scenario.departments || []).map(d => {
      const sd = subDecisions[d.name]
      const opts = sd?.options || {}
      const strategy_options = Object.entries(opts).map(([key, opt]) => {
        const fullLabel = (typeof opt === 'object' ? opt.label : opt) || key
        return {
          key,
          label: fullLabel,
          short_label: toShortLabel(fullLabel),
          description: (typeof opt === 'object' ? opt.description : '') || '',
          // Synergies: { dept_name: smax_bonus } — boost the named department when this strategy is chosen.
          synergy: (typeof opt === 'object' && opt.synergy) ? opt.synergy : {},
        }
      })
      return { ...d, strategy_options }
    })

    const result = []

    // Narrative arc (world → role) — unchanged
    if (sb.world_headline || sb.world_body)
      result.push({ title: sb.world_headline || 'The World', content: sb.world_body || '', type: 'world', scenarioId: scenario.scenario_id || 'us_ev' })
    if (sb.market_body)
      result.push({ title: `The ${scenario.market_label || 'EV Market'}`, content: sb.market_body, type: 'market' })
    if (sb.company_body)
      result.push({ title: scenario.company_name || 'Your Company', subtitle: sb.company_subtitle || null, content: sb.company_body, type: 'company' })
    if (sb.product_body)
      result.push({ title: scenario.product_name || 'The Product', subtitle: sb.product_subtitle || null, content: sb.product_body, type: 'product' })
    if (sb.role_body)
      result.push({ title: 'Your Role', content: sb.role_body, type: 'role' })

    // Mechanics arc (departments → mandate → objective)
    // Departments first so users understand the levers before seeing the mandate.
    if (sb.departments_intro && scenario.departments?.length > 0)
      result.push({
        title: 'Your Four Levers',
        content: sb.departments_intro,
        type: 'departments',
        departments: departmentsEnriched,
        sym, suffix,
        maxChangeRate: 0.30,  // matches cfg.max_change_rate; surfaced as footnote
      })

    // Mandate: the core loop frame (annual budget, five periods, locking).
    const mandateBody = sb.mandate_body || (
      `Each year you receive a fresh **${fmtCur(budget, sym, suffix)}** in operating budget. ` +
      `You allocate it across four departments and choose a strategic direction for each.\n\n` +
      `You do this **${numPeriods} times**. Once a year locks, you cannot return to it — but the next year unlocks a fresh budget, ` +
      `**plus a small bonus**: roughly 3% of last year's profit is reinvested into the next year's budget. ` +
      `Even a loss year keeps a floor — you'll always get at least half the base budget to work with.\n\n` +
      `What carries between years isn't just the bonus. It's the consequences. A strong R&D year still pays off two years later. ` +
      `A starved Operations year still chokes Sales the year after. Your job is to play ${numPeriods} connected hands, not ${numPeriods} independent ones.`
    )
    result.push({
      title: 'Your Mandate',
      content: mandateBody,
      type: 'mandate',
      budget, numPeriods, sym, suffix,
    })

    if (sb.objective_body)
      result.push({
        title: 'How You\'re Scored',
        content: sb.objective_body,
        type: 'objective'
      })

    // Competitors (narrative)
    if (sb.competitors_intro)
      result.push({ title: 'Your Competitors', content: sb.competitors_intro, type: 'competitors', competitors })

    // Inserted only when the scenario has the data we need (departments + sub_decisions).
    if (scenario.departments?.length > 0) {
      const practiceBody = sb.practice_body || (
        "Try one year. Move the four sliders — they start at an even split. " +
        "Each department has a floor and a ceiling; the sliders won't let you go past either. " +
        "Pick a strategic direction in each. Lock the year.\n\n" +
        "Watch the strategy chips: each shifts which customer segments respond, and some pairings boost other departments via synergies.\n\n" +
        "Nothing here counts — get comfortable with the controls. When the real Year 1 starts, you'll have done this exactly once before."
      )
      result.push({
        title: 'Practice Round',
        content: practiceBody,
        type: 'practice',
      })
    }

    // Mechanics summary — final checklist before the clock starts
    result.push({
      title: 'How It Works',
      content: (
        '**The timer is real.** Each year has a fixed window to allocate your budget and lock in your decisions. ' +
        'When time runs out, the year seals automatically.\n\n' +
        '**Decisions are irreversible.** Once your team seals a year, there is no going back.\n\n' +
        '**Everyone advances together.** After your team locks a year, you will wait for all other teams to do the same before the next year begins. ' +
        'This is by design — not a technical issue.\n\n' +
        '**One controller per team.** Only the designated controller can move sliders and seal decisions. ' +
        'Other team members can view and advise but cannot interact directly.\n\n' +
        `**Numbers are in thousands.** A budget of ${sym}60,000${suffix} means ${sym}60 million. This notation is used throughout.`
      ),
      type: 'mechanics',
    })

    // Ready (final CTA)
    result.push({ title: sb.ready_headline || 'Ready to Begin', content: sb.ready_body || 'The clock starts now.', type: 'ready', isFinal: true })
    return result
  }, [scenario, competitors])

  const total   = slides.length
  const isLast  = step >= total - 1
  const current = slides[step] || null
  const style   = SLIDE_STYLES[current?.type] || 'blueprint'

  const { displayed, done } = useTypewriter(current?.content || '', typeActive && !!current && !skipped, 12)

  useEffect(() => {
    setTypeActive(false)
    const t = setTimeout(() => setTypeActive(true), 80)
    return () => clearTimeout(t)
  }, [step])

  const goNext = useCallback(() => { setDir('right'); setStep(s => Math.min(total - 1, s + 1)) }, [total])
  const goBack = useCallback(() => { setDir('left');  setStep(s => Math.max(0, s - 1)) }, [])

  // Skip-button behavior: jump to the final slide.
  const skipAll = useCallback(() => {
    setSkipped(true)
    setDir('right')
    setStep(total - 1)
  }, [total])

  const timerIsLow  = sbRemaining <= 120
  const timerIsWarn = sbRemaining > 120 && sbRemaining <= 300

  if (loading) return (
    <div style={{ minHeight: '100vh', background: '#f0f4fa', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <span style={{ fontSize: 12, color: '#8090a4', fontFamily: MONO }}>Loading briefing...</span>
    </div>
  )

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', fontFamily: SANS, position: 'relative', zIndex: 2 }}>
      <style>{`
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
        @keyframes fadeUp { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
        @keyframes growWidth { from{transform:scaleX(0)} to{transform:scaleX(1)} }
        @keyframes ringIn { from{stroke-dasharray:0 200} }
        @keyframes slideInFromLeft { from{opacity:0;transform:translateX(-20px)} to{opacity:1;transform:translateX(0)} }
        @keyframes slideInFromRight { from{opacity:0;transform:translateX(20px)} to{opacity:1;transform:translateX(0)} }
        @keyframes slideTransitionInright { from{opacity:0;transform:translateX(24px)} to{opacity:1;transform:translateX(0)} }
        @keyframes slideTransitionInleft  { from{opacity:0;transform:translateX(-24px)} to{opacity:1;transform:translateX(0)} }
        @keyframes needleSwing { from{transform:rotate(-90deg)} to{transform:rotate(45deg)} }
        @keyframes cpPulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.45;transform:scale(.85)} }
      `}</style>

      {/* Header */}
      <div style={{ background: '#0a1628', height: 68, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 28px', borderBottom: '3px solid #b8932a', flexShrink: 0, boxShadow: '0 2px 16px rgba(10,22,40,.20)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <OrasMark size={22} />
          <div style={{ width: 1, height: 28, background: 'rgba(255,255,255,.18)', margin: '0 4px' }} />
          <div>
            <div style={{ fontSize: 20, fontWeight: 900, letterSpacing: '.20em', color: 'rgba(255,255,255,.98)', lineHeight: 1 }}>ORAS</div>
            <div style={{ fontSize: 10, color: 'rgba(255,255,255,.50)', letterSpacing: '.14em', fontFamily: MONO, marginTop: 2 }}>Strategic Briefing</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ fontFamily: MONO, fontSize: 11, color: 'rgba(255,255,255,.50)', letterSpacing: '.1em', fontWeight: 600 }}>
            {String(step + 1).padStart(2, '0')} / {String(total).padStart(2, '0')}
          </div>
          {sbRemaining > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 7, padding: '8px 16px', borderRadius: 6, background: timerIsLow ? 'rgba(138,32,32,.28)' : timerIsWarn ? 'rgba(184,147,42,.18)' : 'rgba(255,255,255,.09)', border: `1px solid ${timerIsLow ? 'rgba(138,32,32,.55)' : timerIsWarn ? 'rgba(184,147,42,.45)' : 'rgba(255,255,255,.18)'}`, fontFamily: MONO, fontSize: 15, fontWeight: 700, color: timerIsLow ? '#e89090' : timerIsWarn ? '#d4aa40' : 'rgba(255,255,255,.85)', letterSpacing: '.06em' }}>
            <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="9" r="6" stroke="currentColor" strokeWidth="1.5"/><path d="M8 6v3l2 1.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/></svg>
            {fmtTime(sbRemaining)}
          </div>
          )}
        </div>
      </div>

      {/* Progress strip */}
      <div style={{ height: 3, background: '#e0e6ef', flexShrink: 0 }}>
        <div style={{ height: '100%', width: `${total > 1 ? (step / (total - 1)) * 100 : 0}%`, background: 'linear-gradient(90deg,#b8932a,#d4aa40)', transition: 'width .4s ease' }} />
      </div>

      {/* Slide */}
      <div key={`${step}-${dir}`} style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', animation: `slideTransitionIn${dir} .30s cubic-bezier(.4,0,.2,1) both` }}>
        {style === 'envelope'
          ? <AppointmentSlide slide={current} step={step} total={total} onNext={goNext} onBack={goBack} onSkip={skipAll} isLast={isLast} scenario={scenario} />
          : style === 'practice'
          ? <PracticeSlide slide={current} step={step} total={total} onNext={goNext} onBack={goBack} onSkip={skipAll} isLast={isLast} scenario={scenario} />
          : style === 'blueprint'
          ? <BlueprintSlide slide={current} displayed={displayed} done={done} step={step} total={total} onNext={goNext} onBack={goBack} onSkip={skipAll} isLast={isLast} auth={auth} onReady={onReady} />
          : <PortraitSlide slide={current} displayed={displayed} done={done} step={step} total={total} onNext={goNext} onBack={goBack} onSkip={skipAll} isLast={isLast} auth={auth} onReady={onReady} competitors={competitors} />}
      </div>
    </div>
  )
}
