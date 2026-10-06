/**
 * hooks/useApi.js — REST API helper.
 */

const BASE = '/api'

// Admin endpoints (/api/admin/*) require an opaque session token issued by /api/login on successful
// admin authentication.
const ADMIN_TOKEN_KEY = 'oras_admin_token'

export function getAdminToken() {
  try { return sessionStorage.getItem(ADMIN_TOKEN_KEY) || '' } catch { return '' }
}
export function setAdminToken(tok) {
  try {
    if (tok) sessionStorage.setItem(ADMIN_TOKEN_KEY, tok)
    else sessionStorage.removeItem(ADMIN_TOKEN_KEY)
  } catch {}
}

// Endpoints that are safe to retry on transient server errors (429, 503).
const RETRYABLE_PATHS = ['/lock-year', '/begin-simulation']
const MAX_RETRIES = 4
const RETRY_BASE_MS = 1000  // 1s, 2s, 4s, 8s

async function request(path, options = {}, _attempt = 0) {
  const headers = { 'Content-Type': 'application/json', ...options.headers }
  // Auto-inject the admin token on admin endpoints only.
  if (path.startsWith('/admin/') || path === '/logout') {
    const tok = getAdminToken()
    if (tok) headers['X-Admin-Token'] = tok
  }
  const res = await fetch(`${BASE}${path}`, {
    headers,
    ...options,
  })
  if (!res.ok) {
    // 401 on an admin endpoint means the token expired or was revoked —
    // surface that distinctly so the caller can route back to login.
    if (res.status === 401 && path.startsWith('/admin/')) {
      setAdminToken('')
      const err = new Error('Admin session expired — please log in again.')
      err.status = 401
      throw err
    }
    // Retry on 429 (rate limited) or 503 (server overloaded) for critical endpoints.
    if ((res.status === 429 || res.status === 503) &&
        RETRYABLE_PATHS.some(p => path.startsWith(p)) &&
        _attempt < MAX_RETRIES) {
      const delay = RETRY_BASE_MS * Math.pow(2, _attempt)
      await new Promise(resolve => setTimeout(resolve, delay))
      return request(path, options, _attempt + 1)
    }
    // For game endpoints (like /lock-year), try to parse the error body so the caller can read res.error
    // and show a meaningful message instead of the generic "Network error" catch fallback.
    let body = null
    try { body = await res.json() } catch {}
    if (body && typeof body === 'object') {
      // Return the error payload rather than throwing — lets handleLockYear
      // check res.status === 'error' and display res.error to the user.
      return { status: 'error', error: body.detail || body.error || `Server error ${res.status}`, _httpStatus: res.status }
    }
    throw new Error(`API error: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

// Raw-fetch wrapper for admin endpoints that need non-JSON bodies (e.g.
export async function adminFetch(path, options = {}) {
  if (!path.startsWith('/api/admin/')) {
    throw new Error(`adminFetch only accepts /api/admin/* paths, got ${path}`)
  }
  const tok = getAdminToken()
  const headers = { ...(options.headers || {}) }
  if (tok) headers['X-Admin-Token'] = tok
  const res = await fetch(path, { ...options, headers })
  if (res.status === 401) {
    setAdminToken('')
    const err = new Error('Admin session expired — please log in again.')
    err.status = 401
    throw err
  }
  return res
}

export const api = {
  // Auth
  login: (username, password, team_key = '') =>
    request('/login', {
      method: 'POST',
      body: JSON.stringify({ username, password, team_key }),
    }),

  logout: (username, team_key) =>
    request('/logout', {
      method: 'POST',
      body: JSON.stringify({ username, team_key }),
    }),

  myRole: (team_key, username) =>
    request(`/my-role/${encodeURIComponent(team_key)}/${encodeURIComponent(username)}`),

  beginSimulation: (team_key, username) =>
    request('/begin-simulation', {
      method: 'POST',
      body: JSON.stringify({ team_key, username }),
    }),

  // Game
  lockYear: (team_key, username, allocations, subdecisions, carryover = 0.5) =>
    request('/lock-year', {
      method: 'POST',
      body: JSON.stringify({ team_key, username, allocations, subdecisions, carryover }),
    }),

  // Persist in-progress slider/dropdown state so server-side auto-lock (on year-timer expiry) uses the
  // user's current draft instead of scenario defaults.
  saveDraft: (team_key, username, allocations, subdecisions) =>
    request('/draft-allocations', {
      method: 'POST',
      body: JSON.stringify({ team_key, username, allocations, subdecisions }),
    }),

  getGameState: (team_key) =>
    request(`/game-state/${team_key}`),

  getSubDecisions: () =>
    request('/sub-decisions'),

  getScenarioInfo: () =>
    request('/scenario-info'),

  getCompetitors: (play_seed) =>
    request(`/competitors/${play_seed}`),

  // Admin
  adminStatus: () =>
    request('/admin/status'),

  pause: (paused) =>
    request('/admin/pause', {
      method: 'POST',
      body: JSON.stringify({ paused }),
    }),

  setScenario: (country, industry) =>
    request('/admin/set-scenario', {
      method: 'POST',
      body: JSON.stringify({ country, industry }),
    }),

  setPhase: (phase) =>
    request('/admin/set-phase', {
      method: 'POST',
      body: JSON.stringify({ phase }),
    }),

  resetGame: () =>
    request('/admin/reset', { method: 'POST' }),

  startTimers: (duration_seconds = 2400) =>
    request('/admin/start-timers', {
      method: 'POST',
      body: JSON.stringify({ duration_seconds }),
    }),
}
