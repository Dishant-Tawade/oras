"""Game endpoints: year locking, game state and briefing data."""
import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import APIRouter, HTTPException, Request

from auth import get_store
from config import NP
from game_state import compute_waiting_for_others, get_logged_in_team_keys
from leaderboard import compute_leaderboard_entries
from models.schemas import LockYearRequest, LockYearResponse
from services import event_bus
from services.game_logic import (
    execute_lock_year, get_budget_allocatability, get_competitors_data,
    get_slider_constraints, validate_lock_year,
)
from services.timer import year_duration

logger = logging.getLogger("game_router")

router = APIRouter(tags=["game"])

WATCHDOG_INTERVAL_SECONDS = 30
WATCHDOG_MAX_RETRIES = 18
MAX_LOAD_WORKERS = 32

# Pending watchdog tasks per year; cancelled once the normal broadcast completes.
_year_watchdogs: dict[int, set[asyncio.Task]] = {}
_team_lock_mutexes: dict[str, asyncio.Lock] = {}


def _build_scenario_info() -> dict | None:
    """Scenario details for the client (also returned by GET /scenario-info and bundled into the login response)."""
    from scenarios import get_active_scenario
    from config import get_scenario_cfg
    from simulator import get_consumer_segments, get_sub_decisions, get_dept_background

    s = get_active_scenario()
    if not s:
        return None

    cfg = get_scenario_cfg()
    storyboard_data = None
    sb_obj = getattr(s, 'storyboard', None) or getattr(s, 'briefing', None)
    if sb_obj:
        storyboard_data = {
            'world_headline':    getattr(sb_obj, 'world_headline', ''),
            'world_body':        getattr(sb_obj, 'world_body', ''),
            'market_body':       getattr(sb_obj, 'market_body', ''),
            'company_body':      getattr(sb_obj, 'company_body', ''),
            'company_subtitle':  getattr(sb_obj, 'company_subtitle', ''),
            'product_body':      getattr(sb_obj, 'product_body', ''),
            'product_subtitle':  getattr(sb_obj, 'product_subtitle', ''),
            'role_body':         getattr(sb_obj, 'role_body', ''),
            'objective_body':    getattr(sb_obj, 'objective_body', ''),
            'ready_headline':    getattr(sb_obj, 'ready_headline', ''),
            'ready_body':        getattr(sb_obj, 'ready_body', ''),
            'competitors_intro': getattr(sb_obj, 'competitors_intro', ''),
            'departments_intro': getattr(sb_obj, 'departments_intro', ''),
            'mandate_body':      getattr(sb_obj, 'mandate_body', ''),
            'practice_body':     getattr(sb_obj, 'practice_body', ''),
        }

    segments = []
    segment_colors = {}
    try:
        for seg_key, seg in get_consumer_segments().items():
            segments.append({
                'key':           seg_key,
                'label':         seg.get('label', seg_key),
                'description':   seg.get('description', ''),
                'market_weight': seg.get('market_weight', 0),
            })
        if hasattr(s, 'segment_colors') and s.segment_colors:
            segment_colors = dict(s.segment_colors)
    except Exception:
        pass

    dept_backgrounds = {}
    try:
        dept_backgrounds = get_dept_background()
    except Exception:
        pass

    sub_decisions = {}
    try:
        for dept_name, sd in get_sub_decisions().items():
            sd_opts = getattr(sd, 'options', {}) if not isinstance(sd, dict) else sd.get('options', {})
            opts = {}
            for opt_key, opt in (sd_opts.items() if hasattr(sd_opts, 'items') else {}.items()):
                if isinstance(opt, dict):
                    seg_mults = {k: float(v) for k, v in opt.get('segment_multipliers', {}).items()}
                    label = opt.get('label', opt_key)
                    desc = opt.get('description', '')
                else:
                    seg_mults = {k: float(v) for k, v in getattr(opt, 'segment_multipliers', {}).items()}
                    label = getattr(opt, 'label', opt_key)
                    desc = getattr(opt, 'description', '')
                opts[opt_key] = {'label': label, 'description': desc, 'segment_multipliers': seg_mults}
            sub_decisions[dept_name] = {
                'label':   getattr(sd, 'label', dept_name) if not isinstance(sd, dict) else sd.get('label', dept_name),
                'options': opts,
            }
    except Exception:
        pass

    departments = []
    if hasattr(s, 'department_meta') and s.department_meta:
        for dm in s.department_meta:
            name = dm.name
            departments.append({
                'name':        name,
                'description': getattr(dm, 'description', ''),
                'background':  dept_backgrounds.get(name, '') or getattr(dm, 'background_description', ''),
                'color_key':   getattr(dm, 'color_key', ''),
                'min_spend':   getattr(dm, 'min_spend', 0),
                'max_spend':   getattr(dm, 'max_spend', 0),
            })
    elif hasattr(cfg, 'departments'):
        for d in cfg.departments:
            departments.append({
                'name':        d.name,
                'description': dept_backgrounds.get(d.name, ''),
                'background':  dept_backgrounds.get(d.name, ''),
                'min_spend':   getattr(d, 'min_spend', 0),
                'max_spend':   getattr(d, 'max_spend', 0),
            })

    financials = {}
    if hasattr(s, 'financials'):
        financials = {
            'inflation_min': getattr(s.financials, 'inflation_min', 0.02),
            'inflation_max': getattr(s.financials, 'inflation_max', 0.05),
        }

    return {
        "scenario_id":    s.scenario_id,
        "scenario_label": s.scenario_label,
        "country":        s.locale.country_code.lower(),
        "industry":       s.scenario_id.split('_')[-1] if '_' in s.scenario_id else '',
        "company_name":     s.company.name,
        "company_location": getattr(s.company, 'location', ''),
        "company_tagline":  getattr(s.company, 'tagline', ''),
        "role_title":       getattr(s.company, 'role_title', ''),
        "product_name":     getattr(s.company, 'product_name', ''),
        "unit_price":       getattr(s.company, 'unit_price', 0),
        "unit_price_label": getattr(s.company, 'unit_price_label', 'Unit Price'),
        "year1_capacity":   getattr(s.company, 'year1_capacity', 0),
        "capacity_unit":    getattr(s.company, 'capacity_unit', 'units'),
        "currency_symbol":     s.locale.currency_symbol,
        "small_number_suffix": getattr(s.locale, 'small_number_suffix', 'K'),
        "large_number_suffix": getattr(s.locale, 'large_number_suffix', 'M'),
        "total_budget": getattr(cfg, 'total_budget', 0),
        "fixed_costs":  getattr(cfg, 'fixed_costs', 0),
        "financials":   financials,
        "num_periods":  getattr(cfg, 'num_periods', 5),
        "performance_index_name": getattr(s, 'performance_index_name', 'VPI'),
        "performance_index_full": getattr(s, 'performance_index_full', 'Value Performance Index'),
        "market_label":           getattr(s, 'market_label', ''),
        "storyboard":    storyboard_data,
        "segments":      segments,
        "segment_colors": segment_colors,
        "departments":   departments,
        "sub_decisions": sub_decisions,
    }


