from functools import lru_cache
from html import escape
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


@lru_cache
def _font_names() -> tuple[str, str]:
    candidates = (
        (Path("C:/Windows/Fonts/arial.ttf"), Path("C:/Windows/Fonts/arialbd.ttf")),
        (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")),
    )
    for regular_path, bold_path in candidates:
        if not regular_path.exists() or not bold_path.exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont("VoxVisionSans", str(regular_path)))
            pdfmetrics.registerFont(TTFont("VoxVisionSansBold", str(bold_path)))
            return "VoxVisionSans", "VoxVisionSansBold"
        except Exception:
            continue
    return "Helvetica", "Helvetica-Bold"


def _safe_text(value: object) -> str:
    return escape(str(value or "Not specified")).replace("\n", "<br/>")


def build_pdf(meeting: dict, report: dict, important_points: list[dict], screen_items: list[dict]) -> BytesIO:
    regular_font, bold_font = _font_names()
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="VoxVision AI Meeting Report",
        author="VoxVision AI",
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "VoxVisionTitle",
        parent=styles["Title"],
        fontName=bold_font,
        fontSize=22,
        leading=27,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#243B67"),
        spaceAfter=3 * mm,
    )
    section_style = ParagraphStyle(
        "VoxVisionSection",
        parent=styles["Heading2"],
        fontName=bold_font,
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#243B67"),
        spaceBefore=3 * mm,
        spaceAfter=1.5 * mm,
    )
    body_style = ParagraphStyle(
        "VoxVisionBody",
        parent=styles["BodyText"],
        fontName=regular_font,
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#263247"),
        spaceAfter=1 * mm,
    )
    bullet_style = ParagraphStyle(
        "VoxVisionBullet",
        parent=body_style,
        leftIndent=5 * mm,
        firstLineIndent=-3 * mm,
        bulletIndent=0,
    )
    meta_style = ParagraphStyle(
        "VoxVisionMeta",
        parent=body_style,
        fontSize=8.5,
        leading=13,
        textColor=colors.HexColor("#53627A"),
    )

    story = [
        Paragraph("VoxVision AI Meeting Report", title_style),
        Paragraph(
            f"<b>Meeting:</b> {_safe_text(meeting.get('title', 'Untitled session'))}<br/>"
            f"<b>Website:</b> {_safe_text(meeting.get('platform', 'Web'))}<br/>"
            f"<b>Output mode:</b> {_safe_text(meeting.get('mode') or meeting.get('selected_mode', 'combined'))}<br/>"
            f"<b>Started:</b> {_safe_text(meeting.get('started_at'))}<br/>"
            f"<b>Ended:</b> {_safe_text(meeting.get('ended_at'))}",
            meta_style,
        ),
        Spacer(1, 2 * mm),
        HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#C9D3E6")),
    ]

    _add_section(story, "Summary", [report.get("summary")], section_style, body_style, bullet_style, bullets=False)
    for title, key in (
        ("Detailed notes", "notes"),
        ("Insights", "insights"),
        ("Decisions", "decisions"),
        ("Deadlines", "deadlines"),
        ("Graph insights", "graph_insights"),
        ("Recommendations", "recommendations"),
        ("Uncertain information", "uncertain_information"),
    ):
        _add_section(story, title, report.get(key), section_style, body_style, bullet_style)

    story.append(Paragraph("Tasks", section_style))
    story.append(_task_table(report.get("tasks") or [], body_style, bold_font))
    _add_section(
        story,
        "Important points",
        [f"{item.get('label', 'Important')}: {item.get('user_note') or item.get('transcript_context') or item.get('screen_context') or 'Not specified'}" for item in important_points],
        section_style,
        body_style,
        bullet_style,
    )
    _add_section(
        story,
        "Screen observations",
        [item.get("extracted_text") for item in screen_items if item.get("extracted_text")],
        section_style,
        body_style,
        bullet_style,
    )

    def decorate_page(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D7DEEB"))
        canvas.line(document.leftMargin, 12 * mm, A4[0] - document.rightMargin, 12 * mm)
        canvas.setFillColor(colors.HexColor("#6B778C"))
        canvas.setFont(regular_font, 8)
        canvas.drawString(document.leftMargin, 8 * mm, "VoxVision AI")
        canvas.drawRightString(A4[0] - document.rightMargin, 8 * mm, f"Page {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=decorate_page, onLaterPages=decorate_page)
    output.seek(0)
    return output


def _add_section(story, title, values, section_style, body_style, bullet_style, bullets=True) -> None:
    story.append(Paragraph(title, section_style))
    normalized = values if isinstance(values, list) else [values]
    normalized = [value for value in normalized if value not in (None, "")]
    if not normalized:
        normalized = ["None recorded."]
    for value in normalized:
        if bullets:
            story.append(Paragraph(_safe_text(value), bullet_style, bulletText="-"))
        else:
            story.append(Paragraph(_safe_text(value), body_style))


def _task_table(tasks: list[dict], body_style, bold_font) -> Table:
    headings = ("Task", "Assigned to", "Deadline", "Priority")
    data = [[Paragraph(heading, ParagraphStyle(f"TaskHeading{index}", parent=body_style, fontName=bold_font, textColor=colors.white)) for index, heading in enumerate(headings)]]
    if tasks:
        for task in tasks:
            data.append([
                Paragraph(_safe_text(task.get("task")), body_style),
                Paragraph(_safe_text(task.get("assigned_to")), body_style),
                Paragraph(_safe_text(task.get("deadline")), body_style),
                Paragraph(_safe_text(task.get("priority")), body_style),
            ])
    else:
        data.append([Paragraph("None recorded.", body_style), "", "", ""])
    table = Table(data, colWidths=(82 * mm, 34 * mm, 29 * mm, 25 * mm), repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#405A8B")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9D3E6")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F7F9FC")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("SPAN", (0, 1), (-1, 1)) if not tasks else ("VALIGN", (0, 1), (-1, -1), "TOP"),
    ]))
    return table
