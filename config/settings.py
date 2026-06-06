from starlette.templating import Jinja2Templates
import os

BASE_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

DEBUG = True
# DEBUG = False

# LOCATE_PRINT = True
LOCATE_PRINT = False

TEMPLATES = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# ============================================================
# SQLAlchemy 配置
# ============================================================

# Database URL - supports SQLite, MySQL, PostgreSQL
# SQLite: sqlite+aiosqlite:///path/to/db.sqlite3
# MySQL: mysql+aiomysql://user:pass@host:port/dbname
# PostgreSQL: postgresql+asyncpg://user:pass@host:port/dbname
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'db', 'db.sqlite3')}"
# DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/cameo"
# DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/cameo"
SQL_LOG = False

# When enabled, startup checks registered models and creates missing model permissions.
# It only inserts missing Permission rows; it does not delete permissions or change role/user grants.
SYNC_REGISTERED_MODEL_PERMISSIONS = True

# Mounted FastAPI sub-applications.
# String entries use defaults:
#   "apps.demo.app:app" -> path "/demo", name "demo"
# Dict entries can customize path/name:
#   {"app": "apps.demo.app:app", "path": "/custom-demo", "name": "custom_demo"}
REGISTERED_APPS = [
    {"app": "apps.udadmin.app:app", "path": "/udadmin", "name": "admin"},
    {"app": "apps.demo.app:app", "path": "/demo", "name": "demo"},
]


# app的前端显示配置
APP_INFO = {
    "udadmin": {
        "app_name": "udadmin",
        "app_menu_name": "授权与认证",
        "app_description": "授权与认证,用户管理,角色管理,权限管理",
        "app_icon": "antd:UserOutlined",
    },
    "demo": {
        "app_name": "demo",
        "app_menu_name": "应用demo",
        "app_description": "应用demo,测试描述",
        "app_icon": "antd:AppstoreOutlined",
    },
    "app2": {
        "app_name": "app2",
        "app_menu_name": "应用2",
        "app_description": "应用2,测试描述",
        "app_icon": "antd:BlockOutlined",
    },
}

AUTHENTICATION_BACKENDS = [
    "apps.udadmin.utils.auth.DatabaseAuthenticationBackend",
    "apps.udadmin.utils.auth.LDAPAuthenticationBackend",
]

# 配置 LDAP 参数
LDAP_CONFIG = {
    "AUTH_LDAP_SERVER_URI": "ldap://localhost:389",
    "AUTH_LDAP_BIND_DN": "",
    "AUTH_LDAP_BIND_PASSWORD": "",
    "AUTH_LDAP_USER_SEARCH": {
        "BASE_DN": "",
        "SCOPE": "SUBTREE",
        "FILTERSTR": "(sAMAccountName=%(user)s)",
    },
    "AUTH_LDAP_USER_DN_TEMPLATE": "",
    "AUTH_LDAP_USER_ATTR_MAP": {
        "username": "sAMAccountName",
        "cn_name": "cn",
    },
    "AUTH_LDAP_ALWAYS_UPDATE_USER": True,
    "AUTH_LDAP_CREATE_USER": False,
    "AUTH_LDAP_CONNECTION_OPTIONS": {
        "receive_timeout": 5,
    },
}


SECRET_KEY = "change_to_your_secret_key_here_ghbjgtimngv"
ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_SECONDS = 30
# REFRESH_TOKEN_EXPIRE_SECONDS = 60 * 60 * 24 * 15
ACCESS_TOKEN_EXPIRE_SECONDS = 60 * 30 # 30分钟
REFRESH_TOKEN_EXPIRE_SECONDS = 60 * 60 * 24 * 15 # 15天

TZ = "Asia/Shanghai"  # 东八区时区字符串

# SWAGGER_PATH='swagger_docs.html'
# REDOC_PATH='re_docs.html'



# 本地配置覆盖
try:
    from .local_settings import *  # type: ignore

    # print(f"import settings from local_settings.py")
except Exception as e:
    # print(f"Can't import settings from local_settings.py")
    pass
