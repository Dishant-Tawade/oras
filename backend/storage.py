"""Persistence backends for ORAS.

STORAGE_BACKEND selects the implementation:
  local      JSON files under ORAS_DATA_DIR (default: backend/data). Single process.
  firestore  Google Cloud Firestore. Also reads GCP_PROJECT, FIRESTORE_DATABASE
             and FORCE_SEED_USERS (re-seed users from seed_users.json on boot).
"""
import abc
import json
import os
import shutil
import threading
import time

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
SEED_USERS_FILE = os.path.join(_BACKEND_DIR, 'seed_users.json')
DATA_DIR = os.environ.get('ORAS_DATA_DIR') or os.path.join(_BACKEND_DIR, 'data')

SESSION_TIMEOUT = 90  # seconds without a heartbeat before a session counts as inactive


class StorageBackend(abc.ABC):
    """Persistence interface used by the rest of the backend."""

    # Users
    @abc.abstractmethod
    def load_users(self) -> list[dict]: ...

    @abc.abstractmethod
    def add_user(self, user: dict) -> None: ...

    @abc.abstractmethod
    def delete_users(self, user_keys: list[tuple[str, str]]) -> int:
        """Delete users by (username, team_key). Returns the number deleted."""

    @abc.abstractmethod
    def save_users(self, users: list[dict]) -> None:
        """Replace the full user list."""

    # Game state
    @abc.abstractmethod
    def save_game_state(self, team_key: str, gs: dict) -> None: ...

    @abc.abstractmethod
    def load_game_state(self, team_key: str) -> dict | None: ...

    @abc.abstractmethod
    def delete_game_state(self, team_key: str) -> None: ...

    @abc.abstractmethod
    def patch_game_state_field(self, team_key: str, field: str, value) -> None:
        """Set one top-level field without a read-modify-write race in the caller."""

    @abc.abstractmethod
    def get_all_locked_years(self) -> dict[str, int]:
        """{team_key: years locked} for every team with a game state."""

    # Cohort membership
    @abc.abstractmethod
    def mark_team_joined(self, team_key: str) -> None:
        """Record that a team joined the current game (cleared on reset)."""

    @abc.abstractmethod
    def get_joined_teams(self) -> set: ...

    # Sessions
    @abc.abstractmethod
    def is_session_active(self, username: str, team_key: str) -> bool: ...

    @abc.abstractmethod
    def register_session(self, username: str, team_key: str) -> None:
        """Heartbeat: refresh last_seen. Ignored after an explicit logout."""

    @abc.abstractmethod
    def activate_session(self, username: str, team_key: str) -> None:
        """Start a session on login, clearing any logout marker."""

    @abc.abstractmethod
    def clear_session(self, username: str, team_key: str) -> None: ...

    @abc.abstractmethod
    def get_all_sessions(self) -> list[dict]: ...

    @abc.abstractmethod
    def set_storyboard_seen(self, username: str, team_key: str) -> None: ...

    @abc.abstractmethod
    def get_storyboard_seen(self, username: str, team_key: str) -> bool: ...

    @abc.abstractmethod
    def clear_all_storyboard_seen(self) -> None: ...

    # Controller (one per team)
    @abc.abstractmethod
    def get_controller(self, team_key: str) -> str | None: ...

    @abc.abstractmethod
    def set_controller(self, team_key: str, username: str | None) -> None: ...

    @abc.abstractmethod
    def claim_controller(self, team_key: str, username: str) -> bool:
        """Atomically claim the controller role. True if the caller holds it."""

    # Year barrier
    @abc.abstractmethod
    def increment_lock_counter(self, year: int, total_teams: int) -> bool:
        """Count one team's lock for `year`. True for exactly one caller: the one
        whose increment reaches the threshold set by the first locker."""

    @abc.abstractmethod
    def claim_broadcast_slot(self, year: int) -> bool:
        """Atomically claim the right to broadcast `year`. True for one caller."""

    @abc.abstractmethod
    def mark_broadcast_done(self, year: int) -> None: ...

    @abc.abstractmethod
    def is_broadcast_done(self, year: int) -> bool: ...

    @abc.abstractmethod
    def reset_lock_counters(self) -> None: ...

    # Global state
    @abc.abstractmethod
    def set_paused(self, paused: bool) -> None: ...

    @abc.abstractmethod
    def is_paused(self) -> bool: ...

    @abc.abstractmethod
    def load_active_scenario(self) -> tuple[str, str] | None:
        """(country, industry) last chosen by the admin, if any."""

    @abc.abstractmethod
    def save_active_scenario(self, country: str, industry: str) -> None: ...

    @abc.abstractmethod
    def reset_all_state(self) -> None:
        """Delete game states, sessions, controllers and counters. Keeps users
        and the active scenario."""


