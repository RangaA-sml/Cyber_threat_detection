"""SQLite-backed incident storage and analyst audit history for SentinelAI."""
from __future__ import annotations

from datetime import datetime, timezone
from contextlib import contextmanager
import json
import hashlib
from pathlib import Path
import sqlite3
import uuid
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "sentinel_incidents.db"
STATUSES = ["New", "Acknowledged", "Investigating", "Containment Recorded", "Resolved", "False Positive"]
SEVERITIES = ["Critical", "High", "Medium", "Low"]
OPEN_STATUSES = ["New", "Acknowledged", "Investigating", "Containment Recorded"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


@contextmanager
def _database_connection():
    connection = _connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_database() -> None:
    """Create the incident and immutable-style activity tables if needed."""
    with _database_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                incident_id TEXT PRIMARY KEY,
                batch_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                source_file TEXT NOT NULL,
                record_number INTEGER NOT NULL,
                prediction_code TEXT NOT NULL,
                confidence REAL,
                severity TEXT NOT NULL,
                status TEXT NOT NULL,
                assigned_to TEXT NOT NULL DEFAULT 'Unassigned',
                details_json TEXT NOT NULL,
                last_note TEXT NOT NULL DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at);
            CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
            CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity);
            CREATE TABLE IF NOT EXISTS incident_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT NOT NULL,
                event_time TEXT NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(incident_id) REFERENCES incidents(incident_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_events_incident ON incident_events(incident_id, event_time);
            """
        )


def _safe_json_value(value: Any) -> Any:
    """Convert pandas/numpy values into JSON-safe primitives."""
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, TypeError):
            pass
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _severity_for(confidence: float | None) -> str:
    # Severity is a triage heuristic based on model confidence, not an impact assessment.
    if confidence is None:
        return "High"
    if confidence >= 95:
        return "Critical"
    if confidence >= 85:
        return "High"
    if confidence >= 65:
        return "Medium"
    return "Low"



def get_severity_score(severity: str, incident_id: str) -> int:
    """Return a stable demo triage score for the SOC severity label.

    This is a presentation/priority score, not the model's attack probability.
    """
    ranges = {
        "Low": (10, 20),
        "Medium": (40, 60),
        "High": (70, 85),
        "Critical": (90, 100),
    }
    severity = str(severity).strip().title()
    if severity not in ranges:
        return 0

    low, high = ranges[severity]
    digest = hashlib.sha256(str(incident_id).encode("utf-8")).hexdigest()
    stable_number = int(digest[:8], 16)
    return low + (stable_number % (high - low + 1))


def store_attack_predictions(data: pd.DataFrame, results: pd.DataFrame, source_file: str) -> list[str]:
    """Create one incident for each row predicted as class 1 (Attack).

    A new batch identifier groups detections produced by one model run. Re-running
    the same file deliberately produces a new batch so analysts can compare scans.
    """
    init_database()
    if "Prediction code" not in results.columns:
        raise ValueError("Prediction results do not contain a 'Prediction code' column.")

    batch_id = f"BATCH-{uuid.uuid4().hex[:10].upper()}"
    now = _now()
    created_ids: list[str] = []

    with _database_connection() as connection:
        for result_index, result in results.iterrows():
            try:
                is_attack = int(result["Prediction code"]) == 1
            except (TypeError, ValueError):
                is_attack = str(result.get("Prediction", "")).strip().lower() == "attack"
            if not is_attack:
                continue

            row_position = int(result_index)
            if row_position < 0 or row_position >= len(data):
                continue

            confidence_value = result.get("Attack Probability (%)", None)
            try:
                confidence = float(confidence_value) if pd.notna(confidence_value) else None
            except (TypeError, ValueError):
                confidence = None

            raw_record = data.iloc[row_position].to_dict()
            evidence = {str(key): _safe_json_value(value) for key, value in raw_record.items()}
            incident_id = (
                f"SOC-{datetime.now(timezone.utc).strftime('%y%m%d')}-"
                f"{uuid.uuid4().hex[:6].upper()}"
            )
            # Prefer an explicit SOC demo severity supplied by the mixed dataset.
            # The XGBoost model remains binary (Benign/Attack); this field is
            # demonstration triage metadata, not a model-predicted class.
            supplied_severity = str(raw_record.get("Demo Severity", "")).strip().title()
            severity = (
                supplied_severity
                if supplied_severity in SEVERITIES
                else _severity_for(confidence)
            )
            prediction_code = str(result["Prediction code"])
            connection.execute(
                """INSERT INTO incidents
                (incident_id, batch_id, created_at, updated_at, source_file, record_number,
                 prediction_code, confidence, severity, status, assigned_to, details_json, last_note)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'New', 'Unassigned', ?, '')""",
                (
                    incident_id, batch_id, now, now, Path(source_file).name,
                    row_position + 1, prediction_code, confidence, severity,
                    json.dumps(evidence, ensure_ascii=False, allow_nan=False),
                ),
            )
            connection.execute(
                """INSERT INTO incident_events (incident_id, event_time, actor, action, details)
                VALUES (?, ?, ?, ?, ?)""",
                (incident_id, now, "SentinelAI Detection Engine", "Alert created",
                 f"Model classified record {row_position + 1} as Attack. Severity heuristic: {severity}. Batch: {batch_id}."),
            )
            created_ids.append(incident_id)

    return created_ids


def get_incidents() -> pd.DataFrame:
    init_database()
    with _database_connection() as connection:
        rows = connection.execute(
            """SELECT incident_id AS 'Incident ID', batch_id AS 'Batch ID',
               created_at AS 'Detected At (UTC)', updated_at AS 'Updated At (UTC)',
               source_file AS 'Source File', record_number AS 'Record #',
               prediction_code AS 'Prediction Code', confidence AS 'Attack Confidence (%)',
               severity AS 'Severity', status AS 'Status', assigned_to AS 'Assigned To',
               last_note AS 'Latest Analyst Note'
               FROM incidents ORDER BY created_at DESC"""
        ).fetchall()
    incidents = pd.DataFrame([dict(row) for row in rows])
    if not incidents.empty:
        incidents["Threat Severity Score (%)"] = incidents.apply(
            lambda row: get_severity_score(row["Severity"], row["Incident ID"]),
            axis=1,
        )
    return incidents


def get_incident(incident_id: str) -> dict[str, Any] | None:
    init_database()
    with _database_connection() as connection:
        row = connection.execute("SELECT * FROM incidents WHERE incident_id = ?", (incident_id,)).fetchone()
    if row is None:
        return None
    incident = dict(row)
    try:
        incident["details"] = json.loads(incident.pop("details_json"))
    except (TypeError, json.JSONDecodeError):
        incident["details"] = {}
    incident["threat_severity_score"] = get_severity_score(
        incident.get("severity", ""),
        incident.get("incident_id", ""),
    )
    return incident


def get_incident_events(incident_id: str) -> pd.DataFrame:
    init_database()
    with _database_connection() as connection:
        rows = connection.execute(
            """SELECT event_time AS 'Time (UTC)', actor AS 'Analyst / Actor',
               action AS 'Activity', details AS 'Details'
               FROM incident_events WHERE incident_id = ? ORDER BY event_time DESC, event_id DESC""",
            (incident_id,),
        ).fetchall()
    return pd.DataFrame([dict(row) for row in rows])


def update_incident(
    incident_id: str,
    *,
    status: str,
    assigned_to: str,
    severity: str,
    actor: str,
    note: str = "",
) -> bool:
    """Update triage fields and append an auditable analyst activity event."""
    if status not in STATUSES:
        raise ValueError("Invalid incident status.")
    if severity not in SEVERITIES:
        raise ValueError("Invalid incident severity.")
    now = _now()
    actor = (actor or "SOC Analyst").strip()[:80]
    assigned_to = (assigned_to or "Unassigned").strip()[:100]
    note = (note or "").strip()[:2000]
    details = f"Status: {status}; Assigned to: {assigned_to}; Severity: {severity}"
    if note:
        details += f"; Note: {note}"

    init_database()
    with _database_connection() as connection:
        cursor = connection.execute(
            """UPDATE incidents SET status = ?, assigned_to = ?, severity = ?,
               updated_at = ?, last_note = ? WHERE incident_id = ?""",
            (status, assigned_to, severity, now, note, incident_id),
        )
        if cursor.rowcount == 0:
            return False
        connection.execute(
            """INSERT INTO incident_events (incident_id, event_time, actor, action, details)
            VALUES (?, ?, ?, ?, ?)""",
            (incident_id, now, actor, "Analyst updated incident", details),
        )
    return True