def _build_game_bundle(gs: dict) -> tuple[list, list]:
    """Return (slider_constraints, competitors) for a game state."""
    constraints = get_slider_constraints(gs)
    allocatability = get_budget_allocatability(gs)
    constraints_payload = {
        'items': constraints,
        'max_allocatable': allocatability['max_allocatable'],
        'unallocatable': allocatability['unallocatable'],
    }
    play_seed = gs.get('play_seed', 42)
    competitors, _ = get_competitors_data(play_seed)
    return constraints_payload, competitors


def _with_leaderboard_flag(entries: list, team_key: str) -> list:
    return [{**e, 'is_you': e['team'] == team_key} for e in entries]


def _team_lock_mutex(team_key: str) -> asyncio.Lock:
    """One lock per team so a double-submitted lock request cannot run twice."""
    return _team_lock_mutexes.setdefault(team_key, asyncio.Lock())


async def _barrier_watchdog(request: Request, year: int, broadcaster_team: str, total_teams: int):
    """Release waiting teams if the normal last-locker broadcast never fires.

    Waits for logged-in teams with a connected controller to lock, retrying
    for up to about 10 minutes, then broadcasts `all_teams_locked` itself.
    """
    manager = request.app.state.manager
    timer_mgr = request.app.state.timer_manager
    store = get_store()

    await asyncio.sleep(WATCHDOG_INTERVAL_SECONDS)
    for attempt in range(WATCHDOG_MAX_RETRIES + 1):
        try:
            if store.is_broadcast_done(year):
                return
            counts = store.get_all_locked_years()
            logged_in = get_logged_in_team_keys(sessions=store.get_all_sessions())
            locked_teams = [tk for tk in logged_in if counts.get(tk, -1) >= year]
            if not locked_teams:
                return

            waiting_on = [
                tk for tk in logged_in
                if counts.get(tk, -1) < year and tk in manager.team_keys_with_controller
            ]
            if waiting_on:
                logger.info(
                    "[WATCHDOG] year=%d still waiting on %d connected teams (attempt %d/%d)",
                    year, len(waiting_on), attempt + 1, WATCHDOG_MAX_RETRIES + 1,
                )
                if attempt < WATCHDOG_MAX_RETRIES:
                    await asyncio.sleep(WATCHDOG_INTERVAL_SECONDS)
                    continue
                logger.warning(
                    "[WATCHDOG] year=%d retries exhausted; releasing and abandoning %d teams",
                    year, len(waiting_on),
                )

            if not store.claim_broadcast_slot(year):
                return

            shared_lb = compute_leaderboard_entries(broadcaster_team)
            counts = store.get_all_locked_years()
            team_keys = list(manager.team_keys)

            def prepare_states():
                prepared = {}
                for tk in team_keys:
                    try:
                        tk_gs = store.load_game_state(tk)
                        if not tk_gs:
                            continue
                        tk_gs = dict(tk_gs)
                        tk_gs['waiting_for_others'] = False
                        if counts.get(tk, -1) == year:
                            store.save_game_state(tk, tk_gs)
                        prepared[tk] = tk_gs
                    except Exception:
                        continue
                return prepared

            prepared = await asyncio.get_running_loop().run_in_executor(None, prepare_states)

            async def send_one(tk, tk_gs):
                try:
                    await manager.send_to_team(tk, {
                        "type": "all_teams_locked",
                        "year": year,
                        "game_state": tk_gs,
                        "leaderboard": _with_leaderboard_flag(shared_lb, tk),
                    })
                    await manager.send_to_team(tk, {"type": "blocking_update", "blocking": []})
                    timer_mgr.unpause_team(tk)
                    if counts.get(tk, -1) <= year:
                        timer_mgr.start_timer(tk, year_duration(year + 1), year + 1)
                except Exception:
                    pass

            await asyncio.gather(
                *[send_one(tk, tk_gs) for tk, tk_gs in prepared.items()],
                return_exceptions=True,
            )
            logger.info(
                "[WATCHDOG] Fired all_teams_locked for year %d: %d/%d teams locked",
                year, len(locked_teams), total_teams,
            )
            try:
                store.mark_broadcast_done(year)
            except Exception:
                pass
            return
        except Exception as e:
            logger.error("[WATCHDOG] Error for year %d attempt %d: %s", year, attempt + 1, e)
            if attempt < WATCHDOG_MAX_RETRIES:
                await asyncio.sleep(WATCHDOG_INTERVAL_SECONDS)


