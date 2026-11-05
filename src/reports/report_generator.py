#!/usr/bin/env python3
"""
FRAUDNET AI — Forensic PDF Report Generator
============================================
Generates structured, professional cryptocurrency investigation dossiers.

Features:
  - Standard PDF 1.4 binary stream generation (100% pure Python standard library)
  - Zero external package dependencies (no C-extensions required)
  - Color-coded risk badges (Critical, High, Moderate, Low)
  - Formatted tables for graph metrics, ML risk scores, and feature attributions
  - Formal academic disclaimers and methodological limitations
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORTS_DIR = PROJECT_ROOT / "outputs" / "reports"


class PurePDFDocument:
    """
    Lightweight, standards-compliant PDF 1.4 document builder.
    Constructs multi-page formatted documents with text, lines, and colored badges.
    """

    def __init__(self, page_width: float = 612.0, page_height: float = 792.0):
        self.width = page_width
        self.height = page_height
        self.pages: List[str] = []
        self.current_stream: List[str] = []
        self.current_y = page_height - 50.0
        self.left_margin = 50.0
        self.right_margin = page_width - 50.0

    def new_page(self):
        """Finalize current page stream and open new page."""
        if self.current_stream:
            self.pages.append("\n".join(self.current_stream))
            self.current_stream = []
        self.current_y = self.height - 50.0

    def add_page(self):
        """Alias for new_page."""
        self.new_page()

    def check_space(self, needed_pt: float):
        """Check if remaining page space is sufficient; otherwise start new page."""
        if (self.current_y - needed_pt) < 50.0:
            self.new_page()

    def add_rect(self, x: float, y: float, w: float, h: float, r: float, g: float, b: float, fill: bool = True):
        """Draw filled or stroked colored rectangle."""
        cmd = f"{r:.3f} {g:.3f} {b:.3f} rg\n{x:.2f} {y:.2f} {w:.2f} {h:.2f} re\nf" if fill else f"{r:.3f} {g:.3f} {b:.3f} RG\n{x:.2f} {y:.2f} {w:.2f} {h:.2f} re\nS"
        self.current_stream.append(cmd)

    def draw_rect(self, x: float, y: float, w: float, h: float, fill_rgb: Tuple[float, float, float] = (0, 0, 0)):
        """Convenience method for drawing filled rectangle."""
        self.add_rect(x, y, w, h, fill_rgb[0], fill_rgb[1], fill_rgb[2], fill=True)

    def add_line(self, x1: float, y1: float, x2: float, y2: float, r: float = 0.7, g: float = 0.7, b: float = 0.7, width: float = 0.8):
        """Draw line between (x1, y1) and (x2, y2)."""
        cmd = f"{width:.2f} w\n{r:.3f} {g:.3f} {b:.3f} RG\n{x1:.2f} {y1:.2f} m\n{x2:.2f} {y2:.2f} l\nS"
        self.current_stream.append(cmd)

    def draw_text(self, x: float, y: float, text: str, font_size: float = 10.0, rgb: Tuple[float, float, float] = (0, 0, 0), bold: bool = False):
        """Convenience alias for add_text."""
        self.add_text(text, x, y, size=font_size, bold=bold, r=rgb[0], g=rgb[1], b=rgb[2])

    def add_text(
        self,
        text: str,
        x: float,
        y: float,
        size: float = 10.0,
        bold: bool = False,
        r: float = 0.1,
        g: float = 0.1,
        b: float = 0.1,
    ):
        """Render single line of text."""
        font_name = "/F2" if bold else "/F1"
        # Escape special PDF characters
        safe_text = (
            text.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
            .encode("latin-1", "replace")
            .decode("latin-1")
        )
        cmd = (
            f"BT\n{font_name} {size:.2f} Tf\n{r:.3f} {g:.3f} {b:.3f} rg\n"
            f"1 0 0 1 {x:.2f} {y:.2f} Tm\n({safe_text}) Tj\nET"
        )
        self.current_stream.append(cmd)

    def add_wrapped_text(
        self,
        text: str,
        size: float = 9.0,
        line_height: float = 13.0,
        bold: bool = False,
        r: float = 0.2,
        g: float = 0.2,
        b: float = 0.2,
        max_width_chars: int = 95,
    ):
        """Wrap and print long paragraphs of text."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            if len(" ".join(current_line + [word])) <= max_width_chars:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))

        for line in lines:
            self.check_space(line_height)
            self.add_text(line, self.left_margin, self.current_y, size=size, bold=bold, r=r, g=g, b=b)
            self.current_y -= line_height

    def build(self) -> bytes:
        """Compile internal structures into compliant PDF 1.4 byte stream."""
        if self.current_stream:
            self.pages.append("\n".join(self.current_stream))
            self.current_stream = []

        if not self.pages:
            self.pages.append("BT\n/F1 12 Tf\n50 700 Td\n(Empty Document) Tj\nET")

        num_pages = len(self.pages)
        objects = []

        # Object 1: Catalog
        objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        # Object 2: Pages
        page_refs = " ".join(f"{3 + i * 2} 0 R" for i in range(num_pages))
        objects.append(f"<< /Type /Pages /Kids [{page_refs}] /Count {num_pages} >>".encode("latin-1"))

        # Object for each page and stream
        # Object 3..2+2*N: Page and Stream pairs
        # Fonts: Object 3+2*N (F1 Helvetica), Object 4+2*N (F2 Helvetica-Bold)
        font1_idx = 3 + num_pages * 2
        font2_idx = font1_idx + 1

        for i, page_stream in enumerate(self.pages):
            content_idx = 4 + i * 2
            page_obj = (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.width:.1f} {self.height:.1f}] "
                f"/Resources << /Font << /F1 {font1_idx} 0 R /F2 {font2_idx} 0 R >> >> "
                f"/Contents {content_idx} 0 R >>"
            ).encode("latin-1")
            objects.append(page_obj)

            stream_bytes = page_stream.encode("latin-1")
            stream_obj = (
                f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("latin-1")
                + stream_bytes
                + b"\nendstream"
            )
            objects.append(stream_obj)

        # Font 1: Helvetica (Regular)
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        # Font 2: Helvetica-Bold
        objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")

        # Assemble PDF with cross-reference table
        output = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
        offsets = [0]

        for i, obj in enumerate(objects, 1):
            offsets.append(sum(len(chunk) for chunk in output))
            output.append(f"{i} 0 obj\n".encode("latin-1") + obj + b"\nendobj\n")

        xref_start = sum(len(chunk) for chunk in output)
        total_objs = len(objects) + 1
        xref_table = [f"xref\n0 {total_objs}\n0000000000 65535 f \n".encode("latin-1")]

        for off in offsets[1:]:
            xref_table.append(f"{off:010d} 00000 n \n".encode("latin-1"))

        trailer = (
            f"trailer\n<< /Size {total_objs} /Root 1 0 R >>\n"
            f"startxref\n{xref_start}\n%%EOF\n"
        ).encode("latin-1")

        return b"".join(output + xref_table + [trailer])

    def build_pdf_bytes(self) -> bytes:
        """Alias for build."""
        return self.build()


