import json

import pytest

from bingwm_cli.auth import AuthError, auth_status, clear_stored_api_key, load_api_key, save_api_key
from bingwm_cli.paths import credentials_file


def test_save_and_load_api_key_local():
    path = save_api_key("abc123")
    assert path.exists()

    key, source = load_api_key()
    assert key == "abc123"
    assert source == "local"


def test_env_api_key_precedence(monkeypatch):
    save_api_key("local-key")
    monkeypatch.setenv("BING_WEBMASTER_API_KEY", "env-key")

    key, source = load_api_key()
    assert key == "env-key"
    assert source == "env"


def test_load_api_key_missing_raises():
    with pytest.raises(AuthError, match="No API key found"):
        load_api_key()


def test_clear_stored_api_key():
    save_api_key("abc")
    assert clear_stored_api_key() is True
    assert credentials_file().exists() is False


def test_auth_status_missing():
    status = auth_status()
    assert status["source"] == "missing"
    assert status["api_key_masked"] == ""


def test_auth_status_local_masked():
    save_api_key("0123456789")
    status = auth_status()
    assert status["source"] == "local"
    assert status["api_key_masked"] == "0123...6789"


def test_invalid_stored_json_raises():
    path = credentials_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not-json", encoding="utf-8")

    with pytest.raises(AuthError, match="invalid JSON"):
        load_api_key()


def test_stored_api_key_missing_field_raises():
    path = credentials_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"token": "x"}), encoding="utf-8")

    with pytest.raises(AuthError, match="missing 'api_key'"):
        load_api_key()
