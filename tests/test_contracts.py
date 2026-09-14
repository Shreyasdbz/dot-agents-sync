import copy
from pathlib import Path

import pytest
from dasync.config import default_project_id
from dasync.contracts import validate
from dasync.errors import DasyncError


def planning_context():
    return {
        "version": 1,
        "authority": "github",
        "reference": "https://example.com/board",
        "active_milestone": "m1",
        "milestones": [
            {
                "id": "m1",
                "outcome": "First usable release",
                "status": "active",
                "exit_criteria": ["A user can finish the primary workflow"],
                "dependencies": [],
                "phases": [
                    {
                        "id": "p1",
                        "outcome": "Working vertical slice",
                        "tasks": [
                            {
                                "id": "t1",
                                "outcome": "Persist an item",
                                "acceptance": ["Item survives restart"],
                                "verification": ["Integration test"],
                            }
                        ],
                    }
                ],
            },
            {
                "id": "m2",
                "outcome": "Expand capabilities",
                "status": "future",
                "exit_criteria": ["Expansion validated"],
                "dependencies": ["m1"],
                "planning_task": {"id": "plan-m2", "outcome": "Plan this milestone into phases and tasks"},
            },
        ],
    }


def test_immediate_milestone_only():
    value = planning_context()
    validate("plan-context", value)
    value["milestones"][1]["phases"] = copy.deepcopy(value["milestones"][0]["phases"])
    with pytest.raises(DasyncError, match="Future milestones"):
        validate("plan-context", value)


def test_milestone_cycle():
    value = planning_context()
    value["milestones"][0]["dependencies"] = ["m2"]
    with pytest.raises(DasyncError, match="cycle"):
        validate("plan-context", value)


def test_task_id_collision():
    value = planning_context()
    value["milestones"][1]["planning_task"]["id"] = "t1"
    with pytest.raises(DasyncError, match="globally unique"):
        validate("plan-context", value)


@pytest.mark.parametrize("directory", ["My Project", "123", "日本語", "a.b", "--"])
def test_default_project_id_accepts_ordinary_directories(directory):
    assert default_project_id(Path(directory))
    value = planning_context()
    value["active_milestone"] = default_project_id(Path(directory))
    value["milestones"][0]["id"] = value["active_milestone"]
    value["milestones"][1]["dependencies"] = [value["active_milestone"]]
    validate("plan-context", value)
