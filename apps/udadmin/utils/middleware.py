from functools import wraps
import inspect
import traceback
from fastapi import Request
from fastapi.responses import JSONResponse

# from pydantic import BaseModel, Field
# from typing import Optional
# from fastapi import exceptions as excep
from fastapi import status

# from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from config import settings
from apps.udadmin.utils import resp_code as rc
from apps.udadmin.utils.i18n import parse_accept_language, set_locale, t

# from apps.udadmin.utils.objdoc import get_structure
from datetime import datetime

datetime_encoder = {datetime: lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S")}


async def LocaleMiddleware(request: Request, call_next):
    locale = parse_accept_language(request.headers.get("Accept-Language"))
    request.state.locale = locale
    set_locale(locale)
    response = await call_next(request)
    response.headers["Content-Language"] = locale
    return response


# 处理返回的json里面有时间格式的数据
async def datetime_formator(request: Request, call_next):
    # print(call_next)
    # get_structure(call_next)
    try:
        response = await call_next(request)
    except Exception as e:
        stack_trace = traceback.format_exc()
        # 处理异常
        content = {
            "code": rc.general_error,
            "message": t("error.internal_server_error", request=request),
            "msg": t("error.internal_server_error", request=request),
            "error": str(e),
            "trace": stack_trace,
        }
        return JSONResponse(
            # status_code=500,
            status_code=status.HTTP_200_OK,
            content=content,
        )
    # print(response)
    # get_structure(response)
    # res_test = jsonable_encoder(response, custom_encoder=datetime_encoder)
    return response


async def CommonExceptionHandler(request: Request, call_next):
    try:
        response = await call_next(request)
    except Exception as e:
        print(f"CommonExceptionHandler:{str(e)}")
        stack_trace = traceback.format_exc()
        print(f"trace:\n{str(stack_trace)}")
        code = (
            e.args[0].get("code")
            if e.args and isinstance(e.args[0], dict) and "code" in e.args[0].keys()
            else rc.general_error
        )
        error = (
            e.args[0].get("error")
            if e.args and isinstance(e.args[0], dict) and "error" in e.args[0].keys()
            else str(e)
        )
        msg = (
            e.args[0].get("msg")
            if e.args and isinstance(e.args[0], dict) and "msg" in e.args[0].keys()
            else str(e) or t("error.internal_server_error", request=request)
        )
        raw_extra = (
            e.args[0].get("extra")
            if e.args and isinstance(e.args[0], dict) and "extra" in e.args[0].keys()
            else None
        )
        extra = raw_extra.copy() if isinstance(raw_extra, dict) else {}
        extra["error"] = {
            "__class__": str(e.__class__),
            "__qualname__": str(e.__class__.__qualname__),
            "__module__": str(e.__class__.__module__),
        }
        content = {
            "code": code,
            "error": error,
            "message": msg,
            "msg": msg,
            "extra": extra,
        }
        if settings.DEBUG:
            content["trace"] = str(stack_trace)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            # status_code=status.HTTP_200_OK,
            content=content,
        )
    return response
