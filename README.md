# BusinessFlow Automation Suite

**Automate repetitive business operations with Python.**

BusinessFlow is a modular Python application planned to help small businesses clean and consolidate spreadsheets, process invoices, manage orders and inventory, and generate operational reports.

> **Current release:** Phase 2 foundation. The application shell, configuration, SQLite persistence foundation, processing provenance models, and initial tests are established. Business-processing modules are delivered in later phases and are not represented as complete in this release.

## Architecture

BusinessFlow uses a modular Python monolith: Streamlit interface, independent Python workflow packages, SQLAlchemy persistence with SQLite initially, dataset provenance and processing history, and Pytest/Ruff verification.

See [Architecture](docs/architecture.md) and [Setup](docs/setup.md).

## Quick start

Requires Python 3.11 or newer. Create a virtual environment, install with `python -m pip install -e ".[dev]"`, copy `.env.example` to `.env`, then run `python -m streamlit run app.py`.

Run checks with `pytest` and `ruff check .`.

## Public datasets

Demonstration data will use public sources only after checking source licence, attribution, privacy and redistribution conditions. Raw datasets and processed business data are excluded from Git by default. See `data/README.md`.

## Planned modules

1. Excel/CSV automation and data quality.
2. PDF invoice extraction with human verification.
3. Order processing.
4. Inventory updates and reconciliation.
5. Business reporting and processing history.

## Security

Do not commit `.env`, credentials, local database files, uploads, or private business data. Upload validation and controlled storage are required before file-processing workflows are enabled.
