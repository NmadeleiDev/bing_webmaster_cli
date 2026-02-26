from click.testing import CliRunner

from bingwm_cli.cli import cli
from bingwm_cli.cli import _extract_is_indexed


class FakeClient:
    def __init__(self):
        self.submitted = None

    def get_user_sites(self):
        return [{"Url": "https://example.com", "PermissionLevel": "Admin"}]

    def get_rank_and_traffic_data(self, site_url, start_date, end_date):
        assert site_url == "https://example.com"
        return [{"Date": "2026-02-20", "Clicks": 10, "Impressions": 100}]

    def get_url_traffic_info(self, site_url, url, start_date, end_date):
        return [{"Date": "2026-02-20", "Clicks": 3, "Impressions": 25, "Url": url}]

    def get_url_info(self, site_url, url):
        return {"Url": url, "IsPage": False, "HttpCode": 404}

    def get_crawl_issues(self, site_url):
        return [{"Url": "https://example.com/missing", "Issues": 1}]

    def submit_url(self, site_url, url):
        self.submitted = (site_url, [url])
        return {"Accepted": True}

    def submit_url_batch(self, site_url, urls):
        self.submitted = (site_url, urls)
        return {"Accepted": True, "Count": len(urls)}


def test_site_list(monkeypatch):
    runner = CliRunner()
    fake = FakeClient()

    monkeypatch.setattr("bingwm_cli.cli._build_client", lambda write=False: fake)

    result = runner.invoke(cli, ["site", "list"])

    assert result.exit_code == 0
    assert "https://example.com" in result.output
    assert "Admin" in result.output


def test_stats_site_uses_default_site(monkeypatch):
    runner = CliRunner()
    fake = FakeClient()

    monkeypatch.setattr("bingwm_cli.cli._build_client", lambda write=False: fake)
    monkeypatch.setattr("bingwm_cli.cli.get_default_site", lambda: "https://example.com")

    result = runner.invoke(cli, ["stats", "site", "--output", "json"])

    assert result.exit_code == 0
    assert '"Clicks": 10' in result.output


def test_url_check_index_prints_reason(monkeypatch):
    runner = CliRunner()
    fake = FakeClient()

    monkeypatch.setattr("bingwm_cli.cli._build_client", lambda write=False: fake)
    monkeypatch.setattr("bingwm_cli.cli.get_default_site", lambda: "https://example.com")

    result = runner.invoke(
        cli,
        ["url", "check-index", "--url", "https://example.com/missing", "--output", "json"],
    )

    assert result.exit_code == 0
    assert '"isIndexed": false' in result.output
    assert "NotFound" in result.output


def test_url_submit_multiple_urls(monkeypatch, tmp_path):
    runner = CliRunner()
    fake = FakeClient()
    list_file = tmp_path / "urls.txt"
    list_file.write_text("https://example.com/a\nhttps://example.com/b\n", encoding="utf-8")

    monkeypatch.setattr("bingwm_cli.cli._build_client", lambda write=False: fake)
    monkeypatch.setattr("bingwm_cli.cli.get_default_site", lambda: "https://example.com")

    result = runner.invoke(
        cli,
        [
            "url",
            "submit",
            "--url",
            "https://example.com/c",
            "--file",
            str(list_file),
            "--output",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert fake.submitted == (
        "https://example.com",
        ["https://example.com/c", "https://example.com/a", "https://example.com/b"],
    )
    assert '"submittedCount": 3' in result.output


def test_auth_login_stores_key(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr("bingwm_cli.cli.save_api_key", lambda api_key: "/tmp/creds.json")

    result = runner.invoke(cli, ["auth", "login", "--api-key", "abc123"])

    assert result.exit_code == 0
    assert "Saved API key to /tmp/creds.json" in result.output


def test_extract_is_indexed_false_for_uncrawled_placeholder_record():
    info = {
        "IsPage": True,
        "HttpStatus": 0,
        "DiscoveryDate": "/Date(-62135568000000-0800)/",
        "LastCrawledDate": "/Date(-62135568000000-0800)/",
    }

    assert _extract_is_indexed(info) is False


def test_url_check_index_explain_adds_explanation(monkeypatch):
    runner = CliRunner()
    fake = FakeClient()

    monkeypatch.setattr("bingwm_cli.cli._build_client", lambda write=False: fake)
    monkeypatch.setattr("bingwm_cli.cli.get_default_site", lambda: "https://example.com")

    result = runner.invoke(
        cli,
        [
            "url",
            "check-index",
            "--url",
            "https://example.com/missing",
            "--output",
            "json",
            "--explain",
        ],
    )

    assert result.exit_code == 0
    assert '"explanation"' in result.output
