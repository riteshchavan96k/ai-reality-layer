"""Fail-closed structural guard and bounded licensing metadata for the alpha runtime.

This script does not replace package advisories, container-image scanning,
contractual licence review, or an actual deployed-asset inventory.
"""
from __future__ import annotations

import argparse
from importlib import metadata
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "backend" / "requirements.txt"
DOCKERFILE = ROOT / "Dockerfile"
PIN = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)==([A-Za-z0-9][A-Za-z0-9.+!_-]*)$")


def production_pins(contents: str) -> dict[str, tuple[str, str]]:
    """Reject unpinned, duplicated, remote, option, or mixed-source lines."""
    result: dict[str, tuple[str, str]] = {}
    for line_num, raw in enumerate(contents.splitlines(), 1):
        value = raw.strip()
        if not value or value.startswith("#"):
            continue
        match = PIN.fullmatch(value)
        if match is None:
            raise ValueError(f"non-exact or unsupported production pin at line {line_num}")
        package, version = match.groups()
        normalized = re.sub(r"[-_.]+", "-", package).lower()
        if normalized in result:
            raise ValueError(f"duplicate production dependency at line {line_num}")
        result[normalized] = (package, version)
    if not result:
        raise ValueError("empty production dependency manifest")
    return result


def check_production_dockerfile(contents: str) -> None:
    if "COPY backend/requirements.txt /srv/backend/requirements.txt" not in contents:
        raise ValueError("Docker build does not copy the reviewed production manifest")
    if "python -m pip install --no-cache-dir -r /srv/backend/requirements.txt" not in contents:
        raise ValueError("Docker build no longer installs the reviewed production manifest")
    if any(name in contents for name in (
        "requirements-dev.txt", "requirements-nli-shadow.txt",
        "requirements-nli-quality.txt",
    )):
        raise ValueError("production image references dev/optional ML requirements")


def _license_metadata(distribution: metadata.Distribution) -> str:
    fields = distribution.metadata
    value = fields.get("License-Expression") or fields.get("License")
    if value and len(value.strip()) <= 140 and "\n" not in value.strip():
        return value.strip()
    classes = [
        item.removeprefix("License ::").strip()
        for item in fields.get_all("Classifier", [])
        if item.startswith("License ::")
    ]
    return " | ".join(classes) if classes else "NOT DECLARED / OWNER REVIEW NEEDED"


def runtime_license_inventory(pins: dict[str, tuple[str, str]]) -> list[str]:
    """Emit only non-secret distribution metadata, not a legal clearance."""
    rows = []
    for normalized, (name, version) in sorted(pins.items()):
        installed = metadata.distribution(name)
        if installed.version != version:
            raise ValueError(f"runtime version does not match pinned manifest: {name}")
        rows.append(f"{name}=={version} | declared license metadata: {_license_metadata(installed)}")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Review initial production dependency policy")
    parser.add_argument("--runtime-license-metadata", action="store_true")
    args = parser.parse_args()
    try:
        pins = production_pins(MANIFEST.read_text(encoding="utf-8"))
        check_production_dockerfile(DOCKERFILE.read_text(encoding="utf-8"))
        print(f"Verified {len(pins)} strictly pinned direct production requirements")
        if args.runtime_license_metadata:
            print("Distribution declarations only; NOT a licence-chain or usage-rights audit.")
            for line in runtime_license_inventory(pins):
                print(line)
    except (ValueError, UnicodeError, OSError, metadata.PackageNotFoundError) as exc:
        print(f"Production dependency policy failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
