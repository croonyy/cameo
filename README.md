# Cameo

<p align="center">
  <a href="#"><img src="./static/logo.svg" alt="Cameo" width="200"></a>
</p>

<p align="center">
  <strong>企业级 FastAPI 后台管理系统框架</strong>
</p>

<p align="center">
  基于 FastAPI + SQLAlchemy 2.0 + Vue 3 + Naive UI 的现代化全栈管理后台解决方案（fastapi-admin\fastapi_admin）
</p>

## 介绍

Cameo 是一个开源的企业级后台管理系统框架，包含一个fastapi-admin应用（参考 Django-Admin 设计理念），帮助开发者快速搭建专业的 Web 应用。项目采用前后端分离架构，具备以下核心特性：

- **自动 CRUD 生成** - 基于模型自动生成增删改查 API 和前端页面
- **RBAC 权限管理** - 完善的基于角色的访问控制系统
- **多数据库支持** - 支持 SQLite、MySQL、PostgreSQL、Oracle
- **现代化技术栈** - Python 3.13 + FastAPI 0.115 + Vue 3.5 + Naive UI
- **异步架构** - 全链路异步处理，高性能高并发

## 项目地址

- [GitHub](https://github.com/croonyy/cameo)
- [Gitee](https://gitee.com/croonyy/cameo)

## 效果展示

### 登录页

深色科技风登录界面，默认演示账号为 `admin/admin`，适合后台管理系统的入口场景。

![登录页](static/images/login.png)

### 主控台

登录后的主控台展示系统导航、标签页、快捷工具栏和概览面板，用于承载后台首页与运营数据入口。

![主控台](static/images/dashboard.png)

### 模型列表

基于后端模型自动生成 CRUD 列表，支持分页、排序、批量选择、行操作、列宽调整和横向滚动。

![模型列表](static/images/list.png)

### 查询过滤

列表页内置模型字段过滤区，能够按字段类型生成输入框、选择器、布尔筛选等查询控件。

![查询过滤](static/images/filter.png)

### 编辑表单

编辑页根据模型字段生成表单，覆盖数字、文本、日期、枚举、JSON 等常见字段类型。

![编辑表单](static/images/edit.png)

### 行内编辑

列表支持行内编辑模式，可在表格中直接修改枚举、布尔值等字段，减少频繁跳转表单页的操作成本。

![行内编辑](static/images/inline_edit.png)

### API 文档

后端基于 FastAPI 自动生成 Swagger API 文档，便于调试认证、CRUD 和业务接口。

![API 文档](static/images/api_docs.png)

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

## 快速开始

### 环境要求

- Python 3.13.0+
- Node.js 22.14.0+
- pnpm

### 安装

```bash
# 克隆项目
git clone https://gitee.com/croonyy/cameo.git
# 或者
git clone https://github.com/croonyy/cameo.git
cd cameo

# 安装 Python 依赖
pip install -r requirements.txt

# 初始化数据库
alembic upgrade head

# 创建初始数据（管理员账号：admin/admin）
python init_data.py

# 安装前端依赖
cd front
pnpm install
```

### 运行

```bash
# 启动后端服务（端口 3014）
python run.py

# 启动前端服务（端口 1992）
cd front
pnpm run dev
```

### 访问

- 后端 API 文档: http://localhost:3014/udadmin/docs
- 前端页面: http://localhost:1992/
- 默认账号: `admin` / `admin`
- 测试账号: `test_user` / `123456`

## 项目结构

```
cameo/
├── apps/                    # 应用目录
│   ├── udadmin/            # Admin 管理应用
│   │   ├── models.py       # SQLAlchemy 模型定义
│   │   ├── ui.py           # 前端 UI 配置
│   │   ├── app.py          # FastAPI 应用实例
│   │   ├── routes/         # 路由定义
│   │   └── utils/          # 工具函数
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
├── main.py                # 主应用入口
├── run.py                 # 启动脚本
├── init_data.py           # 数据初始化脚本
├── requirements.txt       # Python 依赖
└── pyproject.toml         # 项目配置
```

## 核心功能

### 1. 模型注册系统

基于 `ModelRegister` 单例类实现自动 CRUD 生成：

```python
from apps.udadmin.utils.model_register import mr
from apps.udadmin import models as md
from apps.udadmin import ui

# 注册模型（自动生成 CRUD API）
mr.register(app, md.User, ui_info=ui.UserUi)
```

### 2. RBAC 权限系统

四层权限架构：
- **PermissionType**: 权限类型（增删改查、自定义）
- **Permission**: 权限实例，绑定到具体模型操作
- **Role**: 角色定义，聚合多个权限
- **User**: 用户，直接拥有权限或通过角色继承

### 3. 自定义列配置

使用 SQLAlchemy 原生 `Column` 的 `info` 参数配置前端显示信息：

```python
from sqlalchemy import Column, String

class MyModel(Base):
    __tablename__ = "mymodel"
    name = Column(String(255), comment="名称", info={"ui_name": "显示名称", "ui_order": 1})
```

## 开发指南

### 创建新应用

1. **创建应用目录**

```bash
mkdir apps/myapp
```

2. **定义模型** (`apps/myapp/models.py`)

```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class MyModel(Base):
    __tablename__ = "mymodel"
    app_name = "myapp"
    
    id = Column(Integer, primary_key=True, comment="主键ID", info={"ui_name": "序号"})
    name = Column(String(255), comment="名称", info={"ui_name": "显示名称"})
```

3. **配置 UI** (`apps/myapp/ui.py`)

```python
from apps.udadmin.utils.ui_tools import UiInfo
from . import models as md

MyModelUi = UiInfo(
    model=md.MyModel,
    list_display=["id", "name"],
    list_filter=["id", "name"],
    search_fields=["name"],
)
```

4. **注册应用** (`main.py`)

```python
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

## 常见问题

### Q: 如何修改数据库类型？

修改 `config/settings.py` 中的 `DATABASE_URL` 环境变量，支持 MySQL、PostgreSQL、Oracle。

### Q: 前端如何调用 API？

使用 `front/src/api/` 中定义的 Alova 客户端，自动处理认证和错误。

### Q: 如何添加自定义 API？

在应用的 `routes/` 目录下创建路由文件，在 `app.py` 中 `include_router`。

### Q: 权限不生效？

检查：1) 权限实例是否存在 2) 用户/角色是否已赋权 3) 权限装饰器格式是否正确

## 更新日志

- **2026-05** - 优化前端显示和各种组件逻辑调整
- **2026-05** - 完成 Tortoise-ORM 到 SQLAlchemy 2.0 迁移(tortoise-orm:c0b69f38)
- **2026-04** - 重构权限系统，优化模型注册机制
- **2026-02** - 前端迁移至 Vue 3 + Naive UI

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feat/xxx`)
3. 提交更改 (`git commit -m 'Add xxx'`)
4. 推送分支 (`git push origin feat/xxx`)
5. 创建 Pull Request

## 许可证

[LICENSE](LICENSE)

## 联系方式

- 问题反馈: [GitHub Issues](https://github.com/croonyy/cameo/issues)
- 邮箱: 799671622@qq.com

---

<p align="center">
  <strong>如果这个项目对你有帮助，请给一个 ⭐️ Star 支持一下</strong>
</p>
