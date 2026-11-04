# Setup and local development

Requirements: Python 3.11 or newer and Git.

Create a virtual environment, install dependencies with python -m pip install -e ".[dev]", and copy .env.example to .env.

Start the application with python -m streamlit run app.py. The local SQLite database is created under data/ on first startup.

Run pytest and ruff check . for tests and linting. Upload size is controlled by BUSINESSFLOW_MAX_UPLOAD_MB. Do not commit .env, local databases, uploads or private business data.

The Data Workbench supports CSV/XLSX upload, cleaning, generic data-quality checks, consolidation, export and processing history. Invoice extraction, order management, inventory and advanced reporting remain planned.
