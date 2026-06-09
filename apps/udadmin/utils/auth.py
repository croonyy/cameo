from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
import importlib
import secrets

import jwt
from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.security import (
    HTTPAuthorizationCredentials,
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    HTTPBearer,
)
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi.security.base import SecurityBase
import asyncio

# from fastapi.openapi.models import SecurityBase
# from typing import Any, Dict, List, Optional, Union, cast
# from jwt.exceptions import InvalidTokenError
from functools import wraps
import inspect
from .i18n import t


from config import settings
from . import jwt_auth as ja
from .. import models as md
from .model_base import get_session_factory

async_session_factory = get_session_factory()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


class AuthException(Exception):
    pass


def import_object(path: str):
    module_path, object_name = path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, object_name)


class BaseAuthenticationBackend:
    async def authenticate(self, username: str, password: str):
        raise NotImplementedError


class DatabaseAuthenticationBackend(BaseAuthenticationBackend):
    async def authenticate(self, username: str, password: str):
        async with async_session_factory() as session:
            from sqlalchemy import select

            stmt = select(md.User).where(md.User.username == username)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if not user:
                return None
            if not verify_password(password, user.password):
                return None
            return user


class LDAPAuthenticationBackend(BaseAuthenticationBackend):
    def __init__(self, config: dict | None = None):
        self.config = config or getattr(settings, "LDAP_CONFIG", {})

    async def authenticate(self, username: str, password: str):
        if not username or not password:
            return None
        ldap_attrs = await asyncio.to_thread(self._authenticate_ldap, username, password)
        if ldap_attrs is None:
            return None
        return await self._get_or_create_user(username, ldap_attrs)

    def _authenticate_ldap(self, username: str, password: str) -> dict | None:
        try:
            from ldap3 import ALL, Connection, Server
            from ldap3.core.exceptions import LDAPException
            from ldap3.utils.conv import escape_filter_chars
        except ImportError as exc:
            raise AuthException("LDAPAuthenticationBackend requires ldap3 package.") from exc

        server_uri = self.config.get("AUTH_LDAP_SERVER_URI") or self._legacy_server_uri()
        user_dn_template = self.config.get("AUTH_LDAP_USER_DN_TEMPLATE")
        user_search = self.config.get("AUTH_LDAP_USER_SEARCH") or {}
        base_dn_value = user_search.get("BASE_DN") or self.config.get("search_base")
        filterstr_value = user_search.get("FILTERSTR") or self.config.get("search_filter")
        base_dn = str(base_dn_value) if base_dn_value else ""
        filterstr = str(filterstr_value) if filterstr_value else ""
        if not server_uri or not user_dn_template and (not base_dn or not filterstr):
            return None

        scope_value = str(user_search.get("SCOPE", "SUBTREE")).upper()
        search_scope: Literal["BASE", "LEVEL", "SUBTREE"]
        if scope_value == "BASE":
            search_scope = "BASE"
        elif scope_value in {"ONELEVEL", "LEVEL"}:
            search_scope = "LEVEL"
        else:
            search_scope = "SUBTREE"
        escaped_username = escape_filter_chars(username)
        search_filter = filterstr % {"user": escaped_username} if filterstr else ""
        attrs = self._ldap_attrs()
        bind_dn = self.config.get("AUTH_LDAP_BIND_DN") or self.config.get("bind_dn") or None
        bind_password = (
            self.config.get("AUTH_LDAP_BIND_PASSWORD") or self.config.get("bind_password") or None
        )
        options = self.config.get("AUTH_LDAP_CONNECTION_OPTIONS") or {}
        server = Server(server_uri, get_info=ALL, connect_timeout=options.get("connect_timeout"))

        service_conn = None
        user_conn = None
        try:
            if user_dn_template:
                user_dn = user_dn_template % {"user": escaped_username}
                user_conn = Connection(
                    server,
                    user=user_dn,
                    password=password,
                    auto_bind=True,
                    receive_timeout=options.get("receive_timeout"),
                )
                return {}

            service_conn = Connection(
                server,
                user=bind_dn,
                password=bind_password,
                auto_bind=True,
                receive_timeout=options.get("receive_timeout"),
            )
            if not service_conn.search(base_dn, search_filter, search_scope, attributes=attrs):
                return None
            if not service_conn.entries:
                return None

            entry = service_conn.entries[0]
            user_dn = entry.entry_dn
            user_conn = Connection(
                server,
                user=user_dn,
                password=password,
                auto_bind=True,
                receive_timeout=options.get("receive_timeout"),
            )
            return self._entry_to_attrs(entry)
        except LDAPException:
            return None
        except Exception:
            return None
        finally:
            if user_conn is not None and user_conn.bound:
                user_conn.unbind()
            if service_conn is not None and service_conn.bound:
                service_conn.unbind()

    def _legacy_server_uri(self) -> str:
        ldap_server = self.config.get("ldap_server")
        if not ldap_server:
            return ""
        port = self.config.get("ldap_port")
        if str(ldap_server).startswith(("ldap://", "ldaps://")):
            return ldap_server
        return f"ldap://{ldap_server}:{port or 389}"

    def _ldap_attrs(self) -> list[str]:
        attrs = set(self.config.get("attrs") or [])
        attr_map = self.config.get("AUTH_LDAP_USER_ATTR_MAP") or {}
        attrs.update(attr_map.values())
        return sorted(attrs) or ["*"]

    def _entry_to_attrs(self, entry) -> dict:
        data = {}
        for attr_name in self._ldap_attrs():
            if attr_name == "*":
                continue
            value = getattr(entry, attr_name, None)
            if value is not None:
                data[attr_name] = value.value
        return data

    async def _get_or_create_user(self, username: str, ldap_attrs: dict):
        from sqlalchemy import select

        attr_map = self.config.get("AUTH_LDAP_USER_ATTR_MAP") or {}
        mapped_values = {
            local_field: ldap_attrs.get(ldap_attr)
            for local_field, ldap_attr in attr_map.items()
            if ldap_attrs.get(ldap_attr) is not None
        }
        mapped_values["username"] = mapped_values.get("username") or username

        async with async_session_factory() as session:
            stmt = select(md.User).where(md.User.username == mapped_values["username"])
            user = await session.scalar(stmt)
            if user:
                if self.config.get("AUTH_LDAP_ALWAYS_UPDATE_USER", True):
                    changed = False
                    for field, value in mapped_values.items():
                        if field != "username" and hasattr(user, field):
                            setattr(user, field, value)
                            changed = True
                    if changed:
                        await session.commit()
                        await session.refresh(user)
                return user

            if not self.config.get("AUTH_LDAP_CREATE_USER", False):
                return None

            user = md.User(
                username=mapped_values["username"],
                password=get_password_hash(secrets.token_urlsafe(32)),
                is_active=True,
            )
            for field, value in mapped_values.items():
                if field != "username" and hasattr(user, field):
                    setattr(user, field, value)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user


