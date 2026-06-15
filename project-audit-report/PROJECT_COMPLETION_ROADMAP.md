# AI Code Review Assistant - Project Completion Roadmap

This roadmap defines the gap analysis and maps out a phased execution plan to make the project fully production-ready.

---

## 1. Gap Analysis

| Area | Current State | Desired State | Gap |
| :--- | :--- | :--- | :--- |
| **Secrets Management** | Private RSA key committed in git root; plaintext API keys in `.env` | Git-clean history; secrets loaded securely via env or secret managers | 🔴 Private key leakage in repo history; exposed NIM credentials |
| **Concurrency & Scaling**| Webhooks block synchronously waiting for LLM reviews (takes 30s+) | Webhook acknowledges instantly; processing occurs in background queue | 🔴 Synchronous execution blocks requests and causes GitHub timeouts |
| **Monitoring Frontend** | Dashboard uses `review_metrics.db`; backend writes `review_metrics.sqlite3` | Dashboard aligns with backend db path for real-time operation charts | 🟡 Database path mismatch renders dashboard empty by default |
| **Benchmark Results** | Existing benchmark JSON run contains exceptions for all 84 snippets | Valid benchmark run results recorded with precision/recall accuracy | 🟡 0% benchmark data due to signature mismatch in a past execution |
| **Logging Quality** | JSON logs implemented but unconfigurable and disabled | Configurable text/JSON logs; JSON logs enabled in production | 🟢 `setup_logging` parameter `json_logs` is not exposed or enabled |
| **Multi-Model Compare** | Notebook setup exists but charts are blank/placeholder | Visualized accuracy charts comparing GPT-4o, DeepSeek, Llama | 🟢 No valid comparative benchmarking runs executed yet |

---

## 2. Phased Execution Plan

---

### Phase A: Critical Fixes
*Goal: Remove immediate execution blockers and security issues.*

#### A.1: Rotate and Remove Private Key
- **Description**: Delete `codesaver-ai.2026-05-04.private-key.pem` from the repository root, purge it from git history, and rotate the private key in the GitHub App developer console.
- **Estimated Effort**: 1 hour
- **Complexity**: Low
- **Dependencies**: Access to GitHub App console
- **Risk Level**: High (risk of breaking active webhooks until key is updated in host environment)

#### A.2: Correct Private Key Configuration Path Typo
- **Description**: Update the `.env` template to use the correct file name: `codesaver-ai.2026-05-04.private-key.pem` instead of `2026-054-04`.
- **Estimated Effort**: 15 minutes
- **Complexity**: Low
- **Dependencies**: None
- **Risk Level**: Low

#### A.3: Reconcile Metrics Database Paths
- **Description**: Update `dashboard/app.py` to check settings from `app.core.config` or read `review_metrics.sqlite3` so that Streamlit charts render backend metrics.
- **Estimated Effort**: 30 minutes
- **Complexity**: Low
- **Dependencies**: None
- **Risk Level**: Low

---

### Phase B: Core Feature Completion
*Goal: Resolve the webhook timeout issue and run benchmarks.*

#### B.1: Implement Asynchronous Background Review Tasks
- **Description**: Refactor the `/webhooks/github` route in `app/api/routes/webhook.py`. The endpoint should validate the signature, trigger a FastAPI `BackgroundTasks` runner, and immediately return `202 Accepted`.
- **Estimated Effort**: 3 hours
- **Complexity**: Medium
- **Dependencies**: None
- **Risk Level**: Medium (requires careful handling of error states since errors won't be returned directly in HTTP responses)

#### B.2: Execute Successful Evaluation Benchmark
- **Description**: Re-run the evaluation benchmark suite via `python -m evaluation.evaluate` to generate a valid, exception-free results file, and run `metrics.py` to calculate precision/recall metrics.
- **Estimated Effort**: 2 hours
- **Complexity**: Low
- **Dependencies**: Working API key and internet access
- **Risk Level**: Low

#### B.3: Populate Multi-Model Comparison Data
- **Description**: Run the evaluation suite against other models (e.g. `gpt-4o-mini` and `meta/llama-3.1-8b-instruct`), save results to `evaluation/results/`, and execute the comparison notebooks to generate radar charts.
- **Estimated Effort**: 2 hours
- **Complexity**: Medium
- **Dependencies**: Multi-model API keys/credits
- **Risk Level**: Low

---

### Phase C: Production Readiness
*Goal: Hardening for deployment.*

#### C.1: Expose and Enable JSON Logging
- **Description**: Add `LOG_JSON` setting to settings config, and update `app/main.py` to pass the flag to `setup_logging` so that JSON logging can be turned on in production environments.
- **Estimated Effort**: 45 minutes
- **Complexity**: Low
- **Dependencies**: None
- **Risk Level**: Low

#### C.2: Docker Volume Adjustments
- **Description**: Remove the directory bind mount (`.:/app`) from `docker-compose.yml` to prevent local development configurations from overriding the container file structure in production, and use named volumes for `data/` persistence.
- **Estimated Effort**: 30 minutes
- **Complexity**: Low
- **Dependencies**: Docker
- **Risk Level**: Low

---

### Phase D: Advanced Enhancements
*Goal: Extended capabilities.*

#### D.1: Distributed Task Queue Integration
- **Description**: For enterprise scale, replace FastAPI's memory-based `BackgroundTasks` with a broker-backed task queue like Redis + Celery/ARQ to ensure review jobs survive server crashes.
- **Estimated Effort**: 4 hours
- **Complexity**: Medium
- **Dependencies**: Redis instance
- **Risk Level**: Medium

#### D.2: Dynamic Token Cost Fetching
- **Description**: Connect the cost tracking engine to an LLM pricing service or config database rather than hardcoding static input/output token rates in metrics calculations.
- **Estimated Effort**: 2 hours
- **Complexity**: Low
- **Dependencies**: Pricing API
- **Risk Level**: Low
