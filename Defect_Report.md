# Defect Report - Login Module

## BUG-01 - No required-field validation
- Related test cases: TC-04, TC-05, TC-06
- Description: Empty username and/or password are processed as a login attempt instead of being rejected with a required-field message.
- Steps to reproduce: 1. Open /login.  2. Leave the username and/or password empty.  3. Click Login.
- Expected result: Required-field validation message (HTTP 400)
- Actual result: HTTP 401 with 'Invalid username' or 'Incorrect password'
- Severity: Major
- Priority: P2
- Recommended corrective action: Validate required fields before authentication and show a clear message.
- Current status: Open

## BUG-02 - No length validation
- Related test cases: TC-07, TC-10, TC-11, TC-12
- Description: Usernames outside 5 to 12 characters and passwords outside 8 to 16 characters are not rejected by validation.
- Steps to reproduce: 1. Open /login.  2. Enter a 4- or 13-character username, or a 7- or 17-character password.  3. Click Login.
- Expected result: Validation message about the allowed length (HTTP 400)
- Actual result: HTTP 401 with a generic credentials error
- Severity: Minor
- Priority: P3
- Recommended corrective action: Add length checks (5-12 and 8-16 characters) before the database lookup.
- Current status: Open

## BUG-03 - Account enumeration through different error messages
- Related test cases: TC-17
- Description: An unknown username and a wrong password give different messages, so an attacker can find out which usernames exist.
- Steps to reproduce: 1. Submit nouser99 / Secure2026.  2. Submit rohan123 / Wrong@1234.  3. Compare the messages.
- Expected result: Identical response for both
- Actual result: 'Invalid username' for the first and 'Incorrect password' for the second
- Severity: Major
- Priority: P2
- Recommended corrective action: Return one generic message for every failed authentication.
- Current status: Open

## BUG-04 - No protection against repeated failed logins
- Related test cases: TC-13 (TC-26 blocked)
- Description: Unlimited wrong passwords are accepted, which allows password guessing; the correct password still works after any number of failures.
- Steps to reproduce: 1. Submit a wrong password for rohan123 five times.  2. Submit the correct password.
- Expected result: Account locked; 6th attempt rejected with a lock message
- Actual result: HTTP 302: login succeeded, no lock applied
- Severity: Critical
- Priority: P1
- Recommended corrective action: Lock the account for 15 minutes after 5 consecutive failures.
- Current status: Open

## BUG-05 - Session still valid after logout
- Related test cases: TC-22
- Description: Logout only clears the browser cookie. The session lives inside the signed cookie, so a copy of the old cookie still opens protected pages.
- Steps to reproduce: 1. Log in and save the session cookie.  2. Log out.  3. Send the saved cookie to /dashboard.
- Expected result: Redirect to the login page
- Actual result: HTTP 200: dashboard shown to the old cookie
- Severity: Critical
- Priority: P1
- Recommended corrective action: Keep sessions on the server and delete the session on logout.
- Current status: Open

