"""SQLAlchemy models for demo."""

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    JSON,
    LargeBinary,
    Numeric,
    SmallInteger,
    String,
    Table,
    Text,
    Time,
)
from sqlalchemy.orm import relationship

from apps.udadmin.utils.ui_tools import FieldInfo
from db.sa import Base

app_name = "demo"


detail_relation = Table(
    "detail_relation",
    Base.metadata,
    Column(
        "detail_id",
        Integer,
        ForeignKey("detailmodel.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "relation_id",
        Integer,
        ForeignKey("relationmodel.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class ForeignKeyModel(Base):
    __tablename__ = "foreignkeymodel"
    app_name = app_name

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        info=FieldInfo(ui_name="序号", ui_align="M"),
    )
    name = Column(
        String(100),
        nullable=False,
        unique=True,
        info=FieldInfo(ui_name="名称", ui_align="L"),
    )
    code = Column(
        String(50), nullable=False, unique=True, info=FieldInfo(ui_name="编码")
    )
    description = Column(Text, info=FieldInfo(ui_name="描述"))

    details = relationship(
        "DetailModel", back_populates="foreign_model", info=FieldInfo(ui_align="M")
    )

    def __str__(self):
        return str(self.name) or f"<{self.__class__.__name__}: {self.id}>"

    class Meta:
        menu_name = "外键模型"
        table_description = "用于测试外键和一对多关系"


class RelationModel(Base):
    __tablename__ = "relationmodel"
    app_name = app_name

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        info=FieldInfo(ui_name="序号", ui_align="M"),
    )
    name = Column(
        String(100),
        nullable=False,
        unique=True,
        info=FieldInfo(ui_name="名称", ui_align="L"),
    )
    category = Column(String(50), info=FieldInfo(ui_name="分类", ui_align="M"))
    remark = Column(Text, info=FieldInfo(ui_name="备注", ui_align="L"))

    one_to_one_detail = relationship(
        "DetailModel",
        back_populates="one_to_one_relation",
        uselist=False,
        foreign_keys="DetailModel.one_to_one_relation_id",
        info=FieldInfo(ui_align="M"),
    )
    many_to_many_details = relationship(
        "DetailModel",
        secondary=detail_relation,
        back_populates="many_to_many_relations",
        info=FieldInfo(ui_align="M"),
    )

    def __str__(self):
        return str(self.name) or f"<{self.__class__.__name__}: {self.id}>"

    class Meta:
        menu_name = "关系模型"
        table_description = "用于测试一对一和多对多关系"


class DetailModel(Base):
    __tablename__ = "detailmodel"
    app_name = app_name

    id = Column(
        Integer,
        primary_key=True,
        autoincrement=True,
        info=FieldInfo(ui_name="序号", ui_align="M"),
    )
    big_int_field = Column(BigInteger, info=FieldInfo(ui_name="大整数"))
    binary_field = Column(LargeBinary, info=FieldInfo(ui_name="二进制"))
    boolean_field = Column(Boolean, info=FieldInfo(ui_name="布尔类型"))
    char_enum_field = Column(
        Enum("option1", "option2", "option3"), info=FieldInfo(ui_name="字符枚举")
    )
    char_field = Column(String(255), info=FieldInfo(ui_name="字符串", ui_align="L"))
    date_field = Column(Date, info=FieldInfo(ui_name="日期"))
    date_time_field = Column(DateTime, info=FieldInfo(ui_name="日期时间"))
    decimal_field = Column(Numeric(10, 2), info=FieldInfo(ui_name="小数"))
    float_field = Column(Float, info=FieldInfo(ui_name="浮点数"))
    int_enum_field = Column(
        Integer,
        info=FieldInfo(ui_name="整数枚举", choices={"ONE": 1, "TWO": 2, "THREE": 3}),
    )
    int_field = Column(Integer, info=FieldInfo(ui_name="整数"))
    json_field = Column(JSON, info=FieldInfo(ui_name="JSON", ui_align="L"))
    small_integer_field = Column(SmallInteger, info=FieldInfo(ui_name="小整数"))
    text_field = Column(Text, info=FieldInfo(ui_name="长文本", ui_align="L"))
    time_field = Column(Time, info=FieldInfo(ui_name="时间"))
    time_delta_field = Column(Integer, info=FieldInfo(ui_name="时间间隔秒"))
    uuid_field = Column(String(36), info=FieldInfo(ui_name="UUID"))

    foreign_model_id = Column(
        Integer, ForeignKey("foreignkeymodel.id"), info=FieldInfo(ui_name="外键模型")
    )
    one_to_one_relation_id = Column(
        Integer,
        ForeignKey("relationmodel.id"),
        unique=True,
        info=FieldInfo(ui_name="一对一关系"),
    )

    foreign_model = relationship(
        "ForeignKeyModel", back_populates="details", info=FieldInfo(ui_align="M")
    )
    one_to_one_relation = relationship(
        "RelationModel",
        back_populates="one_to_one_detail",
        foreign_keys=[one_to_one_relation_id],
        info=FieldInfo(ui_align="M"),
    )
    many_to_many_relations = relationship(
        "RelationModel",
        secondary=detail_relation,
        back_populates="many_to_many_details",
        info=FieldInfo(ui_align="M"),
    )

    def __str__(self):
        return str(self.char_field) or f"<{self.__class__.__name__}: {self.id}>"

    class Meta:
        menu_name = "明细模型"
        table_description = "覆盖常用数据库字段类型并测试全部关系"
