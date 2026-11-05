#!/usr/bin/env python3
"""
FRAUDNET AI — SQLite Database Manager
======================================
Manages thread-safe SQLite connections, schema initialization, and transactional safety.
Stores persistent forensic records at data/runtime/fraudnet.db.
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_DIR = PROJECT_ROOT / "data" / "runtime"
DEFAULT_DB_PATH = RUNTIME_DIR / "fraudnet.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'Open',
    priority TEXT DEFAULT 'Medium',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS case_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    tx_id INTEGER NOT NULL,
    risk_score REAL DEFAULT 0.0,
    risk_category TEXT DEFAULT 'Low',
    notes TEXT,
    added_at TEXT NOT NULL,
    FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE,
    UNIQUE(case_id, tx_id)
);

CREATE TABLE IF NOT EXISTS investigation_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    author TEXT DEFAULT 'Lead Investigator',
    note_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER,
    tx_id INTEGER,
    report_title TEXT NOT NULL,
    file_path TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(case_id) REFERENCES cases(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_case_tx ON case_transactions(case_id, tx_id);
CREATE INDEX IF NOT EXISTS idx_case_notes ON investigation_notes(case_id);
"""


def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Open connection to SQLite database with foreign keys enabled.
    Initializes schema automatically if table does not exist.
    """
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path, timeout=10.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_database(db_path: Optional[Path] = None) -> Path:
    """Initialize SQLite database tables and indexes."""
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    conn = get_db_connection(path)
    try:
        with conn:
            conn.executescript(SCHEMA_SQL)
    finally:
        conn.close()
    return path

