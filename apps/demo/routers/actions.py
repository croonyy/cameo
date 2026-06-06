from typing import Annotated

from fastapi import APIRouter, Depends

from apps.udadmin import models as md
from apps.udadmin.utils import auth
from apps.udadmin.utils import resp_code as rc
from apps.udadmin.utils.i18n import t

router = APIRouter(tags=["Demo Actions"])


@router.post("/detail/preview_row")
@auth.permission_required("model", "demo:DetailModel:action:preview_row")
async def preview_row(
    user: Annotated[md.User, Depends(auth.get_user)],
    payload: dict,
):
    print("demo.detail.preview_row received:", payload)
    return {"code": rc.success, "data": payload, "msg": t("common.ok")}


@router.post("/detail/show_context")
@auth.permission_required("model", "demo:DetailModel:action:show_context")
async def show_context(
    user: Annotated[md.User, Depends(auth.get_user)],
    payload: dict,
):
    print("demo.detail.show_context received:", payload)
    return {"code": rc.success, "data": payload, "msg": t("common.ok")}


@router.post("/detail/preview_record")
@auth.permission_required("model", "demo:DetailModel:action:preview_record")
async def preview_record(
    user: Annotated[md.User, Depends(auth.get_user)],
    payload: dict,
):
    print("demo.detail.preview_record received:", payload)
    return {"code": rc.success, "data": payload, "msg": t("common.ok")}


@router.post("/detail/show_records")
@auth.permission_required("model", "demo:DetailModel:action:show_records")
async def show_records(
    user: Annotated[md.User, Depends(auth.get_user)],
    payload: dict,
):
    print("demo.detail.show_records received:", payload)
    return {"code": rc.success, "data": payload, "msg": t("common.ok")}
