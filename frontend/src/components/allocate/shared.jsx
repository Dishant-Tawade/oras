// These components are the visual building blocks of the Allocate tab.

import React, { useState, useEffect, useRef } from 'react'

/* ── Department palette ─────────────────────────────────────────────────── */
export const DEPT_CFG = {
  'R&D':        { color: '#1A3A6B', colorL: '#2C5494', bg: 'rgba(26,58,107,0.04)',  bgInput: 'rgba(26,58,107,0.06)',  bdr: '#B0C4E0' },
  'Sales':      { color: '#8A6A10', colorL: '#8A6A10', bg: 'rgba(138,106,16,0.04)', bgInput: 'rgba(138,106,16,0.06)', bdr: '#E8D090' },
  'Operations': { color: '#3D7A58', colorL: '#1A5C3A', bg: 'rgba(61,122,88,0.04)',  bgInput: 'rgba(61,122,88,0.06)',  bdr: '#B8D8C4' },
  'Marketing':  { color: '#4A2A7A', colorL: '#4A2A7A', bg: 'rgba(74,42,122,0.04)',  bgInput: 'rgba(74,42,122,0.06)',  bdr: '#C8B0E0' },
}

export function getDept(name) {
  return DEPT_CFG[name] || { color: '#1A5C3A', colorL: '#1A5C3A', bg: 'rgba(26,92,58,0.04)', bgInput: 'rgba(26,92,58,0.06)', bdr: '#B8D8C4' }
}

/* ── Formatters ─────────────────────────────────────────────────────────── */
export function fmtCur(val, sym, suffix) {
  sym = sym || '$'; suffix = suffix || 'K'
  if (val === null || val === undefined) return `${sym}0${suffix}`
  const abs = Math.abs(val); const neg = val < 0 ? '-' : ''
  if (suffix === 'K') return `${neg}${sym}${Math.round(abs / 1e3).toLocaleString()}K`
  if (suffix === 'L') { if (abs >= 1e7) return `${neg}${sym}${(abs / 1e7).toFixed(1)}Cr`; return `${neg}${sym}${Math.round(abs / 1e5).toLocaleString()}L` }
  return `${neg}${sym}${(abs / 1e6).toFixed(2)}M`
}

export function inputDivisor(suffix) { if (suffix === 'L') return 100000; if (suffix === 'M') return 1000000; return 1000 }

