from fastapi.routing import APIRoute, APIRouter
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Type,
    Union,
)
from fastapi import params
from fastapi.datastructures import Default #, DefaultPlaceholder

from fastapi.types import IncEx
from fastapi.utils import generate_unique_id
from starlette.responses import JSONResponse, Response
from starlette.routing import BaseRoute
from starlette.routing import Mount as Mount  # noqa
import inspect

from functools import partial


from functools import wraps


class Path:

    def __init__(self, route: APIRouter):
        self.route = route

    def __call__(self, path, callable, **kwargs):
        udkwargs = {}
        if hasattr(callable, "_ud_kwargs_jbknct"):
            udkwargs = callable._ud_kwargs_jbknct
        mod_udkwargs = {**udkwargs, **kwargs}
        mod_udkwargs = {k: v for k, v in mod_udkwargs.items() if k not in ["callable"]}
        return self.route.api_route(path=path, **mod_udkwargs)(callable)


def api(
    response_model: Any = Default(None),
    status_code: Optional[int] = None,
    tags: Optional[List[Union[str, Enum]]] = None,
    dependencies: Optional[Sequence[params.Depends]] = None,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    response_description: str = "Successful Response",
    responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
    deprecated: Optional[bool] = None,
    methods: Optional[List[str]] = None,
    operation_id: Optional[str] = None,
    response_model_include: Optional[IncEx] = None,
    response_model_exclude: Optional[IncEx] = None,
    response_model_by_alias: bool = True,
    response_model_exclude_unset: bool = False,
    response_model_exclude_defaults: bool = False,
    response_model_exclude_none: bool = False,
    include_in_schema: bool = True,
    response_class: Type[Response] = Default(JSONResponse),
    name: Optional[str] = None,
    callbacks: Optional[List[BaseRoute]] = None,
    openapi_extra: Optional[Dict[str, Any]] = None,
    generate_unique_id_function: Callable[[APIRoute], str] = Default(
        generate_unique_id
    ),
):  # 列出所有参数（不使用args,kwargs）是为了能获得提示功能
    kwargs = locals()  # 放在函数第一行就是收集所有入参

    def decorator(func):
        # 定义一个可以接受函数的变量

        func_wrapper = None
        if inspect.iscoroutinefunction(func):  # 判断函数 是同步还是异步

            @wraps(func)
            async def async_wrapper(*innerargs, **innerkwargs):
                return await func(*innerargs, **innerkwargs)
            func_wrapper = async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*innerargs, **innerkwargs):
                return func(*innerargs, **innerkwargs)
            func_wrapper = sync_wrapper
        # wrapper._ud_args = args
        # 绝不可能冲突 后缀
        setattr(func_wrapper, '_ud_kwargs_jbknct', kwargs)
        return func_wrapper

    return decorator
