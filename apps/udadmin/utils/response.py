from __future__ import annotations

from typing import Any

from fastapi import Request

from . import resp_code as rc
from .i18n import t


def build_response(
    *,
    code: int,
    message: str,
    data: Any = None,
    error: Any = None,
    extra: dict | None = None,
    request_id: str | None = None,
) -> dict:
    content = {
        "code": code,
        "message": message,
        "msg": message,
        "data": data,
    }
    if error is not None:
        content["error"] = error
    if extra is not None:
        content["extra"] = extra
    if request_id is not None:
        content["request_id"] = request_id
    return content


def success(
    data: Any = None,
    message_key: str = "common.success",
    request: Request | None = None,
    **kwargs: Any,
) -> dict:
    return build_response(
        code=rc.success,
        message=t(message_key, request=request, **kwargs),
        data=data,
        request_id=getattr(request.state, "request_id", None) if request else None,
    )


def fail(
    code: int,
    message_key: str,
    data: Any = None,
    request: Request | None = None,
    error: Any = None,
    extra: dict | None = None,
    **kwargs: Any,
) -> dict:
    return build_response(
        code=code,
        message=t(message_key, request=request, **kwargs),
        data=data,
        error=error,
        extra=extra,
        request_id=getattr(request.state, "request_id", None) if request else None,
    )


class AppException(Exception):
    def __init__(
        self,
        *,
        code: int = rc.general_error,
        message_key: str = "error.internal_server_error",
        params: dict | None = None,
        status_code: int = 500,
        error: str | None = None,
        extra: dict | None = None,
    ) -> None:
        self.code = code
        self.message_key = message_key
        self.params = params or {}
        self.status_code = status_code
        self.error = error
        self.extra = extra
        super().__init__(message_key)
