# BusinessFlow Architecture

## Architecture style

BusinessFlow uses a modular Python monolith. Streamlit is the initial interface;
business workflows live in independent Python packages so they can later be
exposed through an API without rewriting processing logic.

## Request flow

1. Streamlit pages collect user input.
2. Application services coordinate a workflow.
3. Processing, inventory and domain modules validate and transform data.
4. SQLAlchemy persists records through transactional service operations.
5. Reporting services will create downloadable outputs in a later phase.
6. Processing jobs and logs provide workflow traceability.

## Technology

Python 3.11+, Streamlit, Pandas, NumPy, OpenPyXL, SQLAlchemy 2, SQLite,
Pydantic, Plotly, PyMuPDF, Pytest and Ruff.

## Persistence

SQLite is the initial local database. SQLAlchemy models and repository boundaries
keep the persistence layer portable to PostgreSQL. initialize_database
creates missing tables and currently applies one additive compatibility change
for optional product links on existing order lines. A formal migration framework
remains a planned improvement before larger schema changes.

Inventory quantities use three-decimal fixed precision. Each stock change adds
an immutable StockMovement record with its delta and resulting balance.
Product balances are updated in the same transaction as the ledger entry.
Physical counts retain the recorded and counted quantities; reconciliation
requires an explicit action and is rejected if the product balance changed
after the count snapshot was taken.

Order fulfilment and inventory deductions share one database transaction.
Only order lines explicitly linked to an active catalogue product deduct stock.
A unique (order_id, product_id) ledger constraint provides an additional
duplicate-deduction safeguard. Freeform order lines remain non-stock lines.

## Public data governance

Every public demonstration dataset must have a provenance record containing its
publisher, original URL, licence, attribution, retrieval date, version and
checksum where available. Licence and privacy checks are required before a
dataset is redistributed or committed.

## Security boundaries

- Secrets belong in environment variables, never source control.
- Raw and processed uploads are excluded from Git.
- Upload validation must check file size, extension and actual content.
- User-supplied paths must not be trusted.
- Database writes that change business state must use transactions.
