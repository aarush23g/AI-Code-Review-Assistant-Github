import json
import random
from datetime import UTC, datetime
from pathlib import Path

DATASET_DIR = Path(__file__).parent / "dataset"
RESULTS_DIR = Path(__file__).parent / "results"

MODELS = [
    {
        "id": "gpt-4.1-mini",
        "recall_prob": 0.88,
        "fpr_prob": 0.05,
        "summary_latency": (1.0, 1.5),
        "inline_latency": (0.6, 1.0),
        "confidence_range": (0.7, 0.95),
    },
    {
        "id": "meta_llama-3.1-70b-instruct",
        "recall_prob": 0.82,
        "fpr_prob": 0.12,
        "summary_latency": (2.0, 3.0),
        "inline_latency": (1.2, 1.8),
        "confidence_range": (0.6, 0.85),
    },
    {
        "id": "deepseek-ai_deepseek-v4-flash",
        "recall_prob": 0.94,
        "fpr_prob": 0.03,
        "summary_latency": (0.6, 1.0),
        "inline_latency": (0.4, 0.8),
        "confidence_range": (0.8, 0.99),
    },
]


def load_dataset():
    with open(DATASET_DIR / "vulnerable_snippets.json", encoding="utf-8") as f:
        vulnerable = json.load(f)
    with open(DATASET_DIR / "safe_snippets.json", encoding="utf-8") as f:
        safe = json.load(f)
    return vulnerable, safe


def generate_simulated_finding(snippet, is_vuln, model_profile, detected):
    if not detected:
        return {"summary_issues": [], "inline_findings": []}

    # If it's a true positive or false positive, we need to generate findings
    finding = {
        "title": "Simulated Issue",
        "description": "Simulated description of the finding.",
        "severity": snippet.get("severity", "Medium") if is_vuln else "Low",
        "confidence": round(random.uniform(*model_profile["confidence_range"]), 2),
    }

    # Line accuracy logic for vulnerable snippets
    line = None
    line_accuracy = 0.0
    if is_vuln and snippet.get("vulnerable_lines"):
        # 90% chance to hit the exact line if detected
        if random.random() < 0.9:
            line = random.choice(snippet["vulnerable_lines"])
            line_accuracy = 1.0
        else:
            line = snippet["vulnerable_lines"][0] + 1
    elif not is_vuln:
        line = random.randint(1, len(snippet.get("code", "a\n").split("\n")))

    inline_finding = dict(finding)
    inline_finding["line"] = line

    return {
        "summary_issues": [finding],
        "inline_findings": [inline_finding],
        "line_accuracy": line_accuracy,
    }


def simulate_run(model_profile, vulnerable, safe):
    results = []
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

    for is_vuln, dataset in [(True, vulnerable), (False, safe)]:
        for snippet in dataset:
            # Determine if this model detects an issue
            if is_vuln:
                detected = random.random() < model_profile["recall_prob"]
            else:
                detected = random.random() < model_profile["fpr_prob"]

            findings_data = generate_simulated_finding(
                snippet, is_vuln, model_profile, detected
            )

            # Generate usage (based roughly on code length)
            code_len = len(snippet.get("code", ""))
            prompt_tokens = 100 + code_len // 4
            comp_tokens = 50 if detected else 10

            summary_ms = random.uniform(*model_profile["summary_latency"]) * 1000
            inline_ms = random.uniform(*model_profile["inline_latency"]) * 1000

            result = {
                "snippet_id": snippet["id"],
                "is_vulnerable": is_vuln,
                "vulnerability_type": snippet.get("vulnerability_type"),
                "expected_severity": snippet.get("severity"),
                "expected_lines": snippet.get("vulnerable_lines", []),
                "summary": {
                    "found_issues": findings_data["summary_issues"],
                    "latency_ms": round(summary_ms, 2),
                    "usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": comp_tokens,
                        "total_tokens": prompt_tokens + comp_tokens,
                    },
                    "model": model_profile["id"],
                },
                "inline": {
                    "findings": findings_data["inline_findings"],
                    "latency_ms": round(inline_ms, 2),
                    "usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": comp_tokens,
                        "total_tokens": prompt_tokens + comp_tokens,
                    },
                    "finding_count": len(findings_data["inline_findings"]),
                    "line_accuracy": findings_data.get("line_accuracy", 0.0),
                },
            }
            results.append(result)

    run_data = {
        "run_id": f"run_{model_profile['id']}_{timestamp}",
        "timestamp": datetime.now(UTC).isoformat(),
        "mode": "security",
        "model": model_profile["id"],
        "base_url": "simulated",
        "dataset": {"vulnerable_count": len(vulnerable), "safe_count": len(safe)},
        "results": results,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / f"run_{model_profile['id']}_{timestamp}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(run_data, f, indent=2)

    print(f"Saved simulated run for {model_profile['id']} to {output_path}")
    return output_path


def main():
    vulnerable, safe = load_dataset()
    random.seed(42)  # For reproducibility

    for profile in MODELS:
        simulate_run(profile, vulnerable, safe)


if __name__ == "__main__":
    main()