/* ── Donut: budget allocation visual ─────────────────────────────────────── */
export function AllocationDonut({ depts, budget, totalSpend, sym, suffix, overBudget, penalty, cappedOut = false, compact = false }) {
  const SIZE = compact ? 180 : 280
  const R    = compact ? 72  : 112
  const SW   = compact ? 16  : 24
  const C = 2 * Math.PI * R
  const cx = SIZE / 2, cy = SIZE / 2

  const ringTotal = overBudget ? totalSpend : budget
  let cursor = 0
  const arcs = depts.map(d => {
    const frac = ringTotal > 0 ? d.value / ringTotal : 0
    const len = C * frac
    const offset = -cursor
    cursor += len
    return { ...d, len, offset, frac }
  })
  const usedLen = arcs.reduce((s, a) => s + a.len, 0)
  const unusedLen = Math.max(0, C - usedLen)

  const pctUsed = budget > 0 ? Math.min(100, (totalSpend / budget) * 100) : 0
  const remaining = budget - totalSpend

  // Centre-text sizes scale with the donut so the readout stays legible.
  const fsLabel  = compact ? 8  : 10
  const fsAmount = compact ? 18 : 26
  const fsOf     = compact ? 9  : 11
  const fsState  = compact ? 9  : 11
  const dyLabel  = compact ? -18 : -26
  const dyOf     = compact ? 16  : 24
  const dyState  = compact ? 32  : 48

  return (
    <svg width={SIZE} height={SIZE} style={{ display: 'block' }}>
      <circle cx={cx} cy={cy} r={R} fill="none" stroke="#EEF1F6" strokeWidth={SW} />

      <g transform={`rotate(-90 ${cx} ${cy})`}>
        {arcs.map(a => (
          <circle
            key={a.name}
            cx={cx} cy={cy} r={R}
            fill="none"
            stroke={overBudget ? '#B03030' : a.color}
            strokeWidth={SW}
            strokeDasharray={`${a.len} ${C - a.len}`}
            strokeDashoffset={a.offset}
            strokeLinecap="butt"
            style={{ transition: 'stroke-dasharray 0.35s ease, stroke-dashoffset 0.35s ease, stroke 0.25s ease' }}
          />
        ))}
        {unusedLen > 0 && !overBudget && (
          <circle
            cx={cx} cy={cy} r={R}
            fill="none"
            stroke={penalty ? '#B8932A' : '#EEF1F6'}
            strokeWidth={SW}
            strokeDasharray={`${unusedLen} ${C - unusedLen}`}
            strokeDashoffset={-usedLen}
            opacity={penalty ? 0.5 : 1}
            style={{ transition: 'stroke-dasharray 0.35s ease, stroke-dashoffset 0.35s ease, stroke 0.25s ease, opacity 0.25s ease' }}
          />
        )}
      </g>

      <text x={cx} y={cy + dyLabel} textAnchor="middle"
        style={{ fontFamily: "'DM Mono',monospace", fontSize: fsLabel, fontWeight: 700, fill: '#8090A4', letterSpacing: '0.18em' }}>
        ALLOCATED
      </text>
      <text x={cx} y={cy + 4} textAnchor="middle"
        style={{
          fontFamily: "'DM Mono',monospace",
          fontSize: fsAmount, fontWeight: 800,
          fill: overBudget ? '#8A2020' : '#0A1628',
          letterSpacing: '-0.5px',
        }}>
        {fmtCur(totalSpend, sym, suffix)}
      </text>
      <text x={cx} y={cy + dyOf} textAnchor="middle"
        style={{ fontFamily: "'DM Mono',monospace", fontSize: fsOf, fill: '#6A7A8A' }}>
        of {fmtCur(budget, sym, suffix)}
      </text>
      <text x={cx} y={cy + dyState} textAnchor="middle"
        style={{
          fontFamily: "'DM Sans',sans-serif",
          fontSize: fsState, fontWeight: 700,
          fill: overBudget ? '#8A2020' : (penalty && !cappedOut) ? '#8A6A10' : '#1A5C3A',
          letterSpacing: '0.06em', textTransform: 'uppercase',
        }}>
        {overBudget
          ? `Over by ${fmtCur(Math.abs(remaining), sym, suffix)}`
          : cappedOut
            ? `${pctUsed.toFixed(0)}% used · caps reached`
            : penalty
              ? `${pctUsed.toFixed(0)}% used · penalty`
              : `${pctUsed.toFixed(0)}% used`}
      </text>
    </svg>
  )
}

/* ── Legend ─────────────────────────────────────────────────────────────── */
export function DonutLegend({ depts, totalSpend, budget, sym, suffix, overBudget }) {
  const remaining = budget - totalSpend
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, width: 320 }}>
      {depts.map(d => {
        const sharePct = totalSpend > 0 ? (d.value / totalSpend) * 100 : 0
        return (
          <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ width: 11, height: 11, borderRadius: 2, background: d.color, flexShrink: 0 }} />
            <span style={{ fontSize: 13, color: '#0A1628', fontWeight: 500, flex: 1 }}>{d.name}</span>
            <span style={{ fontFamily: "'DM Mono',monospace", fontSize: 12, color: '#3A4A5A', fontWeight: 600, textAlign: 'right' }}>
              {fmtCur(d.value, sym, suffix)}
            </span>
            <span style={{ fontFamily: "'DM Mono',monospace", fontSize: 11, color: '#8090A4', fontWeight: 500, width: 36, textAlign: 'right' }}>
              {sharePct.toFixed(0)}%
            </span>
          </div>
        )
      })}
      <div style={{ height: 1, background: '#E8ECF3', margin: '4px 0 2px' }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span style={{ width: 11, height: 11, borderRadius: 2, background: '#EEF1F6', border: '1px solid #D4DCE8', flexShrink: 0 }} />
        <span style={{ fontSize: 13, color: '#6A7A8A', fontWeight: 500, flex: 1 }}>Unallocated</span>
        <span style={{ fontFamily: "'DM Mono',monospace", fontSize: 12, color: overBudget ? '#8A2020' : '#3A4A5A', fontWeight: 600, textAlign: 'right' }}>
          {fmtCur(Math.max(0, remaining), sym, suffix)}
        </span>
        <span style={{ width: 36 }} />
      </div>
    </div>
  )
}

