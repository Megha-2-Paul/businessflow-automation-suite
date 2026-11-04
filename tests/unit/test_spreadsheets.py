"""Unit tests for spreadsheet parsing, cleaning and validation."""
from io import BytesIO
from zipfile import ZipFile

import pandas as pd
import pytest

from processing.cleaning import clean_dataframe, consolidate_dataframes
from processing.spreadsheets import (
    SpreadsheetError,
    export_dataframe,
    list_excel_sheets,
    load_tabular_file,
)
from validation.spreadsheets import validate_dataframe


def test_load_csv_and_fallback_encoding():
    csv_data = "name,city\nAndr\u00e9,Montr\u00e9al\n".encode("cp1252")
    frame = load_tabular_file("customers.csv", csv_data, 1024)
    assert frame.to_dict(orient="records") == [
        {"name": "Andr\u00e9", "city": "Montr\u00e9al"}
    ]


def test_load_xlsx_and_list_sheets():
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame({"item": ["Pen"]}).to_excel(writer, sheet_name="Stock", index=False)
    content = output.getvalue()
    assert list_excel_sheets("stock.xlsx", content, 100_000) == ["Stock"]
    frame = load_tabular_file("stock.xlsx", content, 100_000, "Stock")
    assert frame.loc[0, "item"] == "Pen"


def test_reject_invalid_xlsx_archive_structure():
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame({"item": ["Pen"]}).to_excel(writer, index=False)
    source = ZipFile(BytesIO(output.getvalue()))
    rebuilt = BytesIO()
    with ZipFile(rebuilt, "w") as archive:
        for item in source.infolist():
            if item.filename != "xl/workbook.xml":
                archive.writestr(item, source.read(item.filename))
    source.close()
    with pytest.raises(SpreadsheetError, match="required workbook content"):
        load_tabular_file("bad.xlsx", rebuilt.getvalue(), 100_000)


def test_reject_nonpositive_upload_limit():
    with pytest.raises(SpreadsheetError, match="positive"):
        load_tabular_file("file.csv", b"a,b", 0)


def test_reject_unsupported_empty_oversized_and_invalid_workbook():
    with pytest.raises(SpreadsheetError, match="Only CSV"):
        load_tabular_file("data.xls", b"data", 100)
    with pytest.raises(SpreadsheetError, match="empty"):
        load_tabular_file("data.csv", b"", 100)
    with pytest.raises(SpreadsheetError, match="configured limit"):
        load_tabular_file("data.csv", b"a,b", 2)
    with pytest.raises(SpreadsheetError, match="valid workbook"):
        load_tabular_file("data.xlsx", b"not an xlsx", 100)


def test_clean_dataframe_reports_changes_and_keeps_original():
    source = pd.DataFrame(
        {" Product Name ": [" Pen ", " Pen ", None], "Unused": [None, None, None]}
    )
    cleaned, summary = clean_dataframe(source)
    assert list(cleaned.columns) == ["product_name"]
    assert cleaned["product_name"].tolist() == ["Pen"]
    assert summary["duplicates_removed"] == 1
    assert summary["columns_removed"] == 1
    assert summary["rows_removed"] == 1
    assert summary["values_trimmed"] == 2
    assert source.columns.tolist() == [" Product Name ", "Unused"]


def test_clean_dataframe_disambiguates_normalized_column_names():
    source = pd.DataFrame([[1, 2]], columns=["Order ID", "order-id"])
    cleaned, _ = clean_dataframe(source)
    assert cleaned.columns.tolist() == ["order_id", "order_id_2"]


def test_consolidation_retains_columns_unique_to_each_file():
    combined, summary = consolidate_dataframes(
        [pd.DataFrame({"sku": ["A"]}), pd.DataFrame({"sku": ["B"], "qty": [2]})]
    )
    assert combined["sku"].tolist() == ["A", "B"]
    assert pd.isna(combined.loc[0, "qty"])
    assert combined.loc[1, "qty"] == 2
    assert summary["columns_only_in_some_files"] == ["qty"]


def test_consolidation_requires_at_least_one_file():
    with pytest.raises(ValueError, match="At least one"):
        consolidate_dataframes([])


def test_validation_detects_missing_values_and_duplicates():
    frame = pd.DataFrame({"sku": ["A", "A", "B"], "qty": [1, 1, None]})
    issues = validate_dataframe(frame)
    assert {issue["issue_type"] for issue in issues} == {
        "missing_values",
        "duplicate_rows",
    }
def test_exports_round_trip_and_neutralize_formula_values():
    frame = pd.DataFrame({"value": ["=1+1", "normal", "\tmalicious"]})
    csv_bytes = export_dataframe(frame, "csv")
    assert b"'=1+1" in csv_bytes
    assert b"'\tmalicious" in csv_bytes
    excel_bytes = export_dataframe(frame, "xlsx")
    reloaded = pd.read_excel(BytesIO(excel_bytes))
    assert reloaded.loc[0, "value"] == "'=1+1"
    assert reloaded.loc[2, "value"] == "'\tmalicious"
    with pytest.raises(SpreadsheetError, match="CSV or XLSX"):
        export_dataframe(frame, "pdf")
