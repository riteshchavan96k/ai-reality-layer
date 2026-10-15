"""Step251 operator-authorized persistent writes, keyed idempotency and atomicity.

Only the already-approved one-source observation pipeline may supply answers.
A client operation ID protects against duplicate database records on retries;
it is NOT cryptographic proof of publisher origin or global at-most-once egress.
"""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import json
import re
import sqlite3

from backend.app.api.claim_request_binding import claim_request_binding_sha256
from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.integrations.cited_answer_client import ClientCitedAnswer
from backend.app.integrations.source_history import (
    InvalidHistory, _db, _insert_verified, _canonical,
)
from backend.app.integrations.source_recheck import (
    _validated_observation, reconcile_observations,
)
from backend.app.integrations.source_timeline import (
    MAX_TIMELINE_OBSERVATIONS, _load_chain, _edge_mac, _status,
)

_ID = re.compile(r"[0-9a-f]{32}\Z")
_DOMAIN = b"ai-reality-layer-step251-write-operation-v1\x00"
MAX_OPERATIONS = 1000


def _schema(db: sqlite3.Connection) -> None:
    db.execute("""
        CREATE TABLE IF NOT EXISTS timeline_write_operations (
            operation_id TEXT PRIMARY KEY NOT NULL,
            payload TEXT NOT NULL,
            mac TEXT NOT NULL
        )
    """)


def _mac(key: bytes, operation_id: str, payload: bytes) -> str:
    return hmac.new(
        key, _DOMAIN + operation_id.encode("ascii") + b"\x00" + payload,
        sha256,
    ).hexdigest()


def _intent(request: OriginalSourceClaimRequest, kind: str,
            root: str, expected: str) -> dict:
    if (
        not isinstance(request, OriginalSourceClaimRequest)
        or kind not in ("create", "append")
        or type(root) is not str
        or type(expected) is not str
        or (kind == "create" and (root or expected))
        or (kind == "append" and (
            _ID.fullmatch(root) is None or _ID.fullmatch(expected) is None
        ))
    ):
        raise InvalidHistory("invalid write intent")
    return {
        "kind": kind, "request_binding_sha256": claim_request_binding_sha256(request),
        "root": root, "expected": expected,
    }


def _receipt(op: str, kind: str, root: str, rid: str, seq: int,
             status: str, answer: ClientCitedAnswer, *, replayed: bool) -> dict:
    c = answer.citation
    return {
        "outcome": "created" if kind == "create" else "appended",
        "reason": "verified_observation_persisted",
        "operation_id": op,
        "request_binding_sha256": answer.request_binding_sha256,
        "root_record_id": root,
        "record_id": rid,
        "sequence": seq,
        "change_status": status,
        "decision": answer.decision,
        "source_quote_sha256": c.source_quote_sha256,
        "source_capture_sha256": c.source_capture_sha256,
        "source_capture_observed_at": c.source_capture_observed_at,
        "replayed": replayed,
        "may_use_historical_as_current_evidence": False,
        "factual_truth_verified": False,
        "publisher_authorship_verified": False,
        "historical_receipt_authenticated": False,
        "automatic_monitoring_enabled": False,
        "externally_deployed": False,
    }


def _find(
    db: sqlite3.Connection, path: str, key: bytes, op: str,
    request: OriginalSourceClaimRequest, intent: dict,
) -> dict | None:
    table = db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='timeline_write_operations'"
    ).fetchone()
    if not table:
        return None
    row = db.execute(
        "SELECT payload,mac FROM timeline_write_operations WHERE operation_id=?",
        (op,),
    ).fetchone()
    if row is None:
        return None
    raw_payload, tag = row
    if (type(raw_payload) is not str or type(tag) is not str or
        len(raw_payload) > 2048):
        raise InvalidHistory("invalid keyed write receipt")
    try:
        encoded = raw_payload.encode("ascii")
        if not hmac.compare_digest(_mac(key, op, encoded), tag):
            raise InvalidHistory("invalid keyed write receipt")
        raw = json.loads(encoded)
        if (
            type(raw) is not dict
            or set(raw) != {"intent", "record_id", "sequence", "status", "root_record_id"}
            or type(raw["intent"]) is not dict
            or raw["intent"] != intent
            or type(raw["record_id"]) is not str or _ID.fullmatch(raw["record_id"]) is None
            or type(raw["root_record_id"]) is not str or _ID.fullmatch(raw["root_record_id"]) is None
            or type(raw["sequence"]) is not int
            or type(raw["status"]) is not str
        ):
            raise InvalidHistory("write operation ID reused or receipt inconsistent")
        chain, _ = _load_chain(db, path, key, raw["root_record_id"], request)
        seq = raw["sequence"]
        if (
            seq < 0 or seq >= len(chain)
            or chain[seq][0] != raw["record_id"]
            or chain[seq][1] != raw["status"]
            or (intent["kind"] == "create" and (
                seq != 0 or raw["record_id"] != raw["root_record_id"] or
                raw["status"] != "baseline"
            ))
            or (intent["kind"] == "append" and (
                seq < 1 or raw["root_record_id"] != intent["root"]
                or chain[seq-1][0] != intent["expected"]
            ))
        ):
            raise InvalidHistory("write receipt is inconsistent with history")
        return _receipt(
            op, intent["kind"], raw["root_record_id"], raw["record_id"],
            seq, raw["status"], chain[seq][2], replayed=True,
        )
    except (ValueError, TypeError, KeyError, IndexError, UnicodeError) as exc:
        raise InvalidHistory("cannot validate keyed write receipt") from exc


