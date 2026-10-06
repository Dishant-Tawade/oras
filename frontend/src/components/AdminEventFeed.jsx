import React, { useState, useEffect, useRef, useCallback } from 'react'
import { adminFetch } from '../hooks/useApi'

const MONO = "'DM Mono', monospace"

// Centralised so adding a new event kind on the backend is one edit here: pick a color + dot color +
// (optional) brief label override.
const KIND_STYLE = {
  year_locked:  { dot: '#1A5C3A', accent: 'rgba(26,92,58,0.08)',   label: 'LOCK' },
  year_complete:{ dot: '#B8932A', accent: 'rgba(184,147,42,0.10)', label: 'YEAR' },
  user_joined:  { dot: '#1A3A6B', accent: 'rgba(26,58,107,0.06)',  label: 'JOIN' },
  user_left:    { dot: '#8090A4', accent: 'rgba(128,144,164,0.06)', label: 'LEAVE' },
  paused:       { dot: '#8A6A10', accent: 'rgba(138,106,16,0.08)', label: 'PAUSE' },
  resumed:      { dot: '#1A5C3A', accent: 'rgba(26,92,58,0.06)',   label: 'RESUME' },
  kicked:       { dot: '#B03030', accent: 'rgba(176,48,48,0.08)',  label: 'KICK' },
  kick_all:     { dot: '#B03030', accent: 'rgba(176,48,48,0.10)',  label: 'KICK ALL' },
  reset:        { dot: '#0A1628', accent: 'rgba(10,22,40,0.08)',   label: 'RESET' },
}
const DEFAULT_STYLE = { dot: '#8090A4', accent: 'rgba(128,144,164,0.06)', label: 'EVENT' }

function fmtTime(ts) {
  try {
    const d = new Date(ts * 1000)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
  } catch { return '' }
}

const POLL_INTERVAL_MS = 5000
const MAX_DISPLAYED = 2000   // keep full session history
const HIGHLIGHT_DURATION_MS = 1500

// Module-level cursor — survives component remounts (StrictMode double-mount, parent re-renders.
let _persistedCursor = 0

