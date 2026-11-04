# BusinessFlow Automation Suite

**Automate repetitive business operations with Python.**

BusinessFlow is a modular Python application for small businesses to clean and
consolidate spreadsheets, extract and review PDF invoices, manage customer
orders, maintain stock, and reconcile physical inventory.

## Implemented features

- Upload and preview CSV and XLSX workbooks.
- Clean whitespace, column names, empty rows/columns and duplicate rows.
- Flag missing values, duplicate rows and empty datasets.
- Combine files by column name and export CSV/XLSX.
- Extract selectable text from PDF invoices and identify candidate invoice fields.
- Review and edit invoice details and line items before explicit confirmation.
- Persist confirmed invoice records, line items and processing history in SQLite.
- Create and manage customer orders with exact decimal totals, duplicate-number
  protection, draft editing and controlled status transitions.
- Maintain a product catalogue with unique SKUs, units, reorder levels and
  active/inactive status.
- Record opening balances, receipts, issues and positive stock adjustments in
  an auditable stock movement ledger.
- Run physical stocktakes, review variances and explicitly confirm reconciliation.
- Deduct stock transactionally when an order containing catalogue-linked items
  is fulfilled; non-stock order lines remain unaffected.
- Record inventory and order activity in processing history.
- Do not retain original invoice PDFs or extracted full text by default.
- Neutralise spreadsheet formula-like text in exported files.

See docs/spreadsheet-workflows.md, docs/invoice-workflows.md,
docs/inventory-workflows.md and docs/architecture.md for workflow behaviour
and limits.

## Technology

Python 3.11+, Streamlit, Pandas, NumPy, OpenPyXL, SQLAlchemy, Pydantic, Plotly,
PyMuPDF, Pytest and Ruff.

## Quick start

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies: python -m pip install -e ".[dev]".
3. Copy .env.example to .env and adjust settings if needed.
4. Start the app: python -m streamlit run app.py.
5. Open Inventory Management, Order Management, Data Workbench or Invoice
   Processing from the sidebar.

Run checks with pytest, ruff check ., and the compile command in docs/setup.md.

## Configuration

See .env.example. Upload size is controlled by BUSINESSFLOW_MAX_UPLOAD_MB.
Do not commit .env, local databases, uploads or private business data.

## Architecture

The application is a modular Python monolith. Streamlit pages call application
services; processing, validation and inventory logic are UI-independent;
SQLAlchemy persists operational records and processing history. SQLite is the
initial database, with PostgreSQL support through SQLAlchemy-compatible
configuration. Existing SQLite installations receive an additive product_id
column for optional order-line catalogue links during database initialization.

## Demonstration data

No customer records, synthetic stock balances or fabricated business outcomes
are bundled. Inventory starts at zero unless a user enters a real opening
balance. Public datasets may be downloaded separately after reviewing licence,
attribution and privacy conditions. See data/README.md.

## Roadmap

Deferred capabilities are planned, not abandoned: scanned-PDF OCR, richer
dashboards and downloadable reports, external API integrations, expanded
multi-workspace support, formal schema migration tooling, and expanded
security/retention controls. They will be implemented in later phases after
the core workflows are stable.

## Known limitations

- Spreadsheet support is CSV and XLSX; Excel consolidation uses the first worksheet.
- Spreadsheet validation is generic and does not infer business-specific rules.
- Spreadsheet processing is limited to 250,000 rows and 200 columns per file.
- Invoice extraction supports selectable-text PDFs only; OCR and complex layouts
  are deferred, and extracted fields require human verification.
- Orders support manual entry; catalogue links are optional. Only linked product
  lines affect inventory when an order is fulfilled.
- A fulfilled order cannot be cancelled or automatically restocked. Returns and
  post-fulfilment reversals require a future controlled workflow.
- Inventory counts are reviewed before reconciliation. If stock changes after
  a count snapshot is created, reconciliation is blocked and a new count is needed.
- Stock adjustments currently support receipts, issues and positive adjustments;
  decreases should be recorded as stock issues or physical stocktake variances.
- The current UI uses the first configured business workspace; multi-tenant
  selection is not yet available.
