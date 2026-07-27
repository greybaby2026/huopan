"""Alembic 环境配置 - 自动检测模型变更

导入应用全部 ORM 模型, 使 Base.metadata 包含所有表定义.
Alembic 对比 metadata 与数据库实际结构, 生成增量迁移脚本.
"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

import sys
sys.path.insert(0, "/root/huopan/backend")

from app.core.config import settings
from app.core.database import Base

# 导入所有模型, 确保 Base.metadata 注册全部表
from app.models import user, product, customer, catalog, token, dicts, operation_log

config = context.config

# Alembic 不支持 async, 用同步驱动
if not config.get_main_option("sqlalchemy.url"):
    db_url = settings.database_url.replace("sqlite+aiosqlite", "sqlite")
    config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式: 生成 SQL 脚本"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True,
                       dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """在线模式: 连接数据库执行迁移"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata,
                          render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
