# alembic/env.py
from __future__ import annotations

from logging.config import fileConfig
import os

# Import Base (metadata) từ ORM models của bạn
from infra.db.models import Base  # <-- chỉnh import theo project của bạn
from sqlalchemy import engine_from_config, pool

from alembic import context

# Alembic Config
config = context.config

# Logging từ alembic.ini (nếu có)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---- URL/DSN: ưu tiên ENV (uv run --env-file .env ...) ----
DSN = os.getenv("VECTOR__DSN") or config.get_main_option("sqlalchemy.url")

print("dsn :", DSN)

# ---- Metadata để autogenerate ----
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Chạy migration ở chế độ offline (không tạo Engine)."""
    context.configure(
        url=DSN,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # so sánh kiểu cột
        compare_server_default=True,  # so sánh default ở server
        # render_as_batch=True,          # chỉ bật khi dùng SQLite
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Chạy migration ở chế độ online (tạo Engine + Connection)."""
    # Truyền DSN trực tiếp, bỏ qua url trong alembic.ini nếu ENV đã set
    connectable = engine_from_config(
        {"sqlalchemy.url": DSN},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            # render_as_batch=True,      # chỉ bật khi dùng SQLite
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
