"""Regression checks for the Docker build-context privacy exclusions.

These assertions verify that the required ignore patterns remain present.
They do not replace a real Docker context inspection or image scan.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCKERIGNORE = ROOT / ".dockerignore"


def _patterns() -> set[str]:
    return {
        line.strip()
        for line in DOCKERIGNORE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def test_docker_context_excludes_local_private_audit_and_secrets() -> None:
    patterns = _patterns()
    required = {
        ".private-audit/",
        "private-audit*.json",
        "private-audit*.txt",
        ".arl_data/",
        ".cache/",
        "**/.env*",
        "*.env.*",
        "*.pem",
        "*.key",
        "*.p12",
        "*.pfx",
        "*.jks",
        "*.keystore",
        "credentials.json",
        "credentials.*.json",
        "credentials*.json",
        "secrets.json",
        "secrets.*.json",
        "secrets*.json",
        "*service-account*.json",
        "id_rsa",
        "id_rsa.*",
        "id_ed25519",
        "id_ed25519.*",
        "*.sqlite",
        "*.sqlite3",
        "*.db",
        "*.dump",
        "*.sql.gz",
    }
    assert required <= patterns


def test_docker_context_excludes_local_python_and_model_caches() -> None:
    patterns = _patterns()
    required = {
        ".venv/",
        "venv/",
        "ENV/",
        "env/",
        "**/__pycache__/",
        "**/*.pyc",
        ".pytest_cache/",
        ".huggingface/",
        "model_cache/",
        "datasets/",
    }
    assert required <= patterns
