# from dataclasses import dataclass, asdict
import threading
from typing import Any

class DynamicObject:
    def __init__(self, data: dict | None = None, **kwargs):
        # 支持两种传参：
        # 1. DynamicObject({"name": 1})
        # 2. DynamicObject(name=1, age=2)
        if data is not None:
            assert isinstance(data, dict), "data 必须是字典"
            final_data = data
        else:
            final_data = kwargs

        # 安全存储数据
        super().__setattr__('_DynamicObject__data', final_data)

    def __getattr__(self, name: str) -> Any:
        try:
            value = self.__data[name]
            # 自动嵌套
            if isinstance(value, dict):
                return DynamicObject(value)
            return value
        except KeyError:
            raise AttributeError(f"DynamicObject 没有属性: {name}")

    def __setattr__(self, name: str, value: Any) -> None:
        self.__data[name] = value


class SingletonMeta(type):
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
            return cls._instances[cls]
