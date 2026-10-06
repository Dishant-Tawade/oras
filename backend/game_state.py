"""Team-level game-state helpers. All reads go straight to storage (no caching)."""
from auth import get_store
from config import NP

_store = get_store()


def get_team_gs(team_key: str) -> dict | None:
    return _store.load_game_state(team_key)


def set_team_gs(team_key: str, gs: dict) -> None:
    _store.save_game_state(team_key, gs)


def get_all_team_keys() -> list:
    return list({u['team_key'] for u in _store.load_users()})


def get_logged_in_team_keys(sessions: list | None = None) -> set:
    """Teams with at least one session that has not explicitly logged out."""
    try:
        if sessions is None:
            sessions = _store.get_all_sessions()
        return {
            s['team_key'] for s in sessions
            if isinstance(s, dict) and s.get('team_key') and not s.get('logged_out', False)
        }
    except Exception:
        return set()


def get_active_team_keys() -> set:
    """Logged-in teams that also have a saved game state."""
    try:
        return {tk for tk in get_logged_in_team_keys() if _store.load_game_state(tk)}
    except Exception:
        return set()


def teams_blocking_year(year_to_lock: int, this_team: str) -> list:
    """Logged-in teams (other than this one) that have not yet locked the previous year."""
    needed = year_to_lock - 1
    if needed == 0:
        return []
    all_counts = _store.get_all_locked_years()
    logged_in_teams = get_logged_in_team_keys()
    blocking = []
    for tk in get_all_team_keys():
        if tk == this_team or tk not in logged_in_teams:
            continue
        remote = all_counts.get(tk, -1)
        if remote >= NP:
            continue
        if remote < needed:
            blocking.append(tk)
    return blocking


def compute_waiting_for_others(gs: dict) -> bool:
    """Whether a team is parked at a year-end barrier, recomputed on every read.

    `waiting_for_others` is not persisted (and `current_year` advances as soon as
    a team locks), so a reloaded state alone cannot tell a team it is still
    waiting. A team is waiting if it is in competition mode, has locked at least
    one year, and the all-teams broadcast for its last locked year has not
    completed. Fails safe (waiting) if the broadcast check errors.
    """
    if not gs:
        return False
    if gs.get('mode', 'competition') != 'competition':
        return False
    locked_count = len(gs.get('locked_allocations', []))
    if locked_count <= 0:
        return False
    try:
        return not _store.is_broadcast_done(locked_count)
    except Exception:
        return True
