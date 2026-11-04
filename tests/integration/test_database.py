"""Integration tests for database initialization and relationships."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import Business, DatasetSource, ProcessingJob
from database.session import build_engine, initialize_database


def test_database_initializes_and_persists_related_records(tmp_path):
    db_path = tmp_path / "test.db"
    url = f"sqlite:///{db_path}"
    engine = build_engine(url)
    initialize_database(url)

    with Session(engine) as session:
        business = Business(name="Public Dataset Demo", currency="GBP")
        session.add(business)
        session.flush()
        source = DatasetSource(
            business_id=business.id,
            source_name="Online Retail II",
            publisher="UCI Machine Learning Repository",
            source_url="https://archive.ics.uci.edu/dataset/502/online+retail+ii",
            license_name="CC BY 4.0",
            source_version="1",
        )
        session.add(source)
        session.add(ProcessingJob(business_id=business.id, job_type="dataset_import"))
        session.commit()

        assert session.scalar(
            select(Business).where(Business.name == "Public Dataset Demo")
        ) is not None
        assert session.scalar(
            select(DatasetSource).where(DatasetSource.source_name == "Online Retail II")
        ) is not None
        assert session.scalar(
            select(ProcessingJob).where(ProcessingJob.status == "pending")
        ) is not None

    engine.dispose()


def test_initialize_database_is_idempotent(tmp_path):
    url = f"sqlite:///{tmp_path / 'idempotent.db'}"
    initialize_database(url)
    initialize_database(url)


def test_database_enforces_foreign_keys(tmp_path):
    from sqlalchemy.exc import IntegrityError

    url = f"sqlite:///{tmp_path / 'fk.db'}"
    engine = build_engine(url)
    initialize_database(url)

    with Session(engine) as session:
        session.add(ProcessingJob(business_id=999, job_type="invalid"))
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
        else:
            raise AssertionError("Expected foreign-key constraint to reject unknown business.")
    engine.dispose()