async def authenticate(username, password):
    backends = getattr(settings, "AUTHENTICATION_BACKENDS", None) or [
        "apps.udadmin.utils.auth.DatabaseAuthenticationBackend"
    ]
    for backend_path in backends:
        backend_cls = import_object(backend_path)
        backend = backend_cls()
        try:
            user = await backend.authenticate(username, password)
        except AuthException:
            user = None
        if user:
            return user
    return None


async def authenticate_database(username, password):
    async with async_session_factory() as session:
        from sqlalchemy import select
        stmt = select(md.User).where(md.User.username == username)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=t("auth.user_not_exists", username=username),
            )
        else:
            if not verify_password(password, user.password):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=t("auth.password_incorrect", username=username),
                )
            return user


# user_info:{'iat': 1734080045.264618, 'exp': 1734087247.264618, 'id': 0, 'username': 'admin', 'cn_name': '管理员', 'updated_at': '2024-12-10T17:34:18.477076+08:00', 'password': '$2b$12$nQuFvms5c69eeLG07/xlS.H9cz5aevDUzoC/mzuEEgtWpzVkqOyiO', 'is_active': True, 'is_delete': False, 'created_at': '2024-12-10T17:34:18.477038+08:00', 'gender': '男', 'is_superuser': True, 'last_login': '2024-12-10T17:34:18.477122+08:00'}


