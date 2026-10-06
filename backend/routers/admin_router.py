"""Admin endpoints. Every route requires an X-Admin-Token issued by /api/login."""
import asyncio
import io
import logging
import time

from fastapi import APIRouter, Depends, File, Header, HTTPException, Request, UploadFile

from auth import (
    hash_pw, clear_session, get_store, is_session_active, release_controller,
    verify_admin_token,
)
from config import NP
from models.schemas import (
    AdminStatusResponse, PauseRequest, SetPhaseRequest, SetScenarioRequest,
)
from services import event_bus

logger = logging.getLogger("admin")


def require_admin(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token")) -> str:
    """401 unless the request carries a valid admin token. Returns the admin username."""
    username = verify_admin_token(x_admin_token or "")
    if username is None:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    return username


# The dependency is applied at router level, so any route added here is protected.
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])

KICK_GRACE_SECONDS = 0.3  # lets the "kicked" message reach the client before its socket closes


def _player_team_keys(users: list[dict]) -> list[str]:
    return list({u['team_key'] for u in users if u.get('team_key') and not u.get('is_admin')})


@router.get("/status", response_model=AdminStatusResponse)
async def admin_status(request: Request):
    """Dashboard data: teams, online users, progress and leaderboard."""
    store = get_store()
    users = store.load_users()

    now = time.time()
    connected = await request.app.state.manager.connected_users()
    session_view = [
        {"username": u, "team_key": tk, "last_seen": now, "active": True}
        for (tk, u) in connected
    ]

    all_locked = store.get_all_locked_years()
    completed_teams = []
    pending_teams = []
    for tk in {u['team_key'] for u in users if u.get('team_key')}:
        locked_count = all_locked.get(tk, -1)
        if locked_count >= NP:
            completed_teams.append(tk)
        else:
            pending_teams.append({"team_key": tk, "years_locked": max(locked_count, 0)})

    return AdminStatusResponse(
        teams=[{"team_key": u.get('team_key', ''), "username": u.get('username', ''),
                "is_admin": u.get('is_admin', False)}
               for u in users if not u.get('is_admin', False)],
        sessions=session_view,
        paused=store.is_paused(),
        completed_teams=completed_teams,
        pending_teams=pending_teams,
        leaderboard=_compute_admin_leaderboard() if completed_teams else [],
    )


@router.get("/events")
async def admin_events(request: Request, since: int = 0):
    """Event feed since the given id. Join/leave events are derived from live WebSockets on each poll."""
    try:
        await event_bus.sync_presence(request.app.state.manager)
    except Exception:
        pass
    return {"events": event_bus.get_since(since), "latest_id": event_bus.latest_id()}


@router.post("/pause")
async def toggle_pause(req: PauseRequest, request: Request):
    get_store().set_paused(req.paused)

    await request.app.state.manager.broadcast_all({"type": "paused", "paused": req.paused})

    timer_mgr = request.app.state.timer_manager
    if req.paused:
        timer_mgr.pause_all()
    else:
        timer_mgr.unpause_all()

    event_bus.emit(
        "paused" if req.paused else "resumed",
        text="Game paused by administrator" if req.paused else "Game resumed by administrator",
    )
    return {"status": "ok", "paused": req.paused}


@router.get("/scenarios")
async def list_available_scenarios():
    from scenarios import list_scenarios
    return {"scenarios": list_scenarios()}


@router.get("/active-scenario")
async def get_active_scenario_info():
    from scenarios import get_active_scenario
    s = get_active_scenario()
    if not s:
        return {"country": "us", "industry": "ev", "label": "United States — Electric Vehicles"}
    parts = s.scenario_id.split('_', 1)
    country, industry = (parts[0], parts[1]) if len(parts) == 2 else ('us', 'ev')
    return {
        "country": country,
        "industry": industry,
        "scenario_id": s.scenario_id,
        "label": s.scenario_label,
    }


@router.post("/set-scenario")
async def set_scenario(req: SetScenarioRequest, request: Request):
    from config import refresh_cfg, refresh_derived
    from scenarios import set_active_scenario

    set_active_scenario(req.country, req.industry)
    refresh_cfg()
    refresh_derived()
    get_store().save_active_scenario(req.country, req.industry)

    await request.app.state.manager.broadcast_all({
        "type": "scenario_change",
        "country": req.country,
        "industry": req.industry,
    })
    return {"status": "ok", "country": req.country, "industry": req.industry}


@router.post("/set-phase")
async def set_phase(req: SetPhaseRequest, request: Request):
    """Notify clients of a phase change. Game states are created when each team first logs in."""
    if req.phase == "playing":
        timer_mgr = request.app.state.timer_manager
        for tk in _player_team_keys(get_store().load_users()):
            timer_mgr.stop_storyboard_timer(tk)

    await request.app.state.manager.broadcast_all({"type": "phase_change", "phase": req.phase})
    return {"status": "ok", "phase": req.phase}