def _load_barrier_states(store, cur_year: int, broadcaster: str, broadcaster_gs: dict,
                         team_keys: list[str]) -> tuple[dict, set]:
    """Load every participating team's state for the year-end broadcast.

    Teams that locked this year are saved with `waiting_for_others` cleared.
    Teams already past this year are returned unchanged and reported as
    "advanced" so their timers are not restarted. Teams that have not locked
    are skipped. Returns (states by team, advanced team keys).
    """
    fresh_locked = store.get_all_locked_years()
    states = {broadcaster: dict(broadcaster_gs, waiting_for_others=False)}
    skipped = []
    already_advanced = set()
    others = [tk for tk in team_keys if tk != broadcaster]

    def load_one(tk):
        tk_locked = fresh_locked.get(tk, -1)
        if tk_locked < cur_year:
            # The cached count may lag; trust the state itself if it shows the lock.
            fallback = store.load_game_state(tk)
            if fallback:
                fb_count = len(fallback.get('locked_allocations', []))
                if fb_count >= cur_year:
                    gs_copy = dict(fallback, waiting_for_others=False)
                    advanced = fb_count > cur_year
                    if not advanced:
                        store.save_game_state(tk, gs_copy)
                    return tk, gs_copy, advanced, None
            return tk, None, False, f"{tk}(locked={tk_locked})"
        loaded = store.load_game_state(tk)
        if not loaded:
            return tk, None, False, f"{tk}(no_state)"
        gs_copy = dict(loaded, waiting_for_others=False)
        advanced = tk_locked > cur_year
        if not advanced:
            store.save_game_state(tk, gs_copy)
        return tk, gs_copy, advanced, None

    with ThreadPoolExecutor(max_workers=max(1, min(MAX_LOAD_WORKERS, len(others))),
                            thread_name_prefix="load_clear") as ex:
        futures = {ex.submit(load_one, tk): tk for tk in others}
        for fut in as_completed(futures):
            try:
                tk, gs_copy, advanced, skip_reason = fut.result()
            except Exception as exc:
                skipped.append(f"{futures[fut]}(err:{exc})")
                continue
            if skip_reason:
                skipped.append(skip_reason)
                continue
            if advanced:
                already_advanced.add(tk)
            states[tk] = gs_copy

    if already_advanced:
        logger.info("[BROADCAST] year=%d teams already advanced: %s", cur_year, sorted(already_advanced))
    logger.info(
        "[BROADCAST] year=%d broadcaster=%s included=%d skipped=%d",
        cur_year, broadcaster, len(states), len(skipped),
    )
    return states, already_advanced


