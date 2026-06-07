from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from config import config

_is_sqlite = "sqlite" in config.database_url

# For remote Postgres (Neon), connections can be dropped when the DB
# auto-suspends or after idle timeouts. pool_pre_ping checks a connection is
# alive before use (avoids "server closed the connection" errors), and
# pool_recycle drops connections older than 5 min so we don't reuse stale ones.
_engine_kwargs = (
    {"connect_args": {"check_same_thread": False}}
    if _is_sqlite
    else {"pool_pre_ping": True, "pool_recycle": 300}
)
engine = create_engine(config.database_url, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Columns added after the initial schema. create_all() does not ALTER existing
# tables, so we add any missing columns here to keep an existing DB working.
_MIGRATIONS = {
    "users": {
        "jira_settings_enc": "TEXT",
    },
    "projects": {
        "owner_id": "VARCHAR",
    },
    "documents": {
        "cleaned_text": "TEXT",
    },
    "pipeline_runs": {
        "title": "VARCHAR",
        "requirement_details": "TEXT",
        "persona_override": "VARCHAR",
        "output_style": "VARCHAR",
        "document_ids": "JSON",
        "method": "VARCHAR",
    },
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate():
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as conn:
        for table, columns in _MIGRATIONS.items():
            if table not in existing_tables:
                continue
            present = {c["name"] for c in inspector.get_columns(table)}
            for col, col_type in columns.items():
                if col not in present:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}"))


def create_tables():
    from models import Base as ModelBase
    from sqlalchemy.exc import IntegrityError, ProgrammingError, OperationalError

    # create_all(checkfirst=True) skips existing tables, but on Postgres two app
    # instances booting at once can race: both pass the existence check, then one
    # CREATE hits a unique violation on the system catalog. Tables get created
    # either way, so tolerate the race instead of crashing on first boot.
    try:
        ModelBase.metadata.create_all(bind=engine, checkfirst=True)
    except (IntegrityError, ProgrammingError, OperationalError):
        pass
    try:
        _migrate()
    except (IntegrityError, ProgrammingError, OperationalError):
        pass
