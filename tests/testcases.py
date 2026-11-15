"""Test cases for the login module.

Every test case has a design part (scenario, preconditions, input, steps, expected result)
and an execution function that drives the application and returns (status, actual_result).
"""
import html
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from app import create_app  # noqa: E402

PASS, FAIL, BLOCKED, NOT_EXEC = "Pass", "Fail", "Blocked", "Not Executed"
USER, GOOD_PW = "rohan123", "Secure2026"
WRONG_PW = "Wrong@1234"


# ---------------------------------------------------------------- helpers
def fresh():
    app = create_app()
    return app, app.test_client()


def post(client, username, password):
    return client.post("/login", data={"username": username, "password": password})


def message(resp):
    m = re.search(r'id="error">(.*?)</div>', resp.get_data(as_text=True), re.S)
    return html.unescape(m.group(1)).strip() if m else ""


def location(resp):
    return resp.headers.get("Location", "")


def logged_in(client):
    return client.get("/dashboard").status_code == 200


def describe(resp):
    m = message(resp)
    if resp.status_code == 302:
        return "HTTP 302 redirect to %s" % location(resp)
    return "HTTP %d, message: '%s'" % (resp.status_code, m) if m else "HTTP %d, no message shown" % resp.status_code


def verdict(ok, actual):
    return (PASS if ok else FAIL), actual


def denied(resp, client):
    return resp.status_code in (400, 401, 403, 423, 429) and not logged_in(client)


# ---------------------------------------------------------------- execution functions
def tc01(ctx):
    app, c = fresh()
    r = post(c, USER, GOOD_PW)
    dash = c.get("/dashboard")
    cookie = c.get_cookie("session") is not None
    ok = r.status_code == 302 and location(r).endswith("/dashboard") and "Welcome, rohan123" in dash.get_data(as_text=True) and cookie
    return verdict(ok, "%s; dashboard %s; session cookie %s" % (
        describe(r), "shows 'Welcome, rohan123'" if "Welcome, rohan123" in dash.get_data(as_text=True) else "not shown", "set" if cookie else "not set"))


def tc02(ctx):
    app, c = fresh()
    r = post(c, "nouser99", GOOD_PW)
    return verdict(denied(r, c) and message(r) != "", describe(r) + "; no session created")


def tc03(ctx):
    app, c = fresh()
    r = post(c, USER, WRONG_PW)
    return verdict(denied(r, c) and message(r) != "", describe(r) + "; no session created")


def tc04(ctx):
    app, c = fresh()
    r = post(c, "", "")
    m = message(r).lower()
    return verdict(r.status_code == 400 and "required" in m, describe(r))


def tc05(ctx):
    app, c = fresh()
    r = post(c, "", GOOD_PW)
    m = message(r).lower()
    return verdict(r.status_code == 400 and "username" in m and "required" in m, describe(r))


def tc06(ctx):
    app, c = fresh()
    r = post(c, USER, "")
    m = message(r).lower()
    return verdict(r.status_code == 400 and "password" in m and "required" in m, describe(r))


def tc07(ctx):
    app, c = fresh()
    r = post(c, "abcd", GOOD_PW)
    return verdict(r.status_code == 400 and "5 to 12" in message(r), describe(r))


def tc08(ctx):
    app, c = fresh()
    r = post(c, "ravi5", "Passw0rd")
    return verdict(r.status_code == 302 and logged_in(c), describe(r) + "; dashboard accessible")


def tc09(ctx):
    app, c = fresh()
    r = post(c, "studentadmin", "Passw0rdPassw0rd")
    return verdict(r.status_code == 302 and logged_in(c), describe(r) + "; dashboard accessible")


def tc10(ctx):
    app, c = fresh()
    r = post(c, "abcdefghijklm", GOOD_PW)
    return verdict(r.status_code == 400 and "5 to 12" in message(r), describe(r))


def tc11(ctx):
    app, c = fresh()
    r = post(c, USER, "Abc1234")
    return verdict(r.status_code == 400 and "8 to 16" in message(r), describe(r))


def tc12(ctx):
    app, c = fresh()
    r = post(c, USER, "Abcdefghij1234567")
    return verdict(r.status_code == 400 and "8 to 16" in message(r), describe(r))


def tc13(ctx):
    app, c = fresh()
    codes = [post(c, USER, WRONG_PW).status_code for _ in range(5)]
    r = post(c, USER, GOOD_PW)
    locked = r.status_code in (423, 429) and "locked" in message(r).lower() and not logged_in(c)
    if locked:
        return PASS, "5 failures returned %s; 6th attempt with correct password rejected: %s" % (codes, describe(r))
    return FAIL, "5 failures returned %s; 6th attempt with correct password: %s; no lock applied" % (codes, describe(r))


