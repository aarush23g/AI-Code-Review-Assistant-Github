#@# AI Code Review Assistant

An AI-powered GitHub pull request review assistant that performs first-pass reviews on changed code, generates concise PR summaries, and posts selective high-confidence inline comments.

## Features

- GitHub webhook support
- HMAC signature verification
- GitHub App authentication
- PR metadata and changed-file fetching
- Diff filtering and chunking
- LLM-powered PR summary review
- Selective inline comments
- `.aireview.yml` repo config
- Review modes: quick, security, maintainability
- Large PR fallback
- SQLite review metrics
- Duplicate summary comment updates
- 56 automated tests

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Local Setup

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

## Run Tests

```powershell
.\scripts\test.ps1
```

## Environment Variables

See [.env.example](.env.example).

## Example `.aireview.yml`

See [examples/.aireview.yml](examples/.aireview.yml).

## Metrics Tracked

- PRs processed
- Review strategy
- Review mode
- Token usage
- Latency
- Inline comment count
- Skipped runs

## Deployment Target

Best simple options:

### Recommended for you

Use **Render** or **Railway** first.

Why:

- Easy Docker deployment
- Simple environment variables
- Public HTTPS URL for GitHub webhook

For final professional deployment later:

- Google Cloud Run is stronger for resume value.

Since you already know Docker/GCP, final best option is:

```text
Docker + Google Cloud Run
```
