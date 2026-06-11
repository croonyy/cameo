# Cameo

🌐 Switch Language: [简体中文](README.md)

<p align="center">
  <a href="#"><img src="./static/logo1.svg" alt="Cameo" width="200"></a>
</p>

<p align="center">
  <strong>An admin framework based on FastAPI, SQLAlchemy 2.0, Vue 3, and Naive UI</strong>
</p>

## Introduction

Cameo is a frontend/backend separated admin framework. The backend uses FastAPI and SQLAlchemy 2.0, while the frontend uses Vue 3, Vite, Naive UI, and pnpm. The project includes the built-in `udadmin` management app, the `demo` sample app, and the `db_external` external database sample app to demonstrate model registration, automatic CRUD, permission control, multiple databases, field types, relationship fields, and custom actions.

Core capabilities:

- Automatic CRUD: generate list, detail, create, edit, delete APIs and pages after registering SQLAlchemy models.
- RBAC permissions: built-in users, roles, permission types, permission instances, and operation records.
- Model UI configuration: configure list columns, filters, search fields, editable fields, and custom actions through `UiInfo` and `FieldInfo`.
- Internationalization: backend `locales/zh.yml`, `locales/en.yml`, and frontend `front/src/i18n` provide Chinese and English display support together.
- Demo App: covers common model scenarios such as foreign keys, one-to-one, many-to-many, enums, JSON, dates, booleans, numbers, and text.
- External database: built-in `db_external` sample that shows how to manage existing tables from an independent database.
- Table features: pagination, sorting, filtering, horizontal scrolling, resizable columns, inline editing, batch selection, fixed action columns, and custom row/toolbar actions.
- Docker Compose: supports frontend build, test data initialization, and backend startup with a Python slim image.

## Project Links

- GitHub: https://github.com/croonyy/cameo
- Gitee: https://gitee.com/croonyy/cameo

## Community Chat

Join the QQ group to discuss usage questions, feature suggestions, and customization experience.

<p>
  <img src="static/qq_group.png" alt="Cameo QQ group" width="260">
</p>

## Screenshots

### Login

A dark technology-style login page. The default demo account is `admin/123456`.

![Login](static/images/login.png)

### Dashboard

The dashboard after login shows system navigation, tabs, quick toolbar actions, and overview panels.

![Dashboard](static/images/dashboard.png)

### Model List

CRUD lists are generated from backend models and support pagination, sorting, batch selection, row actions, column resizing, and horizontal scrolling.

![Model List](static/images/list.png)

### Query Filters

The list page includes a model field filter panel that generates inputs, selectors, boolean filters, and other query controls according to field types.

![Query Filters](static/images/filter.png)

### Edit Form

The edit page generates forms from model fields and covers common field types such as numbers, text, dates, enums, and JSON.

![Edit Form](static/images/edit.png)

### Inline Editing

Lists support inline editing, allowing fields such as enums and booleans to be modified directly in the table.

![Inline Editing](static/images/inline_edit.png)

### API Docs

The backend automatically generates Swagger API documentation with FastAPI for debugging authentication, CRUD, and business APIs.

![API Docs](static/images/api_docs.png)

## Tech Stack

Backend:

- FastAPI
- SQLAlchemy 2.0 async
- Alembic
- SQLite as the default database, with MySQL or PostgreSQL available by changing `DATABASE_URL`
- JWT authentication
- Database authentication and LDAP authentication backends

Frontend:

- Vue 3
- Vite
- Naive UI
- Pinia
- Alova
- pnpm 10.5.0
- Node.js 22

## Application Structure

The main application mounts sub-applications in `main.py`:

- `/udadmin`: admin management app, including users, roles, permissions, configuration, operation records, and other management models.
- `/demo`: sample app that demonstrates automatic CRUD and complex fields/relationships.
- `/db_external`: external database sample app that demonstrates CRUD management for independent database tables.
- `/static`: static files. The frontend production build is located in `static/admin`.
- `/admin`: admin frontend entry. After production build, the backend serves `static/admin/index.html` directly.

