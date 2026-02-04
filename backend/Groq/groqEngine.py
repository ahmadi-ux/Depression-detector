# engine.py (for Groq + Llama via Groq API)
from datetime import datetime
import os
import io
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from werkzeug.datastructures import FileStorage
from dotenv import load_dotenv

load_dotenv()

from groq import Groq

# ────────────────────────────────────────────────
# Initialize Groq client (expects GROQ_API_KEY in environment)
# ────────────────────────────────────────────────
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

if not client.api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set")

# You can change the model here
GROQ_MODEL = "openai/gpt-oss-120b"   # or "llama3-70b-8192", "mixtral-8x7b-32768", etc.

def run_groq_job(file_payloads):
    """
    Entry point called by the main backend router.
    Processes files → analyzes with Groq → generates combined PDF.
    Returns PDF bytes.
    """
    combined_results = []

    for payload in file_payloads:
        file = FileStorage(
            stream=io.BytesIO(payload["bytes"]),
            filename=payload["filename"]
        )

        extracted_text = extract_text_from_file(file)
        groq_output = process_with_groq(extracted_text)

        combined_results.append({
            "filename": payload["filename"],
            "text": extracted_text,
            "analysis": groq_output
        })

    pdf = generate_combined_pdf_report(combined_results)
    return pdf.getvalue()


# ============================================================================
# FILE EXTRACTION UTILITIES (same as before)
# ============================================================================

def extract_text_from_pdf(file):
    try:
        pdf_reader = PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")


def extract_text_from_csv(file):
    try:
        content = file.read().decode('utf-8')
        return content.strip()
    except Exception as e:
        raise Exception(f"Error reading CSV: {str(e)}")


def extract_text_from_txt(file):
    try:
        content = file.read().decode('utf-8')
        return content.strip()
    except Exception as e:
        raise Exception(f"Error reading TXT: {str(e)}")


def extract_text_from_file(file):
    filename = file.filename.lower()
    
    if filename.endswith('.pdf'):
        return extract_text_from_pdf(file)
    elif filename.endswith('.csv'):
        return extract_text_from_csv(file)
    elif filename.endswith('.txt'):
        return extract_text_from_txt(file)
    else:
        raise Exception(f"Unsupported file type: {os.path.splitext(filename)[1]}")


# ============================================================================
# GROQ ANALYSIS
# ============================================================================

def process_with_groq(text_content):
    """
    Analyze text using Groq API (Llama model).
    Returns the same structured output format as previous engines.
    """
    if not text_content.strip():
        return {
            "label": "UNKNOWN",
            "confidence": 0.0,
            "signals": {},
            "all_signals": {},
            "explanations": {},
            "key_findings": ["No text content to analyze"],
            "recommendations": ["Please provide valid text content"]
        }

    # Build a prompt that asks for structured depression analysis
    prompt = f"""You are a mental health analysis assistant.
Analyze the following text for signs of depression.
Return a JSON object with exactly these keys:

{{
  "label": "DEPRESSED" or "NOT_DEPRESSED" or "UNKNOWN",
  "confidence": float between 0 and 1,
  "signals": {{ "hopelessness": float, "low_energy": float, ... }}  // any relevant signals with scores 0-1
  "explanations": {{ "hopelessness": "brief explanation", ... }},
  "key_findings": ["short bullet point 1", "short bullet point 2", ...]
}}

Text to analyze:
{text_content[:4000]}  # truncate if too long – adjust limit as needed

Be concise and objective."""

    try:
        print(f"Processing text with Groq ({GROQ_MODEL}) - length: {len(text_content)} chars...")

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise mental health signal detector. Always respond with valid JSON only."
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.2,          # lower for more consistent structured output
            response_format={"type": "json_object"}  # helps enforce JSON
        )

        content = response.choices[0].message.content.strip()
        print("Groq raw response:", content[:200], "...")

        import json
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            print("Warning: Groq did not return valid JSON → fallback parsing")
            result = {}  # fallback

        # Normalize / fill defaults (same structure as your previous engines)
        return {
            "label": result.get("label", "UNKNOWN"),
            "confidence": float(result.get("confidence", 0.0)),
            "signals": result.get("signals", {}),
            "all_signals": result.get("signals", {}),  # keeping for compatibility
            "explanations": result.get("explanations", {}),
            "key_findings": result.get("key_findings", [
                f"Classification: {result.get('label', 'UNKNOWN')}",
                f"Confidence: {result.get('confidence', 0.0) * 100:.1f}%"
            ]),
            "recommendations": [
                "Please consult with a mental health professional for proper diagnosis",
                "Consider speaking with a counselor or therapist",
                "Reach out to trusted friends or family for support"
            ]
        }

    except Exception as e:
        print(f"Error in Groq processing: {str(e)}")
        raise


# ============================================================================
# PDF GENERATION (same as previous engines)
# ============================================================================

def generate_combined_pdf_report(results):
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Combined Depression Analysis Report (Groq)", styles['Heading1']))
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

        if analysis.get("explanations"):
            elements.append(Spacer(1, 0.1 * inch))
            elements.append(Paragraph("Signal Explanations:", styles['Heading3']))
            for signal, explanation in analysis["explanations"].items():
                if explanation:
                    elements.append(Paragraph(
                        f"<b>{signal.capitalize()}:</b> {explanation}",
                        styles['Normal']
                    ))
                    elements.append(Spacer(1, 0.05 * inch))

        elements.append(Spacer(1, 0.2 * inch))

        preview = result["text"][:500] + "..." if len(result["text"]) > 500 else result["text"]
        elements.append(Paragraph("Text Preview:", styles['Heading3']))
        elements.append(Paragraph(preview, styles['Normal']))

        elements.append(Spacer(1, 0.4 * inch))

    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer