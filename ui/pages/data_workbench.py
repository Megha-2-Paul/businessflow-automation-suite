"""Interactive spreadsheet cleaning, validation and consolidation workspace."""
from __future__ import annotations

import re

import streamlit as st

from config.settings import get_settings
from processing.cleaning import clean_dataframe, consolidate_dataframes
from processing.spreadsheets import (
    SpreadsheetError,
    export_dataframe,
    list_excel_sheets,
    load_tabular_file,
)
from services.spreadsheet_service import record_processing_result
from validation.spreadsheets import validate_dataframe

settings = get_settings()


def _safe_export_stem(filename: str) -> str:
    """Build a safe, predictable download name from an uploaded filename."""
    basename = filename.replace(chr(92), "/").rsplit("/", 1)[-1]
    stem = basename.rsplit(".", 1)[0]
    safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", stem).strip("_-")
    return safe_stem[:80] or "processed_data"
max_upload_bytes = settings.max_upload_mb * 1024 * 1024

st.title("Data Workbench")
st.caption("Clean, validate and combine CSV and Excel files.")

clean_tab, combine_tab = st.tabs(["Clean a file", "Combine files"])

with clean_tab:
    uploaded = st.file_uploader(
        "Choose a CSV or XLSX file",
        type=["csv", "xlsx"],
        key="spreadsheet_clean_upload",
        help=f"Maximum file size: {settings.max_upload_mb} MB.",
    )
    sheet_name: str | int = 0
    if uploaded is not None and uploaded.name.lower().endswith(".xlsx"):
        try:
            sheet_names = list_excel_sheets(
                uploaded.name, uploaded.getvalue(), max_upload_bytes
            )
            if not sheet_names:
                st.warning("This workbook does not contain any worksheets.")
            else:
                sheet_name = st.selectbox("Worksheet", sheet_names)
        except SpreadsheetError as exc:
            st.error(str(exc))

    if uploaded is not None and st.button("Load and inspect", key="load_spreadsheet"):
        try:
            frame = load_tabular_file(
                uploaded.name, uploaded.getvalue(), max_upload_bytes, sheet_name
            )
            st.session_state["bf_source_frame"] = frame
            st.session_state["bf_source_name"] = uploaded.name
            st.session_state.pop("bf_clean_frame", None)
            st.success(f"Loaded {len(frame):,} rows and {len(frame.columns):,} columns.")
        except SpreadsheetError as exc:
            st.error(str(exc))

    source_frame = st.session_state.get("bf_source_frame")
    if source_frame is not None:
        st.subheader("Source preview")
        st.dataframe(source_frame.head(100), use_container_width=True)
        source_issues = validate_dataframe(source_frame)
        if source_issues:
            st.warning(f"Found {len(source_issues)} data-quality finding(s). Review below.")
            st.dataframe(source_issues, use_container_width=True, hide_index=True)
        else:
            st.success("No missing values or duplicate rows detected.")

        st.subheader("Cleaning options")
        col1, col2 = st.columns(2)
        with col1:
            trim_text = st.checkbox("Trim extra spaces", value=True)
            standardize = st.checkbox("Standardise column names", value=True)
        with col2:
            remove_duplicates = st.checkbox("Remove duplicate rows", value=True)
            remove_empty = st.checkbox(
                "Remove completely empty rows and columns", value=True
            )

        if st.button("Clean data", type="primary", key="clean_spreadsheet"):
            cleaned, changes = clean_dataframe(
                source_frame,
                trim_text=trim_text,
                standardize_columns=standardize,
                remove_duplicates=remove_duplicates,
                remove_empty=remove_empty,
            )
            cleaned_issues = validate_dataframe(cleaned)
            st.session_state["bf_clean_frame"] = cleaned
            st.session_state["bf_clean_summary"] = changes
            st.session_state["bf_clean_issues"] = cleaned_issues
            job_id = record_processing_result(
                settings.database_url,
                job_type="spreadsheet_clean",
                records_processed=len(source_frame),
                records_succeeded=len(cleaned),
                issues=cleaned_issues,
                message=(
                    f"Cleaned {st.session_state['bf_source_name']}; removed "
                    f"{changes['duplicates_removed']} duplicate row(s)."
                ),
            )
            st.session_state["bf_clean_job_id"] = job_id

        cleaned_frame = st.session_state.get("bf_clean_frame")
        if cleaned_frame is not None:
            st.subheader("Cleaned result")
            st.dataframe(cleaned_frame.head(100), use_container_width=True)
            changes = st.session_state["bf_clean_summary"]
            metrics = st.columns(4)
            metrics[0].metric("Rows removed", changes["rows_removed"])
            metrics[1].metric("Duplicates removed", changes["duplicates_removed"])
            metrics[2].metric("Columns removed", changes["columns_removed"])
            metrics[3].metric("Values trimmed", changes["values_trimmed"])
            st.caption(
                f"Processing job #{st.session_state['bf_clean_job_id']} saved to history."
            )
            base_name = _safe_export_stem(st.session_state["bf_source_name"])
            export_col1, export_col2 = st.columns(2)
            with export_col1:
                st.download_button(
                    "Download CSV",
                    export_dataframe(cleaned_frame, "csv"),
                    file_name=f"{base_name}_cleaned.csv",
                    mime="text/csv",
                )
            with export_col2:
                st.download_button(
                    "Download Excel",
                    export_dataframe(cleaned_frame, "xlsx"),
                    file_name=f"{base_name}_cleaned.xlsx",
                    mime=(
                        "application/vnd.openxmlformats-officedocument."
                        "spreadsheetml.sheet"
                    ),
                )

