"""Browser (Chromium) evidence for key test cases.

Usage:  python tests/ui_evidence.py <output_dir>
Starts the login application from this repository, drives the real login page with
Playwright and saves a screenshot for each scenario. Prints what was observed.
"""
import os
import socket
import sys
import threading

from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from app import create_app  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "evidence"
os.makedirs(OUT, exist_ok=True)


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main():
    port = free_port()
    server = make_server("127.0.0.1", port, create_app(), threaded=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % port
    seen = []

    def shot(page, name, note):
        page.screenshot(path=os.path.join(OUT, name + ".png"))
        seen.append("%s: %s" % (name, note))

    def login(page, user, pw):
        page.goto(base + "/login")
        page.fill("#username", user)
        page.fill("#password", pw)
        page.click("#login-btn")

    def text(page):
        return page.inner_text("body").replace("\n", " | ")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = lambda: browser.new_context(viewport={"width": 480, "height": 400}, device_scale_factor=2)  # noqa: E731

        c = ctx(); pg = c.new_page()
        login(pg, "rohan123", "Secure2026")
        shot(pg, "TC-01_valid_login", text(pg)); c.close()

        c = ctx(); pg = c.new_page()
        login(pg, "nouser99", "Secure2026")
        shot(pg, "TC-02_invalid_username", text(pg)); c.close()

        c = ctx(); pg = c.new_page()
        login(pg, "", "")
        shot(pg, "TC-04_empty_fields", text(pg)); c.close()

        c = ctx(); pg = c.new_page()
        pg.goto(base + "/login")
        pg.fill("#username", "rohan123")
        pg.fill("#password", "Secure2026")
        masked = pg.get_attribute("#password", "type")
        shot(pg, "TC-18_password_masked", "password input type=%s" % masked); c.close()

        a = ctx(); pa = a.new_page()
        login(pa, "rohan123", "Secure2026")
        saved = a.cookies()
        pa.click("#logout")
        b = ctx(); b.add_cookies(saved)
        pb = b.new_page()
        pb.goto(base + "/dashboard")
        shot(pb, "TC-22_session_replay", "old cookie replayed after logout, page shows: " + text(pb))
        a.close(); b.close()

        # last, because a lock stays active for the rest of this server run
        c = ctx(); pg = c.new_page()
        for _ in range(5):
            login(pg, "rohan123", "Wrong@1234")
        login(pg, "rohan123", "Secure2026")
        shot(pg, "TC-13_repeated_failures", "after 5 wrong passwords, correct password: " + text(pg)); c.close()
        browser.close()
    server.shutdown()
    print("\n".join(seen))


if __name__ == "__main__":
    main()
