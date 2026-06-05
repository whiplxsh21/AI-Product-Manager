from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from config import config

engine = create_engine(
    config.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in config.database_url else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Columns added after the initial schema. create_all() does not ALTER existing
# tables, so we add any missing columns here to keep an existing DB working.
_MIGRATIONS = {
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
    ModelBase.metadata.create_all(bind=engine)
    _migrate()
