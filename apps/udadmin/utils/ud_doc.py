from fastapi import applications
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html


# 设置全局docs 从本地加载静态文件
def swagger_ui_patch(*args, **kwargs):
    # 要排除applications的setup函数里面调用这个函数时给的参数，不然会重复传参导致错误
    keys = ["title", "swagger_js_url", "swagger_css_url", "swagger_favicon_url"]
    new_kwargs = {k: v for k, v in kwargs.items() if k not in keys}
    return get_swagger_ui_html(
        *args,
        **new_kwargs,
        title="API swagger doc",
        swagger_js_url="/static/docs-ui/swagger/swagger-ui-bundle.js",
        swagger_css_url="/static/docs-ui/swagger/swagger-ui.css",
        swagger_favicon_url="/static/logo.svg",
    )


def redoc_ui_path(*args, **kwargs):
    # 要排除applications的setup函数里面调用这个函数时给的参数，不然会重复传参导致错误
    keys = ["title", "redoc_js_url", "redoc_favicon_url"]
    new_kwargs = {k: v for k, v in kwargs.items() if k not in keys}
    return get_redoc_html(
        *args,
        **new_kwargs,
        title="API redoc",
        redoc_js_url="/static/docs-ui/redoc/redoc.standalone.js",
        redoc_favicon_url="/static/logo.svg",
    )


applications.get_swagger_ui_html = swagger_ui_patch  # type: ignore
applications.get_redoc_html = redoc_ui_path  # type: ignore
