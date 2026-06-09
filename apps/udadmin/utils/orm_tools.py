"""ORM tools using SQLAlchemy async."""
import json
from datetime import date, datetime, time
from typing import Optional, Union, List
from pydantic import PositiveInt, Field
from pydantic.main import create_model
from sqlalchemy import select, func, delete as sa_delete, inspect as sa_inspect, true
from sqlalchemy.types import (
    JSON,
    Date as SADate,
    DateTime as SADateTime,
    LargeBinary as SALargeBinary,
    Time as SATime,
)
from sqlalchemy.sql.expression import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from math import ceil
from . import pmodels as pm
from . import enums as es
from .i18n import t
from config import settings
from .model_base import get_session_factory

async_session_factory = get_session_factory()

IS_SQLITE = settings.DATABASE_URL.startswith("sqlite")


def build_sa_filter(filters, model):
    valid_fields = set(model.__table__.columns.keys())

    def coerce_filter_value(col, value):
        column_type = getattr(col, "type", None)
        if value is None:
            return value
        if isinstance(value, list):
            return [coerce_filter_value(col, item) for item in value]
        if isinstance(column_type, SALargeBinary):
            if isinstance(value, bytes):
                return value
            if isinstance(value, str):
                return value.encode()
            return value
        if not isinstance(value, str):
            return value
        value = value.strip()
        if isinstance(column_type, SATime):
            return time.fromisoformat(value)
        if isinstance(column_type, SADateTime):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        if isinstance(column_type, SADate):
            return date.fromisoformat(value.split("T")[0].split(" ")[0])
        return value

    def build_condition(condition):
        c = condition
        if c["field"] not in valid_fields:
            raise Exception(t("crud.filter_field_not_in_model", field=c["field"], model=model.__name__))
        col = getattr(model, c["field"])
        column_type = getattr(col, "type", None)
        symbol = c["symbol"]
        value = c["value"] if symbol in ["contains", "icontains"] else coerce_filter_value(col, c["value"])
        if isinstance(column_type, SALargeBinary) and symbol in [
            "contains",
            "icontains",
            "startswith",
            "endswith",
        ]:
            return col == coerce_filter_value(col, c["value"])
        if symbol == "contains":
            return col.contains(value)
        elif symbol == "icontains":
            if IS_SQLITE and isinstance(column_type, JSON):
                escaped_value = json.dumps(value, ensure_ascii=True)[1:-1]
                return or_(col.ilike(f"%{value}%"), col.ilike(f"%{escaped_value}%"))
            return col.ilike(f"%{value}%")
        elif symbol == "startswith":
            return col.startswith(value)
        elif symbol == "endswith":
            return col.endswith(value)
        elif symbol == "lt":
            return col < value
        elif symbol == "lte":
            return col <= value
        elif symbol == "gt":
            return col > value
        elif symbol == "gte":
            return col >= value
        elif symbol == "in":
            return col.in_(value if isinstance(value, list) else [value])
        elif symbol == "not_in":
            return col.notin_(value if isinstance(value, list) else [value])
        elif symbol == "isnull":
            return col.is_(None) if value else col.isnot(None)
        elif symbol == "not":
            return col != value
        elif symbol == "eq":
            return col == value
        elif symbol == "range":
            return col.between(value[0], value[1])
        else:
            raise Exception(t("crud.filter_symbol_not_configured", symbol=symbol))

    def process_filter_group(filter_group):
        if isinstance(filter_group, list):
            if len(filter_group) == 0:
                return and_(true())
            elif len(filter_group) == 1:
                return process_filter_group(filter_group[0])
            else:
                logic = filter_group[0]
                if logic not in ["and", "or"]:
                    raise Exception(t("crud.invalid_logic_operator", logic=logic))
                clauses = [process_filter_group(c) for c in filter_group[1:]]
                if logic == "and":
                    return and_(*clauses)
                else:
                    return or_(*clauses)
        else:
            return build_condition(filter_group)

    if not filters:
        return and_(true())
    return process_filter_group(filters)


async def get_model_objs(pb, model, fields=["*"], label=False, session=None):
    if session is None:
        async with async_session_factory() as session:
            return await _get_model_objs_inner(session, pb, model, fields, label)
    return await _get_model_objs_inner(session, pb, model, fields, label)


async def _get_model_objs_inner(session, pb, model, fields, label):
    mapper = sa_inspect(model)
    rel_names = {rel.key for rel in mapper.relationships}
    where_clause = build_sa_filter(pb.filters, model)
    count_stmt = select(func.count()).select_from(model).where(where_clause)
    total = (await session.execute(count_stmt)).scalar() or 0
    if total == 0:
        return [], 0, 0
    page_cnt = ceil(total / pb.page_size)
    if pb.curr_page > page_cnt:
        raise Exception(t("crud.page_out_of_range", current_page=pb.curr_page, total_page_count=page_cnt))
    stmt = select(model).where(where_clause)
    load_rel_names = rel_names if "*" in fields else rel_names.intersection(fields)
    for rel_name in load_rel_names:
        stmt = stmt.options(selectinload(getattr(model, rel_name)))
    if pb.order_by:
        for ob in pb.order_by:
            if ob.startswith("-"):
                stmt = stmt.order_by(getattr(model, ob[1:]).desc())
            else:
                stmt = stmt.order_by(getattr(model, ob))
    stmt = stmt.offset((pb.curr_page - 1) * pb.page_size).limit(pb.page_size)
    result = await session.execute(stmt)
    objs = result.scalars().all()
    if "*" in fields:
        data = [_obj_to_dict(o) for o in objs]
    else:
        data = [_obj_to_dict(o, fields) for o in objs]
    if label:
        data = [{"label": str(o), "value": d} for o, d in zip(objs, data)]
    return data, total, page_cnt


