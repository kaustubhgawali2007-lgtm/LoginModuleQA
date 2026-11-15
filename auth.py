"""Authentication logic for the login module: validation, hashing, lockout and sessions."""
import hashlib
import secrets

MAX_ATTEMPTS = 5
LOCK_SECONDS = 15 * 60
USERNAME_LENGTH = (5, 12)
PASSWORD_LENGTH = (8, 16)

GENERIC_ERROR = "Invalid username or password"
LOCK_ERROR = "Account temporarily locked. Try again after 15 minutes."


def hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000).hex()


def validate(username, password):
    """Return an error message for invalid input, or None when the input is acceptable."""
    if not username and not password:
        return "Username and password are required"
    if not username:
        return "Username is required"
    if not password:
        return "Password is required"
    if not USERNAME_LENGTH[0] <= len(username) <= USERNAME_LENGTH[1]:
        return "Username must be %d to %d characters" % USERNAME_LENGTH
    if not PASSWORD_LENGTH[0] <= len(password) <= PASSWORD_LENGTH[1]:
        return "Password must be %d to %d characters" % PASSWORD_LENGTH
    return None


class AttemptTracker:
    """Counts consecutive failed logins per username and locks the account for a fixed time."""

    def __init__(self, clock):
        self._clock = clock
        self._state = {}

    def is_locked(self, username):
        state = self._state.get(username)
        return bool(state) and state["locked_until"] > self._clock()

    def record_failure(self, username):
        state = self._state.setdefault(username, {"count": 0, "locked_until": 0})
        state["count"] += 1
        if state["count"] >= MAX_ATTEMPTS:
            state["locked_until"] = self._clock() + LOCK_SECONDS
            state["count"] = 0

    def record_success(self, username):
        self._state.pop(username, None)


class SessionStore:
    """Server-side sessions: a session exists only while its id is stored here."""

    def __init__(self):
        self._sessions = {}

    def create(self, username):
        sid = secrets.token_urlsafe(32)
        self._sessions[sid] = username
        return sid

    def get(self, sid):
        return self._sessions.get(sid)

    def destroy(self, sid):
        self._sessions.pop(sid, None)
