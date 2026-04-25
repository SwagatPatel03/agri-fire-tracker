from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# GeoAlchemy2 helpers for proper PostGIS handling in migrations
from geoalchemy2 import alembic_helpers

# Import our app config and models
from app.core.config import settings
from app.db.database import Base
import app.models  # noqa: F401 — ensures all models are registered

# Alembic Config object
config = context.config

# Set the database URL dynamically from our settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Setup logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The MetaData object for autogenerate support
target_metadata = Base.metadata

# ── Table/schema exclusion filter ─────────────────────────────
# PostGIS installs Tiger geocoder tables (addr, edges, faces, etc.)
# and topology tables that we don't manage. Exclude them from autogenerate.
OUR_TABLES = {"active_fires", "districts", "alerts"}


def _include_object(obj, name, type_, reflected, compare_to):
    """Only include our app's tables in autogenerate, skip PostGIS system tables."""
    # First let geoalchemy2 decide
    if not alembic_helpers.include_object(obj, name, type_, reflected, compare_to):
        return False

    # For tables: only include ours
    if type_ == "table":
        return name in OUR_TABLES

    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generates SQL without DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=_include_object,
        process_revision_directives=alembic_helpers.writer,
        render_item=alembic_helpers.render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (with a live DB connection)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=_include_object,
            process_revision_directives=alembic_helpers.writer,
            render_item=alembic_helpers.render_item,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
