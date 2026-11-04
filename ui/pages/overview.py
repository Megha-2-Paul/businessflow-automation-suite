"""BusinessFlow workspace overview."""
import streamlit as st

st.title("BusinessFlow Automation Suite")
st.caption("A practical workspace for everyday business data operations.")

st.subheader("Spreadsheet workflows")
st.write(
    "Upload CSV and Excel files to inspect data quality, clean common issues, "
    "combine files and export the results."
)
st.page_link("ui/pages/data_workbench.py", label="Open Data Workbench")
st.page_link("ui/pages/history.py", label="View processing history")

st.divider()
st.subheader("Coming in later phases")
st.write(
    "Invoice extraction, order management, inventory reconciliation and "
    "operational reporting are planned for later development phases."
)
