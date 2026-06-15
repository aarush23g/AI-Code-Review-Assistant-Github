# Evaluation Dataset

## Overview

This dataset is designed to benchmark the AI Code Review Assistant's ability to detect security vulnerabilities in Python code. It contains **60 vulnerable snippets** and **25 safe snippets** for measuring detection accuracy and false positive rates.

## Files

| File | Description | Count |
|------|-------------|-------|
| `vulnerable_snippets.json` | Code with known security vulnerabilities | 60 |
| `safe_snippets.json` | Clean code following security best practices | 25 |

## Vulnerability Categories

| Category | Count | CWE Reference |
|----------|-------|---------------|
| SQL Injection | 7 | CWE-89 |
| Path Traversal | 5 | CWE-22 |
| Cross-Site Scripting (XSS) | 5 | CWE-79 |
| Command Injection | 6 | CWE-78 |
| Authentication Bypass | 4 | CWE-287 |
| Broken Access Control | 5 | CWE-284 |
| Insecure Deserialization | 5 | CWE-502 |
| Server-Side Request Forgery (SSRF) | 6 | CWE-918 |
| Hardcoded Secrets | 5 | CWE-798 |
| Unsafe Regex (ReDoS) | 4 | CWE-1333 |
| Weak Cryptography | 3 | CWE-327/328 |
| Misconfiguration / Info Disclosure | 5 | CWE-209/215 |

## Schema

### Vulnerable Snippet

```json
{
  "id": "sqli-001",
  "code": "def get_user(username):\n    query = f\"SELECT * FROM users WHERE name = '{username}'\"\n    ...",
  "language": "python",
  "vulnerability_type": "sql_injection",
  "severity": "high",
  "vulnerable_lines": [2],
  "description": "String interpolation in SQL query allows injection"
}
```

### Safe Snippet

```json
{
  "id": "safe-001",
  "code": "def get_user(username):\n    return db.execute('SELECT * FROM users WHERE name = ?', (username,)).fetchone()",
  "language": "python",
  "description": "Parameterized SQL query"
}
```

## Sources

- **OWASP Top 10 (2021)**: Primary vulnerability categories
- **CWE/SANS Top 25**: Additional weakness patterns
- **Hand-crafted examples**: Realistic patterns from real-world codebases

## Usage

```bash
# Run evaluation against the dataset
python -m evaluation.evaluate --mode security

# Run with specific model
python -m evaluation.evaluate --model gpt-4.1-mini --mode security
```
