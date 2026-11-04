# BusinessFlow Automation Suite

**A practical Python workspace for small-business operations.**

BusinessFlow helps teams clean business spreadsheets, review PDF invoices,
manage customer orders, maintain inventory and produce operational reports from
saved records. It is built as a modular Python application with a Streamlit UI
and a transactional SQLAlchemy persistence layer.

## Features

### Data operations
- Upload and preview CSV and XLSX workbooks.
- Clean whitespace, column names, empty rows/columns and duplicate rows.
- Flag missing values, duplicate rows and empty datasets.
- Combine files by column name and export CSV/XLSX.
- Neutralise spreadsheet formula-like text in exported files.

### Invoices and orders
- Extract selectable text from PDF invoices and identify candidate fields.
- Review and edit invoice details and line items before explicit confirmation.
- Save confirmed invoice records, line items and processing history.
- Create and manage customer orders with exact decimal totals, duplicate-number
  protection, draft editing and controlled status transitions.
- Deduct linked product stock transactionally when an order is fulfilled.

### Inventory and reconciliation
- Maintain a product catalogue with unique SKUs, units, reorder levels and
  active/inactive status.
- Record opening balances, receipts, issues and positive adjustments in an
  auditable stock movement ledger.
- Run physical stocktakes, review variances and explicitly confirm reconciliation.
- Prevent negative stock and block stale stocktake reconciliation.

### Dashboard, reporting and traceability
- Review period-based order KPIs, order trends, order-status distribution, stock health, low-stock items and confirmed invoice values on the dashboard. KPIs and charts are calculated from saved workspace records; order values remain separated by currency.
- Analyse order status and current stock position from persisted records.
- View order values grouped by currency; currencies are never combined.
- Export orders, invoices, inventory, stock movements and processing activity
  as CSV or XLSX.
- Filter processing history by workflow, status and date; inspect logs and errors.
- Download filtered processing history as CSV.

## Demonstration workspace

The sidebar includes a separate Demo workspace backed by
`data/businessflow-demo.db`. The first selection creates an idempotent fictional dataset with 12 products, 30 orders, 20 confirmed invoices, stock movements and processing activity. The dashboard calculates period-based KPIs and charts from these persisted records; it does not display hard-coded business metrics.
The demo database is separate from the configured live database; switching
workspaces changes which database the UI reads and writes. Demo records are
local examples, not customer results. Remove the demo database file to reset
the demonstration dataset; it will be recreated on the next selection.

## Technology

Python 3.11+, Streamlit, Pandas, NumPy, OpenPyXL, SQLAlchemy, Pydantic, Plotly,
PyMuPDF, Pytest and Ruff.

## Quick start

1. Create and activate a Python 3.11+ virtual environment.
2. Install dependencies: python -m pip install -e ".[dev]". For PostgreSQL, install the optional driver with python -m pip install -e ".[postgres]".
3. Copy .env.example to .env and adjust settings if needed.
4. Start the app: python -m streamlit run app.py.
5. Open the Overview, Data Workbench, Invoice Processing, Order Management,
   Inventory Management, Reports & Exports or Processing History pages.

Run checks with pytest, ruff check . and the compile command in docs/setup.md.

## Configuration and data

See .env.example. Upload size is controlled by BUSINESSFLOW_MAX_UPLOAD_MB.
Do not commit .env, local databases, uploads or private business data.

No customer records, synthetic stock balances or fabricated business outcomes
are bundled. Inventory starts at zero unless a user enters a real opening
balance. Dashboard figures and reports are computed from saved workspace data.
Fictional spreadsheet examples for cleaning and consolidation are provided in `sample_data/`. These files intentionally include a duplicate and a missing value for validation demonstrations. Public datasets may be downloaded separately after reviewing licence, attribution and privacy conditions. See data/README.md.

## Architecture

The application is a modular Python monolith. Streamlit pages call application
services; processing, validation, inventory and reporting logic is UI-independent;
SQLAlchemy persists operational records and processing history. SQLite is the
initial database, with PostgreSQL support through SQLAlchemy-compatible
configuration. Existing SQLite installations receive an additive product_id
column for optional order-line catalogue links during database initialization.
See docs/architecture.md for persistence and reporting boundaries. Fiverr portfolio positioning and a safe demo walkthrough are in [docs/fiverr-portfolio.md](docs/fiverr-portfolio.md).

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
- Inventory counts are reviewed before reconciliation. If stock changes after a
  count snapshot is created, reconciliation is blocked and a new count is needed.
- Stock adjustments support receipts, issues and positive adjustments; decreases
  should be recorded as stock issues or physical stocktake variances.
- Dashboard and reports currently use the first configured business workspace.
  Inventory reports represent current balances, not historical balances.
- Date filtering uses record creation timestamps for transactional reports;
  inventory snapshots are not date-filtered.

## Roadmap

Deferred capabilities are planned, not abandoned: scanned-PDF OCR, external API
integrations, expanded multi-workspace support, formal schema migration tooling,
returns and post-fulfilment reversals, and expanded security/retention controls.