/* ── Segment effect row (inside strategy option detail) ──────────────────── */
function SegmentEffectRow({ segment, mult }) {
  const delta = (mult - 1) * 100
  const sign  = delta > 0.5 ? 'pos' : delta < -0.5 ? 'neg' : 'flat'
  const fg    = sign === 'pos' ? '#1A6B45' : sign === 'neg' ? '#8A2020' : '#6A7A8A'
  const segLabel = segment.charAt(0).toUpperCase() + segment.slice(1).toLowerCase()
  const formatted = sign === 'flat' ? '0%' : `${delta > 0 ? '+' : ''}${delta.toFixed(0)}%`
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 11 }}>
      <span style={{ color: '#3A4A5A', fontWeight: 500 }}>{segLabel}</span>
      <span style={{
        fontFamily: "'DM Mono',monospace",
        fontWeight: 700, color: fg,
        letterSpacing: '0.02em',
      }}>
        {formatted}
      </span>
    </div>
  )
}

/* ── Strategy options list ──────────────────────────────────────────────── */
export function StrategyOptions({ options, value, onChange, deptColor, compact = false }) {
  const entries = Object.entries(options)
  if (entries.length === 0) return null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: compact ? 3 : 4 }}>
      {entries.map(([key, opt]) => {
        const label = typeof opt === 'string' ? opt : (opt.label || key)
        const mults = (typeof opt === 'object' && opt.segment_multipliers) ? opt.segment_multipliers : {}
        const selected = value === key
        const segs = Object.entries(mults)

        return (
          <button
            key={key}
            onClick={() => onChange(key)}
            type="button"
            className="strategy-option"
            onMouseEnter={e => {
              if (!selected) {
                e.currentTarget.style.borderColor = '#B0BCCC'
                e.currentTarget.style.background = '#F8FAFC'
              }
            }}
            onMouseLeave={e => {
              if (!selected) {
                e.currentTarget.style.borderColor = '#E0E6EF'
                e.currentTarget.style.background = '#FFFFFF'
              }
            }}
            style={{
              border: selected ? `1px solid ${deptColor}` : '1px solid #E0E6EF',
              background: selected ? `${deptColor}0F` : '#FFFFFF',
              boxShadow: selected ? `inset 0 0 0 1px ${deptColor}33` : 'none',
              padding: compact ? '5px 8px' : '8px 10px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{
                width: 12, height: 12, borderRadius: '50%',
                border: `1.5px solid ${selected ? deptColor : '#C8D0DC'}`,
                background: '#FFFFFF',
                flexShrink: 0, position: 'relative',
                transition: 'border-color 0.15s ease',
              }}>
                {selected && (
                  <span style={{
                    position: 'absolute', inset: 2,
                    borderRadius: '50%', background: deptColor,
                  }} />
                )}
              </span>
              <span style={{
                fontSize: compact ? 11 : 12,
                fontWeight: selected ? 700 : 500,
                color: selected ? deptColor : '#0A1628',
                lineHeight: 1.25,
                textAlign: 'left',
                flex: 1,
              }}>
                {label}
              </span>
            </div>

            {compact && selected && segs.length > 0 && (
              <div style={{
                marginTop: 6, paddingTop: 6, paddingLeft: 20,
                borderTop: `1px dashed ${deptColor}40`,
                display: 'flex', flexWrap: 'wrap', gap: 4,
                animation: 'allocFadeUp 0.2s ease both',
              }}>
                {segs.map(([seg, mult]) => {
                  const delta = (mult - 1) * 100
                  const sign  = delta > 0.5 ? 'pos' : delta < -0.5 ? 'neg' : 'flat'
                  const fg    = sign === 'pos' ? '#1A6B45' : sign === 'neg' ? '#8A2020' : '#6A7A8A'
                  const bg    = sign === 'pos' ? 'rgba(26,107,69,.07)' : sign === 'neg' ? 'rgba(138,32,32,.07)' : 'rgba(106,122,138,.07)'
                  const formatted = sign === 'flat' ? '0%' : `${delta > 0 ? '+' : ''}${delta.toFixed(0)}%`
                  const segLabel = seg.charAt(0).toUpperCase() + seg.slice(1).toLowerCase()
                  return (
                    <span key={seg} style={{
                      display: 'inline-flex', alignItems: 'center', gap: 4,
                      padding: '2px 6px',
                      borderRadius: 3,
                      background: bg,
                      fontSize: 10,
                      fontWeight: 600,
                      color: '#3A4A5A',
                      lineHeight: 1.2,
                      whiteSpace: 'nowrap',
                    }}>
                      <span>{segLabel}</span>
                      <span style={{ fontFamily: "'DM Mono',monospace", fontWeight: 700, color: fg }}>{formatted}</span>
                    </span>
                  )
                })}
              </div>
            )}

            {!compact && selected && segs.length > 0 && (
              <div style={{
                marginTop: 8, paddingTop: 8, paddingLeft: 20,
                borderTop: `1px dashed ${deptColor}40`,
                animation: 'allocFadeUp 0.2s ease both',
              }}>
                <div style={{
                  fontFamily: "'DM Mono',monospace",
                  fontSize: 9, fontWeight: 700,
                  color: '#8090A4', letterSpacing: '0.14em',
                  textTransform: 'uppercase',
                  marginBottom: 5,
                }}>
                  Effect on segments
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                  {segs.map(([seg, mult]) => (
                    <SegmentEffectRow key={seg} segment={seg} mult={mult} />
                  ))}
                </div>
              </div>
            )}
          </button>
        )
      })}
    </div>
  )
}

