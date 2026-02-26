"""Click CLI for Bing Webmaster API."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path

import click
import requests

from bingwm_cli import __version__
from bingwm_cli.auth import AuthError, auth_status, clear_stored_api_key, load_api_key, save_api_key
from bingwm_cli.client import BingAPIError, BingWebmasterClient
from bingwm_cli.config import ConfigError, get_default_site, set_default_site
from bingwm_cli.output import render_records

USER_INPUT_EXIT_CODE = 2
AUTH_EXIT_CODE = 3
API_EXIT_CODE = 4

CRAWL_ISSUE_FLAGS = {
    0: "None",
    1: "NotFound",
    2: "BlockedByRobotsTxt",
    4: "DisallowedByMetaTag",
    8: "Timeout",
    16: "ConnectionAborted",
    32: "ContainsMalware",
    64: "ContainsVirus",
    128: "InternalServerError",
    256: "UnsupportedContentType",
}


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """Bing Webmaster CLI."""


def command_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, ConfigError) as exc:
            click.echo(f"Error: {exc}", err=True)
            raise click.exceptions.Exit(USER_INPUT_EXIT_CODE) from exc
        except AuthError as exc:
            click.echo(f"Auth error: {exc}", err=True)
            raise click.exceptions.Exit(AUTH_EXIT_CODE) from exc
        except (BingAPIError, requests.RequestException) as exc:
            click.echo(f"API error: {exc}", err=True)
            raise click.exceptions.Exit(API_EXIT_CODE) from exc

    return wrapper


@cli.group()
def auth() -> None:
    """Manage API key authentication."""


@auth.command("login")
@click.option("--api-key", help="Bing Webmaster API key.")
@command_errors
def auth_login(api_key: str | None) -> None:
    """Store API key locally for future CLI calls."""
    key = api_key
    if not key:
        key = click.prompt("Bing Webmaster API key", hide_input=True, type=str)

    path = save_api_key(key)
    click.echo(f"Saved API key to {path}")


@auth.command("whoami")
@click.option("--output", "output_format", type=click.Choice(["table", "json"]), default="table")
@command_errors
def auth_whoami(output_format: str) -> None:
    """Show current auth source and key fingerprint."""
    status = auth_status()
    click.echo(render_records([status], output_format=output_format))


@auth.command("clear")
@command_errors
def auth_clear() -> None:
    """Clear locally stored API key file."""
    deleted = clear_stored_api_key()
    if deleted:
        click.echo("Removed local API key file.")
    else:
        click.echo("No local API key file found.")


@cli.group()
def config() -> None:
    """Manage CLI configuration."""


@config.group("set")
def config_set() -> None:
    """Set config values."""


@config_set.command("default-site")
@click.argument("site_url")
@command_errors
def config_set_default_site(site_url: str) -> None:
    """Set default site URL used when --site is omitted."""
    path = set_default_site(site_url)
    click.echo(f"Set default-site to {site_url}")
    click.echo(f"Config file: {path}")


@config.group("get")
def config_get() -> None:
    """Get config values."""


@config_get.command("default-site")
@command_errors
def config_get_default_site() -> None:
    """Get default site URL."""
    site_url = get_default_site()
    if not site_url:
        raise ValueError("default-site is not set.")
    click.echo(site_url)


@cli.group("site")
def site() -> None:
    """Site-level Bing Webmaster commands."""


@site.command("list")
@click.option("--output", "output_format", type=click.Choice(["table", "json", "csv"]), default="table")
@click.option("--csv-path", type=click.Path(dir_okay=False, path_type=str), help="CSV path when --output=csv")
@command_errors
def site_list(output_format: str, csv_path: str | None) -> None:
    """List websites available to this API key."""
    client = _build_client()
    sites = client.get_user_sites()
    records = [_normalize_site_record(item) for item in sites]
    click.echo(render_records(records, output_format=output_format, csv_path=csv_path))


@cli.group("stats")
def stats() -> None:
    """Traffic/ranking statistics commands."""


@stats.command("site")
@click.option("--site", "site_url", help="Site URL. Falls back to configured default site.")
@click.option("--start-date", type=str, help="Start date (YYYY-MM-DD). Defaults to 30 days ago.")
@click.option("--end-date", type=str, help="End date (YYYY-MM-DD). Defaults to today.")
@click.option("--output", "output_format", type=click.Choice(["table", "json", "csv"]), default="table")
@click.option("--csv-path", type=click.Path(dir_okay=False, path_type=str), help="CSV path when --output=csv")
@command_errors
def stats_site(
    site_url: str | None,
    start_date: str | None,
    end_date: str | None,
    output_format: str,
    csv_path: str | None,
) -> None:
    """Get site-level rank and traffic statistics."""
    resolved_site = _resolve_site(site_url)
    start, end = _resolve_date_range(start_date, end_date)
    client = _build_client()
    rows = client.get_rank_and_traffic_data(resolved_site, start, end)
    records = [_normalize_stat_record(row, resolved_site=resolved_site) for row in rows]
    click.echo(render_records(records, output_format=output_format, csv_path=csv_path))


@stats.command("url")
@click.option("--site", "site_url", help="Site URL. Falls back to configured default site.")
@click.option("--url", "url_value", required=True, help="Page URL.")
@click.option("--start-date", type=str, help="Start date (YYYY-MM-DD). Defaults to 30 days ago.")
@click.option("--end-date", type=str, help="End date (YYYY-MM-DD). Defaults to today.")
@click.option("--output", "output_format", type=click.Choice(["table", "json", "csv"]), default="table")
@click.option("--csv-path", type=click.Path(dir_okay=False, path_type=str), help="CSV path when --output=csv")
@command_errors
def stats_url(
    site_url: str | None,
    url_value: str,
    start_date: str | None,
    end_date: str | None,
    output_format: str,
    csv_path: str | None,
) -> None:
    """Get traffic statistics for a specific URL."""
    resolved_site = _resolve_site(site_url)
    start, end = _resolve_date_range(start_date, end_date)
    client = _build_client()
    rows = client.get_url_traffic_info(resolved_site, url_value, start, end)
    records = [_normalize_stat_record(row, resolved_site=resolved_site, url_value=url_value) for row in rows]
    click.echo(render_records(records, output_format=output_format, csv_path=csv_path))


@cli.group("url")
def url() -> None:
    """URL-level status and submission commands."""


@url.command("check-index")
@click.option("--site", "site_url", help="Site URL. Falls back to configured default site.")
@click.option("--url", "url_value", required=True, help="Page URL to inspect.")
@click.option("--output", "output_format", type=click.Choice(["table", "json"]), default="table")
@click.option("--explain", is_flag=True, help="Include richer diagnostics based on available API signals.")
@command_errors
def url_check_index(site_url: str | None, url_value: str, output_format: str, explain: bool) -> None:
    """Check if a URL is indexed by Bing and show known reasons if not."""
    resolved_site = _resolve_site(site_url)
    client = _build_client()

    info = client.get_url_info(resolved_site, url_value)
    indexed = _extract_is_indexed(info)
    reason = ""
    matched_issue = None
    explanations: list[str] = []

    if not indexed:
        crawl_issues = client.get_crawl_issues(resolved_site)
        matched_issue = _find_crawl_issue_for_url(crawl_issues, url_value)
        if matched_issue:
            reason = _format_issue_reason(matched_issue)
            explanations.append(f"Crawl issue: {reason}")
        else:
            reason = "No explicit crawl issue returned by Bing API for this URL."
            explanations.append(reason)

        if explain:
            explanations.extend(_build_explanation_hints(info))

    record = {
        "siteUrl": resolved_site,
        "url": url_value,
        "isIndexed": indexed,
        "reason": reason,
    }
    record.update(_pick_fields(info, ["HttpCode", "CrawlDate", "Date", "IsPage", "Indexable", "LastCrawlTime"]))
    if matched_issue:
        record.update(
            {
                "crawlIssueCode": matched_issue.get("Issues") or matched_issue.get("Issue"),
                "crawlIssueRaw": json.dumps(matched_issue, separators=(",", ":")),
            }
        )
    if explain:
        record["explanation"] = " | ".join(_unique_non_empty(explanations)) if explanations else ""

    click.echo(render_records([record], output_format=output_format))


@url.command("submit")
@click.option("--site", "site_url", help="Site URL. Falls back to configured default site.")
@click.option("--url", "urls", multiple=True, help="URL to submit (repeatable).")
@click.option(
    "--file",
    "file_path",
    type=click.Path(exists=True, dir_okay=False, path_type=str),
    help="Text file with one URL per line.",
)
@click.option("--output", "output_format", type=click.Choice(["table", "json"]), default="table")
@command_errors
def url_submit(site_url: str | None, urls: tuple[str, ...], file_path: str | None, output_format: str) -> None:
    """Submit one or more URLs for Bing indexing."""
    resolved_site = _resolve_site(site_url)
    url_list = _collect_urls(urls, file_path)
    if not url_list:
        raise ValueError("Provide at least one URL via --url or --file.")

    client = _build_client(write=True)
    if len(url_list) == 1:
        response = client.submit_url(resolved_site, url_list[0])
    else:
        response = client.submit_url_batch(resolved_site, url_list)

    record = {
        "siteUrl": resolved_site,
        "submittedCount": len(url_list),
        "status": "submitted",
        "response": json.dumps(response, separators=(",", ":")),
    }
    click.echo(render_records([record], output_format=output_format))


def _build_client(*, write: bool = False) -> BingWebmasterClient:
    # API key permission is managed server-side by Bing; write flag is kept for parity/future checks.
    del write
    key, _source = load_api_key()
    return BingWebmasterClient(api_key=key)


def _resolve_site(site_url: str | None) -> str:
    if site_url and site_url.strip():
        return site_url.strip()

    default_site = get_default_site()
    if default_site:
        return default_site

    raise ValueError(
        "No site specified. Pass --site or set one with `bwm config set default-site <siteUrl>`."
    )


def _resolve_date_range(start_date: str | None, end_date: str | None) -> tuple[date, date]:
    end = _parse_date(end_date) if end_date else date.today()
    start = _parse_date(start_date) if start_date else end - timedelta(days=30)
    if start > end:
        raise ValueError("start-date cannot be after end-date")
    return start, end


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"Invalid date '{value}'. Expected YYYY-MM-DD.") from exc


def _normalize_site_record(item: dict) -> dict:
    return {
        "siteUrl": item.get("Url") or item.get("siteUrl") or item.get("SiteUrl") or "",
        "permissionLevel": item.get("PermissionLevel") or item.get("permissionLevel") or "",
        "isVerified": item.get("IsVerified") if "IsVerified" in item else item.get("isVerified"),
    }


def _normalize_stat_record(row: dict, *, resolved_site: str, url_value: str | None = None) -> dict:
    record = dict(row)
    if "siteUrl" not in record:
        record["siteUrl"] = resolved_site
    if url_value and "url" not in record:
        record["url"] = url_value
    return record


def _extract_is_indexed(info: dict) -> bool:
    for key in ("IsIndexed", "isIndexed", "Indexed", "indexable"):
        value = info.get(key)
        if isinstance(value, bool):
            return value

    # Bing's GetUrlInfo may return IsPage=true even when URL is blocked/not serving.
    http_status = info.get("HttpStatus")
    last_crawled = info.get("LastCrawledDate")
    is_page = info.get("IsPage")
    discovery_date = info.get("DiscoveryDate")

    if isinstance(is_page, bool) and not is_page:
        return False

    has_valid_crawl = isinstance(last_crawled, str) and "-62135568000000" not in last_crawled
    has_valid_discovery = isinstance(discovery_date, str) and "-62135568000000" not in discovery_date
    has_success_status = http_status == 200

    return bool(has_success_status and (has_valid_crawl or has_valid_discovery))


def _find_crawl_issue_for_url(crawl_issues: list[dict], url_value: str) -> dict | None:
    url_lower = url_value.strip().lower()
    for issue in crawl_issues:
        issue_url = issue.get("Url") or issue.get("url")
        if isinstance(issue_url, str) and issue_url.strip().lower() == url_lower:
            return issue
    return None


def _format_issue_reason(issue: dict) -> str:
    code = issue.get("Issues") or issue.get("Issue")
    if isinstance(code, int):
        names = _decode_issue_flags(code)
        return ", ".join(names) if names else f"Unknown issue code: {code}"
    return f"Issue details: {json.dumps(issue, separators=(',', ':'))}"


def _decode_issue_flags(code: int) -> list[str]:
    if code == 0:
        return ["None"]

    names: list[str] = []
    remaining = code
    for flag, name in sorted(CRAWL_ISSUE_FLAGS.items()):
        if flag == 0:
            continue
        if code & flag:
            names.append(name)
            remaining &= ~flag

    if remaining:
        names.append(f"Unknown({remaining})")
    return names


def _pick_fields(payload: dict, keys: list[str]) -> dict:
    result: dict = {}
    for key in keys:
        if key in payload:
            result[key[0].lower() + key[1:]] = payload[key]
    return result


def _build_explanation_hints(info: dict) -> list[str]:
    hints: list[str] = []

    http_status = info.get("HttpStatus")
    if http_status == 0:
        hints.append("Bing reports HttpStatus=0 for this URL, which usually means no successful fetch was recorded.")
    elif isinstance(http_status, int):
        hints.append(f"Bing reports last known HttpStatus={http_status}.")

    discovery_date = info.get("DiscoveryDate")
    if isinstance(discovery_date, str) and "-62135568000000" in discovery_date:
        hints.append("DiscoveryDate is empty/sentinel in API, suggesting Bing has not discovered crawlable content for this URL.")

    last_crawled = info.get("LastCrawledDate")
    if isinstance(last_crawled, str) and "-62135568000000" in last_crawled:
        hints.append("LastCrawledDate is empty/sentinel in API, suggesting the URL has not been crawled successfully.")

    anchor_count = info.get("AnchorCount")
    if isinstance(anchor_count, int) and anchor_count == 0:
        hints.append("AnchorCount=0 in API, meaning Bing has no known inbound link signals for this URL.")

    document_size = info.get("DocumentSize")
    if isinstance(document_size, int) and document_size == 0:
        hints.append("DocumentSize=0 in API, indicating Bing has not stored page content for this URL.")

    return hints


def _unique_non_empty(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        value = item.strip()
        if not value or value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _collect_urls(urls: tuple[str, ...], file_path: str | None) -> list[str]:
    items = [item.strip() for item in urls if item and item.strip()]

    if file_path:
        for line in Path(file_path).read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                items.append(stripped)

    unique: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            unique.append(item)
            seen.add(item)
    return unique


if __name__ == "__main__":
    cli()
