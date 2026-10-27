"""Unit regressions for launch-only production manifest and rights metadata guard."""
import pytest

from scripts.launch_production_dependency_guard import (
    DOCKERFILE, MANIFEST, check_production_dockerfile, production_pins,
)


def test_current_production_dependencies_are_exact_unique_pins():
    packages = production_pins(MANIFEST.read_text(encoding="utf-8"))
    assert len(packages) == 14
    assert packages["fastapi"][1] == "0.141.1"
    assert packages["uvicorn"][1] == "0.52.4"


@pytest.mark.parametrize("contents", [
    "",
    "fastapi>=0.141.1",
    "fastapi",
    "-r requirements-dev.txt",
    "--extra-index-url https://example.com",
    "fastapi @ https://example.com/archive.zip",
    "git+https://example.com/remote.git",
    "fastapi==0.141.1\nFastAPI==0.141.1",
    "typing_extensions==4.16.0\ntyping-extensions==4.16.0",
    "fastapi==0.141.1 --hash=sha256:abc",
])
def test_unsafe_or_duplicate_production_dependency_is_refused(contents):
    with pytest.raises(ValueError):
        production_pins(contents)


def test_actual_production_container_only_uses_reviewed_manifest():
    check_production_dockerfile(DOCKERFILE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("tampering", [
    "COPY backend/requirements-dev.txt /srv/backend/requirements.txt",
    "python -m pip install -r /srv/backend/requirements.txt",
    "requirements-nli-shadow.txt",
])
def test_unapproved_dockerfile_change_is_refused(tampering):
    with pytest.raises(ValueError):
        check_production_dockerfile(tampering)
