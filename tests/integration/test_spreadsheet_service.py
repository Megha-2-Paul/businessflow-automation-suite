"""Integration tests for spreadsheet processing-history persistence."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import Business, ProcessingJob, ProcessingLog
from database.session import get_engine
from services.spreadsheet_service import record_processing_result


def test_record_processing_result_persists_job_and_findings(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'history.db'}"
    job_id = record_processing_result(
        database_url,
        job_type="spreadsheet_clean",
        records_processed=10,
        records_succeeded=8,
        issues=[
            {
                "issue_type": "missing_values",
                "count": 2,
                "details": "Two missing values.",
            }
        ],
        message="Cleaned demonstration file.",
    )
    with Session(get_engine(database_url)) as session:
        job = session.scalar(select(ProcessingJob).where(ProcessingJob.id == job_id))
        assert job is not None
        assert job.status == "completed"
        assert job.records_processed == 10
        assert job.records_succeeded == 8
        assert job.records_failed == 0
        assert session.scalar(select(Business).where(Business.name == "Local Workspace"))
        logs = session.scalars(
            select(ProcessingLog).where(ProcessingLog.job_id == job_id)
        ).all()
        assert len(logs) == 2
        assert {log.level for log in logs} == {"INFO", "WARNING"}


def test_record_clean_job_without_findings_is_completed(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'clean.db'}"
    job_id = record_processing_result(
        database_url,
        job_type="spreadsheet_clean",
        records_processed=3,
        records_succeeded=3,
        issues=[],
        message="No changes needed.",
    )
    with Session(get_engine(database_url)) as session:
        job = session.get(ProcessingJob, job_id)
        assert job is not None
        assert job.status == "completed"
        assert job.records_failed == 0
