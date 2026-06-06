import click
from fastapi import FastAPI, APIRouter, Depends, Path
from enum import Enum
from sqlalchemy import inspect as sa_inspect, select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Optional, Union, cast
from math import ceil
import re
from datetime import date, datetime, time
from copy import deepcopy
from .class_tools import SingletonMeta
from . import orm_tools as ot
from . import resp_code as rc
from . import auth
from . import pmodels as pm
from . import ui_tools
from . import doc
from .model_tools import model_perms, get_model_info
from db.sa import get_db
from . import http_resp as hr
from .i18n import localize_app_info, localize_field_info, localize_model_display, t
from .. import models as md
from config import settings
from pydantic import create_model as pyd_create_model
from sqlalchemy.types import Date as SADate, DateTime as SADateTime, Time as SATime


def ok_msg() -> str:
    return t("common.ok")


class ModleRegister(metaclass=SingletonMeta):
    name: str = "ModleTools"
    models_info: dict = {}
    routes: dict = {}  # 记录route 是否添加了get_model_info方法
    registered_info = set()
    perm_type = "model"  # 模型的增删改查的权限类型名称

    async def clear_unique_fk_conflicts(self, db: AsyncSession, model, values: dict, current_pk=None):
        mapper = sa_inspect(model)
        pk_col = mapper.primary_key[0]
        for key, value in values.items():
            if value is None or key not in mapper.columns:
                continue
            column = mapper.columns[key]
            if not column.unique or not column.foreign_keys:
                continue
            stmt = select(model).where(getattr(model, key) == value)
            if current_pk is not None:
                stmt = stmt.where(pk_col != current_pk)
            result = await db.execute(stmt)
            for conflict_obj in result.scalars().all():
                setattr(conflict_obj, key, None)

    def coerce_db_values(self, model, values: dict) -> dict:
        mapper = sa_inspect(model)
        coerced_values = dict(values)
        for key, value in list(coerced_values.items()):
            if value is None or key not in mapper.columns:
                continue
            column_type = mapper.columns[key].type
            if isinstance(column_type, SATime) and isinstance(value, str):
                coerced_values[key] = time.fromisoformat(value.strip())
            elif isinstance(column_type, SADateTime) and isinstance(value, str):
                raw_value = value.strip().replace("Z", "+00:00")
                coerced_values[key] = datetime.fromisoformat(raw_value)
            elif isinstance(column_type, SADate) and isinstance(value, str):
                coerced_values[key] = date.fromisoformat(value.strip().split("T")[0].split(" ")[0])
        return coerced_values

    def create_item_generator(self, model, info):
        # Build a dynamic Pydantic model from SQLAlchemy columns
        # mapper = _sa_inspect(model)
        field_defs = {}
        for col in model.__table__.columns:
            if col.autoincrement and col.primary_key:
                continue  # skip auto PK
            py_type = col.type.python_type
            if col.nullable:
                py_type = Optional[py_type]
            field_defs[col.name] = (
                py_type,
                ... if not col.nullable and col.default is None else None,
            )
        pmodel = pyd_create_model(f"In{model.__name__}", **field_defs)

        @auth.permission_required(
            "model", f"{info['app']}:{info['model_name']}:{model_perms['create']}"
        )
        async def create_item(
            user: Annotated[str, Depends(auth.get_user)],
            db: AsyncSession = Depends(get_db),
            item: pmodel = None,  # type: ignore[valid-type]
        ):
            rd = info["ui"].check_readonly(item.model_dump(exclude_unset=True))
            if rd:
                raise Exception(t("crud.readonly_field_cannot_set", fields=rd))
            for k, v in info["ui"].db_value_converters.items():
                setattr(item, k, v(getattr(item, k)))
            values = item.model_dump(exclude_unset=True)
            values = self.coerce_db_values(model, values)
            await self.clear_unique_fk_conflicts(db, model, values)
            obj = model(**values)
            db.add(obj)
            await db.flush()
            await db.refresh(obj)
            return {"code": rc.success, "data": ot._obj_to_dict(obj), "msg": ok_msg()}

        return create_item

    def delete_item_generator(self, model, info):
        pk_name = sa_inspect(model).primary_key[0].name

        @auth.permission_required(
            "model", f"{info['app']}:{info['model_name']}:{model_perms['delete']}"
        )
        async def delete_item(
            user: Annotated[str, Depends(auth.get_user)],
            db: AsyncSession = Depends(get_db),
            id: int = Path(title="The ID of the item"),
        ):
            stmt = select(model).where(getattr(model, pk_name) == id)
            result = await db.execute(stmt)
            obj = result.scalar_one_or_none()
            if obj:
                await db.delete(obj)
                await db.flush()
                return {"code": rc.success, "msg": ok_msg(), "data": 1}
            return {"code": rc.success, "msg": ok_msg(), "data": 0}

        return delete_item

    def update_item_generator(self, model, info):
        pk_name = sa_inspect(model).primary_key[0].name

        @auth.permission_required(
            "model", f"{info['app']}:{info['model_name']}:{model_perms['update']}"
        )
        async def update_item(
            user: Annotated[str, Depends(auth.get_user)],
            db: AsyncSession = Depends(get_db),
            item: dict = {},
            id: int = Path(title="The ID of the item"),
        ):
            if not item:
                raise Exception(t("crud.update_field_empty"))
            rd = info["ui"].check_readonly(item)
            if rd:
                raise Exception(t("crud.readonly_field_cannot_set", fields=rd))
            for k, v in info["ui"].db_value_converters.items():
                if k in item:
                    item[k] = v(item[k])
            item = self.coerce_db_values(model, item)
            obj = await db.get(model, id)
            if not obj:
                return {
                    "code": rc.success_request,
                    "msg": t("error.object_not_found"),
                    "data": 0,
                    }
            await self.clear_unique_fk_conflicts(db, model, item, current_pk=id)
            for k, v in item.items():
                if hasattr(obj, k):
                    setattr(obj, k, v)
            await db.flush()
            return {"code": rc.success, "msg": ok_msg(), "data": 1}

        return update_item

    def read_item_generator(self, model, info):
        pk_name = sa_inspect(model).primary_key[0].name

        @auth.permission_required(
            "model", f"{info['app']}:{info['model_name']}:{model_perms['read']}"
        )
        async def get_item(
            user: Annotated[str, Depends(auth.get_user)],
            db: AsyncSession = Depends(get_db),
            id: int = Path(title="The ID of the item"),
        ):
            stmt = select(model).where(getattr(model, pk_name) == id)
            result = await db.execute(stmt)
            obj = result.scalar_one_or_none()
            if not obj:
                raise Exception(t("crud.model_id_not_in_db", model=model.__name__, id=id))
            obj_dict = ot._obj_to_dict(obj)
            list_display = info.get("ui").list_display
            if "*" not in list_display:
                obj_dict = {k: v for k, v in obj_dict.items() if k in list_display}
            return {"code": rc.success, "data": obj_dict, "msg": ok_msg()}

        return get_item

    def get_item_list_generator(self, model, info):
        @auth.permission_required(
            "model", f"{info['app']}:{info['model_name']}:{model_perms['list']}"
        )
        async def get_item_list(
            user: Annotated[str, Depends(auth.get_user)],
            db: AsyncSession = Depends(get_db),
            pb: pm.PaginatorBody = pm.PaginatorBody(),
        ):
            objs, total, page_cnt = await ot.get_model_objs(
                pb, model, fields=info.get("ui").list_display, session=db
            )
            return {
                "code": rc.success,
                "data": objs,
                "msg": ok_msg(),
                "extra": {
                    "paginator": {
                        "curr_page": pb.curr_page,
                        "page_size": pb.page_size,
                        "total": total,
                        "page_cnt": page_cnt,
                    }
                },
            }

        return get_item_list

    def relation_manage_generator(self, model, info):
        req_schema = ot.gen_rel_fields_enum_class(model)
        mapper = sa_inspect(model)
        pk_name = mapper.primary_key[0].name
        rel_names = [r.key for r in mapper.relationships]

        @auth.permission_required(
            "model", f"{info['app']}:{info['model_name']}:{model_perms['read']}"
        )
        async def rel_manage(
            user: Annotated[str, Depends(auth.get_user)],
            db: AsyncSession = Depends(get_db),
            reqb: req_schema = None,  # type: ignore
        ):
            action = reqb.action.value
            id = reqb.id
            paginator = reqb.paginator
            field_name = reqb.field_name.value
            m2m_ids = reqb.m2m_ids or {"add": [], "del": []}
            label = reqb.label

            assert (
                field_name in rel_names
            ), t("crud.relationship_field_not_found", field=field_name)
            rel = mapper.relationships[field_name]
            related_model = rel.mapper.class_
            rel_is_m2m = rel.secondary is not None
            # Detect BackwardFKRelation
            has_local_fk = any(col.foreign_keys for col in rel.local_columns)
            rel_is_backward_fk = rel.uselist and not rel_is_m2m and not has_local_fk
            # Find the remote FK column on the related model for backward FK
            remote_fk_col = None
            if rel_is_backward_fk:
                for col in related_model.__table__.columns:
                    if col.foreign_keys:
                        for fk in col.foreign_keys:
                            if fk.column.table == model.__table__:
                                remote_fk_col = col.name
                                break
            related_objs = None
            if id:
                stmt = (
                    select(model)
                    .where(getattr(model, pk_name) == id)
                    .options(selectinload(getattr(model, field_name)))
                )
                result = await db.execute(stmt)
                obj = result.scalar_one_or_none()
                if not obj:
                    raise Exception(t("crud.model_id_not_found", model=model.__name__, id=id))
                related_objs = getattr(obj, field_name)

            if action == "list":
                assert id, t("crud.id_required_for_action", action="list")
                assert paginator, t("crud.paginator_required_for_action", action="list")
                objs, total, page_cnt = await ot.get_relation_objs(
                    paginator,
                    related_model,
                    fields=["*"],
                    related_objs=related_objs,
                    label=label,
                    session=db,
                )
                return {
                    "code": rc.success,
                    "data": objs,
                    "msg": ok_msg(),
                    "extra": {
                        "paginator": {
                            "curr_page": paginator.curr_page,
                            "page_size": paginator.page_size,
                            "total": total,
                            "page_cnt": page_cnt,
                        },
                        "related_model": related_model.__name__,
                        "app_name": getattr(related_model, "app_name", "") or "",
                    },
                }
            elif action == "manage":
                assert id, t("crud.id_required_for_action", action="manage")
                assert m2m_ids, t("crud.m2m_ids_required_for_action", action="manage")
                if rel_is_m2m:
                    # M2M: add/remove from association table
                    related_pk_name = sa_inspect(related_model).primary_key[0].name
                    current_related_by_id = {
                        str(getattr(item, related_pk_name)): item for item in (related_objs or [])
                    }
                    if m2m_ids.get("add") and related_objs is not None:
                        add_ids = [
                            item_id
                            for item_id in m2m_ids["add"]
                            if str(item_id) not in current_related_by_id
                        ]
                        if not add_ids:
                            add_objs = []
                        else:
                            add_stmt = select(related_model).where(
                                getattr(related_model, related_pk_name).in_(add_ids)
                            )
                            add_result = await db.execute(add_stmt)
                            add_objs = add_result.scalars().all()
                        for ao in add_objs:
                            related_objs.append(ao)
                            current_related_by_id[str(getattr(ao, related_pk_name))] = ao
                    if m2m_ids.get("del") and related_objs is not None:
                        del_ids = [
                            item_id
                            for item_id in m2m_ids["del"]
                            if str(item_id) in current_related_by_id
                        ]
                        if not del_ids:
                            del_objs = []
                        else:
                            del_stmt = select(related_model).where(
                                getattr(related_model, related_pk_name).in_(del_ids)
                            )
                            del_result = await db.execute(del_stmt)
                            del_objs = del_result.scalars().all()
                        for do in del_objs:
                            related_objs.remove(do)
                            current_related_by_id.pop(str(getattr(do, related_pk_name)), None)
                elif rel_is_backward_fk and remote_fk_col:
                    # BackwardFK: update the FK column on the related model
                    if m2m_ids.get("add"):
                        add_stmt = select(related_model).where(
                            related_model.id.in_(m2m_ids["add"])
                        )
                        add_result = await db.execute(add_stmt)
                        add_objs = add_result.scalars().all()
                        for ao in add_objs:
                            setattr(ao, remote_fk_col, id)
                    if m2m_ids.get("del"):
                        del_stmt = select(related_model).where(
                            related_model.id.in_(m2m_ids["del"])
                        )
                        del_result = await db.execute(del_stmt)
                        del_objs = del_result.scalars().all()
                        for do in del_objs:
                            setattr(do, remote_fk_col, None)
                await db.flush()
                return {"code": rc.success, "msg": t("crud.manage_done")}
            elif action == "query":
                assert paginator, t("crud.paginator_required_for_action", action="query")
                objs, total, page_cnt = await ot.get_model_objs(
                    paginator, related_model, fields=["*"], label=label, session=db
                )
                return {
                    "code": rc.success,
                    "data": objs,
                    "msg": ok_msg(),
                    "extra": {
                        "paginator": {
                            "curr_page": paginator.curr_page,
                            "page_size": paginator.page_size,
                            "total": total,
                            "page_cnt": page_cnt,
                        },
                        "related_model": related_model.__name__,
                        "app_name": getattr(related_model, "app_name", "") or "",
                    },
                }
            else:
                raise Exception(t("crud.action_not_supported", action=action))

        return rel_manage

    def get_all_models_info_generator(self):
        async def get_all_models_info(
            user=Depends(auth.get_user),
        ):
            allow_models = await self.get_allow_models(user)
            all_models = {}
            app_info = settings.APP_INFO
            for k,v in self.models_info.items():
                if k in allow_models:
                    Meta = getattr(v["model"], "Meta", None)
                    ud_app = getattr(Meta, "ud_app", None) or v["app"]
                    app_display_info = localize_app_info(ud_app, app_info.get(ud_app, {}))
                    model_menu_name, table_description = localize_model_display(
                        v["model_name"],
                        getattr(Meta, "menu_name", v["model_name"]),
                        getattr(Meta, "table_description", v["model_name"]),
                    )
                    all_models[k] = {
                        "model_menu_name": model_menu_name,
                        "app": v["app"],
                        "ud_app": getattr(Meta, "ud_app", v["app"]) or v["app"],
                        "tb_name": getattr(v["model"], "__tablename__", v["model_name"]),
                        "tb_description": table_description,
                        "model_icon": getattr(Meta, "icon", None),
                        "model_name": v["model_name"],
                        **app_display_info,
                    }
            return {"code": rc.success, "data": {"all_models": all_models}, "msg": ok_msg()}

        return get_all_models_info

    def get_allow_model_info_generator(self):
        async def get_allow_model_info(
            user: Annotated[md.User, Depends(auth.get_user)],
            req: pm.AllowModel,
        ):
            union_name = req.model_name
            perms = await self.get_user_model_perms(user, union_name)
            perms_list: list[str] = [str(getattr(v, "name")) for v in perms]
            await self.check_model_register(union_name)
            await self.check_model_allow(user, union_name)
            if cast(bool, user.is_superuser):
                perms_list.extend(self.get_model_defined_action_permissions(union_name))
            perms_list = sorted(set(perms_list))
            keys = ["ui", "fileds_info"]
            allow_info = {
                k: v for k, v in self.models_info[union_name].items() if k in keys
            }
            ui_data = {
                key: value
                for key, value in vars(allow_info["ui"]).items()
                if not key.startswith("_")
            }
            ui_data["custom_actions"] = ui_tools.serialize_custom_actions(
                ui_data.get("custom_actions")
            )
            fields_info = {
                field_name: localize_field_info(field_name, deepcopy(field_info))
                for field_name, field_info in allow_info["fileds_info"].items()
            }
            return {
                "code": rc.success,
                "data": {
                    "allow_model": union_name,
                    "fields_info": fields_info,
                    "ui": ui_data,
                    "perms": perms_list,
                },
                "msg": ok_msg(),
            }

        return get_allow_model_info

    def get_filter_fields_distinct_values_generator(self):
        async def get_filter_fields_distinct_values(
            user=Depends(auth.get_user),
            db: AsyncSession = Depends(get_db),
            req: pm.FilterFieldsDistinctValues = pm.FilterFieldsDistinctValues(),
        ):
            union_name = req.app_model_name
            await self.check_model_register(union_name)
            await self.check_model_allow(user, union_name)
            if union_name not in self.models_info:
                raise Exception(t("crud.model_not_registered", model=union_name))
            model_info = self.models_info[union_name]
            model = model_info["model"]
            field = req.field_names
            if field not in sa_inspect(model).columns:
                raise Exception(
                    t("crud.filter_field_not_in_model", field=field, model=model.__name__)
                )
            pb = req.paginator
            where_clause = ot.build_sa_filter(pb.filters, model)
            # Count total distinct values
            count_stmt = select(func.count()).select_from(
                select(getattr(model, field)).distinct().where(where_clause).subquery()
            )
            total = (await db.execute(count_stmt)).scalar() or 0
            if total == 0:
                return {
                    "code": rc.success_request,
                    "data": {"values": [], "paginator": pb},
                    "msg": t("crud.no_data_with_filter", filters=pb.filters),
                }
            page_cnt = ceil(total / pb.page_size)
            if pb.curr_page > page_cnt:
                raise Exception(
                    t("crud.page_out_of_range", current_page=pb.curr_page, total_page_count=page_cnt)
                )
            # Query distinct values with pagination
            distinct_stmt = (
                select(getattr(model, field).distinct())
                .where(where_clause)
                .order_by(getattr(model, field))
                .offset((pb.curr_page - 1) * pb.page_size)
                .limit(pb.page_size)
            )
            result = await db.execute(distinct_stmt)
            distinct_values = [row[0] for row in result.all()]
            data = {
                "values": distinct_values,
                "paginator": {
                    "curr_page": pb.curr_page,
                    "page_size": pb.page_size,
                    "total": total,
                    "page_cnt": page_cnt,
                },
            }
            return {"code": rc.success, "data": data, "msg": ok_msg()}

        return get_filter_fields_distinct_values

    async def get_allow_models(self, user):
        if cast(bool, user.is_superuser):
            perms = list(self.models_info.keys())
        else:
            from apps.udadmin.models import Permission, PermissionType, Role
            from db.sa import async_session_factory

            async with async_session_factory() as session:
                # User direct permissions
                stmt = (
                    select(Permission.name)
                    .join(Permission.permission_type)
                    .where(PermissionType.name == self.perm_type)
                    .where(Permission.users.any(id=user.id))
                )
                result = await session.execute(stmt)
                user_perms = [row[0] for row in result.all()]
                # Role-based permissions
                stmt2 = (
                    select(Permission.name)
                    .join(Permission.permission_type)
                    .where(PermissionType.name == self.perm_type)
                    .where(Permission.roles.any(Role.users.any(id=user.id)))
                )
                result2 = await session.execute(stmt2)
                role_perms = [row[0] for row in result2.all()]
            perms = list(set(user_perms) | set(role_perms))
        return {
            match.group(0)
            for perm in perms
            if (match := re.search(r"([^:]+:[^:]+)", perm))
        }

    async def get_user_model_perms(self, user, union_name: str):
        from apps.udadmin.models import Permission, PermissionType, Role
        from db.sa import async_session_factory

        async with async_session_factory() as session:
            if cast(bool, user.is_superuser):
                stmt = (
                    select(Permission)
                    .join(Permission.permission_type)
                    .where(PermissionType.name == self.perm_type)
                    .where(Permission.name.startswith(f"{union_name}:"))
                )
                result = await session.execute(stmt)
                return list(result.scalars().all())
            else:
                stmt = (
                    select(Permission)
                    .join(Permission.permission_type)
                    .where(PermissionType.name == self.perm_type)
                    .where(Permission.users.any(id=user.id))
                    .where(Permission.name.startswith(f"{union_name}:"))
                )
                result = await session.execute(stmt)
                user_perms = list(result.scalars().all())
                stmt2 = (
                    select(Permission)
                    .join(Permission.permission_type)
                    .where(PermissionType.name == self.perm_type)
                    .where(Permission.roles.any(Role.users.any(id=user.id)))
                    .where(Permission.name.startswith(f"{union_name}:"))
                )
                result2 = await session.execute(stmt2)
                role_perms = list(result2.scalars().all())
                return list(set(user_perms) | set(role_perms))

    async def check_model_register(self, union_name: str):
        if union_name not in list(self.models_info.keys()):
            raise Exception(
                {
                    "code": 5010,
                    "msg": t("crud.model_not_registered", model=union_name),
                    "error": t("crud.model_not_registered", model=union_name),
                }
            )

    async def check_model_allow(self, user, union_name: str):
        allow_models = await self.get_allow_models(user)
        if union_name not in allow_models:
            raise Exception(
                {
                    "code": 5010,
                    "msg": t("auth.no_model_permission", username=user.username, model=union_name),
                    "error": t("auth.no_model_permission", username=user.username, model=union_name),
                }
            )
        return allow_models

    def get_model_info(self, model, ui_info=None):
        model_info = get_model_info(model, ui_info=ui_info)
        return model_info

    def get_model_defined_action_permissions(self, union_name: str) -> list[str]:
        model_info = self.models_info.get(union_name) or {}
        ui_info = model_info.get("ui")
        if not ui_info:
            return []
        app_name, model_name = union_name.split(":", 1)
        return ui_tools.get_custom_action_permissions(
            app_name, model_name, getattr(ui_info, "custom_actions", [])
        )

    def get_registered_model_permission_specs(self) -> list[dict]:
        specs = []
        for union_name, model_info in self.models_info.items():
            app_name = model_info["app"]
            model_name = model_info["model_name"]
            for action in model_perms.values():
                specs.append(
                    {
                        "name": f"{app_name}:{model_name}:{action}",
                        "extra": {"app": app_name, "model": model_name, "action": action},
                    }
                )
            for perm_name in self.get_model_defined_action_permissions(union_name):
                specs.append(
                    {
                        "name": perm_name,
                        "extra": {
                            "app": app_name,
                            "model": model_name,
                            "action": "custom_action",
                        },
                    }
                )
        unique_specs = {}
        for spec in specs:
            unique_specs[spec["name"]] = spec
        return list(unique_specs.values())

    async def sync_registered_model_permissions(self) -> list[str]:
        from apps.udadmin.models import Permission, PermissionType
        from db.sa import async_session_factory

        print(click.style("SYNC:     ", fg="cyan") + "registered model permissions sync started.")
        specs = self.get_registered_model_permission_specs()
        if not specs:
            print(
                click.style("SYNC:     ", fg="cyan")
                + "registered model permissions sync finished. checked=0 created=0"
            )
            return []

        async with async_session_factory() as session:
            stmt = select(PermissionType).where(PermissionType.name == self.perm_type)
            result = await session.execute(stmt)
            perm_type = result.scalar_one_or_none()
            if not perm_type:
                perm_type = PermissionType(
                    name=self.perm_type,
                    extra={"description": "Model-level permissions"},
                )
                session.add(perm_type)
                await session.flush()

            names = [spec["name"] for spec in specs]
            stmt = select(Permission.name).where(Permission.name.in_(names))
            result = await session.execute(stmt)
            existing_names = set(result.scalars().all())
            missing_specs = [spec for spec in specs if spec["name"] not in existing_names]
            for spec in missing_specs:
                session.add(
                    Permission(
                        name=spec["name"],
                        permission_type_id=perm_type.id,
                        extra=spec["extra"],
                    )
                )
            await session.commit()
            created_names = [spec["name"] for spec in missing_specs]
            if created_names:
                print(
                    click.style("SYNC:     ", fg="green")
                    + f"created model permissions: {created_names}"
                )
            print(
                click.style("SYNC:     ", fg="cyan")
                + f"registered model permissions sync finished. checked={len(specs)} created={len(created_names)}"
            )
            return created_names

    def register(
        self,
        router: FastAPI | APIRouter,
        model,
        doc_tags: list[Union[str, Enum]] = ["Registered Model Api"],
        crudl: str = "crudl",
        fetch: bool = True,
        prefix: str = "models",
        ui_info: Optional[ui_tools.UiInfo] = None,
    ):
        app_name = getattr(model, "app_name", "") or model.__tablename__.split("_")[0]
        model_name = model.__name__
        union_key = f"{app_name}:{model_name}"
        router_id = id(router)
        model_id = id(model)
        # 获取该路由所有注册的模型信息的接口,如果router 已经注册过这个路由了就不需要再次注册了
        info_tag: list[Union[str, Enum]] = ["Models Info Api"]
        if router_id not in self.routes.keys():
            router.add_api_route(
                "/get_all_models_info",
                self.get_all_models_info_generator(),
                methods=["get"],
                tags=info_tag,
                responses=hr.general_resps,
                description="获取所有已经注册的有权限的模型的信息。",
            )
            router.add_api_route(
                "/get_allow_model_info",
                self.get_allow_model_info_generator(),
                methods=["post"],
                tags=info_tag,
                responses=hr.general_resps,
                description="获取所有已经注册的模型的信息。",
            )
            router.add_api_route(
                "/get_filter_fields_distinct_values",
                self.get_filter_fields_distinct_values_generator(),
                methods=["post"],
                tags=info_tag,
                responses=hr.general_resps,
                description=doc.field_distinct.format(model_name=model_name),
            )
            # 记录router已经注册信息路由
            self.routes[router_id] = router

        register_id = f"{router_id}#{model_id}"
        if register_id in self.registered_info:
            print(click.style("WARNIBG:  ", fg="yellow") + f"model:<{model_name}> is already registered in router:<{router}>.")
            return None
        else:
            self.registered_info.add(register_id)

        route_model_name = model_name
        ui_info = ui_info or ui_tools.UiInfo(model=model)
        if union_key in self.models_info.keys():
            model_info = self.models_info.get(union_key)
        else:
            model_info = self.get_model_info(model, ui_info=ui_info)
            model_info["ui"] = ui_info
            model_info["url"] = f"{prefix}/{route_model_name}"
            self.models_info[f"{app_name}:{model_name}"] = model_info

        prefix = (prefix if prefix.startswith("/") else f"/{prefix}") if prefix else ""
        pk_name = sa_inspect(model).primary_key[0].name

        if "c" in crudl:
            router.add_api_route(
                f"{prefix}/{route_model_name}",
                self.create_item_generator(model, model_info),
                methods=["post"],
                tags=doc_tags,
                responses=hr.general_resps,
                description=model_info["api_docs"]["create_item"] if model_info else "",
            )
        if "d" in crudl:
            router.add_api_route(
                f"{prefix}/{route_model_name}/{{{pk_name}}}",
                self.delete_item_generator(model, model_info),
                methods=["delete"],
                tags=doc_tags,
                responses=hr.general_resps,
                description=model_info["api_docs"]["delete_item"] if model_info else "",
            )
        if "u" in crudl:
            router.add_api_route(
                f"{prefix}/{route_model_name}/{{{pk_name}}}",
                self.update_item_generator(model, model_info),
                methods=["put"],
                tags=doc_tags,
                responses=hr.general_resps,
                description=model_info["api_docs"]["update_item"] if model_info else "",
            )
        if "r" in crudl:
            router.add_api_route(
                f"{prefix}/{route_model_name}/{{{pk_name}}}",
                self.read_item_generator(model, model_info),
                methods=["get"],
                tags=doc_tags,
                responses=hr.general_resps,
                description=model_info["api_docs"]["read_item"] if model_info else "",
            )
        if "l" in crudl:
            router.add_api_route(
                f"{prefix}/{route_model_name}/list",
                self.get_item_list_generator(model, model_info),
                methods=["post"],
                tags=doc_tags,
                responses=hr.general_resps,
                description=(
                    model_info["api_docs"]["get_item_list"] if model_info else ""
                ),
            )
        # Relationship management
        mapper = sa_inspect(model)
        rel_fields = list(mapper.relationships.keys())
        if fetch and rel_fields:
            router.add_api_route(
                f"{prefix}/{route_model_name}/rel_manage",
                self.relation_manage_generator(model, model_info),
                methods=["post"],
                tags=doc_tags,
                responses=hr.general_resps,
                description=(
                    model_info["api_docs"]["rel_manage"] if model_info else ""
                ),
            )


mr = ModleRegister()

if __name__ == "__main__":
    pass
