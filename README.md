# Credit Review MCP

Demo-grade Model Context Protocol server for credit analyst GenAI proof of concept.

See **[credit-review-mcp/README.md](credit-review-mcp/README.md)** for setup, MCP tools, Streamlit UI, and limitations.

```bash
cd credit-review-mcp
pip install -e ".[dev]"
pytest
python3 -m credit_review_mcp.server
streamlit run ui/streamlit_app.py
```