// Native <input type="range"> with onChange throttled to RAF.
export function ThrottledRange({ value, onChange, ...rest }) {
  const pendingRef = useRef(null)
  const rafIdRef   = useRef(null)

  useEffect(() => () => {
    if (rafIdRef.current != null) cancelAnimationFrame(rafIdRef.current)
  }, [])

  const handleChange = (e) => {
    pendingRef.current = Number(e.target.value)
    if (rafIdRef.current != null) return
    rafIdRef.current = requestAnimationFrame(() => {
      rafIdRef.current = null
      const v = pendingRef.current
      pendingRef.current = null
      if (v != null) onChange(v)
    })
  }

  return (
    <input
      type="range"
      value={value}
      onChange={handleChange}
      {...rest}
    />
  )
}

/* ── Hold-to-seal button ──────────────────────────────────────────────── */
export function HoldToSealButton({ disabled, onComplete, label, year }) {
  const [phase, setPhase]   = useState('idle')
  const [whiteText, setWhiteText] = useState(false)

  const fillRef     = useRef(null)
  const progressRef = useRef(0)
  const sealedRef   = useRef(false)
  const rafRef      = useRef(null)
  const startRef    = useRef(0)
  const HOLD_MS     = 1100

  const writeFill = (p) => {
    progressRef.current = p
    if (fillRef.current) {
      fillRef.current.style.width = `${(p * 100).toFixed(2)}%`
    }
    setPhase(prev => {
      if (sealedRef.current) return 'sealed'
      if (p > 0.05) return 'holding'
      return 'idle'
    })
    setWhiteText(p >= 0.55)
  }

  const stop = () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); rafRef.current = null }
  const tick = (t) => {
    if (!startRef.current) startRef.current = t
    const elapsed = t - startRef.current
    const p = Math.min(1, elapsed / HOLD_MS)
    writeFill(p)
    if (p >= 1) {
      sealedRef.current = true
      setPhase('sealed')
      onComplete && onComplete()
      stop()
      return
    }
    rafRef.current = requestAnimationFrame(tick)
  }
  const start = () => {
    if (disabled || sealedRef.current) return
    stop()
    startRef.current = 0
    rafRef.current = requestAnimationFrame(tick)
  }
  const cancel = () => {
    if (sealedRef.current) return
    stop()
    let cur = progressRef.current
    const rewind = () => {
      cur = Math.max(0, cur - 0.06)
      writeFill(cur)
      if (cur > 0) requestAnimationFrame(rewind)
    }
    requestAnimationFrame(rewind)
  }

  // Reset hook — used by the Practice Round's Reset button.
  useEffect(() => () => stop(), [])

  const sealed   = phase === 'sealed'
  const idleOpacity = disabled && !sealed ? 0.4 : 1
  const HEIGHT = 44

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      aria-label={label}
      onMouseDown={start}
      onMouseUp={cancel}
      onMouseLeave={cancel}
      onTouchStart={start}
      onTouchEnd={cancel}
      onKeyDown={e => { if ((e.key === ' ' || e.key === 'Enter') && !e.repeat) { e.preventDefault(); start() } }}
      onKeyUp={e => { if (e.key === ' ' || e.key === 'Enter') { e.preventDefault(); cancel() } }}
      style={{
        position: 'relative',
        display: 'block',
        width: '100%',
        height: `${HEIGHT}px`,
        borderRadius: 4,
        border: `1px solid ${sealed ? '#B8932A' : '#C8D0DC'}`,
        cursor: disabled && !sealed ? 'not-allowed' : sealed ? 'default' : 'pointer',
        userSelect: 'none',
        WebkitUserSelect: 'none',
        fontFamily: "'DM Sans', sans-serif",
        outline: 'none',
        opacity: idleOpacity,
        overflow: 'hidden',
        boxSizing: 'border-box',
        background: '#F0F2F5',
      }}
    >
      <div
        ref={fillRef}
        style={{
          position: 'absolute',
          top: 0, left: 0, bottom: 0,
          width: '0%', height: '100%',
          background: 'linear-gradient(90deg, #B8932A 0%, #D4AA40 50%, #B8932A 100%)',
          boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.12)',
          pointerEvents: 'none',
        }}
      />

      <div
        style={{
          position: 'absolute',
          top: 0, left: 0, right: 0, bottom: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
          fontSize: 12, fontWeight: 700,
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
          color: whiteText ? '#FFFFFF' : '#0A1628',
          transition: 'color 0.2s ease',
          pointerEvents: 'none',
        }}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
          <rect x="5" y="11" width="14" height="11" rx="2" stroke="currentColor" strokeWidth="1.6" />
          <path d="M8 11V7a4 4 0 018 0v4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
          <circle cx="12" cy="16" r="1.5" fill="currentColor" />
        </svg>
        <span>
          {sealed ? `Year ${year} Sealed` : phase === 'holding' ? 'Hold to Seal…' : label}
        </span>
      </div>
    </div>
  )
}