def lookup_operation(
    path: str, key: bytes, op: str, request: OriginalSourceClaimRequest,
    kind: str, root: str = "", expected: str = "",
) -> dict | None:
    """Re-verify a successful old operation before egress; no re-fetch on replay."""
    if type(op) is not str or _ID.fullmatch(op) is None:
        raise InvalidHistory("invalid operation id")
    intent = _intent(request, kind, root, expected)
    try:
        with closing(_db(path)) as db:
            return _find(db, path, key, op, request, intent)
    except (OSError, sqlite3.Error, OverflowError, AttributeError) as exc:
        raise InvalidHistory("write operation unavailable") from exc


def _register(
    db: sqlite3.Connection, key: bytes, op: str,
    intent: dict, root: str, rid: str, seq: int, status: str,
) -> None:
    number = db.execute("SELECT count(*) FROM timeline_write_operations").fetchone()[0]
    if number >= MAX_OPERATIONS:
        raise InvalidHistory("write operation capacity reached")
    payload = _canonical({
        "intent": intent, "record_id": rid, "sequence": seq,
        "status": status, "root_record_id": root,
    })
    db.execute(
        "INSERT INTO timeline_write_operations(operation_id,payload,mac) VALUES (?,?,?)",
        (op, payload.decode("ascii"), _mac(key, op, payload)),
    )


def commit_create(
    path: str, key: bytes, op: str, request: OriginalSourceClaimRequest,
    fresh: ClientCitedAnswer,
) -> dict:
    """Persist verified baseline plus retry receipt in ONE serialized transaction."""
    intent = _intent(request, "create", "", "")
    if type(op) is not str or _ID.fullmatch(op) is None:
        raise InvalidHistory("invalid operation ID")
    if _validated_observation(fresh, request, datetime.now(timezone.utc)) is None:
        raise InvalidHistory("unverified fresh observation")
    try:
        with closing(_db(path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            _schema(db)
            replay = _find(db, path, key, op, request, intent)
            if replay is not None:
                return replay
            rid = _insert_verified(db, key, request, fresh)
            _register(db, key, op, intent, rid, rid, 0, "baseline")
        return _receipt(op, "create", rid, rid, 0, "baseline", fresh, replayed=False)
    except (OSError, sqlite3.Error, OverflowError, AttributeError) as exc:
        raise InvalidHistory("could not commit source history creation") from exc


def commit_append(
    path: str, key: bytes, op: str, request: OriginalSourceClaimRequest,
    root: str, expected: str, fresh: ClientCitedAnswer,
) -> dict:
    """Validate latest timeline and write observation, edge and retry ID atomically."""
    intent = _intent(request, "append", root, expected)
    if type(op) is not str or _ID.fullmatch(op) is None:
        raise InvalidHistory("invalid operation ID")
    if _validated_observation(fresh, request, datetime.now(timezone.utc)) is None:
        raise InvalidHistory("unverified fresh observation")
    try:
        with closing(_db(path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            _schema(db)
            replay = _find(db, path, key, op, request, intent)
            if replay is not None:
                return replay
            chain, linked = _load_chain(db, path, key, root, request)
            if len(chain) >= MAX_TIMELINE_OBSERVATIONS or chain[-1][0] != expected:
                raise InvalidHistory("timeline full or stale expected head")
            old = chain[-1][2]
            comparison = reconcile_observations(request, old, fresh)
            if comparison.status == "abstain":
                raise InvalidHistory("fresh comparison cannot be validated")
            status = _status(old, fresh)
            if status != comparison.status:
                raise InvalidHistory("inconsistent source classification")
            rid = _insert_verified(db, key, request, fresh)
            if not linked:
                db.execute(
                    "INSERT INTO source_timeline_edges VALUES (?,?,?,?,?,?)",
                    (root, 0, root, "", "baseline", _edge_mac(key, root, 0, root, "", "baseline")),
                )
            seq = len(chain)
            db.execute(
                "INSERT INTO source_timeline_edges VALUES (?,?,?,?,?,?)",
                (root, seq, rid, expected, status,
                 _edge_mac(key, root, seq, rid, expected, status)),
            )
            _register(db, key, op, intent, root, rid, seq, status)
        return _receipt(op, "append", root, rid, seq, status, fresh, replayed=False)
    except (OSError, sqlite3.Error, OverflowError, AttributeError) as exc:
        raise InvalidHistory("could not commit source history append") from exc


__all__ = [
    "MAX_OPERATIONS", "lookup_operation", "commit_create", "commit_append",
]
