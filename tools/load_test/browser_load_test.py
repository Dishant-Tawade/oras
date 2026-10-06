"""Browser-driven load test for ORAS.

Starts one Chromium context per user (teams x users per team), drives the real
frontend through login, storyboard and every year of the game, and logs
events to a JSONL file for analyze_events.py.

Slot 1 of each team is the controller (user_team_N); the rest are viewers
(viewer_K_team_N). Usernames, the password "password" and the team keys match
backend/seed_users.json.

A reload check runs for ORAS_RELOAD_TEAM (default team 1; 0 disables): after
each lock the controller reloads the page and the waiting banner must survive,
so a refresh never advances a team before all teams have locked.

Setup and run (backend and frontend running, see the README):
    pip install playwright
    playwright install chromium
    python browser_load_test.py
    python analyze_events.py events.jsonl

Environment: ORAS_HOST, ORAS_TEAMS, ORAS_USERS_PER_TEAM, ORAS_NUM_YEARS,
ORAS_EVENT_LOG, ORAS_LOCK_DELAY_MIN/MAX, ORAS_RELOAD, ORAS_RELOAD_TEAM.
"""

import asyncio
import json
import os
import random
import time

from playwright.async_api import async_playwright, Page, TimeoutError as PWTimeout

# Configuration
HOST = os.environ.get("ORAS_HOST", "http://localhost:8080")
NUM_TEAMS        = int(os.environ.get("ORAS_TEAMS", "6"))
USERS_PER_TEAM   = int(os.environ.get("ORAS_USERS_PER_TEAM", "4"))  # slot 1 = controller,
                                                                   # slots 2+ = viewers.
                                                                   # Set to 1 for controllers-only runs.
NUM_YEARS        = int(os.environ.get("ORAS_NUM_YEARS", "5"))
PASSWORD         = "password"
SPAWN_INTERVAL_S = 0.5   # stagger context spawn so we don't slam login
OUT_PATH         = os.environ.get("ORAS_EVENT_LOG", "events.jsonl")

# Lock timing: each controller waits a random think-time in this window before
# locking each year. Tighten the window to CLUSTER locks for barrier-contention
# stress tests — e.g. ORAS_LOCK_DELAY_MIN=0.2 ORAS_LOCK_DELAY_MAX=1.0 makes all
# teams lock within ~1s of each other (they enter each year together on the
# all_teams_locked broadcast, then wait this jitter). Default is a wide,
# realistic 8–25s spread.
LOCK_DELAY_MIN   = float(os.environ.get("ORAS_LOCK_DELAY_MIN", "8"))
LOCK_DELAY_MAX   = float(os.environ.get("ORAS_LOCK_DELAY_MAX", "25"))
LOCK_DELAY_RANGE = (LOCK_DELAY_MIN, LOCK_DELAY_MAX)

_WAITING_JS = (
    "(document.body.innerText.includes('teams locked in') || "
    "document.body.innerText.includes('Waiting for other teams to lock'))"
)

# Refresh (reload) test
# Master switch for refresh testing. When ON (default), the controller for
# RELOAD_TEST_TEAM reloads the page immediately after each lock and asserts the
# waiting banner survives (i.e. a refresh never sails a team past the barrier
# into year N+1 before all teams have locked year N). The assertion self-skips
# on any year where that team was the LAST to lock, so it never false-fails on
# the last-locker race.
# Set ORAS_RELOAD=0 to disable refreshing entirely — nobody reloads, and the
# early-lock bias on the reload team is removed too. Use this for a pure
# barrier-contention stress test (combine with a tight LOCK_DELAY window so
# many teams lock within ~1s):
#     ORAS_RELOAD=0 ORAS_LOCK_DELAY_MIN=0.2 ORAS_LOCK_DELAY_MAX=1.0 \
#         ORAS_TEAMS=8 python3 playwright_oras.py
RELOAD_ENABLED   = os.environ.get("ORAS_RELOAD", "1") != "0"
RELOAD_TEST_TEAM = (
    int(os.environ.get("ORAS_RELOAD_TEAM", "1")) if RELOAD_ENABLED else 0
)

# Event log
EVENTS: list[dict] = []
EVT_LOCK = asyncio.Lock()
_LOG_FILE: object = None  # opened in main() before any tasks spawn

async def log(**kw):
    async with EVT_LOCK:
        entry = {"ts": time.monotonic(), **kw}
        EVENTS.append(entry)
        # Write incrementally so Ctrl+C always leaves a valid file
        if _LOG_FILE is not None:
            _LOG_FILE.write(json.dumps(entry) + "\n")
            _LOG_FILE.flush()