`REGISTERED_APPS` in `config/settings.py` controls mounted applications:

```python
from apps.udadmin.utils.app_registry import AppReg

REGISTERED_APPS = [
    AppReg("apps.udadmin.app:app", app_icon="antd:UserOutlined"),
    AppReg("apps.demo.app:app"),
    AppReg("apps.db_external.app:app", app_icon="antd:DatabaseOutlined"),
]
```

`AppReg` supports four parameters:

- `app_path`: FastAPI app import path, required. For example, `AppReg("apps.udadmin.app:app")` or `AppReg(app_path="apps.demo.app:app")`.
- `router_prefix`: mount path, defaulting to `/<app directory name>`, such as `/udadmin`, `/demo`, or `/db_external`.
- `app_name`: application name, defaulting to the app directory name.
- `app_icon`: frontend application icon, defaulting to `antd:AppstoreOutlined`.

## Demo App

`apps/demo` provides three sample models:

- `ForeignKeyModel`: foreign key target model used to test one-to-many relationships.
- `RelationModel`: relationship model used to test one-to-one and many-to-many relationships.
- `DetailModel`: detail model covering BigInteger, LargeBinary, Boolean, Enum, String, Date, DateTime, Numeric, Float, Integer, JSON, Text, Time, ForeignKey, relationship, and other fields.

`apps/demo/ui.py` demonstrates model UI configuration:

- `list_display=["*"]` displays all fields.
- `list_filter` configures filter fields.
- `search_fields` configures search fields.
- `editable_fields` configures inline editable fields.
- `custom_actions` configures row-level and toolbar custom actions.

`apps/demo/routers/actions.py` provides custom action APIs and binds permissions through `permission_required`, for example:

- `/demo/actions/detail/preview_row`
- `/demo/actions/detail/preview_record`
- `/demo/actions/detail/show_context`
- `/demo/actions/detail/show_records`

## External Database Sample

`apps/db_external` is the built-in external database sample app and is registered to `/db_external` by default. It uses `DATABASES["db_external"]` to connect to `db/db_external.sqlite3`, and binds models to an independent database and app through `get_base(database="db_external", app_name="db_external")`.

Current sample models:

- `Department`: external department table, including department name, code, office location, active status, and creation time.
- `Employee`: external employee table, including department, name, email, age, salary, hire date, active status, and bio.

`init_data.py` rebuilds and seeds this sample external database. When connecting an existing business database, do not run Alembic migrations against the external database. After the database schema changes, update the corresponding SQLAlchemy models manually.

## Local Development

### Requirements

- Python 3.12+
- Node.js 22+
- pnpm 10.5.0

### Initialization

```bash
pip install -r requirements.txt
python -m alembic upgrade head
python init_data.py
```

`init_data.py` rebuilds the default SQLite database and writes test data, including users, roles, permissions, configuration, operation records, and demo data.
It also rebuilds `db/db_external.sqlite3` and writes sample external departments and employees.

Common accounts:

- `admin` / `123456`
- `test_user` / `123456`
- `all_model_user` / `123456`
- `udadmin_user` / `123456`
- `demo_user` / `123456`
- `editor_user` / `123456`
- `delete_user` / `123456`
- `detail_user` / `123456`
- `direct_user` / `123456`
- `empty_user` / `123456`

### Start Backend

```bash
python run.py
```

The local development script listens on:

```text
http://localhost:3014
```