def tc14(ctx):
    app, c = fresh()
    r = post(c, "rohan123'--", WRONG_PW)
    return verdict(r.status_code < 500 and denied(r, c), describe(r) + "; no session created")


def tc15(ctx):
    app, c = fresh()
    r = post(c, USER, "' OR '1'='1")
    return verdict(r.status_code < 500 and denied(r, c), describe(r) + "; no session created")


def tc16(ctx):
    app, c = fresh()
    payload = "<script>alert(1)</script>"
    r = post(c, payload, GOOD_PW)
    reflected = payload in r.get_data(as_text=True)
    return verdict(not reflected and denied(r, c), describe(r) + "; payload %s in response" % ("reflected unescaped" if reflected else "not reflected"))


def tc17(ctx):
    app, c = fresh()
    r1 = post(c, "nouser99", GOOD_PW)
    r2 = post(c, USER, WRONG_PW)
    same = message(r1) == message(r2) and r1.status_code == r2.status_code
    return verdict(same, "Unknown user: HTTP %d '%s'; wrong password: HTTP %d '%s'" % (
        r1.status_code, message(r1), r2.status_code, message(r2)))


def tc18(ctx):
    app, c = fresh()
    page = c.get("/login").get_data(as_text=True)
    masked = re.search(r'<input[^>]*type="password"[^>]*name="password"', page) is not None
    stored = app.config["DB"].execute("SELECT pw_hash FROM users WHERE username = ?", (USER,)).fetchone()[0]
    hashed = stored != GOOD_PW and re.fullmatch(r"[0-9a-f]{64}", stored) is not None
    return verdict(masked and hashed, "Password input type=password: %s; stored value is a %d-character hash, not plain text: %s" % (
        "yes" if masked else "no", len(stored), "yes" if hashed else "no"))


def tc19(ctx):
    app, c = fresh()
    r = post(c, USER, GOOD_PW)
    cookies = " ".join(r.headers.getlist("Set-Cookie"))
    return verdict("HttpOnly" in cookies, "Set-Cookie header %s HttpOnly" % ("includes" if "HttpOnly" in cookies else "lacks"))


def tc20(ctx):
    app, c = fresh()
    r = c.get("/dashboard")
    return verdict(r.status_code == 302 and location(r).endswith("/login"), describe(r))


def tc21(ctx):
    app, c = fresh()
    post(c, USER, GOOD_PW)
    before = logged_in(c)
    c.get("/logout")
    r = c.get("/dashboard")
    return verdict(before and r.status_code == 302 and location(r).endswith("/login"),
                   "Dashboard before logout: HTTP 200; after logout: %s" % describe(r))


def tc22(ctx):
    app, c = fresh()
    post(c, USER, GOOD_PW)
    old_cookie = c.get_cookie("session").value
    c.get("/logout")
    attacker = app.test_client()
    attacker.set_cookie("session", old_cookie)
    r = attacker.get("/dashboard")
    ok = r.status_code == 302 and location(r).endswith("/login")
    return verdict(ok, "Dashboard requested with the old session cookie after logout: %s" % (
        describe(r) if ok else "HTTP %d, protected page still accessible" % r.status_code))


def tc23(ctx):
    app, c = fresh()
    r = post(c, "ROHAN123", GOOD_PW)
    return verdict(denied(r, c), describe(r) + "; no session created")


def tc24(ctx):
    app, c = fresh()
    r1 = post(c, USER, " " + GOOD_PW)
    r2 = post(c, USER, GOOD_PW + " ")
    ok = denied(r1, c) and denied(r2, c)
    return verdict(ok, "Leading space: HTTP %d; trailing space: HTTP %d; no session created" % (r1.status_code, r2.status_code))


def tc25(ctx):
    app, c = fresh()
    r = post(c, "u" * 1000, "p" * 1000)
    return verdict(r.status_code < 500 and denied(r, c), describe(r) + "; no server error")


def tc26(ctx):
    prior = ctx.get("TC-13")
    if prior is None or prior[0] != PASS:
        return BLOCKED, "Cannot be tested: account lock is not enforced (TC-13 failed), so there is no lock to expire"
    app, c = fresh()
    now = [1_000_000.0]
    app.config["CLOCK"] = lambda: now[0]
    for _ in range(5):
        post(c, USER, WRONG_PW)
    now[0] += 14 * 60
    early = post(c, USER, GOOD_PW)
    now[0] += 60 + 1
    late = post(c, USER, GOOD_PW)
    ok = early.status_code in (423, 429) and late.status_code == 302 and logged_in(c)
    return verdict(ok, "After 14 minutes: HTTP %d (still locked); after 15 minutes 1 second: %s" % (early.status_code, describe(late)))


