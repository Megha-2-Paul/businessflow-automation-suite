"""Reusable DataFrame cleaning and consolidation operations."""
from __future__ import annotations

import re

import pandas as pd


def _unique_column_names(columns: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    result: list[str] = []
    for column in columns:
        base = column or "column"
        counts[base] = counts.get(base, 0) + 1
        result.append(base if counts[base] == 1 else f"{base}_{counts[base]}")
    return result


def clean_dataframe(
    frame: pd.DataFrame,
    *,
    trim_text: bool = True,
    standardize_columns: bool = True,
    remove_duplicates: bool = True,
    remove_empty: bool = True,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Clean a copy of a DataFrame and return a concise change summary."""
    cleaned = frame.copy()
    summary = {
        "rows_removed": 0,
        "columns_removed": 0,
        "duplicates_removed": 0,
        "values_trimmed": 0,
        "columns_renamed": 0,
    }

    if trim_text:
        for column in cleaned.select_dtypes(include=["object", "string"]).columns:
            original = cleaned[column]
            trimmed = original.map(
                lambda value: value.strip() if isinstance(value, str) else value
            )
            summary["values_trimmed"] += int(
                (original.fillna("") != trimmed.fillna("")).sum()
            )
            cleaned[column] = trimmed

    if remove_empty:
        before_rows = len(cleaned)
        cleaned = cleaned.dropna(how="all")
        summary["rows_removed"] += before_rows - len(cleaned)
        empty_columns = cleaned.columns[cleaned.isna().all()].tolist()
        summary["columns_removed"] = len(empty_columns)
        cleaned = cleaned.drop(columns=empty_columns)

    if standardize_columns:
        normalized = [
            re.sub(r"[^0-9a-zA-Z]+", "_", str(column).strip()).strip("_").lower()
            for column in cleaned.columns
        ]
        unique_names = _unique_column_names(normalized)
        summary["columns_renamed"] = sum(
            old != new for old, new in zip(cleaned.columns, unique_names, strict=True)
        )
        cleaned.columns = unique_names

    if remove_duplicates:
        before_rows = len(cleaned)
        cleaned = cleaned.drop_duplicates().reset_index(drop=True)
        summary["duplicates_removed"] = before_rows - len(cleaned)

    return cleaned, summary


def consolidate_dataframes(
    frames: list[pd.DataFrame],
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Combine tables by column name without discarding unmatched columns."""
    if not frames:
        raise ValueError("At least one spreadsheet is required for consolidation.")
    columns_by_file = [set(map(str, frame.columns)) for frame in frames]
    all_columns = set.union(*columns_by_file)
    common_columns = set.intersection(*columns_by_file)
    combined = pd.concat(frames, ignore_index=True, sort=False)
    summary: dict[str, object] = {
        "files_combined": len(frames),
        "rows_combined": len(combined),
        "columns_combined": len(combined.columns),
        "columns_only_in_some_files": sorted(all_columns - common_columns),
    }
    return combined, summary
