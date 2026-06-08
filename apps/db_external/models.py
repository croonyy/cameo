"""Reverse-engineered models for db/db_external.sqlite3.

These models map existing database tables. Schema changes should be made in the
database first, then reflected here manually.
"""

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from apps.udadmin.utils.ui_tools import FieldInfo
from db.sa_external import Base


app_name = "db_external"


class Department(Base):
    __tablename__ = "department"
    app_name = app_name

    id = Column(Integer, primary_key=True, autoincrement=True, info=FieldInfo(ui_name="ID", ui_align="M"))
    name = Column(String(100), nullable=False, unique=True, info=FieldInfo(ui_name="部门名称", ui_align="L"))
    code = Column(String(50), nullable=False, unique=True, info=FieldInfo(ui_name="部门编码", ui_align="M"))
    location = Column(String(100), info=FieldInfo(ui_name="办公地点", ui_align="L"))
    is_active = Column(Boolean, nullable=False, default=True, info=FieldInfo(ui_name="启用"))
    created_at = Column(DateTime, info=FieldInfo(ui_name="创建时间"))

    employees = relationship("Employee", back_populates="department", info=FieldInfo(ui_align="M"))

    def __str__(self):
        return self.name or f"<Department: {self.id}>"

    class Meta:
        menu_name = "外部部门"
        table_description = "外部数据库中的部门表"


class Employee(Base):
    __tablename__ = "employee"
    app_name = app_name

    id = Column(Integer, primary_key=True, autoincrement=True, info=FieldInfo(ui_name="ID", ui_align="M"))
    department_id = Column(Integer, ForeignKey("department.id"), info=FieldInfo(ui_name="所属部门"))
    name = Column(String(100), nullable=False, info=FieldInfo(ui_name="员工姓名", ui_align="L"))
    email = Column(String(120), unique=True, info=FieldInfo(ui_name="邮箱", ui_align="L"))
    age = Column(Integer, info=FieldInfo(ui_name="年龄", ui_align="R"))
    salary = Column(Numeric(12, 2), info=FieldInfo(ui_name="薪资", ui_align="R"))
    hired_on = Column(Date, info=FieldInfo(ui_name="入职日期"))
    is_active = Column(Boolean, nullable=False, default=True, info=FieldInfo(ui_name="在职"))
    bio = Column(Text, info=FieldInfo(ui_name="简介", ui_align="L"))

    department = relationship("Department", back_populates="employees", info=FieldInfo(ui_align="M"))

    def __str__(self):
        return self.name or f"<Employee: {self.id}>"

    class Meta:
        menu_name = "外部员工"
        table_description = "外部数据库中的员工表"
