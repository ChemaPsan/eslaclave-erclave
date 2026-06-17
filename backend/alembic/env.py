from logging.config import fileConfig
import importlib.util
import os
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def load_admin_metadata():
    models_path = Path(__file__).resolve().parents[1] / "services" / "admin-service" / "app" / "models.py"
    spec = importlib.util.spec_from_file_location("admin_service_models", models_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load admin-service models from {models_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.Base.metadata


target_metadata = load_admin_metadata()


def get_database_url() -> str:
    database_url = os.getenv("ERCLAVE_DATABASE_URL")
    if not database_url:
        raise RuntimeError("ERCLAVE_DATABASE_URL is required to run Alembic migrations.")
    return database_url


def run_migrations_offline() -> None:
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section, {})
    section["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
