"""SQLite persistence layer for InvoiceM8.

One :class:`Database` instance is shared across threads (GUI + watcher), so all
access goes through a single connection guarded by a lock. Row factory returns
dict-like ``sqlite3.Row`` objects.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key       TEXT PRIMARY KEY,
    value     TEXT NOT NULL DEFAULT '',
    encrypted INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS customers (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    name                  TEXT NOT NULL UNIQUE COLLATE NOCASE,
    aliases               TEXT NOT NULL DEFAULT '[]',   -- JSON list of alt names
    servicem8_enabled     INTEGER NOT NULL DEFAULT 0,
    myob_enabled          INTEGER NOT NULL DEFAULT 0,
    accounting_enabled    INTEGER NOT NULL DEFAULT 0,   -- generic accounting provider
    file_types            TEXT NOT NULL DEFAULT 'pdf',  -- comma list
    servicem8_client_uuid TEXT NOT NULL DEFAULT '',
    accounting_contact_id TEXT NOT NULL DEFAULT '',
    notes                 TEXT NOT NULL DEFAULT '',
    created_at            TEXT NOT NULL,
    updated_at           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activity_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ts            TEXT NOT NULL,
    level         TEXT NOT NULL DEFAULT 'INFO',
    customer_name TEXT NOT NULL DEFAULT '',
    invoice_ref   TEXT NOT NULL DEFAULT '',
    platform      TEXT NOT NULL DEFAULT '',
    action        TEXT NOT NULL DEFAULT '',
    filename      TEXT NOT NULL DEFAULT '',
    message       TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS error_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ts            TEXT NOT NULL,
    stage         TEXT NOT NULL DEFAULT '',
    customer_name TEXT NOT NULL DEFAULT '',
    invoice_ref   TEXT NOT NULL DEFAULT '',
    filename      TEXT NOT NULL DEFAULT '',
    error         TEXT NOT NULL DEFAULT '',
    payload       TEXT NOT NULL DEFAULT '',   -- JSON snapshot for retry
    retry_count   INTEGER NOT NULL DEFAULT 0,
    resolved      INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pending_invoices (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ts             TEXT NOT NULL,
    extracted_name TEXT NOT NULL DEFAULT '',
    job_number     TEXT NOT NULL DEFAULT '',
    invoice_ref    TEXT NOT NULL DEFAULT '',
    email_subject  TEXT NOT NULL DEFAULT '',
    email_from     TEXT NOT NULL DEFAULT '',
    file_path      TEXT NOT NULL DEFAULT '',
    raw_json       TEXT NOT NULL DEFAULT '{}',
    status         TEXT NOT NULL DEFAULT 'pending_new_customer'
);

CREATE TABLE IF NOT EXISTS processed_emails (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id  TEXT NOT NULL UNIQUE,
    received_at TEXT NOT NULL DEFAULT '',
    processed_at TEXT NOT NULL,
    subject     TEXT NOT NULL DEFAULT '',
    result      TEXT NOT NULL DEFAULT ''
);

-- One row per (document, platform) that was successfully uploaded. Used to
-- stop the same invoice/credit being pushed twice, even from a different
-- email or a manual retry.
CREATE TABLE IF NOT EXISTS processed_documents (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ts            TEXT NOT NULL,
    file_hash     TEXT NOT NULL DEFAULT '',   -- sha256 of the attachment bytes
    customer_name TEXT NOT NULL DEFAULT '',
    invoice_ref   TEXT NOT NULL DEFAULT '',
    doc_type      TEXT NOT NULL DEFAULT 'invoice',   -- invoice | credit
    platform      TEXT NOT NULL DEFAULT '',
    remote_id     TEXT NOT NULL DEFAULT '',
    filename      TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_procdoc_hash ON processed_documents(file_hash, platform);
CREATE INDEX IF NOT EXISTS idx_procdoc_ref
    ON processed_documents(customer_name, invoice_ref, doc_type, platform);
"""


