# Cameo

<p align="center">
  <a href="#"><img src="./static/logo1.svg" alt="Cameo" width="200"></a>
</p>

<p align="center">
  <strong>基于 FastAPI、SQLAlchemy 2.0、Vue 3 和 Naive UI 的后台管理框架</strong>
</p>

## 简介

Cameo 是一个前后端分离的后台管理系统框架。后端使用 FastAPI 和 SQLAlchemy 2.0，前端使用 Vue 3、Vite、Naive UI 和 pnpm。项目内置 `udadmin` 管理应用，并提供 `demo` 示例应用，用于展示模型注册、自动 CRUD、权限控制、字段类型、关系字段和自定义动作。

核心能力：

- 自动 CRUD：注册 SQLAlchemy 模型后生成列表、详情、新增、编辑、删除等接口和页面。
- RBAC 权限：内置用户、角色、权限类型、权限实例和操作记录。
- 模型 UI 配置：通过 `UiInfo`、`FieldInfo` 配置列表列、筛选项、搜索项、可编辑字段和自定义动作。
- 国际化：后端 `locales/zh.yml`、`locales/en.yml` 和前端 `front/src/i18n` 协同提供中英文显示。
- Demo App：覆盖外键、一对一、多对多、枚举、JSON、日期、布尔、数字、文本等常见模型场景。
- Docker Compose：支持容器内前端打包，并用 Python slim 镜像启动后端服务。

## 项目地址

- GitHub: https://github.com/croonyy/cameo
- Gitee: https://gitee.com/croonyy/cameo

## 技术栈

后端：

- FastAPI
- SQLAlchemy 2.0 async
- Alembic
- SQLite 默认数据库，可按 `DATABASE_URL` 切换 MySQL 或 PostgreSQL
- JWT 认证
- 数据库认证和 LDAP 认证后端

前端：

- Vue 3
- Vite
- Naive UI
- Pinia
- Alova
- pnpm 10.5.0
- Node.js 22

## 应用结构

当前主应用在 `main.py` 中挂载子应用：

- `/udadmin`：后台管理应用，包含用户、角色、权限、配置、操作记录等管理模型。
- `/demo`：示例应用，展示自动 CRUD 和复杂字段/关系。
- `/static`：静态资源目录，前端生产构建产物位于 `static/admin`。
- `/admin`：后台前端入口，生产构建后由后端直接返回 `static/admin/index.html`。

`config/settings.py` 中的 `REGISTERED_APPS` 控制挂载应用：

```python
from apps.udadmin.utils.app_registry import AppReg

REGISTERED_APPS = [
    AppReg("apps.udadmin.app:app", app_icon="antd:UserOutlined"),
    AppReg(app_path="apps.demo.app:app"),
]
```

`AppReg` 支持四个参数：

- `app_path`：FastAPI app 导入路径，必填，例如 `AppReg("apps.udadmin.app:app")` 或 `AppReg(app_path="apps.demo.app:app")`。
- `router_prefix`：挂载路径，默认 `/<app 目录名>`，例如 `/udadmin`、`/demo`。
- `name`：注册名称，默认 app 目录名。
- `app_icon`：前端应用图标，默认 `antd:AppstoreOutlined`。

## Demo App

`apps/demo` 提供三个示例模型：

- `ForeignKeyModel`：外键目标模型，用于测试一对多关系。
- `RelationModel`：关系模型，用于测试一对一和多对多关系。
- `DetailModel`：明细模型，覆盖 BigInteger、LargeBinary、Boolean、Enum、String、Date、DateTime、Numeric、Float、Integer、JSON、Text、Time、ForeignKey、relationship 等字段。

`apps/demo/ui.py` 展示了模型 UI 配置：

- `list_display=["*"]` 显示全部字段。
- `list_filter` 配置筛选字段。
- `search_fields` 配置搜索字段。
- `editable_fields` 配置行内编辑字段。
- `custom_actions` 配置行级和工具栏自定义动作。

`apps/demo/routers/actions.py` 提供自定义动作接口，并通过 `permission_required` 绑定权限，例如：

- `/demo/actions/detail/preview_row`
- `/demo/actions/detail/preview_record`
- `/demo/actions/detail/show_context`
- `/demo/actions/detail/show_records`

## 本地开发

### 环境要求

- Python 3.12+
- Node.js 22+
- pnpm 10.5.0

### 初始化

```bash
pip install -r requirements.txt
python -m alembic upgrade head
python init_data.py
```

`init_data.py` 会重建默认 SQLite 数据库并写入测试数据，包括用户、角色、权限、配置、操作记录和 demo 数据。

常用账号：

- `admin` / `admin`
- `test_user` / `123456`
- `demo_user` / `123456`
- `empty_user` / `123456`

### 启动后端

```bash
python run.py
```

