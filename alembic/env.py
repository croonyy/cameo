import sys
import os
import importlib
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# --------------------------
# 🔥 自动导入所有 apps/*/models.py
# --------------------------
from db.sa import Base

APPS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "apps")

# 遍历 apps 下所有子文件夹，自动导入 models
for app_name in os.listdir(APPS_DIR):
    app_path = os.path.join(APPS_DIR, app_name)
    if os.path.isdir(app_path):
        models_path = os.path.join(app_path, "models.py")
        if os.path.exists(models_path):
            try:
                importlib.import_module(f"apps.{app_name}.models")
                print(f"✅ 导入模型: apps.{app_name}.models")
            except Exception as e:
                print(f"❌ 导入失败 apps.{app_name}.models: {e}")

# --------------------------
# Alembic 标准配置
# --------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()