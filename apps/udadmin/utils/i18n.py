from __future__ import annotations

from contextvars import ContextVar
from pathlib import Path
from typing import Any

from fastapi import Request

try:
    import yaml
except Exception:  # pragma: no cover - dependency fallback
    yaml = None


DEFAULT_LOCALE = "zh-CN"
SUPPORTED_LOCALES = ("zh-CN", "en-US")
LOCALE_ALIASES = {
    "zh": "zh-CN",
    "zh-cn": "zh-CN",
    "zh_cn": "zh-CN",
    "en": "en-US",
    "en-us": "en-US",
    "en_us": "en-US",
}
LOCALE_FILE_MAP = {
    "zh-CN": "zh",
    "en-US": "en",
}

current_locale: ContextVar[str] = ContextVar("current_locale", default=DEFAULT_LOCALE)
_translations: dict[str, dict[str, Any]] = {}


def _locale_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "locales"


def _flatten(prefix: str, value: Any, output: dict[str, str]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            _flatten(next_prefix, item, output)
        return
    output[prefix] = "" if value is None else str(value)


def _simple_yaml_load(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        key, sep, raw_value = raw_line.strip().partition(":")
        if not sep:
            continue
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        value = raw_value.strip()
        if value == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            if (value.startswith('"') and value.endswith('"')) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            parent[key] = value
    return root


def load_translations() -> None:
    if _translations:
        return
    for locale, filename in LOCALE_FILE_MAP.items():
        path = _locale_dir() / f"{filename}.yml"
        if not path.exists():
            _translations[locale] = {}
            continue
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text) if yaml else _simple_yaml_load(text)
        flattened: dict[str, str] = {}
        _flatten("", data or {}, flattened)
        _translations[locale] = flattened


def normalize_locale(locale: str | None) -> str:
    if not locale:
        return DEFAULT_LOCALE
    normalized = locale.strip()
    if normalized in SUPPORTED_LOCALES:
        return normalized
    return LOCALE_ALIASES.get(normalized.lower(), DEFAULT_LOCALE)


def parse_accept_language(value: str | None) -> str:
    if not value:
        return DEFAULT_LOCALE
    candidates: list[tuple[float, str]] = []
    for part in value.split(","):
        token = part.strip()
        if not token:
            continue
        language, *params = token.split(";")
        quality = 1.0
        for param in params:
            name, sep, raw_quality = param.strip().partition("=")
            if sep and name == "q":
                try:
                    quality = float(raw_quality)
                except ValueError:
                    quality = 0.0
        candidates.append((quality, language.strip()))
    for _, language in sorted(candidates, reverse=True):
        locale = normalize_locale(language)
        if locale in SUPPORTED_LOCALES:
            return locale
    return DEFAULT_LOCALE


def set_locale(locale: str) -> None:
    current_locale.set(normalize_locale(locale))


def get_locale(request: Request | None = None) -> str:
    if request is not None:
        state_locale = getattr(request.state, "locale", None)
        if state_locale:
            return normalize_locale(state_locale)
        return parse_accept_language(request.headers.get("Accept-Language"))
    return normalize_locale(current_locale.get())


def t(key: str, request: Request | None = None, locale: str | None = None, **kwargs: Any) -> str:
    load_translations()
    active_locale = normalize_locale(locale) if locale else get_locale(request)
    translations = _translations.get(active_locale, {})
    default_translations = _translations.get(DEFAULT_LOCALE, {})
    template = translations.get(key) or default_translations.get(key) or key
    try:
        return template.format(**kwargs)
    except Exception:
        return template


def t_or_original(key: str, original: str | None = None, **kwargs: Any) -> str:
    value = t(key, **kwargs)
    if value == key:
        return "" if original is None else str(original)
    return value


def localize_app_info(app_key: str, app_info: dict[str, Any]) -> dict[str, Any]:
    localized = dict(app_info)
    localized["app_menu_name"] = t_or_original(
        f"ui.apps.{app_key}.menu_name", localized.get("app_menu_name")
    )
    localized["app_description"] = t_or_original(
        f"ui.apps.{app_key}.description", localized.get("app_description")
    )
    return localized


def localize_model_display(
    model_name: str,
    menu_name: str | None = None,
    table_description: str | None = None,
) -> tuple[str, str]:
    return (
        t_or_original(f"ui.models.{model_name}", menu_name or model_name),
        t_or_original(f"ui.tables.{model_name}", table_description or model_name),
    )


def localize_field_info(field_name: str, field_info: dict[str, Any]) -> dict[str, Any]:
    localized = dict(field_info)
    info = dict(localized.get("info") or {})
    info["ui_name"] = t_or_original(
        f"ui.fields.{field_name}", info.get("ui_name") or field_name
    )
    field_type = localized.get("field_type")
    ui_desc = info.get("ui_desc")
    if field_type in {"ManyToManyField", "OneToOneField", "BackwardFKRelation", "ForeignKeyField"}:
        related_model = ui_desc.split(":", 1)[1].strip() if isinstance(ui_desc, str) and ":" in ui_desc else ""
        if related_model:
            related_model_name = t_or_original(f"ui.models.{related_model}", related_model)
            info["ui_desc"] = t_or_original(
                "ui.relationship_model", ui_desc, model=related_model_name
            )
    localized["info"] = info
    return localized
