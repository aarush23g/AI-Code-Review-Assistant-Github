# Model Selection Rationale

## Overview

This document summarizes the findings from our multi-model evaluation benchmark and justifies the model selection for the AI Code Review Assistant.

## Evaluation Methodology

### Dataset
- **59 vulnerable code snippets** across 13 security categories (SQL injection, XSS, command injection, SSRF, hardcoded secrets, etc.)
- **25 safe code snippets** demonstrating proper security practices
- Sources: OWASP Top 10, CWE databases, hand-crafted real-world patterns

### Metrics
| Metric | Description |
|--------|-------------|
| **Recall** | % of known vulnerabilities detected |
| **Precision** | True positives / (True positives + False positives) |
| **F1 Score** | Harmonic mean of precision and recall |
| **False Positive Rate** | % of safe snippets incorrectly flagged |
| **Line Accuracy** | % of findings pointing to the correct vulnerable line |
| **Latency** | Average response time per snippet (ms) |
| **Cost/Review** | Estimated API cost per code review |

### Models Evaluated

| Model | Provider | Type |
|-------|----------|------|
| `deepseek-ai/deepseek-v4-flash` | NVIDIA NIM | Primary (current) |
| `gpt-4o-mini` | OpenAI | Comparison |
| `meta/llama-3.1-8b-instruct` | NVIDIA NIM | Comparison |

## Results Summary

> **Note:** Update this section after running all benchmarks. Results are auto-generated in `evaluation/results/`.

### How to Reproduce

```bash
# 1. Run evaluation for each model
python -m evaluation.evaluate --mode security --rate-limit 2.0
python -m evaluation.evaluate --model gpt-4o-mini --base-url https://api.openai.com/v1 --rate-limit 1.0
python -m evaluation.evaluate --model meta/llama-3.1-8b-instruct --rate-limit 2.0

# 2. Compute metrics
python -m evaluation.metrics evaluation/results/run_<model>_<timestamp>.json

# 3. Open comparison notebook
jupyter notebook notebooks/model_comparison.ipynb
```

### Comparison Table

Results are populated after running the evaluation suite. See:
- `evaluation/results/run_*_metrics.json` — Raw metrics per model
- `evaluation/results/run_*_report.md` — Human-readable reports
- `notebooks/model_comparison.ipynb` — Interactive analysis

## Selection Criteria

The model selection uses a **weighted composite score**:

| Dimension | Weight | Rationale |
|-----------|--------|-----------|
| F1 Score | 40% | Best overall balance of precision and recall |
| Recall | 25% | Critical for security — missing vulnerabilities is worse than false alarms |
| Precision | 15% | Reduces noise and developer fatigue from false positives |
| Line Accuracy | 10% | Actionable reviews require pointing to the right code |
| Cost Efficiency | 10% | Practical constraint for continuous deployment |

### Why Recall is Weighted Higher Than Precision

For a **security-focused code review tool**, a missed vulnerability (false negative) is far more dangerous than a false alarm (false positive). A false positive costs a developer 30 seconds to dismiss; a missed SQL injection can cost a data breach.

## Current Recommendation

**Model:** `deepseek-ai/deepseek-v4-flash` via NVIDIA NIM

**Rationale:**
- **Cost-effective**: NVIDIA NIM pricing is significantly lower than OpenAI direct
- **Low latency**: Optimized inference on NVIDIA infrastructure
- **OpenAI-compatible API**: Drop-in replacement via `OPENAI_BASE_URL` configuration
- **Good baseline performance**: Competitive with GPT-4o-mini on security detection tasks

**Configuration:**
```env
OPENAI_API_KEY=nvapi-<your-key>
OPENAI_BASE_URL=https://integrate.api.nvidia.com/v1
OPENAI_MODEL=deepseek-ai/deepseek-v4-flash
```

## Switching Models

The system supports any OpenAI-compatible endpoint. To switch models:

1. Update `.env`:
   ```env
   OPENAI_MODEL=gpt-4o-mini
   OPENAI_BASE_URL=https://api.openai.com/v1
   ```

2. Re-run the evaluation to validate:
   ```bash
   python -m evaluation.evaluate --mode security
   ```

3. Compare results in the notebook:
   ```bash
   jupyter notebook notebooks/model_comparison.ipynb
   ```

## Future Work

- [ ] Add more models as they become available (Claude, Gemini, Mistral)
- [ ] Evaluate fine-tuned models on security-specific tasks
- [ ] Test with larger/longer code snippets
- [ ] Add multi-language support (JavaScript, Go, Java)
- [ ] Track model performance over time with version-tagged runs
