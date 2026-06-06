from fastapi import status
from datetime import datetime
from typing import Any, Union, Dict, List, Optional
from pydantic import BaseModel, Field
from ..utils import resp_code as rc


class Response200(BaseModel):
    """统一响应格式"""

    code: int = Field(default=rc.success)  # 响应码
    msg: str = Field(default="success")  # 响应信息
    data: Any | None = Field(default="any data of any structure")  # 具体数据
    extra: dict | None = None # 额外信息


class Response500(BaseModel):
    """统一响应格式"""

    code: int = Field(default=rc.unknown_error)  # 响应码
    error: str = Field(default="error string")  # 错误信息
    msg: str = Field(default="internal server error")  # 响应信息
    trace: str = Field(default="set 'settings.DEBUG = TRUE' to see")  # 调试信息
    extra: dict | None = None # 额外信息


class Response422(BaseModel):
    """统一响应格式"""

    code: int = Field(default=rc.param_error)  # 响应码
    error: str = Field(default="error string")  # 错误信息
    msg: str = Field(default="Request Validation Error")  # 响应信息
    trace: str = Field(default="set 'settings.DEBUG = TRUE' to see")  # 调试信息
    extra: dict | None = None # 额外信息


general_resps: dict = {
    status.HTTP_200_OK: {
        "model": Response200,
        "description": "The item was found",
    },
    # status.HTTP_304_NOT_MODIFIED: {
    #     # "model": ItemNotModified,
    #     "description": "The item has not been modified since the last request",
    # },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "model": Response500,
        "description": "There was an internal server error",
    },
    status.HTTP_422_UNPROCESSABLE_ENTITY: {
        "model": Response422,
    },
}
