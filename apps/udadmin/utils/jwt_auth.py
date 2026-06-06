import jwt
from config.settings import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_SECONDS,
    REFRESH_TOKEN_EXPIRE_SECONDS,
)

# from jwt import exceptions
import time


class UdTokenInvalid(Exception):
    pass


# 加的盐
jwt_salt = SECRET_KEY
# algorithm="HS256"
algorithm = ALGORITHM

access_exp = ACCESS_TOKEN_EXPIRE_SECONDS
refresh_exp = REFRESH_TOKEN_EXPIRE_SECONDS
# access_exp = 10
# refresh_exp = 20


def create_token(info: dict, access_exp=access_exp, refresh_exp=refresh_exp):
    """
    用于加密生成token
    :payload dict e.g. {"user_id": "杨远", "age": 31}:
        payload标准信息：（并不完全强制要求全部使用）
        iss    : jwt签发者
        sub  : 主题名称
        aud  : 面向的用户，一般都是通过ip或者域名控制
        exp  : jwt的有效时间（过期时间），这个有效时间必须要大于签发时间，对于交互接口来说，建议是预设5秒
        nbf   : 在什么时候jwt开始生效（在此之前不可用）
        iat    : jwt的签发时间，只能用utc时间
        jti     : 唯一标识，主要用来回避被重复使用攻击
        ————————————————
        版权声明：本文为CSDN博主「H-大叔」的原创文章，遵循CC 4.0 BY-SA版权协议，转载请附上原文出处链接及本声明。
        原文链接：https://blog.csdn.net/HRG520JN/article/details/123664105
    :return: {"status": False, "data": None, "error": None, "errmsg": None}
    """
    # 声明类型，声明加密算法
    headers = {"type": "jwt", "alg": "HS256"}
    now = time.time()
    # access_token
    # 设置过期时间
    access_payload = {
        # "iss": "bbb.com",
        # "iat": int(time.time()),
        # "exp": int(time.time()) + datetime.timedelta(seconds=timeout),
        "iat": now,
        "exp": now + access_exp,
        # "aud": "www.gusibi.mobi",
        # "scopes": ['open']
    }
    access_payload = dict(access_payload, **info)
    access_token = jwt.encode(
        access_payload,
        jwt_salt,
        algorithm=algorithm,
        headers=headers,
    )
    if not isinstance(access_token, str):
        access_token = str(access_token, encoding="utf8")

    # refresh_token
    refresh_payload: dict = {
        "iat": now,
        "exp": now + refresh_exp,
    }
    refresh_payload = dict(refresh_payload, **info)
    refresh_payload["grant_type"] = "refresh"
    refresh_token = jwt.encode(
        refresh_payload, jwt_salt, algorithm="HS256", headers=headers
    )
    if not isinstance(refresh_token, str):
        refresh_token = str(refresh_token, encoding="utf8")
    # 返回加密结果
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "iat": access_payload["iat"],
        "exp": access_payload["exp"],
        "refresh_iat": refresh_payload["iat"],
        "refresh_exp": refresh_payload["exp"],
    }


def parse_payload(token):
    """
    用于解密
    :param token:
    :return: {"status": False, "data": None, "error": None, "errmsg": None}
    """
    # 进行解密
    return jwt.decode(token, key=jwt_salt, algorithms="HS256")


if __name__ == "__main__":
    dict_c = {
        "id": 0,
        "username": "user2",
    }
    token = create_token(
        dict_c,
        # access_exp=60 * 60 * 24 * 365 * 3,
        # refresh_exp=60 * 60 * 24 * 365 * 5,
        access_exp=2,
        refresh_exp=2,
    )
    access_token = token["access_token"]
    print(token)
    # time.sleep(3)
    # admin 3年的token  202402160908
    # eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsInR5cGUiOiJqd3QifQ.eyJpYXQiOjE3MzQzMTE0MzAuNDUwODgwNSwiZXhwIjoxODI4OTE5NDMyLjQ1MDg4MDUsImlkIjowLCJ1c2VybmFtZSI6ImFkbWluIiwiY25fbmFtZSI6Ilx1N2JhMVx1NzQwNlx1NTQ1OCIsInVwZGF0ZWRfYXQiOiIyMDI0LTEyLTEwVDE3OjM0OjE4LjQ3NzA3NiswODowMCIsInBhc3N3b3JkIjoiJDJiJDEyJG5RdUZ2bXM1YzY5ZWVMRzA3L3hsUy5IOWN6NWFldkRVem9DL216dUVFZ3RXcHpWa3FPeWlPIiwiaXNfYWN0aXZlIjp0cnVlLCJpc19kZWxldGUiOmZhbHNlLCJjcmVhdGVkX2F0IjoiMjAyNC0xMi0xMFQxNzozNDoxOC40NzcwMzgrMDg6MDAiLCJnZW5kZXIiOiJcdTc1MzciLCJpc19zdXBlcnVzZXIiOnRydWUsImxhc3RfbG9naW4iOiIyMDI0LTEyLTEwVDE3OjM0OjE4LjQ3NzEyMiswODowMCJ9.z8AaE9i_HERrpORu9cJvxsPPvzuKRrdPGiO2AfRac0c
    # user2 3年的token  202402160908
    # eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsInR5cGUiOiJqd3QifQ.eyJpYXQiOjE3MzUxMDk4MTAuNDIzNjA3MywiZXhwIjoxODI5NzE3ODEyLjQyMzYwNzMsImlkIjowLCJ1c2VybmFtZSI6InVzZXIyIn0.wom3LuEsyqwKcNGrn59EMGSMobKR6kQXsCmlYE8e8CY

    # 过期的access_token
    # eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsInR5cGUiOiJqd3QifQ.eyJpYXQiOjE3Mzc1MzgyOTguMzUxNzUsImV4cCI6MTczNzUzODMwMi4zNTE3NSwiaWQiOjAsInVzZXJuYW1lIjoidXNlcjIifQ.biiSuiUQAv5SairRajFOjeF1OhDvWC7ZQfz5Yd1ag1A
    # 过期的refresh_token
    # eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCIsInR5cGUiOiJqd3QifQ.eyJpYXQiOjE3Mzc1MzgzMDAuMzUxNzUsImV4cCI6MTczNzUzODMwMi4zNTE3NSwiaWQiOjAsInVzZXJuYW1lIjoidXNlcjIiLCJncmFudF90eXBlIjoicmVmcmVzaCJ9.WkUd5CtHd0qeNM7v207LTEjk6BLCwP14iwkqhJDqqM8
    # print(jwt.decode(access_token, key=JWT_SALT, algorithms="HS256"))