@router.post("/reset")
async def reset_game(request: Request):
    """Kick active players, then wipe all game state and timers."""
    store = get_store()
    users = store.load_users()
    manager = request.app.state.manager
    timer_mgr = request.app.state.timer_manager

    admin_team_keys = {u['team_key'] for u in users if u.get('is_admin', False)}
    active_sessions = [
        s for s in store.get_all_sessions()
        if s.get('active', False) and s.get('team_key', '') not in admin_team_keys
        and s.get('username') and s.get('team_key')
    ]

    for s in active_sessions:
        await manager.send_to_user(s['team_key'], s['username'], {
            "type": "kicked",
            "message": "Game has been reset by the administrator.",
        })
        release_controller(s['team_key'], s['username'])
        clear_session(s['username'], s['team_key'])

    if active_sessions:
        await asyncio.sleep(KICK_GRACE_SECONDS)

    for s in active_sessions:
        await manager.disconnect_user(s['team_key'], s['username'])

    store.reset_all_state()
    store.clear_all_storyboard_seen()

    for tk in list(timer_mgr._tasks):
        timer_mgr.stop_timer(tk)
    for tk in list(timer_mgr._sb_tasks):
        timer_mgr.stop_storyboard_timer(tk)

    await manager.broadcast_all({"type": "game_reset"})

    event_bus.reset_all()
    event_bus.emit("reset", text="Game reset by administrator — all teams returned to Year 1")
    return {"status": "ok"}


@router.post("/start-timers")
async def start_timers(request: Request):
    """Start year timers for all teams."""
    body = await request.json()
    duration = body.get('duration_seconds', 2400)

    store = get_store()
    team_keys = _player_team_keys(store.load_users())

    timer_mgr = request.app.state.timer_manager
    for tk in team_keys:
        gs = store.load_game_state(tk)
        timer_mgr.start_timer(tk, duration, gs.get('current_year', 1) if gs else 1)

    return {"status": "ok", "teams": len(team_keys), "duration": duration}


@router.post("/add-user")
async def add_user(request: Request):
    body = await request.json()
    username = body.get('username', '').strip()
    password = body.get('password', '').strip()
    team_key = body.get('team_key', '').strip()
    mode = body.get('mode', 'competition')

    if not username or not password or not team_key:
        return {"status": "error", "error": "username, password and team_key are required"}

    store = get_store()
    if any(u['username'] == username for u in store.load_users()):
        return {"status": "error", "error": f"Username '{username}' already exists"}

    store.add_user({
        "username": username,
        "password": hash_pw(password),
        "team_key": team_key,
        "mode": mode,
        "is_admin": False,
    })
    return {"status": "ok", "username": username, "team_key": team_key}


@router.post("/delete-user")
async def delete_user(request: Request):
    """Delete a user. Blocked while that user is logged in."""
    body = await request.json()
    username = body.get('username', '').strip()
    team_key = body.get('team_key', '').strip()
    if not username or not team_key:
        return {"status": "error", "error": "username and team_key are required"}

    if is_session_active(username, team_key):
        return {"status": "error", "error": f"Cannot delete '{username}' — they are currently logged in. Ask them to log out first."}

    deleted = get_store().delete_users([(username, team_key)])
    if deleted == 0:
        return {"status": "error", "error": "User not found"}
    return {"status": "ok", "deleted": deleted}


@router.post("/kick-user")
async def kick_user(request: Request):
    """Log a user out: the client gets a "kicked" message, then its socket is closed."""
    body = await request.json()
    username = body.get('username', '').strip()
    team_key = body.get('team_key', '').strip()
    if not username or not team_key:
        return {"status": "error", "error": "username and team_key are required"}

    manager = request.app.state.manager
    await manager.send_to_user(team_key, username, {
        "type": "kicked",
        "message": "You have been logged out by the administrator.",
    })
    await asyncio.sleep(KICK_GRACE_SECONDS)
    await manager.disconnect_user(team_key, username)

    release_controller(team_key, username)
    clear_session(username, team_key)

    event_bus.emit(
        "kicked",
        text=f"{username} ({team_key}) was kicked by administrator",
        team_key=team_key,
        username=username,
    )
    return {"status": "ok", "kicked": username}


@router.post("/kick-all-users")
async def kick_all_users(request: Request):
    """Log out every connected non-admin player."""
    users = get_store().load_users()
    admin_team_keys = {u['team_key'] for u in users if u.get('is_admin')}

    manager = request.app.state.manager
    active_players = [
        (tk, u) for (tk, u) in await manager.connected_users()
        if u and tk and tk != "__admin__" and tk not in admin_team_keys
    ]

    for team_key, username in active_players:
        await manager.send_to_user(team_key, username, {
            "type": "kicked",
            "message": "You have been logged out by the administrator.",
        })
        release_controller(team_key, username)
        clear_session(username, team_key)

    if active_players:
        await asyncio.sleep(KICK_GRACE_SECONDS)

    for team_key, username in active_players:
        await manager.disconnect_user(team_key, username)

    kicked = len(active_players)
    event_bus.emit(
        "kick_all",
        text=f"All players kicked by administrator ({kicked} session(s) closed)",
        count=kicked,
    )
    return {"status": "ok", "kicked": kicked}


