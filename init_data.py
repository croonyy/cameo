import asyncio
import os
import random
import subprocess
import sys
import traceback
import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import click
from sqlalchemy import func, select

from apps.demo import models as demo_md
from apps.demo import ui as demo_ui
from apps.udadmin import models as md
from apps.udadmin import ui as udadmin_ui
from apps.udadmin.utils.auth import pwd_context as pc
from apps.udadmin.utils.model_tools import model_perms
from apps.udadmin.utils.ui_tools import UiInfo, get_custom_action_permissions
from config.settings import BASE_DIR
from db.sa import async_session_factory, engine


BASE_PATH = Path(BASE_DIR)
DB_PATH = BASE_PATH / "db" / "db.sqlite3"
CRUD_ACTIONS = tuple(model_perms.values())


# ---------------------------------------------------------------------------
# Database and migration helpers
# ---------------------------------------------------------------------------
def _safe_print(text: str) -> None:
    encoding = sys.stdout.encoding or "utf-8"
    safe_text = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
    print(safe_text)


def _run_command(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    result = subprocess.run(
        [sys.executable, *args],
        cwd=BASE_PATH,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    if result.stdout:
        _safe_print(result.stdout.strip())
    if result.stderr:
        _safe_print(result.stderr.strip())
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {sys.executable} {' '.join(args)}")
    return result


def reset_sqlite_database() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"✓ Deleted database: {DB_PATH}")
    else:
        print(f"✓ Database does not exist, skip delete: {DB_PATH}")


def run_alembic_migrations() -> None:
    print("✓ Running Alembic upgrade head")
    _run_command(["-m", "alembic", "upgrade", "head"])

    print("✓ Checking model changes for Alembic autogenerate")
    check_result = _run_command(["-m", "alembic", "check"], check=False)
    output = f"{check_result.stdout}\n{check_result.stderr}"
    if check_result.returncode == 0:
        print("✓ No pending model changes; no new migration file needed")
        return
    if "New upgrade operations detected" not in output:
        raise RuntimeError("Alembic check failed for a reason other than model changes.")

    print("✓ Generating Alembic migration for pending model changes")
    _run_command(["-m", "alembic", "revision", "--autogenerate", "-m", "auto_model_sync"])
    print("✓ Applying generated Alembic migration")
    _run_command(["-m", "alembic", "upgrade", "head"])


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------
def _rand_datetime(start_year: int = 2023, end_year: int = 2026) -> datetime:
    start = datetime(start_year, 1, 1, tzinfo=timezone.utc)
    end = datetime(end_year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    return start + timedelta(
        days=random.randint(0, (end - start).days),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )


def _rand_date(start_year: int = 2022, end_year: int = 2026) -> date:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))


