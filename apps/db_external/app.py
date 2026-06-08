from fastapi import FastAPI
from fastapi import exceptions as excep
from starlette.exceptions import HTTPException

from apps.db_external import models as md
from apps.db_external import ui
from apps.udadmin.utils import error_handler as eh
from apps.udadmin.utils import middleware as mw
from apps.udadmin.utils.model_register import mr
from apps.udadmin.utils.openapi_tags import openapi_tags
from db.sa_external import async_session_factory


app = FastAPI(
    title="db_external",
    version="1.0.0",
    debug=True,
    openapi_tags=openapi_tags,
)

app.exception_handler(excep.RequestValidationError)(eh.RequestValidationErrorHandler)
app.exception_handler(HTTPException)(eh.HttpExceptionHandler)
app.exception_handler(eh.AppException)(eh.AppExceptionHandler)
app.middleware("http")(mw.LocaleMiddleware)
app.middleware("http")(mw.CommonExceptionHandler)

mr.register(app, md.Department, ui_info=ui.DepartmentUi, session_factory=async_session_factory)
mr.register(app, md.Employee, ui_info=ui.EmployeeUi, session_factory=async_session_factory)
