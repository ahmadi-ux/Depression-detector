from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime
import os
import io
import threading
from uuid import uuid4
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from werkzeug.datastructures import FileStorage
from .interface import analyze_text
from uuid import UUID
from werkzeug.datastructures import FileStorage

def run_gemini_job(file_payloads):
    """
    Entry point called by the main backend router
    """
    combined_results = []

    for payload in file_payloads:
        file = FileStorage(
            stream=io.BytesIO(payload["bytes"]),
            filename=payload["filename"]
        )

        extracted_text = extract_text_from_file(file)
        gemini_output = process_with_gemini(extracted_text)

        combined_results.append({
            "filename": payload["filename"],
            "text": extracted_text,
            "analysis": gemini_output
        })

    pdf = generate_combined_pdf_report(combined_results)
    return pdf.getvalue()

# Job storage (in production, use Redis or database)
jobs = {}

# ============================================================================
# FILE EXTRACTION UTILITIES
# ============================================================================

def extract_text_from_pdf(file):
    """Extract text from PDF file"""
    try:
        pdf_reader = PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")

def extract_text_from_csv(file):
    """Extract text from CSV file"""
    try:
        content = file.read().decode('utf-8')
        return content.strip()
    except Exception as e:
        raise Exception(f"Error reading CSV: {str(e)}")

def extract_text_from_txt(file):
    """Extract text from TXT file"""
    try:
        content = file.read().decode('utf-8')
        return content.strip()
    except Exception as e:
        raise Exception(f"Error reading TXT: {str(e)}")

def extract_text_from_file(file):
    """Extract text from uploaded file based on file type"""
    filename = file.filename.lower()
    
    if filename.endswith('.pdf'):
        return extract_text_from_pdf(file)
    elif filename.endswith('.csv'):
        return extract_text_from_csv(file)
    elif filename.endswith('.txt'):
        return extract_text_from_txt(file)
    else:
        raise Exception(f"Unsupported file type: {os.path.splitext(filename)[1]}")

def process_with_gemini(text_content):
    """
    Process text content with Gemini using interface.py
    Extracts depression signals and classifies the text
    """
    try:
        print(f"Processing text with Gemini (length: {len(text_content)} chars)...")
        
        # Call interface.py's analyze_text function
        result = analyze_text(text_content)
        
        print(f"Analysis result: {result}")
        
        return {
            "label": result.get("label", "UNKNOWN"),
            "confidence": result.get("confidence", 0),
            "signals": result.get("signals", {}),
            "all_signals": result.get("all_signals", {}),
            "explanations": result.get("explanations", {}),
            "key_findings": [
                f"Classification: {result.get('label', 'UNKNOWN')}",
                f"Confidence: {result.get('confidence', 0) * 100:.1f}%",
                f"Detected signals: {', '.join(result.get('signals', {}).keys()) if result.get('signals') else 'None'}"
            ],
            "recommendations": [
                "Please consult with a mental health professional for proper diagnosis",
                "Consider speaking with a counselor or therapist",
                "Reach out to trusted friends or family for support"
            ]
        }
    except Exception as e:
        print(f"Error in Gemini processing: {str(e)}")
        raise

