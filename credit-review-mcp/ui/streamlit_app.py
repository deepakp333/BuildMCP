"""Streamlit demo UI for credit review workflow."""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to path for demo runs without install
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import streamlit as st

from credit_review_mcp.config import MEMOS_DIR, SAMPLE_DATA_DIR
from credit_review_mcp.memo import memo_to_markdown
from credit_review_mcp.workflow import run_demo_credit_review

st.set_page_config(page_title="Credit Review MCP Demo", layout="wide")
st.title("Credit Review MCP — Analyst Demo")
st.caption(
    "Draft generated for analyst review. Not a rating action, investment recommendation, or credit approval."
)

default_csv = str(SAMPLE_DATA_DIR / "companies.csv")
csv_path = st.text_input("Company CSV path", value=default_csv)
max_companies = st.slider("Max companies", min_value=1, max_value=5, value=3)
website_url = st.text_input("Optional HTML table URL", value="")

if st.button("Run Demo Credit Review", type="primary"):
    with st.spinner("Running credit review pipeline..."):
        result = run_demo_credit_review(
            csv_path=csv_path or None,
            website_url=website_url or None,
            max_companies=max_companies,
        )
    st.success(result.summary)

    for review in result.results:
        company = review.company
        st.header(f"{company.company_name} ({company.ticker})")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Credit Ratios")
            if review.ratios:
                for r in review.ratios.ratios:
                    val = f"{r.value:.2f}" if r.value is not None else "N/A"
                    st.write(f"**{r.name}**: {val}")
            else:
                st.write("No ratios computed.")

        with col2:
            st.subheader("CAMEL Scores (1=strong, 5=weak)")
            if review.camel:
                for c in review.camel.components:
                    st.write(f"**{c.component}**: {c.score}/5 — {c.rationale[:120]}...")
                st.write(f"Overall: {review.camel.overall_score}")

        st.subheader("Top News")
        if review.news:
            for article in review.news.articles[:5]:
                mock = " [MOCK]" if article.is_mock else ""
                st.write(
                    f"- **{article.source}**{mock} ({article.published_at.date()}): "
                    f"{article.title} — sentiment {article.sentiment_score:+.2f}"
                )

        st.subheader("Memo Preview")
        if review.memo:
            st.markdown(memo_to_markdown(review.memo)[:4000])

        if review.pdf_path:
            pdf_file = Path(review.pdf_path)
            if pdf_file.exists():
                st.download_button(
                    label=f"Download PDF — {company.ticker}",
                    data=pdf_file.read_bytes(),
                    file_name=pdf_file.name,
                    mime="application/pdf",
                    key=f"pdf_{company.ticker}",
                )

        if review.errors:
            st.warning("Errors: " + "; ".join(review.errors))

st.sidebar.markdown("### Output folders")
st.sidebar.code(str(MEMOS_DIR))
st.sidebar.markdown("Run MCP server: `python -m credit_review_mcp.server`")
