"""Data-quality checks for tabular business data."""
from __future__ import annotations

import pandas as pd


def validate_dataframe(frame: pd.DataFrame) -> list[dict[str, object]]:
    """Return actionable warnings for missing values and duplicate records."""
    issues: list[dict[str, object]] = []
    if frame.empty:
        issues.append(
            {
                "severity": "warning",
                "issue_type": "empty_dataset",
                "column": None,
                "count": 0,
                "details": "The dataset contains no data rows.",
            }
        )

    for column in frame.columns:
        missing_count = int(frame[column].isna().sum())
        if missing_count:
            issues.append(
                {
                    "severity": "warning",
                    "issue_type": "missing_values",
                    "column": str(column),
                    "count": missing_count,
                    "details": f"{missing_count:,} missing value(s) in {column}.",
                }
            )

    duplicate_count = int(frame.duplicated().sum())
    if duplicate_count:
        issues.append(
            {
                "severity": "warning",
                "issue_type": "duplicate_rows",
                "column": None,
                "count": duplicate_count,
                "details": f"{duplicate_count:,} duplicate row(s).",
            }
        )
    return issues
