# Evaluation Report — `run_gpt-4.1-mini_20260614_092224`

**Model:** `gpt-4.1-mini`  
**Mode:** `security`  
**Dataset:** 59 vulnerable + 25 safe snippets

## Overall Metrics

| Metric | Value |
|--------|-------|
| Detection Rate (Recall) | 81.4% |
| Precision | 96.0% |
| F1 Score | 88.1% |
| False Positive Rate | 8.0% |
| Avg Line Accuracy | 76.3% |

## Classification Matrix

| | Predicted Positive | Predicted Negative |
|---|---|---|
| **Actually Vulnerable** | TP: 48 | FN: 11 |
| **Actually Safe** | FP: 2 | TN: 23 |

## Detection by Category

| Category | Total | Detected | Recall |
|----------|-------|----------|--------|
| auth_bypass | 4 | 3 | 75% |
| broken_access_control | 6 | 5 | 83% |
| command_injection | 6 | 5 | 83% |
| hardcoded_secrets | 5 | 4 | 80% |
| information_disclosure | 2 | 2 | 100% |
| insecure_deserialization | 5 | 5 | 100% |
| misconfiguration | 1 | 0 | 0% |
| path_traversal | 5 | 3 | 60% |
| sql_injection | 7 | 6 | 86% |
| ssrf | 6 | 5 | 83% |
| unsafe_regex | 4 | 4 | 100% |
| weak_crypto | 3 | 2 | 67% |
| xss | 5 | 4 | 80% |

## Confidence Calibration

| Bin | Range | Total Findings | Correct | Accuracy |
|-----|-------|----------------|---------|----------|
| low | 0.0-0.3 | 0 | 0 | 0% |
| medium | 0.3-0.6 | 0 | 0 | 0% |
| high | 0.6-0.8 | 27 | 27 | 100% |
| very_high | 0.8-1.0 | 23 | 21 | 91% |

## Performance

| Metric | Value |
|--------|-------|
| Avg Summary Latency | 1234 ms |
| Avg Inline Latency | 804 ms |
| Avg Total Latency | 2038 ms |
| Total Tokens | 28,834 |
| Avg Tokens/Snippet | 343 |
| Est. Total Cost | $0.0183 |
| Est. Cost/Review | $0.000218 |
