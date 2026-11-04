# BusinessFlow Architecture

## Architecture style

BusinessFlow uses a modular Python monolith. Streamlit is the interface; business
workflows live in independent Python packages so they can later be exposed through
an API without rewriting processing logic.

## Request flow

1. Streamlit pages collect user input and render workflow results.
2. Application services coordinate a workflow.
3. Processing, inventory, reporting and domain modules validate and transform data.
4. SQLAlchemy persists records through transactional service operations.
5. Reporting queries saved workspace records and exports CSV or XLSX files.
6. Processing jobs, logs and errors provide workflow traceability.

## Technology

Python 3.11+, Streamlit, Pandas, NumPy, OpenPyXL, SQLAlchemy 2, SQLite,
Pydantic, Plotly, PyMuPDF, Pytest and Ruff.

## Persistence

SQLite is the initial local database. SQLAlchemy models and repository boundaries
keep the persistence layer portable to PostgreSQL. initialize_database creates
missing tables and currently applies one additive compatibility change for optional
product links on existing order lines. A formal migration framework remains a
planned improvement before larger schema changes.

Inventory quantities use three-decimal fixed precision. Each stock change adds an
immutable StockMovement record with its delta and resulting balance. Product
balances are updated in the same transaction as the ledger entry. Physical counts
retain recorded and counted quantities; reconciliation requires an explicit action
and is rejected if the product balance changed after the count snapshot was taken.

Order fulfilment and inventory deductions share one database transaction. Only
order lines explicitly linked to an active catalogue product deduct stock. A unique
(order_id, product_id) ledger constraint provides an additional duplicate-deduction
safeguard. Freeform order lines remain non-stock lines.

## Reporting

The reporting service reads the first configured workspace, matching the current
single-workspace UI behaviour. Dashboard counts, order status analysis, inventory
position and processing activity are derived from persisted records. Financial
order totals are grouped by currency and are never combined across currencies.
Orders, invoices, inventory, stock movements and processing jobs can be exported
to CSV or XLSX. Date filters apply to record creation timestamps for orders,
invoices, movements and jobs; inventory is a current snapshot and is not date
filtered. Exports contain saved business data only and do not append demonstration
rows. XLSX exports include a frozen header and filter row.

## Public data governance

Every public demonstration dataset must have a provenance record containing its
publisher, original URL, licence, attribution, retrieval date, version and checksum
where available. Licence and privacy checks are required before redistribution or
commitment to source control.

## Security boundaries

- Secrets belong in environment variables, never source control.
- Raw and processed uploads are excluded from Git.
- Upload validation must check file size, extension and actual content.
- User-supplied paths must not be trusted.
- Database writes that change business state must use transactions.
