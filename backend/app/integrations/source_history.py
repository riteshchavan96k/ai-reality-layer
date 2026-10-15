"""Step247 local, operator-controlled, keyed historical source observations.

This is not a publisher signature, independent timestamp, anti-rollback log,
monitor, or factual-truth database. Same-user compromise/rollback is outside
the operator-HMAC trust boundary. Database bytes and source quotes are untrusted.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from contextlib import closing
from hashlib import sha256
import hmac
import json
import os
import re
import secrets
import sqlite3
import stat

from backend.app.api.original_source_claim import OriginalSourceClaimRequest
from backend.app.integrations.cited_answer_client import (
    ALIGNED, CONTRADICTED, CitedSourceObservation, ClientCitedAnswer,
)
from backend.app.integrations.source_recheck import _validated_observation

MAX_RECORDS = 1000
MAX_PAYLOAD_BYTES = 8192
_ID = re.compile(r"[0-9a-f]{32}\Z")
_KEY = re.compile(r"[0-9a-fA-F]{64}\Z")
_DOMAIN = b"ai-reality-layer-step247-history-v1\x00"


class InvalidHistory(ValueError):
    """Reject invalid or untrusted history without exposing stored content."""


def operator_history_configuration() -> tuple[str, bytes]:
    """Read explicit local operator settings; reject weak or missing secrets."""
    path = os.environ.get("ARL_OBSERVATION_STORE_PATH", "")
    key_text = os.environ.get("ARL_OBSERVATION_HMAC_KEY_HEX", "")
    if (
        not path or not os.path.isabs(path) or os.path.normpath(path) != path
        or not path.endswith(".sqlite3")
        or not _KEY.fullmatch(key_text)
    ):
        raise InvalidHistory("invalid local history configuration")
    key = bytes.fromhex(key_text)
    if not any(key):
        raise InvalidHistory("invalid local history configuration")
    try:
        with closing(_db(path)):
            pass
    except (OSError, sqlite3.Error) as exc:
        raise InvalidHistory("history store unavailable") from exc
    return path, key


def _check_private(path: str, *, directory: bool) -> None:
    try:
        mode = os.lstat(path)
    except OSError as exc:
        raise InvalidHistory("private history location unavailable") from exc
    if (
        (not stat.S_ISDIR(mode.st_mode) if directory else not stat.S_ISREG(mode.st_mode))
        or (hasattr(os, "getuid") and mode.st_uid != os.getuid())
        or stat.S_IMODE(mode.st_mode) & 0o077
    ):
        raise InvalidHistory("history location is not operator private")


def _prepare_db(path: str) -> None:
    # Caller must provision a private owned directory before the first use.
    # Reject symlinked final directory/file; avoid opening paths in /tmp
    # or shared workspaces. Parent ownership and 0700 guard other OS users.
    _check_private(os.path.dirname(path), directory=True)
    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError:
        pass
    except OSError as exc:
        raise InvalidHistory("history file unavailable") from exc
    else:
        os.close(descriptor)
    _check_private(path, directory=False)


def _db(path: str) -> sqlite3.Connection:
    _prepare_db(path)
    connection = sqlite3.connect(path, timeout=5)
    try:
        connection.execute("PRAGMA secure_delete=ON")
        connection.execute("""
            CREATE TABLE IF NOT EXISTS original_source_observations (
                record_id TEXT PRIMARY KEY NOT NULL,
                payload TEXT NOT NULL,
                mac TEXT NOT NULL
            )
        """)
        return connection
    except Exception:
        connection.close()
        raise


def _canonical(value: object) -> bytes:
    try:
        data = json.dumps(value, sort_keys=True, ensure_ascii=True,
                          separators=(",", ":"), allow_nan=False).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise InvalidHistory("invalid observation encoding") from exc
    if len(data) > MAX_PAYLOAD_BYTES:
        raise InvalidHistory("observation exceeds history limit")
    return data


def _mac(key: bytes, record_id: str, payload: bytes) -> str:
    return hmac.new(key, _DOMAIN + record_id.encode("ascii") + b"\x00" + payload,
                    sha256).hexdigest()


def save_verified_answer(
    path: str, key: bytes, request: OriginalSourceClaimRequest, 
    answer: ClientCitedAnswer,
) -> str:
    """Persist only one currently validated original-source observation."""
    if (not isinstance(request, OriginalSourceClaimRequest) or type(key) is not bytes or len(key) != 32):
        raise InvalidHistory("invalid history request")
    if _validated_observation(answer, request, datetime.now(timezone.utc)) is None:
        raise InvalidHistory("cannot store an unverified source observation")
    c = answer.citation
    payload = {
        "version": 1,
        "request": request.model_dump(mode="json"),
        "decision": answer.decision,
        "reason_code": answer.reason_code,
        "answer_text": answer.answer_text,
        "request_binding_sha256": answer.request_binding_sha256,
        "may_use_as_bounded_evidence": answer.may_use_as_bounded_evidence,
        "citation": {
            "source_uri": c.source_uri,
            "original_source_quote": c.original_source_quote,
            "source_quote_sha256": c.source_quote_sha256,
            "source_capture_sha256": c.source_capture_sha256,
            "source_capture_observed_at": c.source_capture_observed_at,
        },
        "saved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    encoded = _canonical(payload)
    record_id = secrets.token_hex(16)
    with closing(_db(path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        number = connection.execute(
            "SELECT count(*) FROM original_source_observations"
        ).fetchone()[0]
        if number >= MAX_RECORDS:
            raise InvalidHistory("history capacity reached")
        connection.execute(
            "INSERT INTO original_source_observations(record_id,payload,mac) VALUES (?,?,?)",
            (record_id, encoded.decode("ascii"), _mac(key, record_id, encoded)),
        )
    return record_id


def load_verified_answer(
    path: str, key: bytes, record_id: str, request: OriginalSourceClaimRequest,
) -> ClientCitedAnswer:
    """Verify an operator-MACed baseline prior to ANY fresh source request."""
    if (
        type(record_id) is not str or _ID.fullmatch(record_id) is None
        or not isinstance(request, OriginalSourceClaimRequest)
        or type(key) is not bytes or len(key) != 32
    ):
        raise InvalidHistory("invalid history request")
    try:
        with _db(path) as connection:
            row = connection.execute(
                "SELECT payload,mac FROM original_source_observations WHERE record_id=?",
                (record_id,),
            ).fetchone()
        if row is None or type(row[0]) is not str or type(row[1]) is not str:
            raise InvalidHistory("history unavailable")
        encoded = row[0].encode("ascii")
        if len(encoded) > MAX_PAYLOAD_BYTES or not hmac.compare_digest(
            _mac(key, record_id, encoded), row[1]
        ):
            raise InvalidHistory("history integrity check failed")
        raw = json.loads(encoded)
        if not isinstance(raw, dict) or set(raw) != {
            "version", "request", "decision", "reason_code", "answer_text",
            "request_binding_sha256", "may_use_as_bounded_evidence",
            "citation", "saved_at",
        } or type(raw["version"]) is not int or raw["version"] != 1:
            raise InvalidHistory("invalid history schema")
        if raw["request"] != request.model_dump(mode="json"):
            raise InvalidHistory("history request mismatch")
        if type(raw["saved_at"]) is not str or not raw["saved_at"].endswith("Z"):
            raise InvalidHistory("invalid save time")
        saved_at = datetime.fromisoformat(raw["saved_at"].replace("Z", "+00:00"))
        if saved_at > datetime.now(timezone.utc) + timedelta(seconds=30):
            raise InvalidHistory("invalid save time")
        citation = raw["citation"]
        if not isinstance(citation, dict) or set(citation) != {
            "source_uri", "original_source_quote", "source_quote_sha256",
            "source_capture_sha256", "source_capture_observed_at",
        }:
            raise InvalidHistory("invalid source citation")
        answer = ClientCitedAnswer(
            decision=raw["decision"],
            reason_code=raw["reason_code"],
            answer_text=raw["answer_text"],
            request_binding_sha256=raw["request_binding_sha256"],
            citation=CitedSourceObservation(**citation),
            may_use_as_bounded_evidence=raw["may_use_as_bounded_evidence"],
        )
        if _validated_observation(answer, request, datetime.now(timezone.utc)) is None:
            raise InvalidHistory("invalid stored source observation")
        observed_at = datetime.fromisoformat(
            answer.citation.source_capture_observed_at.replace("Z", "+00:00")
        )
        if saved_at < observed_at - timedelta(seconds=30):
            raise InvalidHistory("save time precedes source capture")
        return answer
    except (sqlite3.Error, OSError, UnicodeError, ValueError, TypeError,
            KeyError, OverflowError, AttributeError) as exc:
        raise InvalidHistory("historical observation cannot be verified") from exc


__all__ = [
    "InvalidHistory", "operator_history_configuration",
    "save_verified_answer", "load_verified_answer",
]
