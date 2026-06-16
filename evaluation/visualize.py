import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import typing
from matplotlib.projections.polar import PolarAxes

RESULTS_DIR = Path(__file__).parent / "results"


def load_metrics():
    metrics_files = list(RESULTS_DIR.glob("*_metrics.json"))
    data = []
    for f in metrics_files:
        with open(f, encoding="utf-8") as file:
            data.append(json.load(file))
    return data


def plot_radar_chart(metrics_data):
    """Generate a radar chart comparing key metrics across models."""
    labels = [
        "Detection Rate (Recall)",
        "Precision",
        "F1 Score",
        "Avg Line Accuracy",
        "Confidence Calibration (High/Very High)",
    ]
    num_vars = len(labels)

    # Compute angle of each axis
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # Complete the loop

    fig, ax_base = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax = typing.cast(PolarAxes, ax_base)

    # Set background and styling
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, size=10)
    ax.set_rlabel_position(0)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(
        ["20%", "40%", "60%", "80%", "100%"],
        color="grey",
        size=8,
    )
    ax.set_ylim(0, 1)

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    for i, m in enumerate(metrics_data):
        model_name = m["model"]

        # Calculate Confidence Calibration correctly (average of 'high' and 'very_high' accuracy if they exist)
        conf_bins = m.get("confidence_calibration", {})
        conf_acc_sum = 0
        conf_acc_count = 0
        for bin_name in ["high", "very_high"]:
            if bin_name in conf_bins:
                conf_acc_sum += conf_bins[bin_name].get("accuracy", 0)
                conf_acc_count += 1
        conf_acc = conf_acc_sum / conf_acc_count if conf_acc_count > 0 else 0

        values = [
            m.get("detection_rate_recall", 0),
            m.get("precision", 0),
            m.get("f1_score", 0),
            m.get("avg_line_accuracy", 0),
            conf_acc,
        ]
        values += values[:1]  # Complete the loop

        ax.plot(
            angles,
            values,
            color=colors[i % len(colors)],
            linewidth=2,
            linestyle="solid",
            label=model_name,
        )
        ax.fill(angles, values, color=colors[i % len(colors)], alpha=0.1)

    plt.title("Model Performance Comparison (Radar)", size=15, y=1.1)
    plt.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))

    output_path = RESULTS_DIR / "radar_chart.png"
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    print(f"Saved radar chart to {output_path}")


def plot_cost_quality_tradeoff(metrics_data):
    """Generate a scatter plot showing cost vs quality trade-off."""
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.set_style("whitegrid")

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    for i, m in enumerate(metrics_data):
        model_name = m["model"]
        cost_per_review = m.get("cost_estimate", {}).get("cost_per_review_usd", 0)
        f1_score = m.get("f1_score", 0)

        # We'll use latency as bubble size (smaller = better, but let's just show it)
        latency_ms = m.get("latency", {}).get("avg_total_ms", 0)
        bubble_size = latency_ms / 5  # Scaling factor

        ax.scatter(
            cost_per_review,
            f1_score,
            s=bubble_size,
            color=colors[i % len(colors)],
            alpha=0.6,
            label=f"{model_name}\n({latency_ms}ms avg latency)",
            edgecolors="w",
            linewidth=2,
        )

        # Add labels to points
        ax.annotate(
            model_name,
            (cost_per_review, f1_score),
            xytext=(10, -5),
            textcoords="offset points",
            ha="left",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    plt.title("Cost-Quality Trade-off", size=15, pad=15)
    plt.xlabel("Cost per Review ($ USD)", size=12)
    plt.ylabel("Quality (F1 Score)", size=12)

    # Expand axes slightly
    plt.xlim(
        0,
        max(
            m.get("cost_estimate", {}).get("cost_per_review_usd", 0)
            for m in metrics_data
        )
        * 1.5,
    )
    plt.ylim(min(m.get("f1_score", 0) for m in metrics_data) * 0.9, 1.05)

    plt.legend(title="Models", loc="lower right", frameon=True)

    output_path = RESULTS_DIR / "cost_quality_tradeoff.png"
    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    print(f"Saved cost-quality trade-off chart to {output_path}")


def main():
    metrics_data = load_metrics()
    if not metrics_data:
        print("No metrics files found in evaluation/results/")
        return

    plot_radar_chart(metrics_data)
    plot_cost_quality_tradeoff(metrics_data)


if __name__ == "__main__":
    main()
