import React from 'react'

export default function PauseOverlay({ announcement }) {
  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(10,22,40,0.50)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 99999,
      backdropFilter: 'blur(6px)', WebkitBackdropFilter: 'blur(6px)',
    }}>
      <div style={{
        background: '#FFFFFF',
        
        border: '2px solid rgba(61,153,88,0.35)',
        borderRadius: 4, padding: '36px 32px',
        maxWidth: 440, width: '90%', textAlign: 'center',
        boxShadow: '0 12px 48px rgba(0,0,0,0.5)',
      }}>
        <div style={{ marginBottom: 14, display: 'flex', justifyContent: 'center' }}>
          <div style={{
            width: 48, height: 48, borderRadius: '50%',
            background: '#EAF4EE', border: '1px solid rgba(26,107,69,0.22)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <rect x="6" y="4" width="4" height="16" rx="1.5" fill="rgba(91,191,116,0.7)"/>
              <rect x="14" y="4" width="4" height="16" rx="1.5" fill="rgba(91,191,116,0.7)"/>
            </svg>
          </div>
        </div>
        <div style={{ fontSize: 18, fontWeight: 700, color: '#0A1628', marginBottom: 8 }}>
          Admin Announcement
        </div>
        <div style={{ fontSize: 13, color: '#3A4A5A', lineHeight: '1.7' }}>
          The simulation has been paused by your instructor. Please wait — the session will resume shortly.
        </div>
        {announcement && (
          <div style={{
            marginTop: 14, padding: '12px 16px',
            background: '#EAF0FA', border: '1px solid #B0C4E0',
            borderRadius: 4, fontSize: 13, color: '#1A3A6B', fontWeight: 600,
          }}>
            {announcement}
          </div>
        )}
      </div>
    </div>
  )
}
