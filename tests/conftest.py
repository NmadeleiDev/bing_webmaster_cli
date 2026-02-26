import pytest


@pytest.fixture(autouse=True)
def isolate_user_files(tmp_path, monkeypatch):
    config_dir = tmp_path / "bwm"
    monkeypatch.setenv("BWM_CONFIG_DIR", str(config_dir))
    monkeypatch.setenv("BWM_APP_CONFIG_FILE", str(config_dir / "config.json"))
    monkeypatch.setenv("BWM_CREDENTIALS_FILE", str(config_dir / "credentials.json"))
    monkeypatch.delenv("BING_WEBMASTER_API_KEY", raising=False)
