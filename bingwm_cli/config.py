"""Persistent app config helpers."""

from __future__ import annotations

import json
from pathlib import Path

from bingwm_cli.paths import app_config_file


class ConfigError(RuntimeError):
    """Raised when config cannot be loaded or validated."""


def load_config() -> dict:
    path = app_config_file()
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Config file is not valid JSON: {path}") from exc


def save_config(config: dict) -> Path:
    path = app_config_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return path


def set_default_site(site_url: str) -> Path:
    value = site_url.strip()
    if not value:
        raise ConfigError("default-site cannot be empty")

    config = load_config()
    config["default_site"] = value
    return save_config(config)


def get_default_site() -> str | None:
    value = load_config().get("default_site")
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None
