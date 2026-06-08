import importlib
import traceback

from fastapi import FastAPI


def import_app(import_path: str):
    if ":" in import_path:
        module_path, attr_name = import_path.split(":", 1)
    else:
        module_path, attr_name = import_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, attr_name)


def default_registered_app_name(import_path: str) -> str:
    module_path = import_path.split(":", 1)[0]
    parts = module_path.split(".")
    if "apps" in parts:
        app_index = parts.index("apps") + 1
        if app_index < len(parts):
            return parts[app_index]
    if len(parts) >= 2:
        return parts[-2]
    return parts[0]


class AppReg:
    DEFAULT_APP_ICON = "antd:AppstoreOutlined"

    def __init__(
        self,
        app_path: str,
        router_prefix: str | None = None,
        name: str | None = None,
        app_icon: str = DEFAULT_APP_ICON,
    ):
        self.app_path = app_path
        app_name = default_registered_app_name(app_path)
        self.app_name = app_name

        if router_prefix is None:
            router_prefix = f"/{app_name}"
        elif not router_prefix.startswith("/"):
            router_prefix = f"/{router_prefix}"

        self.router_prefix = router_prefix
        self.name = name or app_name
        self.app_icon = app_icon


def mount_registered_apps(app: FastAPI) -> None:
    from config import settings

    registered_apps = getattr(settings, "REGISTERED_APPS", [])
    for app_reg in registered_apps:
        if not isinstance(app_reg, AppReg):
            print(
                "skip registered app: "
                f"{app_reg!r} is not an AppReg instance"
            )
            continue

        try:
            sub_app = import_app(app_reg.app_path)
            app.mount(
                app_reg.router_prefix,
                sub_app,
                name=app_reg.name,
            )
            print(
                "mounted app: "
                f"{app_reg.app_path} -> {app_reg.router_prefix} "
                f"(name={app_reg.name})"
            )
        except Exception as exc:
            print(
                "skip registered app: "
                f"{app_reg.app_path} -> {app_reg.router_prefix} "
                f"(name={app_reg.name}) failed: "
                f"{exc.__class__.__name__}: {exc}"
            )
            if getattr(settings, "DEBUG", False):
                print(traceback.format_exc())
