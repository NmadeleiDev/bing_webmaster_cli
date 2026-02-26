"""Bing Webmaster API client."""

from __future__ import annotations

import json
import os
from datetime import date
from urllib.parse import urlencode

import requests

BING_WEBMASTER_BASE_URL = "https://ssl.bing.com/webmaster/api.svc/json"


class BingAPIError(RuntimeError):
    """Raised for API responses with non-2xx status."""

    def __init__(self, message: str, *, status_code: int | None = None, payload: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload or {}


class BingWebmasterClient:
    """Thin wrapper around Bing Webmaster JSON API methods."""

    def __init__(self, api_key: str, *, base_url: str | None = None, timeout: int = 30):
        self.api_key = api_key
        self.base_url = (base_url or os.environ.get("BWM_API_BASE_URL") or BING_WEBMASTER_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def get_user_sites(self) -> list[dict]:
        data = self._call("GetUserSites", {})
        return _extract_list(data, ["Results", "SiteInfo", "Sites"])

    def get_rank_and_traffic_data(self, site_url: str, start_date: date, end_date: date) -> list[dict]:
        payload = {
            "siteUrl": site_url,
            "startDate": _format_bing_date(start_date),
            "endDate": _format_bing_date(end_date),
        }
        data = self._call("GetRankAndTrafficStats", payload)
        return _extract_list(data, ["Results", "Data", "Rows"])

    def get_url_traffic_info(self, site_url: str, url: str, start_date: date, end_date: date) -> list[dict]:
        payload = {
            "siteUrl": site_url,
            "url": url,
            "startDate": _format_bing_date(start_date),
            "endDate": _format_bing_date(end_date),
        }
        data = self._call("GetUrlTrafficInfo", payload)
        rows = _extract_list(data, ["Results", "Data", "Rows"])
        if rows:
            return rows
        return [data] if data else []

    def get_url_info(self, site_url: str, url: str) -> dict:
        payload = {"siteUrl": site_url, "url": url}
        data = self._call("GetUrlInfo", payload)
        if isinstance(data, dict):
            return data
        return {}

    def get_crawl_issues(self, site_url: str) -> list[dict]:
        data = self._call("GetCrawlIssues", {"siteUrl": site_url})
        return _extract_list(data, ["Results", "CrawlIssues", "UrlWithCrawlIssues"])

    def submit_url(self, site_url: str, url: str) -> dict:
        return self._call("SubmitUrl", {"siteUrl": site_url, "url": url})

    def submit_url_batch(self, site_url: str, urls: list[str]) -> dict:
        return self._call("SubmitUrlBatch", {"siteUrl": site_url, "urlList": urls})

    def _call(self, method: str, payload: dict) -> dict:
        method_mode = _http_mode(method)
        if method_mode == "GET":
            query = {"apikey": self.api_key, **payload}
            url = f"{self.base_url}/{method}?{urlencode(query)}"
            response = self.session.get(url, timeout=self.timeout)
        else:
            url = f"{self.base_url}/{method}?apikey={self.api_key}"
            response = self.session.post(url, json=payload, timeout=self.timeout)

        if response.status_code >= 400:
            detail = _extract_error_text(response)
            raise BingAPIError(
                f"{method} failed ({response.status_code}): {detail}",
                status_code=response.status_code,
                payload=_safe_json(response),
            )

        body = _safe_json(response)
        if not isinstance(body, dict):
            return {}

        container = body.get("d")
        if not isinstance(container, dict):
            return body

        method_key = f"{method}Result"
        if method_key in container:
            result = container.get(method_key)
            if isinstance(result, dict):
                return result
            return {"value": result}

        if method == "GetUserSites" and "Results" in container:
            return container

        for key, value in container.items():
            if key.endswith("Result") and isinstance(value, dict):
                return value

        return container


def _extract_error_text(response: requests.Response) -> str:
    payload = _safe_json(response)
    if isinstance(payload, dict):
        for key in ("Message", "message", "error_description", "error"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value

        d_payload = payload.get("d")
        if isinstance(d_payload, dict):
            message = d_payload.get("Message")
            if isinstance(message, str) and message.strip():
                return message

    return response.text.strip() or "Unknown error"


def _safe_json(response: requests.Response):
    try:
        return response.json()
    except ValueError:
        return {}


def _extract_list(payload: dict, preferred_keys: list[str]) -> list[dict]:
    for key in preferred_keys:
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    # Fallback for envelopes that return a single list-valued key.
    for value in payload.values():
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    return []


def _format_bing_date(value: date) -> str:
    return f"{value.month}/{value.day}/{value.year}"


def _http_mode(method: str) -> str:
    if method.startswith("Get"):
        return "GET"
    return "POST"
