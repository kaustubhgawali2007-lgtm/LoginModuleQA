"""Execute all login test cases and save the results.

Usage:  python tests/run_tests.py <label>          e.g.  python tests/run_tests.py round1_v1.0
Writes results/<label>.json and results/<label>.csv and prints a summary.
Pass percentage = Passed / Executed x 100, where Executed = Passed + Failed.
Blocked and Not Executed cases are reported separately and never counted as passed.
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from testcases import BLOCKED, CASES, FAIL, NOT_EXEC, PASS, execute_all  # noqa: E402


def summarize(results):
    counts = {s: sum(1 for st, _ in results.values() if st == s) for s in (PASS, FAIL, BLOCKED, NOT_EXEC)}
    executed = counts[PASS] + counts[FAIL]
    counts["Executed"] = executed
    counts["Total"] = len(results)
    counts["PassPercentage"] = round(counts[PASS] / executed * 100, 1) if executed else 0.0
    return counts


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "run"
    results = execute_all()
    root = os.environ.get("RESULTS_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
    os.makedirs(root, exist_ok=True)
    with open(os.path.join(root, label + ".json"), "w") as f:
        json.dump({"results": {k: {"status": v[0], "actual": v[1]} for k, v in results.items()}, "summary": summarize(results)}, f, indent=1)
    with open(os.path.join(root, label + ".csv"), "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Test Case ID", "Expected Result", "Actual Result", "Status"])
        for case in CASES:
            st, actual = results[case["id"]]
            w.writerow([case["id"], case["expected"], actual, st])
    s = summarize(results)
    for case in CASES:
        st, actual = results[case["id"]]
        print("%-6s %-13s %s" % (case["id"], st, actual))
    print("\nPassed=%d Failed=%d Blocked=%d NotExecuted=%d | Executed=%d | Pass%%=%.1f" % (
        s[PASS], s[FAIL], s[BLOCKED], s[NOT_EXEC], s["Executed"], s["PassPercentage"]))


if __name__ == "__main__":
    main()