def _utcnow() -> str:
    """ISO-8601 UTC timestamp used for every stored row."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class _ClosedCursor:
    """Stand-in returned by Database._exec after close() so a racing worker
    thread on shutdown gets a harmless no-op instead of an exception."""

    lastrowid = 0
    rowcount = 0

    def fetchall(self):
        return []

    def fetchone(self):
        return None


class Database:
    """Serialized access to the InvoiceM8 SQLite file."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._closed = False
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        with self._lock:
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    # -- low level helpers -------------------------------------------------
    def _exec(self, sql: str, params: Iterable[Any] = ()):
        with self._lock:
            if self._closed:                 # a leaked worker thread on shutdown
                return _ClosedCursor()
            cur = self._conn.execute(sql, tuple(params))
            self._conn.commit()
            return cur

    def _query(self, sql: str, params: Iterable[Any] = ()) -> list[sqlite3.Row]:
        with self._lock:
            if self._closed:
                return []
            return self._conn.execute(sql, tuple(params)).fetchall()

    # -- settings -------------------------------------------------------
    def get_setting(self, key: str, default: str = "") -> tuple[str, bool]:
        """Return (raw_value, encrypted_flag) for a setting key."""
        rows = self._query("SELECT value, encrypted FROM settings WHERE key=?", (key,))
        if not rows:
            return default, False
        return rows[0]["value"], bool(rows[0]["encrypted"])

    def set_setting(self, key: str, value: str, encrypted: bool = False) -> None:
        """Upsert a setting."""
        self._exec(
            "INSERT INTO settings(key,value,encrypted) VALUES(?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, encrypted=excluded.encrypted",
            (key, value, int(encrypted)),
        )

    def all_settings(self) -> dict[str, sqlite3.Row]:
        return {r["key"]: r for r in self._query("SELECT * FROM settings")}

    # -- customers ----------------------------------------------------
    def list_customers(self) -> list[sqlite3.Row]:
        return self._query("SELECT * FROM customers ORDER BY name COLLATE NOCASE")

    def get_customer(self, cid: int) -> sqlite3.Row | None:
        rows = self._query("SELECT * FROM customers WHERE id=?", (cid,))
        return rows[0] if rows else None

    def find_customer_by_name(self, name: str) -> sqlite3.Row | None:
        """Match on canonical name first, then alias lists (case-insensitive)."""
        name_norm = (name or "").strip().lower()
        if not name_norm:
            return None
        rows = self._query("SELECT * FROM customers WHERE lower(name)=?", (name_norm,))
        if rows:
            return rows[0]
        for r in self.list_customers():
            aliases = [a.strip().lower() for a in json.loads(r["aliases"] or "[]")]
            if name_norm in aliases:
                return r
        return None

    def upsert_customer(self, data: dict[str, Any]) -> int:
        """Insert or update a customer profile. ``data`` may contain ``id``."""
        now = _utcnow()
        fields = dict(
            name=data["name"].strip(),
            aliases=json.dumps(data.get("aliases", [])),
            servicem8_enabled=int(bool(data.get("servicem8_enabled"))),
            myob_enabled=int(bool(data.get("myob_enabled"))),
            accounting_enabled=int(bool(data.get("accounting_enabled"))),
            file_types=",".join(data.get("file_types", ["pdf"])) or "pdf",
            servicem8_client_uuid=data.get("servicem8_client_uuid", ""),
            accounting_contact_id=data.get("accounting_contact_id", ""),
            notes=data.get("notes", ""),
            updated_at=now,
        )
        cid = data.get("id")
        if cid:
            cols = ", ".join(f"{k}=?" for k in fields)
            self._exec(f"UPDATE customers SET {cols} WHERE id=?", (*fields.values(), cid))
            return cid
        fields["created_at"] = now
        cols = ", ".join(fields)
        ph = ", ".join("?" for _ in fields)
        cur = self._exec(f"INSERT INTO customers({cols}) VALUES({ph})", tuple(fields.values()))
        return int(cur.lastrowid)

    def delete_customer(self, cid: int) -> None:
        self._exec("DELETE FROM customers WHERE id=?", (cid,))

    # -- logs --------------------------------------------------------
    def add_activity(self, **kw: Any) -> None:
        kw.setdefault("ts", _utcnow())
        keys = ("ts", "level", "customer_name", "invoice_ref", "platform",
                "action", "filename", "message")
        vals = [kw.get(k, "") for k in keys]
        self._exec(
            f"INSERT INTO activity_log({','.join(keys)}) VALUES({','.join('?' for _ in keys)})",
            vals,
        )

    def search_activity(self, term: str = "", limit: int = 500) -> list[sqlite3.Row]:
        like = f"%{term}%"
        return self._query(
            "SELECT * FROM activity_log WHERE "
            "customer_name LIKE ? OR invoice_ref LIKE ? OR platform LIKE ? "
            "OR action LIKE ? OR filename LIKE ? OR message LIKE ? "
            "ORDER BY id DESC LIMIT ?",
            (like, like, like, like, like, like, limit),
        )

    def clear_activity_log(self) -> int:
        """Delete all activity_log rows. Returns how many were removed."""
        n = len(self._query("SELECT id FROM activity_log"))
        self._exec("DELETE FROM activity_log")
        return n

    def add_error(self, **kw: Any) -> int:
        kw.setdefault("ts", _utcnow())
        keys = ("ts", "stage", "customer_name", "invoice_ref", "filename",
                "error", "payload")
        vals = [kw.get(k, "") for k in keys]
        cur = self._exec(
            f"INSERT INTO error_log({','.join(keys)}) VALUES({','.join('?' for _ in keys)})",
            vals,
        )
        return int(cur.lastrowid)

    def list_errors(self, include_resolved: bool = False) -> list[sqlite3.Row]:
        sql = "SELECT * FROM error_log"
        if not include_resolved:
            sql += " WHERE resolved=0"
        return self._query(sql + " ORDER BY id DESC LIMIT 500")

    def mark_error_resolved(self, eid: int) -> None:
        self._exec("UPDATE error_log SET resolved=1 WHERE id=?", (eid,))

    def bump_error_retry(self, eid: int) -> None:
        self._exec("UPDATE error_log SET retry_count=retry_count+1 WHERE id=?", (eid,))

    # -- pending invoices (new-customer queue) ----------------------
    def add_pending(self, **kw: Any) -> int:
        kw.setdefault("ts", _utcnow())
        keys = ("ts", "extracted_name", "job_number", "invoice_ref",
                "email_subject", "email_from", "file_path", "raw_json", "status")
        vals = [kw.get(k, "") for k in keys]
        cur = self._exec(
            f"INSERT INTO pending_invoices({','.join(keys)}) VALUES({','.join('?' for _ in keys)})",
            vals,
        )
        return int(cur.lastrowid)

    def list_pending(self, status: str = "pending_new_customer") -> list[sqlite3.Row]:
        return self._query(
            "SELECT * FROM pending_invoices WHERE status=? ORDER BY id DESC", (status,)
        )

    def set_pending_status(self, pid: int, status: str) -> None:
        self._exec("UPDATE pending_invoices SET status=? WHERE id=?", (status, pid))

    # -- processed email dedupe -----------------------------------
    def is_email_processed(self, message_id: str) -> bool:
        return bool(
            self._query("SELECT 1 FROM processed_emails WHERE message_id=?", (message_id,))
        )

    def mark_email_processed(self, message_id: str, received_at: str,
                             subject: str, result: str) -> None:
        self._exec(
            "INSERT OR IGNORE INTO processed_emails(message_id,received_at,processed_at,subject,result) "
            "VALUES(?,?,?,?,?)",
            (message_id, received_at, _utcnow(), subject, result),
        )

    # -- per-document dedupe -------------------------------------
    def document_already_sent(self, file_hash: str, customer_name: str,
                              invoice_ref: str, doc_type: str,
                              platform: str) -> sqlite3.Row | None:
        """Return the prior upload row if this document already went to ``platform``.

        A match is either the exact same file bytes, or the same
        customer + reference + document type (when a reference was parsed).
        """
        if file_hash:
            rows = self._query(
                "SELECT * FROM processed_documents WHERE file_hash=? AND platform=? LIMIT 1",
                (file_hash, platform),
            )
            if rows:
                return rows[0]
        if invoice_ref:
            rows = self._query(
                "SELECT * FROM processed_documents WHERE customer_name=? AND invoice_ref=? "
                "AND doc_type=? AND platform=? LIMIT 1",
                (customer_name, invoice_ref, doc_type, platform),
            )
            if rows:
                return rows[0]
        return None

    def record_document_sent(self, *, file_hash: str, customer_name: str,
                             invoice_ref: str, doc_type: str, platform: str,
                             remote_id: str, filename: str) -> None:
        """Remember a successful upload so it is never repeated."""
        self._exec(
            "INSERT INTO processed_documents"
            "(ts,file_hash,customer_name,invoice_ref,doc_type,platform,remote_id,filename) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (_utcnow(), file_hash, customer_name, invoice_ref, doc_type,
             platform, remote_id, filename),
        )

    def last_seen_email_time(self) -> str | None:
        rows = self._query("SELECT MAX(received_at) AS m FROM processed_emails")
        return rows[0]["m"] if rows and rows[0]["m"] else None

    def close(self) -> None:
        """Close the connection. Idempotent; safe while other threads race."""
        with self._lock:
            if self._closed:
                return
            self._closed = True
            try:
                self._conn.close()
            except Exception:
                pass
