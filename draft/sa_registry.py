"""ModelRegistry: Global model registry."""
import inspect
from typing import Type, Optional
from sqlalchemy.orm import DeclarativeBase
from apps.udadmin.utils.class_tools import SingletonMeta


class ModelRegistry(metaclass=SingletonMeta):
    def __init__(self):
        self.apps: dict = {}

    def register_app(self, app_name, models_module):
        if app_name not in self.apps:
            self.apps[app_name] = {}
        for name, obj in inspect.getmembers(models_module, inspect.isclass):
            if (
                issubclass(obj, DeclarativeBase)
                and obj is not DeclarativeBase
                and "__tablename__" in obj.__dict__
            ):
                # print(f"{app_name}:{name}")
                self.apps[app_name][name] = obj
                self.apps[app_name][name.lower()] = obj

    def get_model(self, app_name, model_name):
        return self.apps.get(app_name, {}).get(model_name)

    def all_models(self):
        return self.apps

    @classmethod
    def get_instance(cls):
        return cls()


def get_model_registry():
    return ModelRegistry.get_instance()
