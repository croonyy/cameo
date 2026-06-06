from fastapi import APIRouter
from apps.udadmin.utils.urls import Path
from apps.udadmin.handlers import security as st


router = APIRouter()
path = Path(router)


path("/test", st.test)
path("/token", st.login)
path("/refresh", st.refresh)
path("/me", st.me)
