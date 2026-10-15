"""Step248 append-only *operator-held* timeline of bounded original-source checks.

All timeline edges are independently keyed and verified, their transitions are
recomputed from MAC-verified Step247 original-source records, and a fresh
observation is appended atomically after one explicitly authorized HTTPS read.
Operator-led rollback, deletion and publisher authorship are NOT attested.
"""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import json
import re
import secrets
import sqlite3

from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.integrations.cited_answer_client import (
    ALIGNED, CONTRADICTED, ClientCitedAnswer,
)
from backend.app.integrations.source_history import (
    InvalidHistory, MAX_RECORDS, _db, _insert_verified, load_verified_answer,
)
from backend.app.integrations.source_recheck import SourceRecheck, _validated_observation

MAX_TIMELINE_OBSERVATIONS = 64
_ID = re.compile(r"[0-9a-f]{32}\Z")
_STATUS = frozenset({
    "capture_unchanged", "capture_changed_statement_unchanged",
    "bounded_statement_changed",
})
_DOMAIN = b"ai-reality-layer-step248-timeline-edge-v1\x00"


def _edge_bytes(
    root: str, seq: int, record: str, previous: str, status: str,
) -> bytes:
    return json.dumps({
        "root": root, "sequence": seq, "record": record,
        "previous": previous, "status": status,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")


def _edge_mac(key: bytes, root: str, seq: int, record: str,
              previous: str, status: str) -> str:
    return hmac.new(key, _DOMAIN + _edge_bytes(root, seq, record, previous, status),
                    sha256).hexdigest()


def _schema(db: sqlite3.Connection) -> None:
    db.execute("""
        CREATE TABLE IF NOT EXISTS source_timeline_edges (
            root_id TEXT NOT NULL,
            sequence INTEGER NOT NULL,
            record_id TEXT NOT NULL UNIQUE,
            previous_id TEXT NOT NULL,
            change_status TEXT NOT NULL,
            edge_mac TEXT NOT NULL,
            PRIMARY KEY (root_id, sequence)
        )
    """)


def _validate_input(root: str, key: bytes, request: OriginalSourceClaimRequest) -> None:
    if (type(root) is not str or _ID.fullmatch(root) is None
        or type(key) is not bytes or len(key) != 32
        or not isinstance(request, OriginalSourceClaimRequest)):
        raise InvalidHistory("invalid timeline request")


def _status(previous: ClientCitedAnswer, current: ClientCitedAnswer) -> str:
    a = previous.citation
    b = current.citation
    if (a is None or b is None
        or b.source_capture_observed_at is None
        or datetime.fromisoformat(b.source_capture_observed_at.replace("Z", "+00:00")) <
           datetime.fromisoformat(a.source_capture_observed_at.replace("Z", "+00:00"))):
        raise InvalidHistory("invalid timeline capture order")
    if a.source_capture_sha256 == b.source_capture_sha256:
        if a.source_quote_sha256 != b.source_quote_sha256 or previous.decision != current.decision:
            raise InvalidHistory("same capture has inconsistent statement")
        return "capture_unchanged"
    if a.source_quote_sha256 == b.source_quote_sha256 and previous.decision == current.decision:
        return "capture_changed_statement_unchanged"
    return "bounded_statement_changed"


def _load_chain(
    db: sqlite3.Connection, path: str, key: bytes, root: str,
    request: OriginalSourceClaimRequest,
) -> tuple[list[tuple[str, str, ClientCitedAnswer]], bool]:
    """Fail closed over the *whole* linked history, not merely the last row."""
    _schema(db)
    edges = db.execute(
        "SELECT sequence,record_id,previous_id,change_status,edge_mac "
        "FROM source_timeline_edges WHERE root_id=? ORDER BY sequence",
        (root,),
    ).fetchall()
    if len(edges) > MAX_TIMELINE_OBSERVATIONS:
        raise InvalidHistory("timeline capacity exceeded")
    if not edges:
        baseline = load_verified_answer(path, key, root, request, connection=db)
        return [(root, "baseline", baseline)], False
    if len(edges) < 2:
        raise InvalidHistory("incomplete timeline")
    output = []
    for index, row in enumerate(edges):
        seq, record_id, parent, status, mac = row
        if (
            type(seq) is not int or seq != index
            or type(record_id) is not str or _ID.fullmatch(record_id) is None
            or type(parent) is not str
            or type(status) is not str
            or status not in (_STATUS if index else {"baseline"})
            or type(mac) is not str or not hmac.compare_digest(
                _edge_mac(key, root, seq, record_id, parent, status), mac
            )
            or record_id != (root if index == 0 else record_id)
            or parent != ("" if index == 0 else output[-1][0])
        ):
            raise InvalidHistory("timeline integrity check failed")
        current = load_verified_answer(path, key, record_id, request, connection=db)
        if index and _status(output[-1][2], current) != status:
            raise InvalidHistory("timeline classification mismatch")
        output.append((record_id, status, current))
    return output, True


def _read_chain(
    path: str, key: bytes, root: str, request: OriginalSourceClaimRequest,
) -> tuple[list[tuple[str, str, ClientCitedAnswer]], bool]:
    _validate_input(root, key, request)
    try:
        with closing(_db(path)) as db:
            return _load_chain(db, path, key, root, request)
    except (sqlite3.Error, ValueError, TypeError, OverflowError,
            AttributeError, IndexError) as exc:
        raise InvalidHistory("cannot verify timeline") from exc


def latest_timeline_answer(
    path: str, key: bytes, root: str, request: OriginalSourceClaimRequest,
) -> tuple[str, ClientCitedAnswer]:
    """Preflight complete integrity and identity before any publisher egress."""
    chain, _ = _read_chain(path, key, root, request)
    if len(chain) >= MAX_TIMELINE_OBSERVATIONS:
        raise InvalidHistory("timeline capacity reached")
    return chain[-1][0], chain[-1][2]


def inspect_timeline(
    path: str, key: bytes, root: str, request: OriginalSourceClaimRequest,
) -> dict:
    """Read-only, bounded summary; quotes are never exposed."""
    chain, linked = _read_chain(path, key, root, request)
    return {
        "scope": "operator_held_original_source_timeline",
        "root_record_id": root,
        "request_binding_sha256": chain[0][2].request_binding_sha256,
        "total_observations": len(chain),
        "linked_history": linked,
        "latest_record_id": chain[-1][0],
        "observations": [{
            "sequence": i,
            "record_id": rid,
            "change_from_previous": status,
            "decision": answer.decision,
            "source_quote_sha256": answer.citation.source_quote_sha256,
            "source_capture_sha256": answer.citation.source_capture_sha256,
            "source_capture_observed_at": answer.citation.source_capture_observed_at,
        } for i, (rid, status, answer) in enumerate(chain)],
        "historical_receipt_authenticated": False,
        "publisher_authorship_verified": False,
        "factual_truth_verified": False,
        "automatic_monitoring_enabled": False,
        "externally_deployed": False,
    }


def append_verified_recheck(
    path: str, key: bytes, root: str, request: OriginalSourceClaimRequest,
    expected_latest_id: str, comparison: SourceRecheck,
) -> tuple[str, int]:
    """Atomically commit a freshly validated comparison and its linked edge.

    Re-verify the entire chain under SQLite BEGIN IMMEDIATE to prevent
    concurrent stale-baseline writers from incorrectly appending.
    """
    _validate_input(root, key, request)
    if (type(expected_latest_id) is not str or _ID.fullmatch(expected_latest_id) is None
        or type(comparison) is not SourceRecheck
        or comparison.status not in _STATUS
        or comparison.previous is None or comparison.current is None
        or comparison.previous_decision not in ("bounded_source_support", "bounded_source_contradiction")
        or comparison.current_decision not in ("bounded_source_support", "bounded_source_contradiction")
        or comparison.request_binding_sha256 is None):
        raise InvalidHistory("unverified timeline comparison")
    current_support = comparison.current_decision == "bounded_source_support"
    if type(comparison.may_use_current_as_bounded_evidence) is not bool or (
        comparison.may_use_current_as_bounded_evidence is not current_support
    ):
        raise InvalidHistory("inconsistent timeline evidence decision")
    new_answer = ClientCitedAnswer(
        decision=comparison.current_decision,
        reason_code="source_aligned" if current_support else "source_contradicted",
        answer_text=ALIGNED if current_support else CONTRADICTED,
        request_binding_sha256=comparison.request_binding_sha256,
        citation=comparison.current,
        may_use_as_bounded_evidence=current_support,
    )
    if _validated_observation(new_answer, request, datetime.now(timezone.utc)) is None:
        raise InvalidHistory("fresh source cannot be validated")
    try:
        with closing(_db(path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            chain, linked = _load_chain(db, path, key, root, request)
            if (chain[-1][0] != expected_latest_id
                or chain[-1][2].citation != comparison.previous
                or chain[-1][2].decision != comparison.previous_decision
                or len(chain) >= MAX_TIMELINE_OBSERVATIONS):
                raise InvalidHistory("timeline advanced or changed")
            if _status(chain[-1][2], new_answer) != comparison.status:
                raise InvalidHistory("timeline comparison mismatch")
            new_id = _insert_verified(db, key, request, new_answer)
            if not linked:
                db.execute(
                    "INSERT INTO source_timeline_edges VALUES (?,?,?,?,?,?)",
                    (root, 0, root, "", "baseline", _edge_mac(key, root, 0, root, "", "baseline")),
                )
            seq = len(chain)
            db.execute(
                "INSERT INTO source_timeline_edges VALUES (?,?,?,?,?,?)",
                (root, seq, new_id, expected_latest_id, comparison.status,
                 _edge_mac(key, root, seq, new_id, expected_latest_id, comparison.status)),
            )
        return new_id, len(chain) + 1
    except (sqlite3.Error, ValueError, TypeError, OverflowError,
            AttributeError, IndexError) as exc:
        raise InvalidHistory("timeline append failed") from exc


__all__ = [
    "MAX_TIMELINE_OBSERVATIONS", "latest_timeline_answer",
    "inspect_timeline", "append_verified_recheck",
]
