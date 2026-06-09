# AGENT.md

## Project Overview

Cameo is a FastAPI + SQLAlchemy 2.0 + Vue 3 admin framework inspired by Django Admin. The backend exposes a main FastAPI app and mounted sub-apps, while the frontend is a Vite/Naive UI single-page admin console.

Primary capabilities:

- Automatic CRUD API generation from registered SQLAlchemy models.
- RBAC with users, roles, permissions, and permission types.
- Async SQLAlchemy database access with Alembic migrations.
- Vue 3 admin UI with Pinia, Vue Router, Naive UI, Alova, and ECharts.

## Repository Layout

- `main.py`: Main FastAPI application. Initializes the database, mounts sub-apps, serves static assets, and redirects `/` to `/admin`.
- `run.py`: Local backend startup script. Runs `main:app` on `localhost:3014` with reload enabled.
- `config/settings.py`: Runtime settings, database URL, auth settings, app metadata, timezone, language, and optional `local_settings.py` override.
- `db/sa.py`: Async SQLAlchemy engine/session setup, declarative `Base`, database dependency, and create/dispose helpers.
- `apps/udadmin/`: Core admin app, RBAC models, security routes, model registration utilities, response/error/auth helpers, and UI metadata.
- `apps/demo/`: Example/test app with `TestModel` and generated CRUD routes.
- `alembic/`: Active database migration environment. It auto-imports `apps/*/models.py`.
- `migrations/`: Legacy/unused migration directory.
- `front/`: Vue 3 frontend project.
- `static/`: Backend-served static assets and production frontend output under `static/dist/`.
- `test/`: Python test and inspection scripts.
- `draft/` and `notes/`: Design notes, migration notes, and experiments. Treat as reference unless the task targets them.

## Backend Stack

- Python 3.13 expected by project docs.
- FastAPI, Starlette, Uvicorn.
- SQLAlchemy 2.0 async ORM.
- Alembic for migrations.
- SQLite by default: `sqlite+aiosqlite:///db/db.sqlite3`.
- Optional database drivers are listed in `requirements.txt` for MySQL, PostgreSQL, Oracle, and ODBC.
- JWT-based authentication and custom RBAC live under `apps/udadmin/utils/`.

## Frontend Stack

- Vue 3.5, TypeScript, Vite.
- Naive UI for components.
- Pinia for state.
- Vue Router.
- Alova for HTTP.
- ECharts for charts.
- pnpm is the package manager.

Important frontend paths:

- `front/src/api/`: API clients.
- `front/src/views/crud/`: Generic CRUD UI.
- `front/src/router/`: Route definitions and guards.
- `front/src/store/`: Pinia stores.
- `front/src/components/`: Shared components.
- `front/vite.config.ts`: Vite config. Uses `@` alias for `front/src/` and `/#/` for `front/types/`.

## Common Commands

Backend setup:

```bash
pip install -r requirements.txt
alembic upgrade head
python init_data.py
```

Run backend:

```bash
python run.py
```

Backend URLs:

- API docs: `http://localhost:3014/udadmin/docs`
- ReDoc: `http://localhost:3014/udadmin/redoc`
- Admin entry: `http://localhost:3014/admin`

Frontend setup and development:

```bash
cd front
pnpm install
pnpm run dev
```

Frontend production build:

```bash
cd front
pnpm run build
```

Frontend scripts:

- `pnpm run dev`: Vite dev server.
- `pnpm run build`: Vite build plus post-build script.
- `pnpm run lint:eslint`: ESLint with fixes.
- `pnpm run lint:prettier`: Prettier write.
- `pnpm run lint:stylelint`: Stylelint with fixes.

