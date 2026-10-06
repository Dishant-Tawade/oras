/**
 * hooks/useGameSocket.js — WebSocket hook for real-time updates.
 */

import { useEffect, useRef, useState, useCallback } from 'react'

export function useGameSocket(teamKey, username, isController) {
  const wsRef        = useRef(null)
  const heartbeatRef = useRef(null)
  const reconnectRef = useRef(null)
  // `stopReconnectRef` is set to true when: (a) the component unmounts, or (b) we receive a terminal
  // server message (`kicked`, `game_reset`).
  const stopReconnectRef = useRef(false)

  const [connected,         setConnected]         = useState(false)
  const [gameState,         setGameState]         = useState(null)
  const [timerRemaining,    setTimerRemaining]    = useState(0)
  const [timerPaused,       setTimerPaused]       = useState(false)
  const [paused,            setPaused]            = useState(false)
  const [pauseAnnouncement, setPauseAnnouncement] = useState(null)
  const [blocking,          setBlocking]          = useState([])
  const [lockProgress,      setLockProgress]      = useState({ locked: 0, total: 0 })
  const [leaderboard,       setLeaderboard]       = useState([])
  const [phase,             setPhase]             = useState(null)
  const [timerExpired,      setTimerExpired]      = useState(null)   // {year, game_state}
  const [sbRemaining,       setSbRemaining]       = useState(0)      // storyboard countdown
  const [sbExpired,         setSbExpired]         = useState(false)  // storyboard timer ran out
  const [simulationBegun,   setSimulationBegun]   = useState(false)  // controller hit "Begin Simulation"

  const [wasLastLocker,     setWasLastLocker]     = useState(false)

  const connect = useCallback(() => {
    if (!teamKey) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = import.meta.env.VITE_WS_HOST || window.location.host
    const wsUrl = `${protocol}//${wsHost}/ws/${teamKey}?username=${encodeURIComponent(username || '')}&is_controller=${isController ? 'true' : 'false'}`

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      // Send immediate heartbeat so admin sees user online straight away
      ws.send(JSON.stringify({ type: 'heartbeat' }))
      heartbeatRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'heartbeat' }))
        }
      }, 10000)  // 10s heartbeat — keeps sessions active on admin dashboard
    }

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        switch (msg.type) {
          case 'game_state_update':
            setGameState(msg.data)
            break

          case 'year_locked':
            if (msg.game_state) setGameState(msg.game_state)
            setWasLastLocker(false)
            break

          case 'all_teams_locked':
            if (msg.game_state) setGameState(msg.game_state)
            if (msg.leaderboard) setLeaderboard(msg.leaderboard)
            // Clear waiting state so WaitingOverlay disappears immediately
            setLockProgress({ locked: 0, total: 0 })
            setBlocking([])
            // Clear the old timer — next year's tick will arrive shortly and set the new value
            setTimerRemaining(0)
            setTimerPaused(false)
            // Server tells us which team triggered the barrier (triggered_by).
            setWasLastLocker(msg.triggered_by != null && msg.triggered_by === teamKey)
            break

          case 'timer_tick':
            setTimerRemaining(msg.remaining)
            setTimerPaused(msg.paused || false)
            break

          case 'timer_expired':
            // Server auto-locked the year — update game state and notify UI
            setTimerRemaining(0)
            if (msg.game_state) setGameState(msg.game_state)
            setTimerExpired({ year: msg.year, game_state: msg.game_state })
            break

          case 'paused':
            setPaused(msg.paused)
            setPauseAnnouncement(msg.paused ? (msg.announcement || null) : null)
            break

          case 'blocking_update':
            setBlocking(msg.blocking || [])
            break

          case 'lock_progress':
            setLockProgress({ locked: msg.locked || 0, total: msg.total || 0 })
            break

          case 'leaderboard_update':
            setLeaderboard(msg.entries || [])
            break

          case 'phase_change':
            setPhase(msg.phase)
            break

          case 'game_reset':
            // Terminal message — do not reconnect after the upcoming close.
            stopReconnectRef.current = true
            clearTimeout(reconnectRef.current)
            clearInterval(heartbeatRef.current)
            try { wsRef.current?.close() } catch {}
            // Server will follow with phase_change → 'login', which triggers logout via GamePage useEffect
            // Small delay so UI doesn't flash blank before redirect
            setTimeout(() => { setGameState(null); setPhase('login') }, 600)
            break

          case 'kicked':
            // Same terminal-message handling as game_reset — see above.
            stopReconnectRef.current = true
            clearTimeout(reconnectRef.current)
            clearInterval(heartbeatRef.current)
            try { wsRef.current?.close() } catch {}
            setGameState(null)
            setPhase('login')
            break

          case 'storyboard_tick':
            setSbRemaining(msg.remaining)
            break

          case 'storyboard_expired':
            setSbRemaining(0)
            setSbExpired(true)
            break

          case 'storyboard_complete':
            // The controller finished the briefing and started the run for the whole team (begin-simulation
            // endpoint).
            setSimulationBegun(true)
            break

          default:
            break
        }
      } catch (e) {
        console.error('[WS] Failed to parse message:', e)
      }
    }

    ws.onclose = () => {
      setConnected(false)
      clearInterval(heartbeatRef.current)
      // Do NOT reconnect if the component unmounted or we received a terminal message (kicked / game_reset).
      if (stopReconnectRef.current) return
      reconnectRef.current = setTimeout(connect, 3000)
    }

    ws.onerror = () => {}
  }, [teamKey, username, isController])

  useEffect(() => {
    // No team key → logged out, kicked, or between sessions.
    if (!teamKey) {
      stopReconnectRef.current = true
      clearInterval(heartbeatRef.current)
      clearTimeout(reconnectRef.current)
      if (wsRef.current) { try { wsRef.current.close() } catch {} }
      return
    }
    // Re-arm reconnect each time the effect (re-)mounts — teamKey may have changed.
    stopReconnectRef.current = false
    // A new session is starting (teamKey / username / role changed — e.g.
    setPhase(null)
    setSbExpired(false)
    setSimulationBegun(false)
    setSbRemaining(0)
    connect()
    return () => {
      // Stop the reconnect loop *before* closing the socket — the upcoming onclose callback runs
      // asynchronously after this cleanup returns.
      stopReconnectRef.current = true
      clearInterval(heartbeatRef.current)
      clearTimeout(reconnectRef.current)
      if (wsRef.current) wsRef.current.close()
    }
  }, [connect])

  const requestState = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'request_state' }))
    }
  }, [])

  return {
    connected,
    gameState,
    timerRemaining,
    timerPaused,
    paused,
    pauseAnnouncement,
    blocking,
    lockProgress,
    setBlocking,
    setLockProgress,
    leaderboard,
    phase,
    timerExpired,
    sbRemaining,
    sbExpired,
    simulationBegun,
    wasLastLocker,
    setWasLastLocker,
    requestState,
    ws: wsRef,
  }
}