def _atomic_write_json(path: str, data, **dump_kwargs) -> None:
    tmp = path + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(data, f, **dump_kwargs)
    os.replace(tmp, path)


class LocalStorage(StorageBackend):
    """JSON files under DATA_DIR. Supports a single server process."""

    def __init__(self):
        self._users_file = os.path.join(DATA_DIR, 'users.json')
        self._states_dir = os.path.join(DATA_DIR, 'game_states')
        self._sessions_file = os.path.join(DATA_DIR, 'sessions.json')
        self._storyboard_file = os.path.join(DATA_DIR, 'storyboard_seen.json')
        self._joined_file = os.path.join(DATA_DIR, 'joined_teams.json')
        self._pause_file = os.path.join(DATA_DIR, '.pause_state')
        self._scenario_file = os.path.join(DATA_DIR, 'active_scenario.json')
        os.makedirs(self._states_dir, exist_ok=True)
        if not os.path.exists(self._users_file) and os.path.exists(SEED_USERS_FILE):
            shutil.copy(SEED_USERS_FILE, self._users_file)

        self._controllers: dict[str, str | None] = {}
        self._active_sessions: dict[str, float] = {}
        self._logged_out: set[str] = set()
        self._paused = False
        self._paused_cache_ts = 0.0
        self._paused_cache_lock = threading.Lock()

        self._barrier_lock = threading.Lock()
        self._lock_counters: dict[int, int] = {}
        self._lock_thresholds: dict[int, int] = {}
        self._barrier_fired: set[int] = set()
        self._claimed_broadcasts: set[int] = set()
        self._fanout_done: set[int] = set()

        self._reload_sessions()

    # Users
    def load_users(self) -> list[dict]:
        try:
            with open(self._users_file) as f:
                return json.load(f)
        except Exception:
            return []

    def save_users(self, users: list[dict]) -> None:
        try:
            _atomic_write_json(self._users_file, users, indent=2)
        except Exception as e:
            print(f"[WARN] Could not save users: {e}")

    def add_user(self, user: dict) -> None:
        users = self.load_users()
        users.append(user)
        self.save_users(users)

    def delete_users(self, user_keys: list[tuple[str, str]]) -> int:
        users = self.load_users()
        key_set = set(user_keys)
        remaining = [u for u in users if (u['username'], u['team_key']) not in key_set]
        self.save_users(remaining)
        return len(users) - len(remaining)

    # Game state
    def _state_path(self, team_key: str) -> str:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in team_key)
        return os.path.join(self._states_dir, f"{safe}.json")

    def save_game_state(self, team_key: str, gs: dict) -> None:
        try:
            _atomic_write_json(self._state_path(team_key), gs)
        except Exception as e:
            print(f"[WARN] Could not save state for {team_key}: {e}")

    def load_game_state(self, team_key: str) -> dict | None:
        try:
            path = self._state_path(team_key)
            if not os.path.exists(path):
                return None
            with open(path) as f:
                return json.load(f)
        except Exception:
            return None

    def delete_game_state(self, team_key: str) -> None:
        try:
            path = self._state_path(team_key)
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            print(f"[WARN] Could not delete state for {team_key}: {e}")

    def patch_game_state_field(self, team_key: str, field: str, value) -> None:
        gs = self.load_game_state(team_key)
        if gs is None:
            return
        gs[field] = value
        self.save_game_state(team_key, gs)

    def get_all_locked_years(self) -> dict[str, int]:
        result = {}
        for name in os.listdir(self._states_dir):
            if not name.endswith('.json'):
                continue
            try:
                with open(os.path.join(self._states_dir, name)) as f:
                    gs = json.load(f)
                result[name[:-5]] = len(gs.get('locked_allocations', []))
            except Exception:
                pass
        return result

    # Cohort membership
    def _read_joined(self) -> set:
        try:
            with open(self._joined_file) as f:
                return set(json.load(f))
        except Exception:
            return set()

    def _write_joined(self, teams: set) -> None:
        try:
            _atomic_write_json(self._joined_file, sorted(teams))
        except Exception as e:
            print(f"[WARN] Could not persist joined_teams: {e}")

    def mark_team_joined(self, team_key: str) -> None:
        if not team_key or team_key == '__admin__':
            return
        with self._barrier_lock:
            teams = self._read_joined()
            if team_key not in teams:
                teams.add(team_key)
                self._write_joined(teams)

    def get_joined_teams(self) -> set:
        return self._read_joined()

    # Sessions
    @staticmethod
    def _session_key(username: str, team_key: str) -> str:
        return f"{username}:{team_key}"

    def _reload_sessions(self) -> None:
        """Re-read sessions.json into memory."""
        try:
            if not os.path.exists(self._sessions_file):
                return
            with open(self._sessions_file) as f:
                data = json.load(f)
        except Exception as e:
            print(f"[WARN] Could not load sessions.json: {e}")
            return
        self._active_sessions.clear()
        self._logged_out.clear()
        for key, entry in data.items():
            if entry.get('logged_out', False):
                self._logged_out.add(key)
            else:
                self._active_sessions[key] = entry.get('last_seen', 0)

    def _save_sessions(self) -> None:
        data = {key: {'last_seen': ts, 'logged_out': False}
                for key, ts in self._active_sessions.items()}
        for key in self._logged_out:
            data.setdefault(key, {})['logged_out'] = True
            data[key].setdefault('last_seen', 0)
        try:
            _atomic_write_json(self._sessions_file, data)
        except Exception as e:
            print(f"[WARN] Could not save sessions.json: {e}")

    def is_session_active(self, username: str, team_key: str) -> bool:
        self._reload_sessions()
        key = self._session_key(username, team_key)
        if key in self._logged_out:
            return False
        ts = self._active_sessions.get(key)
        return ts is not None and (time.time() - ts) < SESSION_TIMEOUT

    def register_session(self, username: str, team_key: str) -> None:
        key = self._session_key(username, team_key)
        if key in self._logged_out:
            return
        self._active_sessions[key] = time.time()
        self._save_sessions()

    def activate_session(self, username: str, team_key: str) -> None:
        key = self._session_key(username, team_key)
        self._logged_out.discard(key)
        self._active_sessions[key] = time.time()
        self._save_sessions()

    def clear_session(self, username: str, team_key: str) -> None:
        key = self._session_key(username, team_key)
        self._active_sessions.pop(key, None)
        self._logged_out.add(key)
        self._save_sessions()

    def get_all_sessions(self) -> list[dict]:
        """All non-logged-out sessions, whatever their age. A stale heartbeat
        (e.g. during a heavy simulation) must not shrink the barrier's team count."""
        self._reload_sessions()
        now = time.time()
        result = []
        for key, ts in self._active_sessions.items():
            username, _, team_key = key.partition(':')
            if team_key:
                result.append({'username': username, 'team_key': team_key,
                               'last_seen': ts, 'active': (now - ts) < SESSION_TIMEOUT})
        return result

    # Storyboard seen
    def _read_storyboard_seen(self) -> set:
        try:
            if os.path.exists(self._storyboard_file):
                with open(self._storyboard_file) as f:
                    return set(json.load(f))
        except Exception as e:
            print(f"[WARN] Could not read storyboard_seen.json: {e}")
        return set()

    def _write_storyboard_seen(self, keys: set) -> None:
        try:
            _atomic_write_json(self._storyboard_file, sorted(keys))
        except Exception as e:
            print(f"[WARN] Could not write storyboard_seen.json: {e}")

    def set_storyboard_seen(self, username: str, team_key: str) -> None:
        keys = self._read_storyboard_seen()
        keys.add(f"{username}_{team_key}")
        self._write_storyboard_seen(keys)

    def get_storyboard_seen(self, username: str, team_key: str) -> bool:
        return f"{username}_{team_key}" in self._read_storyboard_seen()

    def clear_all_storyboard_seen(self) -> None:
        self._write_storyboard_seen(set())

    # Controller
    def get_controller(self, team_key: str) -> str | None:
        return self._controllers.get(team_key)

    def set_controller(self, team_key: str, username: str | None) -> None:
        self._controllers[team_key] = username

    def claim_controller(self, team_key: str, username: str) -> bool:
        if self._controllers.get(team_key) is None:
            self._controllers[team_key] = username
        return self._controllers[team_key] == username

    # Year barrier
    def increment_lock_counter(self, year: int, total_teams: int) -> bool:
        with self._barrier_lock:
            # After the barrier fired, a late locker must not trigger a second broadcast.
            if year in self._barrier_fired:
                return False
            # The first locker's total is the threshold for everyone.
            threshold = self._lock_thresholds.setdefault(year, total_teams)
            self._lock_counters[year] = self._lock_counters.get(year, 0) + 1
            reached = self._lock_counters[year] >= threshold
            if reached:
                self._barrier_fired.add(year)
            return reached

    def claim_broadcast_slot(self, year: int) -> bool:
        with self._barrier_lock:
            if year in self._claimed_broadcasts:
                return False
            self._claimed_broadcasts.add(year)
            return True

    def mark_broadcast_done(self, year: int) -> None:
        with self._barrier_lock:
            self._fanout_done.add(year)

    def is_broadcast_done(self, year: int) -> bool:
        return year in self._fanout_done

    def reset_lock_counters(self) -> None:
        with self._barrier_lock:
            self._lock_counters.clear()
            self._lock_thresholds.clear()
            self._barrier_fired.clear()
            self._claimed_broadcasts.clear()
            self._fanout_done.clear()

    # Global state
    def set_paused(self, paused: bool) -> None:
        with self._paused_cache_lock:
            self._paused = paused
            self._paused_cache_ts = time.time()
        try:
            with open(self._pause_file, 'w') as f:
                f.write('1' if paused else '0')
        except Exception as e:
            print(f"[PAUSE] set_paused({paused}) — disk write failed: {e}")

    def is_paused(self) -> bool:
        now = time.time()
        with self._paused_cache_lock:
            if (now - self._paused_cache_ts) < 2.0:
                return self._paused
        try:
            if os.path.exists(self._pause_file):
                with open(self._pause_file) as f:
                    val = f.read().strip() == '1'
                with self._paused_cache_lock:
                    self._paused = val
                    self._paused_cache_ts = now
                return val
        except Exception as e:
            print(f"[PAUSE] is_paused disk read failed: {e}")
        with self._paused_cache_lock:
            self._paused_cache_ts = now
            return self._paused

    def load_active_scenario(self) -> tuple[str, str] | None:
        try:
            with open(self._scenario_file) as f:
                data = json.load(f)
            country, industry = data.get('country', ''), data.get('industry', '')
            return (country, industry) if country and industry else None
        except Exception:
            return None

    def save_active_scenario(self, country: str, industry: str) -> None:
        try:
            _atomic_write_json(self._scenario_file, {'country': country, 'industry': industry})
        except Exception as e:
            print(f"[WARN] Could not persist scenario: {e}")

    def reset_all_state(self) -> None:
        for name in os.listdir(self._states_dir):
            if name.endswith('.json'):
                try:
                    os.remove(os.path.join(self._states_dir, name))
                except Exception:
                    pass
        self._controllers.clear()
        self._active_sessions.clear()
        self._logged_out.clear()
        self._save_sessions()
        self._write_storyboard_seen(set())
        self._write_joined(set())
        with self._paused_cache_lock:
            self._paused = False
            self._paused_cache_ts = 0.0
        try:
            os.remove(self._pause_file)
        except FileNotFoundError:
            pass
        self.reset_lock_counters()


