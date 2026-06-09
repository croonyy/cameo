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
_missing_translation_warnings: set[tuple[str, str]] = set()


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
    template = translations.get(key)
    if template is None:
        warning_key = (active_locale, key)
        if warning_key not in _missing_translation_warnings:
            _missing_translation_warnings.add(warning_key)
            print(f"i18n missing translation: locale={active_locale}, key={key}")
        template = default_translations.get(key)
    if template is None:
        default_warning_key = (DEFAULT_LOCALE, key)
        if active_locale != DEFAULT_LOCALE and default_warning_key not in _missing_translation_warnings:
            _missing_translation_warnings.add(default_warning_key)
            print(f"i18n missing translation: locale={DEFAULT_LOCALE}, key={key}")
        template = key
    try:
        return template.format(**kwargs)
    except Exception:
        return template
