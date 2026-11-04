"""Downloadable business reports."""
from datetime import date

import streamlit as st

from config.settings import get_settings
from reporting.exports import export_csv, export_xlsx
from reporting.service import REPORT_TYPES, report_data

settings = get_settings()
labels = {
    "orders": "Orders",
    "invoices": "Invoices",
    "inventory": "Inventory position",
    "stock_movements": "Stock movement ledger",
    "processing": "Processing activity",
}
st.title("Reports & exports")
st.caption("Build downloadable reports from saved workspace records. No sample rows are added.")
report_type = st.selectbox("Report", REPORT_TYPES, format_func=lambda value: labels[value])

start = None
end = None
if report_type != "inventory":
    col1, col2 = st.columns(2)
    with col1:
        use_start = st.checkbox("Set start date")
        start_date = st.date_input("From", value=date.today(), disabled=not use_start)
    with col2:
        use_end = st.checkbox("Set end date")
        end_date = st.date_input("Through", value=date.today(), disabled=not use_end)
    start = start_date if use_start else None
    end = end_date if use_end else None
else:
    st.caption(
        "Inventory is a current stock snapshot; historical stock balances are "
        "not reconstructed."
    )

try:
    frame = report_data(settings.database_url, report_type, start_date=start, end_date=end)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

st.subheader(labels[report_type])
if start or end:
    st.caption(
        f"Date filter: {start.isoformat() if start else 'Any'} to "
        f"{end.isoformat() if end else 'Any'} (UTC timestamps where applicable)"
    )
if frame.empty:
    st.info(
        "No saved records match this report and date range. Try a wider date range "
        "or complete the relevant workflow."
    )
else:
    st.caption(f"{len(frame):,} record(s) · Based on saved workspace data")
    st.dataframe(frame, use_container_width=True, hide_index=True)
    safe_name = report_type.replace("_", "-")
    download_left, download_right = st.columns(2)
    download_left.download_button(
        "Download CSV",
        data=export_csv(frame),
        file_name=f"businessflow-{safe_name}.csv",
        mime="text/csv",
        type="primary",
        use_container_width=True,
    )
    download_right.download_button(
        "Download Excel",
        data=export_xlsx(frame, sheet_name=labels[report_type]),
        file_name=f"businessflow-{safe_name}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
if report_type in {"orders", "invoices"}:
    st.caption(
        "Financial amounts are shown with their currency code. Do not compare or "
        "add amounts across different currencies."
    )
