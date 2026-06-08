from apps.udadmin.utils.ui_tools import UiInfo
from . import models as md


DepartmentUi = UiInfo(
    model=md.Department,
    list_display=["*"],
    list_filter=["id", "name", "code", "is_active"],
    search_fields=["name", "code", "location"],
    editable_fields=["name", "code", "location", "is_active"],
    readonly_fields=["created_at"],
)


EmployeeUi = UiInfo(
    model=md.Employee,
    list_display=["*"],
    list_filter=["id", "department_id", "name", "email", "age", "hired_on", "is_active"],
    search_fields=["name", "email", "bio"],
    editable_fields=[
        "department_id",
        "name",
        "email",
        "age",
        "salary",
        "hired_on",
        "is_active",
        "bio",
    ],
)
