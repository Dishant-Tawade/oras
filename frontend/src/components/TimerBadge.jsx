import React from 'react'

export default function TimerBadge({ remaining, paused }) {
  const rem = remaining ?? 0
  const minutes = Math.floor(rem / 60)
  const seconds = rem % 60
  const display = `${minutes}:${seconds.toString().padStart(2, '0')}`
  const isExpired = rem <= 0
  const isLow     = rem > 0 && rem <= 120
  const isWarning = rem > 120 && rem <= 300

  let bg, color, bdr, pulse
  if (isExpired) {
    bg='#FAEBEB'; bdr='#E0B0B0'; color='#8A2020'; pulse=false
  } else if (isLow) {
    bg='#FAEBEB'; bdr='#E0B0B0'; color='#8A2020'; pulse=true
  } else if (isWarning) {
    bg='#FBF5E6'; bdr='#E8D090'; color='#8A6A10'; pulse=false
  } else if (paused) {
    bg='#FBF5E6'; bdr='#E8D090'; color='#8A6A10'; pulse=false
  } else {
    bg='#EAF0FA'; bdr='#B0C4E0'; color='#1A3A6B'; pulse=false
  }

  return (
    <div style={{ display:'flex', alignItems:'center', gap:7, padding:'5px 12px', borderRadius:3, background:bg, border:`1px solid ${bdr}`, fontFamily:"'DM Mono',monospace", fontSize:13, fontWeight:600, color, animation: pulse ? 'timerPulse 1s infinite' : 'none', transition:'background 0.4s,border-color 0.4s,color 0.4s' }}>
      <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="9" r="6" stroke="currentColor" strokeWidth="1.4"/>
        <path d="M8 6v3l2 1.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
        <path d="M6 2h4" stroke="currentColor" strokeOpacity="0.4" strokeWidth="1.2" strokeLinecap="round"/>
      </svg>
      <span>{isExpired ? 'TIME UP' : display}</span>
      {isWarning && !paused && <span style={{ fontSize:9, color:'#A0AABA' }}>LOW</span>}
      {paused && !isExpired && <span style={{ fontSize:9, color:'#A0AABA' }}>PAUSED</span>}
    </div>
  )
}
