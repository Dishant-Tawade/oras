"""In-memory event feed for the admin dashboard.

Events live in a bounded ring buffer with monotonically increasing IDs, so
clients can poll with `?since=<id>`. Nothing is persisted: a restart clears the feed.
"""
import threading
import time
from collections import deque

_MAX_EVENTS = 2000
_buffer: deque[dict] = deque(maxlen=_MAX_EVENTS)
_next_id = 1
_lock = threading.Lock()

# Presence is derived by diffing live WebSocket connections on each admin poll
# rather than from connect/disconnect handlers, which race during page navigation.
_last_known_presence: set[tuple[str, str]] = set()
_presence_lock = threading.Lock()


def _append(kind: str, **fields) -> dict:
    """Append an event. Caller must hold `_lock`."""
    global _next_id
    evt = {"id": _next_id, "ts": time.time(), "kind": kind, **fields}
    _next_id += 1
    _buffer.append(evt)
    return evt


async def sync_presence(manager) -> None:
    """Emit join/leave events for changes in live WebSocket connections.

    A user counts as having left only when they have no live socket and their
    session is no longer active, so brief reconnects do not produce false leaves.
    """
    global _last_known_presence

    current = set(await manager.connected_users())
    with _presence_lock:
        prev = _last_known_presence
        newly_joined = current - prev
        departed = prev - current
        _last_known_presence = current

    if newly_joined:
        with _lock:
            for tk, u in sorted(newly_joined):
                _append("user_joined", team_key=tk, username=u,
                        text=f"{u} ({tk}) came online")

    if departed:
        try:
            from auth import get_store
            store = get_store()
            confirmed_left = []
            for tk, u in sorted(departed):
                try:
                    if not store.is_session_active(u, tk):
                        confirmed_left.append((tk, u))
                except Exception:
                    pass
            with _lock:
                for tk, u in confirmed_left:
                    _append("user_left", team_key=tk, username=u,
                            text=f"{u} ({tk}) went offline")
        except Exception:
            pass


def emit(kind: str, **fields) -> dict:
    """Append an event. `text` should be a human-readable summary."""
    with _lock:
        return _append(kind, **fields)


def get_since(since_id: int = 0, limit: int = 100) -> list[dict]:
    """Events with id > since_id, oldest first."""
    with _lock:
        return [e for e in _buffer if e["id"] > since_id][:limit]


def latest_id() -> int:
    with _lock:
        return _next_id - 1


def reset_all() -> None:
    """Clear the feed and presence state."""
    global _next_id, _last_known_presence
    with _lock:
        _buffer.clear()
        _next_id = 1
    with _presence_lock:
        _last_known_presence = set()
