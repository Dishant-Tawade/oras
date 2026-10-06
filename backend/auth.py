"""Authentication: password hashing, controller roles, sessions and admin tokens."""
import hashlib
import hmac
import secrets
import threading
import time

from storage import create_storage

_store = create_storage()


def get_store():
    return _store


# Passwords
# Stored as "pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>".

_PBKDF2_ITERATIONS = 200_000
_PBKDF2_ALGO = 'sha256'
_PBKDF2_PREFIX = 'pbkdf2_sha256'


def hash_pw(pw: str, salt: bytes | None = None) -> str:
    """Hash a password with PBKDF2-HMAC-SHA256 and a random salt."""
    if salt is None:
        salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(_PBKDF2_ALGO, pw.encode(), salt, _PBKDF2_ITERATIONS)
    return f"{_PBKDF2_PREFIX}${_PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_pw(pw: str, stored: str) -> bool:
    if not stored or not stored.startswith(_PBKDF2_PREFIX + '$'):
        return False
    try:
        _, iter_str, salt_hex, hash_hex = stored.split('$', 3)
        iterations = int(iter_str)
        salt = bytes.fromhex(salt_hex)
        expect = bytes.fromhex(hash_hex)
    except (ValueError, AttributeError):
        return False
    actual = hashlib.pbkdf2_hmac(_PBKDF2_ALGO, pw.encode(), salt, iterations)
    return hmac.compare_digest(actual, expect)


def authenticate(username: str, password: str, team_key: str) -> dict | None:
    """Return the user record if the credentials match, else None."""
    for u in _store.load_users():
        if u['username'] == username and u['team_key'] == team_key:
            return u if verify_pw(password, u.get('password', '')) else None
    return None


# Controller role (one per team)

def get_controller(team_key: str) -> str | None:
    return _store.get_controller(team_key)


def claim_controller(team_key: str, username: str) -> bool:
    """Claim the controller role if unclaimed. True if `username` now holds it."""
    return _store.claim_controller(team_key, username)


def release_controller(team_key: str, username: str) -> None:
    if _store.get_controller(team_key) == username:
        _store.set_controller(team_key, None)


# Sessions

def is_session_active(username: str, team_key: str) -> bool:
    return _store.is_session_active(username, team_key)


def register_session(username: str, team_key: str) -> None:
    """Start a session on login, clearing any logout marker."""
    _store.activate_session(username, team_key)


def refresh_session(username: str, team_key: str) -> None:
    """Heartbeat. Ignored if the user has logged out."""
    _store.register_session(username, team_key)


def clear_session(username: str, team_key: str) -> None:
    _store.clear_session(username, team_key)


# Admin tokens
# Issued by /api/login for admins and sent as X-Admin-Token. Only the SHA-256
# digest is kept, in process memory, so tokens do not survive a restart or
# work across server instances. Expiry is sliding.

_ADMIN_TOKEN_TTL = 12 * 3600
_ADMIN_TOKENS: dict[str, dict] = {}  # digest -> {username, expires_at}
_ADMIN_TOKENS_LOCK = threading.Lock()


def _admin_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_admin_token(username: str) -> str:
    token = secrets.token_urlsafe(32)
    now = time.time()
    with _ADMIN_TOKENS_LOCK:
        _ADMIN_TOKENS[_admin_token_hash(token)] = {
            'username': username,
            'expires_at': now + _ADMIN_TOKEN_TTL,
        }
        for digest in [d for d, info in _ADMIN_TOKENS.items() if info['expires_at'] < now]:
            del _ADMIN_TOKENS[digest]
    return token


def verify_admin_token(token: str) -> str | None:
    """Return the admin username for a valid token and extend its expiry."""
    if not token:
        return None
    digest = _admin_token_hash(token)
    now = time.time()
    with _ADMIN_TOKENS_LOCK:
        info = _ADMIN_TOKENS.get(digest)
        if info is None:
            return None
        if info['expires_at'] < now:
            del _ADMIN_TOKENS[digest]
            return None
        info['expires_at'] = now + _ADMIN_TOKEN_TTL
        return info['username']


def revoke_admin_token(token: str) -> bool:
    if not token:
        return False
    with _ADMIN_TOKENS_LOCK:
        return _ADMIN_TOKENS.pop(_admin_token_hash(token), None) is not None