def _safe_id(value: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in value)


class FirestoreStorage(StorageBackend):
    """Cloud Firestore backend for multi-instance deployments.

    Collections:
      users/{username}_{team_key}  user record
      game_states/{team_key}       {"data": <game state JSON string>}
      controllers/{team_key}       {"username", "claimed_at"}
      sessions/{user}__{team}      {"last_seen", "logged_out"}
      locked_years/{team_key}      {"count"}
      meta/session_state           {"teams": {team_key: locked_count}}
      meta/lock_counters           year barrier counters and flags
      meta/joined_teams            {"teams": [team_key, ...]}
      meta/pause_state             {"paused": bool}
      meta/active_scenario         {"country", "industry"}

    The users and sessions collections are mirrored into in-process caches kept
    fresh by Firestore snapshot listeners, so hot paths avoid collection scans.
    """

    _PAUSE_CACHE_TTL = 3.0
    _HEARTBEAT_WRITE_INTERVAL = 30.0  # session timeout is 90s, so writing every heartbeat is wasted

    _COL_USERS = 'users'
    _COL_GAME_STATES = 'game_states'
    _COL_CONTROLLERS = 'controllers'
    _COL_SESSIONS = 'sessions'
    _COL_LOCKED = 'locked_years'
    _COL_META = 'meta'
    _DOC_SESSION_STATE = 'session_state'

    def __init__(self):
        from google.cloud import firestore
        self._fs = firestore
        self._db = firestore.Client(
            project=os.environ.get('GCP_PROJECT'),
            database=os.environ.get('FIRESTORE_DATABASE', '(default)'),
        )

        self._users_cache: list[dict] = []
        self._users_ready = threading.Event()
        self._users_lock = threading.Lock()
        self._users_watch = None  # hold a reference so the listener is not garbage-collected
        self._seed_users()
        self._start_users_listener()

        self._sessions_cache: list[dict] = []
        self._sessions_lock = threading.Lock()
        self._sessions_watch = None
        self._session_write_ts: dict[str, float] = {}
        self._start_sessions_listener()

        self._paused_cache = False
        self._paused_cache_ts = 0.0
        self._paused_cache_lock = threading.Lock()

    def _meta(self, doc_id: str):
        return self._db.collection(self._COL_META).document(doc_id)

    # Listeners
    def _start_sessions_listener(self) -> None:
        def on_snapshot(col_snapshot, changes, read_time):
            sessions = []
            for doc in col_snapshot:
                d = doc.to_dict()
                parts = doc.id.split('__', 1)
                if len(parts) != 2:
                    continue
                sessions.append({
                    'username': parts[0],
                    'team_key': parts[1],
                    'last_seen': d.get('last_seen', 0),
                    'logged_out': d.get('logged_out', False),
                })
            with self._sessions_lock:
                self._sessions_cache = sessions

        try:
            self._sessions_watch = self._db.collection(self._COL_SESSIONS).on_snapshot(on_snapshot)
        except Exception as e:
            print(f"[WARN] Could not start sessions listener: {e}")

    def _start_users_listener(self) -> None:
        def on_snapshot(col_snapshot, changes, read_time):
            docs = [doc.to_dict() for doc in col_snapshot]
            with self._users_lock:
                self._users_cache = docs
            self._users_ready.set()

        self._users_watch = self._db.collection(self._COL_USERS).on_snapshot(on_snapshot)

        if not self._users_ready.wait(timeout=10):
            print("[WARN] Firestore user snapshot not ready after 10 s; reading directly.")
            try:
                docs = [d.to_dict() for d in self._db.collection(self._COL_USERS).stream()]
                with self._users_lock:
                    self._users_cache = docs
                self._users_ready.set()
            except Exception as e:
                print(f"[WARN] Firestore fallback user read failed: {e}")

    def _seed_users(self) -> None:
        """Load seed_users.json when the collection is empty (or FORCE_SEED_USERS is set)."""
        users_ref = self._db.collection(self._COL_USERS)
        force = os.environ.get('FORCE_SEED_USERS', 'false').lower() in ('true', '1', 'yes')

        if not force and list(users_ref.limit(1).stream()):
            return

        for doc in users_ref.stream():
            doc.reference.delete()

        try:
            with open(SEED_USERS_FILE) as f:
                users = json.load(f)
            for u in users:
                users_ref.document(f"{u['username']}_{u['team_key']}").set(u)
            print(f"[INFO] Seeded {len(users)} users into Firestore (force={force}).")
        except Exception as e:
            print(f"[WARN] Could not seed users to Firestore: {e}")

    # Users
    def load_users(self) -> list[dict]:
        with self._users_lock:
            return list(self._users_cache)

    def add_user(self, user: dict) -> None:
        """Also updates the local cache so the change shows before the listener fires."""
        try:
            doc_id = f"{user['username']}_{user['team_key']}"
            self._db.collection(self._COL_USERS).document(doc_id).set(user)
            with self._users_lock:
                self._users_cache = [
                    u for u in self._users_cache
                    if not (u.get('username') == user.get('username')
                            and u.get('team_key') == user.get('team_key'))
                ]
                self._users_cache.append(user)
        except Exception as e:
            print(f"[WARN] Firestore add_user failed: {e}")

    def delete_users(self, user_keys: list[tuple[str, str]]) -> int:
        key_set = set(user_keys)
        deleted = 0
        try:
            for doc in self._db.collection(self._COL_USERS).stream():
                d = doc.to_dict()
                if (d.get('username', ''), d.get('team_key', '')) in key_set:
                    doc.reference.delete()
                    deleted += 1
            with self._users_lock:
                self._users_cache = [
                    u for u in self._users_cache
                    if (u.get('username', ''), u.get('team_key', '')) not in key_set
                ]
        except Exception as e:
            print(f"[WARN] Firestore delete_users failed: {e}")
        return deleted

    def save_users(self, users: list[dict]) -> None:
        chunk = 250  # Firestore allows 500 operations per batch
        try:
            users_ref = self._db.collection(self._COL_USERS)
            existing = list(users_ref.stream())
            for i in range(0, len(existing), chunk):
                batch = self._db.batch()
                for doc in existing[i:i + chunk]:
                    batch.delete(doc.reference)
                batch.commit()
            for i in range(0, len(users), chunk):
                batch = self._db.batch()
                for u in users[i:i + chunk]:
                    batch.set(users_ref.document(f"{u['username']}_{u['team_key']}"), u)
                batch.commit()
        except Exception as e:
            print(f"[WARN] Firestore save_users failed: {e}")

    # Game state
    def save_game_state(self, team_key: str, gs: dict) -> None:
        """Write the state, the team's locked-year count and the shared summary in one batch.

        `waiting_for_others` is a transient flag recomputed on read, so it is not stored.
        """
        try:
            sk = _safe_id(team_key)
            count = len(gs.get('locked_allocations', []))
            gs_to_store = {k: v for k, v in gs.items() if k != 'waiting_for_others'}

            batch = self._db.batch()
            batch.set(self._db.collection(self._COL_GAME_STATES).document(sk),
                      {'data': json.dumps(gs_to_store)})
            batch.set(self._db.collection(self._COL_LOCKED).document(sk), {'count': count})
            batch.set(self._meta(self._DOC_SESSION_STATE), {'teams': {team_key: count}}, merge=True)
            batch.commit()
        except Exception as e:
            print(f"[ERROR] Firestore save_game_state failed for {team_key}: {e}", flush=True)
            raise

    def load_game_state(self, team_key: str) -> dict | None:
        try:
            doc = self._db.collection(self._COL_GAME_STATES).document(_safe_id(team_key)).get()
            if not doc.exists:
                return None
            raw = doc.to_dict()
            return json.loads(raw['data']) if 'data' in raw else raw
        except Exception as e:
            print(f"[WARN] Firestore load_game_state failed for {team_key}: {e}")
            return None

    def delete_game_state(self, team_key: str) -> None:
        try:
            from google.cloud.firestore_v1 import transforms
            sk = _safe_id(team_key)
            batch = self._db.batch()
            batch.delete(self._db.collection(self._COL_GAME_STATES).document(sk))
            batch.delete(self._db.collection(self._COL_LOCKED).document(sk))
            batch.set(self._meta(self._DOC_SESSION_STATE),
                      {'teams': {team_key: transforms.DELETE_FIELD}}, merge=True)
            batch.commit()
        except Exception as e:
            print(f"[WARN] Firestore delete_game_state failed for {team_key}: {e}")

    def patch_game_state_field(self, team_key: str, field: str, value) -> None:
        """Transactional, so a stale read cannot overwrite a newer state."""
        gs_ref = self._db.collection(self._COL_GAME_STATES).document(_safe_id(team_key))

        @self._fs.transactional
        def patch(txn, ref):
            snap = ref.get(transaction=txn)
            if not snap.exists:
                return
            raw = snap.to_dict()
            gs = json.loads(raw['data']) if 'data' in raw else raw
            gs[field] = value
            gs.pop('waiting_for_others', None)
            txn.set(ref, {'data': json.dumps(gs)})

        try:
            patch(self._db.transaction(), gs_ref)
        except Exception as e:
            print(f"[WARN] Firestore patch_game_state_field failed for {team_key}: {e}")

    def get_all_locked_years(self) -> dict[str, int]:
        """One read of the aggregated summary instead of one read per team."""
        try:
            doc = self._meta(self._DOC_SESSION_STATE).get()
            return doc.to_dict().get('teams', {}) if doc.exists else {}
        except Exception as e:
            print(f"[WARN] Firestore get_all_locked_years failed: {e}")
            return {}

    # Cohort membership
    def mark_team_joined(self, team_key: str) -> None:
        if not team_key or team_key == '__admin__':
            return
        try:
            self._meta('joined_teams').set(
                {'teams': self._fs.ArrayUnion([team_key])}, merge=True
            )
        except Exception as e:
            print(f"[WARN] Firestore mark_team_joined failed for {team_key}: {e}")

    def get_joined_teams(self) -> set:
        try:
            doc = self._meta('joined_teams').get()
            if doc.exists:
                return set((doc.to_dict() or {}).get('teams', []))
        except Exception as e:
            print(f"[WARN] Firestore get_joined_teams failed: {e}")
        return set()

    # Sessions
    @staticmethod
    def _session_key(username: str, team_key: str) -> str:
        return f"{_safe_id(username)}__{_safe_id(team_key)}"

    def _session_doc(self, username: str, team_key: str):
        return self._db.collection(self._COL_SESSIONS).document(self._session_key(username, team_key))

    def _cached_logged_out(self, username: str, team_key: str) -> bool:
        su, st = _safe_id(username), _safe_id(team_key)
        with self._sessions_lock:
            return any(s['username'] == su and s['team_key'] == st and s['logged_out']
                       for s in self._sessions_cache)

    def is_session_active(self, username: str, team_key: str) -> bool:
        try:
            doc = self._session_doc(username, team_key).get()
            if not doc.exists:
                return False
            d = doc.to_dict()
            if d.get('logged_out', False):
                return False
            return (time.time() - d.get('last_seen', 0)) < SESSION_TIMEOUT
        except Exception:
            return False

    def register_session(self, username: str, team_key: str) -> None:
        """Heartbeat, throttled to one write per interval. Skipped after an explicit logout."""
        now = time.time()
        key = self._session_key(username, team_key)
        if (now - self._session_write_ts.get(key, 0.0)) < self._HEARTBEAT_WRITE_INTERVAL:
            return
        if self._cached_logged_out(username, team_key):
            return
        try:
            self._session_doc(username, team_key).set(
                {'last_seen': now, 'logged_out': False}, merge=True
            )
            self._session_write_ts[key] = now
        except Exception as e:
            print(f"[WARN] Firestore register_session failed for {username}: {e}")

    def activate_session(self, username: str, team_key: str) -> None:
        try:
            self._session_doc(username, team_key).set(
                {'last_seen': time.time(), 'logged_out': False}
            )
            self._session_write_ts.pop(self._session_key(username, team_key), None)
        except Exception as e:
            print(f"[WARN] Firestore activate_session failed for {username}: {e}")

    def clear_session(self, username: str, team_key: str) -> None:
        try:
            self._session_doc(username, team_key).set({'last_seen': 0, 'logged_out': True})
        except Exception as e:
            print(f"[WARN] Firestore clear_session failed for {username}: {e}")

    def get_all_sessions(self) -> list[dict]:
        """Sessions from the listener cache. `active` is computed per read so a
        user who stops heartbeating stops counting as online."""
        now = time.time()
        with self._sessions_lock:
            snapshot = list(self._sessions_cache)
        return [
            {**s, 'active': not s['logged_out'] and (now - s['last_seen']) < SESSION_TIMEOUT}
            for s in snapshot
        ]

    def set_storyboard_seen(self, username: str, team_key: str) -> None:
        try:
            self._db.collection(self._COL_USERS).document(f"{username}_{team_key}").set(
                {'storyboard_seen': True}, merge=True
            )
            with self._users_lock:
                for u in self._users_cache:
                    if u.get('username') == username and u.get('team_key') == team_key:
                        u['storyboard_seen'] = True
                        break
        except Exception as e:
            print(f"[WARN] set_storyboard_seen failed for {username}: {e}")

    def get_storyboard_seen(self, username: str, team_key: str) -> bool:
        try:
            with self._users_lock:
                for u in self._users_cache:
                    if u.get('username') == username and u.get('team_key') == team_key:
                        return bool(u.get('storyboard_seen', False))
            doc = self._db.collection(self._COL_USERS).document(f"{username}_{team_key}").get()
            if doc.exists:
                return bool(doc.to_dict().get('storyboard_seen', False))
        except Exception as e:
            print(f"[WARN] get_storyboard_seen failed for {username}: {e}")
        return False

    def clear_all_storyboard_seen(self) -> None:
        try:
            for doc in self._db.collection(self._COL_USERS).stream():
                doc.reference.set({'storyboard_seen': False}, merge=True)
            with self._users_lock:
                for u in self._users_cache:
                    u['storyboard_seen'] = False
        except Exception as e:
            print(f"[WARN] clear_all_storyboard_seen failed: {e}")

    # Controller
    def get_controller(self, team_key: str) -> str | None:
        try:
            doc = self._db.collection(self._COL_CONTROLLERS).document(_safe_id(team_key)).get()
            return doc.to_dict().get('username') if doc.exists else None
        except Exception:
            return None

    def set_controller(self, team_key: str, username: str | None) -> None:
        try:
            ref = self._db.collection(self._COL_CONTROLLERS).document(_safe_id(team_key))
            if username is None:
                ref.delete()
            else:
                ref.set({'username': username, 'claimed_at': time.time()})
        except Exception as e:
            print(f"[WARN] Firestore set_controller failed for {team_key}: {e}")

    def claim_controller(self, team_key: str, username: str) -> bool:
        ref = self._db.collection(self._COL_CONTROLLERS).document(_safe_id(team_key))

        @self._fs.transactional
        def try_claim(txn, ref):
            snap = ref.get(transaction=txn)
            if snap.exists:
                current = snap.to_dict().get('username')
                if current is not None:
                    return current == username
            txn.set(ref, {'username': username, 'claimed_at': time.time()})
            return True

        try:
            return try_claim(self._db.transaction(), ref)
        except Exception as e:
            print(f"[WARN] Firestore claim_controller failed for {team_key}: {e}")
            return False

    # Year barrier
    def increment_lock_counter(self, year: int, total_teams: int) -> bool:
        """Count a lock and claim the broadcast in one transaction.

        The first locker's `total_teams` is stored as the year's threshold and
        later lockers read it back, so every team uses the same denominator. A
        larger total from a late locker raises the threshold and re-opens the claim.
        """
        field = f"year_{year}"
        total_field = f"total_year_{year}"
        claimed_field = f"claimed_year_{year}"
        ref = self._meta('lock_counters')

        @self._fs.transactional
        def inc_and_claim(txn, ref):
            snap = ref.get(transaction=txn)
            data = (snap.to_dict() if snap.exists else {}) or {}
            new_val = data.get(field, 0) + 1

            stored_total = data.get(total_field)
            if stored_total is None:
                stored_total = total_teams
                updates = {field: new_val, total_field: stored_total}
            elif total_teams > stored_total:
                stored_total = total_teams
                updates = {field: new_val, total_field: stored_total, claimed_field: False}
            else:
                updates = {field: new_val}

            if new_val < stored_total or data.get(claimed_field, False):
                txn.set(ref, updates, merge=True)
                return False
            updates[claimed_field] = True
            txn.set(ref, updates, merge=True)
            return True

        try:
            return inc_and_claim(self._db.transaction(), ref)
        except Exception as e:
            print(f"[WARN] Firestore increment_lock_counter failed for year {year}: {e}")
            return False

    def claim_broadcast_slot(self, year: int) -> bool:
        done_field = f"done_year_{year}"
        ref = self._meta('lock_counters')

        @self._fs.transactional
        def claim(txn, ref):
            snap = ref.get(transaction=txn)
            if snap.exists and (snap.to_dict() or {}).get(done_field, False):
                return False
            txn.set(ref, {done_field: True}, merge=True)
            return True

        try:
            return claim(self._db.transaction(), ref)
        except Exception as e:
            print(f"[WARN] Firestore claim_broadcast_slot failed for year {year}: {e}")
            return False

    def mark_broadcast_done(self, year: int) -> None:
        try:
            self._meta('lock_counters').set({f"fanout_done_year_{year}": True}, merge=True)
        except Exception as e:
            print(f"[WARN] mark_broadcast_done failed for year {year}: {e}")

    def is_broadcast_done(self, year: int) -> bool:
        try:
            snap = self._meta('lock_counters').get()
            return bool((snap.to_dict() or {}).get(f"fanout_done_year_{year}", False)) if snap.exists else False
        except Exception as e:
            print(f"[WARN] Firestore is_broadcast_done failed for year {year}: {e}")
            return False

    def reset_lock_counters(self) -> None:
        try:
            self._meta('lock_counters').delete()
        except Exception as e:
            print(f"[WARN] Firestore reset_lock_counters failed: {e}")

    # Global state
    def set_paused(self, paused: bool) -> None:
        try:
            self._meta('pause_state').set({'paused': paused})
            with self._paused_cache_lock:
                self._paused_cache = paused
                self._paused_cache_ts = time.time()
        except Exception as e:
            print(f"[WARN] Firestore set_paused({paused}) failed: {e}", flush=True)

    def is_paused(self) -> bool:
        now = time.time()
        with self._paused_cache_lock:
            if (now - self._paused_cache_ts) < self._PAUSE_CACHE_TTL:
                return self._paused_cache
        try:
            doc = self._meta('pause_state').get()
            val = bool(doc.to_dict().get('paused', False)) if doc.exists else False
            with self._paused_cache_lock:
                self._paused_cache = val
                self._paused_cache_ts = time.time()
            return val
        except Exception as e:
            print(f"[WARN] Firestore is_paused read failed: {e}", flush=True)
            with self._paused_cache_lock:
                return self._paused_cache

    def load_active_scenario(self) -> tuple[str, str] | None:
        try:
            doc = self._meta('active_scenario').get()
            if not doc.exists:
                return None
            data = doc.to_dict() or {}
            country, industry = data.get('country', ''), data.get('industry', '')
            return (country, industry) if country and industry else None
        except Exception:
            return None

    def save_active_scenario(self, country: str, industry: str) -> None:
        try:
            self._meta('active_scenario').set({'country': country, 'industry': industry})
        except Exception as e:
            print(f"[WARN] Firestore save_active_scenario failed: {e}")

    def reset_all_state(self) -> None:
        for coll in (self._COL_GAME_STATES, self._COL_LOCKED,
                     self._COL_CONTROLLERS, self._COL_SESSIONS):
            try:
                for doc in self._db.collection(coll).stream():
                    doc.reference.delete()
            except Exception as e:
                print(f"[WARN] Firestore reset_all_state failed for {coll}: {e}")
        for doc_id in (self._DOC_SESSION_STATE, 'joined_teams'):
            try:
                self._meta(doc_id).delete()
            except Exception as e:
                print(f"[WARN] Firestore reset failed for meta/{doc_id}: {e}")
        self.reset_lock_counters()
        try:
            self._meta('pause_state').set({'paused': False})
        except Exception:
            pass
        with self._paused_cache_lock:
            self._paused_cache = False
            self._paused_cache_ts = 0.0
        self._session_write_ts.clear()


def create_storage() -> StorageBackend:
    """Build the backend selected by the STORAGE_BACKEND environment variable."""
    backend = os.environ.get('STORAGE_BACKEND', 'local').lower()
    if backend == 'firestore':
        print("[INFO] Using Firestore storage backend.")
        return FirestoreStorage()
    print("[INFO] Using local file storage backend.")
    return LocalStorage()
