# Evaluation Report — `run_meta_llama-3.1-70b-instruct_20260614_092224`

**Model:** `meta_llama-3.1-70b-instruct`  
**Mode:** `security`  
**Dataset:** 59 vulnerable + 25 safe snippets

## Overall Metrics

| Metric | Value |
|--------|-------|
| Detection Rate (Recall) | 84.8% |
| Precision | 98.0% |
| F1 Score | 90.9% |
| False Positive Rate | 4.0% |
| Avg Line Accuracy | 78.0% |

## Classification Matrix

| | Predicted Positive | Predicted Negative |
|---|---|---|
| **Actually Vulnerable** | TP: 50 | FN: 9 |
| **Actually Safe** | FP: 1 | TN: 24 |

## Detection by Category

| Category | Total | Detected | Recall |
|----------|-------|----------|--------|
| auth_bypass | 4 | 4 | 100% |
| broken_access_control | 6 | 5 | 83% |
| command_injection | 6 | 4 | 67% |
| hardcoded_secrets | 5 | 5 | 100% |
| information_disclosure | 2 | 1 | 50% |
| insecure_deserialization | 5 | 4 | 80% |
| misconfiguration | 1 | 1 | 100% |
| path_traversal | 5 | 5 | 100% |
| sql_injection | 7 | 7 | 100% |
| ssrf | 6 | 4 | 67% |
| unsafe_regex | 4 | 3 | 75% |
| weak_crypto | 3 | 3 | 100% |
| xss | 5 | 4 | 80% |

## Confidence Calibration

| Bin | Range | Total Findings | Correct | Accuracy |
|-----|-------|----------------|---------|----------|
| low | 0.0-0.3 | 0 | 0 | 0% |
| medium | 0.3-0.6 | 0 | 0 | 0% |
| high | 0.6-0.8 | 42 | 42 | 100% |
| very_high | 0.8-1.0 | 9 | 8 | 89% |

## Performance

| Metric | Value |
|--------|-------|
| Avg Summary Latency | 2521 ms |
| Avg Inline Latency | 1517 ms |
| Avg Total Latency | 4038 ms |
| Total Tokens | 28,914 |
| Avg Tokens/Snippet | 344 |
| Est. Total Cost | $0.0185 |
| Est. Cost/Review | $0.000220 |
