# fastapi keycloak integration
https://stackoverflow.com/questions/76921747/integrate-keycloak-with-fastapi/77186511#77186511

# naive-ui-admin
https://docs.naiveadmin.com/guide/introduction.html

# pypi
https://pypi.org/

# Tortoise ORM
官方文档 https://tortoise.github.io/
https://blog.csdn.net/D_ASH/article/details/140390651 
# aerich==0.7.2   aerich==0.8.0（执行完命令不退出）


# pydantic doc
https://pydantic.com.cn/
https://docs.pydantic.dev/2.7/

# fastapi
https://fastapi.tiangolo.com/
https://fastapi.tiangolo.com/zh/

# Chroma
https://docs.trychroma.com/


# mysql 允许远程登录
切换到系统数据库
use mysql；

创建用户或更新用户密码：
使用 CREATE USER（如果用户不存在）或 ALTER USER（如果用户已存在）来设置或更新密码。
CREATE USER 'root'@'%' IDENTIFIED BY '123456';  
-- 或者如果用户已存在，使用  
ALTER USER 'root'@'%' IDENTIFIED BY '123456';

使用 GRANT 语句来授予权限。
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;

修改密码加密方式
ALTER USER 'username'@'hostname' IDENTIFIED WITH mysql_native_password BY '123456';

刷新信息
FLUSH PRIVILEGES;


# 安装orm依赖
 pip install fastapi tortoise-orm aerich aiomysql


# 迁移命令
1、安装aerich工具
pip install aerich
2、初始化配置，初始化一次即可,会生成pyproject.toml文件
aerich init -t config.settings.TORTOISE_ORM
3、初始化数据库生成数据表和migrations文件, 要删除掉migrations下对应的app的文件夹，命令会重新生成，否则会报错
aerich init-db
4、修改models的数据之后重新生成迁移文件
aerich migrate
5、将迁移文件写入数据库中
aerich upgrade
6、回退到上一个版本
aerich downgrade
7、查看迁移记录

# 重建数据库 （没有数据库）
1、如果没有pyproject.toml 文件，需要先初始化aerich init -t config.settings.TORTOISE_ORM 生成pyproject.toml文件
2、如果有migrations文件夹，直接aerich upgrade 即可生成所有的数据库表
3、如果没有migrations文件夹，需要先aerich init-db 生成migrations文件夹，然后aerich migrate 生成所有的数据库表




# 多个数据库
aerich --app=demo init-db

# git 文件名大小写敏感设置
git config --global core.ignorecase false

# gitcode
https://gitcode.com/



# 定义枚举类型

    class Gander(Enum):
        male = "男"
        female = "女"



    class Operate(Enum):
        default = "default"
        add = "add"
        delete = "delete"
        update = "update"
        query = "query"

# 数据库配置
```python
TORTOISE_ORM = {
    "connections": {
        # "default": {
        "conn1": {
            # 'engine': 'tortoise.backends.asyncpg',  PostgreSQL
            "engine": "tortoise.backends.mysql",  # MySQL or Mariadb
            "credentials": {
                "host": "localhost",
                "port": "3306",
                "user": "root",
                "password": "123456",
                "database": "cameo",
                "minsize": 1,
                "maxsize": 5,
                "charset": "utf8mb4",
                "echo": True,
            },
        },
    },
    "apps": {
        "demo": {
            # 'models': ['apps.models', "aerich.models"],
            "models": ["models.models", "aerich.models"],
            "default_connection": "conn1",
        }
    },
    "use_tz": False,
    "timezone": "Asia/Shanghai",
}




 r.get("/test", tags=["ud_tag"])(viewtest.test1)
```