def generate_forensic_pdf_report(
    dossier: Union[Dict[str, any], int, str] = None,
    case_info: Optional[Dict[str, any]] = None,
    output_path: Optional[Path] = None,
    generated_by: Optional[str] = None,
    tx_id: Optional[int] = None,
) -> Path:
    """
    Generate a formal PDF investigation dossier for a transaction.
    """
    if isinstance(dossier, (int, str)):
        from src.analytics.transaction_investigation import compile_investigation_dossier
        dossier = compile_investigation_dossier(int(dossier))
    elif dossier is None and tx_id is not None:
        from src.analytics.transaction_investigation import compile_investigation_dossier
        dossier = compile_investigation_dossier(int(tx_id))
    elif not isinstance(dossier, dict) and tx_id is not None:
        from src.analytics.transaction_investigation import compile_investigation_dossier
        dossier = compile_investigation_dossier(int(tx_id))

    tx_id = dossier.get("txId", tx_id)
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    report_id = f"REP-BTC-{tx_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}"

    target_dir = Path(output_path).parent if output_path else DEFAULT_REPORTS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = Path(output_path) if output_path else (target_dir / f"FRAUDNET_Report_{tx_id}.pdf")

    pdf = PurePDFDocument()

    # ---------------- PAGE 1: EXECUTIVE BRIEFING ----------------
    # Header Banner
    pdf.add_rect(0, 720, 612, 72, 0.06, 0.09, 0.16)  # Dark navy #0f172a
    pdf.add_text("FRAUDNET AI | FORENSIC INVESTIGATION REPORT", 50, 760, size=15, bold=True, r=0.23, g=0.51, b=0.96)
    pdf.add_text("CRYPTOCURRENCY TRANSACTION NETWORK INTELLIGENCE", 50, 742, size=9, bold=False, r=0.6, g=0.7, b=0.9)
    pdf.add_text(f"Report ID: {report_id}", 380, 742, size=8, bold=False, r=0.8, g=0.8, b=0.8)

    pdf.current_y = 690.0

    # Case Metadata (if linked)
    if case_info:
        pdf.add_text("LINKED CASE FILE", 50, pdf.current_y, size=10, bold=True, r=0.1, g=0.2, b=0.4)
        pdf.current_y -= 15
        pdf.add_text(f"Case Title: {case_info.get('title', 'N/A')}  |  Status: {case_info.get('status', 'Open')}  |  Priority: {case_info.get('priority', 'Medium')}", 50, pdf.current_y, size=9)
        pdf.current_y -= 15
        pdf.add_line(50, pdf.current_y, 562, pdf.current_y)
        pdf.current_y -= 20

    # Section: Target Transaction Overview
    pdf.add_text("1. TRANSACTION IDENTITY & RISK PROFILE", 50, pdf.current_y, size=11, bold=True, r=0.1, g=0.15, b=0.3)
    pdf.current_y -= 8
    pdf.add_line(50, pdf.current_y, 562, pdf.current_y, width=1.0, r=0.2, g=0.4, b=0.8)
    pdf.current_y -= 25

    ml = dossier.get("risk_assessment", {})
    risk_cat = ml.get("risk_category", "Low")
    prob_pct = ml.get("illicit_probability", 0.0) * 100

    # Risk Badge Colors
    badge_colors = {
        "Critical": (0.85, 0.15, 0.15),   # Red
        "High": (0.95, 0.45, 0.10),       # Orange
        "Moderate": (0.85, 0.70, 0.10),   # Amber/Yellow
        "Low": (0.10, 0.65, 0.35),        # Green
    }
    br, bg, bb = badge_colors.get(risk_cat, (0.5, 0.5, 0.5))

    # Draw Risk Score Card
    pdf.add_rect(50, pdf.current_y - 45, 512, 60, 0.95, 0.96, 0.98)
    pdf.add_rect(420, pdf.current_y - 35, 120, 30, br, bg, bb)
    pdf.add_text("ESTIMATED RISK LEVEL", 435, pdf.current_y - 18, size=7, bold=True, r=1.0, g=1.0, b=1.0)
    pdf.add_text(f"{risk_cat.upper()} ({prob_pct:.1f}%)", 435, pdf.current_y - 30, size=9, bold=True, r=1.0, g=1.0, b=1.0)

    pdf.add_text(f"Transaction ID: {tx_id}", 65, pdf.current_y - 15, size=11, bold=True)
    pdf.add_text(f"Time Step: {dossier.get('time_step', 1)} (Two-Week Slice)  |  Model: {ml.get('model_name', 'RandomForest')} v{ml.get('model_version', '1.0.0')}", 65, pdf.current_y - 30, size=9)
    pdf.add_text(f"Ground-Truth Label: {dossier.get('ground_truth_label', 'unknown')}  |  Decision Threshold: {ml.get('decision_threshold', 0.5):.4f}", 65, pdf.current_y - 42, size=8, r=0.4, g=0.4, b=0.4)

    pdf.current_y -= 70

    # Section: Graph & Payment Flow Metrics
    pdf.add_text("2. GRAPH TOPOLOGY & FLOW CHARACTERISTICS", 50, pdf.current_y, size=11, bold=True, r=0.1, g=0.15, b=0.3)
    pdf.current_y -= 8
    pdf.add_line(50, pdf.current_y, 562, pdf.current_y, width=1.0, r=0.2, g=0.4, b=0.8)
    pdf.current_y -= 20

    gm = dossier.get("graph_metrics", {})
    metrics_table = [
        ("In-Degree (Incoming Inputs):", f"{gm.get('in_degree', 0):,}", "PageRank Centrality:", f"{gm.get('pagerank', 0.0):.6f}"),
        ("Out-Degree (Outgoing Outputs):", f"{gm.get('out_degree', 0):,}", "Clustering Coefficient:", f"{gm.get('clustering_coeff', 0.0):.4f}"),
        ("Total Degree:", f"{gm.get('total_degree', 0):,}", "Community ID:", f"{gm.get('community_id', 0)}"),
        ("Weakly Connected Component:", f"WCC #{gm.get('wcc_id', 0)}", "Component Size:", f"{gm.get('wcc_size', 0):,} nodes"),
    ]

    for c1_label, c1_val, c2_label, c2_val in metrics_table:
        pdf.add_text(c1_label, 60, pdf.current_y, size=9, bold=False, r=0.3, g=0.3, b=0.3)
        pdf.add_text(c1_val, 210, pdf.current_y, size=9, bold=True)
        pdf.add_text(c2_label, 320, pdf.current_y, size=9, bold=False, r=0.3, g=0.3, b=0.3)
        pdf.add_text(c2_val, 460, pdf.current_y, size=9, bold=True)
        pdf.current_y -= 16

    pdf.current_y -= 10

    # Section: Explainability & Predictive Drivers
    pdf.add_text("3. TOP PREDICTIVE FEATURE DRIVERS", 50, pdf.current_y, size=11, bold=True, r=0.1, g=0.15, b=0.3)
    pdf.current_y -= 8
    pdf.add_line(50, pdf.current_y, 562, pdf.current_y, width=1.0, r=0.2, g=0.4, b=0.8)
    pdf.current_y -= 20

    expl = dossier.get("explainability", {})
    drivers = expl.get("top_drivers", [])[:6]

    if drivers:
        for d in drivers:
            pdf.check_space(20)
            is_risk = d.get("impact_direction") == "increases_risk"
            bullet_r, bullet_g, bullet_b = (0.8, 0.2, 0.2) if is_risk else (0.1, 0.6, 0.3)
            prefix = "[RISK ELEVATOR]" if is_risk else "[RISK MITIGATOR]"

            pdf.add_text(f"{prefix} {d.get('feature')}", 60, pdf.current_y, size=9, bold=True, r=bullet_r, g=bullet_g, b=bullet_b)
            pdf.current_y -= 12
            pdf.add_text(f"  {d.get('explanation')}", 75, pdf.current_y, size=8, r=0.3, g=0.3, b=0.3)
            pdf.current_y -= 15
    else:
        pdf.add_text("No significant feature outliers detected against licit baseline.", 60, pdf.current_y, size=9)
        pdf.current_y -= 20

    pdf.current_y -= 10

    # Section: Executive Narrative & Limitations
    pdf.check_space(100)
    pdf.add_text("4. FORENSIC NARRATIVE & LIMITATIONS", 50, pdf.current_y, size=11, bold=True, r=0.1, g=0.15, b=0.3)
    pdf.current_y -= 8
    pdf.add_line(50, pdf.current_y, 562, pdf.current_y, width=1.0, r=0.2, g=0.4, b=0.8)
    pdf.current_y -= 18

    narrative = dossier.get("executive_summary", "Forensic summary generated.")
    pdf.add_wrapped_text(narrative, size=9, line_height=13)

    pdf.current_y -= 10
    disclaimer = (
        "ACADEMIC & FORENSIC DISCLAIMER: FRAUDNET AI assessments represent statistical "
        "and topological risk estimations derived from the Elliptic Bitcoin dataset. "
        "High fan-in or high risk scores do not constitute automated proof of legal wrongdoing. "
        "All investigative findings must be corroborated with blockchain ledger data and human expertise."
    )
    pdf.add_wrapped_text(disclaimer, size=8, line_height=11, bold=False, r=0.45, g=0.45, b=0.45)

    # Footer
    pdf.add_line(50, 45, 562, 45, width=0.5, r=0.7, g=0.7, b=0.7)
    pdf.add_text(f"Generated: {now_str}  |  FRAUDNET AI Investigation Platform", 50, 32, size=7, r=0.5, g=0.5, b=0.5)

    # Write PDF bytes
    pdf_bytes = pdf.build()
    with open(file_path, "wb") as f:
        f.write(pdf_bytes)

    return file_path
