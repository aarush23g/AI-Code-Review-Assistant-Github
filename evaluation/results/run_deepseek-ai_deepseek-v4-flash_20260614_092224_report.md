# Evaluation Report — `run_deepseek-ai_deepseek-v4-flash_20260614_092224`

**Model:** `deepseek-ai_deepseek-v4-flash`  
**Mode:** `security`  
**Dataset:** 59 vulnerable + 25 safe snippets

## Overall Metrics

| Metric | Value |
|--------|-------|
| Detection Rate (Recall) | 96.6% |
| Precision | 100.0% |
| F1 Score | 98.3% |
| False Positive Rate | 0.0% |
| Avg Line Accuracy | 86.4% |

## Classification Matrix

| | Predicted Positive | Predicted Negative |
|---|---|---|
| **Actually Vulnerable** | TP: 57 | FN: 2 |
| **Actually Safe** | FP: 0 | TN: 25 |

## Detection by Category

| Category | Total | Detected | Recall |
|----------|-------|----------|--------|
| auth_bypass | 4 | 4 | 100% |
| broken_access_control | 6 | 6 | 100% |
| command_injection | 6 | 6 | 100% |
| hardcoded_secrets | 5 | 4 | 80% |
| information_disclosure | 2 | 1 | 50% |
| insecure_deserialization | 5 | 5 | 100% |
| misconfiguration | 1 | 1 | 100% |
| path_traversal | 5 | 5 | 100% |
| sql_injection | 7 | 7 | 100% |
| ssrf | 6 | 6 | 100% |
| unsafe_regex | 4 | 4 | 100% |
| weak_crypto | 3 | 3 | 100% |
| xss | 5 | 5 | 100% |

## Confidence Calibration

| Bin | Range | Total Findings | Correct | Accuracy |
|-----|-------|----------------|---------|----------|
| low | 0.0-0.3 | 0 | 0 | 0% |
| medium | 0.3-0.6 | 0 | 0 | 0% |
| high | 0.6-0.8 | 0 | 0 | 0% |
| very_high | 0.8-1.0 | 57 | 57 | 100% |

## Performance

| Metric | Value |
|--------|-------|
| Avg Summary Latency | 810 ms |
| Avg Inline Latency | 590 ms |
| Avg Total Latency | 1400 ms |
| Total Tokens | 29,394 |
| Avg Tokens/Snippet | 350 |
| Est. Total Cost | $0.0192 |
| Est. Cost/Review | $0.000229 |
