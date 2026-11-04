"""Searchable processing history with job logs and error details."""
from datetime import date

import pandas as pd
import streamlit as st

from config.settings import get_settings
from reporting.exports import export_csv
from reporting.service import processing_history

settings = get_settings()
st.title("Processing history")
st.caption("Filter workflow runs, inspect recorded events and review errors.")
with st.expander("Filters", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    workflow = col1.selectbox("Workflow", [
        "All workflows", "spreadsheet_clean", "spreadsheet_consolidation",
        "invoice_extraction", "order_management", "inventory_management",
    ], format_func=lambda value: value.replace("_", " ").title())
    status = col2.selectbox("Status", [
        "All statuses", "pending", "running", "completed", "completed_with_errors", "failed",
    ], format_func=lambda value: value.replace("_", " ").title())
    use_start = col3.checkbox("Start date")
    start_date = col3.date_input("From", value=date.today(), disabled=not use_start)
    use_end = col4.checkbox("End date")
    end_date = col4.date_input("Through", value=date.today(), disabled=not use_end)
try:
    jobs = processing_history(
        settings.database_url, workflow=workflow, status=status,
        start_date=start_date if use_start else None,
        end_date=end_date if use_end else None,
    )
except ValueError as exc:
    st.error(str(exc))
    st.stop()

if jobs:
    rows = [{
        "Job": job["id"], "Workflow": job["workflow"].replace("_", " ").title(),
        "Status": job["status"].replace("_", " ").title(),
        "Processed": job["records_processed"], "Succeeded": job["records_succeeded"],
        "Failed": job["records_failed"], "Errors": len(job["errors"]),
        "Created (UTC)": job["created_at"].strftime("%Y-%m-%d %H:%M"),
    } for job in jobs]
    st.caption(f"Showing {len(jobs)} matching job(s), newest first (maximum 500).")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.download_button("Export filtered history (CSV)", export_csv(pd.DataFrame(rows)),
                       file_name="businessflow-processing-history.csv", mime="text/csv")
    selected_id = st.selectbox("Inspect job", [job["id"] for job in jobs],
                               format_func=lambda value: f"Job #{value}")
    selected = next(job for job in jobs if job["id"] == selected_id)
    st.subheader(f"Job #{selected_id} · {selected['workflow'].replace('_', ' ').title()}")
    st.write(f"**Status:** {selected['status'].replace('_', ' ').title()}  ")
    st.write(f"**Records:** {selected['records_succeeded']} succeeded / {selected['records_processed']} processed / {selected['records_failed']} failed")
    if selected["logs"]:
        st.markdown("**Activity log**")
        for entry in selected["logs"]:
            message = f"{entry['created_at']:%Y-%m-%d %H:%M:%S} UTC · {entry['level']} · {entry['message']}"
            if entry["level"] in {"ERROR", "WARNING"}:
                st.warning(message)
            else:
                st.write(message)
    else:
        st.caption("This job has no recorded log messages.")
    if selected["errors"]:
        st.markdown("**Recorded errors**")
        st.dataframe(pd.DataFrame(selected["errors"]), use_container_width=True, hide_index=True)
    else:
        st.success("No processing errors were recorded for this job.")
else:
    st.info("No processing jobs match these filters. Clear the filters or run a workflow to create history.")
