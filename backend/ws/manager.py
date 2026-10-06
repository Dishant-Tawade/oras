"""WebSocket connection manager, grouped by team."""
import asyncio
import logging

from fastapi import WebSocket

logger = logging.getLogger("ws.manager")


class ConnectionManager:
    def __init__(self):
        # team_key -> [(socket, username, is_controller)]
        self._connections: dict[str, list[tuple[WebSocket, str, bool]]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, team_key: str, ws: WebSocket,
                      username: str, is_controller: bool):
        await ws.accept()
        async with self._lock:
            self._connections.setdefault(team_key, []).append(
                (ws, username, is_controller)
            )
        logger.info(f"Connected: {username} ({team_key}) "
                    f"{'controller' if is_controller else 'viewer'} "
                    f"[total={self.total_connections}]")

    async def disconnect(self, team_key: str, ws: WebSocket):
        async with self._lock:
            conns = self._connections.get(team_key, [])
            self._connections[team_key] = [
                (w, u, c) for w, u, c in conns if w is not ws
            ]
            if not self._connections[team_key]:
                del self._connections[team_key]
        logger.info(f"Disconnected from {team_key} [total={self.total_connections}]")

    async def disconnect_all(self):
        async with self._lock:
            for conns in self._connections.values():
                for ws, _, _ in conns:
                    try:
                        await ws.close()
                    except Exception:
                        pass
            self._connections.clear()

    @property
    def total_connections(self) -> int:
        return sum(len(conns) for conns in self._connections.values())

    @property
    def team_keys(self) -> list[str]:
        return list(self._connections.keys())

    @property
    def team_keys_with_controller(self) -> set[str]:
        """Teams with at least one connected controller."""
        return {
            tk
            for tk, conns in list(self._connections.items())
            if any(is_ctrl for _, _, is_ctrl in conns)
        }

    async def connected_users(self) -> set[tuple[str, str]]:
        """(team_key, username) for every live connection."""
        async with self._lock:
            return {
                (tk, uname)
                for tk, conns in self._connections.items()
                for _, uname, _ in conns
            }

    async def _safe_send(self, ws: WebSocket, data: dict):
        try:
            await ws.send_json(data)
        except Exception:
            pass  # dead socket; cleaned up by disconnect()

    async def send_to_team(self, team_key: str, message: dict):
        async with self._lock:
            conns = list(self._connections.get(team_key, []))
        if conns:
            await asyncio.gather(*[self._safe_send(ws, message) for ws, _, _ in conns])

    async def send_to_user(self, team_key: str, username: str, message: dict):
        async with self._lock:
            conns = list(self._connections.get(team_key, []))
        targets = [ws for ws, u, _ in conns if u == username]
        if targets:
            await asyncio.gather(*[self._safe_send(ws, message) for ws in targets])

    async def disconnect_user(self, team_key: str, username: str):
        """Close every socket belonging to one user (used after kick/reset)."""
        conns = list(self._connections.get(team_key, []))
        for ws, u, _ in conns:
            if u == username:
                try:
                    await ws.close(code=1000, reason="kicked")
                except Exception:
                    pass

    async def broadcast_all(self, message: dict):
        async with self._lock:
            all_ws = [ws for conns in self._connections.values() for ws, _, _ in conns]
        if all_ws:
            await asyncio.gather(*[self._safe_send(ws, message) for ws in all_ws])
