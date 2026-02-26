"""Filesystem path helpers for Bing Webmaster CLI."""

from __future__ import annotations

import os
from pathlib import Path


def config_dir() -> Path:
    env_value = os.environ.get("BWM_CONFIG_DIR")
    if env_value:
        return Path(env_value).expanduser()
    return Path.home() / ".config" / "bing-webmaster-cli"


def credentials_file() -> Path:
    env_value = os.environ.get("BWM_CREDENTIALS_FILE")
    if env_value:
        return Path(env_value).expanduser()
    return config_dir() / "credentials.json"


def app_config_file() -> Path:
    env_value = os.environ.get("BWM_APP_CONFIG_FILE")
    if env_value:
        return Path(env_value).expanduser()
    return config_dir() / "config.json"
