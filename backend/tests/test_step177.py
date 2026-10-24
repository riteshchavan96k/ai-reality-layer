from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
DEV_REQUIREMENTS = ROOT / "backend" / "requirements-dev.txt"
PRODUCTION_REQUIREMENTS = ROOT / "backend" / "requirements.txt"
PYTEST_INI = ROOT / "pytest.ini"
WORKFLOW = ROOT / ".github" / "workflows" / "backend-tests.yml"
README = ROOT / "README.md"


def _read(path: Path) -> str:
    data = path.read_bytes()
    if data.startswith(
        (bytes.fromhex("fffe"), bytes.fromhex("feff"))
    ):
        return data.decode("utf-16")
    return data.decode("utf-8-sig")


def test_development_requirements_layer_on_production_requirements():
    content = _read(DEV_REQUIREMENTS)

    assert "-r requirements.txt" in content
    assert "pytest==9.0.2" in content


def test_pytest_remains_out_of_production_requirements():
    production = _read(PRODUCTION_REQUIREMENTS).lower()

    assert "pytest" not in production


def test_pytest_configuration_targets_complete_backend_suite():
    content = _read(PYTEST_INI)

    assert "testpaths = backend/tests" in content
    assert "python_files = test_*.py" in content
    assert "pythonpath = ." in content
    assert "addopts = -ra" in content


def test_backend_ci_workflow_has_safe_triggers_and_permissions():
    content = _read(WORKFLOW)

    assert "name: Backend tests" in content
    assert "push:" in content
    assert "pull_request:" in content
    assert "workflow_dispatch:" in content
    assert "pull_request_target:" not in content
    assert "permissions:\n  contents: read" in content
    assert "secrets." not in content


def test_backend_ci_workflow_uses_pinned_project_python_and_dev_dependencies():
    content = _read(WORKFLOW)

    assert 'python-version: "3.13"' in content
    assert "backend/requirements.txt" in content
    assert "backend/requirements-dev.txt" in content
    assert "python -m pip install -r backend/requirements-dev.txt" in content


def test_backend_ci_workflow_uses_current_node24_action_majors():
    content = _read(WORKFLOW)

    # Pin reviewed Node24-major action releases to immutable Git object IDs.
    assert "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7" in content
    assert "actions/setup-python@6d4fd22b20465ccc0f7354476588e8df7c9ca0e0 # v7" in content
    assert "actions/checkout@v7" not in content
    assert "actions/setup-python@v7" not in content


def test_all_github_workflows_use_reviewed_immutable_action_revisions():
    # Any new action, or revised action version, requires explicit test review.
    expected = {
        "actions/checkout": "3d3c42e5aac5ba805825da76410c181273ba90b1",
        "actions/setup-python": "6d4fd22b20465ccc0f7354476588e8df7c9ca0e0",
        "actions/upload-artifact": "ea165f8d65b6e75b540449e92b4886f43607fa02",
    }
    workflows = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    assert len(workflows) >= 24
    for workflow in workflows:
        content = _read(workflow)
        uses = [
            line.strip().split("uses:", 1)[1].split("#", 1)[0].strip()
            for line in content.splitlines()
            if line.strip().startswith("uses:")
            or line.strip().startswith("- uses:")
        ]
        assert len(uses) >= 2, workflow.name
        for ref in uses:
            assert "@" in ref, (workflow.name, ref)
            action, revision = ref.rsplit("@", 1)
            assert action in expected, (workflow.name, action)
            assert revision == expected[action], (workflow.name, ref)


def test_backend_ci_workflow_compiles_before_running_full_test_suite():
    content = _read(WORKFLOW)

    compile_command = "python -m compileall -q backend/app"
    pytest_command = "python -m pytest"

    assert compile_command in content
    assert pytest_command in content
    assert content.index(compile_command) < content.index(pytest_command)

    assert "backend/tests/test_step" not in content


def test_backend_ci_workflow_is_bounded_and_cancels_superseded_runs():
    content = _read(WORKFLOW)

    assert "timeout-minutes: 20" in content
    assert "concurrency:" in content
    assert "cancel-in-progress: true" in content


def test_readme_documents_reproducible_local_validation_commands():
    content = _read(README)

    assert "## Development validation" in content
    assert "python -m pip install -r backend/requirements-dev.txt" in content
    assert "python -m pytest" in content
    assert "GitHub Actions" in content

def test_grounding_authorization_contract_modules_import_without_cycle():
    code = (
        "import backend.app.reality."
        "grounding_execution_authorization_consumption_decision_result_"
        "consumption_result_decision_result_consumption as consumption; "
        "import backend.app.reality."
        "grounding_execution_authorization_consumption_decision_result_"
        "consumption_result_decision_result_consumption_result as result; "
        "assert consumption."
        "GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumer; "
        "assert result."
        "GroundingExecutionAuthorizationConsumptionDecisionResultConsumptionResultDecisionResultConsumptionResult"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr

