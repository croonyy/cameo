from .utils.auth import get_password_hash
from .utils.ui_tools import UiInfo
from . import models as md

user_ac = UiInfo(
    # model=md.User,  # type: ignore
    model=md.User,
    # list_filter=[
    #     "id",
    #     "username",
    #     "gender",
    #     "cn_name",
    #     "is_active",
    #     "is_superuser",
    #     "roles",
    # ],
    readonly_fields=["created_at", "updated_at", "last_login"],
    # exclude_fields=["password", "is_delete", "operations"],
    ordering=["-id"],
    db_value_converters={"password": get_password_hash},
    # json类型不支持icontain 搜索，所以relation_search中不包含json字段
    relation_search={"roles": ["name", "id"], "permissions": ["name", "id"]},
)
