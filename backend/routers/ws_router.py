"""WebSocket endpoint: initial state push, heartbeats and barrier catch-up."""
import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from auth import get_store, refresh_session
from game_state import (
    compute_waiting_for_others, get_active_team_keys, teams_blocking_year,
)
from leaderboard import compute_leaderboard_entries
from services.timer import year_duration

router = APIRouter()
logger = logging.getLogger("ws")


def _leaderboard_for(entries: list, team_key: str) -> list:
    return [{**e, 'is_you': e.get('team') == team_key} for e in entries]


@router.websocket("/ws/{team_key}")
async def websocket_endpoint(
    ws: WebSocket,
    team_key: str,
    username: str = Query(""),
    is_controller: str = Query("false"),
):
    is_ctrl = isinstance(is_controller, str) and is_controller.lower() in ("true", "1", "yes")
    manager = ws.app.state.manager

    try:
        await manager.connect(team_key, ws, username, is_ctrl)
    except Exception as e:
        logger.warning("Failed to accept WS for %s@%s: %s", username, team_key, e)
        return

    logger.info("[WS CONNECT] %s@%s ctrl=%s", username, team_key, is_ctrl)

    # Clients navigate between pages by closing and reopening the socket, so a send
    # can fail mid-burst. After the first failure, skip the remaining sends.
    dead = False

    async def safe_send(payload: dict) -> bool:
        nonlocal dead
        if dead:
            return False
        try:
            await ws.send_json(payload)
            return True
        except Exception as e:
            dead = True
            logger.debug(
                "[WS SEND FAIL] %s@%s dropped payload type=%s (%s)",
                username, team_key, payload.get('type', '?'), type(e).__name__,
            )
            return False

    loop = asyncio.get_event_loop()

    try:
        # refresh_session (not register_session) so a reconnect cannot revive a
        # session that was kicked or logged out.
        if username and team_key:
            await loop.run_in_executor(None, refresh_session, username, team_key)

        store = get_store()
        gs = store.load_game_state(team_key)

        if gs:
            cur_year = gs.get('current_year', 1)
            is_comp = gs.get('mode', 'competition') == 'competition'
            locked_count = len(gs.get('locked_allocations', []))

            fresh_waiting = await loop.run_in_executor(
                None, lambda: compute_waiting_for_others(gs)
            )
            gs['waiting_for_others'] = fresh_waiting

            if not await safe_send({"type": "game_state_update", "data": gs}):
                return

            # Reconnecting after the year-end broadcast already fired: replay it
            # to this socket only.
            if is_comp and locked_count > 0 and not fresh_waiting:
                try:
                    broadcast_done = await loop.run_in_executor(
                        None, lambda: store.is_broadcast_done(locked_count)
                    )
                    if broadcast_done:
                        lb = await loop.run_in_executor(
                            None, lambda: compute_leaderboard_entries(team_key)
                        )
                        if not await safe_send({
                            "type": "all_teams_locked",
                            "year": locked_count,
                            "game_state": gs,
                            "leaderboard": _leaderboard_for(lb, team_key),
                        }):
                            return
                        logger.info(
                            "[WS CATCHUP] %s@%s sent targeted all_teams_locked for year %d",
                            username, team_key, locked_count,
                        )
                except Exception as e:
                    logger.warning("[WS CATCHUP] failed for %s@%s: %s", username, team_key, e)

            blocking = []
            if fresh_waiting:
                blocking = await loop.run_in_executor(
                    None, lambda: teams_blocking_year(cur_year, team_key)
                )
                # Restore the "X of Y teams locked" tally the client missed.
                try:
                    counts = await loop.run_in_executor(None, store.get_all_locked_years)
                    await safe_send({
                        "type": "lock_progress",
                        "locked": sum(1 for c in counts.values() if c >= locked_count),
                        "total": len(counts),
                    })
                except Exception as e:
                    logger.warning("[WS LOCKPROGRESS] failed for %s@%s: %s", username, team_key, e)
            total_active = await loop.run_in_executor(None, lambda: len(get_active_team_keys()))
            if not await safe_send(
                {"type": "blocking_update", "blocking": blocking, "total": total_active}
            ):
                return

        paused = store.is_paused()
        if not await safe_send({"type": "paused", "paused": paused}):
            return

        timer_mgr = ws.app.state.timer_manager
        remaining = timer_mgr.get_remaining(team_key)

        # The year timer starts only after the storyboard is finished.
        if gs and gs.get('simulation_begun') and not gs.get('completed') and remaining == 0:
            current_year = gs.get('current_year', 1)
            timer_mgr.start_timer(team_key, year_duration(current_year), current_year)
            remaining = timer_mgr.get_remaining(team_key)

        if remaining > 0:
            if not await safe_send({
                "type": "timer_tick",
                "remaining": remaining,
                "year": gs.get('current_year', 1) if gs else 1,
                "paused": paused,
            }):
                return

        # Idempotent: the first member to connect starts the team's storyboard timer.
        if gs and not gs.get('completed') and not gs.get('simulation_begun'):
            timer_mgr.start_storyboard_timer(team_key)

        sb_remaining = timer_mgr.get_storyboard_remaining(team_key)
        if sb_remaining > 0:
            if not await safe_send({"type": "storyboard_tick", "remaining": sb_remaining}):
                return

        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                continue
            msg_type = msg.get("type", "")

            if msg_type == "heartbeat":
                if username and team_key:
                    await loop.run_in_executor(None, refresh_session, username, team_key)
                    await _heartbeat_catchup(
                        store, timer_mgr, safe_send, loop, username, team_key,
                    )

            elif msg_type == "request_state":
                gs = store.load_game_state(team_key)
                if gs and not await safe_send({"type": "game_state_update", "data": gs}):
                    return

    except WebSocketDisconnect:
        logger.info("[WS DISCONNECT] %s@%s", username, team_key)
    except Exception as e:
        logger.warning("[WS ERROR] %s@%s: %s: %s", username, team_key, type(e).__name__, e)
    finally:
        await manager.disconnect(team_key, ws)


async def _heartbeat_catchup(store, timer_mgr, safe_send, loop, username, team_key):
    """If the team is still marked waiting but its year-end broadcast already
    fired, release it and start the next year's timer."""
    try:
        gs = store.load_game_state(team_key)
        if not (gs and gs.get('waiting_for_others')):
            return
        locked_count = len(gs.get('locked_allocations', []))
        if locked_count <= 0:
            return
        if not await loop.run_in_executor(None, lambda: store.is_broadcast_done(locked_count)):
            return

        gs['waiting_for_others'] = False
        await loop.run_in_executor(None, lambda: store.save_game_state(team_key, gs))
        lb = await loop.run_in_executor(None, lambda: compute_leaderboard_entries(team_key))
        await safe_send({
            "type": "all_teams_locked",
            "year": locked_count,
            "game_state": gs,
            "leaderboard": _leaderboard_for(lb, team_key),
            "triggered_by": team_key,
        })
        await safe_send({"type": "blocking_update", "blocking": []})
        timer_mgr.unpause_team(team_key)
        if not gs.get('completed', False):
            next_year = gs.get('current_year', locked_count + 1)
            timer_mgr.start_timer(team_key, year_duration(next_year), next_year)
        logger.info(
            "[HB CATCHUP] %s@%s sent catch-up all_teams_locked year=%d",
            username, team_key, locked_count,
        )
    except Exception as e:
        logger.debug("[HB CATCHUP] %s@%s error: %s", username, team_key, e)
