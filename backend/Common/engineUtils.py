# common/engine_utils.py
# Shared across all engines: file extraction, PDF generation

import io
from datetime import datetime
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from werkzeug.datastructures import FileStorage

def extract_text_from_pdf(file):
    try:
        pdf_reader = PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += (page.extract_text() or "") + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Error reading PDF: {str(e)}")

def extract_text_from_csv(file):
    try:
        content = file.read().decode('utf-8', errors='replace')
        return content.strip()
    except Exception as e:
        raise ValueError(f"Error reading CSV: {str(e)}")

def extract_text_from_txt(file):
    try:
        content = file.read().decode('utf-8', errors='replace')
        return content.strip()
    except Exception as e:
        raise ValueError(f"Error reading TXT: {str(e)}")

def extract_text_from_file(file):
    filename = file.filename.lower()
    if filename.endswith('.pdf'):
        return extract_text_from_pdf(file)
    elif filename.endswith('.csv'):
        return extract_text_from_csv(file)
    elif filename.endswith('.txt'):
        return extract_text_from_txt(file)
    else:
        raise ValueError(f"Unsupported file type: {os.path.splitext(filename)[1]}")

def generate_combined_pdf_report(results, title_suffix="Analysis"):
    """
    Generate combined PDF report (shared)
    """
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"Combined Depression Analysis Report ({title_suffix})", styles['Heading1']))
    elements.append(Spacer(1, 0.3 * inch))

    for result in results:
        elements.append(Paragraph(f"File: {result['filename']}", styles['Heading2']))

        analysis = result["analysis"]

        label = analysis.get('label', 'UNKNOWN')
        conf = analysis.get('confidence', 0.0) * 100

        elements.append(Paragraph(f"Label: <b>{label}</b>", styles['Normal']))
        elements.append(Paragraph(f"Confidence: {conf:.1f}%", styles['Normal']))

        if signals := analysis.get("signals"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Detected Signals:", styles['Heading3']))
            for signal, value in signals.items():
                elements.append(Paragraph(f"- {signal}: {value:.2f}", styles['Normal']))

        if explanations := analysis.get("explanations"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Explanations:", styles['Heading3']))
            for signal, expl in explanations.items():
                if expl:
                    elements.append(Paragraph(f"<b>{signal.capitalize()}:</b> {expl}", styles['Normal']))
                    elements.append(Spacer(1, 0.05 * inch))

        elements.append(Spacer(1, 0.2 * inch))
        preview = result["text"][:500] + "..." if len(result["text"]) > 500 else result["text"]
        elements.append(Paragraph("Text Preview:", styles['Heading3']))
        elements.append(Paragraph(preview, styles['Normal']))
        elements.append(Spacer(1, 0.4 * inch))

    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer