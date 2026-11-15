# Login Module Test Plan

## Objective
Verify that the login module authenticates valid users, rejects invalid input and credentials, and resists common attacks.

## Techniques
Functional, negative, boundary value analysis, equivalence partitioning, security and regression testing.

## Input rules under test
- Username: 5 to 12 characters, case-sensitive
- Password: 8 to 16 characters
- Account lock after 5 consecutive failed attempts (15 minutes)
- Sessions end at logout

## Test cases
- TC-01 (Functional): Login with valid credentials
- TC-02 (Functional): Login with an invalid username
- TC-03 (Functional): Login with an incorrect password
- TC-04 (Functional): Submit the form with both fields empty
- TC-05 (Functional): Submit the form with an empty username
- TC-06 (Functional): Submit the form with an empty password
- TC-07 (Boundary): Username length 4 (below minimum of 5)
- TC-08 (Boundary): Username length 5 and password length 8 (minimum values)
- TC-09 (Boundary): Username length 12 and password length 16 (maximum values)
- TC-10 (Boundary): Username length 13 (above maximum of 12)
- TC-11 (Boundary): Password length 7 (below minimum of 8)
- TC-12 (Boundary): Password length 17 (above maximum of 16)
- TC-13 (Security): Repeated failed login attempts (account protection)
- TC-14 (Security): SQL injection in the username field
- TC-15 (Security): SQL injection in the password field
- TC-16 (Security): Script injection (XSS) in the username field
- TC-17 (Security): Account enumeration: compare errors for unknown user and wrong password
- TC-18 (Security): Password is masked and stored as a hash
- TC-19 (Security): Session cookie has the HttpOnly flag
- TC-20 (Security): Open a protected page without logging in
- TC-21 (Session): Logout ends the session
- TC-22 (Session): Reuse of an old session cookie after logout
- TC-23 (Negative): Username with the wrong letter case
- TC-24 (Negative): Password with a leading or trailing space
- TC-25 (Negative): Very long input (1000 characters)
- TC-26 (Security): Account lock expires after 15 minutes
- TC-27 (Security): Login over HTTPS (credentials encrypted in transit)
- TC-28 (Compatibility): Login in Firefox and Safari

## Exit criteria
All executed test cases pass and no Critical or Major defect is open.
