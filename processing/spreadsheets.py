"""Safe loading and export helpers for CSV and Excel workbooks."""
from __future__ import annotations

from io import BytesIO
from pathlib import PurePath
from zipfile import BadZipFile, is_zipfile

import pandas as pd
from pandas.errors import EmptyDataError, ParserError

SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}
MAX_ROWS = 250_000
MAX_COLUMNS = 200


class SpreadsheetError(ValueError):
    """Raised when an uploaded spreadsheet cannot be processed safely."""


def _validate_upload(filename: str, content: bytes, max_size_bytes: int) -> str:
    extension = PurePath(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise SpreadsheetError("Only CSV and XLSX files are supported.")
    if not content:
        raise SpreadsheetError("The uploaded file is empty.")
    if len(content) > max_size_bytes:
        raise SpreadsheetError(
            f"File exceeds the configured limit of {max_size_bytes // (1024 * 1024)} MB."
        )
    if extension == ".xlsx" and not is_zipfile(BytesIO(content)):
        raise SpreadsheetError("The XLSX file is not a valid workbook.")
    return extension


def list_excel_sheets(filename: str, content: bytes, max_size_bytes: int) -> list[str]:
    """Return worksheet names after validating an XLSX upload."""
    extension = _validate_upload(filename, content, max_size_bytes)
    if extension != ".xlsx":
        return []
    try:
        with pd.ExcelFile(BytesIO(content), engine="openpyxl") as workbook:
            return workbook.sheet_names
    except (ValueError, OSError, BadZipFile) as exc:
        raise SpreadsheetError("Unable to read the Excel workbook.") from exc


def load_tabular_file(
    filename: str,
    content: bytes,
    max_size_bytes: int,
    sheet_name: str | int = 0,
) -> pd.DataFrame:
    """Load a CSV or XLSX file into a DataFrame with resource limits."""
    extension = _validate_upload(filename, content, max_size_bytes)
    try:
        if extension == ".csv":
            try:
                frame = pd.read_csv(BytesIO(content), encoding="utf-8-sig")
            except UnicodeDecodeError:
                frame = pd.read_csv(BytesIO(content), encoding="cp1252")
        else:
            frame = pd.read_excel(
                BytesIO(content), sheet_name=sheet_name, engine="openpyxl"
            )
    except (EmptyDataError, ParserError, ValueError, OSError, BadZipFile) as exc:
        raise SpreadsheetError("Unable to parse the uploaded file. Check its contents.") from exc

    if frame.empty and len(frame.columns) == 0:
        raise SpreadsheetError("The selected file or worksheet contains no tabular data.")
    if len(frame) > MAX_ROWS:
        raise SpreadsheetError(f"The file exceeds the {MAX_ROWS:,}-row processing limit.")
    if len(frame.columns) > MAX_COLUMNS:
        raise SpreadsheetError(
            f"The file exceeds the {MAX_COLUMNS}-column processing limit."
        )
    return frame


def export_dataframe(frame: pd.DataFrame, file_format: str) -> bytes:
    """Serialize a DataFrame, neutralising spreadsheet formula injection."""
    if file_format not in {"csv", "xlsx"}:
        raise SpreadsheetError("Export format must be CSV or XLSX.")
    safe_frame = frame.copy()
    dangerous_prefixes = ("=", "+", "-", "@", chr(9), chr(13))
    for column in safe_frame.select_dtypes(include=["object", "string"]).columns:
        safe_frame[column] = safe_frame[column].map(
            lambda value: (
                "'" + value
                if isinstance(value, str) and value.startswith(dangerous_prefixes)
                else value
            )
        )

    output = BytesIO()
    if file_format == "csv":
        safe_frame.to_csv(output, index=False, encoding="utf-8-sig")
    else:
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            safe_frame.to_excel(writer, index=False, sheet_name="Processed Data")
    return output.getvalue()