def tc27(ctx):
    return NOT_EXEC, "Not run: the test environment serves plain HTTP; needs an HTTPS deployment"


def tc28(ctx):
    return NOT_EXEC, "Not run: only Chromium is available in the test environment"


# ---------------------------------------------------------------- design of the test cases
U = "1. Open /login.  2. Enter the username and password.  3. Click Login.  4. Observe the response."
CASES = [
 dict(id="TC-01", cat="Functional", scenario="Login with valid credentials", pre="User rohan123 is registered", inp="rohan123 / Secure2026",
      steps=U + "  5. Open the dashboard.", expected="User is authenticated, redirected to the dashboard and a session is created", short="Login successful", run=tc01),
 dict(id="TC-02", cat="Functional", scenario="Login with an invalid username", pre="Username nouser99 is not registered", inp="nouser99 / Secure2026",
      steps=U, expected="Access is denied and an error message is displayed", short="Access denied", run=tc02),
 dict(id="TC-03", cat="Functional", scenario="Login with an incorrect password", pre="User rohan123 is registered", inp="rohan123 / Wrong@1234",
      steps=U, expected="Access is denied and an error message is displayed", short="Access denied", run=tc03),
 dict(id="TC-04", cat="Functional", scenario="Submit the form with both fields empty", pre="Login page is open", inp="(empty) / (empty)",
      steps="1. Open /login.  2. Leave both fields empty.  3. Click Login.", expected="Required-field validation is displayed", short="Validation displayed", run=tc04),
 dict(id="TC-05", cat="Functional", scenario="Submit the form with an empty username", pre="Login page is open", inp="(empty) / Secure2026",
      steps="1. Open /login.  2. Enter only the password.  3. Click Login.", expected="Username validation is displayed", short="Username validation", run=tc05),
 dict(id="TC-06", cat="Functional", scenario="Submit the form with an empty password", pre="Login page is open", inp="rohan123 / (empty)",
      steps="1. Open /login.  2. Enter only the username.  3. Click Login.", expected="Password validation is displayed", short="Password validation", run=tc06),
 dict(id="TC-07", cat="Boundary", scenario="Username length 4 (below minimum of 5)", pre="Login page is open", inp="abcd / Secure2026",
      steps=U, expected="Validation message: username must be 5 to 12 characters", short="Length validation", run=tc07),
 dict(id="TC-08", cat="Boundary", scenario="Username length 5 and password length 8 (minimum values)", pre="User ravi5 is registered", inp="ravi5 / Passw0rd",
      steps=U, expected="Login succeeds", short="Login successful", run=tc08),
 dict(id="TC-09", cat="Boundary", scenario="Username length 12 and password length 16 (maximum values)", pre="User studentadmin is registered", inp="studentadmin / Passw0rdPassw0rd",
      steps=U, expected="Login succeeds", short="Login successful", run=tc09),
 dict(id="TC-10", cat="Boundary", scenario="Username length 13 (above maximum of 12)", pre="Login page is open", inp="abcdefghijklm / Secure2026",
      steps=U, expected="Validation message: username must be 5 to 12 characters", short="Length validation", run=tc10),
 dict(id="TC-11", cat="Boundary", scenario="Password length 7 (below minimum of 8)", pre="Login page is open", inp="rohan123 / Abc1234",
      steps=U, expected="Validation message: password must be 8 to 16 characters", short="Length validation", run=tc11),
 dict(id="TC-12", cat="Boundary", scenario="Password length 17 (above maximum of 16)", pre="Login page is open", inp="rohan123 / Abcdefghij1234567",
      steps=U, expected="Validation message: password must be 8 to 16 characters", short="Length validation", run=tc12),
 dict(id="TC-13", cat="Security", scenario="Repeated failed login attempts (account protection)", pre="User rohan123 is registered, not locked", inp="5 x (rohan123 / Wrong@1234), then rohan123 / Secure2026",
      steps="1. Submit a wrong password 5 times.  2. Submit the correct password.", expected="After 5 failures the account is locked; the 6th attempt is rejected with a lock message", short="Protection operates as specified", run=tc13),
 dict(id="TC-14", cat="Security", scenario="SQL injection in the username field", pre="Login page is open", inp="rohan123'-- / Wrong@1234",
      steps=U, expected="Input is treated as data; access denied; no server error", short="Access denied", run=tc14),
 dict(id="TC-15", cat="Security", scenario="SQL injection in the password field", pre="User rohan123 is registered", inp="rohan123 / ' OR '1'='1",
      steps=U, expected="Input is treated as data; access denied; no server error", short="Access denied", run=tc15),
 dict(id="TC-16", cat="Security", scenario="Script injection (XSS) in the username field", pre="Login page is open", inp="<script>alert(1)</script> / Secure2026",
      steps=U, expected="Access denied; the script is not reflected unescaped in the page", short="Not reflected", run=tc16),
 dict(id="TC-17", cat="Security", scenario="Account enumeration: compare errors for unknown user and wrong password", pre="User rohan123 is registered", inp="nouser99 / Secure2026 and rohan123 / Wrong@1234",
      steps="1. Submit an unknown username.  2. Submit a valid username with a wrong password.  3. Compare the responses.", expected="Both responses are identical, so valid usernames are not revealed", short="Identical error", run=tc17),
 dict(id="TC-18", cat="Security", scenario="Password is masked and stored as a hash", pre="Login page is open", inp="Open the page and inspect the user table",
      steps="1. Open /login.  2. Check the password input type.  3. Read the stored value for rohan123.", expected="Password input is masked; stored value is a hash, not plain text", short="Masked and hashed", run=tc18),
 dict(id="TC-19", cat="Security", scenario="Session cookie has the HttpOnly flag", pre="User rohan123 is registered", inp="rohan123 / Secure2026",
      steps="1. Log in.  2. Read the Set-Cookie header.", expected="Session cookie is marked HttpOnly", short="HttpOnly set", run=tc19),
 dict(id="TC-20", cat="Security", scenario="Open a protected page without logging in", pre="No active session", inp="GET /dashboard",
      steps="1. Open /dashboard directly.", expected="User is redirected to the login page", short="Redirect to login", run=tc20),
 dict(id="TC-21", cat="Session", scenario="Logout ends the session", pre="User is logged in", inp="rohan123 / Secure2026, then Logout",
      steps="1. Log in.  2. Click Logout.  3. Open /dashboard.", expected="After logout the dashboard redirects to the login page", short="Redirect to login", run=tc21),
 dict(id="TC-22", cat="Session", scenario="Reuse of an old session cookie after logout", pre="User logged in and logged out; old cookie saved", inp="Saved session cookie",
      steps="1. Log in and save the session cookie.  2. Log out.  3. Send the saved cookie to /dashboard.", expected="Protected page is not accessible; redirect to login", short="Redirect to login", run=tc22),
 dict(id="TC-23", cat="Negative", scenario="Username with the wrong letter case", pre="User rohan123 is registered", inp="ROHAN123 / Secure2026",
      steps=U, expected="Access is denied (usernames are case-sensitive)", short="Access denied", run=tc23),
 dict(id="TC-24", cat="Negative", scenario="Password with a leading or trailing space", pre="User rohan123 is registered", inp="rohan123 / ' Secure2026' and 'Secure2026 '",
      steps=U, expected="Access is denied (spaces are part of the password)", short="Access denied", run=tc24),
 dict(id="TC-25", cat="Negative", scenario="Very long input (1000 characters)", pre="Login page is open", inp="1000 x 'u' / 1000 x 'p'",
      steps=U, expected="Handled without a server error; access denied", short="Denied, no error", run=tc25),
 dict(id="TC-26", cat="Security", scenario="Account lock expires after 15 minutes", pre="Account locked by TC-13 (depends on TC-13)", inp="Correct password at 14 min and at 15 min 1 s",
      steps="1. Lock the account.  2. Try after 14 minutes.  3. Try after 15 minutes.", expected="Still locked at 14 minutes; login succeeds after 15 minutes", short="Lock expires", run=tc26),
 dict(id="TC-27", cat="Security", scenario="Login over HTTPS (credentials encrypted in transit)", pre="Application deployed with TLS", inp="rohan123 / Secure2026 over https://",
      steps="1. Open the https:// URL.  2. Log in.  3. Check the connection and cookie flags.", expected="Login works over HTTPS; session cookie has the Secure flag", short="HTTPS works", run=tc27),
 dict(id="TC-28", cat="Compatibility", scenario="Login in Firefox and Safari", pre="Browsers installed", inp="rohan123 / Secure2026",
      steps="1. Open /login in each browser.  2. Log in.", expected="Login works the same as in Chromium", short="Works in all browsers", run=tc28),
]


def execute_all():
    """Run every case in order and return {id: (status, actual)}; cases may depend on earlier results."""
    ctx = {}
    for case in CASES:
        try:
            ctx[case["id"]] = case["run"](ctx)
        except Exception as exc:  # an unexpected crash is recorded as a failure, never hidden
            ctx[case["id"]] = (FAIL, "Test crashed: %s: %s" % (type(exc).__name__, exc))
    return ctx