with combine_tab:
    uploads = st.file_uploader(
        "Choose two or more CSV or XLSX files",
        type=["csv", "xlsx"],
        accept_multiple_files=True,
        key="spreadsheet_combine_uploads",
        help=f"Each file must be no larger than {settings.max_upload_mb} MB.",
    )
    if uploads and st.button("Combine files", type="primary", key="combine_spreadsheets"):
        try:
            frames = [
                load_tabular_file(file.name, file.getvalue(), max_upload_bytes)
                for file in uploads
            ]
            combined, summary = consolidate_dataframes(frames)
            issues = validate_dataframe(combined)
            st.session_state["bf_combined_frame"] = combined
            st.session_state["bf_combined_summary"] = summary
            job_id = record_processing_result(
                settings.database_url,
                job_type="spreadsheet_consolidation",
                records_processed=sum(len(frame) for frame in frames),
                records_succeeded=len(combined),
                issues=issues,
                message=f"Combined {len(frames)} uploaded files into {len(combined)} rows.",
            )
            st.session_state["bf_combined_job_id"] = job_id
        except (SpreadsheetError, ValueError) as exc:
            st.error(str(exc))

    combined_frame = st.session_state.get("bf_combined_frame")
    if combined_frame is not None:
        st.subheader("Combined result")
        st.dataframe(combined_frame.head(100), use_container_width=True)
        summary = st.session_state["bf_combined_summary"]
        st.write(
            f"Combined {summary['files_combined']} files into "
            f"{summary['rows_combined']:,} rows and {summary['columns_combined']} columns."
        )
        if summary["columns_only_in_some_files"]:
            st.info(
                "These columns were present in only some files and were retained: "
                + ", ".join(summary["columns_only_in_some_files"])
            )
        st.caption(
            f"Processing job #{st.session_state['bf_combined_job_id']} saved to history."
        )
        st.download_button(
            "Download combined Excel",
            export_dataframe(combined_frame, "xlsx"),
            file_name="combined_data.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        )
        st.download_button(
            "Download combined CSV",
            export_dataframe(combined_frame, "csv"),
            file_name="combined_data.csv",
            mime="text/csv",
        )
