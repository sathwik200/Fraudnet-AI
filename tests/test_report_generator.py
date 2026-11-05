"""Unit tests for Pure-Python Forensic PDF Report Generator (Module H)."""

import tempfile
from pathlib import Path
import pytest

from src.reports.report_generator import PurePDFDocument, generate_forensic_pdf_report


def test_pure_pdf_document_construction():
    """Verify PurePDFDocument builds valid PDF 1.4 binary stream."""
    doc = PurePDFDocument()
    doc.add_page()
    doc.draw_rect(50, 700, 500, 40, fill_rgb=(0.1, 0.2, 0.4))
    doc.draw_text(60, 715, "TEST PDF FORENSIC REPORT", font_size=14, rgb=(1, 1, 1), bold=True)
    pdf_bytes = doc.build_pdf_bytes()

    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert b"%%EOF" in pdf_bytes
    assert len(pdf_bytes) > 200


def test_generate_forensic_pdf_report_real_tx():
    """Verify generating complete dossier PDF for real transaction."""
    tx_id = 230425980
    with tempfile.TemporaryDirectory() as tmp_dir:
        out_path = Path(tmp_dir) / f"test_dossier_{tx_id}.pdf"
        res_path = generate_forensic_pdf_report(
            tx_id=tx_id,
            output_path=out_path,
            generated_by="Automated Test Auditor",
        )

        assert res_path.exists()
        assert res_path == out_path
        size = res_path.stat().st_size
        assert size > 500

        with open(res_path, "rb") as f:
            header = f.read(8)
            assert header.startswith(b"%PDF-1.4")

