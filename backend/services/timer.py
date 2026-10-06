"""Server-side countdown timers.

Year timers run 30 min for year 1 and 20 min afterwards. The storyboard timer
runs 25 min. When a year timer expires the server locks the year for that team.
Pause state lives in storage, so a pause from any server instance takes effect
on the next tick.
"""
import asyncio
import logging

from services.executors import SIMULATION_EXECUTOR

logger = logging.getLogger("services.timer")

YEAR_1_DURATION = 1800
YEAR_N_DURATION = 1200
STORYBOARD_DURATION = 1500
TICK_SECONDS = 5
PERSIST_EVERY_SECONDS = 30  # how often the remaining time is saved for page-refresh recovery


def year_duration(year: int) -> int:
    return YEAR_1_DURATION if year == 1 else YEAR_N_DURATION


class TimerManager:
    def __init__(self, ws_manager):
        self._ws_manager = ws_manager
        self._tasks: dict[str, asyncio.Task] = {}
        self._remaining: dict[str, int] = {}
        self._paused: dict[str, bool] = {}
        self._global_paused = False  # fallback when storage is unreachable

        self._sb_tasks: dict[str, asyncio.Task] = {}
        self._sb_remaining: dict[str, int] = {}

    # Year timers
    def start_timer(self, team_key: str, duration_seconds: int, year: int):
        """Start (or restart) a team's year countdown."""
        self.stop_timer(team_key)
        self._remaining[team_key] = duration_seconds
        self._paused[team_key] = False
        self._tasks[team_key] = asyncio.create_task(self._run_year_timer(team_key, year))
        logger.info(f"Year timer started for {team_key}: {duration_seconds}s (year {year})")

    def stop_timer(self, team_key: str):
        task = self._tasks.pop(team_key, None)
        if task and not task.done():
            task.cancel()
        self._remaining.pop(team_key, None)
        self._paused.pop(team_key, None)

    def pause_all(self):
        self._global_paused = True

    def unpause_all(self):
        self._global_paused = False

    def pause_team(self, team_key: str):
        self._paused[team_key] = True

    def unpause_team(self, team_key: str):
        self._paused[team_key] = False

    def get_remaining(self, team_key: str) -> int:
        return self._remaining.get(team_key, 0)

    def _is_paused_global(self) -> bool:
        try:
            from auth import get_store
            return get_store().is_paused()
        except Exception:
            return self._global_paused

    async def _tick_all_teams(self, year: int) -> None:
        """Send timer ticks, batching teams with identical (remaining, paused) values.

        Teams running in lockstep collapse into a single broadcast.
        """
        globally_paused = self._is_paused_global()

        groups: dict[tuple, list[str]] = {}
        for tk, rem in list(self._remaining.items()):
            task = self._tasks.get(tk)
            if task is None or task.done():
                continue
            paused = globally_paused or self._paused.get(tk, False)
            groups.setdefault((rem, paused), []).append(tk)

        for (rem, paused), team_keys in groups.items():
            msg = {"type": "timer_tick", "remaining": rem, "year": year, "paused": paused}
            if len(team_keys) == len(self._remaining) and not paused:
                await self._ws_manager.broadcast_all(msg)
            else:
                await asyncio.gather(
                    *[self._ws_manager.send_to_team(tk, msg) for tk in team_keys]
                )

    async def _run_year_timer(self, team_key: str, year: int):
        try:
            while self._remaining.get(team_key, 0) > 0:
                await asyncio.sleep(TICK_SECONDS)

                if self._is_paused_global() or self._paused.get(team_key, False):
                    await self._ws_manager.send_to_team(team_key, {
                        "type": "timer_tick",
                        "remaining": self._remaining.get(team_key, 0),
                        "year": year,
                        "paused": True,
                    })
                    continue

                self._remaining[team_key] = max(0, self._remaining[team_key] - TICK_SECONDS)
                remaining = self._remaining[team_key]

                await self._tick_all_teams(year)

                if remaining % PERSIST_EVERY_SECONDS == 0 and remaining > 0:
                    try:
                        from auth import get_store
                        get_store().patch_game_state_field(team_key, 'timer_remaining', remaining)
                    except Exception as e:
                        logger.warning(f"Timer persist failed for {team_key}: {e}")

                if remaining <= 0:
                    break

            logger.info(f"Year {year} timer expired for {team_key}; auto-locking")
            await self._auto_lock_year(team_key, year)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Year timer error for {team_key}: {e}")

    async def _auto_lock_year(self, team_key: str, year: int):
        """Lock the year with the team's draft allocations when its timer expires.

        Uses the draft saved via /api/draft-allocations, falls back to scenario
        defaults, and mirrors the barrier logic of the manual lock endpoint.
        """
        try:
            from auth import get_store
            from services.game_logic import execute_lock_year, get_slider_constraints

            store = get_store()
            gs = store.load_game_state(team_key)
            if not gs or gs.get('completed'):
                return
            if gs.get('current_year', 1) != year:
                return  # the team already locked this year manually

            constraints = get_slider_constraints(gs)
            dept_names = [c['dept_name'] for c in constraints]
            allocations = self._draft_allocations(gs, constraints, team_key, year)
            subdecisions = self._draft_subdecisions(gs, dept_names)

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                SIMULATION_EXECUTOR,
                lambda: execute_lock_year(
                    allocations=allocations,
                    subdecisions=subdecisions,
                    gs=gs,
                    team_key=team_key,
                    carryover=0.5,
                ),
            )
            new_gs = result.get('game_state', {})

            await self._ws_manager.send_to_team(team_key, {
                "type": "timer_expired",
                "year": year,
                "game_state": new_gs,
            })
            await self._ws_manager.broadcast_all({
                "type": "year_locked",
                "team_key": team_key,
                "year": year,
                "game_state": new_gs,
            })

            # Barrier participants: teams with a live session or an open socket,
            # which avoids an undersized total while logins are still settling.
            all_locked_counts = store.get_all_locked_years()
            participating_teams = {
                s['team_key'] for s in store.get_all_sessions()
                if isinstance(s, dict) and s.get('team_key') and not s.get('logged_out', False)
            }
            participating_teams |= set(self._ws_manager.team_keys)
            participating_teams.add(team_key)

            barrier_total = len(participating_teams)
            locked_count = sum(
                1 for tk in participating_teams if all_locked_counts.get(tk, -1) >= year
            )
            await self._ws_manager.broadcast_all({
                "type": "lock_progress",
                "locked": locked_count,
                "total": barrier_total,
            })

            if store.increment_lock_counter(year, barrier_total):
                await self._broadcast_all_teams_locked(
                    store, participating_teams, team_key, year, new_gs
                )
            else:
                self._start_next_year_timer(team_key, year, new_gs)

        except Exception as e:
            logger.error(f"Auto-lock failed for {team_key} year {year}: {e}")
            await self._ws_manager.send_to_team(team_key, {
                "type": "timer_expired",
                "year": year,
                "game_state": None,
            })

    @staticmethod
    def _draft_allocations(gs: dict, constraints: list, team_key: str, year: int) -> list:
        """Draft allocations clipped to each department's range and the total budget.

        Falls back to scenario defaults when there is no usable draft or the
        draft cannot fit the budget.
        """
        defaults = [c.get('default', c.get('min', 0)) for c in constraints]

        def clip(values):
            return [
                max(c.get('min', 0), min(c.get('max', v), v))
                for c, v in zip(constraints, values)
            ]

        draft = gs.get('draft_allocations')
        if isinstance(draft, list) and len(draft) == len(constraints):
            allocations = clip([float(x) for x in draft])
        else:
            logger.info(f"Auto-lock {team_key} year {year}: no draft, using defaults")
            allocations = clip(defaults)

        available = float(gs.get('available_budget', sum(c.get('default', 0) for c in constraints)))
        total = sum(allocations)
        if total > available and total > 0:
            allocations = clip([a * available / total for a in allocations])
            if sum(allocations) > available + 1.0:  # +1 tolerates float rounding
                logger.warning(
                    f"Auto-lock {team_key} year {year}: draft cannot fit the budget; using defaults"
                )
                allocations = defaults

        return [int(round(a)) for a in allocations]

    @staticmethod
    def _draft_subdecisions(gs: dict, dept_names: list) -> dict:
        """Draft choices, else last year's, with any gaps filled by each department's first option."""
        from simulator import get_sub_decisions

        draft = gs.get('draft_subdecisions')
        if isinstance(draft, dict) and draft:
            subdecisions = dict(draft)
        else:
            previous = gs.get('locked_subdecisions', [])
            subdecisions = dict(previous[-1]) if previous else {}

        sub_decisions = get_sub_decisions()
        for dept_name in dept_names:
            if subdecisions.get(dept_name):
                continue
            sd = sub_decisions.get(dept_name)
            if sd is None:
                continue
            options = sd.get('options', {}) if isinstance(sd, dict) else getattr(sd, 'options', {})
            if options:
                subdecisions[dept_name] = next(iter(options))
        return subdecisions

    async def _broadcast_all_teams_locked(self, store, participating_teams, team_key, year, new_gs):
        """Last locker: release every waiting team and start their next year timer."""
        from leaderboard import compute_leaderboard_entries
        shared_lb = compute_leaderboard_entries(team_key)

        async def send_to_team(tk: str):
            try:
                store.patch_game_state_field(tk, 'waiting_for_others', False)
                tk_gs = dict(store.load_game_state(tk) or {})
                tk_gs['waiting_for_others'] = False

                lb_for_team = [{**e, 'is_you': e['team'] == tk} for e in shared_lb]
                await asyncio.gather(
                    self._ws_manager.send_to_team(tk, {
                        "type": "all_teams_locked",
                        "year": year,
                        "game_state": tk_gs,
                        "leaderboard": lb_for_team,
                    }),
                    self._ws_manager.send_to_team(tk, {"type": "blocking_update", "blocking": []}),
                )
                self.unpause_team(tk)
                if tk != team_key:
                    self.start_timer(tk, year_duration(year + 1), year + 1)
            except Exception:
                pass

        await asyncio.gather(*[send_to_team(tk) for tk in participating_teams])
        self._start_next_year_timer(team_key, year, new_gs)

    def _start_next_year_timer(self, team_key: str, year: int, new_gs: dict):
        if not new_gs.get('completed', False):
            next_year = new_gs.get('current_year', year + 1)
            self.start_timer(team_key, year_duration(next_year), next_year)

    # Storyboard timer
    def start_storyboard_timer(self, team_key: str):
        """Start the team's storyboard countdown. No-op if already running."""
        existing = self._sb_tasks.get(team_key)
        if existing and not existing.done():
            return
        self.stop_storyboard_timer(team_key)
        self._sb_remaining[team_key] = STORYBOARD_DURATION
        self._sb_tasks[team_key] = asyncio.create_task(self._run_storyboard_timer(team_key))
        logger.info(f"Storyboard timer started for {team_key}")

    def stop_storyboard_timer(self, team_key: str):
        task = self._sb_tasks.pop(team_key, None)
        if task and not task.done():
            task.cancel()
        self._sb_remaining.pop(team_key, None)

    def get_storyboard_remaining(self, team_key: str) -> int:
        return self._sb_remaining.get(team_key, 0)

    async def _run_storyboard_timer(self, team_key: str):
        try:
            while self._sb_remaining.get(team_key, 0) > 0:
                await asyncio.sleep(TICK_SECONDS)
                self._sb_remaining[team_key] = max(0, self._sb_remaining[team_key] - TICK_SECONDS)
                remaining = self._sb_remaining[team_key]

                await self._ws_manager.send_to_team(team_key, {
                    "type": "storyboard_tick",
                    "remaining": remaining,
                })
                if remaining <= 0:
                    break

            logger.info(f"Storyboard timer expired for {team_key}")

            # Expiry behaves like clicking "Begin Simulation": start the simulation and year 1 timer.
            try:
                from auth import get_store
                store = get_store()
                gs = store.load_game_state(team_key)
                if gs and not gs.get('completed', False) and not gs.get('simulation_begun', False):
                    gs['simulation_begun'] = True
                    store.save_game_state(team_key, gs)
                    current_year = gs.get('current_year', 1)
                    if self.get_remaining(team_key) == 0:
                        self.start_timer(team_key, year_duration(current_year), current_year)
            except Exception as e:
                logger.warning(f"Failed to start year timer after storyboard expiry for {team_key}: {e}")

            await self._ws_manager.send_to_team(team_key, {"type": "storyboard_expired"})

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Storyboard timer error for {team_key}: {e}")
