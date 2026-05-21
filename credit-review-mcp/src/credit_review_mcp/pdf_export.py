"""PDF export for credit memos using ReportLab."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from credit_review_mcp.config import DISCLAIMER, MEMOS_DIR
from credit_review_mcp.schemas import CreditMemo
from credit_review_mcp.memo import memo_to_markdown


def export_credit_memo_pdf(memo: CreditMemo, output_dir: Path | None = None) -> str:
    out_dir = output_dir or MEMOS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_ticker = "".join(c if c.isalnum() else "_" for c in memo.ticker)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"credit_memo_{safe_ticker}_{ts}.pdf"

    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "MemoTitle",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "MemoHeading",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "MemoBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
    )

    story = []
    story.append(Paragraph(f"Draft Credit Memo — {memo.company_name}", title_style))
    story.append(
        Paragraph(
            f"Ticker: {memo.ticker} | As-of: {memo.as_of_date} | "
            f"Generated: {memo.generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
            body_style,
        )
    )
    story.append(Paragraph(DISCLAIMER, disclaimer_style))
    story.append(Spacer(1, 0.2 * inch))

    for section in memo.sections:
        story.append(Paragraph(section.title, heading_style))
        for para in section.content.split("\n"):
            if para.strip():
                safe = para.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(safe, body_style))
        story.append(Spacer(1, 0.1 * inch))

    story.append(Paragraph("Sources", heading_style))
    for src in memo.sources:
        story.append(Paragraph(f"• {src}", body_style))

    if memo.llm_used:
        story.append(
            Paragraph(
                "Note: LLM narrative section included — verify all facts independently.",
                disclaimer_style,
            )
        )

    doc.build(story)
    return str(path)


def export_memo_markdown_file(memo: CreditMemo, output_dir: Path | None = None) -> str:
    out_dir = output_dir or MEMOS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_ticker = "".join(c if c.isalnum() else "_" for c in memo.ticker)
    path = out_dir / f"credit_memo_{safe_ticker}.md"
    path.write_text(memo_to_markdown(memo), encoding="utf-8")
    return str(path)
