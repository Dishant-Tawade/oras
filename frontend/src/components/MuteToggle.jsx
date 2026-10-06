import React from 'react'

// MuteToggle — small icon button for the dark-header right slot.
export default function MuteToggle({ muted, onToggle }) {
  const baseColor = muted ? '#FF8A8A' : 'rgba(255,255,255,0.85)'
  const baseBg    = muted
    ? 'rgba(255,80,80,0.12)'
    : 'rgba(255,255,255,0.06)'
  const hoverBg   = muted
    ? 'rgba(255,80,80,0.20)'
    : 'rgba(255,255,255,0.14)'

  return (
    <button
      type="button"
      aria-label={muted ? 'Unmute sounds' : 'Mute sounds'}
      title={muted ? 'Sounds off — click to enable' : 'Sounds on — click to mute'}
      onClick={() => onToggle(!muted)}
      onMouseEnter={e => { e.currentTarget.style.background = hoverBg }}
      onMouseLeave={e => { e.currentTarget.style.background = baseBg }}
      onMouseDown ={e => { e.currentTarget.style.transform  = 'scale(0.94)' }}
      onMouseUp   ={e => { e.currentTarget.style.transform  = 'scale(1)'    }}
      style={{
        // Pill button, header-height. 30px keeps it sitting inside the
        // header's vertical rhythm without dominating the brand mark.
        width: 30, height: 30,
        borderRadius: 8,
        background: baseBg,
        border: `1px solid ${muted ? 'rgba(255,120,120,0.45)' : 'rgba(255,255,255,0.18)'}`,
        color: baseColor,
        cursor: 'pointer',
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        padding: 0,
        // Quick visual feedback on hover/click — same easing as the Auxi-logo opacity transition next door, so
        // the two feel like siblings rather than dissonant elements.
        transition: 'background 200ms, border-color 200ms, transform 100ms',
      }}
    >
      {muted ? (
        // Speaker with X — muted
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M11 5L6 9H2v6h4l5 4V5z" stroke="currentColor" strokeWidth="1.8"
                strokeLinejoin="round" fill="currentColor" fillOpacity="0.18"/>
          <line x1="17" y1="9"  x2="22" y2="14" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round"/>
          <line x1="22" y1="9"  x2="17" y2="14" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round"/>
        </svg>
      ) : (
        // Speaker with sound waves — unmuted
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path d="M11 5L6 9H2v6h4l5 4V5z" stroke="currentColor" strokeWidth="1.8"
                strokeLinejoin="round" fill="currentColor" fillOpacity="0.18"/>
          <path d="M15.5 8.5a5 5 0 010 7" stroke="currentColor" strokeWidth="1.8"
                strokeLinecap="round" fill="none"/>
          <path d="M19 5a9 9 0 010 14" stroke="currentColor" strokeWidth="1.8"
                strokeLinecap="round" fill="none"/>
        </svg>
      )}
    </button>
  )
}
