"""Date parsing helpers for Bing API payloads."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone

_BING_DATE_RE = re.compile(r"^/?Date\((?P<millis>-?\d+)(?P<offset>[+-]\d{4})?\)/?$")
_BING_SENTINEL_MILLIS = -62135568000000


def normalize_bing_date_string(value: str) -> str:
    match = _BING_DATE_RE.fullmatch(value.strip())
    if not match:
        return value

    millis = int(match.group("millis"))
    if millis == _BING_SENTINEL_MILLIS:
        return ""

    offset_text = match.group("offset")
    tz = timezone.utc
    if offset_text:
        sign = 1 if offset_text[0] == "+" else -1
        hours = int(offset_text[1:3])
        minutes = int(offset_text[3:5])
        tz = timezone(sign * timedelta(hours=hours, minutes=minutes))

    dt = datetime.fromtimestamp(millis / 1000, tz=timezone.utc).astimezone(tz)
    if dt.time() == datetime.min.time():
        return dt.date().isoformat()
    if dt.microsecond:
        return dt.isoformat(timespec="milliseconds")
    return dt.isoformat(timespec="seconds")


def coerce_date_value(value: object) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None

    normalized = normalize_bing_date_string(value)
    if not normalized:
        return None

    try:
        return date.fromisoformat(normalized)
    except ValueError:
        pass

    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        return None
