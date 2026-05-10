# AI Code Review Assistant

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
