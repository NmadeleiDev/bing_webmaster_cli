from datetime import date

import pytest

from bingwm_cli.client import BingAPIError, BingWebmasterClient


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.last_url = None
        self.last_json = None
        self.last_timeout = None
        self.last_method = None

    def post(self, url, json, timeout):
        self.last_method = "POST"
        self.last_url = url
        self.last_json = json
        self.last_timeout = timeout
        return self.response

    def get(self, url, timeout):
        self.last_method = "GET"
        self.last_url = url
        self.last_timeout = timeout
        return self.response


def test_get_user_sites_extracts_results():
    client = BingWebmasterClient("k")
    fake = FakeSession(FakeResponse(payload={"d": {"Results": [{"Url": "https://example.com"}]}}))
    client.session = fake

    rows = client.get_user_sites()

    assert len(rows) == 1
    assert rows[0]["Url"] == "https://example.com"
    assert "GetUserSites?apikey=k" in fake.last_url
    assert fake.last_method == "GET"


def test_get_url_info_extracts_method_result_wrapper():
    client = BingWebmasterClient("k")
    fake = FakeSession(
        FakeResponse(payload={"d": {"GetUrlInfoResult": {"Url": "https://example.com/p", "IsPage": True}}})
    )
    client.session = fake

    record = client.get_url_info("https://example.com", "https://example.com/p")

    assert record["IsPage"] is True
    assert fake.last_method == "GET"


def test_get_rank_and_traffic_data_formats_dates():
    client = BingWebmasterClient("k")
    fake = FakeSession(FakeResponse(payload={"d": {"GetRankAndTrafficStatsResult": {"Results": []}}}))
    client.session = fake

    client.get_rank_and_traffic_data("https://example.com", date(2026, 2, 1), date(2026, 2, 26))

    assert "startDate=2%2F1%2F2026" in fake.last_url
    assert "endDate=2%2F26%2F2026" in fake.last_url
    assert "GetRankAndTrafficStats" in fake.last_url
    assert fake.last_method == "GET"


def test_get_rank_and_traffic_data_filters_rows_to_requested_range():
    client = BingWebmasterClient("k")
    fake = FakeSession(
        FakeResponse(
            payload={
                "d": {
                    "GetRankAndTrafficStatsResult": {
                        "Results": [
                            {"Date": "2026-03-19", "Clicks": 1},
                            {"Date": "2026-03-20", "Clicks": 2},
                            {"Date": "2026-03-21", "Clicks": 3},
                        ]
                    }
                }
            }
        )
    )
    client.session = fake

    rows = client.get_rank_and_traffic_data("https://example.com", date(2026, 3, 20), date(2026, 3, 20))

    assert rows == [{"Date": "2026-03-20", "Clicks": 2}]


def test_get_url_traffic_info_single_object_wrapped_as_row():
    client = BingWebmasterClient("k")
    fake = FakeSession(
        FakeResponse(
            payload={
                "d": {
                    "GetUrlTrafficInfoResult": {
                        "Url": "https://example.com/p",
                        "Clicks": 2,
                        "Impressions": 10,
                        "IsPage": True,
                    }
                }
            }
        )
    )
    client.session = fake

    rows = client.get_url_traffic_info(
        "https://example.com",
        "https://example.com/p",
        date(2026, 2, 1),
        date(2026, 2, 26),
    )

    assert len(rows) == 1
    assert rows[0]["Url"] == "https://example.com/p"


def test_get_url_traffic_info_filters_rows_to_requested_range():
    client = BingWebmasterClient("k")
    fake = FakeSession(
        FakeResponse(
            payload={
                "d": {
                    "GetUrlTrafficInfoResult": {
                        "Results": [
                            {"Date": "Date(1773385200000-0700)", "Clicks": 1},
                            {"Date": "Date(1773471600000-0700)", "Clicks": 2},
                        ]
                    }
                }
            }
        )
    )
    client.session = fake

    rows = client.get_url_traffic_info(
        "https://example.com",
        "https://example.com/p",
        date(2026, 3, 14),
        date(2026, 3, 14),
    )

    assert rows == [{"Date": "Date(1773471600000-0700)", "Clicks": 2}]


def test_api_error_raises_with_status_code():
    client = BingWebmasterClient("k")
    fake = FakeSession(FakeResponse(status_code=401, payload={"Message": "bad key"}))
    client.session = fake

    with pytest.raises(BingAPIError, match="401"):
        client.get_user_sites()
