from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from pathlib import Path

def generate_pdf(run_id, result):
    out_dir = Path(f"reports/{run_id}")
    out_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = out_dir / "report.pdf"
    doc = SimpleDocTemplate(str(pdf_path))
    styles = getSampleStyleSheet()

    content = [
        Paragraph("<b>Depression Detection Report</b>", styles["Title"]),
        Paragraph(f"Label: {result['label']}", styles["Normal"]),
        Paragraph(f"Confidence: {result['confidence']}", styles["Normal"]),
        Paragraph(f"Signals: {result['signals']}", styles["Normal"]),
    ]

    doc.build(content)
    return pdf_path
