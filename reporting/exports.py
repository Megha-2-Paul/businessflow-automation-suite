"""CSV and Excel export helpers for operational reports."""
from __future__ import annotations

from io import BytesIO

import pandas as pd


def _safe_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Neutralise formula-like text before writing spreadsheet-compatible files."""
    safe = frame.copy()
    for column in safe.select_dtypes(include=["object", "string"]).columns:
        safe[column] = safe[column].map(
            lambda value: (
                "'" + value
                if isinstance(value, str)
                and value.startswith(("=", "+", "-", "@", chr(9), chr(10), chr(13)))
                else value
            )
        )
    return safe


def export_csv(frame: pd.DataFrame) -> bytes:
    """Return a UTF-8 CSV representation of a report."""
    return _safe_frame(frame).to_csv(index=False).encode("utf-8-sig")


def export_xlsx(frame: pd.DataFrame, *, sheet_name: str = "Report") -> bytes:
    """Return a formatted single-sheet Excel workbook."""
    buffer = BytesIO()
    safe = _safe_frame(frame)
    name = sheet_name[:31] or "Report"
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        safe.to_excel(writer, index=False, sheet_name=name)
        worksheet = writer.sheets[name]
        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions
        for column in worksheet.columns:
            values = [len(str(cell.value or "")) for cell in column]
            width = min(max(max(values, default=10) + 2, 12), 42)
            worksheet.column_dimensions[column[0].column_letter].width = width
    return buffer.getvalue()
