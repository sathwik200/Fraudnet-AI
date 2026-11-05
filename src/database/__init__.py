"""
FRAUDNET AI — Database Package
===============================
SQLite database management, schemas, and case management repository.
"""

from .db import get_db_connection, init_database
from .models import Case, CaseTransaction, InvestigationNote, ReportRecord
from .case_repository import CaseRepository

__all__ = [
    "get_db_connection",
    "init_database",
    "Case",
    "CaseTransaction",
    "InvestigationNote",
    "ReportRecord",
    "CaseRepository",
]

