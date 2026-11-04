"""Processing history for spreadsheet and invoice workflows."""
import streamlit as st
from sqlalchemy import select

from config.settings import get_settings
from database.models import Business, ProcessingJob, ProcessingLog
from database.session import get_session_factory

settings = get_settings()
st.title("Processing history")
st.caption("Review recent spreadsheet and invoice jobs recorded in the local database.")
factory = get_session_factory(settings.database_url)
with factory() as session:
    statement = (
        select(ProcessingJob)
        .join(Business)
        .where(
            ProcessingJob.job_type.in_(
                ["spreadsheet_clean", "spreadsheet_consolidation", "invoice_extraction"]
            )
        )
        .order_by(ProcessingJob.created_at.desc())
        .limit(100)
    )
    jobs = session.scalars(statement).all()
    records = [
        {
            "Job": job.id,
            "Workflow": job.job_type.replace("spreadsheet_", "").replace("_", " ").title(),
            "Status": job.status.replace("_", " ").title(),
            "Rows processed": job.records_processed,
            "Rows retained": job.records_succeeded,
            "Started (UTC)": job.started_at.strftime("%Y-%m-%d %H:%M") if job.started_at else "",
            "Completed (UTC)": (
                job.completed_at.strftime("%Y-%m-%d %H:%M") if job.completed_at else ""
            ),
        }
        for job in jobs
    ]
if records:
    st.dataframe(records, use_container_width=True, hide_index=True)
    selected_id = st.selectbox("View job details", [record["Job"] for record in records])
    with factory() as session:
        selected_job = session.get(ProcessingJob, selected_id)
        if selected_job is not None:
            logs = session.scalars(
                select(ProcessingLog)
                .where(ProcessingLog.job_id == selected_id)
                .order_by(ProcessingLog.created_at)
            ).all()
            st.subheader(f"Job #{selected_id}")
            for log in logs:
                if log.level == "WARNING":
                    st.warning(log.message)
                else:
                    st.info(log.message)
            if selected_job.errors:
                error_rows = [
                    {"Issue": error.issue_type, "Details": error.details}
                    for error in selected_job.errors
                ]
                st.dataframe(error_rows, use_container_width=True, hide_index=True)
else:
    st.info("No processing jobs have been recorded yet.")
