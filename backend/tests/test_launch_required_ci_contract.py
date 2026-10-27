"""Guard the critical GitHub Actions job identities required by main ruleset.

This is a local structural regression, not proof of GitHub's remote settings.
Actual ruleset enforcement must be confirmed in GitHub separately.
"""
from pathlib import Path
import re

import pytest


WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"


@pytest.mark.parametrize(
    "filename, required_job_name",
    [
        ("backend-tests.yml", "Python 3.13 full suite"),
        ("step255-real-unified-ask.yml",
         "Real official publisher heldout + optional pinned model"),
    ],
)
def test_required_status_check_names_are_kept_in_pr_workflows(
    filename: str, required_job_name: str
) -> None:
    workflow = (WORKFLOWS / filename).read_text(encoding="utf-8")
    assert re.search(r"^  pull_request:\s*$", workflow, flags=re.MULTILINE)
    assert re.search(r"^  push:\s*$", workflow, flags=re.MULTILINE)
    assert re.search(
        r"^\s{4}name:\s*" + re.escape(required_job_name) + r"\s*$",
        workflow,
        flags=re.MULTILINE,
    ), f"Protected required job identity changed or is absent: {filename}"
    assert re.search(
        r"^permissions:\s*\n\s+contents:\s*read\s*$",
        workflow,
        flags=re.MULTILINE,
    )


@pytest.mark.parametrize(
    "filename", ["backend-tests.yml", "step255-real-unified-ask.yml"]
)
def test_critical_ci_uses_immutable_action_references(filename: str) -> None:
    workflow = (WORKFLOWS / filename).read_text(encoding="utf-8")
    refs = re.findall(r"^\s*(?:-\s*)?uses:\s*(\S+)", workflow, flags=re.MULTILINE)
    assert refs, f"No Actions dependencies were found: {filename}"
    for ref in refs:
        assert re.fullmatch(
            r"[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+@[0-9a-f]{40}", ref
        ), f"Action must be pinned to an immutable commit: {filename}"
