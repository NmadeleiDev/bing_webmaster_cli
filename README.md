# bing-webmaster-cli

CLI for Bing Webmaster API using API-key authentication.

## Features

- API key auth from `BING_WEBMASTER_API_KEY` or local stored credentials
- List sites available to your Bing Webmaster account
- Site and URL traffic stats
- URL index check with crawl-issue reason hints when URL is not indexed
- Submit one URL or a batch of URLs for indexing
- Output formats: `table`, `json`, `csv`

## Install (Recommended)

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install bing-webmaster-cli
```

Verify:

```bash
bwm --version
```

## Install From Source

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Authentication

The CLI reads API key from:

1. `BING_WEBMASTER_API_KEY` environment variable
2. local credentials file (`~/.config/bing-webmaster-cli/credentials.json`)

Store key locally:

```bash
bwm auth login --api-key "<your-api-key>"
```

Or interactive prompt:

```bash
bwm auth login
```

Check auth source:

```bash
bwm auth whoami
```

Clear local key:

```bash
bwm auth clear
```

## Optional Default Site

```bash
bwm config set default-site https://example.com
bwm config get default-site
```

## Usage

### Sites

```bash
bwm site list
bwm site list --output json
```

### Stats

Site-level stats:

```bash
bwm stats site --site https://example.com --start-date 2026-02-01 --end-date 2026-02-26
```

URL-level stats:

```bash
bwm stats url --site https://example.com --url https://example.com/page --start-date 2026-02-01 --end-date 2026-02-26
```

Save as CSV:

```bash
bwm stats site --site https://example.com --output csv --csv-path ./site-stats.csv
```

### URL Indexing

Check if a URL is indexed by Bing:

```bash
bwm url check-index --site https://example.com --url https://example.com/page
```

If not indexed, CLI attempts to map crawl issue flags from `GetCrawlIssues` and prints the likely reason.

### URL Submission

Submit one URL:

```bash
bwm url submit --site https://example.com --url https://example.com/new-page
```

Submit many URLs:

```bash
bwm url submit --site https://example.com \
  --url https://example.com/a \
  --url https://example.com/b
```

Submit URLs from file (one URL per line):

```bash
bwm url submit --site https://example.com --file ./urls.txt
```

## Config Paths

Defaults:

- credentials: `~/.config/bing-webmaster-cli/credentials.json`
- app config: `~/.config/bing-webmaster-cli/config.json`

Overrides:

- `BWM_CONFIG_DIR`
- `BWM_CREDENTIALS_FILE`
- `BWM_APP_CONFIG_FILE`
- `BWM_API_BASE_URL`

## API References

This CLI is based on Microsoft Bing Webmaster API docs:

- Getting access: `https://learn.microsoft.com/en-us/bingwebmaster/getting-access`
- API interfaces: `https://learn.microsoft.com/en-us/dotnet/api/microsoft.bing.webmaster.api.interfaces?view=bing-webmaster-dotnet`

## Publishing

### Trusted Publishing via GitHub Actions (Recommended)

This repo includes `.github/workflows/publish.yml`.

Release flow:

1. Bump version in `pyproject.toml`.
2. Commit and push.
3. Tag and push:

```bash
git tag v0.1.0
git push origin v0.1.0
```

### Manual publishing

```bash
python -m pip install --upgrade build twine
python -m build
python -m twine upload dist/*
```
