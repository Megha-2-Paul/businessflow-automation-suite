"""Spreadsheet workflow orchestration and processing-history persistence."""
from __future__ import annotations
from datetime import UTC, datetime
from typing import Any
from sqlalchemy import select
from database.models import Business, ProcessingJob, ProcessingLog
from database.session import get_session_factory, initialize_database


def record_processing_result(database_url: str, *, job_type: str,
    records_processed: int, records_succeeded: int,
    issues: list[dict[str, Any]], message: str) -> int:
    """Persist a completed spreadsheet job and its data-quality findings."""
    initialize_database(database_url)
    factory = get_session_factory(database_url)
    now = datetime.now(UTC)
    with factory.begin() as session:
        business = session.scalar(select(Business).order_by(Business.id).limit(1))
        if business is None:
            business = Business(name="Local Workspace")
            session.add(business)
            session.flush()
        job = ProcessingJob(
            business_id=business.id, job_type=job_type, status="completed",
            records_processed=records_processed, records_succeeded=records_succeeded,
            records_failed=0, started_at=now, completed_at=now,
        )
        session.add(job)
        session.flush()
        session.add(ProcessingLog(job_id=job.id, level="INFO", message=message))
        for issue in issues:
            session.add(ProcessingLog(
                job_id=job.id, level="WARNING", message=str(issue["details"])
            ))
        return job.id