def _attach_final_insights(store, all_states: dict) -> None:
    """After the last year, compute each team's insights and save them with its state."""
    from services.insights import compute_player_insights

    def compute_one(tk, gs):
        try:
            gs['final_insights'] = compute_player_insights(tk, gs, all_states)
        except Exception:
            pass
        return tk, gs

    with ThreadPoolExecutor(max_workers=max(1, min(MAX_LOAD_WORKERS, len(all_states))),
                            thread_name_prefix="insights") as ex:
        futures = [ex.submit(compute_one, tk, gs) for tk, gs in all_states.items()]
        for fut in as_completed(futures):
            try:
                tk, gs = fut.result()
                all_states[tk] = gs
            except Exception:
                pass
    for tk, gs in all_states.items():
        if 'final_insights' in gs:
            try:
                store.save_game_state(tk, gs)
            except Exception:
                pass


@router.post("/lock-year", response_model=LockYearResponse)
async def lock_year(req: LockYearRequest, request: Request):
    """Lock the team's year, then run the all-teams barrier.

    Each team's lock counts toward a shared per-year counter. The request that
    brings it to the number of participating teams broadcasts `all_teams_locked`
    to everyone and starts their next-year timers. If that never happens, a
    watchdog does it after a delay.
    """
    store = get_store()
    manager = request.app.state.manager
    timer_mgr = request.app.state.timer_manager
    loop = asyncio.get_event_loop()
    sim_executor = request.app.state.simulation_executor
    sim_semaphore = request.app.state.sim_semaphore
    broadcast_executor = request.app.state.broadcast_executor

    async with _team_lock_mutex(req.team_key):
        gs = store.load_game_state(req.team_key)
        if not gs:
            return LockYearResponse(status="error", error="No game state found")

        if compute_waiting_for_others(gs):
            already = len(gs.get('locked_allocations', []))
            logger.info("[LOCK DEDUP] %s resent a lock while awaiting the year-%d barrier; ignoring.",
                        req.team_key, already)
            return LockYearResponse(
                status="ok",
                year=already,
                game_state={**gs, "waiting_for_others": True},
                all_teams_locked=False,
            )

        err, resolved_subdecisions = validate_lock_year(
            req.allocations, req.subdecisions, gs, req.team_key,
        )
        if err:
            return LockYearResponse(status="error", error=err.get("error", "Validation failed"))

        async with sim_semaphore:
            result = await loop.run_in_executor(
                sim_executor,
                lambda: execute_lock_year(
                    allocations=req.allocations,
                    subdecisions=resolved_subdecisions,
                    gs=gs,
                    team_key=req.team_key,
                    carryover=req.carryover,
                ),
            )
        cur_year = result["year"]

    # Locking is activity, so refresh the session in the background.
    asyncio.ensure_future(loop.run_in_executor(
        None, lambda: store.activate_session(req.username, req.team_key)
    ))

    await manager.send_to_team(req.team_key, {
        "type": "year_locked",
        "year": cur_year,
        "year_result": result["year_result"],
        "game_state": result["game_state"],
    })

    year_result = result.get("year_result", {})
    vpi = year_result.get("vpi")
    grade = year_result.get("grade")
    text = f"{req.team_key} locked Year {cur_year}"
    if vpi is not None:
        text += f" (VPI {int(vpi)}{f', grade {grade}' if grade else ''})"
    event_bus.emit(
        "year_locked", text=text, team_key=req.team_key, username=req.username,
        year=cur_year, vpi=vpi, grade=grade,
    )

    timer_mgr.stop_timer(req.team_key)
    if result["waiting_for_others"]:
        timer_mgr.pause_team(req.team_key)

    # Participating teams: live sessions, open sockets, and teams that have
    # joined or started playing. The union keeps the total from being
    # undersized while logins are still settling.
    participating_teams = get_logged_in_team_keys(sessions=store.get_all_sessions())
    participating_teams |= set(manager.team_keys)
    try:
        participating_teams |= store.get_joined_teams() | set(store.get_all_locked_years())
    except Exception:
        pass
    total_teams = len(participating_teams)

    everyone_locked = await loop.run_in_executor(
        broadcast_executor,
        lambda: store.increment_lock_counter(cur_year, total_teams) if total_teams > 0 else True,
    )
    logger.debug("[BARRIER] %s year=%d total_teams=%d everyone_locked=%s",
                 req.team_key, cur_year, total_teams, everyone_locked)

    fresh_locked_counts = await loop.run_in_executor(broadcast_executor, store.get_all_locked_years)
    locked_count = sum(1 for tk in participating_teams if fresh_locked_counts.get(tk, -1) >= cur_year)
    await manager.broadcast_all({"type": "lock_progress", "locked": locked_count, "total": total_teams})

    await asyncio.sleep(0.1)  # let the progress message go out before the heavy broadcast

    if not everyone_locked:
        task = asyncio.create_task(_barrier_watchdog(request, cur_year, req.team_key, total_teams))
        _year_watchdogs.setdefault(cur_year, set()).add(task)
        task.add_done_callback(lambda t, y=cur_year: _year_watchdogs.get(y, set()).discard(t))

    response_gs = dict(result["game_state"])
    if everyone_locked:
        response_gs['waiting_for_others'] = False
        store.save_game_state(req.team_key, response_gs)
        await _broadcast_year_complete(
            request, store, cur_year, req.team_key, req.username,
            response_gs, sorted(participating_teams),
        )

    return LockYearResponse(
        status="ok",
        year=cur_year,
        year_result=result["year_result"],
        game_state=response_gs,
        all_teams_locked=everyone_locked,
        blocking_total=total_teams,
        locked_count=locked_count,
    )


