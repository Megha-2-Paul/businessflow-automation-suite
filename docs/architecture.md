# BusinessFlow Architecture

## Architecture style

BusinessFlow uses a modular Python monolith. Streamlit is the initial interface;
business workflows live in independent Python packages so they can later be
exposed through an API without rewriting processing logic.

## Request flow

1. Streamlit pages collect user input.
2. Application services coordinate a workflow.
3. Processing and domain modules validate and transform data.
4. Repository functions persist records through SQLAlchemy.
5. Reporting services create downloadable outputs.
6. Processing jobs, logs, and errors provide traceability.

## Technology

Python 3.11+, Streamlit, Pandas, NumPy, OpenPyXL, SQLAlchemy 2, SQLite,
Pydantic, Plotly, PyMuPDF, Pytest and Ruff.

## Persistence

SQLite is the initial local database. SQLAlchemy models and repository boundaries
keep the persistence layer portable to PostgreSQL. Database schema changes will
be managed through migrations when domain modules are introduced.

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
