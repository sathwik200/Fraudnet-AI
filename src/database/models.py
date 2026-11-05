#!/usr/bin/env python3
"""
FRAUDNET AI — Database Models
==============================
Data transfer objects and schemas for the forensic investigation case management system.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class Case:
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    status: str = "Open"          # Open, Under Review, Escalated, Closed
    priority: str = "Medium"      # Low, Medium, High, Critical
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    transaction_count: int = 0


@dataclass
class CaseTransaction:
    id: Optional[int] = None
    case_id: int = 0
    tx_id: int = 0
    risk_score: float = 0.0
    risk_category: str = "Low"
    notes: str = ""
    added_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class InvestigationNote:
    id: Optional[int] = None
    case_id: int = 0
    author: str = "Lead Investigator"
    note_text: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class ReportRecord:
    id: Optional[int] = None
    case_id: Optional[int] = None
    tx_id: Optional[int] = None
    report_title: str = ""
    file_path: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