@router.post("/mass-delete-users")
async def mass_delete_users():
    """Delete all non-admin users. Blocked while any player is logged in."""
    store = get_store()
    users = store.load_users()

    admin_team_keys = {u['team_key'] for u in users if u.get('is_admin')}
    active_players = [
        s for s in store.get_all_sessions()
        if s.get('active') and s.get('team_key') not in admin_team_keys
    ]
    if active_players:
        names = ', '.join(s.get('username', '?') for s in active_players[:5])
        return {"status": "error", "error": f"Cannot delete users while players are logged in ({names}). Kick them first."}

    players = [(u['username'], u['team_key']) for u in users if not u.get('is_admin')]
    return {"status": "ok", "deleted": store.delete_users(players)}


@router.post("/reset-team")
async def reset_team(request: Request):
    """Wipe one team's game state."""
    body = await request.json()
    team_key = body.get('team_key', '').strip()
    if not team_key:
        return {"status": "error", "error": "team_key is required"}

    store = get_store()
    try:
        store.delete_game_state(team_key)
    except Exception:
        store.save_game_state(team_key, {})
    return {"status": "ok", "team_key": team_key}


@router.post("/bulk-add-users")
async def bulk_add_users(file: UploadFile = File(...)):
    """Add users from an .xlsx file with the columns Username, Password, Team Key (and optional Mode)."""
    import openpyxl

    contents = await file.read()
    try:
        wb = openpyxl.load_workbook(io.BytesIO(contents))
    except Exception as e:
        return {"status": "error", "error": f"Could not read xlsx file: {e}"}

    rows = list(wb.active.iter_rows(values_only=True))
    if not rows:
        return {"status": "error", "error": "File is empty"}

    def norm(v):
        return str(v or '').lower().strip().replace(' ', '').replace('_', '').replace('-', '')

    headers = [norm(h) for h in rows[0]]

    def col(aliases):
        for alias in aliases:
            if norm(alias) in headers:
                return headers.index(norm(alias))
        return -1

    ui = col(['username', 'user', 'name'])
    pi = col(['password', 'pass', 'pwd'])
    ti = col(['teamkey', 'team', 'key'])
    mi = col(['mode'])

    if ui == -1 or pi == -1 or ti == -1:
        return {
            "status": "error",
            "error": f"Could not find required columns. Headers found: {list(rows[0])}. "
                     "Need: Username, Password, Team Key",
        }

    store = get_store()
    existing_usernames = {u['username'] for u in store.load_users()}

    added = 0
    errors = []
    for i, row in enumerate(rows[1:], start=2):
        def cell(idx):
            return str(row[idx] or '').strip() if 0 <= idx < len(row) else ''

        username, password, team_key = cell(ui), cell(pi), cell(ti)
        mode = cell(mi) if mi >= 0 else 'competition'
        if mode not in ('competition', 'course'):
            mode = 'competition'

        if not username or not password or not team_key:
            errors.append(f"Row {i}: missing required fields")
            continue
        if username in existing_usernames:
            errors.append(f"Row {i}: username '{username}' already exists — skipped")
            continue

        try:
            store.add_user({
                "username": username,
                "password": hash_pw(password),
                "team_key": team_key,
                "mode": mode,
                "is_admin": False,
            })
            existing_usernames.add(username)
            added += 1
        except Exception as e:
            errors.append(f"Row {i}: {e}")

    return {"status": "ok", "added": added, "errors": errors}


def _compute_admin_leaderboard() -> list[dict]:
    """Leaderboard from each team's stored final_vpi, computed on demand if missing."""
    try:
        from game_state import get_all_team_keys, get_team_gs
        from leaderboard import compute_final_vpi

        entries = []
        for tk in get_all_team_keys():
            gs = get_team_gs(tk)
            if not gs or not gs.get('year_results'):
                continue
            vpi_data = gs.get('final_vpi')
            if not vpi_data:
                try:
                    vpi_data = compute_final_vpi(gs, gs.get('mode', 'competition'))
                except Exception:
                    continue
            if vpi_data:
                entries.append({
                    'team_key': tk,
                    'team': tk,
                    'vpi': vpi_data['vpi'],
                    'grade': vpi_data['grade'],
                    'year': vpi_data['year'],
                    'avg_share': vpi_data.get('avg_share', 0),
                    'ras': vpi_data.get('ras', 0),
                })
        entries.sort(key=lambda e: e['vpi'], reverse=True)
        return entries
    except Exception as e:
        logger.warning("Admin leaderboard failed: %s", e)
        return []
