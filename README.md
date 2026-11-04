# BusinessFlow Automation Suite

**Automate repetitive business operations with Python.**

BusinessFlow is a modular Python application for small businesses to clean and
consolidate spreadsheets, extract and review PDF invoices, manage orders and
inventory, and generate operational reports.

> **Current release:** CSV/XLSX data cleaning and consolidation plus human-reviewed
> PDF invoice extraction are implemented. Order management, inventory reconciliation,
> advanced reporting, integrations and expanded security controls remain on the roadmap.

## Features

- Upload and preview CSV and XLSX workbooks.
- Clean whitespace, column names, empty rows/columns and duplicate rows.
- Flag missing values, duplicate rows and empty datasets.
- Combine files by column name and export CSV/XLSX.
- Extract selectable text from PDF invoices and identify candidate invoice fields.
- Review and edit invoice details and line items before explicit confirmation.
- Persist confirmed invoice records, line items and processing history in SQLite.
- Do not retain the original invoice PDF or extracted full text by default.
- Neutralise spreadsheet formula-like text in exported files.

See docs/spreadsheet-workflows.md and docs/invoice-workflows.md for workflow behaviour and limits.

## Technology

Python 3.11+, Streamlit, Pandas, NumPy, OpenPyXL, SQLAlchemy, Pydantic, Plotly,
PyMuPDF, Pytest and Ruff.

## Quick start

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies: python -m pip install -e ".[dev]".
3. Copy .env.example to .env and adjust settings if needed.
4. Start the app: python -m streamlit run app.py.
5. Open Data Workbench or Invoice Processing from the sidebar.

Run checks with pytest, ruff check ., and the compileall command in docs/setup.md.

## Configuration

See .env.example. Upload size is controlled by BUSINESSFLOW_MAX_UPLOAD_MB.
Do not commit .env, local databases, uploads or private business data.

## Architecture

The application is a modular Python monolith. Streamlit pages call application
services; processing and validation functions are UI-independent; SQLAlchemy
persists operational records and processing history. SQLite is the initial
database, with PostgreSQL support through SQLAlchemy-compatible configuration.

## Demonstration data

No customer records or synthetic business outcomes are bundled. Public datasets
may be downloaded separately after reviewing licence, attribution and privacy
conditions. See data/README.md.

## Roadmap

Deferred capabilities are planned, not abandoned: scanned-PDF OCR, order management,
inventory snapshots and reconciliation, richer dashboards/reports, integrations,
expanded multi-workspace support, and security/retention controls. They will be
implemented in later phases after the core workflows are stable.

## Known limitations

- Spreadsheet support is CSV and XLSX; Excel consolidation uses the first worksheet.
- Spreadsheet validation is generic and does not infer business-specific rules.
- Spreadsheet processing is limited to 250,000 rows and 200 columns per file.
- Invoice extraction supports selectable-text PDFs only; OCR and complex layouts are deferred.
- Invoice field extraction is heuristic and requires human verification.
- The current UI uses the first configured business workspace; multi-tenant selection is not yet available.
