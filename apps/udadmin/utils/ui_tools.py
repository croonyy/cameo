from dataclasses import asdict, dataclass
from typing import Any, Literal, Mapping, Type
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import DeclarativeBase

UiAlign = Literal["L", "M", "R"]
ActionPlacement = Literal["row", "toolbar"]
ActionParam = Literal["id", "record"]


@dataclass
class ActionSchema:
    key: str
    label: str
    url: str
    permission: str
    placement: ActionPlacement
    action_key: str | None = None
    icon: str | None = None
    type: str = "default"
    param: ActionParam = "id"
    confirm: bool | Mapping[str, Any] | None = None
    show_if: Mapping[str, Any] | list[Mapping[str, Any]] | None = None
    disabled_if: Mapping[str, Any] | list[Mapping[str, Any]] | None = None

    def __post_init__(self):
        if self.action_key is None:
            self.action_key = self.key

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}


def get_custom_action_permission(
    app_name: str, model_name: str, action: Mapping[str, Any]
) -> str:
    permission = action.get("permission")
    if permission:
        return str(permission)
    perm_name = action.get("key") or action.get("action_key")
    return f"{app_name}:{model_name}:action:{perm_name}"


def get_custom_action_permissions(
    app_name: str, model_name: str, actions: list[Mapping[str, Any]] | None
) -> list[str]:
    return [get_custom_action_permission(app_name, model_name, action) for action in actions or []]


def serialize_custom_actions(actions: list[Mapping[str, Any] | ActionSchema] | None):
    return [action.to_dict() if isinstance(action, ActionSchema) else dict(action) for action in actions or []]


def FieldInfo(
    *,
    ui_name: str | None = None,
    ui_desc: str | None = None,
    ui_align: UiAlign | None = None,
    ui_order: int | None = None,
    ui_page_size: int | None = None,
    read_only: bool | None = None,
    choices: Mapping[str, Any] | list[Any] | tuple[Any, ...] | None = None,
    style: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    info = {
        "ui_name": ui_name,
        "ui_desc": ui_desc,
        "ui_align": ui_align,
        "ui_order": ui_order,
        "ui_page_size": ui_page_size,
        "read_only": read_only,
        "choices": choices,
        "style": dict(style) if style is not None else None,
    }
    return {key: value for key, value in info.items() if value is not None}


class UiInfo:

    def __init__(
        self,
        model: Type[DeclarativeBase],
        list_display=["*"],
        list_per_page=10,
        list_filter=[],
        search_fields=[],
        readonly_fields=[],
        exclude_fields=[],
        ordering=[],
        db_value_converters={},
        relation_search={},
        editable_fields=[],
        filter_cmps={},
        form_cmps={},
        custom_actions=[],
        **kwargs,
    ):
        self._model = model
        self.list_display = list_display
        self.list_per_page = list_per_page
        self.list_filter = list_filter
        self.search_fields = search_fields
        self.readonly_fields = readonly_fields
        self.exclude_fields = exclude_fields
        self.ordering = ordering
        self.db_value_converters = db_value_converters
        self.relation_search = relation_search
        self.editable_fields = editable_fields
        self.filter_cmps = filter_cmps
        self.form_cmps = form_cmps
        self.custom_actions = custom_actions
        for k, v in kwargs.items():
            setattr(self, k, v)
        if model:
            self._check(model)

    def check_readonly(self, item) -> list[str]:
        return [i for i in item.keys() if i in self.readonly_fields]

    def _check(self, model):
        # Get column names from SQLAlchemy model
        fields = set(model.__table__.columns.keys()) | {"*"}
        # Add relationship field names too
        mapper = sa_inspect(model)
        fields = fields | {r.key for r in mapper.relationships}
        attrs = [
            "list_display",
            "list_filter",
            "search_fields",
            "readonly_fields",
            "exclude_fields",
            "editable_fields",
        ]
        for attr in attrs:
            attr_v = getattr(self, attr)
            if tmp := [i for i in attr_v if i not in fields]:
                raise ValueError(
                    f"UiInfo {attr} config error:{tmp} not in model fields"
                )
        # Validate ordering: strip leading '-' for descending sort
        if self.ordering:
            ordering_fields = {o.lstrip("-") for o in self.ordering}
            if tmp := [f for f in ordering_fields if f not in fields]:
                raise ValueError(
                    f"UiInfo ordering config error:{tmp} not in model fields"
                )
        if tmp := [i for i in self.db_value_converters.keys() if i not in fields]:
            raise ValueError(
                f"UiInfo db_value_converters config error:{tmp} not in fields of model[{model.__name__}] "
            )
        if tmp := [i for i in self.filter_cmps.keys() if i not in fields]:
            raise ValueError(
                f"UiInfo filter_cmps config error:{tmp} not in fields of model[{model.__name__}] "
            )
        if tmp := [i for i in self.form_cmps.keys() if i not in fields]:
            raise ValueError(
                f"UiInfo form_cmps config error:{tmp} not in fields of model[{model.__name__}] "
            )


if __name__ == "__main__":
    pass
