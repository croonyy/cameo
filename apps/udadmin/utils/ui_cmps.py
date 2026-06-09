# Frontend filter components:
# front/src/views/crud/cmpsFilter.ts
# D:/Users/yuan.yang/Desktop/git_clone/cameo/front/src/views/crud/cmpsFilter.ts
filter_map = {
    "BigInteger": "SelectFilter",
    "Boolean": "SelectFilter",
    "Date": "DateFilter",
    "DateTime": "DatetimeFilter",
    "Enum": "SelectFilter",
    "Float": "SelectFilter",
    "Integer": "SelectFilter",
    "JSON": "JsonFilter",
    "Numeric": "SelectFilter",
    "SmallInteger": "SelectFilter",
    "String": "SelectFilter",
    "Text": "SelectFilter",
    "Time": "TimeFilter",
    "LargeBinary": "SelectFilter",
    "BackwardFKRelation": "SelectFilter",
    "ForeignKeyField": "SelectFilter",
    "ManyToManyField": "SelectFilter",
    "OneToOneField": "SelectFilter",
}


# Frontend form components:
# front/src/views/crud/cmpsForm.ts
form_map = {
    "BigInteger": "NumberComponent",
    "Boolean": "BooleanField",
    "Date": "DateField",
    "DateTime": "DatetimeField",
    "Enum": "SelectField",
    "Float": "FloatField",
    "Integer": "IntField",
    "JSON": "JSONField",
    "LargeBinary": "CharField",
    "Numeric": "DecimalField",
    "SmallInteger": "IntField",
    "String": "InputField",
    "Text": "TextField",
    "Time": "TimeField",
    "BackwardFKRelation": "RelationField",
    "ForeignKeyField": "ForeignKeyField",
    "ManyToManyField": "RelationField",
    "OneToOneField": "ForeignKeyField",
}


def get_ui_field_cmp(ui_info, attr_name: str, field_name: str | None):
    if not ui_info or not field_name:
        return None
    return getattr(ui_info, attr_name, {}).get(field_name)


def get_filter_cmp(field_name: str | None, field_type: str | None, ui_info=None):
    ui_cmp = get_ui_field_cmp(ui_info, "filter_cmps", field_name)
    if ui_cmp or not field_type:
        return ui_cmp
    return filter_map.get(field_type)


def get_form_cmp(field_name: str | None, field_type: str | None, ui_info=None):
    ui_cmp = get_ui_field_cmp(ui_info, "form_cmps", field_name)
    if ui_cmp or not field_type:
        return ui_cmp
    return form_map.get(field_type)
