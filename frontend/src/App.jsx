import React, { createContext, useContext, useState, useCallback, useEffect } from 'react'
import { api, setAdminToken } from './hooks/useApi'
import { useGameSocket } from './hooks/useGameSocket'
import WelcomePage from './pages/WelcomePage'
import LoginPage from './pages/LoginPage'
import LandingPage from './pages/LandingPage'
import StoryboardPage from './pages/StoryboardPage'
import GamePage from './pages/GamePage'
import AdminPage from './pages/AdminPage'

const AuthContext = createContext(null)
export function useAuth() { return useContext(AuthContext) }

// Storage helpers
function storageGet(key) {
  try { return sessionStorage.getItem(key) } catch { return null }
}
function storageSet(key, val) {
  try { if (val == null) sessionStorage.removeItem(key); else sessionStorage.setItem(key, val) } catch {}
}
function loadSavedAuth() {
  try { const r = storageGet('oras_auth'); return r ? JSON.parse(r) : null } catch { return null }
}
function saveAuth(auth) {
  storageSet('oras_auth', auth ? JSON.stringify(auth) : null)
}
function markStoryboardSeen(auth) {
  if (!auth) return
  fetch('/api/storyboard-seen', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: auth.username, team_key: auth.team_key }),
  }).catch(() => {})
}

// Compute initial phase synchronously
function computeInitialPhase(auth) {
  if (!auth) return 'welcome'
  if (auth.is_admin) return 'admin'
  return 'landing'
}