To access the backend from another machine on the LAN, do not listen only on `localhost`. Start it with `0.0.0.0`, for example:

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 3014 --reload
```

### Start Frontend Development Server

```bash
cd front
corepack enable
corepack prepare pnpm@10.5.0 --activate
pnpm install
pnpm run dev
```

The frontend development server port follows the Vite configuration. For production builds, the frontend output goes to `static/admin`:

```bash
pnpm run build
```

In production, the backend serves the frontend pages and APIs from the same origin by default. In `front/.env.production`, `VITE_PUBLIC_PATH=/static/admin/`, while `VITE_GLOB_API_URL` and `VITE_GLOB_API_URL_PREFIX` are blank by default. When blank, requests use the current page origin, which works well when the backend is deployed on the actual server IP or domain. If the frontend and backend are deployed separately, configure these two variables according to the gateway address.

## Docker Compose

The repository root provides `docker-compose.yml` with three services:

- `frontend-build`: uses `node:22-alpine` to install dependencies and build the frontend.
- `init-data`: runs `python init_data.py`, rebuilding the main database and external sample database and seeding test data.
- `backend`: uses `python:3.12-slim` to build and run the backend, exposing port `3014`.

### One-Command Startup

```bash
# First startup: build frontend, initialize data, and start backend
docker compose --profile build --profile init up --build

# Regular startup afterward
docker compose up -d backend
```

After startup, visit:

```text
http://localhost:3014
http://localhost:3014/admin
http://localhost:3014/docs
http://localhost:3014/udadmin/docs
http://localhost:3014/demo/docs
http://localhost:3014/db_external/docs
```

Rebuild after code or dependency changes:

```bash
docker compose up -d --build backend
```

View logs:

```bash
docker compose logs -f backend
```

Stop services:

```bash
docker compose down
```

## Directory Structure

```text
cameo/
├─ apps/
│  ├─ udadmin/              # Admin management app
│  │  ├─ models.py          # Users, roles, permissions, configuration, and other models
│  │  ├─ ui.py              # Admin app UI configuration
│  │  ├─ app.py             # udadmin FastAPI sub-app
│  │  ├─ routers/           # Routes
│  │  └─ utils/             # Auth, permissions, i18n, model registration, and other utilities
│  ├─ demo/                 # Sample app
│  │  ├─ models.py          # Sample models
│  │  ├─ ui.py              # Sample model UI configuration
│  │  ├─ app.py             # demo FastAPI sub-app
│  │  └─ routers/actions.py # Custom action APIs
│  └─ db_external/          # External database sample app
│     ├─ models.py          # External database table models
│     ├─ ui.py              # External database model UI configuration
│     └─ app.py             # db_external FastAPI sub-app
├─ config/
│  ├─ settings.py           # Default configuration
│  └─ local_settings.py     # Optional local override configuration
├─ db/
│  ├─ db.sqlite3            # Default SQLite database
│  └─ db_external.sqlite3   # External database sample SQLite database
├─ front/                   # Vue frontend project
├─ locales/                 # Backend i18n resources
├─ static/
│  └─ admin/                # Frontend production build output
├─ main.py                  # Main FastAPI application
├─ run.py                   # Local development startup script
├─ init_data.py             # Test data initialization
├─ requirements.txt         # Python dependencies
└─ docker-compose.yml       # Container orchestration configuration
```

## Model Registration

Models are registered to sub-applications through `apps.udadmin.utils.model_register.mr`. After registration, corresponding CRUD APIs and frontend metadata are generated.

Example:

```python
from apps.udadmin.utils.model_register import mr
from apps.demo import models as md
from apps.demo import ui

