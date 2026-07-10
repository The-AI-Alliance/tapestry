"""Static audit of the contributed workflows, as a unit test.

``nika check`` verifies the task DAG, tool surface, types, and permits
without executing anything, so it doubles as a cheap conformance test for
the workflow files in this contribution. The test skips cleanly when the
``nika`` binary is not installed (for example on CI runners), per the
contrib guidance on keeping optional toolchains non-blocking.
"""

import pathlib
import shutil
import subprocess

import pytest

WORKFLOWS_DIR = pathlib.Path(__file__).resolve().parent.parent / "workflows"
REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


def workflow_files() -> list[pathlib.Path]:
    """Every workflow shipped by this contribution."""
    return sorted(WORKFLOWS_DIR.glob("*.nika.yaml"))


def test_contribution_ships_at_least_one_workflow() -> None:
    """The workflows directory is the contribution's substance."""
    assert workflow_files(), f"no *.nika.yaml under {WORKFLOWS_DIR}"


@pytest.mark.skipif(shutil.which("nika") is None, reason="nika binary not installed")
@pytest.mark.parametrize("workflow", workflow_files(), ids=lambda p: p.name)
def test_workflow_passes_static_audit(workflow: pathlib.Path) -> None:
    """``nika check`` exits 0: DAG, tools, types, and permits all verify."""
    result = subprocess.run(
        ["nika", "check", str(workflow.relative_to(REPO_ROOT))],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, f"nika check failed for {workflow.name}:\n{result.stdout}\n{result.stderr}"
