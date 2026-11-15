# Login Module QA Project

Login module of the Online Movie Ticket Booking System, with a test plan.
Version 1.0 is the first prototype that is tested in this project.

## Files
- `app.py`, `auth.py`, `templates/` - the login module
- `Test_Plan.md`, `Test_Cases.csv` - test plan and the 28 designed test cases
- `tests/` - automated test cases (`run_tests.py`, pytest wrapper, Chromium screenshot script)
- `results/` - recorded results: round 1 on v1.0 and round 2 (regression) on v1.1
- `evidence/` - screenshots from the browser run
- `Defect_Report.md` - defects with status

## Run
    pip install -r requirements.txt -r requirements-test.txt
    python tests/run_tests.py my_run
    python -m pytest tests -q
    python app.py