async def _broadcast_year_complete(request: Request, store, cur_year: int, broadcaster: str,
                                   username: str, response_gs: dict, team_keys: list[str]):
    """Last locker: send every team its updated state and leaderboard, then start next-year timers."""
    manager = request.app.state.manager
    timer_mgr = request.app.state.timer_manager
    broadcast_executor = request.app.state.broadcast_executor
    loop = asyncio.get_event_loop()
    started = time.perf_counter()

    all_states, advanced_teams = await loop.run_in_executor(
        broadcast_executor,
        lambda: _load_barrier_states(store, cur_year, broadcaster, response_gs, team_keys),
    )
    loaded = time.perf_counter()

    shared_lb = compute_leaderboard_entries(broadcaster, all_game_states=all_states)
    leaderboard_done = time.perf_counter()

    if cur_year >= NP:
        try:
            await loop.run_in_executor(
                broadcast_executor, lambda: _attach_final_insights(store, all_states)
            )
        except Exception as e:
            logger.warning("[INSIGHTS] computation failed for year %d: %s", cur_year, e)

    event_bus.emit(
        "year_complete",
        text=f"Year {cur_year} complete — all teams locked",
        year=cur_year,
        team_count=len(team_keys),
    )

    async def fan_out_one(team_key):
        try:
            payload = all_states.get(team_key)
            if not payload:
                return
            await manager.send_to_team(team_key, {
                "type": "all_teams_locked",
                "year": cur_year,
                "game_state": payload,
                "leaderboard": _with_leaderboard_flag(shared_lb, team_key),
                "triggered_by": broadcaster,
            })
            await manager.send_to_team(team_key, {"type": "blocking_update", "blocking": []})
            timer_mgr.unpause_team(team_key)
            if team_key in advanced_teams:
                return
            if team_key != broadcaster:
                timer_mgr.start_timer(team_key, year_duration(cur_year + 1), cur_year + 1)
            elif not response_gs.get('completed', False):
                next_year = response_gs.get('current_year', cur_year + 1)
                timer_mgr.start_timer(team_key, year_duration(next_year), next_year)
        except Exception:
            pass

    fan_out_start = time.perf_counter()
    await asyncio.gather(*[fan_out_one(tk) for tk in team_keys], return_exceptions=True)
    logger.info(
        "[PERF] year=%d load=%.0fms leaderboard=%.0fms fanout=%.0fms total=%.0fms teams=%d",
        cur_year, (loaded - started) * 1000, (leaderboard_done - loaded) * 1000,
        (time.perf_counter() - fan_out_start) * 1000, (time.perf_counter() - started) * 1000,
        len(team_keys),
    )

    try:
        await loop.run_in_executor(None, lambda: store.mark_broadcast_done(cur_year))
    except Exception:
        pass

    cancelled = _year_watchdogs.pop(cur_year, set())
    for watchdog in cancelled:
        watchdog.cancel()


