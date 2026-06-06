# Cameo 项目文档

## 项目概述

Cameo 是一个基于 FastAPI 的开源全栈管理后台框架，参考 Django-Admin 设计，采用前后端分离架构。项目提供完整的 RBAC 权限管理系统，支持自动 CRUD API 生成。

**仓库地址**: [GitHub](https://github.com/croonyy/cameo) | [Gitee](https://gitee.com/croonyy/cameo)

## 技术栈

### 后端
- **框架**: FastAPI 0.115+
- **ORM**: SQLAlchemy 2.0（异步模式）
- **数据库迁移**: Alembic
- **数据库**: SQLite（默认）、MySQL、PostgreSQL、Oracle
- **认证**: JWT + 自定义 RBAC
- **Python**: 3.13.0

### 前端
- **框架**: Vue 3.5+
- **UI 库**: Naive UI
- **状态管理**: Pinia
- **构建工具**: Vite
- **HTTP 客户端**: Alova
- **Node**: 22.14.0
- **包管理器**: pnpm

## 项目结构

```
cameo/
├── apps/                    # 应用目录
│   ├── udadmin/            # Admin 管理应用
│   │   ├── models.py       # SQLAlchemy 模型定义
│   │   ├── ui.py           # 前端 UI 配置
│   │   ├── app.py          # FastAPI 应用实例
│   │   ├── routes/         # 路由定义
│   │   ├── utils/          # 工具函数
│   │   └── types/          # 类型定义
│   └── demo/               # 示例应用
├── front/                  # 前端根目录
│   ├── src/
│   │   ├── api/           # API 客户端
│   │   ├── views/         # 页面组件
│   │   ├── router/        # 路由配置
│   │   └── store/         # 状态管理
│   ├── dist/              # 构建输出（生产环境）
│   └── package.json
├── config/
│   └── settings.py        # 项目配置文件
├── db/
│   └── db.sqlite3         # SQLite 数据库文件
├── alembic/               # 数据库迁移文件
│   └── versions/
├── static/
│   ├── dist/              # 前端构建产物（生产环境）
│   └── images/            # 静态图片资源
├── migrations/            # （已弃用）旧版迁移目录
├── main.py                # 主应用入口
├── run.py                 # 启动脚本
├── init_data.py           # 数据初始化脚本
├── requirements.txt       # Python 依赖
└── pyproject.toml         # 项目配置
```

## 核心架构

### 1. 模型注册系统

项目的核心是自动 CRUD 生成系统，基于 `ModelRegister` 单例类实现：

- **自动路由生成**: 为注册的模型自动创建增删改查 API
- **权限集成**: 与 RBAC 系统深度集成，支持细粒度权限控制
- **UI 配置**: 通过 `UiInfo` 类配置前端显示行为

```python
from apps.udadmin.utils.model_register import mr
from apps.udadmin import models as md
from apps.udadmin import ui

# 注册模型（自动生成 CRUD API）
mr.register(app, md.User, ui_info=ui.UserUi)
```

### 2. RBAC 权限系统

基于模型-权限-角色-用户的四层架构：

- **PermissionType**: 权限类型（增删改查、自定义）
- **Permission**: 权限实例，绑定到具体模型操作
- **Role**: 角色定义，聚合多个权限
- **User**: 用户，直接拥有权限或通过角色继承

权限装饰器：
```python
from apps.udadmin.utils.auth import permission_required

@permission_required("udadmin:User:create")
async def create_user(...):
    ...
```

### 3. 自定义列配置

使用 SQLAlchemy 原生 `Column` 的 `info` 参数配置前端显示信息：

```python
from sqlalchemy import Column, String

class MyModel(Base):
    __tablename__ = "mymodel"
    name = Column(String(255), comment="名称", info={"ui_name": "显示名称", "ui_order": 1})
```

## 开发指南

### 环境搭建

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 初始化数据库
alembic upgrade head

# 创建初始数据
python init_data.py

# 安装前端依赖
cd front
pnpm install
```

### 运行项目

```bash
# 启动后端（端口 3014）
python run.py

# 启动前端（端口 1992）
cd front
pnpm run dev

# 访问
# 后端文档: http://localhost:3014/udadmin/docs
# 前端页面: http://localhost:1992/
# 默认账号: admin / admin
```

### 创建新应用

1. 在 `apps/` 下创建应用目录（如 `myapp/`）
2. 创建 `myapp/models.py` 定义 SQLAlchemy 模型
3. 创建 `myapp/ui.py` 配置前端显示
4. 创建 `myapp/app.py` 定义 FastAPI 应用
5. 在 `main.py` 中注册应用和模型

```python
# main.py 生命周期中添加
import apps.myapp.models
registry.register_app("myapp", apps.myapp.models)
from apps.myapp.app import app as myapp_app
app.mount("/myapp", myapp_app, name="myapp")
```

### 数据库迁移

```bash
# 生成迁移文件
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

## 重要约定

### 命名规范
- 模型类使用 PascalCase（如 `User`）
- 表名使用小写下划线（如 `user_role`）
- 模型文件统一命名为 `models.py`
- UI 配置文件统一命名为 `ui.py`

### 模型约定
- 所有模型必须继承自 `Base`（SQLAlchemy DeclarativeBase）
- 模型必须定义 `__tablename__`
- 模型应定义 `app_name` 类属性
- 使用原生 `Column(..., info={...})` 配置前端展示元数据

### 权限约定
- 模型权限格式: `{app_name}:{model_name}:{action}`
- 预置权限类型: create, read, update, delete, list, export
- 自定义权限可扩展其他类型

## 技术债务与迁移

项目已完成从 Tortoise-ORM 到 SQLAlchemy 2.0 的迁移（2026-04），详见 [MIGRATION_PLAN.md](MIGRATION_PLAN.md)。

关键变化：
- 完全移除 Tortoise-ORM 依赖
- 使用 Alembic 替代 Aerich
- 所有异步操作使用 SQLAlchemy 2.0 风格
- 保留 API 兼容性，前端无需修改

## 生产部署

### 前端构建

```bash
cd front
pnpm run build
```

构建产物在 `front/dist/`，需复制到 `static/dist/` 并修改 API 地址配置。

### 后端部署

修改 `run.py` 中的启动参数：

```python
uvicorn.run("main:app", host="0.0.0.0", port=3014, reload=False, workers=4)
```

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # 静态文件
    location /static/ {
        alias /path/to/static/dist/;
        expires 7d;
    }

    # 前端路由
    location /admin/ {
        alias /path/to/static/dist/;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API
    location / {
        proxy_pass http://127.0.0.1:3014;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 调试与测试

### API 文档
- Swagger UI: `http://localhost:3014/udadmin/docs`
- ReDoc: `http://localhost:3014/udadmin/redoc`

### 日志
项目使用 Python 标准日志系统，可在 `config/settings.py` 中配置级别。

### 测试脚本
项目包含多个测试脚本和验证清单：
- `test/` - 测试代码目录
- `PHASE1_VERIFICATION_CHECKLIST.md` - 功能验证清单
- `create_test_data.py` - 测试数据生成

## 常见问题

### Q: 如何修改数据库类型？
A: 修改 `config/settings.py` 中的 `DATABASE_URL` 环境变量，支持 MySQL、PostgreSQL、Oracle。

### Q: 前端如何调用 API？
A: 使用 `front/src/api/` 中定义的 Alova 客户端，自动处理认证和错误。

### Q: 如何添加自定义 API？
A: 在应用的 `routes/` 目录下创建路由文件，在 `app.py` 中 `include_router`。

### Q: 权限不生效？
A: 检查：1) 权限实例是否存在 2) 用户/角色是否已赋权 3) 权限装饰器格式是否正确

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feat/xxx`)
3. 提交更改 (`git commit -m 'Add xxx'`)
4. 推送分支 (`git push origin feat/xxx`)
5. 创建 Pull Request

## 许可证

LICENSE
