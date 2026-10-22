"""Read-only full-history scanner checks on synthetic test repositories."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
SCANNER=ROOT/"scripts"/"prepublication_history_audit.py"


def _cmd(*args,cwd=None):
    p=subprocess.run(args,cwd=cwd,capture_output=True,text=True)
    assert p.returncode==0, f"Test git setup failed: {args[:3]}"
    return p.stdout


def _make_mirror(folder:Path,include_deleted_secret:bool):
    source=folder/"src"
    _cmd("git","init","-q",str(source))
    _cmd("git","config","user.name","Synthetic Tester",cwd=source)
    _cmd("git","config","user.email","synthetic@example.invalid",cwd=source)
    (source/"hello.txt").write_text("hello\n",encoding="utf-8")
    _cmd("git","add",".",cwd=source)
    _cmd("git","commit","-qm","initial",cwd=source)
    if include_deleted_secret:
        (source/".env.production").write_text("PRIVATE_TOKEN=placeholder\n",encoding="utf-8")
        (source/"historic.txt").write_text("ghp_"+"A"*36+"\n",encoding="utf-8")
        _cmd("git","add",".env.production","historic.txt",cwd=source)
        _cmd("git","commit","-qm","temporary dummy credential",cwd=source)
        _cmd("git","rm","-q",".env.production","historic.txt",cwd=source)
        _cmd("git","commit","-qm","delete dummy credential files",cwd=source)
    mirror=folder/"mirror.git"
    _cmd("git","clone","--mirror","-q",str(source),str(mirror))
    return mirror


def test_previous_commit_deleted_token_found_without_echoing_it():
    with tempfile.TemporaryDirectory() as t:
        mirror=_make_mirror(Path(t),True)
        r=subprocess.run([sys.executable,str(SCANNER),str(mirror)],
                         capture_output=True,text=True)
        assert r.returncode==1
        assert ("ghp_"+"A"*36) not in r.stdout
        report=json.loads(r.stdout)
        assert report["finding_counts"]["github_token"]>=1
        assert report["finding_counts"]["sensitive_filename_review"]>=1
        assert report["publication_cleared"] is False
        assert report["secrets_values_included"] is False


def test_even_clean_scan_does_not_clear_publication():
    with tempfile.TemporaryDirectory() as t:
        mirror=_make_mirror(Path(t),False)
        r=subprocess.run([sys.executable,str(SCANNER),str(mirror)],
                         capture_output=True,text=True)
        assert r.returncode==0
        report=json.loads(r.stdout)
        assert report["finding_counts"]=={}
        assert report["publication_cleared"] is False
