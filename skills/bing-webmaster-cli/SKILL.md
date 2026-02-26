# Bing Webmaster CLI Skill

Use this skill to operate `bing-webmaster-cli` (`bwm`) for Bing Webmaster API tasks.

## What this CLI does

- Authenticate with Bing Webmaster API using API key (env var or locally stored key)
- List sites available to the authenticated account
- Fetch site and URL traffic stats
- Check whether a URL is indexed
- Submit URLs for indexing

## Install

### Option 1: Install from PyPI with pipx (recommended)

```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install bing-webmaster-cli
bwm --version
```

### Option 2: Install with pip

```bash
python3 -m pip install bing-webmaster-cli
bwm --version
```

### Option 3: Run from source repo

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python3 -m bingwm_cli.cli --help
```

## Create Bing Webmaster API Key

1. Sign in to Bing Webmaster Tools: `https://www.bing.com/webmasters/`
2. Open API access/key management from account settings (as documented in Bing Webmaster “Getting access”).
3. Generate a new API key.
4. Copy it immediately and store it securely.

Reference: `https://learn.microsoft.com/en-us/bingwebmaster/getting-access`

## Configure API key in CLI

### A) Environment variable (best for CI and ephemeral sessions)

```bash
export BING_WEBMASTER_API_KEY="<your_api_key>"
bwm auth whoami
```

### B) Local stored key via auth command

```bash
bwm auth login --api-key "<your_api_key>"
bwm auth whoami
```

Interactive prompt:

```bash
bwm auth login
```

Clear local stored key:

```bash
bwm auth clear
```

## Optional default site

Set once so `--site` can be omitted in most commands:

```bash
bwm config set default-site https://example.com/
bwm config get default-site
```

## Commands

## Auth commands

```bash
bwm auth login --api-key "<your_api_key>"
bwm auth whoami
bwm auth clear
```

## Site commands

List all sites available to the API key:

```bash
bwm site list
bwm site list --output json
bwm site list --output csv --csv-path ./sites.csv
```

## Stats commands

Site-level traffic/rank stats:

```bash
bwm stats site --site https://example.com/
bwm stats site --site https://example.com/ --start-date 2026-02-01 --end-date 2026-02-26
bwm stats site --site https://example.com/ --output csv --csv-path ./site-stats.csv
```

URL-level traffic stats:

```bash
bwm stats url --site https://example.com/ --url https://example.com/page
bwm stats url --site https://example.com/ --url https://example.com/page --output json
```

## URL commands

Check index status:

```bash
bwm url check-index --site https://example.com/ --url https://example.com/page
bwm url check-index --site https://example.com/ --url https://example.com/page --output json
bwm url check-index --site https://example.com/ --url https://example.com/page --output json --explain
```

Submit one URL:

```bash
bwm url submit --site https://example.com/ --url https://example.com/new-page
```

Submit multiple URLs (repeatable flag):

```bash
bwm url submit --site https://example.com/ \
  --url https://example.com/page-a \
  --url https://example.com/page-b
```

Submit from file (one URL per line):

```bash
bwm url submit --site https://example.com/ --file ./urls.txt
```

## Output formats

Where supported:

- `--output table` (default)
- `--output json`
- `--output csv --csv-path <file>`

## Config/environment paths

- API key env var: `BING_WEBMASTER_API_KEY`
- Config dir override: `BWM_CONFIG_DIR`
- Credentials file override: `BWM_CREDENTIALS_FILE`
- App config file override: `BWM_APP_CONFIG_FILE`
- API base URL override: `BWM_API_BASE_URL`

Default local files:

- `~/.config/bing-webmaster-cli/credentials.json`
- `~/.config/bing-webmaster-cli/config.json`