export default function App() {
  const savedAuth = loadSavedAuth()
  const [auth, setAuthState] = useState(savedAuth)
  const [phase, setPhase] = useState(() => computeInitialPhase(savedAuth))
  const [scenarioInfo, setScenarioInfo] = useState(null)
  const [gameState, setGameState] = useState(null)
  const [sliderConstraints, setSliderConstraints] = useState([])
  const [competitors, setCompetitors] = useState([])
  const [gameActive, setGameActive] = useState(false) // true once user has a live game state
  // Whether THIS user has finished the storyboard for the current run. Seeded
  // from the (possibly stale) login snapshot, then corrected from the server on
  // mount and kept in sync on begin/login. Drives Start-vs-Resume on reload and
  // the "Re-read Briefing" affordance. Must come from the server because the
  // login-time value is never updated locally and a reset clears it.
  const [briefingRead, setBriefingRead] = useState(!!savedAuth?.storyboard_seen)

  const setAuth = useCallback((a) => {
    setAuthState(a)
    saveAuth(a)
  }, [])

  // On mount with saved auth: verify session + restore bundled data + correct phase
  useEffect(() => {
    if (!auth || auth.is_admin) return
    api.getGameState(auth.team_key, auth.username)
      .then(data => {
        if (!data?.game_state) {
          // Game was reset — go to landing. storyboard_seen was cleared
          // server-side by the reset, so the user correctly sees START again.
          setBriefingRead(false)
          setPhase('landing')
          setGameActive(false)
        } else {
          if (data.game_state) setGameState(data.game_state)
          if (data.slider_constraints) setSliderConstraints(data.slider_constraints)
          if (data.competitors) setCompetitors(data.competitors)
          // Decide Start-vs-Resume.
          const gs = data.game_state
          const hasProgress = !!(gs && (
            (Array.isArray(gs.locked_allocations) && gs.locked_allocations.length > 0) ||
            (typeof gs.current_year === 'number' && gs.current_year > 1) ||
            gs.waiting_for_others ||
            gs.simulation_begun ||
            (Array.isArray(gs.year_results) && gs.year_results.length > 0)
          ))
          const seen = !!data.storyboard_seen || hasProgress
          setBriefingRead(seen)
          setGameActive(seen)
          // Always go to landing — user clicks START or Resume from there
          setPhase('landing')
          // Re-verify controller role from server — sessionStorage may be stale
          return api.myRole(auth.team_key, auth.username)
            .then(roleData => {
              if (roleData?.is_controller !== auth.is_controller) {
                const corrected = { ...auth, is_controller: roleData.is_controller }
                setAuth(corrected)
              }
            })
            .catch(() => {})
        }
      })
      .catch(() => {})
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Load scenario info on mount (fallback for page refresh — login provides it directly)
  useEffect(() => {
    if (auth && !auth.is_admin && !scenarioInfo) {
      api.getScenarioInfo().then(setScenarioInfo).catch(() => {})
    }
  }, [auth])

  // One WS connection is opened on login and kept alive through all page transitions (landing →
  // storyboard → game).
  const wsData = useGameSocket(
    auth && !auth.is_admin ? auth.team_key : null,
    auth?.username,
    auth?.is_controller
  )
  const { phase: wsPhase, sbRemaining, sbExpired, simulationBegun } = wsData

  // Route terminal WS messages to App-level state changes
  useEffect(() => {
    if (!wsPhase) return
    // An admin has no game WebSocket of its own (useGameSocket is passed a null teamKey for admins).
    if (auth?.is_admin) return
    if (wsPhase === 'login') {
      // game_reset or kicked received
      setAuth(null)
      setGameActive(false)
      setPhase('login')
    }
  }, [wsPhase]) // eslint-disable-line react-hooks/exhaustive-deps

  // NOTE: A `pagehide` + navigator.sendBeacon('/api/logout', ...) handler would make tab-close detection
  // instant by removing the dependency on the server noticing a dropped TCP connection.

  // Handlers
  const handleLogin = useCallback((authData) => {
    setAuth(authData)
    // Store the admin token (if any) so subsequent /api/admin/* calls can present it via the X-Admin-Token
    // header.
    if (authData.is_admin && authData.admin_token) {
      setAdminToken(authData.admin_token)
    }
    // Store bundled data from login response — no follow-up API calls needed
    if (authData.scenario_info) setScenarioInfo(authData.scenario_info)
    if (authData.game_state)    setGameState(authData.game_state)
    if (authData.slider_constraints) setSliderConstraints(authData.slider_constraints)
    if (authData.competitors)   setCompetitors(authData.competitors)
    // Resume (vs Start) if the storyboard is marked seen OR there is real game progress — locking,
    // advancing past year 1, having begun.
    const lgs = authData.game_state
    const lhasProgress = !!(lgs && (
      (Array.isArray(lgs.locked_allocations) && lgs.locked_allocations.length > 0) ||
      (typeof lgs.current_year === 'number' && lgs.current_year > 1) ||
      lgs.waiting_for_others ||
      lgs.simulation_begun ||
      (Array.isArray(lgs.year_results) && lgs.year_results.length > 0)
    ))
    const lseen = (authData.phase === 'playing' && !!authData.storyboard_seen) || lhasProgress
    setBriefingRead(lseen)
    setGameActive(lseen)
    if (authData.is_admin) {
      setPhase('admin')
      return
    }
    if (authData.phase === 'start') {
      setPhase('landing')
      return
    }
    // Always go to landing — user clicks START (unseen) or Resume (seen) from there
    setPhase('landing')
  }, [setAuth])

  const handleStart = useCallback(() => setPhase('storyboard'), [])

  // "Resume" from landing page — go straight to game background tab
  const handleResume = useCallback(() => setPhase('playing'), [])

  // Called when user clicks "Begin Simulation" in storyboard
  const handleBeginSimulation = useCallback((currentAuth) => {
    markStoryboardSeen(currentAuth || auth)
    setGameActive(true)
    setPhase('playing')
  }, [auth])

  const handleLogout = useCallback(async () => {
    if (auth) {
      // Do NOT clear the storyboard flag on logout — the briefing content
      // doesn't change between sessions. It is only cleared on game reset.
      try { await api.logout(auth.username, auth.team_key) } catch {}
    }
    // Clear admin token (if any) — must happen even if api.logout failed,
    // so a stale token can't be replayed from sessionStorage on next mount.
    setAdminToken('')
    setAuth(null)
    setScenarioInfo(null)
    setGameState(null)
    setSliderConstraints([])
    setCompetitors([])
    setGameActive(false)
    setPhase('welcome')
  }, [auth, setAuth])

  // "← Main Page" from GamePage — go back to landing (don't log out)
  const handleMainPage = useCallback(() => setPhase('landing'), [])

  return (
    <AuthContext.Provider value={{ auth, setAuth, phase, setPhase, logout: handleLogout }}>
      <div style={{ minHeight: '100vh', position: 'relative', zIndex: 2, background: '#F0F2F5' }}>

        {phase === 'welcome'    && <WelcomePage onEnter={() => setPhase('login')} />}
        {phase === 'login'      && <LoginPage onLogin={handleLogin} />}
        {phase === 'landing'    && <LandingPage onStart={handleStart} onResume={handleResume} gameActive={gameActive} scenario={scenarioInfo} briefingRead={briefingRead} />}
        {phase === 'storyboard' && <StoryboardPage auth={auth} onReady={handleBeginSimulation} scenarioInfoProp={scenarioInfo} competitorsProp={competitors} sbRemaining={sbRemaining} sbExpired={sbExpired} simulationBegun={simulationBegun} />}
        {phase === 'playing'    && <GamePage onMainPage={handleMainPage} scenarioInfoProp={scenarioInfo} gameStateProp={gameState} sliderConstraintsProp={sliderConstraints} competitorsProp={competitors} onGameStateChange={setGameState} wsData={wsData} />}
        {phase === 'admin'      && <AdminPage />}
      </div>
    </AuthContext.Provider>
  )
}