mr.register(app, md.DetailModel, ui_info=ui.DetailModelUi)
```

Common `UiInfo` configuration:

```python
DetailModelUi = UiInfo(
    model=md.DetailModel,
    list_display=["*"],
    list_filter=["id", "boolean_field", "char_enum_field"],
    search_fields=["char_field", "text_field", "uuid_field"],
    editable_fields=["char_field", "boolean_field", "json_field"],
)
```

## Managing External Databases

Cameo can connect existing database tables to the admin interface. The repository includes `apps/db_external` as an example: `DATABASES["db_external"]` is configured in `config/settings.py`, and `apps.db_external.app:app` is registered in `REGISTERED_APPS`. This scenario follows a database-to-model workflow: the database schema already exists, SQLAlchemy models are generated manually or through reflection tools, and then registered in an independent app for CRUD management.

External databases are not managed by the main project's Alembic migrations. In production, do not run Alembic migrations against an existing business database, and do not call `Base.metadata.create_all()` or `drop_all()` for the external database during application startup. The current `init_data.py` only rebuilds `db/db_external.sqlite3` and seeds sample data for the demo environment.

Basic steps:

1. Prepare an external database, such as the built-in sample `db/db_external.sqlite3`, with existing business tables and data.
2. Add a database configuration entry to `DATABASES` in `config/settings.py`.
3. Create an independent app under `apps/`, for example `apps/db_external/`.
4. Generate or write `apps/db_external/models.py` according to the external database tables.
5. Configure `apps/db_external/ui.py`, declaring list fields, filter fields, search fields, editable fields, and so on.
6. Use `Base = get_base(database="db_external", app_name="db_external")` so models inherit the Base for the corresponding database and app. `mr.register()` will automatically use the corresponding database connection and app name.
7. Register the app in `REGISTERED_APPS` in `config/settings.py`.
8. After the external database schema changes, update `models.py` manually and do not generate migration files.

External database configuration example:

```python
# config/settings.py
import os


DATABASES = {
    "default": {
        "url": DATABASE_URL,
        "engine_options": {
            "echo": SQL_LOG,
            "connect_args": {"check_same_thread": False}
            if DATABASE_URL.startswith("sqlite")
            else {},
        },
        "managed_by_alembic": True,
    },
    "db_external": {
        "url": f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'db', 'db_external.sqlite3')}",
        "engine_options": {
            "echo": SQL_LOG,
            "connect_args": {"check_same_thread": False},
        },
        "managed_by_alembic": False,
    },
}
```

External table model example:

```python
# apps/db_external/models.py
from typing import cast

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from apps.udadmin.utils.ui_tools import FieldInfo
from apps.udadmin.utils.model_base import get_base


Base = get_base(database="db_external", app_name="db_external")


class Department(Base):
    __tablename__ = "department"

    id = Column(Integer, primary_key=True, autoincrement=True, info=FieldInfo(ui_name="ID"))
    name = Column(String(100), nullable=False, unique=True, info=FieldInfo(ui_name="Department Name"))
    code = Column(String(50), nullable=False, unique=True, info=FieldInfo(ui_name="Department Code"))
    location = Column(String(100), info=FieldInfo(ui_name="Office Location"))
    is_active = Column(Boolean, nullable=False, default=True, info=FieldInfo(ui_name="Active"))
    created_at = Column(DateTime, info=FieldInfo(ui_name="Created At"))

    employees = relationship("Employee", back_populates="department")

    def __str__(self) -> str:
        name = cast(str | None, self.name)
        return name or f"<Department: {self.id}>"

    class Meta:
        menu_name = "External Department"
        table_description = "Department table from the external database"
```

UI configuration example:

```python
# apps/db_external/ui.py
from apps.udadmin.utils.ui_tools import UiInfo
from apps.db_external import models as md


DepartmentUi = UiInfo(
    model=md.Department,
    list_display=["id", "name", "code", "location", "is_active", "created_at"],
    list_filter=["id", "is_active"],
    search_fields=["name", "code", "location"],
    editable_fields=["name", "code", "location", "is_active"],
    readonly_fields=["created_at"],
)
```

App registration example:

```python
# apps/db_external/app.py
from fastapi import FastAPI
from fastapi import exceptions as excep
from starlette.exceptions import HTTPException

from apps.db_external import models as md
from apps.db_external import ui
from apps.udadmin.utils import error_handler as eh
from apps.udadmin.utils import middleware as mw
from apps.udadmin.utils.model_register import mr
from apps.udadmin.utils.openapi_tags import openapi_tags


app = FastAPI(title="db_external", version="1.0.0", debug=True, openapi_tags=openapi_tags)

