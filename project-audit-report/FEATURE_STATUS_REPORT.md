# AI Code Review Assistant - Feature Status Report

This report catalogs all features discovered in the repository, analyzing their current status, technical evidence, and remaining work.

---

## 1. Feature Inventory & Status Matrix

| Feature / Component | Description | Current Status | Evidence | Remaining Work |
| :--- | :--- | :--- | :--- | :--- |
| **HMAC Signature Check** | Webhook request signature verification using SHA-256 HMAC | **Completed** | `app/core/security.py`, `app/api/routes/webhook.py` | None |
| **Persistent HTTP Client** | Persistent GitHub client reuse via `httpx.AsyncClient` | **Completed** | `app/github/client.py` | None |
| **Token Caching** | Cached GitHub installation tokens with auto-renewal before expiry | **Completed** | `app/github/client.py` | None |
| **Diff Filtering** | Ignores lockfiles, binary files, node_modules, and custom paths | **Completed** | `app/review/diff_parser.py`, `app/review/rules.py` | None |
| **Diff Chunker** | Splits git patches into token-safe character chunks | **Completed** | `app/review/chunker.py` | None |
| **Line Mapping** | Restricts comments to changed target-side lines only | **Completed** | `app/review/line_mapper.py` | None |
| **Orchestrated Strategy** | Choose quick summary, full review, or skip based on size | **Completed** | `app/review/orchestrator.py` | None |
| **LLM Resilience** | Retry decorators, JSON error recovery, and token caps | **Completed** | `app/review/llm_reviewer.py` | None |
| **Comment Capping** | Limit maximum inline comments posted per PR | **Completed** | `app/review/post_processor.py` | None |
| **Comment Updating** | Updates the bot's summary comment on push instead of spamming | **Completed** | `app/services/review_service.py` | None |
| **Async Metrics Save** | Async SQLite logging of review status, tokens, cost, and duration | **Completed** | `app/storage/metrics_store.py` | None |
| **Enhanced Health Checks** | Health route checking SQLite query execution and LLM settings | **Completed** | `app/api/routes/health.py` | None |
| **Developer CI/CD** | GitHub Action checks running tests, formatters, and linter | **Completed** | `.github/workflows/ci.yml` | None |
| **Streamlit Dashboard** | UI to visualize costs, latency, operations, and models | **Mostly Complete** | `dashboard/app.py` | Database file naming alignment (discrepancy between `.sqlite3` and `.db`) |
| **Webhook Processing** | Server processing of webhook events | **Mostly Complete** | `app/api/routes/webhook.py` | Typos in PEM private key configurations preventing key load |
| **Benchmarking Suite** | Script to execute and score LLM reviews against 84 snippets | **Mostly Complete** | `evaluation/evaluate.py`, `evaluation/metrics.py` | Re-running the benchmark successfully (the current dataset results file contains execution errors) |
| **Background Processing** | Asynchronously defer reviews so webhooks don't block the request | **Stubbed / Planned** | — | Implement a background queue worker task |
| **Multi-Model Compare** | Benchmarking across multiple providers (NIM, OpenAI, Llama) | **Planned / Unfinished** | `notebooks/model_comparison.ipynb` | Run actual benchmark runs across 3+ providers to generate results |

---

## 2. GitHub Integration Audit

### What's Working:
1. **GitHub App Token Caching**: In `app/github/client.py`, installation access tokens are successfully cached by `installation_id` with expiration tracking, reducing duplicate token generation requests.
2. **Signature Integrity**: Webhooks successfully enforce signature checking against `GITHUB_WEBHOOK_SECRET` via `verify_github_signature` inside `app/core/security.py`.
3. **PR Comments Posting**: Supports creating and updating issue comments (`create_issue_comment`, `update_issue_comment`) to prevent spamming multiple summary reviews. Inline comments are supported via `create_pull_request_review_comment`.

### What's Missing / Incomplete:
1. **GitHub App Private Key Path Typo**: In `.env`, line 9 defines:
   `GITHUB_PRIVATE_KEY_PATH=D:\ai-code-review-assistant\codesaver-ai.2026-054-04.private-key.pem`
   However, the file checked into the root directory is actually named:
   `codesaver-ai.2026-05-04.private-key.pem` (note the `05` vs `054` difference).
   This causes `load_github_private_key()` in `app/github/auth.py` to raise `FileNotFoundError` whenever a webhook executes.
