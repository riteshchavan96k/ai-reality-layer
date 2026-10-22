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


def test_utf16_and_commit_message_secrets_are_detected_without_values():
    with tempfile.TemporaryDirectory() as t:
        root=Path(t)
        mirror=_make_mirror(root,False)
        source=root/'src'
        token='ghp_'+'B'*36
        (source/'encoded.txt').write_text(token,encoding='utf-16')
        _cmd('git','add','encoded.txt',cwd=source)
        _cmd('git','commit','-qm','synthetic '+token,cwd=source)
        _cmd('git','fetch','-q',str(source),'+refs/heads/*:refs/heads/*',cwd=mirror)
        r=subprocess.run([sys.executable,str(SCANNER),str(mirror)],capture_output=True,text=True)
        report=json.loads(r.stdout)
        assert r.returncode==1 and token not in r.stdout
        assert report['finding_counts']['github_token']==2
        assert report['commit_and_tag_objects_scanned']>=2


def test_sensitive_alias_of_identical_blob_is_not_lost():
    with tempfile.TemporaryDirectory() as t:
        root=Path(t)
        mirror=_make_mirror(root,False)
        source=root/'src'
        (source/'.env.production').write_text('hello\n',encoding='utf-8')
        _cmd('git','add','.env.production',cwd=source)
        _cmd('git','commit','-qm','same blob sensitive alias',cwd=source)
        _cmd('git','fetch','-q',str(source),'+refs/heads/*:refs/heads/*',cwd=mirror)
        r=subprocess.run([sys.executable,str(SCANNER),str(mirror)],capture_output=True,text=True)
        assert r.returncode==1
        assert json.loads(r.stdout)['finding_counts']['sensitive_filename_review']==1


def test_shallow_history_is_refused():
    with tempfile.TemporaryDirectory() as t:
        root=Path(t)
        _make_mirror(root,True)
        shallow=root/'shallow.git'
        _cmd('git','clone','--bare','--depth=1',(root/'src').as_uri(),str(shallow))
        r=subprocess.run([sys.executable,str(SCANNER),str(shallow)],capture_output=True,text=True)
        assert r.returncode==2
        assert 'shallow' in r.stderr
