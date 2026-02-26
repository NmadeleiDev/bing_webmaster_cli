"""Output rendering helpers."""

from __future__ import annotations

import csv
import json
from pathlib import Path


def render_records(records: list[dict], output_format: str, csv_path: str | None = None) -> str:
    if output_format == "json":
        return json.dumps(records, indent=2)

    if output_format == "csv":
        if not csv_path:
            raise ValueError("csv_path is required when output format is csv")
        _write_csv(records, csv_path)
        return f"Wrote {len(records)} row(s) to {csv_path}"

    if output_format == "table":
        return _render_table(records)

    raise ValueError(f"Unsupported output format: {output_format}")


def _write_csv(records: list[dict], csv_path: str) -> None:
    path = Path(csv_path)
    fieldnames: list[str] = []

    for record in records:
        for key in record.keys():
            if key not in fieldnames:
                fieldnames.append(key)

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if fieldnames:
            writer.writeheader()
            writer.writerows(records)


def _render_table(records: list[dict]) -> str:
    if not records:
        return "No rows found."

    headers: list[str] = []
    for record in records:
        for key in record.keys():
            if key not in headers:
                headers.append(key)

    widths = {key: len(key) for key in headers}
    for record in records:
        for key in headers:
            cell = "" if record.get(key) is None else str(record.get(key))
            widths[key] = max(widths[key], len(cell))

    lines = [
        " | ".join(key.ljust(widths[key]) for key in headers),
        "-+-".join("-" * widths[key] for key in headers),
    ]

    for record in records:
        lines.append(
            " | ".join(
                ("" if record.get(key) is None else str(record.get(key))).ljust(widths[key])
                for key in headers
            )
        )

    return "\n".join(lines)
