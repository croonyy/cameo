"""SQLAlchemy models for udadmin app."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    Table,
    func,
)
from sqlalchemy.orm import relationship

from apps.udadmin.utils.ui_tools import FieldInfo
from db.sa import Base

app_name = "udadmin"

# M2M Association Tables
user_role = Table(
    "user_role",
    Base.metadata,
    Column(
        "user_id", Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "role_id", Integer, ForeignKey("role.id", ondelete="CASCADE"), primary_key=True
    ),
)

user_permission = Table(
    "user_permission",
    Base.metadata,
    Column(
        "user_id", Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "permission_id",
        Integer,
        ForeignKey("permission.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

role_permission = Table(
    "role_permission",
    Base.metadata,
    Column(
        "role_id", Integer, ForeignKey("role.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "permission_id",
        Integer,
        ForeignKey("permission.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class DtBase(Base):
    __abstract__ = True
    created_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=True,
        info=FieldInfo(ui_name="创建时间", ui_order=998),
    )
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
        info=FieldInfo(ui_name="更新时间", ui_order=999),
    )


class User(DtBase):
    __tablename__ = "user"
    app_name = "udadmin"
    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        info=FieldInfo(ui_name="用户ID", ui_order=1),
    )
    username = Column(
        String(255),
        unique=True,
        nullable=False,
        info=FieldInfo(ui_name="账号", ui_order=2),
    )
    password = Column(
        String(255), nullable=False, info=FieldInfo(ui_name="密码", ui_order=3)
    )
    gender = Column(
        String(50), default="男", info=FieldInfo(ui_name="性别", ui_order=4)
    )
    cn_name = Column(
        String(255), nullable=True, info=FieldInfo(ui_name="中文名", ui_order=5)
    )
    is_delete = Column(
        Boolean, default=False, info=FieldInfo(ui_name="是否删除", ui_order=6)
    )
    last_login = Column(
        DateTime, nullable=True, info=FieldInfo(ui_name="最后登录", ui_order=7)
    )
    is_superuser = Column(
        Boolean, default=False, info=FieldInfo(ui_name="超级管理员", ui_order=8)
    )
    is_active = Column(
        Boolean, default=True, info=FieldInfo(ui_name="活动状态", ui_order=9)
    )
    roles = relationship(
        "Role",
        secondary=user_role,
        back_populates="users",
        lazy="selectin",
        info=FieldInfo(ui_name="角色", ui_page_size=30),
    )
    permissions = relationship(
        "Permission", secondary=user_permission, back_populates="users", lazy="selectin"
    )
    operations = relationship("Record", back_populates="user", lazy="selectin")

    def __str__(self):
        return f"{self.id} | {getattr(self.Meta, 'menu_name', self.__class__.__name__)} | {self.username}"

    class Meta:
        menu_name = "用户管理"
        icon = "antd:TeamOutlined"
        table_description = "用户表"


class Role(DtBase):
    __tablename__ = "role"
    app_name = "udadmin"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    extra = Column(JSON, nullable=True)
    permissions = relationship(
        "Permission", secondary=role_permission, back_populates="roles", lazy="selectin"
    )
    users = relationship(
        "User", secondary=user_role, back_populates="roles", lazy="selectin"
    )

    def __str__(self):
        return f"{self.id} | {getattr(self.Meta, 'menu_name', self.__class__.__name__)} | {self.name}"

    class Meta:
        menu_name = "角色管理"
        icon = "antd:StarOutlined"
        table_description = "角色表"


class PermissionType(DtBase):
    __tablename__ = "permissiontype"
    app_name = "udadmin"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    extra = Column(JSON, nullable=True)
    permissions = relationship(
        "Permission", back_populates="permission_type", lazy="selectin"
    )

    def __str__(self):
        return f"{self.id} | {getattr(self.Meta, 'menu_name', self.__class__.__name__)} | {self.name}"

    class Meta:
        menu_name = "权限类型"
        icon = "antd:TagFilled"
        table_description = "权限类型表"


class Permission(DtBase):
    __tablename__ = "permission"
    app_name = "udadmin"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    permission_type_id = Column(
        Integer, ForeignKey("permissiontype.id", ondelete="CASCADE")
    )
    extra = Column(JSON, nullable=True)
    permission_type = relationship(
        "PermissionType", back_populates="permissions", lazy="selectin"
    )
    roles = relationship(
        "Role", secondary=role_permission, back_populates="permissions", lazy="selectin"
    )
    users = relationship(
        "User", secondary=user_permission, back_populates="permissions", lazy="selectin"
    )

    def __str__(self):
        return f"{self.id} | {getattr(self.Meta, 'menu_name', self.__class__.__name__)} | {self.name}"

    class Meta:
        menu_name = "权限实例"
        icon = "antd:TagsFilled"
        table_description = "权限表"


class ConfigType(DtBase):
    __tablename__ = "configtype"
    app_name = "udadmin"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    extra = Column(JSON, nullable=True)
    configs = relationship("Config", back_populates="config_type", lazy="selectin")

    def __str__(self):
        return f"{self.id} | {getattr(self.Meta, 'menu_name', self.__class__.__name__)} | {self.name}"

    class Meta:
        menu_name = "配置类型管理"
        icon = "antd:BuildFilled"
        table_description = "配置类型表"


class Config(DtBase):
    __tablename__ = "config"
    app_name = "udadmin"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    config_type_id = Column(Integer, ForeignKey("configtype.id", ondelete="CASCADE"))
    params = Column(JSON, nullable=True)
    extra = Column(JSON, nullable=True)
    config_type = relationship("ConfigType", back_populates="configs", lazy="selectin")

    def __str__(self):
        return f"{self.id} | {getattr(self.Meta, 'menu_name', self.__class__.__name__)} | {self.name}"

    class Meta:
        menu_name = "配置管理"
        icon = "antd:SettingFilled"
        table_description = "配置表"


class Record(DtBase):
    __tablename__ = "record"
    app_name = "udadmin"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=True)
    info = Column(JSON, nullable=True)
    extra = Column(JSON, nullable=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    operate_time = Column(
        DateTime,
        server_default=func.now(),
        nullable=True,
        info=FieldInfo(ui_name="操作时间"),
    )
    user = relationship("User", back_populates="operations", lazy="selectin")

    def __str__(self):
        return f"{self.id} | {getattr(self.Meta, 'menu_name', self.__class__.__name__)} | {self.name}"

    class Meta:
        menu_name = "操作记录"
        icon = "antd:ToolOutlined"
        table_description = "操作记录表"
