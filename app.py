"""Login module for the Online Movie Ticket Booking System (version 1.0 prototype)."""
import hashlib
import hmac
import os
import sqlite3

from flask import Flask, redirect, render_template, request, session, url_for

SEED_USERS = {
    "rohan123": "Secure2026",
    "ravi5": "Passw0rd",
    "studentadmin": "Passw0rdPassw0rd",
}


def hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000).hex()


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

    @app.route("/")
    def index():
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            row = db.execute(
                "SELECT salt, pw_hash FROM users WHERE username = ?", (username,)
            ).fetchone()
            if row is None:
                error = "Invalid username"
            elif not hmac.compare_digest(hash_password(password, bytes.fromhex(row[0])), row[1]):
                error = "Incorrect password"
            else:
                session["user"] = username
                return redirect(url_for("dashboard"))
            return render_template("login.html", error=error), 401
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