def generate_pdf_report(filename, extracted_text, gemini_output):
    """Generate a PDF report from Gemini output"""
    # Create PDF in memory
    pdf_buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
    )
    
    # Container for PDF elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Add title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#1f2937',
        spaceAfter=30,
    )
    elements.append(Paragraph(f"Depression Detector Analysis Report", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Add file info
    elements.append(Paragraph(f"<b>File Analyzed:</b> {filename}", styles['Normal']))
    elements.append(Paragraph(f"<b>Analysis Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Add classification result
    elements.append(Paragraph("<b>Classification Result</b>", styles['Heading2']))
    label = gemini_output.get('label', 'UNKNOWN')
    confidence = gemini_output.get('confidence', 0)
    
    result_color = '#dc2626' if label == 'DEPRESSED' else '#16a34a'
    result_style = ParagraphStyle(
        'Result',
        parent=styles['Normal'],
        fontSize=14,
        textColor=result_color,
        spaceAfter=12,
    )
    elements.append(Paragraph(f"<b>Label: {label}</b>", result_style))
    elements.append(Paragraph(f"<b>Confidence: {confidence * 100:.1f}%</b>", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Add detected signals
    signals = gemini_output.get('signals', {})
    if signals:
        elements.append(Paragraph("<b>Detected Depression Signals</b>", styles['Heading2']))
        for signal, value in signals.items():
            elements.append(Paragraph(f"• {signal.capitalize()}: {value:.2f}", styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
    
    # Add signal explanations
    explanations = gemini_output.get('explanations', {})
    if explanations:
        elements.append(Paragraph("<b>Signal Explanations</b>", styles['Heading2']))
        for signal, explanation in explanations.items():
            if explanation:  # Only show non-empty explanations
                elements.append(Paragraph(f"<b>{signal.capitalize()}:</b> {explanation}", styles['Normal']))
                elements.append(Spacer(1, 0.1*inch))
        elements.append(Spacer(1, 0.1*inch))
    
    # Add key findings
    elements.append(Paragraph("<b>Key Findings</b>", styles['Heading2']))
    for finding in gemini_output.get('key_findings', []):
        elements.append(Paragraph(f"• {finding}", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Add recommendations
    elements.append(Paragraph("<b>Recommendations</b>", styles['Heading2']))
    for rec in gemini_output.get('recommendations', []):
        elements.append(Paragraph(f"• {rec}", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Add disclaimer
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=10,
        textColor='#666666',
        spaceAfter=12,
    )
    elements.append(Paragraph(
        "<i>Disclaimer: This analysis is for research purposes only." 
        " It should not be used as a substitute for professional mental health diagnosis or treatment." 
        " Please consult with a qualified mental health professional for proper assessment and care.</i>",
        disclaimer_style
    ))
    
    # Add extracted text section (truncated)
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph("<b>Original Text (first 500 characters)</b>", styles['Heading2']))
    text_preview = extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
    elements.append(Paragraph(text_preview, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    pdf_buffer.seek(0)
    
    return pdf_buffer

def generate_combined_pdf_report(results):
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Combined Depression Analysis Report", styles['Heading1']))
    elements.append(Spacer(1, 0.3 * inch))

    for result in results:
        elements.append(Paragraph(
            f"File: {result['filename']}",
            styles['Heading2']
        ))

        analysis = result["analysis"]

        elements.append(Paragraph(
            f"Label: <b>{analysis['label']}</b>",
            styles['Normal']
        ))
        elements.append(Paragraph(
            f"Confidence: {analysis['confidence'] * 100:.1f}%",
            styles['Normal']
        ))

        if analysis.get("signals"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Detected Signals:", styles['Heading3']))
            for signal, value in analysis["signals"].items():
                elements.append(Paragraph(
                    f"- {signal}: {value:.2f}",
                    styles['Normal']
                ))
        
        # Add explanations
        if analysis.get("explanations"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Signal Explanations:", styles['Heading3']))
            for signal, explanation in analysis["explanations"].items():
                if explanation:  # Only show non-empty explanations
                    elements.append(Paragraph(
                        f"<b>{signal.capitalize()}:</b> {explanation}",
                        styles['Normal']
                    ))
                    elements.append(Spacer(1, 0.05 * inch))

        elements.append(Spacer(1, 0.2 * inch))

        preview = result["text"][:500]
        elements.append(Paragraph("Text Preview:", styles['Heading3']))
        elements.append(Paragraph(preview + "...", styles['Normal']))

        elements.append(Spacer(1, 0.4 * inch))

    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer

def process_file_async(job_id, file_bytes, filename):
    """
    Background worker: Extract → Analyze → Generate PDF
    """
    try:
        print(f"\n[{job_id}] Starting async processing...")

        # 🔥 Rebuild FileStorage from raw bytes (thread-safe)
        file = FileStorage(
            stream=io.BytesIO(file_bytes),
            filename=filename
        )

        # Step 1: Extract text
        print(f"[{job_id}] Step 1: Extracting text...")
        jobs[job_id]['progress'] = 10

        extracted_text = extract_text_from_file(file)

        if not extracted_text or not extracted_text.strip():
            raise Exception("No text could be extracted from file")

        print(f"[{job_id}] ✓ Extracted {len(extracted_text)} characters")
        jobs[job_id]['progress'] = 30

        # Step 2: Process with Gemini
        print(f"[{job_id}] Step 2: Processing with Gemini...")
        jobs[job_id]['progress'] = 40

        gemini_output = process_with_gemini(extracted_text)
        print(f"[{job_id}] ✓ Gemini analysis complete")
        print(f"[{job_id}]   - Label: {gemini_output.get('label')}")
        print(f"[{job_id}]   - Confidence: {gemini_output.get('confidence')}")
        jobs[job_id]['progress'] = 70

        # Step 3: Generate PDF
        print(f"[{job_id}] Step 3: Generating PDF...")
        pdf_report = generate_pdf_report(filename, extracted_text, gemini_output)
        pdf_data = pdf_report.getvalue()

        print(f"[{job_id}] ✓ PDF generated ({len(pdf_data)} bytes)")
        jobs[job_id]['progress'] = 90

        # Step 4: Mark complete
        jobs[job_id] = {
            'status': 'complete',
            'progress': 100,
            'filename': filename,
            'pdf': pdf_data,
            'created_at': jobs[job_id]['created_at'],
            'completed_at': datetime.now().isoformat()
        }

        print(f"[{job_id}] ✓ Job complete!")

    except Exception as e:
        print(f"[{job_id}] ✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

        jobs[job_id] = {
            'status': 'error',
            'error': str(e),
            'filename': filename,
            'created_at': jobs[job_id].get('created_at'),
            'failed_at': datetime.now().isoformat()
        }

def process_multiple_files_async(job_id, file_payloads):
    try:
        combined_results = []
        combined_text = ""

        total_files = len(file_payloads)

        for idx, payload in enumerate(file_payloads):
            file = FileStorage(
                stream=io.BytesIO(payload["bytes"]),
                filename=payload["filename"]
            )

            jobs[job_id]['progress'] = int((idx / total_files) * 40)

            extracted_text = extract_text_from_file(file)
            combined_text += f"\n\n--- {payload['filename']} ---\n\n"
            combined_text += extracted_text

            gemini_output = process_with_gemini(extracted_text)

            combined_results.append({
                "filename": payload["filename"],
                "text": extracted_text,
                "analysis": gemini_output
            })

        jobs[job_id]['progress'] = 70

        pdf = generate_combined_pdf_report(combined_results)
        pdf_data = pdf.getvalue()

        jobs[job_id] = {
            'status': 'complete',
            'progress': 100,
            'filenames': [f["filename"] for f in file_payloads],
            'pdf': pdf_data,
            'completed_at': datetime.now().isoformat()
        }

    except Exception as e:
        jobs[job_id] = {
            'status': 'error',
            'error': str(e)
        }