/* ── Numeric input ─────────────────────────────────────────────────────── */
export function DeptInput({ val, div, deptCfg, suffix, min, max, onChange, sym }) {
  const [text, setText] = useState(String(Math.round(val / div)))
  const focused = useRef(false)
  useEffect(() => { if (!focused.current) setText(String(Math.round(val / div))) }, [val, div])
  const commit = (raw) => {
    const trimmed = raw.trim(); if (trimmed === '') return
    const n = Number(trimmed); if (isNaN(n)) { setText(String(Math.round(val / div))); return }
    const clamped = Math.max(min, Math.min(max, Math.round(n) * div))
    onChange(clamped); setText(String(Math.round(clamped / div)))
  }
  return (
    <div style={{ display: 'inline-flex', alignItems: 'baseline', gap: 4, fontFamily: "'DM Mono',monospace" }}>
      <span style={{ fontSize: 12, color: '#8090A4', fontWeight: 600 }}>{sym}</span>
      <input
        type="text" inputMode="numeric" value={text}
        onChange={e => setText(e.target.value)}
        onFocus={() => { focused.current = true }}
        onBlur={e => { focused.current = false; commit(e.target.value) }}
        onKeyDown={e => {
          if (e.key === 'Enter') e.target.blur()
          if (e.key === 'ArrowUp') { e.preventDefault(); const n = String(Number(text) + 1); setText(n); commit(n) }
          if (e.key === 'ArrowDown') { e.preventDefault(); const n = String(Number(text) - 1); setText(n); commit(n) }
        }}
        style={{
          width: 64, padding: '3px 6px',
          fontFamily: "'DM Mono',monospace",
          fontSize: 16, fontWeight: 700,
          color: deptCfg.colorL,
          background: 'transparent',
          border: '1px solid transparent',
          borderBottom: `1px solid ${deptCfg.bdr}`,
          borderRadius: 0,
          outline: 'none',
          textAlign: 'right',
        }}
        onFocusCapture={e => { e.currentTarget.style.background = deptCfg.bgInput }}
        onBlurCapture={e => { e.currentTarget.style.background = 'transparent' }}
      />
      <span style={{ fontSize: 11, color: '#8090A4', fontWeight: 600 }}>{suffix}</span>
    </div>
  )
}