def _rand_cn_name(index: int) -> str:
    last_names = ["王", "李", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴"]
    first_names = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
    return f"{last_names[index % len(last_names)]}{first_names[index % len(first_names)]}"


def _iter_models(module) -> list[type]:
    models = []
    for value in module.__dict__.values():
        if isinstance(value, type) and hasattr(value, "__tablename__") and hasattr(value, "__table__"):
            if value.__dict__.get("__abstract__", False):
                continue
            models.append(value)
    return sorted(models, key=lambda item: item.__name__)


def _permission_name(model: type, action: str) -> str:
    app_name = getattr(model, "app_name", model.__tablename__.split("_")[0])
    return f"{app_name}:{model.__name__}:{action}"


def _perm_names_for_models(models: list[type], actions: tuple[str, ...] = CRUD_ACTIONS) -> list[str]:
    return [_permission_name(model, action) for model in models for action in actions]


def _iter_ui_infos(*modules) -> list[UiInfo]:
    ui_infos = []
    for module in modules:
        for value in module.__dict__.values():
            if isinstance(value, UiInfo):
                ui_infos.append(value)
    return ui_infos


def _custom_action_permission_names() -> list[str]:
    names = []
    for ui_info in _iter_ui_infos(udadmin_ui, demo_ui):
        model = ui_info._model
        app_name = getattr(model, "app_name", model.__tablename__.split("_")[0])
        names.extend(
            get_custom_action_permissions(
                app_name, model.__name__, getattr(ui_info, "custom_actions", [])
            )
        )
    return names


def _custom_action_perm_names_for_app(app_name: str) -> list[str]:
    return [name for name in _custom_action_permission_names() if name.startswith(f"{app_name}:")]


def _custom_action_perm_names_for_models(models: list[type]) -> list[str]:
    prefixes = {
        f"{getattr(model, 'app_name', model.__tablename__.split('_')[0])}:{model.__name__}:"
        for model in models
    }
    return [
        name
        for name in _custom_action_permission_names()
        if any(name.startswith(prefix) for prefix in prefixes)
    ]


async def _create_permissions(session):
    permission_types = [
        md.PermissionType(id=1, name="model", extra={"description": "模型级别权限"}),
        md.PermissionType(id=2, name="api", extra={"description": "API接口权限"}),
        md.PermissionType(id=3, name="menu", extra={"description": "菜单权限"}),
    ]
    session.add_all(permission_types)
    await session.flush()

    models = _iter_models(md) + _iter_models(demo_md)
    permissions = []
    next_id = 1
    for model in models:
        for action in CRUD_ACTIONS:
            permissions.append(
                md.Permission(
                    id=next_id,
                    name=_permission_name(model, action),
                    permission_type_id=1,
                    extra={"app": getattr(model, "app_name", ""), "model": model.__name__, "action": action},
                )
            )
            next_id += 1
    for perm_name in _custom_action_permission_names():
        permissions.append(
            md.Permission(
                id=next_id,
                name=perm_name,
                permission_type_id=1,
                extra={"action": "custom_action"},
            )
        )
        next_id += 1
    session.add_all(permissions)
    await session.flush()
    return {perm.name: perm for perm in permissions}, models


async def _create_roles(session, permissions_by_name: dict[str, md.Permission], models: list[type]):
    all_model_perms = list(permissions_by_name.values())
    udadmin_models = [model for model in models if getattr(model, "app_name", "") == "udadmin"]
    demo_models = [model for model in models if getattr(model, "app_name", "") == "demo"]

    role_specs = [
        ("超级管理员角色", [perm.name for perm in all_model_perms]),
        ("全部模型管理员", [perm.name for perm in all_model_perms]),
        ("udadmin应用管理员", _perm_names_for_models(udadmin_models)),
        ("demo应用管理员", _perm_names_for_models(demo_models)),
        ("全模型只读", _perm_names_for_models(models, ("list", "read"))),
        ("全模型新增编辑", _perm_names_for_models(models, ("create", "update"))),
        ("全模型删除", _perm_names_for_models(models, ("delete",))),
        (
            "demo明细维护",
            _perm_names_for_models([demo_md.DetailModel])
            + _perm_names_for_models([demo_md.ForeignKeyModel, demo_md.RelationModel], ("list", "read")),
        ),
    ]

    roles = []
    for index, (name, perm_names) in enumerate(role_specs, start=1):
        role = md.Role(
            id=index,
            name=name,
            extra={"description": f"测试角色: {name}", "level": index},
        )
        role.permissions = [permissions_by_name[name] for name in perm_names if name in permissions_by_name]
        roles.append(role)
    session.add_all(roles)
    await session.flush()
    return roles


async def _create_users(session, roles: list[md.Role], permissions_by_name: dict[str, md.Permission]):
    user_specs = [
        ("admin", "admin", "管理员", True, [roles[0]], []),
        ("test_user", "123456", "普通只读用户", False, [roles[4]], []),
        ("all_model_user", "123456", "全部模型用户", False, [roles[1]], []),
        ("udadmin_user", "123456", "后台管理用户", False, [roles[2]], []),
        ("demo_user", "123456", "示例应用用户", False, [roles[3]], []),
        ("editor_user", "123456", "新增编辑用户", False, [roles[5]], []),
        ("delete_user", "123456", "删除权限用户", False, [roles[6]], []),
        ("detail_user", "123456", "明细维护用户", False, [roles[7]], []),
        (
            "direct_user",
            "123456",
            "直接授权用户",
            False,
            [],
            [
                "udadmin:User:list",
                "udadmin:User:read",
                "demo:DetailModel:list",
                "demo:DetailModel:read",
                "demo:DetailModel:update",
            ],
        ),
        ("empty_user", "123456", "无权限用户", False, [], []),
    ]

    users = []
    for index, (username, password, cn_name, is_superuser, user_roles, direct_perms) in enumerate(user_specs, start=1):
        user = md.User(
            id=index,
            username=username,
            password=pc.hash(password),
            is_superuser=is_superuser,
            cn_name=cn_name,
            gender="男" if index % 2 else "女",
            is_active=True,
            is_delete=False,
            last_login=_rand_datetime() if index <= 5 else None,
        )
        user.roles = user_roles
        user.permissions = [permissions_by_name[name] for name in direct_perms if name in permissions_by_name]
        users.append(user)
    session.add_all(users)
    await session.flush()
    return users


async def _create_udadmin_data(session, users: list[md.User]):
    config_types = [
        md.ConfigType(id=1, name="system", extra={"description": "系统配置"}),
        md.ConfigType(id=2, name="security", extra={"description": "安全配置"}),
        md.ConfigType(id=3, name="ui", extra={"description": "界面配置"}),
        md.ConfigType(id=4, name="storage", extra={"description": "存储配置"}),
        md.ConfigType(id=5, name="integration", extra={"description": "集成配置"}),
    ]
    session.add_all(config_types)

    configs = []
    for index in range(1, 21):
        config_type = config_types[(index - 1) % len(config_types)]
        configs.append(
            md.Config(
                id=index,
                name=f"config_{index:02d}",
                config_type=config_type,
                params={
                    "value": f"value_{index:02d}",
                    "enabled": index % 2 == 0,
                    "priority": index,
                },
                extra={"label": f"测试配置{index:02d}", "scope": config_type.name},
            )
        )
    session.add_all(configs)

    actions = ["login", "create", "read", "update", "delete", "export", "permission_check"]
    records = []
    for index in range(1, 51):
        user = users[(index - 1) % len(users)]
        action = actions[index % len(actions)]
        records.append(
            md.Record(
                id=index,
                name=f"测试操作{index:02d}",
                info={
                    "action": action,
                    "result": random.choice(["success", "failed", "partial"]),
                    "ip": f"192.168.1.{index % 255}",
                    "target": random.choice(["User", "Role", "Permission", "DetailModel"]),
                },
                extra={"duration_ms": random.randint(10, 3000), "seed": True},
                user=user,
                operate_time=_rand_datetime(),
            )
        )
    session.add_all(records)
    await session.flush()
    return config_types, configs, records


async def _create_demo_data(session):
    products = [
        "笔记本电脑",
        "无线鼠标",
        "机械键盘",
        "显示器",
        "耳机",
        "手机",
        "平板",
        "路由器",
        "移动硬盘",
        "摄像头",
    ]
    tags_pool = ["热销", "新品", "促销", "推荐", "限量", "预售", "清仓", "旗舰", "特价", "样品"]
    categories = ["电子产品", "办公用品", "网络设备", "外设配件", "存储设备", "音视频设备", "智能穿戴", "配件"]

    fk_objs = []
    for index in range(1, 26):
        fk_obj = demo_md.ForeignKeyModel(
            id=index,
            name=f"供应商{index:02d}",
            code=f"SUP-{index:03d}",
            description=f"覆盖一对多测试的供应商 {index:02d}",
        )
        session.add(fk_obj)
        fk_objs.append(fk_obj)

    relation_objs = []
    relation_categories = ["一对一", "多对多", "标签", "分组", "空闲关系"]
    for index in range(1, 121):
        relation_obj = demo_md.RelationModel(
            id=index,
            name=f"关系对象{index:03d}",
            category=relation_categories[index % len(relation_categories)],
            remark=f"覆盖关系字段测试的对象 {index:03d}",
        )
        session.add(relation_obj)
        relation_objs.append(relation_obj)

    await session.flush()

    detail_objs = []
    enum_values = ["option1", "option2", "option3"]
    decimal_values = [Decimal("0.00"), Decimal("0.01"), Decimal("999999.99")]
    int_values = [0, -1, 1, 10000, 2147483647]
    small_values = [0, 1, 32767]
    float_values = [0.0, 59.99, 100.0]

    for index in range(1, 501):
        product = random.choice(products)
        category = categories[index % len(categories)]
        char_enum = enum_values[index % len(enum_values)]
        int_choice = int_values[index % len(int_values)] if index <= len(int_values) else random.randint(1, 10000)
        decimal_choice = decimal_values[index % len(decimal_values)] if index <= 30 else Decimal(f"{random.randint(10, 9999)}.{random.randint(0, 99):02d}")
        score = float_values[index % len(float_values)] if index <= 30 else round(random.uniform(1, 99), 2)

        detail = demo_md.DetailModel(
            id=index,
            big_int_field=random.choice([0, 9223372036854775807, random.randint(100000, 999999999)]),
            binary_field=None if index % 7 else f"binary-{index}".encode("utf-8"),
            boolean_field=[True, False, None][index % 3],
            char_enum_field=char_enum,
            char_field=f"{category}-{product}-{index:04d}",
            date_field=date(2020, 1, 1) if index == 1 else _rand_date(),
            date_time_field=_rand_datetime(),
            decimal_field=decimal_choice,
            float_field=score,
            int_enum_field=(index % 3) + 1,
            int_field=int_choice,
            json_field={
                "product": product,
                "category": category,
                "status": char_enum,
                "tags": random.sample(tags_pool, k=random.randint(1, 5)),
                "warehouse": f"WH-{(index % 12) + 1:02d}",
                "meta": {"created_by": (index % 10) + 1, "batch": index // 50},
            },
            small_integer_field=small_values[index % len(small_values)] if index <= 30 else random.randint(1, 30000),
            text_field=(
                f"{product}用于{random.choice(['办公', '游戏', '设计', '开发', '教育', '家庭'])}场景，"
                f"分类为{category}，库存基准{int_choice}，评分{score}。"
            ),
            time_field=time(index % 24, index % 60, (index * 7) % 60),
            time_delta_field=random.choice([0, 60, 3600, 86400, 86400 * 30]),
            uuid_field=str(uuid.uuid4()),
            foreign_model=None if index % 11 == 0 else fk_objs[index % len(fk_objs)],
            one_to_one_relation=relation_objs[index - 1] if index <= len(relation_objs) else None,
        )

        if index % 10 == 0:
            detail.many_to_many_relations = []
        else:
            detail.many_to_many_relations = random.sample(relation_objs, k=random.randint(1, 6))
        session.add(detail)
        detail_objs.append(detail)

    await session.flush()
    return fk_objs, relation_objs, detail_objs


async def seed_test_data():
    random.seed(20260527)
    async with async_session_factory() as session:
        permissions_by_name, models = await _create_permissions(session)
        roles = await _create_roles(session, permissions_by_name, models)
        users = await _create_users(session, roles, permissions_by_name)
        config_types, configs, records = await _create_udadmin_data(session, users)
        fk_objs, relation_objs, detail_objs = await _create_demo_data(session)
        await session.commit()

    print("✓ Seed data committed")
    return {
        "models": len(models),
        "permissions": len(permissions_by_name),
        "roles": len(roles),
        "users": len(users),
        "config_types": len(config_types),
        "configs": len(configs),
        "records": len(records),
        "foreign_key_models": len(fk_objs),
        "relation_models": len(relation_objs),
        "detail_models": len(detail_objs),
    }


async def verify_seed_data() -> dict[str, int]:
    async with async_session_factory() as session:
        counts = {
            "users": await session.scalar(select(func.count()).select_from(md.User)),
            "roles": await session.scalar(select(func.count()).select_from(md.Role)),
            "permissions": await session.scalar(select(func.count()).select_from(md.Permission)),
            "config_types": await session.scalar(select(func.count()).select_from(md.ConfigType)),
            "configs": await session.scalar(select(func.count()).select_from(md.Config)),
            "records": await session.scalar(select(func.count()).select_from(md.Record)),
            "foreign_key_models": await session.scalar(select(func.count()).select_from(demo_md.ForeignKeyModel)),
            "relation_models": await session.scalar(select(func.count()).select_from(demo_md.RelationModel)),
            "detail_models": await session.scalar(select(func.count()).select_from(demo_md.DetailModel)),
            "detail_relations": await session.scalar(select(func.count()).select_from(demo_md.detail_relation)),
        }
    return {key: int(value or 0) for key, value in counts.items()}


async def async_main():
    reset_sqlite_database()
    run_alembic_migrations()
    expected = await seed_test_data()
    counts = await verify_seed_data()

    print("\n" + "=" * 80)
    print(click.style("数据初始化完成！", bold=True, fg=(0, 255, 0)))
    print("=" * 80)
    print("登录账号:")
    print("  admin/admin")
    print("  test_user/123456")
    print("  empty_user/123456")
    print("写入统计:")
    for key, value in counts.items():
        print(f"  {key}: {value}")
    print("预期核心数据:")
    for key, value in expected.items():
        print(f"  {key}: {value}")
    print("=" * 80)


def main():
    try:
        asyncio.run(async_main())
    except Exception as exc:
        print(traceback.format_exc())
        raise exc
    finally:
        asyncio.run(engine.dispose())


if __name__ == "__main__":
    main()
