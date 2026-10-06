import React, { useState, useEffect, useCallback, useRef } from 'react'
import { useAuth } from '../App'
import { api } from '../hooks/useApi'
import AllocateTab from '../components/AllocateTab'
import MarketTab from '../components/MarketTab'
import PerformanceTab from '../components/PerformanceTab'
import BriefingTab from '../components/BriefingTab'
import ObjectiveTab from '../components/ObjectiveTab'
import PauseOverlay from '../components/PauseOverlay'
import TimerBadge from '../components/TimerBadge'
import Header, { AuxiLogo } from '../components/Header'
import FinalInsights from '../components/FinalInsights'
import YearTransitionOverlay from '../components/YearTransitionOverlay'
import { fmtCur } from '../components/allocate/shared'
import MuteToggle from '../components/MuteToggle'
import { useToast, ToastContainer } from '../hooks/useToast'
import { useSound } from '../hooks/useSound'
import { Eye } from '@phosphor-icons/react'

const TAB_ORDER = ['briefing','objective','allocate','performance','market']

// Animated VPI count-up
function AnimatedNumber({ value, duration = 1400 }) {
  const [display, setDisplay] = useState(value)
  const prevRef = useRef(value)
  useEffect(() => {
    const from = prevRef.current ?? 0
    const to = value ?? 0
    if (from === to) return
    prevRef.current = to
    const start = Date.now()
    const tick = () => {
      const p = Math.min((Date.now() - start) / duration, 1)
      const ease = 1 - Math.pow(1 - p, 3)
      setDisplay(Math.round(from + (to - from) * ease))
      if (p < 1) requestAnimationFrame(tick)
      else setDisplay(to)
    }
    requestAnimationFrame(tick)
  }, [value, duration])
  return <span>{display != null ? display.toLocaleString() : '—'}</span>
}

