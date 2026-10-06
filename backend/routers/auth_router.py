"""Login, logout and role endpoints."""
import asyncio
import logging
import os
import random

from fastapi import APIRouter, Request

import config as _config
from auth import (
    authenticate, claim_controller, clear_session, get_controller, get_store,
    issue_admin_token, register_session, release_controller, revoke_admin_token,
)
from models.schemas import LoginRequest, LoginResponse

router = APIRouter(tags=["auth"])
logger = logging.getLogger("auth")

# Admin credentials come from the environment. Admin login stays disabled
# until both are set.
ADMIN_USERNAME = (os.environ.get('ADMIN_USERNAME') or '').strip()
ADMIN_PASSWORD = (os.environ.get('ADMIN_PASSWORD') or '').strip()
_ADMIN_CONFIGURED = bool(ADMIN_USERNAME and ADMIN_PASSWORD)
if not _ADMIN_CONFIGURED:
    logger.warning(
        "ADMIN_USERNAME and/or ADMIN_PASSWORD are not set; admin login is disabled."
    )


def _new_game_state() -> dict | None:
    """Create a team's first game state for the active scenario, or None if no scenario is active."""
    from scenarios import get_active_scenario
    from simulator import generate_player_news_events

    if get_active_scenario() is None:
        return None

    play_seed = random.randint(1, 99999)
    news = generate_player_news_events(_config.NP, play_seed)
    # Every field is persisted because game_logic rebuilds NewsEvent objects from this dict.
    player_news = [
        {
            'year': e.year, 'headline': e.headline, 'detail': e.detail,
            'sentiment': e.sentiment, 'dept_pressure': e.dept_pressure,
            'dept_k_mult': e.dept_k_mult, 'dept_smax_mult': e.dept_smax_mult,
            'revenue_impact': e.revenue_impact, 'profit_impact': e.profit_impact,
        }
        for e in news
    ]
    return {
        'current_year': 1,
        'locked_allocations': [],
        'locked_subdecisions': [],
        'year_results': [],
        'play_seed': play_seed,
        'completed': False,
        'mode': 'competition',
        'available_budget': _config.cfg.total_budget,
        'current_fixed_costs': _config.cfg.fixed_costs,
        'cumulative_inflation': 1.0,
        'player_news': player_news,
        'waiting_for_others': False,
        'simulation_started': True,
    }


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, request: Request):
    username = req.username.strip()
    password = req.password.strip()
    team_key = req.team_key.strip()

    if not username or not password:
        return LoginResponse(status="error", error="Username and password are required")

    if _ADMIN_CONFIGURED and username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return LoginResponse(
            status="ok",
            username=username,
            team_key="__admin__",
            is_admin=True,
            phase="admin",
            admin_token=issue_admin_token(username),
        )
    if username == ADMIN_USERNAME or username in ('superadmin', 'admin'):
        if not _ADMIN_CONFIGURED:
            return LoginResponse(
                status="error",
                error="Admin login is not configured for this deployment.",
            )
        return LoginResponse(status="error", error="Invalid admin credentials")

    if not team_key:
        return LoginResponse(status="error", error="Team key is required")

    # "Already logged in" means a live WebSocket, not a session record that
    # lingers after a tab closes.
    connected_now = await request.app.state.manager.connected_users()

    # Storage and CPU-heavy work runs in a thread so logins do not block the event loop.
    def do_login_work():
        user = authenticate(username, password, team_key)
        if not user:
            return None, "Invalid username, password, or team key"
        if (team_key, username) in connected_now:
            return None, "This user is already logged in. Log out of the other session first."

        is_ctrl = claim_controller(team_key, username)
        register_session(username, team_key)

        store = get_store()
        # Joined teams form the lock barrier's denominator floor.
        store.mark_team_joined(team_key)

        gs = store.load_game_state(team_key)
        if not gs:
            try:
                gs = _new_game_state()
                if gs:
                    store.save_game_state(team_key, gs)
            except Exception as e:
                logger.warning("Could not create game state for %s: %s", team_key, e)

        if gs and gs.get('simulation_started'):
            phase = 'playing'
        elif gs:
            phase = 'storyboard'
        else:
            phase = 'start'  # no scenario active

        # Bundle everything the client needs to render without follow-up requests.
        scenario_info = slider_constraints = competitors = None
        try:
            from routers.game_router import _build_game_bundle, _build_scenario_info
            scenario_info = _build_scenario_info()
            if gs:
                slider_constraints, competitors = _build_game_bundle(gs)
        except Exception as e:
            logger.warning("Could not bundle login data: %s", e)

        return {
            'is_ctrl': is_ctrl,
            'gs': gs,
            'phase': phase,
            'scenario_info': scenario_info,
            'slider_constraints': slider_constraints,
            'competitors': competitors,
            'storyboard_seen': store.get_storyboard_seen(username, team_key),
        }, None

    result, err = await asyncio.get_event_loop().run_in_executor(None, do_login_work)
    if err:
        return LoginResponse(status="error", error=err)

    gs = result['gs']
    return LoginResponse(
        status="ok",
        username=username,
        team_key=team_key,
        is_controller=result['is_ctrl'],
        phase=result['phase'],
        play_seed=gs.get('play_seed', 0) if gs else 0,
        storyboard_seen=result['storyboard_seen'],
        game_state=gs,
        scenario_info=result['scenario_info'],
        slider_constraints=result['slider_constraints'],
        competitors=result['competitors'],
    )


@router.post("/logout")
async def logout(request: Request):
    body = await request.json()
    username = body.get('username', '')
    team_key = body.get('team_key', '')

    admin_token = request.headers.get('X-Admin-Token', '')
    if admin_token:
        revoke_admin_token(admin_token)

    if username and team_key:
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: (release_controller(team_key, username),
                     clear_session(username, team_key)),
        )
    return {"status": "ok"}


@router.post("/storyboard-seen")
async def mark_storyboard_seen(request: Request):
    body = await request.json()
    username = body.get('username', '').strip()
    team_key = body.get('team_key', '').strip()
    if not username or not team_key:
        return {"status": "error", "error": "username and team_key required"}
    await asyncio.get_event_loop().run_in_executor(
        None, get_store().set_storyboard_seen, username, team_key
    )
    return {"status": "ok"}


@router.get("/my-role/{team_key}/{username}")
async def my_role(team_key: str, username: str):
    """Whether this user is their team's controller. The role is only assigned at login."""
    current = await asyncio.get_event_loop().run_in_executor(
        None, lambda: get_controller(team_key)
    )
    return {"is_controller": current == username}
