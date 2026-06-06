from fastapi import FastAPI
from fastapi import exceptions as excep
from starlette.exceptions import HTTPException

from . import models as md
from . import ui
from .utils import error_handler as eh
from .utils import middleware as mw
from .utils.model_register import mr
from .utils.openapi_tags import openapi_tags

app = FastAPI(
    title="API-Help",
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

from apps.udadmin.routers.security import router as r_security

app.include_router(r_security, prefix="/security")

mr.register(app, md.User, ui_info=ui.user_ac)
mr.register(app, md.PermissionType)
mr.register(app, md.Permission)
mr.register(app, md.Role)
mr.register(app, md.Record)
mr.register(app, md.Config)
mr.register(app, md.ConfigType)