export default function GamePage({ onMainPage, scenarioInfoProp, gameStateProp, sliderConstraintsProp, competitorsProp, onGameStateChange, wsData: wsDataProp }) {
  const { auth, logout } = useAuth()
  // wsData from App.jsx persistent WS — no new connection opened here
  const wsData = wsDataProp || {}
  const { connected, timerRemaining, timerPaused, paused, pauseAnnouncement, blocking, lockProgress, setLockProgress, leaderboard: wsLeaderboard, phase: wsPhase, timerExpired, setWasLastLocker } = wsData

  useEffect(() => { if (wsPhase === 'login') logout() }, [wsPhase, logout])

  // Track whether the game was completed during THIS session
  // (don't show completion screen on initial load with cached game state)
  const [justCompleted, setJustCompleted] = useState(false)
  const [showResultsInGame, setShowResultsInGame] = useState(false)
  const prevYearCount = useRef(gameStateProp?.year_results?.length || 0)

  // Detect completion in real-time — only trigger when year_results transitions to 5
  const isGameComplete = justCompleted || wsPhase === 'complete'
  useEffect(() => {
    if (!timerExpired) return
    if (timerExpired.game_state) applyGameState(timerExpired.game_state)
    else loadState()
    const orig = document.title
    document.title = `[Time up] Year ${timerExpired.year} auto-locked`
    const t = setTimeout(() => { document.title = orig }, 5000)
    return () => clearTimeout(t)
  }, [timerExpired])

  const [gameState, setGameState]           = useState(gameStateProp || null)

  // Apply a game_state update MONOTONICALLY by progress = (current_year, then number of year_results).
  const applyGameState = useCallback((next) => {
    if (!next) return
    setGameState(prev => {
      if (!prev) return next
      const nY = next.current_year || 0
      const pY = prev.current_year || 0
      const nR = (next.year_results || []).length
      const pR = (prev.year_results || []).length
      if (nY > pY || (nY === pY && nR >= pR)) return next
      return prev   // stale / out-of-order — ignore so the year can't regress
    })
  }, [])
  // Accepts a plain array or {items, max_allocatable, unallocatable}.
  const _normConstraints = (v) => Array.isArray(v) ? { items: v, max_allocatable: null, unallocatable: 0 } : (v || { items: [], max_allocatable: null, unallocatable: 0 })
  const [sliderConstraints, setSliderConstraints] = useState(_normConstraints(sliderConstraintsProp))
  const [subDecisionOptions, setSubDecisionOptions] = useState({})
  const [leaderboard, setLeaderboard]       = useState([])
  const [scenarioInfo, setScenarioInfo]     = useState(scenarioInfoProp || null)
  const [loading, setLoading]               = useState(!gameStateProp)
  const [localRemaining, setLocalRemaining] = useState(0)

  // Directional tab tracking
  const [activeTab, setActiveTab] = useState('briefing')
  const [tabDir, setTabDir]       = useState('right')
  const prevTabRef = useRef('briefing')

  const switchTab = (id) => {
    const prevIdx = TAB_ORDER.indexOf(prevTabRef.current)
    const nextIdx = TAB_ORDER.indexOf(id)
    setTabDir(nextIdx >= prevIdx ? 'right' : 'left')
    prevTabRef.current = id
    setActiveTab(id)
  }

  useEffect(() => {
    if (!wsData.gameState) return
    applyGameState(wsData.gameState)
    // Reliable year-transition trigger.
    const ny = wsData.gameState.current_year || 0
    // [YT-DIAG] Year-transition diagnostics. Remove this block once the
    // year-on-year animation is confirmed working in the deployed build.
    console.log('[YT] effect run — incoming current_year=%s, shown=%s, transitionYear=%s',
                ny, shownTransitionYear.current, transitionYear)
    if (shownTransitionYear.current == null) {
      shownTransitionYear.current = ny
    } else if (ny > shownTransitionYear.current && ny <= 5) {
      shownTransitionYear.current = ny
      setTransitionYear(ny)
      console.log('[YT] >>> FIRED transition to YEAR', ny)   // [YT-DIAG]
      playYearTransition()
      setWasLastLocker(false)
    }
  }, [wsData.gameState]) // eslint-disable-line
  useEffect(() => { if (wsLeaderboard?.length > 0) setLeaderboard(wsLeaderboard) }, [wsLeaderboard])

  // Detect Y5 lock happening live during this session
  useEffect(() => {
    const count = gameState?.year_results?.length || 0
    if (count >= 5 && prevYearCount.current < 5) {
      setJustCompleted(true)
    }
    prevYearCount.current = count
  }, [gameState?.year_results?.length])
  useEffect(() => { setLocalRemaining(timerRemaining) }, [timerRemaining])
  useEffect(() => {
    const w = gameState?.waiting_for_others || blocking?.length > 0
    if (localRemaining <= 0 || timerPaused || paused || w) return
    const id = setInterval(() => setLocalRemaining(r => Math.max(0, r - 1)), 1000)
    return () => clearInterval(id)
  }, [localRemaining, timerPaused, paused, gameState?.waiting_for_others, blocking])

  const { toast, msg: toastMsg, ok: toastOk } = useToast()
  const { muted: soundMuted, setMuted: setSoundMuted,
          playLockSeal, playTimerWarning, playYearTransition } = useSound()

  // Fires when current_year increments — typically when the barrier completes and all teams advance
  // together.
  const prevYearForTransition = useRef(null)
  const [transitionYear, setTransitionYear] = useState(null)
  // Tracks the highest year we've actually played a transition for.
  const shownTransitionYear = useRef(gameStateProp?.current_year ?? null)
  // Year-transition animation logic: Last locker (wasLastLocker=true): show "ADVANCING TO YEAR N"
  // animation directly.
  useEffect(() => {
    const cur = gameState?.current_year
    if (cur != null) prevYearForTransition.current = cur
  }, [gameState?.current_year])

  // Fires the warning beep exactly once per year, when the timer crosses the 30-second mark going DOWN.
  const prevRemainingRef = useRef(localRemaining)
  const lastWarnedYearRef = useRef(null)
  useEffect(() => {
    const cur = gameState?.current_year
    const prev = prevRemainingRef.current
    if (prev > 30 && localRemaining <= 30 && localRemaining > 0
        && lastWarnedYearRef.current !== cur) {
      playTimerWarning()
      lastWarnedYearRef.current = cur
    }
    prevRemainingRef.current = localRemaining
  }, [localRemaining, gameState?.current_year, playTimerWarning])

  const loadState = useCallback(async () => {
    if (!auth?.team_key) return
    try {
      const data = await api.getGameState(auth.team_key)
      if (data.game_state) {
        applyGameState(data.game_state)
        if (data.slider_constraints) setSliderConstraints(_normConstraints(data.slider_constraints))
        // Note: /api/game-state does NOT return a `leaderboard` field — the leaderboard arrives via the
        // WebSocket `all_teams_locked` message (wsLeaderboard → setLeaderboard useEffect above).
        const p = data.game_state.timer_remaining
        if (p > 0 && localRemaining === 0) setLocalRemaining(p)
      } else { onMainPage() }
    } catch {}
    finally { setLoading(false) }
  }, [auth?.team_key, onMainPage])

  useEffect(() => { loadState() }, [loadState])
  useEffect(() => {
    if (scenarioInfoProp?.sub_decisions) setSubDecisionOptions(scenarioInfoProp.sub_decisions)
    else api.getSubDecisions().then(setSubDecisionOptions).catch(() => {})
    if (!scenarioInfoProp) api.getScenarioInfo().then(setScenarioInfo).catch(() => {})
  }, [])
  useEffect(() => {
    // On year change, re-fetch /api/game-state to get fresh slider_constraints.
    if (gameState?.current_year && auth?.team_key) {
      api.getGameState(auth.team_key).then(data => {
        if (data.slider_constraints) setSliderConstraints(_normConstraints(data.slider_constraints))
      }).catch(() => {})
    }
  }, [gameState?.current_year])

  const isController     = auth?.is_controller
  // Default 'competition' to match all backend code paths (services/game_logic.py, routers/ws_router.py,
  // routers/admin_router.py).
  const mode             = gameState?.mode || 'competition'
  const waitingForOthers = gameState?.waiting_for_others || blocking?.length > 0


  const currentYear      = Math.min(gameState?.current_year || 1, 5)

  // Dashboard hero data
  const yearResults  = gameState?.year_results || []
  const latestResult = yearResults[yearResults.length - 1]
  const latestVpi    = latestResult?.vpi ?? null
  const latestGrade  = latestResult?.grade ?? null
  const latestShare  = latestResult?.market_share ?? null
  const latestProfit = latestResult?.profit ?? null
  const sym          = scenarioInfo?.currency_symbol || '$'
  const suffix       = scenarioInfo?.small_number_suffix || 'K'
  const hasResults   = yearResults.length > 0
  // All five years locked → the progress widget reads "Completed" rather than
  // "Year 5 of 5 · 0 remaining". Mirrors the "5 / 5 LOCKED" header badge.
  const allLocked    = yearResults.length >= 5

  const handleLockYear = async (allocations, subdecisions) => {
    try {
      const res = await api.lockYear(auth.team_key, auth.username, allocations, subdecisions)
      if (res.status === 'ok') {
        if (res.game_state) { applyGameState(res.game_state); onGameStateChange?.(res.game_state) }
        if (res.blocking_total) setLockProgress({ locked: res.locked_count || 0, total: res.blocking_total })
        // Do NOT clear waiting_for_others here even if res.all_teams_locked is true.
        const sealedYear = res.year || (res.game_state?.year_results?.length)
        toast(sealedYear ? `Year ${sealedYear} sealed.` : 'Year sealed.', 'success')
        // Audio cue — silent if user has muted (handled inside the hook).
        playLockSeal()
      } else {
        toast(res.error || 'Lock failed', 'error', 6000)
      }
    } catch (err) {
      toast(err?.message || 'Network error — please retry.', 'error', 6000)
    }
  }

  const completedFromState = yearResults.length >= 5 && !waitingForOthers

  if ((isGameComplete || completedFromState) && !loading && !showResultsInGame) {
    return (
      <div style={{
        minHeight: '100vh', background: '#F0F2F5',
        display: 'flex', flexDirection: 'column',
        position: 'relative', zIndex: 2,
      }}>
        <Header />
        <FinalInsights
          gameState={gameState}
          scenarioInfo={scenarioInfo}
          onContinue={() => { setActiveTab('performance'); setShowResultsInGame(true) }}
          onExit={onMainPage}
        />
      </div>
    )
  }

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', background: '#F0F2F5', display: 'flex', flexDirection: 'column', position: 'relative', zIndex: 2 }}>
        <div style={{ height: 56, background: '#FFFFFF', borderBottom: '1px solid #D4DCE8', padding: '0 28px', display: 'flex', alignItems: 'center', gap: 12 }}>
          {[18,80].map((w,i) => <div key={i} className="skeleton" style={{ width: w, height: 18, borderRadius: i===0?'50%':6 }}/>)}
          <div style={{flex:1}}/>
          {[60,80].map((w,i) => <div key={i} className="skeleton" style={{ width: w, height: 22, borderRadius: 100 }}/>)}
        </div>
        <div style={{ height: 44, background: '#F5F7FA', borderBottom: '1px solid rgba(255,255,255,0.07)', padding: '0 28px', display: 'flex', alignItems: 'center', gap: 24 }}>
          {[80,65,110,85,55].map((w,i) => <div key={i} className="skeleton" style={{ width: w, height: 12 }}/>)}
        </div>
        <div style={{ flex:1, padding:'22px 28px', display:'flex', gap:14 }}>
          <div style={{ width:210, display:'flex', flexDirection:'column', gap:10 }}>
            {[180,140].map((h,i) => <div key={i} className="skeleton" style={{ height:h, borderRadius:12 }}/>)}
          </div>
          <div style={{ flex:1, display:'flex', flexDirection:'column', gap:10 }}>
            {[72,110,110,110,110].map((h,i) => <div key={i} className="skeleton" style={{ height:h, borderRadius:i===0?12:11 }}/>)}
          </div>
        </div>
      </div>
    )
  }

  const tabs = [
    { id:'briefing',    label:'Background' },
    { id:'objective',   label:'Objective' },
    { id:'allocate',    label:'Allocate & Decide' },
    { id:'performance', label:'Performance' },
    { id:'market',      label:'Market' },
  ]

  // GRADE_COL: saturated hues for use on LIGHT surfaces (e.g. the small grade
  // badge, which has white text on a solid color fill).
  const GRADE_COL = { S:'#8A6A10', A:'#1A5C3A', B:'#1A3A6B', C:'#8A6A10', D:'#8A6A10', F:'#8A2020' }
  // GRADE_COL_ON_DARK: brightened versions of the same hues for use as TEXT on the dark-navy KPI cards.
  const GRADE_COL_ON_DARK = { S:'#E8C75A', A:'#5FD699', B:'#7FB4F5', C:'#E8C75A', D:'#E8C75A', F:'#FF6B6B' }

  // Profit text colours, brightened for the dark KPI card.
  const PROFIT_POS_ON_DARK = '#5FD699'  // bright green
  const PROFIT_NEG_ON_DARK = '#FF6B6B'  // bright red

  const centerSlot = (
    <>
      {mode === 'competition' && localRemaining > 0 && (
        <TimerBadge remaining={localRemaining} paused={timerPaused || paused || waitingForOthers} />
      )}
      {/* Year flip animation */}
      <span className="tag tag-navy" style={{ fontFamily:"'DM Mono',monospace", fontSize: 11 }}>
        <span key={yearResults.length} className="year-flip">{yearResults.length}</span>
        <span style={{ opacity: 0.55 }}>&thinsp;/&thinsp;5 locked</span>
      </span>
      <span className="tag tag-b">{mode.charAt(0).toUpperCase() + mode.slice(1)}</span>
      <span style={{ fontSize: 11, color: '#8090A4', fontFamily:"'DM Mono',monospace" }}>
        {isController ? 'Controller' : 'Viewer'} · {auth?.username}
      </span>
      {!connected && <span style={{ fontSize:11, color:'#D4AA40', fontWeight:600 }}>● Reconnecting...</span>}
      <button className="btn btn-g btn-sm" onClick={onMainPage} style={{ display:'flex', alignItems:'center', gap:5 }}>
        <svg width="11" height="11" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>
        Main
      </button>
    </>
  )

  return (
    <div style={{ minHeight:'100vh', background:'#0B1829', display:'flex', flexDirection:'column', position:'relative', zIndex:2 }}>

      <Header
        center={centerSlot}
        right={
          <>
            <MuteToggle muted={soundMuted} onToggle={setSoundMuted} />
            <AuxiLogo />
          </>
        }
      />

      {/* Viewer banner */}
      {!isController && (
        <div style={{ background:'rgba(212,170,64,0.08)', border:'1px solid rgba(212,170,64,0.22)', borderRadius:8, padding:'9px 28px', margin:'10px 28px 0', fontSize:12, color:'#D4AA40', fontWeight:600, textAlign:'center', display:'flex', alignItems:'center', justifyContent:'center', gap:6 }}>
          <Eye size={13} weight="bold" />
          Viewer mode — allocations and strategic directions are set by your team controller.
        </div>
      )}

      {/* ── Dashboard hero bar — shows after Year 1 is locked ── */}
      {hasResults && !waitingForOthers && (
        <div className="game-hero-bar" style={{ padding:'14px 28px 0', flexShrink:0, display:'flex', gap:8, flexWrap:'wrap' }}>
            {/* VPI score */}
            <div className="game-hero-card" style={{ background:'rgba(15,40,75,0.75)', backdropFilter:'blur(24px) saturate(1.6)', WebkitBackdropFilter:'blur(24px) saturate(1.6)', border:'1px solid rgba(212,170,64,0.28)', borderRadius:12, padding:'14px 20px', minWidth:130, position:'relative', overflow:'hidden' }}>
              <div style={{ fontSize:9, color:'rgba(212,170,64,0.70)', textTransform:'uppercase', letterSpacing:'0.18em', fontFamily:"'DM Mono',monospace", marginBottom:4 }}>VPI Score</div>
              <div style={{ fontSize:32, fontWeight:900, fontFamily:"'DM Mono',monospace", lineHeight:1, color: GRADE_COL_ON_DARK[latestGrade] || '#E8C75A' }}>
                <AnimatedNumber value={latestVpi} />
              </div>
              {latestGrade && (
                <div style={{ position:'absolute', top:10, right:12, width:28, height:28, borderRadius:5, background: GRADE_COL[latestGrade] || '#D4AA40', display:'flex', alignItems:'center', justifyContent:'center', fontWeight:800, fontSize:13, color: '#FFFFFF' }}>
                  {latestGrade}
                </div>
              )}
            </div>
            {/* Market share */}
            <div className="game-hero-card" style={{ background:'rgba(15,40,75,0.65)', backdropFilter:'blur(18px)', WebkitBackdropFilter:'blur(18px)', border:'1px solid rgba(255,255,255,0.09)', borderRadius:12, padding:'14px 20px', minWidth:120 }}>
              <div style={{ fontSize:9, color:'rgba(255,255,255,0.55)', textTransform:'uppercase', letterSpacing:'0.18em', fontFamily:"'DM Mono',monospace", marginBottom:4 }}>Market Share</div>
              <div style={{ fontSize:28, fontWeight:900, fontFamily:"'DM Mono',monospace", lineHeight:1, color:'#7FB4F5' }}>
                <AnimatedNumber value={latestShare != null ? Math.round(latestShare * 10) / 10 : null} />{latestShare != null ? '%' : ''}
              </div>
            </div>
            {/* Profit */}
            <div className="game-hero-card" style={{ background:'rgba(15,40,75,0.65)', backdropFilter:'blur(18px)', WebkitBackdropFilter:'blur(18px)', border:'1px solid rgba(255,255,255,0.09)', borderRadius:12, padding:'14px 20px', minWidth:120 }}>
              <div style={{ fontSize:9, color:'rgba(255,255,255,0.55)', textTransform:'uppercase', letterSpacing:'0.18em', fontFamily:"'DM Mono',monospace", marginBottom:4 }}>Net Profit Y{yearResults.length}</div>
              <div style={{ fontSize:28, fontWeight:900, fontFamily:"'DM Mono',monospace", lineHeight:1, color: latestProfit >= 0 ? PROFIT_POS_ON_DARK : PROFIT_NEG_ON_DARK }}>
                {latestProfit != null ? `${latestProfit >= 0 ? '+' : '-'}${fmtCur(Math.abs(latestProfit), sym, suffix)}` : '—'}
              </div>
            </div>
            {/* Spacer then year progress */}
            <div style={{ flex:1 }} />
            <div className="game-hero-progress" style={{ background:'rgba(15,40,75,0.65)', backdropFilter:'blur(18px)', WebkitBackdropFilter:'blur(18px)', border:'1px solid rgba(255,255,255,0.09)', borderRadius:12, padding:'14px 20px', minWidth:160 }}>
              <div style={{ fontSize:9, color:'rgba(255,255,255,0.55)', textTransform:'uppercase', letterSpacing:'0.18em', fontFamily:"'DM Mono',monospace", marginBottom:8 }}>Progress</div>
              <div style={{ display:'flex', gap:5 }}>
                {[1,2,3,4,5].map(y => (
                  <div key={y} style={{ flex:1, height:6, borderRadius:3, background: (allLocked || y < currentYear) ? '#D4AA40' : y === currentYear ? 'rgba(212,170,64,0.35)' : '#E0E6EF', transition:'background 0.4s', position:'relative', overflow:'hidden' }}>
                    {!allLocked && y === currentYear && (
                      <div style={{ position:'absolute', inset:0, background:'linear-gradient(90deg, rgba(212,170,64,0.6), rgba(240,204,96,0.8))', animation:'shimmer 2s linear infinite', backgroundSize:'200% 100%' }} />
                    )}
                  </div>
                ))}
              </div>
              <div style={{ fontSize:10, color:'rgba(255,255,255,0.30)', fontFamily:"'DM Mono',monospace", marginTop:6 }}>{allLocked ? 'Completed' : `Year ${currentYear} of 5 · ${5 - yearResults.length} remaining`}</div>
            </div>
          </div>
      )}

      {/* Tab bar */}
      <div className="game-tabbar" style={{ background:'#FFFFFF', borderBottom:'1px solid #D4DCE8', boxShadow:'0 1px 4px rgba(10,22,40,0.05)', padding:'0 28px', display:'flex', marginTop: (hasResults && !waitingForOthers) ? 12 : (!isController ? 10 : 0) }}>
        {tabs.map(tab => (
          <button key={tab.id} className={`oras-tab${activeTab===tab.id?' active':''}`} onClick={() => switchTab(tab.id)}>{tab.label}</button>
        ))}
      </div>

      {/* Content */}
      <div className="game-content" style={{ flex:1, padding:'20px 28px', overflowY:'auto' }}>
        <div key={activeTab} className={`tab-panel-enter-${tabDir}`}>
          {activeTab==='briefing'    && <BriefingTab gameState={gameState} scenarioInfo={scenarioInfo} />}
          {activeTab==='objective'   && <ObjectiveTab scenarioInfo={scenarioInfo} />}
          {activeTab==='allocate'    && <AllocateTab gameState={gameState} constraints={sliderConstraints.items} maxAllocatable={sliderConstraints.max_allocatable} unallocatableBudget={sliderConstraints.unallocatable || 0} subDecisionOptions={subDecisionOptions} isController={isController} blocking={blocking} onLockYear={handleLockYear} scenarioInfo={scenarioInfo} teamKey={auth?.team_key} username={auth?.username} />}
          {activeTab==='performance' && <PerformanceTab gameState={gameState} scenarioInfo={scenarioInfo} />}
          {activeTab==='market'      && <MarketTab gameState={gameState} scenarioInfo={scenarioInfo} leaderboard={leaderboard} />}
        </div>
      </div>

      {paused && <PauseOverlay announcement={pauseAnnouncement} />}
      {(transitionYear || waitingForOthers) && (
        <YearTransitionOverlay
          key={transitionYear || currentYear}
          year={transitionYear || currentYear}
          persist={waitingForOthers}
          lockProgress={lockProgress}
          onComplete={() => setTransitionYear(null)}
        />
      )}
      <ToastContainer msg={toastMsg} ok={toastOk} />
    </div>
  )
}
