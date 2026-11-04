# Setup and local development

## Requirements

Python 3.11 or newer and Git.

## Install

Create and activate a virtual environment, then install the project and
development tools with `python -m pip install -e ".[dev]"`.

Copy `.env.example` to `.env` for local configuration.

## Run

Start the application with `python -m streamlit run app.py`. The local SQLite
database is created under `data/` on first startup.

## Test and lint

Run `pytest` and `ruff check .`.

## Configuration

See `.env.example`. Do not commit `.env`, local databases, uploads, or
business data.

## Current scope

This release establishes the application shell, configuration, persistence
foundation, logging, and tests. File automation, invoice extraction, order
management, inventory processing, and reporting are scheduled for later phases.
