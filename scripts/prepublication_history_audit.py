#!/usr/bin/env python3
"""Read-only prepublication scan of ALL reachable Git blobs in a local mirror.

No detected secret VALUES are printed or uploaded. Screen findings manually;
zero matches is not proof of safety. GitHub historical Actions logs, unreachable
server-side objects and repository account secrets are outside this scan.
"""
from __future__ import annotations

import collections
import json
from pathlib import Path
import re
import subprocess
import sys

PATTERNS = {
    "private_key": re.compile(rb"-----BEGIN (?:OPENSSH |RSA |EC |DSA |ENCRYPTED )?PRIVATE KEY-----"),
    "github_token": re.compile(rb"\b(?:github_pat_|gh[pousr]_)[A-Za-z0-9_]{30,}"),
    "openai_key": re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}"),
    "aws_access_key_id": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "google_api_key": re.compile(rb"\bAIza[0-9A-Za-z_-]{35}\b"),
    "huggingface_access_token": re.compile(rb"\bhf_[A-Za-z0-9]{30,}\b"),
    "slack_token": re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{20,}"),
    "embedded_credential_url": re.compile(
        rb"(?:https?|postgres(?:ql)?|mysql|redis|mongodb(?:\+srv)?):\/\/"
        rb"[^\s:/@]{1,90}:[^\s/@]{1,150}@[^\s/]+"
    ),
    "secret_literal_assignment_review": re.compile(
        rb"(?i)\b(?:password|client_secret|api[_-]?key|access[_-]?token|"
        rb"auth[_-]?token|private[_-]?key|secret[_-]?key)"
        rb"\b[ \t]{0,12}[:=][ \t]*[\"'][^\"'\r\n]{16,}[\"']"
    ),
}
SENSITIVE_PATH = re.compile(
    r"(?i)(^|/)(?:\.env(?:\.|$)|\.envrc$|\.npmrc$|\.pypirc$|"
    r"id_rsa(?:\.|$)|id_ed25519(?:\.|$)|credentials?(?:\.|$)|"
    r"secrets?(?:\.|$))|(?i:\.(?:pem|p12|pfx|key|jks|keystore|kdbx)$)"
)
LICENSE_PATH = re.compile(r"(?i)(^|/)(?:license|copying|notice)(?:\.[^/]*)?$")
MAX_BLOB_BYTES = 5_000_000
MAX_EXAMPLES = 20


def git(repo: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], input=input_bytes,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    if proc.returncode:
        raise RuntimeError("Git inspection failed: " + " ".join(args[:3]))
    return proc.stdout


def scan(repo: Path) -> dict:
    git(repo, "rev-parse", "--git-dir")
    refs = git(repo, "for-each-ref", "--format=%(refname)").decode(
        "utf-8", "replace").splitlines()
    objects = git(repo, "rev-list", "--objects", "--all").decode(
        "utf-8", "replace").splitlines()
    paths: dict[str, str] = {}
    for line in objects:
        oid, _, path = line.partition(" ")
        if oid:
            paths.setdefault(oid, path)
    checks = git(
        repo, "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)",
        input_bytes=("\n".join(paths) + "\n").encode("ascii"),
    )
    blobs: list[str] = []
    for line in checks.decode("ascii", "replace").splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[1] == "blob":
            blobs.append(parts[0])
    counts = collections.Counter()
    samples: dict[str, list[dict]] = collections.defaultdict(list)

    def flag(label: str, oid: str, path: str) -> None:
        counts[label] += 1
        if len(samples[label]) < MAX_EXAMPLES:
            samples[label].append({
                "path": path or "(unknown-history-path)",
                "git_object": oid[:12],
            })

    proc = subprocess.Popen(
        ["git", "-C", str(repo), "cat-file", "--batch"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert proc.stdin is not None and proc.stdout is not None
    try:
        for oid in blobs:
            path = paths[oid]
            if path and SENSITIVE_PATH.search(path):
                flag("sensitive_filename_review", oid, path)
            if path and LICENSE_PATH.search(path):
                flag("historical_license_or_notice_file_review", oid, path)
            proc.stdin.write((oid+"\n").encode("ascii"))
            proc.stdin.flush()
            head = proc.stdout.readline().decode(
                "ascii", "replace").strip().split()
            if len(head) != 3 or head[0] != oid or head[1] != "blob":
                raise RuntimeError("Unexpected git batch response")
            size = int(head[2])
            if size > MAX_BLOB_BYTES:
                flag("oversized_blob_not_scanned", oid, path)
                remaining = size
                while remaining:
                    block = proc.stdout.read(min(65536, remaining))
                    if not block:
                        raise RuntimeError("Unexpected oversized blob EOF")
                    remaining -= len(block)
            else:
                value = proc.stdout.read(size)
                if len(value) != size:
                    raise RuntimeError("Unexpected blob EOF")
                for label, regex in PATTERNS.items():
                    if regex.search(value):
                        flag(label, oid, path)
                if b"\x00" in value:
                    flag("binary_blob_review", oid, path)
            if proc.stdout.read(1) != b"\n":
                raise RuntimeError("Unexpected blob delimiter")
    finally:
        proc.stdin.close()
        if proc.poll() is None:
            proc.terminate()
        proc.wait(timeout=10)
    authors = git(repo, "log", "--all", "--format=%an").decode(
        "utf-8", "replace").splitlines()
    return {
        "refs_inspected": len(refs),
        "reachable_git_objects_identified": len(paths),
        "reachable_blobs_scanned_or_flagged": len(blobs),
        "git_commits_recorded_across_all_refs": len(authors),
        "commit_author_display_names_only": dict(collections.Counter(authors)),
        "finding_counts": dict(counts),
        "redacted_finding_locations": dict(samples),
        "secrets_values_included": False,
        "publication_cleared": False,
        "coverage_limits": [
            "GitHub-hosted Actions logs, artifacts, PR references and comments require separate review.",
            "Unreachable server-side Git objects, LFS and submodules need separate treatment.",
            "Binary and oversized objects, unknown key formats and contractual IP are not cleared.",
            "Review a complete authorized --mirror clone, not a shallow checkout.",
        ],
        "next_action": "Private manual triage, verified second scanner, history/log review and owner signoff",
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/prepublication_history_audit.py LOCAL_MIRROR_GIT_DIR", file=sys.stderr)
        return 2
    repo = Path(sys.argv[1]).expanduser().resolve()
    if not repo.exists():
        print("Repository path does not exist", file=sys.stderr)
        return 2
    try:
        result = scan(repo)
    except (RuntimeError, ValueError, OSError) as exc:
        print("Audit did not finish: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    serious = [
        k for k, n in result["finding_counts"].items()
        if n and k not in {"historical_license_or_notice_file_review"}
    ]
    return 1 if serious else 0


if __name__ == "__main__":
    raise SystemExit(main())
