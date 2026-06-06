from pydantic import BaseModel, PositiveInt
from fastapi import Body
from typing import Optional, Union, List
from .enums import UdEnum


class Symbol(UdEnum):
    """
    条件符号
    """

    contains = "contains"
    icontains = "icontains"
    lt = "lt"
    gt = "gt"
    in_ = "in"
    eq = "eq"


class Filter(BaseModel):
    field: str = "field"
    symbol: Symbol = Symbol.contains
    value: Union[str, List[str]] = "value"


class PaginatorBody(BaseModel):
    curr_page: PositiveInt = Body(default=1, gt=0)
    page_size: PositiveInt = Body(default=10, gt=0)
    order_by: Optional[list[str]] = Body(
        default=[], description="'field' for ASC,'-field' for DESC."
    )
    filters: Optional[list | str] = Body(
        # filters: list = Body(
        default=[],
        description=(
            """
    [ 'or',
        [ 'and',
            {'field': 'username', 'symbol': 'icontains', 'value': 'user'},
            {'field': 'gender', 'symbol': 'eq', 'value': '女'}
        ],
        [ 'and',
            {'field': 'username', 'symbol': 'icontains', 'value': 'user'},
            {'field': 'username', 'symbol': 'eq', 'value': 'aa'}
        ]
    ]"""
        ),
    )


class LoginForm(BaseModel):
    username: str = "username"
    password: str = "password"


class RefreshToken(BaseModel):
    refresh_token: str = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsInR5cGUiOiJqd3QifQ.eyJpYXQiOjE3Mzc1MzgyOTguMzUxNzUsImV4cCI6MTczNzUzODMwMi4zNTE3NSwiaWQiOjAsInVzZXJuYW1lIjoidXNlcjIifQ.biiSuiUQAv5SairRajFOjeF1OhDvWC7ZQfz5Yd1ag1A"
    )


class AllowModel(BaseModel):
    model_name: str = "app_name:model_name"


class FilterFieldsDistinctValues(BaseModel):
    app_model_name: str = "app_name:model_name"
    field_names: str = "field1"
    paginator: PaginatorBody = Body(default=PaginatorBody())