async def get_user(
    Authorization: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())],
) -> md.User:
    token = Authorization.credentials
    try:
        user_info = ja.parse_payload(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("auth.token_expired"),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("auth.invalid_token", error=e.__class__.__name__),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=t("auth.jwt_error", error_class=e.__class__.__name__, error=str(e)),
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user_info.get("username"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("auth.token_missing_username"),
            headers={"WWW-Authenticate": "Bearer"},
        )
    async with async_session_factory() as session:
        from sqlalchemy import select

        # 👇 这是 SQLAlchemy 2.0 异步 唯一正确、稳定、不报错的写法
        stmt = select(md.User).where(md.User.username == user_info["username"])
        user = await session.scalar(stmt)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=t("auth.user_not_found", username=user_info["username"]),
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.is_delete is True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=t("auth.user_deleted", username=user_info["username"]),
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active is True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=t("auth.user_not_active", username=user_info["username"]),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def check_user_permission_async(user, perm_type, perm_name):
    from sqlalchemy import select, exists
    from apps.udadmin.models import Permission, PermissionType
    async with async_session_factory() as session:
        # Check if permission exists
        stmt = select(Permission).join(Permission.permission_type).where(
            Permission.name == perm_name, PermissionType.name == perm_type
        )
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=t("auth.permission_not_defined", perm_type=perm_type, perm_name=perm_name),
            )
        # Check user direct permission
        stmt2 = select(Permission).join(Permission.permission_type).where(
            Permission.name == perm_name, PermissionType.name == perm_type,
            Permission.users.any(id=user.id)
        )
        result2 = await session.execute(stmt2)
        user_perms = result2.scalar_one_or_none()
        # Check role-based permission
        stmt3 = select(Permission).join(Permission.permission_type).where(
            Permission.name == perm_name, PermissionType.name == perm_type,
            Permission.roles.any(md.Role.users.any(id=user.id))
        )
        result3 = await session.execute(stmt3)
        role_perms = result3.scalar_one_or_none()
        if user_perms or role_perms:
            return True
        else:
            return False


def permission_required(perm_type, perm_name):
    def inner(func):
        if inspect.iscoroutinefunction(func):  # 判断函数是不是异步函数

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                user = kwargs.get("user")
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=t("auth.request_user_missing"),
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                if not user.is_superuser:
                    if await check_user_permission_async(user, perm_type, perm_name):
                        return await func(*args, **kwargs)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=t(
                                "auth.no_permission",
                                username=user.username,
                                permission=f"{perm_type}:{perm_name}",
                            ),
                        )
                return await func(*args, **kwargs)

            return async_wrapper

        else:
            # raise Exception(f"check_user_permission not support sync function")
            # 如果想要支持同步函数，则需要实现下面的check_user_permission_sync方法（同步），
            # 不能在同步函数中直接使用异步方法
            # 在同步函数里面强行用异步函数check_user_permission_sync(user, perm_type, perm_name) 会返回一个awaitable对象
            # if判断会一直为真，也就是说不会判断
            # 所以需要用asyncio.run()来强制执行
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                user = kwargs.get("user")
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=t("auth.request_user_missing"),
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                if not user.is_superuser:
                    if asyncio.run(
                        check_user_permission_async(user, perm_type, perm_name)
                    ):
                        return func(*args, **kwargs)
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=t(
                                "auth.no_permission",
                                username=user.username,
                                permission=f"{perm_type}:{perm_name}",
                            ),
                        )
                return func(*args, **kwargs)

            return sync_wrapper

    return inner