app.exception_handler(excep.RequestValidationError)(eh.RequestValidationErrorHandler)
app.exception_handler(HTTPException)(eh.HttpExceptionHandler)
app.exception_handler(eh.AppException)(eh.AppExceptionHandler)
app.middleware("http")(mw.LocaleMiddleware)
app.middleware("http")(mw.CommonExceptionHandler)

mr.register(app, md.Department, ui_info=ui.DepartmentUi)
```

Main configuration registration example:

```python
# config/settings.py
from apps.udadmin.utils.app_registry import AppReg


REGISTERED_APPS = [
    AppReg("apps.udadmin.app:app", app_icon="antd:UserOutlined"),
    AppReg("apps.demo.app:app"),
    AppReg("apps.db_external.app:app", app_icon="antd:DatabaseOutlined"),
]
```

Database selection order for a model: first read the model class's own `database`; if it is not declared, read the database name from the inherited Base; if `get_base()` does not receive a database name and the model does not declare one, use the first database connection configured in `settings.DATABASES` by default.

App selection order for a model: first read the model class's own `app_name`; if it is not declared, read the app name from the inherited Base; if the Base does not declare one, read the current mounted `AppReg.app_name`; if there is no mount context, infer from the model module path, for example `apps.db_external.models` infers `db_external`; finally infer from the table name prefix. The model's list, detail, create, edit, delete, and filter value APIs all use the final resolved database and app.

Multiple apps can use the same database. For example, `udadmin` and `demo` both use `database="default"` but use `app_name="udadmin"` and `app_name="demo"` respectively. These apps share the same database metadata, while model registration and frontend routes belong to different apps.

Notes:

- External databases do not participate in the current project's Alembic migrations.
- After an external database changes, update `apps/db_external/models.py` manually.
- The Base `app_name` should match the app registration name, such as `db_external`.
- External database models should use `get_base(database="database name", app_name="app name")` to get the corresponding `Base`, and should not inherit the default database Base.
- When relationship fields are needed, declare `ForeignKey` and `relationship` normally, but keep model definitions consistent with existing database constraints.

## Database Migrations

Generate a migration:

```bash
python -m alembic revision --autogenerate -m "change description"
```

Apply migrations:

```bash
python -m alembic upgrade head
```

Rollback one revision:

```bash
python -m alembic downgrade -1
```

## Configuration

Common configuration is located in `config/settings.py`:

- `DEBUG`, `SQL_LOG`, `LOCATE_PRINT`: debugging, SQL logging, and print location switches.
- `DATABASE_URL`: database connection URL.
- `DATABASES`: multi-database connection registry. The first item is used when `model.database` is not declared.
- `REGISTERED_APPS`: sub-application mount configuration.
- `AUTHENTICATION_BACKENDS`: authentication backends.
- `LDAP_CONFIG`: LDAP parameters.
- `SYNC_REGISTERED_MODEL_PERMISSIONS`: synchronize registered model permissions on startup.
- `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_SECONDS`, `REFRESH_TOKEN_EXPIRE_SECONDS`: JWT configuration.
- `TZ`: backend timezone, defaulting to `Asia/Shanghai`.

Local private configuration can be written to `config/local_settings.py` to override defaults.

Frontend production configuration is located in `front/.env.production`:

- `VITE_PUBLIC_PATH`: production static asset prefix, currently `/static/admin/`.
- `VITE_GLOB_API_URL`: API base URL. When blank, the current page origin is used.
- `VITE_GLOB_API_URL_PREFIX`: API prefix. When blank, no additional prefix is appended. For same-origin deployment, keep it blank to avoid packaging a fixed `localhost`.
- `VITE_BUILD_COMPRESS`: build compression mode, available values are `gzip`, `brotli`, and `none`.

## Access URLs

- Admin page: `http://localhost:3014/admin`
- Main app docs: `http://localhost:3014/docs`
- Admin app docs: `http://localhost:3014/udadmin/docs`
- Demo app docs: `http://localhost:3014/demo/docs`
- External database sample docs: `http://localhost:3014/db_external/docs`

## License

See [LICENSE](LICENSE).
