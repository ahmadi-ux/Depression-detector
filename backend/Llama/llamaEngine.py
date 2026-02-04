# Llama/engine.py
# ────────────────────────────────────────────────
# Uses Groq API to run Llama models (no local inference anymore)
# ────────────────────────────────────────────────

from datetime import datetime
import os
import io
import json
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from werkzeug.datastructures import FileStorage

from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

if not client.api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set")

# You can choose different models here if you want variety
# Popular fast & capable options on Groq in early 2026:
GROQ_MODEL = "llama-3.1-8b-instant"   # high quality
# GROQ_MODEL = "llama-3.1-8b-instant"    # faster & cheaper
# GROQ_MODEL = "mixtral-8x7b-32768"      # alternative strong model

def run_llama_job(file_payloads):
    """
    Entry point called by the main backend router.
    Processes files → analyzes with Groq (Llama) → generates combined PDF.
    Returns PDF bytes.
    """
    combined_results = []

    for payload in file_payloads:
        file = FileStorage(
            stream=io.BytesIO(payload["bytes"]),
            filename=payload["filename"]
        )

        extracted_text = extract_text_from_file(file)
        analysis = process_with_groq_llama(extracted_text)

        combined_results.append({
            "filename": payload["filename"],
            "text": extracted_text,
            "analysis": analysis
        })

    pdf = generate_combined_pdf_report(combined_results)
    return pdf.getvalue()


# ============================================================================
# FILE EXTRACTION (unchanged)
# ============================================================================

def extract_text_from_pdf(file):
    try:
        pdf_reader = PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += (page.extract_text() or "") + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")


def extract_text_from_csv(file):
    try:
        content = file.read().decode('utf-8', errors='replace')
        return content.strip()
    except Exception as e:
        raise Exception(f"Error reading CSV: {str(e)}")


def extract_text_from_txt(file):
    try:
        content = file.read().decode('utf-8', errors='replace')
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
# GROQ + LLAMA ANALYSIS
# ============================================================================

def process_with_groq_llama(text_content):
    """
    Analyze text using Groq-hosted Llama model.
    Returns the same dict structure your PDF generator expects.
    """
    if not text_content or not text_content.strip():
        return {
            "label": "UNKNOWN",
            "confidence": 0.0,
            "signals": {},
            "all_signals": {},
            "explanations": {},
            "key_findings": ["No meaningful text content to analyze"],
            "recommendations": ["Please upload a document with readable text"]
        }

    # Prompt tuned to produce consistent structured output
    system_prompt = """You are a mental health signal detection assistant.
Analyze the provided text for signs of depression.
Respond **only** with valid JSON containing exactly these fields:

{
  "label": "DEPRESSED" | "NOT_DEPRESSED" | "UNKNOWN",
  "confidence": number between 0.0 and 1.0,
  "signals": object with signal names as keys and 0.0-1.0 scores as values,
  "explanations": object with signal names as keys and short explanations as values,
  "key_findings": array of short bullet-point strings
}

Be concise, objective, and evidence-based."""

    user_prompt = f"""Text to analyze (may be truncated):

{text_content[:12000]}   # Groq context limit is generous, but we truncate for safety

Return JSON only — no other text."""

    try:
        print(f"[Groq Llama] Processing text (length: {len(text_content)} chars)...")

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt}
            ],
            max_tokens=900,
            temperature=0.15,
            top_p=0.9,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content.strip()
        print("Groq response preview:", content[:200] + "..." if len(content) > 200 else content)

        result = json.loads(content)

        # Normalize / fill defaults to match your previous format
        return {
            "label": result.get("label", "UNKNOWN"),
            "confidence": float(result.get("confidence", 0.0)),
            "signals": result.get("signals", {}),
            "all_signals": result.get("signals", {}),  # for backward compatibility
            "explanations": result.get("explanations", {}),
            "key_findings": result.get("key_findings", [
                f"Classification: {result.get('label', 'UNKNOWN')}",
                f"Confidence: {result.get('confidence', 0.0) * 100:.1f}%"
            ]),
            "recommendations": [
                "This is not a clinical diagnosis.",
                "Please consult a qualified mental health professional.",
                "Consider speaking with a counselor or trusted support person."
            ]
        }

    except json.JSONDecodeError:
        print("Warning: Groq response was not valid JSON")
        return {
            "label": "ERROR",
            "confidence": 0.0,
            "signals": {},
            "explanations": {},
            "key_findings": ["Analysis failed — invalid response format"],
            "recommendations": ["Try again or contact support"]
        }
    except Exception as e:
        print(f"Groq error: {str(e)}")
        return {
            "label": "ERROR",
            "confidence": 0.0,
            "signals": {},
            "explanations": {},
            "key_findings": [f"Analysis failed: {str(e)}"],
            "recommendations": ["Check API status or try again later"]
        }


# ============================================================================
# PDF GENERATION (same as before – only title changed for clarity)
# ============================================================================

def generate_combined_pdf_report(results):
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Combined Depression Analysis Report (Llama via Groq)", styles['Heading1']))
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