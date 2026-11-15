"""Login module for the Online Movie Ticket Booking System (version 1.0 prototype)."""
import hashlib
import hmac
import os
import sqlite3
import time

from flask import Flask, redirect, render_template, request, session, url_for

MAX_ATTEMPTS = 5
LOCK_SECONDS = 15 * 60

SEED_USERS = {
    "rohan123": "Secure2026",
    "ravi5": "Passw0rd",
    "studentadmin": "Passw0rdPassw0rd",
}


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
    if not 5 <= len(username) <= 12:
        return "Username must be 5 to 12 characters"
    if not 8 <= len(password) <= 16:
        return "Password must be 8 to 16 characters"
    return None


def create_app(config=None):
    app = Flask(__name__)
    app.secret_key = "dev-secret-key"
    if config:
        app.config.update(config)

    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.execute("CREATE TABLE users (username TEXT PRIMARY KEY, salt TEXT, pw_hash TEXT)")
    for name, pw in SEED_USERS.items():
        salt = os.urandom(16)
        db.execute("INSERT INTO users VALUES (?, ?, ?)", (name, salt.hex(), hash_password(pw, salt)))
    db.commit()
    app.config["DB"] = db
    app.config.setdefault("CLOCK", time.time)
    failures = {}  # username -> {"count": int, "locked_until": float}

    @app.route("/")
    def index():
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            error = validate(username, password)
            if error:
                return render_template("login.html", error=error), 400
            now = app.config["CLOCK"]()
            state = failures.setdefault(username, {"count": 0, "locked_until": 0})
            if state["locked_until"] > now:
                return render_template(
                    "login.html", error="Account temporarily locked. Try again after 15 minutes."
                ), 429
            row = db.execute(
                "SELECT salt, pw_hash FROM users WHERE username = ?", (username,)
            ).fetchone()
            if row is None or not hmac.compare_digest(
                hash_password(password, bytes.fromhex(row[0])), row[1]
            ):
                state["count"] += 1
                if state["count"] >= MAX_ATTEMPTS:
                    state["locked_until"] = now + LOCK_SECONDS
                    state["count"] = 0
                return render_template("login.html", error="Invalid username or password"), 401
            failures.pop(username, None)
            session["user"] = username
            return redirect(url_for("dashboard"))
        return render_template("login.html")

    @app.route("/dashboard")
    def dashboard():
        if "user" not in session:
            return redirect(url_for("login"))
        return render_template("dashboard.html", user=session["user"])

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    return app


if __name__ == "__main__":
    create_app().run(debug=False)