export default function AdminEventFeed() {
  const [events, setEvents]       = useState([])
  const [collapsed, setCollapsed] = useState(false)
  const cursorRef                 = useRef(_persistedCursor)
  const newIdsRef                 = useRef(new Set()) // ids that should flash on insert
  const allEventsRef              = useRef([])        // full unbounded history for copy
  const pollRef                   = useRef(null)
  const mountedRef                = useRef(true)
  const [copied, setCopied]       = useState(false)

  const copyLog = useCallback(() => {
    // Use full unbounded history (allEventsRef), oldest-first
    const lines = allEventsRef.current.map(e => {
      const style = KIND_STYLE[e.kind] || DEFAULT_STYLE
      return `[${fmtTime(e.ts)}] ${style.label.padEnd(8)} ${e.text || e.kind}`
    }).join('\n')
    navigator.clipboard.writeText(lines).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }, [events])

  const poll = useCallback(async () => {
    try {
      const res = await adminFetch(`/api/admin/events?since=${cursorRef.current}`)
      const data = await res.json()
      if (!mountedRef.current) return
      const incoming = data.events || []
      if (incoming.length) {
        // Track which IDs are new so we can flash them briefly.
        const flashes = new Set(incoming.map(e => e.id))
        newIdsRef.current = flashes
        // Append to unbounded history ref (used by copy), deduplicating by event ID.
        const existingIds = new Set(allEventsRef.current.map(e => e.id))
        const newOnly = incoming.filter(e => !existingIds.has(e.id))
        if (newOnly.length) {
          allEventsRef.current = [...allEventsRef.current, ...newOnly]
        }
        setEvents(prev => {
          // Prepend newest-first (incoming is oldest-first from server) and trim to MAX_DISPLAYED.
          const merged = [...incoming.slice().reverse(), ...prev]
          const seen = new Set()
          const deduped = []
          for (const e of merged) {
            if (seen.has(e.id)) continue
            seen.add(e.id)
            deduped.push(e)
            if (deduped.length >= MAX_DISPLAYED) break
          }
          return deduped
        })
        // Clear flashes after highlight duration
        setTimeout(() => {
          if (!mountedRef.current) return
          newIdsRef.current = new Set()
          // Force a re-render to drop the highlight class.
          setEvents(prev => prev.slice())
        }, HIGHLIGHT_DURATION_MS)
      }
      // Always advance the cursor, even on empty polls, so subsequent polls don't re-request the same range.
      cursorRef.current = data.latest_id ?? cursorRef.current
      _persistedCursor = cursorRef.current
    } catch (e) {
      // 401 means admin token expired — useApi already cleared the token and threw.
      if (e?.status !== 401) {
        // Network errors during dev are expected (frontend on a different port from backend at startup, etc.).
      }
    }
  }, [])

  useEffect(() => {
    mountedRef.current = true
    poll()                                              // initial backfill
    pollRef.current = setInterval(poll, POLL_INTERVAL_MS)
    return () => {
      mountedRef.current = false
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [poll])

  // Collapsed: a thin tab on the right edge that expands on click.
  if (collapsed) {
    return (
      <div
        onClick={() => setCollapsed(false)}
        title="Show live event feed"
        style={{
          position: 'fixed', right: 0, top: 120,
          background: '#1A3A6B', color: '#FFFFFF', cursor: 'pointer',
          padding: '12px 8px', borderRadius: '4px 0 0 4px',
          fontFamily: MONO, fontSize: 9, letterSpacing: '0.18em',
          writingMode: 'vertical-rl', transform: 'rotate(180deg)',
          fontWeight: 800, zIndex: 50,
          boxShadow: '-2px 0 8px rgba(10,22,40,0.12)',
        }}
      >
        LIVE FEED · {events.length}
      </div>
    )
  }

  return (
    <div
      style={{
        position: 'fixed', right: 14, top: 70, bottom: 14,
        width: 280,
        background: '#FFFFFF', border: '1px solid #D4DCE8',
        borderRadius: 6, boxShadow: '0 4px 16px rgba(10,22,40,0.08)',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
        zIndex: 50,
      }}
    >
      {/* Header */}
      <div style={{
        padding: '10px 14px', borderBottom: '1px solid #E8ECF3',
        background: '#0A1628', color: '#FFFFFF',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{
            width: 6, height: 6, borderRadius: '50%', background: '#1A5C3A',
            boxShadow: '0 0 8px rgba(26,92,58,0.6)',
            animation: 'feedPulse 1.6s ease-in-out infinite',
          }} />
          <span style={{ fontFamily: MONO, fontSize: 10, letterSpacing: '0.18em', fontWeight: 700 }}>
            LIVE FEED
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            onClick={copyLog}
            title="Copy log to clipboard"
            style={{
              background: copied ? 'rgba(26,92,58,0.4)' : 'rgba(255,255,255,0.12)',
              border: 'none', color: copied ? '#7FFFD4' : 'rgba(255,255,255,0.7)',
              cursor: 'pointer', fontSize: 9, padding: '3px 7px', lineHeight: 1,
              borderRadius: 3, fontFamily: MONO, letterSpacing: '0.1em',
              transition: 'all 200ms ease',
            }}
          >{copied ? 'COPIED' : 'COPY'}</button>
          <button
            onClick={() => setCollapsed(true)}
            aria-label="Hide live feed"
            style={{
              background: 'transparent', border: 'none', color: 'rgba(255,255,255,0.7)',
              cursor: 'pointer', fontSize: 14, padding: 2, lineHeight: 1,
            }}
          >×</button>
        </div>
      </div>

      {/* Event list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '4px 0' }}>
        {events.length === 0 && (
          <div style={{
            padding: '24px 14px', color: '#8090A4', fontSize: 11, textAlign: 'center',
            fontStyle: 'italic',
          }}>
            Waiting for activity…
          </div>
        )}
        {events.map((e) => {
          const style = KIND_STYLE[e.kind] || DEFAULT_STYLE
          const isNew = newIdsRef.current.has(e.id)
          return (
            <div
              key={e.id}
              style={{
                padding: '8px 14px',
                borderBottom: '1px solid #F0F2F5',
                background: isNew ? style.accent : 'transparent',
                transition: 'background 600ms ease',
                animation: isNew ? 'feedSlideIn 200ms ease-out' : undefined,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 2 }}>
                <span style={{
                  width: 6, height: 6, borderRadius: '50%', background: style.dot,
                  flexShrink: 0, marginTop: 2,
                }} />
                <span style={{
                  fontFamily: MONO, fontSize: 8, letterSpacing: '0.18em',
                  color: style.dot, fontWeight: 800, flexShrink: 0,
                }}>
                  {style.label}
                </span>
                <span style={{
                  fontFamily: MONO, fontSize: 9, color: '#8090A4',
                  marginLeft: 'auto', flexShrink: 0,
                }}>
                  {fmtTime(e.ts)}
                </span>
              </div>
              <div style={{ fontSize: 12, color: '#3A4A5A', paddingLeft: 14, lineHeight: 1.4 }}>
                {e.text || `(${e.kind})`}
              </div>
            </div>
          )
        })}
      </div>

      <style>{`
        @keyframes feedPulse {
          0%, 100% { opacity: 1; }
          50%      { opacity: 0.4; }
        }
        @keyframes feedSlideIn {
          from { opacity: 0; transform: translateY(-4px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}
