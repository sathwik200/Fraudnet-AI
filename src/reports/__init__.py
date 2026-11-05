"""Reporting module for FRAUDNET AI.

Provides forensic PDF dossier generation with zero external dependencies.
"""

from src.reports.report_generator import PurePDFDocument, generate_forensic_pdf_report

__all__ = [
    "PurePDFDocument",
    "generate_forensic_pdf_report",
]

