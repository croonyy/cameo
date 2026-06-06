from functools import wraps
import inspect
import traceback

from fastapi import HTTPException, Request, exceptions as excep, status
from fastapi.responses import JSONResponse

from config import settings
from . import resp_code as rc
from .i18n import t
from .response import AppException, fail


class udException(Exception):
    pass


def hand_error(func):
    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                trace = traceback.format_exc()
                return {
                    "code": rc.unknown_error,
                    "error": str(e),
                    "trace": str(trace),
                }

        return wrapper

    @wraps(func)
    def wrapper1(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            trace = traceback.format_exc()
            return {
                "code": rc.unknown_error,
                "error": str(e),
                "trace": str(trace),
            }

    return wrapper1


async def RequestValidationErrorHandler(
    request: Request, exc: excep.RequestValidationError
):
    stack_trace = traceback.format_exc()
    errors = []
    errors_str = []

    for error in exc.errors():
        field = ".".join(str(item) for item in error.get("loc", []) if item != "body")
        message_key = (
            "validation.field_required"
            if error.get("type") in {"missing", "value_error.missing"}
            else "validation.value_error"
        )
        translated_msg = t(message_key, request=request, field=field or str(error.get("loc", "")))
        errors.append(
            {
                "loc": error.get("loc"),
                "msg": translated_msg,
                "message": translated_msg,
                "type": error.get("type"),
                "input": error.get("input"),
            }
        )
        errors_str.append(f"{error.get('loc')}{translated_msg}")

    content = fail(
        rc.param_error,
        "validation.invalid_params",
        request=request,
        error="|".join(errors_str),
        extra={"errors": errors},
    )
    if settings.DEBUG:
        content["trace"] = stack_trace
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=content,
    )


async def HttpExceptionHandler(request: Request, exc: HTTPException) -> JSONResponse:
    stack_trace = traceback.format_exc()
    detail = str(exc.detail)
    message_key_map = {
        401: "auth.unauthorized",
        403: "auth.forbidden",
        404: "error.not_found",
    }
    if detail and detail not in {"None", "null"}:
        message_key = detail
    else:
        message_key = message_key_map.get(exc.status_code, "error.http_exception")
    translated_message = t(message_key, request=request)
    if translated_message == message_key:
        translated_message = detail

    content = {
        "code": rc.http_exception,
        "message": translated_message,
        "msg": translated_message,
        "data": None,
        "error": f"http exception:{str(exc)}",
    }
    if settings.DEBUG:
        content["trace"] = stack_trace
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
    )


async def AppExceptionHandler(request: Request, exc: AppException) -> JSONResponse:
    content = fail(
        exc.code,
        exc.message_key,
        request=request,
        error=exc.error or exc.message_key,
        extra=exc.extra,
        **exc.params,
    )
    return JSONResponse(status_code=exc.status_code, content=content)
