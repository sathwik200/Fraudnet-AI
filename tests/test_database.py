"""Unit tests for SQLite Database and Case Management (Module G)."""

import tempfile
from pathlib import Path
import pytest

from src.database.case_repository import CaseRepository


@pytest.fixture
def temp_repo():
    """Create a temporary SQLite database repository for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = Path(f.name)
    repo = CaseRepository(db_path=temp_path)
    yield repo
    if temp_path.exists():
        temp_path.unlink()


def test_create_and_get_case(temp_repo):
    """Test creating and retrieving a case."""
    case_id = temp_repo.create_case(
        title="Test Incident #1",
        description="Testing case functionality",
        priority="High",
    )
    assert case_id is not None
    assert isinstance(case_id, int)

    retrieved = temp_repo.get_case(case_id)
    assert retrieved is not None
    assert retrieved["title"] == "Test Incident #1"
    assert retrieved["status"] == "Open"
    assert retrieved["priority"] == "High"


def test_update_case_status(temp_repo):
    """Test updating case status."""
    case_id = temp_repo.create_case(title="Status Test")
    updated = temp_repo.update_case(case_id, status="In Progress")
    assert updated is True

    retrieved = temp_repo.get_case(case_id)
    assert retrieved["status"] == "In Progress"


def test_case_transactions(temp_repo):
    """Test attaching, listing, and detaching transactions."""
    case_id = temp_repo.create_case(title="Transaction Test")

    added = temp_repo.add_transaction_to_case(
        case_id=case_id,
        tx_id=230425980,
        risk_score=0.95,
        risk_category="Critical",
        notes="High fan-in source",
    )
    assert added is True

    txs = temp_repo.get_case_transactions(case_id)
    assert len(txs) == 1
    assert txs[0]["tx_id"] == 230425980
    assert txs[0]["risk_category"] == "Critical"

    # Remove transaction
    removed = temp_repo.remove_transaction_from_case(case_id, 230425980)
    assert removed is True
    assert len(temp_repo.get_case_transactions(case_id)) == 0


def test_case_notes(temp_repo):
    """Test adding and retrieving chronological investigator notes."""
    case_id = temp_repo.create_case(title="Notes Test")
    note_id = temp_repo.add_note(
        case_id=case_id,
        author="Officer Smith",
        note_text="Subpoena submitted to exchange.",
    )
    assert note_id is not None
    notes = temp_repo.get_case_notes(case_id)
    assert len(notes) == 1
    assert notes[0]["note_text"] == "Subpoena submitted to exchange."


def test_report_logging(temp_repo):
    """Test recording and retrieving report history."""
    report_id = temp_repo.record_report(
        report_title="Forensic Dossier Tx 230425980",
        file_path="/tmp/test_report.pdf",
        tx_id=230425980,
    )
    assert report_id is not None
    all_reports = temp_repo.list_reports()
    assert len(all_reports) == 1
    assert all_reports[0]["tx_id"] == 230425980


def test_delete_case_cascade(temp_repo):
    """Test deleting case cascades to transactions and notes."""
    case_id = temp_repo.create_case(title="Delete Cascade Test")
    temp_repo.add_transaction_to_case(case_id, 11111)
    temp_repo.add_note(case_id, "Test note", author="Author")

    deleted = temp_repo.delete_case(case_id)
    assert deleted is True
    assert temp_repo.get_case(case_id) is None
    assert len(temp_repo.get_case_transactions(case_id)) == 0
    assert len(temp_repo.get_case_notes(case_id)) == 0
