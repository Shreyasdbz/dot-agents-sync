"""Check completeness of an externally observed behavioral evaluation record."""

import json
import sys
from pathlib import Path


def check(result, cases):
    case = next(c for c in cases if c["id"] == result["case_id"])
    for key in ("provider", "model", "source_revision", "output"):
        if not isinstance(result.get(key), str) or not result[key].strip():
            raise ValueError(f"Missing {key}")
    if not isinstance(result.get("observed_actions"), list):
        raise ValueError("Missing observed actions")
    assertions = result.get("assertions", [])
    if {a["id"] for a in assertions} != {a["id"] for a in case["assertions"]}:
        raise ValueError("Assertion coverage differs from the case")
    if len(assertions) != len(case["assertions"]):
        raise ValueError("Duplicate assertions")
    for assertion in assertions:
        if type(assertion.get("passed")) is not bool or not assertion.get("evidence", "").strip():
            raise ValueError("Every assertion needs an observed verdict and evidence")
    return all(a["passed"] for a in assertions)


if __name__ == "__main__":
    try:
        cases = json.loads(Path(__file__).with_name("cases.json").read_text())
        result = json.loads(Path(sys.argv[1]).read_text())
        passed = check(result, cases)
        print(json.dumps({"complete": True, "recorded_pass": passed, "independently_verified": False}))
        raise SystemExit(0 if passed else 1)
    except (IndexError, KeyError, ValueError, StopIteration) as exc:
        print(json.dumps({"complete": False, "error": str(exc)}))
        raise SystemExit(2)