2. **Webhook Timeout**: Incoming webhooks block on the FastAPI request thread while making API calls to fetch PR files, execute summary LLM requests, execute inline findings LLM requests, and write comments. Because this process takes upwards of 30+ seconds, the connection will hit GitHub's 10-second webhook delivery timeout, leading to webhook delivery failures on GitHub.

---

## 3. AI Review Engine Audit

### What's Working:
1. **Structured Outputs**: Fully structures and validates prompts, parsing LLM output back into Pydantic schemas (`PRSummaryReview` and `InlineReviewResult`) using JSON mode `response_format={"type": "json_object"}`.
2. **Tenacity Retries**: LLM requests are wrapped in robust retry handlers that back off on API connection failures, rate limits, timeouts, and internal server errors.
3. **JSON Structure Recovery**: In `app/review/llm_reviewer.py`, if the model returns malformed JSON, a fallback request is triggered with temperature `0.0` and a strict instruction format: `"Your previous response was not valid JSON. Please respond ONLY with a valid JSON object."`
4. **Context Clamping**: Filters out large files and partitions diff patches into token-safe chunks, and limits overall review depth using `max_review_chunks` and `max_review_files`.

### What's Missing / Incomplete:
1. **Token Cost Modeling Rates**: Token cost calculations in `evaluation/metrics.py` (lines 28-29) and `dashboard/app.py` (lines 231-235) use hardcoded pricing values (`$0.0004` per 1K input, `$0.0016` per 1K output) which does not align with modern LLM costs.

---

## 4. Frontend Audit (Streamlit Dashboard)

### What's Working:
1. **Operations Tab**: Displays review operations over time, status breakdown, mode breakdown, and a review history log.
2. **Token Usage Tab**: Displays token distribution, average tokens, cost settings, and repo-level trends.
3. **Quality Tab**: Renders issues found by severity, comments posted vs findings generated funnel, and a latency histogram.
4. **Model Performance Tab**: Parses benchmark JSON run results, rendering recall, precision, line accuracy, and cost comparisons.

### What's Missing / Incomplete:
1. **Database Path Mismatch**: The dashboard `DB_PATH` is hardcoded to `review_metrics.db` in `dashboard/app.py` line 60. However, the FastAPI backend writes metrics to `review_metrics.sqlite3` (defined in `app/core/config.py` line 23 and `.env` line 26). As a result, the dashboard starts up empty and does not reflect any reviews.

---

## 5. Dead Code & Cleanup Analysis

1. **`codesaver-ai.2026-05-04.private-key.pem`**:
   This is a real private key checked directly into the git repository. While technically used by the local app to generate token signatures, it poses a severe security risk and should be deleted from git history, rotated, and loaded through secure volume mounts or environment values.
2. **`strategic_upgraded_plan.md`**:
   An internal development plan from an upgrade phase. While containing checklists of the steps required to clean up, configure, and benchmark the app, all checkboxes are unchecked. However, checking the code reveals that Phase 0, Phase 1, Phase 2, and Phase 4 were largely implemented. This file is now redundant and should be cleaned up.

---

## 6. Upgrade Detection & WIP Gaps

An analysis of the repository history and comparison against `strategic_upgraded_plan.md` reveals that the project underwent a significant upgrade to support structured outputs, tenacity retries, evaluation benchmarking, and a Streamlit dashboard. 

The following WIP upgrades remain unfinished:
1. **Multi-Model Comparison**: The `notebooks/model_comparison.ipynb` notebook and `docs/MODEL_SELECTION.md` are present but contain placeholder/empty cells or stubbed tables because the benchmark runner was never successfully executed on multiple models (due to prompt builder exceptions).
2. **Evaluation Benchmark Run Recovery**: The only evaluation results file in the repository (`evaluation/results/run_20260504_121707.json`) contains exceptions for every test snippet:
   - `build_pr_summary_review_prompt() got an unexpected keyword argument 'review_chunks'`
   - `build_inline_findings_prompt() got an unexpected keyword argument 'chunk'`
   These errors occurred because the prompt functions were modified to expect `pr_context` and `review_chunk`, but `evaluate.py` was not updated at that time. While the code in `evaluate.py` has since been fixed, a new successful benchmark run has not been executed, meaning the dashboard's model performance analytics are blank or display 0% metrics.
