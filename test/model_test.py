# import pytest
import sys
from pathlib import Path

# 将项目根目录添加到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import inspect
import traceback
from apps.udadmin.models import Permission
from apps.udadmin.utils.model_tools import get_model_info
# from apps.udadmin.utils.model_base import init_db, get_engine


# @pytest.mark.asyncio
async def test_main():
    # await init_db()
    try:
        mapper = inspect(Permission)
        print(dir(mapper))
        # print("="*80)
        print("=" * 50, "普通字段（columns）", "=" * 50)
        # 所有普通字段
        for col in mapper.columns:
            print(f"字段名: {col.name} | 类型: {col.type} | 是否主键: {col.primary_key}")

        print("\n" + "=" * 50, "关系字段（relationships）", "=" * 50)
        # 所有关系字段
        for rel in mapper.relationships:
            print(f"关系名: {rel.key}")
            print(f"  → 关联模型: {rel.mapper.class_}")
            print(f"  → 是否一对多/多对一: {not rel.uselist}")
            print(f"  → 是否多对多: {rel.secondary is not None}")
            print("-" * 80)
        # print(get_model_info(Permission))
        for attr in mapper.attrs.values():
            print(attr.key, type(attr))          # 字段名
    except Exception as e:
        print(traceback.format_exc())
        print(e)
    # finally:
        # await engine.dispose()


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_main())
