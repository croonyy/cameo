from fastapi import FastAPI
from fastapi import exceptions as excep
from starlette.exceptions import HTTPException

from apps.demo import models as md
from apps.demo import ui
from apps.udadmin.utils import error_handler as eh
from apps.udadmin.utils import middleware as mw
from apps.udadmin.utils.model_register import mr
from apps.udadmin.utils.openapi_tags import openapi_tags

app = FastAPI(
    title="demo",
    version="1.0.0",
    swagger_ui_oauth2_redirect_url="/docs/oauth2-redirect",
    servers=[{"url": "http://localhost:1002", "description": "test"}],
    description='<img src="/static/logo.svg" height=100>',
    debug=True,
    openapi_tags=openapi_tags,
)

app.exception_handler(excep.RequestValidationError)(eh.RequestValidationErrorHandler)
app.exception_handler(HTTPException)(eh.HttpExceptionHandler)
app.exception_handler(eh.AppException)(eh.AppExceptionHandler)
app.middleware("http")(mw.LocaleMiddleware)
app.middleware("http")(mw.CommonExceptionHandler)

from apps.demo.routers.actions import router as r_actions

app.include_router(r_actions, prefix="/actions")

mr.register(app, md.ForeignKeyModel, ui_info=ui.ForeignKeyModelUi)
mr.register(app, md.RelationModel, ui_info=ui.RelationModelUi)
mr.register(app, md.DetailModel, ui_info=ui.DetailModelUi)
