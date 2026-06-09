from apps.udadmin.utils import logo_letters  # 打印logo
from apps.udadmin.utils import ud_doc  # 自定义swagger文档的静态文件本地加载

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from apps.udadmin.utils.app_registry import mount_registered_apps
from config.settings import BASE_DIR
from config import settings
from fastapi.middleware.cors import CORSMiddleware
import os
from apps.udadmin.utils.model_base import init_db, close_db

if settings.LOCATE_PRINT:
    from apps.udadmin.utils import locate_print
    locate_print.locate_print()


# 使用模板渲染器处理根路径
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "static"))


# 上下文管理，startup执行yield之前的代码，shutdown执行yield以下的代码
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLAlchemy database
    await init_db()
    mount_registered_apps(app)
    from apps.udadmin.utils.model_register import mr

    if getattr(settings, "SYNC_REGISTERED_MODEL_PERMISSIONS", False):
        await mr.sync_registered_model_permissions()
    print(f"registered models:\n{list(mr.models_info.keys())}")
    yield
    try:
        await close_db()
    except Exception as e:
        print("=" * 80)
        print(e)


app = FastAPI(
    title="title",
    lifespan=lifespan,
    # root_path="/test", # 除了openapi文档地址，将服务所有的路由加上前缀才能访问。主文档地址是下面设置的，不会影响主应用文档前缀，但是会影响子应用的文档地址
    # 如果配置的不是本身文档所在的域 会导致跨域问题
    # servers=[{"url": "http://localhost:1002", "description": "test"}],  # 服务器配置
    docs_url="/docs",
    redoc_url="/redoc",
    debug=True,
)


# 挂载静态文件服务
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static"), html=True),
    name="static",
)


# @app.middleware("http")
# async def add_process_time_handler(request: Request, call_next):
#     start_time = time.time()
#     # call_next 处理了所有的错误，这里不会抛出错误，所以也就捕捉不到错误。
#     response = await call_next(request)
#     process_time = time.time() - start_time
#     print(f"耗费时间：{process_time:0.6f} seconds")
#     # response.headers["X-Process-Time"] = str(process_time)测试MySQL数据库
#     return response


# cors 配置,对app起作用，并非全局，子app也需要配置
# origins = [
#     "http://localhost",
#     "http://localhost:8080",
#     "http://localhost:1718",
# ]

app.add_middleware(
    CORSMiddleware,
    # allow_origins=origins,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/favicon.ico")
async def get_favicon():
    # return {"file": "static/favicon.ico"}
    return FileResponse("static/logo.svg", media_type="image/svg+xml")


# 重定向
@app.get("/")
async def index():
    return RedirectResponse(url="/admin")


# # 前端入口
# 所有admin应用的路由都要定位到前端主页
# 捕获所有其他路径并返回 index.html
@app.get("/admin", response_class=HTMLResponse)
@app.get("/admin/{full_path:path}", response_class=HTMLResponse)
async def catch_all(request: Request, full_path: str = ""):
    index_path = os.path.join(BASE_DIR, "static", "admin", "index.html")
    return FileResponse(index_path, media_type="text/html")