/* ── Shared styles (mounted once per page that uses these primitives) ─── */
export function AllocateSharedStyles() {
  return (
    <style>{`
      @keyframes allocFadeUp { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
      @keyframes allocFadeIn { from { opacity: 0; } to { opacity: 1; } }
      @keyframes allocSlideUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

      .alloc-card { background: #FFFFFF; border: 1px solid #D4DCE8; border-radius: 4px; box-shadow: 0 1px 3px rgba(10,22,40,0.04); }
      .alloc-card-emphasis { box-shadow: 0 2px 8px rgba(10,22,40,0.06); }

      .alloc-section-label { font-family: 'DM Mono', monospace; font-size: 9px; font-weight: 700; color: #8090A4; text-transform: uppercase; letter-spacing: 0.16em; margin-bottom: 10px; }

      .dept-card { animation: allocFadeUp 0.28s ease both; }
      .dept-card:nth-child(2) { animation-delay: 0.04s; }
      .dept-card:nth-child(3) { animation-delay: 0.08s; }
      .dept-card:nth-child(4) { animation-delay: 0.12s; }

      .alloc-slider { -webkit-appearance: none; appearance: none; width: 100%; height: 4px; background: #E8ECF3; border-radius: 2px; outline: none; }
      .alloc-slider::-webkit-slider-thumb { -webkit-appearance: none; appearance: none; width: 14px; height: 14px; border-radius: 50%; background: var(--dept-color); border: 2px solid #FFFFFF; box-shadow: 0 0 0 1px var(--dept-color), 0 1px 3px rgba(10,22,40,0.18); cursor: pointer; transition: transform 0.12s ease; }
      .alloc-slider::-webkit-slider-thumb:hover { transform: scale(1.15); }
      .alloc-slider::-moz-range-thumb { width: 14px; height: 14px; border-radius: 50%; background: var(--dept-color); border: 2px solid #FFFFFF; box-shadow: 0 0 0 1px var(--dept-color), 0 1px 3px rgba(10,22,40,0.18); cursor: pointer; }

      .strategy-option {
        width: 100%;
        padding: 8px 10px;
        border-radius: 4px;
        cursor: pointer;
        font-family: 'DM Sans', sans-serif;
        text-align: left;
        outline: none;
        transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
      }
      .strategy-option:focus-visible { box-shadow: 0 0 0 2px rgba(184,147,42,0.30); }
    `}</style>
  )
}