async def get_relation_objs(pb, related_model, fields=["*"], related_objs=None, label=False, session=None):
    if related_objs is None:
        return [], 0, 0
    if session is None:
        async with async_session_factory() as session:
            return await _get_relation_objs_inner(session, pb, related_model, fields, related_objs, label)
    return await _get_relation_objs_inner(session, pb, related_model, fields, related_objs, label)


async def _get_relation_objs_inner(session, pb, related_model, fields, related_objs, label):
    mapper = sa_inspect(related_model)
    rel_names = {rel.key for rel in mapper.relationships}
    where_clause = build_sa_filter(pb.filters, related_model)
    if isinstance(related_objs, list):
        related_ids = [o.id for o in related_objs]
    else:
        related_ids = [related_objs.id] if related_objs else []
    if not related_ids:
        return [], 0, 0
    count_stmt = select(func.count()).select_from(related_model).where(
        and_(related_model.id.in_(related_ids), where_clause)
    )
    total = (await session.execute(count_stmt)).scalar() or 0
    if total == 0:
        return [], 0, 0
    page_cnt = ceil(total / pb.page_size)
    if pb.curr_page > page_cnt:
        raise Exception(t("crud.page_out_of_range", current_page=pb.curr_page, total_page_count=page_cnt))
    stmt = select(related_model).where(
        and_(related_model.id.in_(related_ids), where_clause)
    )
    load_rel_names = rel_names if "*" in fields else rel_names.intersection(fields)
    for rel_name in load_rel_names:
        stmt = stmt.options(selectinload(getattr(related_model, rel_name)))
    if pb.order_by:
        for ob in pb.order_by:
            if ob.startswith("-"):
                stmt = stmt.order_by(getattr(related_model, ob[1:]).desc())
            else:
                stmt = stmt.order_by(getattr(related_model, ob))
    stmt = stmt.offset((pb.curr_page - 1) * pb.page_size).limit(pb.page_size)
    result = await session.execute(stmt)
    objs = result.scalars().all()
    if "*" in fields:
        data = [_obj_to_dict(o) for o in objs]
    else:
        data = [_obj_to_dict(o, fields) for o in objs]
    if label:
        if isinstance(data, list):
            data = [{"label": str(o), "value": d} for o, d in zip(objs, data)]
        elif isinstance(data, dict):
            data = [{"label": str(objs[0]) if objs else "", "value": data}]
    else:
        if not isinstance(data, list):
            data = [data] if data else []
    return data, total, page_cnt


def gen_rel_fields_enum_class(model):
    mapper = sa_inspect(model)
    rel_fields = list(mapper.relationships.keys())
    class_prefix = f"{model.__name__.capitalize()}"
    enum_dict = {i: i for i in rel_fields}
    f_enum_cls_name = f"{class_prefix}RelFieldEnum"
    f_manage_cls_name = f"{class_prefix}RelMgr" # relation manage body
    DynamicEnum = es.create_enum_class(f_enum_cls_name, enum_dict)
    DynamicEnum.__doc__ = f"values for 'field_name' in {f_manage_cls_name}"
    RelManageBody = create_model(
        f_manage_cls_name,
        action=(es.M2mAction, Field(description=f"One of {es.M2mAction.values()}")),
        label=(bool, False),
        field_name=(
            DynamicEnum,
            Field(description=f"One of {DynamicEnum.__name__}:{DynamicEnum.values()}"),
        ),
        id=(Optional[PositiveInt], None),
        paginator=(Optional[pm.PaginatorBody], None),
        m2m_ids=(dict, {"add": [], "del": []}),
    )
    RelManageBody.__doc__ = f"fetch fields manage for {model.__name__}"
    return RelManageBody


def _relation_value(rel, related_obj):
    if rel.secondary is not None or rel.uselist:
        return f"[{len(related_obj or [])}]"
    return str(related_obj) if related_obj is not None else None


def _obj_to_dict(obj, fields=None):
    if obj is None:
        return {}
    result = {}
    mapper = sa_inspect(obj.__class__)
    state = sa_inspect(obj)
    requested_fields = set(fields or ["*"])
    include_all = "*" in requested_fields
    for col in mapper.columns:
        if not include_all and col.key not in requested_fields:
            continue
        val = getattr(obj, col.key, None)
        if val is not None and hasattr(val, 'isoformat'):
            val = val.isoformat()
        result[col.key] = val
    for rel in mapper.relationships:
        if not include_all and rel.key not in requested_fields:
            continue
        if rel.key in state.unloaded:
            result[rel.key] = None
            result[f"_{rel.key}_str"] = None
            continue
        related_obj = getattr(obj, rel.key, None)
        result[rel.key] = _relation_value(rel, related_obj)
        result[f"_{rel.key}_str"] = result[rel.key]
    return result