## 代码片段
```python

# 执行原生sql
sql = f"SELECT DISTINCT {fields_str} FROM {md.User._meta.db_table}"
affected_rows, rows_list = await md.User._meta.db.execute_query(sql)


@app.on_event("startup")
async def startup_event():
    # 传递 TORTOISE_ORM 配置给 Tortoise.init()
    await Tortoise.init(
        config=TORTOISE_ORM,
        # generate_schemas=True,
        # add_exception_handlers=True,
    )
    # 确保所有的模型都被创建（如果需要）
    await Tortoise.generate_schemas()


@app.on_event("shutdown")
async def shutdown_event():
    await Tortoise.close_connections()


class SingletonTest(Object):

    # 单例模式
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = object.__new__(cls)
        return cls._instance



sub_router = APIRouter(prefix="/sub")
router.include_router(sub_router)

    # kwargs = {
    #     "response_model":response_model,
    #     "status_code":status_code,
    #     "tags":tags,
    #     "dependencies":dependencies,
    #     "summary":summary,
    #     "description":description,
    #     "response_description":response_description,
    #     "responses":responses,
    #     "deprecated":deprecated,
    #     "methods":methods,
    #     "operation_id":operation_id,
    #     "response_model_include":response_model_include,
    #     "response_model_exclude":response_model_exclude,
    #     "response_model_by_alias":response_model_by_alias,
    #     "response_model_exclude_unset":response_model_exclude_unset,
    #     "response_model_exclude_defaults":response_model_exclude_defaults,
    #     "response_model_exclude_none":response_model_exclude_none,
    #     "include_in_schema":include_in_schema,
    #     "response_class":response_class,
    #     "name":name,
    #     "callbacks":callbacks,
    #     "openapi_extra":openapi_extra,
    #     "generate_unique_id_function":generate_unique_id_function
    #     }



"""
This example demonstrates most basic operations with single model
"""

from tortoise import Tortoise, fields, run_async
from tortoise.models import Model


class Event(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    datetime = fields.DatetimeField(null=True)

    class Meta:
        table = "event"

    def __str__(self):
        return self.name


async def run():
    await Tortoise.init(db_url="sqlite://:memory:", modules={"models": ["__main__"]})
    await Tortoise.generate_schemas()

    event = await Event.create(id=1, name="Test")
    await Event.filter(id=event.id).update(name="Updated name")

    print(await Event.filter(name="Updated name").first())
    # >>> Updated name

    await Event(name="Test 2").save()
    print(await Event.all().values_list("id", flat=True))
    # >>> [1, 2]
    print(await Event.all().values("id", "name"))
    # >>> [{'id': 1, 'name': 'Updated name'}, {'id': 2, 'name': 'Test 2'}]


# 为实例添加实例方法
from types import MethodType
router.path = MethodType(path, router)
r = router.path


if __name__ == "__main__":
    run_async(run())
```



### 正则表达式符号
```python
# 正则表达式修饰符 - 可选标志
re.I	使匹配对大小写不敏感
re.L	做本地化识别（locale-aware）匹配
re.M	多行匹配，影响 ^ 和 $
re.S	使 . 匹配包括换行在内的所有字符
re.U	根据Unicode字符集解析字符。这个标志影响 \w, \W, \b, \B.
re.X	该标志通过给予你更灵活的格式以便你将正则表达式写得更易于理解。

# 正则表达式模式
^	匹配字符串的开头
$	匹配字符串的末尾。
.	匹配任意字符，除了换行符，当re.DOTALL标记被指定时，则可以匹配包括换行符的任意字符。
[...]	用来表示一组字符,单独列出：[amk] 匹配 'a'，'m'或'k'
[^...]	不在[]中的字符：[^abc] 匹配除了a,b,c之外的字符。
re*	匹配0个或多个的表达式。
re+	匹配1个或多个的表达式。
re?	匹配0个或1个由前面的正则表达式定义的片段，非贪婪方式
re{ n}	匹配n个前面表达式。例如，"o{2}"不能匹配"Bob"中的"o"，但是能匹配"food"中的两个o。
re{ n,}	精确匹配n个前面表达式。例如，"o{2,}"不能匹配"Bob"中的"o"，但能匹配"foooood"中的所有o。"o{1,}"等价于"o+"。"o{0,}"则等价于"o*"。
re{ n, m}	匹配 n 到 m 次由前面的正则表达式定义的片段，贪婪方式
a|b	匹配a或b
(re)	匹配括号内的表达式，也表示一个组
(?imx)	正则表达式包含三种可选标志：i, m, 或 x 。只影响括号中的区域。
(?-imx)	正则表达式关闭 i, m, 或 x 可选标志。只影响括号中的区域。
(?: re)	类似 (...), 但是不表示一个组
(?imx: re)	在括号中使用i, m, 或 x 可选标志
(?-imx: re)	在括号中不使用i, m, 或 x 可选标志
(?#...)	注释.
(?= re)	前向肯定界定符。如果所含正则表达式，以 ... 表示，在当前位置成功匹配时成功，否则失败。但一旦所含表达式已经尝试，匹配引擎根本没有提高；模式的剩余部分还要尝试界定符的右边。
(?! re)	前向否定界定符。与肯定界定符相反；当所含表达式不能在字符串当前位置匹配时成功。
(?> re)	匹配的独立模式，省去回溯。
\w	匹配数字字母下划线
\W	匹配非数字字母下划线
\s	匹配任意空白字符，等价于 [\t\n\r\f]。
\S	匹配任意非空字符
\d	匹配任意数字，等价于 [0-9]。
\D	匹配任意非数字
\A	匹配字符串开始
\Z	匹配字符串结束，如果是存在换行，只匹配到换行前的结束字符串。
\z	匹配字符串结束
\G	匹配最后匹配完成的位置。
\b	匹配一个单词边界，也就是指单词和空格间的位置。例如， 'er\b' 可以匹配"never" 中的 'er'，但不能匹配 "verb" 中的 'er'。
\B	匹配非单词边界。'er\B' 能匹配 "verb" 中的 'er'，但不能匹配 "never" 中的 'er'。
\n, \t, 等。	匹配一个换行符。匹配一个制表符, 等
\1...\9	匹配第n个分组的内容。
\10	匹配第n个分组的内容，如果它经匹配。否则指的是八进制字符码的表达式。

# 正则表达式实例
[Pp]ython	匹配 "Python" 或 "python"
rub[ye]	匹配 "ruby" 或 "rube"
[aeiou]	匹配中括号内的任意一个字母
[0-9]	匹配任何数字。类似于 [0123456789]
[a-z]	匹配任何小写字母
[A-Z]	匹配任何大写字母
[a-zA-Z0-9]	匹配任何字母及数字
[^aeiou]	除了aeiou字母以外的所有字符
[^0-9]	匹配除了数字外的字符
特殊字符类
.	匹配除 "\n" 之外的任何单个字符。要匹配包括 '\n' 在内的任何字符，请使用象 '[.\n]' 的模式。
\d	匹配一个数字字符。等价于 [0-9]。
\D	匹配一个非数字字符。等价于 [^0-9]。
\s	匹配任何空白字符，包括空格、制表符、换页符等等。等价于 [ \f\n\r\t\v]。
\S	匹配任何非空白字符。等价于 [^ \f\n\r\t\v]。
\w	匹配包括下划线的任何单词字符。等价于'[A-Za-z0-9_]'。
\W	匹配任何非单词字符。等价于 '[^A-Za-z0-9_]'。
```



