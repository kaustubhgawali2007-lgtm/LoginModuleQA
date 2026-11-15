"""Login module for the Online Movie Ticket Booking System."""
import hmac
import os
import sqlite3
import time

from flask import Flask, redirect, render_template, request, session, url_for

from auth import (GENERIC_ERROR, LOCK_ERROR, AttemptTracker, SessionStore,
                  hash_password, validate)

SEED_USERS = {
    "rohan123": "Secure2026",
    "ravi5": "Passw0rd",
    "studentadmin": "Passw0rdPassw0rd",
}


def create_app(config=None):
    app = Flask(__name__)
    app.secret_key = "dev-secret-key"
    app.config.setdefault("CLOCK", time.time)
    if config:
        app.config.update(config)

    db = sqlite3.connect(":memory:", check_same_thread=False)
    db.execute("CREATE TABLE users (username TEXT PRIMARY KEY, salt TEXT, pw_hash TEXT)")
    for name, pw in SEED_USERS.items():
        salt = os.urandom(16)
        db.execute("INSERT INTO users VALUES (?, ?, ?)", (name, salt.hex(), hash_password(pw, salt)))
    db.commit()
    app.config["DB"] = db

    attempts = AttemptTracker(lambda: app.config["CLOCK"]())
    sessions = SessionStore()

    def credentials_ok(username, password):
        row = db.execute(
            "SELECT salt, pw_hash FROM users WHERE username = ?", (username,)
        ).fetchone()
        return row is not None and hmac.compare_digest(
            hash_password(password, bytes.fromhex(row[0])), row[1]
        )

    @app.route("/")
    def index():
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html")
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        error = validate(username, password)
        if error:
            return render_template("login.html", error=error), 400
        if attempts.is_locked(username):
            return render_template("login.html", error=LOCK_ERROR), 429
        if not credentials_ok(username, password):
            attempts.record_failure(username)
            return render_template("login.html", error=GENERIC_ERROR), 401
        attempts.record_success(username)
        session["sid"] = sessions.create(username)
        return redirect(url_for("dashboard"))

    @app.route("/dashboard")
    def dashboard():
        user = sessions.get(session.get("sid"))
        if user is None:
            return redirect(url_for("login"))
        return render_template("dashboard.html", user=user)

    @app.route("/logout")
    def logout():
        sessions.destroy(session.get("sid"))
        session.clear()
        return redirect(url_for("login"))

    return app


if __name__ == "__main__":
    create_app().run(debug=False)
