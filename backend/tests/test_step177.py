from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEV_REQUIREMENTS = ROOT / "backend" / "requirements-dev.txt"
PRODUCTION_REQUIREMENTS = ROOT / "backend" / "requirements.txt"
PYTEST_INI = ROOT / "pytest.ini"
WORKFLOW = ROOT / ".github" / "workflows" / "backend-tests.yml"
README = ROOT / "README.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


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
