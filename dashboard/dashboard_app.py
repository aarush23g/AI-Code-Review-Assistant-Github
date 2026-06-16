"""
AI Code Review Assistant — Metrics Dashboard

A Streamlit dashboard for monitoring review operations, token usage,
review quality, and model performance.

Usage:
    streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

# Fix name collision: Streamlit adds dashboard/ to sys.path, causing import app to conflict with dashboard/app.py
dashboard_path = Path(__file__).parent.resolve()
sys.path = [p for p in sys.path if Path(p).resolve() != dashboard_path]

# Ensure repository root is in sys.path
root_path = Path(__file__).parent.parent.resolve()
if str(root_path) not in [str(Path(p).resolve()) for p in sys.path]:
    sys.path.insert(0, str(root_path))

# Remove the shadowed 'app' module from sys.modules
if "app" in sys.modules:
    del sys.modules["app"]

import json  # noqa: E402
import sqlite3  # noqa: E402

import streamlit as st  # noqa: E402

from app.core.config import get_settings  # noqa: E402

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Code Review Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Theme / CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-card h3 { margin: 0; font-size: 2rem; }
    .metric-card p { margin: 0; opacity: 0.85; font-size: 0.9rem; }
    .metric-green { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
    .metric-blue { background: linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%); }
    .metric-orange { background: linear-gradient(135deg, #f2994a 0%, #f2c94c 100%); }
    .metric-purple { background: linear-gradient(135deg, #834d9b 0%, #d04ed6 100%); }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
settings = get_settings()
DB_PATH = Path(__file__).parent.parent / settings.review_metrics_db_path
EVAL_RESULTS_DIR = Path(__file__).parent.parent / "evaluation" / "results"


@st.cache_data(ttl=30)
def load_review_data() -> list[dict]:
    """Load all review runs from SQLite."""
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM review_runs ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@st.cache_data(ttl=60)
def load_eval_metrics() -> list[dict]:
    """Load evaluation metrics files."""
    if not EVAL_RESULTS_DIR.exists():
        return []
    metrics_files = sorted(EVAL_RESULTS_DIR.glob("*_metrics.json"))
    results = []
    for f in metrics_files:
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)
            data["_file"] = f.name
            results.append(data)
    return results


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("🔍 AI Code Review")
st.sidebar.markdown("**Metrics Dashboard**")
st.sidebar.markdown("---")

reviews = load_review_data()
eval_metrics = load_eval_metrics()

if reviews:
    st.sidebar.metric("Total Reviews", len(reviews))
    completed = sum(1 for r in reviews if r.get("status") == "completed")
    st.sidebar.metric("Completed", completed)
else:
    st.sidebar.info("No review data yet. Run some reviews first!")

st.sidebar.markdown("---")
st.sidebar.caption("Dashboard refreshes every 30s")

# ---------------------------------------------------------------------------
# Main content — tabs
# ---------------------------------------------------------------------------
st.title("📊 AI Code Review Assistant — Dashboard")

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🔄 Review Operations",
        "💰 Token Usage & Cost",
        "✅ Review Quality",
        "🤖 Model Performance",
    ]
)

# =========================================================================
# Tab 1: Review Operations
# =========================================================================
with tab1:
    st.header("Review Operations")

    if not reviews:
        st.info(
            "No review data available. Reviews are recorded when the webhook "
            "processes pull requests. Start the server and trigger a PR review!"
        )
    else:
        # KPI cards
        total = len(reviews)
        completed = sum(1 for r in reviews if r.get("status") == "completed")
        skipped = sum(1 for r in reviews if r.get("status") == "skipped")
        failed = total - completed - skipped
        avg_lat = sum(r.get("duration_ms", 0) or 0 for r in reviews) / max(total, 1)

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(
            f'<div class="metric-card"><h3>{total}</h3><p>Total Reviews</p></div>',
            unsafe_allow_html=True,
        )
        c2.markdown(
            f'<div class="metric-card metric-green"><h3>{completed}</h3><p>Completed</p></div>',
            unsafe_allow_html=True,
        )
        c3.markdown(
            f'<div class="metric-card metric-orange"><h3>{skipped}</h3><p>Skipped</p></div>',
            unsafe_allow_html=True,
        )
        c4.markdown(
            f'<div class="metric-card metric-blue"><h3>{avg_lat:,.0f}ms</h3><p>Avg Latency</p></div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # Reviews by status
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Reviews by Status")
            status_counts = {}
            for r in reviews:
                s = r.get("status", "unknown")
                status_counts[s] = status_counts.get(s, 0) + 1
            st.bar_chart(status_counts)

        with col2:
            st.subheader("Reviews by Mode")
            mode_counts = {}
            for r in reviews:
                m = r.get("mode", "unknown")
                if m:
                    mode_counts[m] = mode_counts.get(m, 0) + 1
            if mode_counts:
                st.bar_chart(mode_counts)
            else:
                st.info("No mode data available")

        # Reviews over time
        st.subheader("Reviews Over Time")
        dates = {}
        for r in reviews:
            d = (r.get("created_at") or "")[:10]
            if d:
                dates[d] = dates.get(d, 0) + 1
        if dates:
            sorted_dates = dict(sorted(dates.items()))
            st.line_chart(sorted_dates)

        # Recent reviews table
        st.subheader("Recent Reviews")
        table_data = []
        for r in reviews[:15]:
            table_data.append(
                {
                    "Repository": r.get("repository", "—"),
                    "PR #": r.get("pull_number", "—"),
                    "Status": r.get("status", "—"),
                    "Mode": r.get("mode", "—"),
                    "Latency (ms)": f"{r.get('duration_ms', 0) or 0:,.0f}",
                    "Tokens": f"{r.get('total_tokens', 0) or 0:,}",
                    "Comments": r.get("inline_comment_count", 0),
                    "Date": (r.get("created_at") or "")[:19],
                }
            )
        st.dataframe(table_data, use_container_width=True)

# =========================================================================
# Tab 2: Token Usage & Cost
# =========================================================================
with tab2:
    st.header("Token Usage & Cost Analysis")

    if not reviews:
        st.info("No review data available yet.")
    else:
        total_prompt = sum(r.get("prompt_tokens", 0) or 0 for r in reviews)
        total_completion = sum(r.get("completion_tokens", 0) or 0 for r in reviews)
        total_tokens = total_prompt + total_completion
        n = len(reviews)

        # Cost estimation (configurable)
        st.sidebar.markdown("### 💰 Cost Settings")
        cost_input = st.sidebar.number_input(
            "Cost per 1K input tokens ($)", value=0.0004, format="%.4f"
        )
        cost_output = st.sidebar.number_input(
            "Cost per 1K output tokens ($)", value=0.0016, format="%.4f"
        )

        est_cost = (total_prompt / 1000 * cost_input) + (
            total_completion / 1000 * cost_output
        )
        cost_per_review = est_cost / max(n, 1)

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(
            f'<div class="metric-card metric-blue"><h3>{total_tokens:,}</h3><p>Total Tokens</p></div>',
            unsafe_allow_html=True,
        )
        c2.markdown(
            f'<div class="metric-card metric-purple"><h3>{total_prompt:,}</h3><p>Prompt Tokens</p></div>',
            unsafe_allow_html=True,
        )
        c3.markdown(
            f'<div class="metric-card metric-green"><h3>{total_completion:,}</h3><p>Completion Tokens</p></div>',
            unsafe_allow_html=True,
        )
        c4.markdown(
            f'<div class="metric-card metric-orange"><h3>${est_cost:.4f}</h3><p>Est. Total Cost</p></div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Token Distribution")
            st.bar_chart({"Prompt": total_prompt, "Completion": total_completion})

        with col2:
            st.subheader("Avg Tokens per Review")
            st.metric("Prompt", f"{total_prompt / max(n, 1):,.0f}")
            st.metric("Completion", f"{total_completion / max(n, 1):,.0f}")
            st.metric("Cost/Review", f"${cost_per_review:.6f}")

        # Token usage by repo
        st.subheader("Token Usage by Repository")
        repo_tokens = {}
        for r in reviews:
            repo = r.get("repository", "unknown")
            repo_tokens[repo] = repo_tokens.get(repo, 0) + (
                r.get("total_tokens", 0) or 0
            )
        if repo_tokens:
            st.bar_chart(repo_tokens)

        # Token trend over time
        st.subheader("Cumulative Token Usage Over Time")
        token_by_date = {}
        for r in sorted(reviews, key=lambda x: x.get("created_at", "")):
            d = (r.get("created_at") or "")[:10]
            if d:
                token_by_date[d] = token_by_date.get(d, 0) + (
                    r.get("total_tokens", 0) or 0
                )
        if token_by_date:
            cumulative = {}
            total = 0
            for date, tokens in sorted(token_by_date.items()):
                total += tokens
                cumulative[date] = total
            st.line_chart(cumulative)

# =========================================================================
# Tab 3: Review Quality
# =========================================================================
with tab3:
    st.header("Review Quality Metrics")

    if not reviews:
        st.info("No review data available yet.")
    else:
        total_issues = sum(r.get("summary_issue_count", 0) or 0 for r in reviews)
        total_findings = sum(r.get("inline_finding_count", 0) or 0 for r in reviews)
        total_comments = sum(r.get("inline_comment_count", 0) or 0 for r in reviews)
        funnel_rate = total_comments / max(total_findings, 1) * 100

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(
            f'<div class="metric-card"><h3>{total_issues}</h3><p>Issues Found</p></div>',
            unsafe_allow_html=True,
        )
        c2.markdown(
            f'<div class="metric-card metric-green"><h3>{total_findings}</h3><p>Inline Findings</p></div>',
            unsafe_allow_html=True,
        )
        c3.markdown(
            f'<div class="metric-card metric-blue"><h3>{total_comments}</h3><p>Comments Posted</p></div>',
            unsafe_allow_html=True,
        )
        c4.markdown(
            f'<div class="metric-card metric-orange"><h3>{funnel_rate:.0f}%</h3><p>Post Rate</p></div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Findings → Comments Funnel")
            st.bar_chart(
                {
                    "Findings Generated": total_findings,
                    "Comments Posted": total_comments,
                }
            )

        with col2:
            st.subheader("Issues by Repository")
            repo_issues = {}
            for r in reviews:
                repo = r.get("repository", "unknown")
                repo_issues[repo] = repo_issues.get(repo, 0) + (
                    r.get("summary_issue_count", 0) or 0
                )
            if repo_issues:
                st.bar_chart(repo_issues)

        # Latency distribution
        st.subheader("Latency Distribution")
        latencies = [
            r.get("duration_ms", 0) or 0 for r in reviews if r.get("duration_ms")
        ]
        if latencies:
            st.bar_chart({"Latency (ms)": latencies})
            st.caption(
                f"Min: {min(latencies):,.0f}ms | "
                f"Avg: {sum(latencies)/len(latencies):,.0f}ms | "
                f"Max: {max(latencies):,.0f}ms"
            )

# =========================================================================
# Tab 4: Model Performance (from evaluation data)
# =========================================================================
with tab4:
    st.header("Model Performance — Evaluation Benchmark")

    if not eval_metrics:
        st.info(
            "No evaluation results found. Run the evaluation benchmark:\n\n"
            "```bash\n"
            "python -m evaluation.evaluate --mode security --rate-limit 2.0\n"
            "python -m evaluation.metrics evaluation/results/run_<timestamp>.json\n"
            "```"
        )
    else:
        # Filter out broken runs (0 recall means likely errored)
        valid = [
            m
            for m in eval_metrics
            if m.get("detection_rate_recall", 0) > 0 or m.get("precision", 0) > 0
        ]
        if not valid:
            valid = eval_metrics  # show anyway

        st.subheader("Model Comparison")

        # Side-by-side comparison
        comparison_data = []
        for m in valid:
            comparison_data.append(
                {
                    "Model": m.get("model", "unknown"),
                    "Mode": m.get("mode", "—"),
                    "Recall": f"{m.get('detection_rate_recall', 0):.1%}",
                    "Precision": f"{m.get('precision', 0):.1%}",
                    "F1 Score": f"{m.get('f1_score', 0):.1%}",
                    "FP Rate": f"{m.get('false_positive_rate', 0):.1%}",
                    "Line Accuracy": f"{m.get('avg_line_accuracy', 0):.1%}",
                    "Avg Latency": f"{m.get('latency', {}).get('avg_total_ms', 0):,.0f}ms",
                    "Cost/Review": f"${m.get('cost_estimate', {}).get('cost_per_review_usd', 0):.6f}",
                }
            )
        st.dataframe(comparison_data, use_container_width=True)

        st.markdown("---")

        # Per-model details
        for m in valid:
            model_name = m.get("model", "unknown")
            with st.expander(f"📋 {model_name} — Detailed Breakdown"):
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Detection by Category")
                    cats = m.get("category_breakdown", {})
                    if cats:
                        cat_data = []
                        for cat, stats in sorted(
                            cats.items(),
                            key=lambda x: x[1].get("recall", 0),
                            reverse=True,
                        ):
                            cat_data.append(
                                {
                                    "Category": cat,
                                    "Total": stats.get("total", 0),
                                    "Detected": stats.get("detected", 0),
                                    "Recall": f"{stats.get('recall', 0):.0%}",
                                }
                            )
                        st.dataframe(cat_data, use_container_width=True)

                with col2:
                    st.subheader("Confidence Calibration")
                    cal = m.get("confidence_calibration", {})
                    if cal:
                        cal_data = []
                        for label, data in cal.items():
                            cal_data.append(
                                {
                                    "Bin": label,
                                    "Range": data.get("range", ""),
                                    "Total": data.get("total", 0),
                                    "Correct": data.get("correct", 0),
                                    "Accuracy": f"{data.get('accuracy', 0):.0%}",
                                }
                            )
                        st.dataframe(cal_data, use_container_width=True)

                # Classification matrix
                clf = m.get("classification", {})
                if clf:
                    st.subheader("Classification Matrix")
                    matrix_data = [
                        {
                            "": "Predicted Positive",
                            "Actually Vulnerable": clf.get("true_positives", 0),
                            "Actually Safe": clf.get("false_positives", 0),
                        },
                        {
                            "": "Predicted Negative",
                            "Actually Vulnerable": clf.get("false_negatives", 0),
                            "Actually Safe": clf.get("true_negatives", 0),
                        },
                    ]
                    st.dataframe(matrix_data, use_container_width=True)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption(
    "AI Code Review Assistant Dashboard • "
    f"Data from `{DB_PATH}` • "
    f"Evaluation results from `{EVAL_RESULTS_DIR}`"
)
