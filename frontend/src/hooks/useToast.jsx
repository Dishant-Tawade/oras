// hooks/useToast.js — small toast notification hook.

import { useState, useCallback, useRef, useEffect } from 'react'

const DEFAULT_DURATION_MS = 4000

// useToast — returns: toast(text, kind='success', durationMs?) — call to show a toast msg, ok —
// current toast state (pass to ToastContainer) `kind` is 'success' | 'error' | 'info'.
export function useToast(defaultDuration = DEFAULT_DURATION_MS) {
  const [msg, setMsg] = useState('')
  const [ok, setOk]   = useState(true)
  const timerRef = useRef(null)

  // Clear any pending timer when the component unmounts.
  useEffect(() => () => { if (timerRef.current) clearTimeout(timerRef.current) }, [])

  const toast = useCallback((text, kind = 'success', durationMs) => {
    if (timerRef.current) clearTimeout(timerRef.current)
    setMsg(text || '')
    setOk(kind !== 'error')
    if (text) {
      timerRef.current = setTimeout(
        () => { setMsg(''); timerRef.current = null },
        durationMs ?? defaultDuration,
      )
    }
  }, [defaultDuration])

  return { toast, msg, ok }
}

// ToastContainer — render this once per page that uses useToast.
export function ToastContainer({ msg, ok }) {
  if (!msg) return null
  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        position: 'fixed',
        bottom: 24,
        left: '50%',
        transform: 'translateX(-50%)',
        background: ok ? '#1A5C3A' : '#B03030',
        color: 'white',
        padding: '12px 28px',
        borderRadius: 4,
        fontSize: 13,
        fontWeight: 600,
        zIndex: 10000,
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        boxShadow: '0 4px 16px rgba(0,0,0,0.18)',
        // Subtle entrance — no library needed
        animation: 'toastIn 180ms ease-out',
      }}
    >
      {msg}
      <style>{`
        @keyframes toastIn {
          from { opacity: 0; transform: translate(-50%, 8px); }
          to   { opacity: 1; transform: translate(-50%, 0); }
        }
      `}</style>
    </div>
  )
}
