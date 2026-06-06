from sqlalchemy import inspect
from collections import OrderedDict

from sqlalchemy.orm import RelationshipProperty, ColumnProperty
from sqlalchemy.types import Enum
from . import enums as es
from . import doc
from . import udtools as ut
from . import ui_cmps
from db.sa import Base

model_perms = {
    "create": "create",
    "delete": "delete",
    "update": "update",
    "list": "list",
    "read": "read",
}

def get_model_info(model: type["Base"], ui_info=None):
    mapper = inspect(model)
    app_name = getattr(model, "app_name", "") or model.__tablename__.split("_")[0]
    model_name = model.__name__

    fields_info = OrderedDict()
    fields_doc = []
    pk = mapper.primary_key[0].name if mapper.primary_key else "id"

    # ==================================================================
    # ✅ 关键：按模型定义顺序遍历属性（保证 fields_doc 顺序正确）
    # ==================================================================
    model_attrs = []
    for name in model.__dict__:
        if name.startswith("_"):
            continue
        try:
            prop = mapper.attrs.get(name)
            if prop:
                model_attrs.append(prop)
        except Exception:
            continue

    # 把 mapper 里有，但模型 __dict__ 里没有的补上（比如继承字段 id, created_at）
    existing_names = {a.key for a in model_attrs}
    for attr in mapper.attrs.values():
        if attr.key not in existing_names:
            model_attrs.append(attr)

    # 开始遍历（顺序 = 模型定义顺序）
    for attr in model_attrs:
        field_name = attr.key
        field_info = {
            "app_name": app_name,
            "model_name": model_name,
            "field_name": field_name,
            "info": {},
            "is_required": False,
            "default": None,
            "choices": None,
            "has_db_field": False,
            "is_pk": False,
            "is_fk": False,
            "is_m2m": False,
            "is_o2o": False,
            "is_backward_fk": False,
            "generated": False,
            "unique": False,
            "null": True,
            "index": False,
            "indexable": False,
            "read_only": False,
            "field_type": None,
            "filter_cmp": None,
            "form_cmp": None,
            "decimal_places": None,
            "max_digits": None,
            "max_length": None,
            "source_field": None,
            "remote_fk_col": None,
        }

        # ------------------------------
        # 普通字段
        # ------------------------------
        if isinstance(attr, ColumnProperty):
            col = attr.columns[0]
            col_info = col.info or {}
            field_type = col.type.__class__.__name__

            field_info.update(
                {
                    "has_db_field": True,
                    "info": col_info,
                    "is_pk": col.primary_key,
                    "unique": col.unique,
                    "null": col.nullable,
                    "index": col.index,
                    "indexable": True,
                    "field_type": field_type,
                    "generated": col.autoincrement,
                    "read_only": col_info.get("read_only", field_info["read_only"]),
                    "decimal_places": getattr(col.type, "scale", None),
                    "max_digits": getattr(col.type, "precision", None),
                    "max_length": getattr(col.type, "length", None),
                }
            )

            is_auto_pk = col.primary_key and col.autoincrement
            field_info["is_required"] = (
                not col.nullable
                and not is_auto_pk
                and col.default is None
                and col.server_default is None
            )

            if col.default is not None:
                arg = getattr(col.default, "arg", None)
                field_info["default"] = arg if not callable(arg) else str(arg)

            if col.foreign_keys:
                field_info["is_fk"] = True
                for fk in col.foreign_keys:
                    field_info["remote_fk_col"] = fk.column.name
                    break

            if isinstance(col.type, Enum):
                field_info["choices"] = list(col.type.enums)
            if "choices" in col_info:
                field_info["choices"] = col_info["choices"]

            pk_tag = ut.font("#", color="#00aa00") if col.primary_key else "#"
            required_tag = (
                ut.font("\\*", color="#00aa00")
                if field_info["is_required"]
                else ut.font("\\*")
            )
            read_only_tag = ut.font("\u2776")
            db_field_tag = ut.font("\u2777", color="#00aa00")
            default_str = f"_default:{field_info['default']}_" if col.default else ""
            choices_str = (
                f"_可选值:{field_info['choices']}_" if field_info["choices"] else ""
            )

            doc_line = (
                f"- [{pk_tag}{required_tag}{read_only_tag}{db_field_tag}]"
                f"__{field_name}({col_info.get('ui_name', field_name)})__ "
                f"_<{field_type}({col.type})>_ __:__ "
                f"{col_info.get('ui_desc', col.comment or '')} {default_str} {choices_str}"
            )
            fields_doc.append(doc_line)

        # ------------------------------
        # 关系字段
        # ------------------------------
        elif isinstance(attr, RelationshipProperty):
            rel = attr
            rel_info = rel.info or {}
            is_m2m = rel.secondary is not None
            is_o2o = not rel.uselist and not is_m2m
            has_local_fk = any(col.foreign_keys for col in rel.local_columns)
            is_backward_fk = rel.uselist and not has_local_fk and not is_m2m

            if is_m2m:
                rel_field_type = "ManyToManyField"
            elif is_o2o:
                rel_field_type = "OneToOneField"
            elif is_backward_fk:
                rel_field_type = "BackwardFKRelation"
            else:
                rel_field_type = "ForeignKeyField"

            source_field = None
            rel_required = False
            if not is_m2m and has_local_fk:
                for col in rel.local_columns:
                    source_field = col.name
                    rel_required = (
                        not col.nullable
                        and col.default is None
                        and col.server_default is None
                    )
                    break

            remote_fk_col = None
            if is_backward_fk:
                for col in rel.mapper.class_.__table__.columns:
                    for fk in col.foreign_keys:
                        if fk.column.table == model.__table__:
                            remote_fk_col = col.name
                            break

            field_info.update(
                {
                    "has_db_field": False,
                    "is_required": rel_required,
                    "is_fk": not is_m2m and not is_backward_fk,
                    "is_m2m": is_m2m,
                    "is_o2o": is_o2o,
                    "is_backward_fk": is_backward_fk,
                    "field_type": rel_field_type,
                    "source_field": source_field,
                    "remote_fk_col": remote_fk_col,
                    "indexable": False,
                    "info": {
                        "ui_desc": f"关联模型: {rel.mapper.class_.__name__}",
                        **rel_info,
                    },
                }
            )

            pk_tag = "#"
            required_tag = ut.font("\\*")
            read_only_tag = ut.font("\u2776")
            db_field_tag = ut.font("\u2777")
            type_str = f"Relationship({rel_field_type})"

            doc_line = (
                f"- [{pk_tag}{required_tag}{read_only_tag}{db_field_tag}]"
                f"__{field_name}({field_info['info'].get('ui_name', field_name)})__ "
                f"_<{type_str}>_ __:__ "
                f"{field_info['info'].get('ui_desc', '')}"
            )
            fields_doc.append(doc_line)

        field_info["filter_cmp"] = ui_cmps.get_filter_cmp(
            field_info["field_name"], field_info["field_type"], ui_info
        )
        field_info["form_cmp"] = ui_cmps.get_form_cmp(
            field_info["field_name"], field_info["field_type"], ui_info
        )
        if not field_info["filter_cmp"]:
            print(f"数据库类型 {field_info['field_type']} 不支持filter组件化。")
        if not field_info["form_cmp"]:
            print(f"数据库类型 {field_info['field_type']} 不支持form组件化。")

        fields_info[field_name] = field_info

    # ====================== API 文档 ======================
    fields_doc_str = "\n".join(fields_doc)
    fetch_fields = [rel.key for rel in mapper.relationships]
    api_docs = {
        "create_item": doc.create_item.format(
            app_name=app_name,
            model_name=model_name,
            perm="create",
            fields=fields_doc_str,
        ),
        "delete_item": doc.delete_item.format(
            app_name=app_name, model_name=model_name, pk=pk, perm="delete"
        ),
        "update_item": doc.update_item.format(
            app_name=app_name,
            model_name=model_name,
            perm="update",
            fields=fields_doc_str,
        ),
        "read_item": doc.read_item.format(
            app_name=app_name,
            model_name=model_name,
            pk=pk,
            perm="read",
            fields=fields_doc_str,
        ),
        "get_item_list": doc.get_item_list.format(
            app_name=app_name, model_name=model_name, perm="list", fields=fields_doc_str
        ),
        "rel_manage": doc.rel_manage.format(
            app_name=app_name,
            model_name=model_name,
            perm="fetch",
            fetch_action=es.M2mAction.values(),
            fetch_fields=fetch_fields,
        ),
    }

    def meta_attr(name, default):
        return getattr(getattr(model, "Meta", object()), name, default)

    model_info = {
        "model": model,
        "menu_name": meta_attr("menu_name", model_name),
        "fileds_info": fields_info,
        "app": app_name,
        "tb_name": model.__tablename__,
        "tb_description": meta_attr("table_description", ""),
        "model_name": model_name,
        "fields_doc": fields_doc_str,
        "api_docs": api_docs,
    }
    return model_info
