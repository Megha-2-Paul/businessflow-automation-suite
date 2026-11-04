# Setup and local development

Requirements: Python 3.11 or newer and Git.

1. Create and activate a virtual environment.
2. Install dependencies with python -m pip install -e ".[dev]".
3. Copy .env.example to .env and adjust settings if needed. SQLite is ready by default. For PostgreSQL, install `python -m pip install -e ".[postgres]"`, then set `BUSINESSFLOW_DATABASE_URL` to a PostgreSQL SQLAlchemy URL such as `postgresql+psycopg://user:password@host:5432/database`. Keep credentials in environment variables or a local ignored `.env` file.
4. Start the application with python -m streamlit run app.py.

The local SQLite database is created under data/ on first startup. Run pytest,
ruff check . and the compile command below to check the application.

    python -m compileall -q app.py config database logging_config ui processing validation services invoices orders inventory reporting tests

`BUSINESSFLOW_MAX_UPLOAD_MB` accepts whole numbers from 1 to 500. `BUSINESSFLOW_ENVIRONMENT` accepts `development`, `testing` or `production`; `BUSINESSFLOW_LOG_LEVEL` must be a standard Python logging level. Database URLs are checked at startup. Do not commit `.env`,
local databases, uploads or private business data.

## Main workflows

- **Data Workbench:** CSV/XLSX upload, preview, cleaning, generic data-quality
  checks, consolidation and CSV/XLSX export.
- **Invoice Processing:** selectable-text PDF extraction with human review and
  confirmation. OCR and complex layouts are not supported.
- **Order Management:** manual orders, editable drafts, duplicate protection and
  controlled status transitions. Fulfilment deducts only linked catalogue stock.
- **Inventory Management:** product catalogue, stock receipts/issues/adjustments,
  ledger and reviewed physical stocktake reconciliation.
- **Business Overview:** live database-backed counts, order status analysis,
  currency-separated order values, current stock position and recent activity.
- **Reports & Exports:** order, invoice, inventory, stock movement and processing
  reports with CSV/XLSX downloads. Date filters apply to dated transactional
  records; inventory is a current snapshot.
- **Processing History:** workflow, status and date filters with per-job logs,
  error details and filtered CSV export.

The UI currently uses the first configured business workspace. There is no login or role-based access control: use only in a trusted, access-controlled environment and do not expose the app publicly. PostgreSQL support requires the optional psycopg extra; automated PostgreSQL schema migrations are not included. Back up databases before upgrades. Reports and the
Dashboard use the same workspace boundary. No fabricated records are bundled.