Database migrations:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
alembic downgrade -1
```

Tests:

```bash
pytest
```

Some files under `test/` are inspection scripts rather than conventional pytest tests; inspect before assuming they are stable automated tests.

## Backend Architecture Notes

`main.py` creates the root FastAPI app and uses a lifespan handler to:

1. Initialize the database with `init_db()`.
2. Import and mount `apps.udadmin.app` at `/udadmin`.
3. Import and mount `apps.demo.app` at `/demo`.
4. Print registered models from the singleton model register.
5. Dispose the database engine on shutdown.

Each sub-app is responsible for:

- Creating its own `FastAPI` instance.
- Registering exception handlers/middleware as needed.
- Including custom routers.
- Registering models through `apps.udadmin.utils.model_register.mr`.

Model registration generates routes under `/models/<model_name>` by default:

- `POST /models/<model>` create.
- `DELETE /models/<model>/{id}` delete.
- `PUT /models/<model>/{id}` update.
- `GET /models/<model>/{id}` read.
- `POST /models/<model>/list` list with pagination/filtering.
- `POST /models/<model>/rel_manage` relationship management when relationships exist.

The model register also adds model metadata endpoints once per router:

- `GET /get_all_models_info`
- `POST /get_allow_model_info`
- `POST /get_filter_fields_distinct_values`

## Model Conventions

- Models live in `apps/<app_name>/models.py`.
- All models should inherit from the Base returned by `apps.udadmin.utils.model_base.get_base(...)` or an abstract subclass of it.
- Set `__tablename__` explicitly.
- Set `app_name` on each model or module so generated permission/model keys are stable.
- Use SQLAlchemy 2.0-compatible patterns.
- Put UI-facing metadata in `Column(..., info={...})` and/or a `Meta` inner class.
- Relationship fields should use `lazy="selectin"` when they are intended for async API serialization.
- If adding a new app, make sure Alembic can import `apps.<app>.models` and `main.py` mounts the app if it needs runtime routes.

Existing registered models:

- `apps.udadmin.models`: `User`, `PermissionType`, `Permission`, `Role`, `Record`, `Config`, `ConfigType`.
- `apps.demo.models`: `TestModel`.

## RBAC Notes

- Permissions are checked with `apps.udadmin.utils.auth.permission_required`.
- Generated model permissions use permission type `model`.
- Generated permission names follow this shape: `<app_name>:<model_name>:<action>`.
- Common generated actions come from `apps.udadmin.utils.model_tools.model_perms`.
- Superusers are allowed to access all registered models.
- Non-superusers are allowed through direct user permissions and role permissions.

## Database Notes

- `config/settings.py` controls `DATABASE_URL`.
- `config/local_settings.py` can override settings and is imported opportunistically.
- `apps.udadmin.utils.model_base.get_db_dependency()` yields an `AsyncSession`, commits on success, rolls back on error, and closes the session.
- `init_db()` calls `Base.metadata.create_all`; migrations are still managed by Alembic.
- `alembic/env.py` imports every `apps/*/models.py` file before reading `Base.metadata`.

Be careful when changing models:

- Add or update Alembic migrations for schema changes.
- Keep association table names stable unless the migration handles existing data.
- Avoid changing generated permission names casually; they are likely stored in the database.

## Frontend Architecture Notes

The frontend is a Vite application served in development by `pnpm run dev` and in production through backend static files.

Key conventions:

- Use `@/` for imports from `front/src/`.
- Keep CRUD-specific logic in `front/src/views/crud/`.
- Use existing API client patterns in `front/src/api/`.
- Use existing Naive UI and project component patterns before adding new UI abstractions.
- Route definitions and route guards live in `front/src/router/`.
- App state should use existing Pinia stores under `front/src/store/`.

When changing CRUD behavior, inspect both sides:

- Backend: `apps/udadmin/utils/model_register.py`, `model_tools.py`, `orm_tools.py`, `pmodels.py`, and model UI metadata.
- Frontend: `front/src/views/crud/List.vue`, `Create.vue`, `Edit.vue`, `formData.ts`, `filterData.ts`, `fieldInfo.ts`, `cmpsForm.ts`, `cmpsFilter.ts`, `columnRender.ts`, and `relationChanges.ts`.

## Internationalization And Encoding

- Backend translation files live under root-level `locales/zh.yml` and `locales/en.yml`.
- Frontend translation files live under `front/src/i18n/resources/zh-CN.json` and `front/src/i18n/resources/en-US.json`.
- The project contains Chinese text in comments, metadata, YAML, and JSON translation files.
- On Windows PowerShell, plain `Get-Content` may display UTF-8 Chinese as mojibake depending on console encoding. Do not rewrite files just to fix terminal display.
- Preserve existing file encodings and only edit text that is relevant to the task.

## Agent Working Rules

- Read existing local patterns before editing; this project has custom model/UI/permission conventions.
- Keep changes narrowly scoped to the requested behavior.
- Do not touch `db/db.sqlite3` unless the user explicitly asks for data changes or a migration/test needs it.
- Do not reintroduce gettext `.po/.mo` catalogs; the current i18n implementation uses YAML resources.
- Avoid unrelated formatting churn, especially in large Vue files and generated lock files.
- Treat `front/pnpm-lock.yaml` as authoritative; do not edit `front/pnpm-lock copy.yaml` unless specifically requested.
- Do not revert user changes in a dirty worktree.
- Prefer `rg`/`rg --files` for search.
- Use Alembic for schema changes; do not rely only on `create_all`.
- After backend changes, run the narrowest useful Python checks or tests.
- After frontend changes, run the narrowest useful pnpm lint/build check available for the touched area.

## Useful Inspection Targets

For backend CRUD and model metadata issues:

- `apps/udadmin/utils/model_register.py`
- `apps/udadmin/utils/model_tools.py`
- `apps/udadmin/utils/orm_tools.py`
- `apps/udadmin/utils/ui_tools.py`
- `apps/udadmin/utils/pmodels.py`

For auth and permissions:

- `apps/udadmin/utils/auth.py`
- `apps/udadmin/routes/security.py`
- `apps/udadmin/models.py`

For app startup and routing:

- `main.py`
- `run.py`
- `apps/udadmin/app.py`
- `apps/demo/app.py`

For frontend CRUD:

- `front/src/views/crud/List.vue`
- `front/src/views/crud/Create.vue`
- `front/src/views/crud/Edit.vue`
- `front/src/api/crud/models.ts`