Access to fetch at 'http://192.168.100.197:8099/realms/sso-test-ldap/protocol/openid-connect/token/' from origin 'http://172.9.50.223:1001' has been blocked by CORS policy: The request client is not a secure context and the resource is in more-private address space `private`.

解决方案：
1:两种资源都改成 https
2.在浏览器中直接执行chrome://flags/#block-insecure-private-network-requests ，选中Disabled ，relaunch 后就可以恢复正常了。


# 序列化模型
from fastapi.encoders import jsonable_encoder
jsonable_encoder(model_obj)


```python
tortoise-orm创建表时指定字段顺序
使用sqlalchemy时，可以通过sort_order字段指定创建表时的字段顺序，切换到tortoise-orm后，字段顺序不能自定义了，用起来很麻烦

废话不多说，直接上方法（需要修改源码）
第一步 修改Field类，增加field_order字段

# 只修改Field类的init方法
    def __init__(
        self,
        source_field: Optional[str] = None,
        generated: bool = False,
        primary_key: Optional[bool] = None,
        null: bool = False,
        default: Any = None,
        unique: bool = False,
        db_index: Optional[bool] = None,
        description: Optional[str] = None,
        model: "Optional[Model]" = None,
        validators: Optional[List[Union[Validator, Callable]]] = None,
        field_order: int = 0,  # 这里加一行，字段顺序
        **kwargs: Any,
    ) -> None:
        self.field_order = field_order   # 增加一个field_order属性
第二步 修改Tortoise.init

# 这里需要改两个地方
# 1. 在Tortoise中增加sort_fields方法
    @classmethod
    def sort_fields(cls):
        last_fields = []
        for app_name, app in cls.apps.items():
            for model_name, model in app.items():
                fields_order = {k: getattr(v, 'field_order', 0) for k, v in model._meta.fields_map.items()}
                model._meta.fields_db_projection = {
                    k: v for k, v in sorted(
                        model._meta.fields_db_projection.items(),
                        key=lambda x: fields_order.get(x[0], 0)
                    )
                }
# 2. 在Tortoise.init方法中增加sort_fields调用
    async def init():
        ....  # 上面的代码都不动
        
        cls._init_timezone(use_tz, timezone)
        await connections._init(connections_config, _create_db)
        cls._init_apps(apps_config)
        cls._init_routers(routers)
        cls.sort_fields()   # 就增加这一行

        cls._inited = True
第三步 在model定义的时候添加field_order参数

# 比如这样
class BaseDBModel(Model):
    id = fields.IntField(pk=True)
    is_deleted = fields.BooleanField(default=False, description='是否删除， 1=删除，0=未删除', field_order=995)
    created_by = fields.IntField(null=True, description='创建人', field_order=996)
    updated_by = fields.IntField(null=True, description='最后更新人', field_order=997)
    created_time = fields.DatetimeField(auto_now_add=True, description='创建时间', field_order=998)
    updated_time = fields.DatetimeField(auto_now=True, description='最后更新时间', field_order=999)

    class Mate:
        abstract = True
        ordering = ['-created_time']
PS: 如果找不到源码的位置可以import对应的类，然后按住ctrl点击对应的方法跳转（Pycharm中可以这么操作）
```

```python
from tortoise.contrib.fastapi import register_tortoise

register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=False,
    add_exception_handlers=False,
)



@api(
    methods=["post"],
    tags=["Security"],
)
# @permission_required("model", "udadmin#User#list")
# async def test(
def test(
    user: Annotated[str, Depends(auth.get_user)],
    b: Body2,
):
    async def get_user():
        return await md.User.filter(id=1).first()

    c = asyncio.run(get_user())
    # 同步函数里面调用异步函数，需要用asyncio.run()来运行
    # 只能上述这样请求，下面的都报错
    # c = md.User.filter(id=1).first()
    # c = await get_user()

    return {
        "status": 1,
        "data": {
            "user": user,
            "b": b,
            "c": c,
        },
    }


```