本地开发脚本默认监听：

```text
http://localhost:3014
```

### 启动前端开发服务

```bash
cd front
corepack enable
corepack prepare pnpm@10.5.0 --activate
pnpm install
pnpm run dev
```

前端开发服务端口以 Vite 配置为准。生产构建时前端会输出到 `static/admin`。

## Docker Compose

项目根目录提供 `docker-compose.yml`，包含两个服务：

- `frontend-build`：使用 `node:22-alpine` 安装依赖并执行前端打包。
- `backend`：使用 `python:3.12-slim` 构建并运行后端，暴露 `3014` 端口。

### 前端打包

```bash
docker compose run --rm frontend-build
```

说明：

- `--rm` 会在打包结束后删除前端构建容器。
- 前端产物保留在宿主机 `static/admin`。
- `node_modules` 和 pnpm store 使用 Docker volume 缓存，不写入宿主机源码目录。

### 启动后端

```bash
docker compose up -d --build backend
```

启动后访问：

```text
http://localhost:3014
http://localhost:3014/admin
http://localhost:3014/docs
http://localhost:3014/udadmin/docs
http://localhost:3014/demo/docs
```

日常启动已构建过的后端镜像时可以使用：

```bash
docker compose up -d backend
```

代码或依赖变更后再重新构建：

```bash
docker compose up -d --build backend
```

### 完整容器流程

```bash
docker compose run --rm frontend-build
docker compose up -d --build backend
```

如果需要查看日志：

```bash
docker compose logs -f backend
```

如果需要停止服务：

```bash
docker compose down
```

## 目录结构

```text
cameo/
├─ apps/
│  ├─ udadmin/              # 后台管理应用
│  │  ├─ models.py          # 用户、角色、权限、配置等模型
│  │  ├─ ui.py              # 管理应用 UI 配置
│  │  ├─ app.py             # udadmin FastAPI 子应用
│  │  ├─ routers/           # 路由
│  │  └─ utils/             # 认证、权限、国际化、模型注册等工具
│  └─ demo/                 # 示例应用
│     ├─ models.py          # 示例模型
│     ├─ ui.py              # 示例模型 UI 配置
│     ├─ app.py             # demo FastAPI 子应用
│     └─ routers/actions.py # 自定义动作接口
├─ config/
│  ├─ settings.py           # 默认配置
│  └─ local_settings.py     # 本地覆盖配置，可选
├─ db/
│  └─ db.sqlite3            # 默认 SQLite 数据库
├─ front/                   # Vue 前端工程
├─ locales/                 # 后端国际化资源
├─ static/
│  └─ admin/                # 前端生产构建产物
├─ main.py                  # 主 FastAPI 应用
├─ run.py                   # 本地开发启动脚本
├─ init_data.py             # 初始化测试数据
├─ requirements.txt         # Python 依赖
└─ docker-compose.yml       # 容器编排配置
```

## 模型注册

模型通过 `apps.udadmin.utils.model_register.mr` 注册到子应用，注册后会生成对应 CRUD API 和前端所需元数据。

示例：

```python
from apps.udadmin.utils.model_register import mr
from apps.demo import models as md
from apps.demo import ui

mr.register(app, md.DetailModel, ui_info=ui.DetailModelUi)
```

`UiInfo` 常用配置：

```python
DetailModelUi = UiInfo(
    model=md.DetailModel,
    list_display=["*"],
    list_filter=["id", "boolean_field", "char_enum_field"],
    search_fields=["char_field", "text_field", "uuid_field"],
    editable_fields=["char_field", "boolean_field", "json_field"],
)
```

## 数据库迁移

生成迁移：

```bash
python -m alembic revision --autogenerate -m "change description"
```

执行迁移：

```bash
python -m alembic upgrade head
```

回滚一版：

```bash
python -m alembic downgrade -1
```

## 配置说明

常用配置位于 `config/settings.py`：

- `DATABASE_URL`：数据库连接地址。
- `REGISTERED_APPS`：子应用挂载配置。
- `AUTHENTICATION_BACKENDS`：认证后端。
- `LDAP_CONFIG`：LDAP 参数。
- `SYNC_REGISTERED_MODEL_PERMISSIONS`：启动时同步已注册模型权限。
- `SECRET_KEY`、`ACCESS_TOKEN_EXPIRE_SECONDS`、`REFRESH_TOKEN_EXPIRE_SECONDS`：JWT 配置。

本地私有配置可写入 `config/local_settings.py` 覆盖默认值。

## 访问入口

- 后台页面：`http://localhost:3014/admin`
- 主应用文档：`http://localhost:3014/docs`
- 管理应用文档：`http://localhost:3014/udadmin/docs`
- Demo 应用文档：`http://localhost:3014/demo/docs`

## License

见 [LICENSE](LICENSE)。