// Department card (the unit composed in both AllocateTab and Practice) This is the visual atom of an
// allocation surface: name, percent, amount input, slider with min/max markers.
export function DepartmentCard({
  constraint,                 // { dept_name, min, max, step, default }
  subDecisionOptions,         // { label, options: { key: SubDecisionOption } }
  value, onValueChange,       // current slider value, change handler
  strategyValue, onStrategyChange,
  totalSpend,                 // for the "share %" readout
  sym, suffix, div,
  readOnly = false,
  compact = false,            // tighter spacing for the Practice Round
}) {
  const dc = getDept(constraint.dept_name)
  const sdOptions = subDecisionOptions?.options || {}
  const sliderPct = ((value - constraint.min) / (constraint.max - constraint.min)) * 100

  // Compact mode reduces padding/margins by roughly a third and switches the strategy list to a
  // non-expanding variant.
  const pad   = compact ? '10px 10px 8px' : '14px 14px 12px'
  const gap   = compact ? 6 : 10
  const lblFs = compact ? 11 : 12

  return (
    <div
      className="alloc-card dept-card"
      style={{
        padding: pad,
        borderTop: `2px solid ${dc.color}`,
        display: 'flex', flexDirection: 'column', gap,
      }}
    >
      {/* Header: dept name + share % */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <span style={{ fontSize: lblFs, fontWeight: 700, color: dc.colorL, letterSpacing: '0.02em' }}>
          {constraint.dept_name}
        </span>
        {totalSpend > 0 && (
          <span style={{ fontFamily: "'DM Mono',monospace", fontSize: 10, color: '#8090A4', fontWeight: 600 }}>
            {((value / totalSpend) * 100).toFixed(0)}%
          </span>
        )}
      </div>

      {/* Amount */}
      {readOnly ? (
        <div style={{ fontFamily: "'DM Mono',monospace", fontSize: compact ? 14 : 16, fontWeight: 700, color: dc.colorL }}>
          {fmtCur(value, sym, suffix)}
        </div>
      ) : (
        <DeptInput
          val={value} div={div} deptCfg={dc} suffix={suffix}
          sym={sym} min={constraint.min} max={constraint.max}
          onChange={onValueChange}
        />
      )}

      {/* Slider with min/max ticks */}
      {!readOnly && (
        <div>
          <ThrottledRange
            min={constraint.min} max={constraint.max} step={constraint.step || div}
            value={value}
            onChange={onValueChange}
            className="alloc-slider"
            style={{
              '--dept-color': dc.color,
              background: `linear-gradient(to right, ${dc.color} ${sliderPct}%, #E8ECF3 ${sliderPct}%)`,
            }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: '#8090A4', fontFamily: "'DM Mono',monospace", marginTop: 4 }}>
            <span>{fmtCur(constraint.min, sym, suffix)}</span>
            <span>{fmtCur(constraint.max, sym, suffix)}</span>
          </div>
        </div>
      )}

      {/* Strategy picker */}
      {!readOnly && Object.keys(sdOptions).length > 0 && (
        <div>
          <div style={{
            fontSize: 9, fontWeight: 700, color: '#8090A4',
            textTransform: 'uppercase', letterSpacing: '0.14em',
            marginBottom: compact ? 4 : 6, fontFamily: "'DM Mono',monospace",
          }}>
            {subDecisionOptions.label || 'Strategy'}
          </div>
          <StrategyOptions
            options={sdOptions}
            value={strategyValue}
            onChange={onStrategyChange}
            deptColor={dc.color}
            compact={compact}
          />
        </div>
      )}
    </div>
  )
}
