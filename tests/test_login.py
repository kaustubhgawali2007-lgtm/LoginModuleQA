"""pytest entry point: python -m pytest tests -q   (Blocked and Not Executed cases are skipped)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from testcases import BLOCKED, CASES, NOT_EXEC, PASS, execute_all  # noqa: E402

_results = {}


@pytest.fixture(scope="module", autouse=True)
def run_everything():
    _results.update(execute_all())


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_case(case):
    status, actual = _results[case["id"]]
    if status in (BLOCKED, NOT_EXEC):
        pytest.skip("%s: %s" % (status, actual))
    assert status == PASS, "%s | expected: %s | actual: %s" % (case["scenario"], case["expected"], actual)
