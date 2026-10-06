import React from 'react'

export function OrasMark({ size = 18 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" style={{ flexShrink: 0 }}>
      <path d="M16 3L29 16L16 29L3 16Z" stroke="rgba(255,255,255,0.50)" strokeWidth="1.5" fill="none"/>
      <path d="M16 3L16 29" stroke="rgba(255,255,255,0.18)" strokeWidth="1"/>
      <path d="M3 16L29 16" stroke="rgba(255,255,255,0.18)" strokeWidth="1"/>
      <circle cx="16" cy="16" r="2.5" fill="white"/>
      <circle cx="16" cy="3"  r="2" fill="#D4AA40"/>
      <circle cx="29" cy="16" r="2" fill="#D4AA40"/>
      <circle cx="16" cy="29" r="2" fill="#D4AA40"/>
      <circle cx="3"  cy="16" r="2" fill="#D4AA40"/>
    </svg>
  )
}

export function AuxiLogo() {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:7, opacity:0.70, transition:'opacity 0.2s', cursor:'default' }}
      onMouseEnter={e => e.currentTarget.style.opacity='1'}
      onMouseLeave={e => e.currentTarget.style.opacity='0.70'}>
      <img src="/auxi-logo.png" alt="Auxi Studios" style={{ height:22, filter:'invert(1) brightness(1.2)' }} />
      <div style={{ display:'flex', flexDirection:'column' }}>
        <span style={{ fontSize:12, fontWeight:800, letterSpacing:'0.2em', color:'rgba(255,255,255,0.95)', lineHeight:1.2 }}>AUXI</span>
        <span style={{ fontSize:7.5, letterSpacing:'0.3em', color:'rgba(255,255,255,0.55)' }}>STUDIOS</span>
      </div>
    </div>
  )
}

export default function Header({ left, center, right }) {
  return (
    <div className="oras-header" style={{ position:'relative', zIndex:10 }}>
      <div style={{ display:'flex', alignItems:'center', gap:10 }}>
        {left || (
          <>
            <OrasMark size={22} />
            <div style={{ width:1, height:28, background:'rgba(255,255,255,0.18)', margin:'0 6px' }} />
            <div>
              <div style={{ fontSize:20, fontWeight:900, letterSpacing:'0.20em', color:'rgba(255,255,255,0.98)', lineHeight:1 }}>ORAS</div>
              <div style={{ fontSize:10, color:'rgba(255,255,255,0.55)', letterSpacing:'0.12em', fontFamily:"'DM Mono',monospace", textTransform:'uppercase', marginTop:2 }}>Resource Allocation Simulator</div>
            </div>
          </>
        )}
      </div>
      <div style={{ display:'flex', alignItems:'center', gap:9 }}>{center}</div>
      <div style={{ display:'flex', alignItems:'center', gap:12 }}>{right || <AuxiLogo />}</div>
    </div>
  )
}
