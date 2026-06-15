"""
Metrics calculator for evaluation runs.

Computes detection rate, false positive rate, precision, recall, F1,
line accuracy, confidence calibration, latency/token stats, and cost estimates.

Usage:
    python -m evaluation.metrics evaluation/results/run_<timestamp>.json
    python -m evaluation.metrics evaluation/results/run_<timestamp>.json --cost-per-1k-tokens 0.002
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def load_run(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def compute_metrics(
    run_data: dict[str, Any],
    cost_per_1k_input: float = 0.0004,
    cost_per_1k_output: float = 0.0016,
) -> dict[str, Any]:
    """Compute all evaluation metrics from a run."""
    results = run_data["results"]

    # Separate vulnerable vs safe
    vulnerable = [r for r in results if r["is_vulnerable"]]
    safe = [r for r in results if not r["is_vulnerable"]]

    # --- Detection rate (recall) ---
    true_positives = 0
    false_negatives = 0
    for r in vulnerable:
        summary_issues = r.get("summary", {}).get("found_issues", [])
        inline_findings = r.get("inline", {}).get("findings", [])
        detected = len(summary_issues) > 0 or len(inline_findings) > 0
        if detected:
            true_positives += 1
        else:
            false_negatives += 1

    # --- False positive rate ---
    false_positives = 0
    true_negatives = 0
    for r in safe:
        summary_issues = r.get("summary", {}).get("found_issues", [])
        inline_findings = r.get("inline", {}).get("findings", [])
        flagged = len(summary_issues) > 0 or len(inline_findings) > 0
        if flagged:
            false_positives += 1
        else:
            true_negatives += 1

    total_vulnerable = len(vulnerable)
    total_safe = len(safe)

    recall = true_positives / total_vulnerable if total_vulnerable > 0 else 0.0
    fpr = false_positives / total_safe if total_safe > 0 else 0.0
    precision = (
        true_positives / (true_positives + false_positives)
        if (true_positives + false_positives) > 0
        else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    # --- Line accuracy ---
    line_accuracies = []
    for r in vulnerable:
        la = r.get("inline", {}).get("line_accuracy")
        if la is not None:
            line_accuracies.append(la)
    avg_line_accuracy = (
        sum(line_accuracies) / len(line_accuracies) if line_accuracies else 0.0
    )

    # --- Confidence calibration ---
    confidence_bins: dict[str, dict[str, Any]] = {}
    bin_edges = [
        (0.0, 0.3, "low"),
        (0.3, 0.6, "medium"),
        (0.6, 0.8, "high"),
        (0.8, 1.0, "very_high"),
    ]
    for bin_low, bin_high, label in bin_edges:
        confidence_bins[label] = {
            "total": 0,
            "correct": 0,
            "range": f"{bin_low}-{bin_high}",
        }

    for r in results:
        is_vuln = r["is_vulnerable"]
        findings = r.get("inline", {}).get("findings", [])
        for f in findings:
            conf = f.get("confidence", 0)
            for bin_low, bin_high, label in bin_edges:
                if bin_low <= conf < bin_high or (bin_high == 1.0 and conf == 1.0):
                    confidence_bins[label]["total"] += 1
                    if is_vuln:
                        confidence_bins[label]["correct"] += 1
                    break

    for label in confidence_bins:
        total = confidence_bins[label]["total"]
        correct = confidence_bins[label]["correct"]
        confidence_bins[label]["accuracy"] = correct / total if total > 0 else 0.0

    # --- Latency stats ---
    summary_latencies = []
    inline_latencies = []
    for r in results:
        sl = r.get("summary", {}).get("latency_ms")
        il = r.get("inline", {}).get("latency_ms")
        if sl is not None:
            summary_latencies.append(sl)
        if il is not None:
            inline_latencies.append(il)

    total_latencies = [
        s + i for s, i in zip(summary_latencies, inline_latencies, strict=False)
    ]

    # --- Token usage ---
    total_prompt = 0
    total_completion = 0
    for r in results:
        for phase in ["summary", "inline"]:
            usage = r.get(phase, {}).get("usage") or {}
            total_prompt += usage.get("prompt_tokens") or 0
            total_completion += usage.get("completion_tokens") or 0

    total_tokens = total_prompt + total_completion
    n = len(results)

    # --- Cost estimate ---
    input_cost = (total_prompt / 1000) * cost_per_1k_input
    output_cost = (total_completion / 1000) * cost_per_1k_output
    total_cost = input_cost + output_cost

    # --- Per-category breakdown ---
    category_stats: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"total": 0, "detected": 0, "recall": 0.0}
    )
    for r in vulnerable:
        cat = r.get("vulnerability_type", "unknown")
        category_stats[cat]["total"] += 1
        summary_issues = r.get("summary", {}).get("found_issues", [])
        inline_findings = r.get("inline", {}).get("findings", [])
        if len(summary_issues) > 0 or len(inline_findings) > 0:
            category_stats[cat]["detected"] += 1

    for cat in category_stats:
        t = category_stats[cat]["total"]
        d = category_stats[cat]["detected"]
        category_stats[cat]["recall"] = d / t if t > 0 else 0.0

    return {
        "run_id": run_data["run_id"],
        "model": run_data["model"],
        "mode": run_data["mode"],
        "dataset_size": {"vulnerable": total_vulnerable, "safe": total_safe},
        "classification": {
            "true_positives": true_positives,
            "false_negatives": false_negatives,
            "false_positives": false_positives,
            "true_negatives": true_negatives,
        },
        "detection_rate_recall": round(recall, 4),
        "false_positive_rate": round(fpr, 4),
        "precision": round(precision, 4),
        "f1_score": round(f1, 4),
        "avg_line_accuracy": round(avg_line_accuracy, 4),
        "confidence_calibration": confidence_bins,
        "latency": {
            "avg_summary_ms": (
                round(sum(summary_latencies) / len(summary_latencies), 2)
                if summary_latencies
                else 0
            ),
            "avg_inline_ms": (
                round(sum(inline_latencies) / len(inline_latencies), 2)
                if inline_latencies
                else 0
            ),
            "avg_total_ms": (
                round(sum(total_latencies) / len(total_latencies), 2)
                if total_latencies
                else 0
            ),
            "min_total_ms": round(min(total_latencies), 2) if total_latencies else 0,
            "max_total_ms": round(max(total_latencies), 2) if total_latencies else 0,
        },
        "tokens": {
            "total_prompt_tokens": total_prompt,
            "total_completion_tokens": total_completion,
            "total_tokens": total_tokens,
            "avg_tokens_per_snippet": round(total_tokens / n, 1) if n else 0,
        },
        "cost_estimate": {
            "input_cost_usd": round(input_cost, 4),
            "output_cost_usd": round(output_cost, 4),
            "total_cost_usd": round(total_cost, 4),
            "cost_per_review_usd": round(total_cost / n, 6) if n else 0,
        },
        "category_breakdown": dict(category_stats),
    }


def generate_markdown_report(metrics: dict[str, Any]) -> str:
    """Generate a human-readable markdown report from metrics."""
    lines = [
        f"# Evaluation Report — `{metrics['run_id']}`",
        "",
        f"**Model:** `{metrics['model']}`  ",
        f"**Mode:** `{metrics['mode']}`  ",
        f"**Dataset:** {metrics['dataset_size']['vulnerable']} vulnerable + {metrics['dataset_size']['safe']} safe snippets",
        "",
        "## Overall Metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Detection Rate (Recall) | {metrics['detection_rate_recall']:.1%} |",
        f"| Precision | {metrics['precision']:.1%} |",
        f"| F1 Score | {metrics['f1_score']:.1%} |",
        f"| False Positive Rate | {metrics['false_positive_rate']:.1%} |",
        f"| Avg Line Accuracy | {metrics['avg_line_accuracy']:.1%} |",
        "",
        "## Classification Matrix",
        "",
        "| | Predicted Positive | Predicted Negative |",
        "|---|---|---|",
        f"| **Actually Vulnerable** | TP: {metrics['classification']['true_positives']} | FN: {metrics['classification']['false_negatives']} |",
        f"| **Actually Safe** | FP: {metrics['classification']['false_positives']} | TN: {metrics['classification']['true_negatives']} |",
        "",
        "## Detection by Category",
        "",
        "| Category | Total | Detected | Recall |",
        "|----------|-------|----------|--------|",
    ]

    for cat, stats in sorted(metrics["category_breakdown"].items()):
        lines.append(
            f"| {cat} | {stats['total']} | {stats['detected']} | {stats['recall']:.0%} |"
        )

    lines.extend(
        [
            "",
            "## Confidence Calibration",
            "",
            "| Bin | Range | Total Findings | Correct | Accuracy |",
            "|-----|-------|----------------|---------|----------|",
        ]
    )

    for label, data in metrics["confidence_calibration"].items():
        lines.append(
            f"| {label} | {data['range']} | {data['total']} | {data['correct']} | {data['accuracy']:.0%} |"
        )

    lines.extend(
        [
            "",
            "## Performance",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| Avg Summary Latency | {metrics['latency']['avg_summary_ms']:.0f} ms |",
            f"| Avg Inline Latency | {metrics['latency']['avg_inline_ms']:.0f} ms |",
            f"| Avg Total Latency | {metrics['latency']['avg_total_ms']:.0f} ms |",
            f"| Total Tokens | {metrics['tokens']['total_tokens']:,} |",
            f"| Avg Tokens/Snippet | {metrics['tokens']['avg_tokens_per_snippet']:,.0f} |",
            f"| Est. Total Cost | ${metrics['cost_estimate']['total_cost_usd']:.4f} |",
            f"| Est. Cost/Review | ${metrics['cost_estimate']['cost_per_review_usd']:.6f} |",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute evaluation metrics")
    parser.add_argument("run_file", help="Path to run results JSON file")
    parser.add_argument("--cost-per-1k-input", type=float, default=0.0004)
    parser.add_argument("--cost-per-1k-output", type=float, default=0.0016)
    args = parser.parse_args()

    run_data = load_run(args.run_file)
    metrics = compute_metrics(run_data, args.cost_per_1k_input, args.cost_per_1k_output)

    # Save metrics JSON
    run_path = Path(args.run_file)
    metrics_path = run_path.parent / f"{run_path.stem}_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # Save markdown report
    report = generate_markdown_report(metrics)
    report_path = run_path.parent / f"{run_path.stem}_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nMetrics saved to: {metrics_path}")
    print(f"Report saved to: {report_path}")
    print(f"\n{report}")


if __name__ == "__main__":
    main()
