# BusinessFlow Automation Suite

**Automate repetitive business operations with Python.**

BusinessFlow is a modular Python application for small businesses to clean and
consolidate spreadsheets, validate business data, process invoices, manage orders
and inventory, and generate operational reports.

> **Current release:** Phase 3 spreadsheet workflows are implemented. The
> application foundation, SQLite persistence, processing history, and the CSV/XLSX
> Data Workbench are available. Invoice, order, inventory and advanced reporting
> workflows remain planned.

## Features

- Upload and preview CSV and XLSX workbooks.
- Clean text whitespace, column names, empty rows/columns and duplicate rows.
- Flag missing values, duplicate rows and empty datasets.
- Combine multiple files by column name without discarding unmatched columns.
- Export cleaned and combined data as CSV or XLSX.
- Record processing jobs and data-quality findings in SQLite.
- Neutralise spreadsheet formula-like text in exported files.

See docs/spreadsheet-workflows.md for behaviour and limits.

## Technology

Python 3.11+, Streamlit, Pandas, NumPy, OpenPyXL, SQLAlchemy, Pydantic, Plotly,
PyMuPDF, Pytest and Ruff.

## Quick start

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies: python -m pip install -e ".[dev]".
3. Copy .env.example to .env and adjust settings if needed.
4. Start the app: python -m streamlit run app.py.
5. Open Data Workbench to clean or combine files.

Run checks with pytest, ruff check ., and the compileall command in docs/setup.md.

## Configuration

See .env.example. Upload size is controlled by BUSINESSFLOW_MAX_UPLOAD_MB.
Do not commit .env, local databases, uploads or private business data.

## Architecture

The application is a modular Python monolith. Streamlit pages call application
services; processing and validation functions are UI-independent; SQLAlchemy
persists processing history. SQLite is the initial database, with PostgreSQL
support available through SQLAlchemy-compatible connection configuration.

## Demonstration data

No customer records or synthetic business outcomes are bundled. A public retail
dataset may be downloaded separately after reviewing its licence, attribution
and privacy conditions. See data/README.md.

## Known limitations

- Only CSV and XLSX are accepted; XLS/XLSM are not supported.
- Generic validation does not infer business-specific rules.
- Excel consolidation uses the first worksheet in each uploaded workbook.
- Processing is in-memory and limited to 250,000 rows and 200 columns per file.
- The current workspace uses the first configured business record; multi-tenant
  workspace selection is not yet part of the UI.
