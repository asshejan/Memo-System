import io
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from app.core.deps import get_current_user
from app.db import get_db
from app.models.user import User
from app.models.organization import Organization
from app.services.authorization import assert_can_view_memo
from app.routers.memos import _load_memo

router = APIRouter(prefix="/api/memos", tags=["pdf"])


@router.get("/{memo_id}/pdf")
def export_memo_pdf(memo_id: uuid.UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memo = _load_memo(db, memo_id)
    if memo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memo not found")
    assert_can_view_memo(current_user, memo)

    org = db.get(Organization, memo.organization_id)
    author = db.get(User, memo.author_id)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.6 * inch, bottomMargin=0.6 * inch)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(org.name if org else "Organization", styles["Title"]),
        Paragraph(f"Memo {memo.memo_number}", styles["Heading2"]),
        Spacer(1, 0.15 * inch),
    ]

    meta_rows = [
        ["Subject", memo.subject],
        ["Author", author.name if author else str(memo.author_id)],
        ["Date", memo.created_at.strftime("%Y-%m-%d %H:%M UTC")],
        ["Priority", memo.priority.value.capitalize()],
        ["Status", memo.status.value.replace("_", " ").title()],
    ]
    table = Table(meta_rows, colWidths=[1.5 * inch, 4.5 * inch])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Memo Body", styles["Heading3"]))
    for para in (memo.body or "").split("\n"):
        story.append(Paragraph(para or "&nbsp;", styles["BodyText"]))
    story.append(Spacer(1, 0.2 * inch))

    if memo.workflow_instance:
        story.append(Paragraph("Approval History", styles["Heading3"]))
        rows = [["Position", "Status", "Acted At", "Comment"]]
        for step in memo.workflow_instance.steps:
            rows.append([
                step.label or f"Step {step.position_index + 1}",
                step.status.value.replace("_", " ").title(),
                step.acted_at.strftime("%Y-%m-%d %H:%M UTC") if step.acted_at else "-",
                step.comment or "-",
            ])
        wf_table = Table(rows, colWidths=[1.3 * inch, 1.3 * inch, 1.6 * inch, 1.8 * inch])
        wf_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
        ]))
        story.append(wf_table)
        story.append(Spacer(1, 0.2 * inch))

    if memo.comments:
        story.append(Paragraph("Comments", styles["Heading3"]))
        for c in memo.comments:
            story.append(Paragraph(f"[{c.comment_type.value}] {c.created_at.strftime('%Y-%m-%d %H:%M UTC')}: {c.text}", styles["BodyText"]))
        story.append(Spacer(1, 0.2 * inch))

    final_status = "IN PROGRESS"
    if memo.status.value == "approved":
        final_status = "APPROVED"
    elif memo.status.value == "rejected":
        final_status = "REJECTED"
    story.append(Paragraph(f"Final Status: {final_status}", styles["Heading2"]))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{memo.memo_number}.pdf"'},
    )
