import importlib

from fastapi import Request, Depends, HTTPException, status
from sqlalchemy import inspect as sa_inspect

# 序列化模型
from fastapi.encoders import jsonable_encoder
from ..utils.urls import api
from ..utils import auth
from ..utils import jwt_auth as ja
from ..utils import encoder as ec
from ..utils import resp_code as rc
from ..utils import pmodels as pm
from ..utils import http_resp as hr
from ..utils.i18n import t


def _sa_columns_to_dict(obj):
    """Extract only column attributes from a SQLAlchemy model instance.
    Excludes relationship attributes and internal SQLAlchemy state.
    """
    if obj is None:
        return {}
    mapper = sa_inspect(obj.__class__)
    return {col.key: getattr(obj, col.key, None) for col in mapper.columns}


@api(
    methods=["get"],
    tags=["Security"],
)
def test():
    return "success"


def import_function_from_path(function_path):
    """
    根据函数路径字符串（如 "module.submodule.function_name"）导入并返回函数对象
    """
    # 分割模块路径和函数名
    module_path, func_name = function_path.rsplit(".", 1)

    # 动态导入模块
    module = importlib.import_module(module_path)

    # 获取函数对象
    func = getattr(module, func_name)
    return func


@api(
    methods=["post"],
    tags=["Security"],
    responses=hr.general_resps,
)
async def login(req: pm.LoginForm):
    username = req.username.strip()
    password = req.password.strip()
    user = await auth.authenticate(username, password)
    if not user:
        return {"code": rc.user_error, "msg": t("auth.invalid_credentials")}
    user_json = jsonable_encoder(
        _sa_columns_to_dict(user), custom_encoder=ec.custom_encoder
    )
    token_info = ja.create_token(user_json)
    return {
        "code": rc.success,
        "data": token_info,
    }


@api(
    methods=["post"],
    tags=["Security"],
    responses=hr.general_resps,
)
async def refresh(request: Request, params: pm.RefreshToken):
    """
    refresh token
    """
    import jwt

    try:
        info = ja.parse_payload(params.refresh_token)
        # {'iat': 1737441868.4656336, 'exp': 1738737868.4656336, '_partial': True, '_custom_generated_pk': False, '_await_when_save': {}, 'password': '$2b$12$2al7PoB3s.xDaekG1KDI3eJgQqEL3f5qneygPtie7g80FLqMaUM1O', 'id': 1, 'is_delete': False, 'is_superuser': True, 'gender': '男', 'created_at': '2025-01-10 11:37:49', 'is_active': True, 'username': 'admin', 'last_login': '2025-01-10 11:37:49', 'updated_at': '2025-01-10 16:00:26', 'grant_type': 'refresh'}
        # print(info)
        if info.get("grant_type") == "refresh":
            payload = {
                k: v for k, v in info.items() if k not in ["exp", "iat", "grant_type"]
            }
            token_info = ja.create_token(payload)
            # token_info["status"] = 1
            return {
                "code": rc.success,
                "data": token_info,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=t("auth.not_refresh_token"),
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("auth.refresh_token_expired"),
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("auth.invalid_refresh_token", error=e.__class__.__name__),
        )


@api(
    methods=["get"],
    tags=["Security"],
)
# @eh.hand_error
def me(request: Request, user=Depends(auth.get_user)):
    return jsonable_encoder(
        {
            "code": rc.success,
            "data": _sa_columns_to_dict(user),
        },
        custom_encoder=ec.custom_encoder,
    )
