#!/usr/bin/env python3
"""Build the Triple T engineering journal PDF from its Markdown source."""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "ENGINEERING_JOURNAL.md"
OUTPUT = ROOT / "docs" / "Triple_T_Engineering_Journal.pdf"

ACCENT = colors.HexColor("#1F4E79")
TEXT = colors.HexColor("#202124")
MUTED = colors.HexColor("#5F6368")
LIGHT = colors.HexColor("#D9E6F2")


def inline_markup(text: str) -> str:
    """Escape text and support the small Markdown subset used by the journal."""
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    return escaped


def scaled_image(path: Path, max_width: float, max_height: float) -> Image:
    image = Image(str(path))
    scale = min(max_width / image.imageWidth, max_height / image.imageHeight, 1.0)
    image.drawWidth = image.imageWidth * scale
    image.drawHeight = image.imageHeight * scale
    image.hAlign = "CENTER"
    return image


def page_footer(canvas, document) -> None:
    canvas.saveState()
    width, _ = A4
    canvas.setStrokeColor(LIGHT)
    canvas.line(18 * mm, 14 * mm, width - 18 * mm, 14 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, 9 * mm, "Team Triple T · WRO Future Engineers 2026")
    canvas.drawRightString(width - 18 * mm, 9 * mm, f"Page {document.page}")
    canvas.restoreState()


def build_styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=29,
            textColor=ACCENT,
            alignment=TA_CENTER,
            spaceAfter=10 * mm,
        ),
        "h2": ParagraphStyle(
            "Heading2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=19,
            textColor=ACCENT,
            spaceBefore=7 * mm,
            spaceAfter=3 * mm,
            keepWithNext=True,
        ),
        "h3": ParagraphStyle(
            "Heading3",
            parent=base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=15,
            textColor=TEXT,
            spaceBefore=4 * mm,
            spaceAfter=2 * mm,
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=TEXT,
            alignment=TA_LEFT,
            spaceAfter=2.5 * mm,
        ),
        "meta": ParagraphStyle(
            "Metadata",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=16,
            textColor=TEXT,
            alignment=TA_CENTER,
            spaceAfter=1.5 * mm,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            leftIndent=7 * mm,
            firstLineIndent=0,
            bulletIndent=2 * mm,
            textColor=TEXT,
            spaceAfter=1.2 * mm,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontName="Courier",
            fontSize=8,
            leading=10,
            leftIndent=5 * mm,
            rightIndent=5 * mm,
            backColor=colors.HexColor("#F4F6F8"),
            borderPadding=4 * mm,
            spaceBefore=2 * mm,
            spaceAfter=3 * mm,
        ),
        "caption": ParagraphStyle(
            "Caption",
            parent=base["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=10,
            textColor=MUTED,
            alignment=TA_CENTER,
            spaceBefore=1 * mm,
            spaceAfter=4 * mm,
        ),
    }


def markdown_to_story(source: Path):
    styles = build_styles()
    story = []
    paragraph_lines: list[str] = []
    code_lines: list[str] = []
    in_code = False
    title_seen = False
    metadata_mode = False

    def flush_paragraph() -> None:
        nonlocal paragraph_lines
        if paragraph_lines:
            text = " ".join(line.strip() for line in paragraph_lines)
            style = styles["meta"] if metadata_mode else styles["body"]
            story.append(Paragraph(inline_markup(text), style))
            paragraph_lines = []

    for raw_line in source.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()

        if line.startswith("```"):
            flush_paragraph()
            if in_code:
                story.append(Preformatted("\n".join(code_lines), styles["code"]))
                code_lines = []
            in_code = not in_code
            continue

        if in_code:
            code_lines.append(line)
            continue

        image_match = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", line.strip())
        if image_match:
            flush_paragraph()
            alt_text, relative_path = image_match.groups()
            image_path = (source.parent / relative_path).resolve()
            if image_path.exists():
                story.append(scaled_image(image_path, 168 * mm, 105 * mm))
                story.append(Paragraph(html.escape(alt_text), styles["caption"]))
            continue

        if line.startswith("# "):
            flush_paragraph()
            if title_seen:
                story.append(PageBreak())
            story.append(Spacer(1, 15 * mm))
            story.append(Paragraph(inline_markup(line[2:]), styles["title"]))
            story.append(HRFlowable(width="65%", thickness=1.5, color=ACCENT))
            story.append(Spacer(1, 6 * mm))
            title_seen = True
            metadata_mode = True
            continue

        if line.startswith("## "):
            flush_paragraph()
            metadata_mode = False
            story.append(Paragraph(inline_markup(line[3:]), styles["h2"]))
            continue

        if line.startswith("### "):
            flush_paragraph()
            metadata_mode = False
            story.append(Paragraph(inline_markup(line[4:]), styles["h3"]))
            continue

        if re.match(r"^\d+\.\s+", line):
            flush_paragraph()
            item = re.sub(r"^\d+\.\s+", "", line)
            number = line.split(".", 1)[0] + "."
            story.append(Paragraph(inline_markup(item), styles["bullet"], bulletText=number))
            continue

        if line.startswith("- "):
            flush_paragraph()
            story.append(
                Paragraph(inline_markup(line[2:]), styles["bullet"], bulletText="•")
            )
            continue

        if not line.strip():
            flush_paragraph()
            continue

        paragraph_lines.append(line)

    flush_paragraph()
    return story


def main() -> int:
    if not SOURCE.exists():
        print(f"Missing source: {SOURCE}", file=sys.stderr)
        return 1

    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=19 * mm,
        title="Triple T Engineering Journal — WRO Future Engineers 2026",
        author="Team Triple T",
        subject="Engineering journal and project report",
    )
    document.build(
        markdown_to_story(SOURCE),
        onFirstPage=page_footer,
        onLaterPages=page_footer,
    )
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
