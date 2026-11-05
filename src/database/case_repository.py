#!/usr/bin/env python3
"""
FRAUDNET AI — Case Repository
==============================
CRUD operations and business logic for case management and evidence tracking.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import sqlite3

from src.database.db import get_db_connection, init_database
from src.database.models import Case, CaseTransaction, InvestigationNote, ReportRecord


class CaseRepository:
    """Repository managing forensic cases, suspect transactions, and investigator notes."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path
        init_database(self.db_path)

    def _conn(self) -> sqlite3.Connection:
        return get_db_connection(self.db_path)

    def create_case(
        self,
        title: str,
        description: str = "",
        priority: str = "Medium",
        status: str = "Open",
    ) -> int:
        """Create new case and return case ID."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._conn()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO cases (title, description, status, priority, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (title, description, status, priority, now, now),
                )
                return cursor.lastrowid
        finally:
            conn.close()

    def get_case(self, case_id: int) -> Optional[Dict[str, any]]:
        """Retrieve single case with transaction count."""
        conn = self._conn()
        try:
            row = conn.execute(
                """
                SELECT c.*, COUNT(ct.id) as transaction_count
                FROM cases c
                LEFT JOIN case_transactions ct ON c.id = ct.case_id
                WHERE c.id = ?
                GROUP BY c.id
                """,
                (case_id,),
            ).fetchone()
            if not row:
                return None
            return dict(row)
        finally:
            conn.close()

    def list_cases(self, status: Optional[str] = None) -> List[Dict[str, any]]:
        """List all cases with transaction counts ordered by update time."""
        conn = self._conn()
        try:
            if status:
                rows = conn.execute(
                    """
                    SELECT c.*, COUNT(ct.id) as transaction_count
                    FROM cases c
                    LEFT JOIN case_transactions ct ON c.id = ct.case_id
                    WHERE c.status = ?
                    GROUP BY c.id
                    ORDER BY c.updated_at DESC
                    """,
                    (status,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT c.*, COUNT(ct.id) as transaction_count
                    FROM cases c
                    LEFT JOIN case_transactions ct ON c.id = ct.case_id
                    GROUP BY c.id
                    ORDER BY c.updated_at DESC
                    """
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def update_case(
        self,
        case_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> bool:
        """Update case fields."""
        conn = self._conn()
        now = datetime.now(timezone.utc).isoformat()
        updates = ["updated_at = ?"]
        params = [now]

        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)

        params.append(case_id)
        sql = f"UPDATE cases SET {', '.join(updates)} WHERE id = ?"

        try:
            with conn:
                cur = conn.execute(sql, params)
                return cur.rowcount > 0
        finally:
            conn.close()

    def delete_case(self, case_id: int) -> bool:
        """Delete case and cascade-delete associated transactions and notes."""
        conn = self._conn()
        try:
            with conn:
                cur = conn.execute("DELETE FROM cases WHERE id = ?", (case_id,))
                return cur.rowcount > 0
        finally:
            conn.close()

    def add_transaction_to_case(
        self,
        case_id: int,
        tx_id: int,
        risk_score: float = 0.0,
        risk_category: str = "Low",
        notes: str = "",
    ) -> bool:
        """Add transaction to case (idempotent)."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._conn()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO case_transactions (case_id, tx_id, risk_score, risk_category, notes, added_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(case_id, tx_id) DO UPDATE SET
                        risk_score = excluded.risk_score,
                        risk_category = excluded.risk_category,
                        notes = excluded.notes
                    """,
                    (case_id, int(tx_id), float(risk_score), risk_category, notes, now),
                )
                conn.execute("UPDATE cases SET updated_at = ? WHERE id = ?", (now, case_id))
                return True
        finally:
            conn.close()

    def remove_transaction_from_case(self, case_id: int, tx_id: int) -> bool:
        """Remove transaction from case."""
        conn = self._conn()
        now = datetime.now(timezone.utc).isoformat()
        try:
            with conn:
                cur = conn.execute(
                    "DELETE FROM case_transactions WHERE case_id = ? AND tx_id = ?",
                    (case_id, int(tx_id)),
                )
                conn.execute("UPDATE cases SET updated_at = ? WHERE id = ?", (now, case_id))
                return cur.rowcount > 0
        finally:
            conn.close()

    def get_case_transactions(self, case_id: int) -> List[Dict[str, any]]:
        """List all transactions attached to a case."""
        conn = self._conn()
        try:
            rows = conn.execute(
                """
                SELECT * FROM case_transactions
                WHERE case_id = ?
                ORDER BY risk_score DESC, added_at DESC
                """,
                (case_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def add_note(self, case_id: int, note_text: str, author: str = "Lead Investigator") -> int:
        """Append investigator note to case."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._conn()
        try:
            with conn:
                cur = conn.execute(
                    """
                    INSERT INTO investigation_notes (case_id, author, note_text, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (case_id, author, note_text, now),
                )
                conn.execute("UPDATE cases SET updated_at = ? WHERE id = ?", (now, case_id))
                return cur.lastrowid
        finally:
            conn.close()

    def get_case_notes(self, case_id: int) -> List[Dict[str, any]]:
        """Retrieve notes for a case."""
        conn = self._conn()
        try:
            rows = conn.execute(
                """
                SELECT * FROM investigation_notes
                WHERE case_id = ?
                ORDER BY created_at ASC
                """,
                (case_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def record_report(
        self,
        report_title: str,
        file_path: str,
        case_id: Optional[int] = None,
        tx_id: Optional[int] = None,
    ) -> int:
        """Record generated report in audit history."""
        now = datetime.now(timezone.utc).isoformat()
        conn = self._conn()
        try:
            with conn:
                cur = conn.execute(
                    """
                    INSERT INTO report_history (case_id, tx_id, report_title, file_path, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (case_id, tx_id, report_title, str(file_path), now),
                )
                return cur.lastrowid
        finally:
            conn.close()

    def list_reports(self, limit: int = 50) -> List[Dict[str, any]]:
        """List generated reports history."""
        conn = self._conn()
        try:
            rows = conn.execute(
                """
                SELECT * FROM report_history
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

