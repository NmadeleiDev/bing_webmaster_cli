"""API-key authentication helpers."""

from __future__ import annotations

import json
from pathlib import Path

from bingwm_cli.paths import credentials_file

API_KEY_ENV_VAR = "BING_WEBMASTER_API_KEY"


class AuthError(RuntimeError):
    """Raised when API key auth state is invalid."""


def save_api_key(api_key: str) -> Path:
    value = api_key.strip()
    if not value:
        raise AuthError("API key cannot be empty")

    path = credentials_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"api_key": value}, indent=2) + "\n", encoding="utf-8")
    return path


def clear_stored_api_key() -> bool:
    path = credentials_file()
    if path.exists():
        path.unlink()
        return True
    return False


def load_stored_api_key() -> str | None:
    path = credentials_file()
    if not path.exists():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AuthError(f"Stored credentials are invalid JSON: {path}") from exc

    value = payload.get("api_key")
    if not isinstance(value, str):
        raise AuthError(f"Stored credentials are missing 'api_key': {path}")

    value = value.strip()
    if not value:
        raise AuthError(f"Stored API key is empty: {path}")
    return value


def load_api_key() -> tuple[str, str]:
    from os import environ

    env_value = environ.get(API_KEY_ENV_VAR)
    if isinstance(env_value, str) and env_value.strip():
        return env_value.strip(), "env"

    stored = load_stored_api_key()
    if stored:
        return stored, "local"

    raise AuthError(
        "No API key found. Set BING_WEBMASTER_API_KEY or run `bwm auth login`."
    )


def auth_status() -> dict:
    from os import environ

    env_value = environ.get(API_KEY_ENV_VAR)
    stored_value: str | None = None
    stored_path = credentials_file()

    if isinstance(env_value, str) and env_value.strip():
        source = "env"
        key = env_value.strip()
    else:
        stored_value = load_stored_api_key()
        if stored_value:
            source = "local"
            key = stored_value
        else:
            source = "missing"
            key = ""

    return {
        "source": source,
        "api_key_masked": _mask_key(key) if key else "",
        "env_var": API_KEY_ENV_VAR,
        "credentials_path": str(stored_path),
        "local_key_present": bool(stored_value) if source != "local" else True,
    }


def _mask_key(value: str) -> str:
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"