# Per-user driver
async def run_user(browser, team_num: int, slot: int, controller_done_evt: dict,
                   controller_ready: asyncio.Event,
                   all_controllers_ready: asyncio.Event,
                   controller_ready_events: dict,
                   controller_begun_events: dict | None = None,
                   all_controllers_begun: asyncio.Event | None = None,
                   final_atl_event: asyncio.Event | None = None):
    """
    team_num: 1..NUM_TEAMS
    slot:     1..4   (slot 1 is controller — must login before viewers to claim role)
    controller_done_evt: dict[year -> asyncio.Event] per team — viewers wait
                         on this to know the controller has finished a year.
                         (Not strictly needed; viewers just hold the page and
                         the WS handler logs everything. Included for clarity.)
    """
    team_key = f"team_{team_num}"
    is_intended_controller = (slot == 1)
    username = f"user_team_{team_num}" if is_intended_controller else f"viewer_{slot - 1}_team_{team_num}"

    ctx = await browser.new_context(
        viewport={"width": 1280, "height": 800},
        # Block heavy assets — we don't need them for a load test.
        # This is a critical optimization for 16GB RAM machines.
    )
    await ctx.route(
        "**/*.{png,jpg,jpeg,gif,svg,webp,woff,woff2,ttf,otf,mp3,mp4,wav}",
        lambda r: r.abort(),
    )
    page = await ctx.new_page()

    # WS frame capture — the most accurate barrier measurement
    def on_ws(ws):
        def on_frame(payload):
            try:
                msg = json.loads(payload)
            except Exception:
                return
            mtype = msg.get("type")
            year = msg.get("year")
            asyncio.create_task(log(
                team_key=team_key, username=username,
                role="controller" if is_intended_controller else "viewer",
                kind="ws_msg", msg_type=mtype, year=year,
            ))
            # Signal viewers to exit once the final year's broadcast lands.
            if (final_atl_event is not None
                    and mtype == "all_teams_locked"
                    and year == NUM_YEARS):
                final_atl_event.set()
        ws.on("framereceived", on_frame)
    page.on("websocket", on_ws)

    # Surface page errors as events so the analyzer can see them
    page.on("pageerror", lambda exc: asyncio.create_task(log(
        team_key=team_key, username=username, kind="page_error", err=str(exc),
    )))

    try:
        await log(team_key=team_key, username=username,
                  role="controller" if is_intended_controller else "viewer",
                  kind="spawn_start")

        await page.goto(HOST, wait_until="domcontentloaded", timeout=60_000)

        # 1. Welcome page → "Enter Platform"
        try:
            await page.get_by_role("button", name="Enter Platform").click(timeout=10_000)
        except PWTimeout:
            # Already past welcome (saved auth or different entry) — fine
            pass

        # 2. Login form
        # Viewers wait here until the controller has completed its login and
        # claimed the controller role.  Without this gate, a viewer's login
        # POST can arrive at the backend before the controller's if the page
        # loads slowly, causing the viewer to win the claim_controller race
        # and the intended controller to be demoted to viewer.
        if not is_intended_controller:
            try:
                await asyncio.wait_for(controller_ready.wait(), timeout=60)
            except asyncio.TimeoutError:
                await log(team_key=team_key, username=username,
                          kind="error", err="timed_out_waiting_for_controller_login")
                return

        # Re-try login up to 3 times.  With many teams logging in concurrently
        # the server occasionally returns a transient error; the React form
        # shows it as "incorrect login details" even though credentials are
        # correct.  Detecting success via the landing page button avoids
        # relying solely on the DOM value check (which passes before the
        # server has responded).
        for _login_attempt in range(3):
            await page.get_by_placeholder("your_name").fill(username, timeout=15_000)
            # Password field has no placeholder — locate by type
            await page.locator('input[type="password"]').first.fill(PASSWORD)
            await page.get_by_placeholder("TEAM-XXX").fill(team_key)
            # Confirm all three values are in the DOM before clicking
            await page.wait_for_function(
                f"""() => {{
                    const inputs = document.querySelectorAll('input');
                    const vals = Array.from(inputs).map(i => i.value);
                    return vals.some(v => v === {repr(username)})
                        && vals.some(v => v === {repr(PASSWORD)})
                        && vals.some(v => v === {repr(team_key)})
                }}""",
                timeout=5_000,
            )
            await page.get_by_role("button", name="Sign In", exact=True).first.click()
            # Landing page appears on success; if login failed the form stays
            # visible and we retry with exponential backoff.
            try:
                await page.wait_for_selector(
                    "button:has-text('Start Simulation'), button:has-text('Resume Simulation')",
                    timeout=10_000,
                )
                break  # success
            except PWTimeout:
                await log(team_key=team_key, username=username,
                          kind="login_retry", err=f"attempt {_login_attempt + 1}")
                await asyncio.sleep(2 ** _login_attempt)   # 1s, 2s, 4s backoff
        await log(team_key=team_key, username=username, kind="logged_in")

        # Controller sets the event so viewers can proceed to login.
        # Also check if ALL controllers are now ready, and if so fire the
        # all_controllers_ready event so no one starts the game prematurely.
        if is_intended_controller:
            controller_ready.set()
            if all(e.is_set() for e in controller_ready_events.values()):
                all_controllers_ready.set()
                # Verifiable marker: the moment EVERY controller has completed a
                # successful login. No lock can occur before this timestamp —
                # the gate below blocks Start until it fires, and Start precedes
                # storyboard → begin → lock. Mirrors the real deployment, where
                # the ~15-minute storyboard guarantees all teams have logged in
                # long before anyone locks Year 1, so no team logs in mid-sim.
                await log(team_key=team_key, username=username,
                          kind="all_controllers_logged_in",
                          note=f"{len(controller_ready_events)} controllers "
                               f"logged in — locking may now begin")

        # 3. Landing page → "Start Simulation" (or "Resume Simulation") ──
        # Wait for ALL controllers to have logged in before any of them
        # clicks Start Simulation — otherwise fast controllers start the game
        # while slow-spawning users are still on the login form.
        if is_intended_controller:
            try:
                await asyncio.wait_for(all_controllers_ready.wait(), timeout=300)
            except asyncio.TimeoutError:
                await log(team_key=team_key, username=username,
                          kind="error", err="timed_out_waiting_for_all_controllers")
                return

        try:
            await page.get_by_role("button", name="Start Simulation").click(timeout=60_000)
        except PWTimeout:
            try:
                await page.get_by_role("button", name="Resume Simulation").click(timeout=5_000)
            except PWTimeout:
                pass

        # Detect where we actually landed.  If simulation_begun=True is
        # already in the server-side game state from a previous run, the
        # React WS handler calls onReady() immediately on connect and the
        # app skips to GamePage without ever showing the storyboard.  We
        # must detect this before running any storyboard code, otherwise
        # the controller times out waiting for "Skip all" that will never
        # appear on the game page.
        try:
            await page.wait_for_selector(
                ".oras-tab, button:has-text('Skip all')", timeout=60_000
            )
        except PWTimeout:
            pass

        on_game_page = bool(await page.query_selector(".oras-tab"))

        # 4. Storyboard
        if on_game_page:
            # Already past the storyboard (auto-advanced via WS on-connect).
            # Nothing to do here — fall straight through to step 5.
            await log(team_key=team_key, username=username,
                      kind="storyboard_skipped_server_state")
        elif is_intended_controller:
            # Storyboard is showing — skip to the last slide and begin.
            # page.evaluate fires the click directly on the DOM node;
            # get_by_role().click() can miss inside an animating container.
            await page.evaluate("""() => {
                const btn = Array.from(document.querySelectorAll('button'))
                    .find(b => b.textContent.trim() === 'Skip all');
                if (btn) btn.click();
            }""")

            # With skipped=true the typewriter completes instantly and
            # FinalCTA renders immediately — wait to confirm before clicking.
            await page.wait_for_selector(
                "button:has-text('Begin Simulation')", timeout=60_000
            )
            await page.get_by_role("button", name="Begin Simulation").click(timeout=60_000)
            await log(team_key=team_key, username=username, kind="begin_simulation")
        else:
            # Viewer on storyboard — normally auto-advances when the controller
            # clicks Begin Simulation (storyboard_complete broadcast). But that
            # broadcast only reaches viewers whose WS is connected at that
            # instant. A viewer that reaches the storyboard AFTER the controller
            # began misses it, and game_state_update on reconnect does NOT carry
            # simulation_begun into the storyboard view — so the viewer would
            # sit here until the 300s timeout. Give the broadcast a short grace
            # window; if still on the storyboard, self-advance the same way the
            # controller does. For a viewer the "Begin Simulation" handler is
            # purely client-side (it only calls the API when is_controller), so
            # this just flips the viewer into the game with no server effect —
            # removing the missed-broadcast race entirely.
            await log(team_key=team_key, username=username, kind="viewer_waiting_storyboard")
            try:
                await page.wait_for_selector(".oras-tab", timeout=20_000)
            except PWTimeout:
                if not await page.query_selector(".oras-tab"):
                    await page.evaluate("""() => {
                        const btn = Array.from(document.querySelectorAll('button'))
                            .find(b => b.textContent.trim() === 'Skip all');
                        if (btn) btn.click();
                    }""")
                    try:
                        await page.wait_for_selector(
                            "button:has-text('Begin Simulation')", timeout=30_000)
                        await page.get_by_role(
                            "button", name="Begin Simulation").click(timeout=30_000)
                        await log(team_key=team_key, username=username,
                                  kind="viewer_self_skipped_storyboard")
                    except Exception as _vs_err:
                        await log(team_key=team_key, username=username,
                                  kind="error",
                                  err=f"viewer_self_skip_failed: "
                                      f"{type(_vs_err).__name__}: {_vs_err}")

        await page.wait_for_selector(".oras-tab", timeout=300_000)
        await log(team_key=team_key, username=username, kind="game_page_ready")

        # 5b. Barrier: no controller locks Year 1 until ALL controllers have
        #        BEGUN (reached the game page, so their game state is persisted).
        # all_controllers_ready only gates LOGIN. After it releases, controllers
        # race independently through storyboard → begin → Year 1 lock. With a
        # tight think-time the first team can lock Year 1 before the last team
        # has finished writing its game state — so the server's begun-teams
        # barrier denominator reads fewer than the full cohort and the Year 1
        # threshold is set too low, letting an early subset advance before
        # everyone has locked. Holding every controller here until all have begun
        # makes the cohort fully assembled (all game states written) before any
        # Year 1 lock, so the denominator is correct. (Real classrooms never hit
        # this — teams begin minutes before locking — it's a stress-test
        # artifact of joining and locking within ~1s.)
        if is_intended_controller and controller_begun_events is not None:
            controller_begun_events[team_num].set()
            if all(e.is_set() for e in controller_begun_events.values()):
                all_controllers_begun.set()
                # Verifiable marker: every controller has reached the sim (logged
                # in AND begun). The first lock cannot precede this timestamp.
                await log(team_key=team_key, username=username,
                          kind="all_controllers_begun",
                          note=f"{len(controller_begun_events)} controllers in "
                               f"the sim — first lock may now occur")
            try:
                await asyncio.wait_for(all_controllers_begun.wait(), timeout=300)
            except asyncio.TimeoutError:
                await log(team_key=team_key, username=username,
                          kind="error",
                          err="timeout waiting for all controllers to begin")

        # 6. Drive the game
        if is_intended_controller:
            await drive_controller(page, team_key, username, team_num=team_num)
        else:
            await be_viewer(page, team_key, username, final_atl_event)

    except Exception as e:
        await log(team_key=team_key, username=username,
                  kind="error", err=f"{type(e).__name__}: {e}")
    finally:
        # Close the context first — this drops the WebSocket immediately,
        # stopping heartbeats. Then logout to mark the session as logged_out.
        # Order matters: closing first means no heartbeat can revive the session
        # between the logout call and the WS dropping.
        try:
            await ctx.close()
        except Exception:
            pass
        # Logout via a fresh aiohttp-style request using the browser's
        # API request context is gone after ctx.close(), so use a plain
        # asyncio approach instead.
        try:
            import urllib.request as _urllib
            import json as _json
            def _do_logout():
                _req = _urllib.Request(
                    f"{HOST}/api/logout",
                    data=_json.dumps({"username": username, "team_key": team_key}).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                _urllib.urlopen(_req, timeout=5)
            await asyncio.get_event_loop().run_in_executor(None, _do_logout)
        except Exception:
            pass


async def assert_waiting_banner_persists_after_reload(
        page: Page, team_key: str, username: str, year: int):
    """Regression test for the reload-advances-past-barrier bug.

    Call site: right after this team locked `year` (hold button gone, lock
    HTTP committed) but BEFORE the all_teams_locked broadcast advances it.

    The waiting overlay (YearTransitionOverlay with persist=true) shows the
    text "Waiting for other teams to lock in…". current_year is already N+1 in
    the persisted state at this point, so the ONLY thing keeping the team off
    the year N+1 UI is the recomputed waiting flag. The historical bug: the
    Firestore backend strips waiting_for_others on save, so a reload reloaded
    a state that read current_year=N+1 with no waiting flag and dropped the
    team straight into year N+1 ahead of the barrier. This asserts the flag is
    rebuilt on both read paths (HTTP game-state + WS reconnect) so the banner
    survives a reload.

    Self-guarding: if the overlay is NOT showing shortly after the lock, this
    team was the last locker and already advanced — there is nothing to wait
    for, so the reload assertion is N/A and we skip (not fail).
    """
    # 1. Confirm the overlay is up before we reload. If it never appears within
    #    a short window, this team was (almost certainly) the last to lock and
    #    advanced immediately — skip rather than false-fail.
    try:
        await page.wait_for_function(
            f"""() => {_WAITING_JS}""",
            timeout=8_000,
        )
    except Exception:
        await log(team_key=team_key, username=username,
                  kind="reload_test_skipped", year=year,
                  note="overlay not showing pre-reload (last locker?)")
        return

    await log(team_key=team_key, username=username,
              kind="reload_test_begin", year=year)

    # 2. Hard reload — this re-runs the HTTP /game-state fetch on mount AND a
    #    fresh WebSocket connect, the two read paths that must recompute the
    #    waiting flag from the monotonic broadcast slot.
    try:
        await page.reload(wait_until="domcontentloaded", timeout=60_000)
    except Exception as e:
        await log(team_key=team_key, username=username,
                  kind="reload_test_error", year=year,
                  err=f"reload_failed: {type(e).__name__}: {e}")
        return

    # 2b. On reload the app always routes to the Landing page; the real user
    #     clicks "Resume Simulation" to re-enter the game. Replicate that. A
    #     team mid-barrier has locked progress, so Landing shows Resume (not
    #     Start). If "Start Simulation" shows instead, progress was lost — that
    #     is itself a failure, captured below when the banner check times out.
    try:
        await page.get_by_role(
            "button", name="Resume Simulation").click(timeout=30_000)
    except Exception as e:
        await log(team_key=team_key, username=username,
                  kind="reload_test_error", year=year,
                  err=f"resume_button_missing: {type(e).__name__}: {e}")
        return

    # 3. Back in the game, the waiting banner must be shown (30s covers page mount and WS reconnect).
    try:
        await page.wait_for_function(
            f"""() => {_WAITING_JS}""",
            timeout=30_000,
        )
    except Exception:
        # FAILURE: banner did not survive the reload. Capture what's on screen
        # (and whether the year N+1 allocate UI is exposed) for the analyzer.
        body_excerpt = ""
        alloc_exposed = False
        try:
            body_excerpt = (await page.inner_text("body"))[:500]
            alloc_exposed = bool(await page.query_selector(".alloc-card")) or \
                bool(await page.query_selector('button:has-text("Allocate & Decide")'))
        except Exception:
            pass
        await log(team_key=team_key, username=username,
                  kind="reload_test_fail", year=year,
                  note="waiting banner did NOT persist after reload — team advanced past barrier",
                  alloc_ui_exposed=alloc_exposed,
                  body_excerpt=body_excerpt)
        return

    # 4. Belt-and-suspenders: the banner is up; confirm the team is NOT
    #    simultaneously able to interact with a fresh year N+1 allocation.
    #    (The Year N+1 heading legitimately renders behind the overlay, so we
    #    check for an *interactive* allocate surface, not the year number.)
    alloc_exposed = False
    try:
        alloc_card = await page.query_selector(".alloc-card")
        alloc_exposed = bool(alloc_card and await alloc_card.is_visible())
    except Exception:
        pass

    await log(team_key=team_key, username=username,
              kind="reload_test_pass", year=year,
              alloc_ui_exposed=alloc_exposed)


async def drive_controller(page: Page, team_key: str, username: str,
                           team_num: int = 0):
    """Click through 5 years of locks. Each year: wait, slide some sliders,
    Review & Seal, hold-to-seal for 1.2s, wait for all_teams_locked broadcast
    to advance us to year+1, repeat."""
    for year in range(1, NUM_YEARS + 1):
        # Minimum think time before locking each year. Without this, teams
        # that receive the previous year's all_teams_locked via the late-joiner
        # path (instant HTTP response) immediately advance and lock the next year
        # before the barrier has propagated to all other teams — causing the
        # next year's barrier to fire at a lower total_teams count.
        # Real students take at least 30s to review allocations. 5s here is
        # conservative but enough to ensure the previous year's barrier has
        # fully propagated before the next lock burst begins.
        if year > 1:
            await asyncio.sleep(5)

        # Navigate to the Allocate & Decide tab.
        # The driver must also notice if the game has already COMPLETED while it
        # was mid-transition — e.g. the server auto-locked this team's year on
        # timer expiry, so the barrier released and the FinalInsights screen
        # ("Simulation Complete") replaced the tab bar. In that case .alloc-card
        # will never appear, and without an early-out the driver would block on
        # the 60s .alloc-card timeout, logging a spurious allocate_tab_not_found
        # AND holding teardown open for ~a minute (the script can't end until
        # every controller task returns).
        async def _game_complete():
            try:
                return await page.evaluate(
                    "() => document.body.innerText.includes('Simulation Complete')")
            except Exception:
                return False

        # Already over before we even try — exit cleanly.
        if await _game_complete():
            await log(team_key=team_key, username=username,
                      kind="game_completed_early", year=year,
                      note="completion screen present before allocate tab — "
                           "server auto-locked this team; exiting controller")
            return

        # Click the tab (short timeout — the tab bar renders fast; if the button
        # is gone it's because completion replaced it, so tolerate failure and
        # let the combined wait below decide).
        try:
            await page.get_by_role(
                "button", name="Allocate & Decide", exact=True).click(timeout=15_000)
        except PWTimeout:
            pass

        # Resolve as soon as EITHER the allocate surface renders (normal path)
        # OR the game completes underneath us (auto-lock during the transition).
        try:
            await page.wait_for_function(
                """() => !!document.querySelector('.alloc-card')
                        || document.body.innerText.includes('Simulation Complete')""",
                timeout=45_000,
            )
        except PWTimeout:
            await log(team_key=team_key, username=username,
                      kind="error", year=year, err="allocate_tab_not_found")
            return

        # Completion won the race — nothing left to drive, exit promptly.
        if await _game_complete():
            await log(team_key=team_key, username=username,
                      kind="game_completed_early", year=year,
                      note="game completed while waiting for allocate tab "
                           "(server auto-locked this team); exiting controller")
            return

        await log(team_key=team_key, username=username,
                  kind="tab_navigated", year=year, tab="allocate")

        # Think time before locking (jitter so controllers don't all hit at once).
        # When refresh testing is on, the designated reload-test team deliberately
        # locks EARLY — strictly before the random window's lower bound — so it is
        # reliably NOT the last locker. That guarantees the waiting overlay appears
        # after its lock, so the reload assertion fires every year instead of
        # self-skipping. Scaling off LOCK_DELAY_MIN keeps it non-last even when the
        # window is tightened for a clustering stress test. (When ORAS_RELOAD=0,
        # RELOAD_TEST_TEAM is 0, so no team is biased and every team draws from the
        # window — which is what clusters the locks.)
        if RELOAD_TEST_TEAM and team_num == RELOAD_TEST_TEAM:
            delay = max(0.1, min(3.0, LOCK_DELAY_MIN * 0.5))
        else:
            delay = random.uniform(*LOCK_DELAY_RANGE)
        await log(team_key=team_key, username=username,
                  kind="thinking", year=year, delay_s=round(delay, 2))
        await asyncio.sleep(delay)

        # Slider nudge removed: `value + 1` overflows for teams whose default
        # allocation already equals the budget (totalSpend > budget →
        # overBudget=true → canSeal=false → R&S disabled for 30s → quit).
        # The draft auto-saves via AllocateTab's useEffect([sliderValues,
        # subdecisions]) whenever year hydration runs, so no nudge is needed.

        # Pick a strategy for every department card.
        # canSeal (which gates "Review & Seal") requires allStrategiesSet —
        # every dept must have a subdecision chosen before the button is
        # enabled. We click the first .strategy-option inside each .dept-card.
        # Using evaluate so all four clicks happen synchronously before React
        # re-renders, avoiding a race where one click triggers a re-render
        # that repositions the next target.
        try:
            # Wait for dept cards (year 2+ re-fetches slider_constraints).
            # Then sleep so the year-change useEffect([currentYear]) has run
            # before we click — the effect can call setSubdecisions({}) after
            # the DOM commits but before our evaluate, wiping what we select.
            await page.wait_for_selector(".strategy-option", timeout=60_000)
            await asyncio.sleep(0.5)
            await page.evaluate("""() => {
                const cards = document.querySelectorAll('.dept-card');
                for (const card of cards) {
                    const opts = card.querySelectorAll('.strategy-option');
                    if (opts.length > 0) opts[0].click();
                }
            }""")
            # Wait for React to flush the subdecision state so canSeal becomes
            # true before we attempt the Review & Seal click.
            await page.wait_for_function(
                "() => !!Array.from(document.querySelectorAll('button'))"
                ".find(b => b.textContent.trim() === 'Review & Seal' && !b.disabled)",
                timeout=30_000,
            )
        except Exception:
            pass  # best-effort; Review & Seal click will surface any failure

        # Click "Review & Seal" to open the confirmation modal
        try:
            await page.get_by_role("button", name="Review & Seal").click(timeout=90_000)
        except PWTimeout:
            await log(team_key=team_key, username=username,
                      kind="error", year=year, err="review_seal_not_found")
            return

        # Hold-to-Seal
        # Strategy: fire the realistic KeyboardEvent hold first (onKeyDown →
        # start() → RAF), then drive completion via the React onComplete prop
        # in a short retry loop. RAF is unreliable for non-foreground contexts
        # and handleSeal can transiently reject on !canSeal, so a single shot
        # isn't enough — the loop rides through both. Re-firing is safe: the
        # first accepted handleSeal sets locking=true, which no-ops the rest.
        # tabIndex===0 wait ensures canSeal=true and disabled=false before we
        # attempt anything; a blocking_update WS message can set disabled=true
        # after the modal opens.
        seal_btn = page.locator('[role="button"][aria-label^="Hold to Seal"]')
        try:
            await seal_btn.wait_for(state="visible", timeout=10_000)
            await asyncio.sleep(0.35)         # let allocSlideUp (220ms) finish
            await page.wait_for_function(
                """() => {
                    const b = document.querySelector(
                        '[role="button"][aria-label^="Hold to Seal"]')
                    return b && b.tabIndex === 0
                }""",
                timeout=90_000,
            )
            await log(team_key=team_key, username=username,
                      kind="lock_hold_start", year=year)

            # Attempt 1: KeyboardEvent dispatch
            await page.evaluate("""() => {
                const b = document.querySelector(
                    '[role="button"][aria-label^="Hold to Seal"]')
                if (!b) throw new Error('seal button not found')
                b.dispatchEvent(new KeyboardEvent('keydown', {
                    key: ' ', code: 'Space',
                    bubbles: true, cancelable: true, repeat: false
                }))
            }""")
            await asyncio.sleep(1.6)   # foreground RAF completes the hold in
                                       # 1.1s; small margin before releasing
            await page.evaluate("""() => {
                const b = document.querySelector(
                    '[role="button"][aria-label^="Hold to Seal"]')
                if (b) b.dispatchEvent(new KeyboardEvent('keyup', {
                    key: ' ', code: 'Space', bubbles: true, cancelable: true
                }))
            }""")

            # Seal completion: fiber onComplete with retries
            # requestAnimationFrame is throttled or frozen for any browser
            # context that isn't the foreground tab, so the keydown hold above
            # frequently never reaches HOLD_MS — exactly the contexts that
            # need help. Drive completion directly via the React onComplete
            # prop (handleSeal), which is equivalent to a full-duration hold.
            # Why a RETRY loop, not a single shot:
            #   handleSeal bails on `if (!canSeal) return`, and
            #     canSeal = isController && !overBudget && allStrategiesSet
            #               && !(blocking?.length > 0) && !locking
            #   A blocking_update WS frame can flip blocking non-empty for a
            #   moment right as we fire, so a single onComplete can be silently
            #   dropped — leaving the team "sealed"-looking but unlocked. The
            #   RAF tick sets phase='sealed' BEFORE calling onComplete, so the
            #   button can even read "Year N Sealed" while no lock happened.
            #   Re-firing every ~1.2s rides through those transient windows.
            # Why re-firing is SAFE (no double-lock): the first accepted
            # handleSeal sets locking=true synchronously, which makes canSeal
            # false, so every subsequent onComplete no-ops until the modal
            # closes. (This is also why the old `/Sealed/i` guard was wrong —
            # it blocked the legitimate retry while the locking flag already
            # prevented double-submit.)
            # Identify THIS year's seal button by its exact aria-label
            # ("Hold to Seal Year N", from AllocateTab). Matching it is itself
            # the "still on the right year" guard: if the UI had advanced past
            # year N, this button would be gone. Crucially this works for
            # EVERY year — including Year 1, where the "Year N of 5" hero text
            # does NOT exist (it lives in the dashboard hero bar, which only
            # renders once hasResults is true, i.e. from Year 2 on). The
            # previous body-text guard therefore rejected every onComplete on
            # Year 1, so any context whose RAF was throttled never locked Year 1.
            seal_label = f"Hold to Seal Year {year}"
            fired_fallback = False
            for _attempt in range(8):
                modal_gone = await page.evaluate(
                    """(lbl) => !document.querySelector('[aria-label="' + lbl + '"]')""",
                    seal_label)
                if modal_gone:
                    break
                if not fired_fallback:
                    fired_fallback = True
                    await log(team_key=team_key, username=username,
                              kind="hold_fiber_fallback", year=year)
                await page.evaluate("""(lbl) => {
                    const b = document.querySelector('[aria-label="' + lbl + '"]')
                    if (!b) return  // modal gone / advanced — nothing to seal
                    const fk = Object.keys(b).find(
                        k => k.startsWith('__reactFiber') ||
                             k.startsWith('__reactInternalInstance'))
                    if (!fk) return
                    let node = b[fk]
                    while (node) {
                        if (node.memoizedProps &&
                            typeof node.memoizedProps.onComplete === 'function') {
                            node.memoizedProps.onComplete()
                            return
                        }
                        node = node.return
                    }
                }""", seal_label)
                await asyncio.sleep(1.2)

            # Wait for the modal to close — that happens in handleSeal's
            # finally block after the lock HTTP response arrives.
            # Logging lock_hold_end HERE (not before) means the timestamp
            # reflects the actual API completion, so the analyzer's invariant
            # check (all_teams_locked arrives after lock_hold_end) is correct.
            await page.wait_for_function(
                """(lbl) => !document.querySelector('[aria-label="' + lbl + '"]')""",
                arg=seal_label,
                timeout=360_000,  # broadcaster runs _load_and_clear_all + insights for all 32 teams
                                  # measured at up to 204s in production — 360s gives safe headroom
            )
            await log(team_key=team_key, username=username,
                      kind="lock_hold_end", year=year)
        except Exception as e:
            await log(team_key=team_key, username=username,
                      kind="error", year=year, err=f"hold_failed: {e}")
            return

        if RELOAD_TEST_TEAM and team_num == RELOAD_TEST_TEAM:
            await assert_waiting_banner_persists_after_reload(
                page, team_key, username, year)

        # Wait for advancement: year display flips to year+1
        # Match the header text "Year N of 5" specifically, not any occurrence
        # of "Year N+1" anywhere in the body.  The AllocateTab renders text
        # like "revenue in Year {currentYear+1}" in strategy tooltips, which
        # means body.innerText already contains "Year N+1" while the team is
        # still on year N — causing the check to resolve immediately and the
        # controller to attempt locking the wrong year.
        # The heading format is "Year N of 5" (GamePage.jsx line 435).
        # For year 5 we also accept Final/Insights/Game Complete.
        # Late-joiner guard: if this team received the Year N barrier BEFORE
        # locking (e.g. team locked Year 1 and Year 2 simultaneously because
        # it was the last to lock Year 1 and the barrier had already fired),
        # the page already shows Year N+1 when this check runs. In that case
        # wait for the waiting overlay to clear for Year N+1 before continuing;
        # otherwise the next iteration tries to lock a year that is already locked.
        try:
            await page.wait_for_function(
                f"""() => {{
                    if (/\\bYear {year + 1} of \\d\\b/.test(document.body.innerText))
                        return true;
                    return /Final|Insights|Game Complete/i.test(document.body.innerText);
                }}""",
                timeout=300_000,
            )
            # Extra guard: wait for the waiting overlay to clear before
            # proceeding. If this team is a late-joiner that already advanced,
            # the overlay may still be showing for Year N+1. Without this wait,
            # the next loop iteration clicks Allocate & Decide and tries to lock
            # Year N+1 which was already locked — causing validate_lock_year to
            # reject it and leaving the controller stuck.
            try:
                # Wait until the overlay text is gone — the reliable signal that
                # all_teams_locked arrived and the overlay cleared for this year.
                # Must use the same predicate the overlay actually renders
                # ("…teams locked in…"), not the total==0 fallback string.
                await page.wait_for_function(
                    f"""() => !{_WAITING_JS}""",
                    timeout=120_000,
                )
            except Exception as _ow_err:
                # Log but continue — overlay may already be gone
                await log(team_key=team_key, username=username,
                          kind="error", year=year,
                          err=f"overlay_wait: {type(_ow_err).__name__}: {_ow_err}")
            await log(team_key=team_key, username=username,
                      kind="ui_advanced", year=year + 1)
        except PWTimeout:
            await log(team_key=team_key, username=username,
                      kind="ui_stuck", year=year,
                      note="never advanced past current year — barrier stuck?")
            return


async def be_viewer(page: Page, team_key: str, username: str,
                    final_atl_event: asyncio.Event):
    """Viewers don't drive anything. They hold the page open so:
       1. Their WebSocket stays connected and receives all_teams_locked.
       2. The React app processes those messages (this is what we're testing).
       3. The WS frame logger captures everything via on_ws above.

    We wait until the final year's all_teams_locked broadcast arrives (signalled
    via final_atl_event) rather than sleeping for a fixed duration.  This
    eliminates the race where viewer tasks are cancelled before the year-5 ATL
    WS frame arrives at the client — the task simply stays alive until the frame
    is confirmed received, then exits cleanly without needing cancellation."""
    timeout = NUM_YEARS * 90 + 120   # generous upper bound (same as before)
    try:
        await asyncio.wait_for(final_atl_event.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        pass   # timed out waiting — viewer task exits anyway


# Orchestration
async def main():
    print(f"[oras-pw] Host: {HOST}")
    print(f"[oras-pw] Teams: {NUM_TEAMS}  Users/team: {USERS_PER_TEAM}  "
          f"Total: {NUM_TEAMS * USERS_PER_TEAM} contexts")
    print(f"[oras-pw] Lock think-time window: {LOCK_DELAY_MIN}–{LOCK_DELAY_MAX}s")
    if RELOAD_ENABLED:
        print(f"[oras-pw] Refresh test: ON (team_{RELOAD_TEST_TEAM} reloads after each lock)")
    else:
        print(f"[oras-pw] Refresh test: OFF (no reloads)")
    print(f"[oras-pw] Output: {OUT_PATH}")

    global _LOG_FILE
    _LOG_FILE = open(OUT_PATH, "w")

    async with async_playwright() as p:
        # M1 macOS notes:
        # headless=True is essential (rendering 60 windowed Chromiums = death)
        # --no-sandbox is harmless on macOS, helpful on Linux
        # --disable-dev-shm-usage matters more on Linux but doesn't hurt
        # --disable-blink-features=AutomationControlled helps if the
        #    React app sniffs for automation (ORAS doesn't, but cheap to add)
        browser = await p.chromium.launch(
            headless=(os.environ.get("ORAS_HEADLESS", "1") != "0"),
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                # Resource hints: reduce per-context overhead
                "--disable-background-timer-throttling",
                "--disable-renderer-backgrounding",
                "--disable-backgrounding-occluded-windows",
            ],
        )

        controller_done = {y: asyncio.Event() for y in range(1, NUM_YEARS + 1)}

        # One event per team: viewers block on this until the controller's
        # login POST has succeeded and the controller role is claimed.
        # Without this, a viewer can win the claim_controller race if the
        # browser takes > SPAWN_INTERVAL_S to load the page for slot 1.
        controller_ready_events = {
            team: asyncio.Event() for team in range(1, NUM_TEAMS + 1)
        }

        final_atl_event = asyncio.Event()

        # Fired once ALL controllers have logged in. No controller clicks
        # "Start Simulation" until this is set, preventing fast controllers
        # from starting the game while slow-spawning users are still on the
        # login form.
        all_controllers_ready = asyncio.Event()

        # Fired once ALL controllers have BEGUN (reached the game page, game
        # state persisted). No controller proceeds to lock Year 1 until this is
        # set, so the server's begun-teams barrier denominator sees the full
        # cohort before the first lock — preventing an early subset from
        # advancing past Year 1 while teams are still assembling.
        controller_begun_events = {
            team: asyncio.Event() for team in range(1, NUM_TEAMS + 1)
        }
        all_controllers_begun = asyncio.Event()

        ctrl_tasks = []   # one per team (slot 1)
        view_tasks = []   # three per team (slots 2-4)
        # Spawn ordering: slot 1 (controller) first so it reaches login before
        # viewers are even allowed to submit their forms.
        for team in range(1, NUM_TEAMS + 1):
            for slot in range(1, USERS_PER_TEAM + 1):
                task = asyncio.create_task(
                    run_user(browser, team, slot, controller_done,
                             controller_ready_events[team],
                             all_controllers_ready,
                             controller_ready_events,
                             controller_begun_events=controller_begun_events,
                             all_controllers_begun=all_controllers_begun,
                             final_atl_event=final_atl_event)
                )
                (ctrl_tasks if slot == 1 else view_tasks).append(task)
                await asyncio.sleep(SPAWN_INTERVAL_S)

        total = len(ctrl_tasks) + len(view_tasks)
        print(f"[oras-pw] All {total} contexts spawned; running...")

        # Wait for all controllers to finish (all 5 years locked per team).
        ctrl_results = await asyncio.gather(*ctrl_tasks, return_exceptions=True)
        ctrl_errors  = [r for r in ctrl_results if isinstance(r, Exception)]
        if ctrl_errors:
            print(f"[oras-pw] {len(ctrl_errors)} controller contexts raised exceptions")

        # Viewer tasks exit on their own once final_atl_event fires (set by the
        # on_frame callback when any client receives all_teams_locked for the
        # final year).  We just wait for them — no cancellation needed.
        print(f"[oras-pw] All controllers done — waiting for viewers to receive final broadcast...")
        view_results = await asyncio.gather(*view_tasks, return_exceptions=True)
        view_errors  = [r for r in view_results
                        if isinstance(r, Exception)
                        and not isinstance(r, asyncio.CancelledError)]
        if view_errors:
            print(f"[oras-pw] {len(view_errors)} viewer contexts raised non-cancel exceptions")

        await browser.close()

    if _LOG_FILE is not None:
        _LOG_FILE.close()
    print(f"[oras-pw] Wrote {len(EVENTS)} events to {OUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