@router.get("/game-state/{team_key}")
async def get_game_state(team_key: str, request: Request):
    """A team's current game state, with slider constraints and competitors."""
    store = get_store()
    gs = store.load_game_state(team_key)
    if not gs:
        return {"status": "ok", "game_state": None}

    constraints_payload, competitors = _build_game_bundle(gs)
    timer_remaining = 0
    try:
        timer_mgr = request.app.state.timer_manager
        timer_remaining = timer_mgr.get_remaining(team_key)
    except Exception:
        pass

    gs = {**gs, "waiting_for_others": compute_waiting_for_others(gs)}

    return {
        "status": "ok",
        "game_state": {**gs, "timer_remaining": timer_remaining},
        "slider_constraints": constraints_payload,
        "competitors": competitors,
    }


@router.get("/competitors/{play_seed}")
async def get_competitors(play_seed: int):
    """Competitor data for the briefing tab."""
    competitors, _ = get_competitors_data(play_seed)
    return {"competitors": competitors}


@router.get("/sub-decisions")
async def get_sub_decisions_endpoint():
    """Sub-decision options per department."""
    from simulator import get_sub_decisions
    raw = get_sub_decisions()
    result = {}
    for dept_name, dept_data in raw.items():
        if hasattr(dept_data, 'options'):
            opts = {}
            for key, opt in dept_data.options.items():
                if hasattr(opt, 'label'):
                    opts[key] = {
                        'key': key,
                        'label': opt.label,
                        'description': getattr(opt, 'description', ''),
                    }
                else:
                    opts[key] = opt
            result[dept_name] = {
                'label': getattr(dept_data, 'label', dept_name),
                'tooltip': getattr(dept_data, 'tooltip', ''),
                'options': opts,
                'default': getattr(dept_data, 'default', ''),
            }
        elif isinstance(dept_data, dict):
            result[dept_name] = dept_data
    return result


@router.get("/scenario-info")
async def get_scenario_info():
    """Details of the active scenario."""
    result = _build_scenario_info()
    if result is None:
        return {"error": "No scenario loaded"}
    return result


@router.post("/begin-simulation")
async def begin_simulation(request: Request):
    """The controller finished the briefing: start year 1 and tell teammates' clients to advance."""
    body = await request.json()
    team_key = body.get('team_key', '')
    username = body.get('username', '')

    if not team_key:
        raise HTTPException(status_code=400, detail="team_key required")

    timer_mgr = request.app.state.timer_manager

    timer_mgr.stop_storyboard_timer(team_key)

    store = get_store()
    gs = store.load_game_state(team_key)
    if gs and not gs.get('completed', False):
        gs['simulation_begun'] = True
        store.save_game_state(team_key, gs)
        current_year = gs.get('current_year', 1)
        if timer_mgr.get_remaining(team_key) == 0:
            timer_mgr.start_timer(team_key, year_duration(current_year), current_year)

    manager = request.app.state.manager
    await manager.send_to_team(team_key, {
        "type": "storyboard_complete",
        "triggered_by": username,
    })

    return {"status": "ok"}


@router.post("/draft-allocations")
async def draft_allocations(request: Request):
    """Save the controller's unlocked slider and dropdown state.

    Called (debounced) as the controller edits. If the year timer expires, the
    auto-lock uses these values. Intentionally unvalidated so a transient
    out-of-range value while dragging cannot fail; auto-lock clips and scales.

    Body: {team_key, username, allocations: [float per department],
           subdecisions: {department: option key}}
    """
    body = await request.json()
    team_key = body.get('team_key', '')
    allocations = body.get('allocations', None)
    subdecisions = body.get('subdecisions', None)

    if not team_key:
        raise HTTPException(status_code=400, detail="team_key required")

    store = get_store()

    def load_and_save():
        gs = store.load_game_state(team_key)
        if not gs or gs.get('completed', False):
            return False
        if isinstance(allocations, list):
            gs['draft_allocations'] = list(allocations)
        if isinstance(subdecisions, dict):
            gs['draft_subdecisions'] = dict(subdecisions)
        store.save_game_state(team_key, gs)
        return True

    stored = await asyncio.get_event_loop().run_in_executor(None, load_and_save)
    return {"status": "ok", "stored": stored}
