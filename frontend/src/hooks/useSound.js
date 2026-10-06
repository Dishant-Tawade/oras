// hooks/useSound.js — Audio cues for game events.

import { useCallback, useEffect, useRef, useState } from 'react'

const MUTE_KEY = 'oras_sound_muted'

// Module-level AudioContext — lazily created on first play.
let _ctx = null
function getCtx() {
  if (_ctx) return _ctx
  try {
    const Ctx = window.AudioContext || window.webkitAudioContext
    if (!Ctx) return null
    _ctx = new Ctx()
    return _ctx
  } catch {
    return null
  }
}

// Helper: schedule a single sine-wave tone with an exponential decay envelope, returning the time the
// tone ends (so callers can chain).
function playTone(ctx, when, freq, duration, peakGain = 0.18) {
  const osc = ctx.createOscillator()
  const gain = ctx.createGain()
  osc.type = 'sine'
  osc.frequency.value = freq

  // Attack: 8 ms ramp up so we don't get a click on the leading edge.
  gain.gain.setValueAtTime(0.0001, when)
  gain.gain.exponentialRampToValueAtTime(peakGain, when + 0.008)
  // Decay: exponential fade to near zero by the end of the duration.
  gain.gain.exponentialRampToValueAtTime(0.0001, when + duration)

  osc.connect(gain)
  gain.connect(ctx.destination)
  osc.start(when)
  osc.stop(when + duration + 0.02)
  return when + duration
}

// Frequencies chosen as a coherent tonal palette: Lock seal: E5 (659 Hz) + A5 (880 Hz) — a fifth
// interval, satisfying "completion" feel.

function actuallyPlay(playFn) {
  const ctx = getCtx()
  if (!ctx) return
  // Resume context if it was suspended (Chrome's autoplay policy suspends the context until a user
  // gesture; we resume on every play since we don't have a separate "user has interacted" signal).
  if (ctx.state === 'suspended') {
    ctx.resume().catch(() => {})
  }
  try {
    playFn(ctx)
  } catch {
    // Synthesis can fail in obscure ways (audio device disconnected, browser memory pressure).
  }
}

function _doLockSeal(ctx) {
  const t = ctx.currentTime
  playTone(ctx, t,         659, 0.18, 0.16) // E5
  playTone(ctx, t + 0.10,  880, 0.30, 0.18) // A5
}

function _doTimerWarning(ctx) {
  const t = ctx.currentTime
  playTone(ctx, t,         440, 0.12, 0.20) // A4 — quick beep
  playTone(ctx, t + 0.18,  440, 0.12, 0.20) // A4 — second beep (double-beep is more recognizable)
}

function _doYearTransition(ctx) {
  const t = ctx.currentTime
  playTone(ctx, t,         262, 0.30, 0.14) // C4
  playTone(ctx, t + 0.18,  523, 0.50, 0.18) // C5
}

// Returns {muted, setMuted, play*}.

export function useSound() {
  const [muted, setMutedState] = useState(() => {
    try { return localStorage.getItem(MUTE_KEY) === '1' } catch { return false }
  })
  // Keep a ref to the latest `muted` value so the play callbacks can read it without listing `muted` as
  // a dep (which would invalidate them every toggle).
  const mutedRef = useRef(muted)
  useEffect(() => { mutedRef.current = muted }, [muted])

  const setMuted = useCallback((next) => {
    setMutedState(next)
    try { localStorage.setItem(MUTE_KEY, next ? '1' : '0') } catch {}
  }, [])

  const playLockSeal       = useCallback(() => { if (!mutedRef.current) actuallyPlay(_doLockSeal)       }, [])
  const playTimerWarning   = useCallback(() => { if (!mutedRef.current) actuallyPlay(_doTimerWarning)   }, [])
  const playYearTransition = useCallback(() => { if (!mutedRef.current) actuallyPlay(_doYearTransition) }, [])

  return { muted, setMuted, playLockSeal, playTimerWarning, playYearTransition }
}
