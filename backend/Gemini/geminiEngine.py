# Gemini/engine.py
import io
from werkzeug.datastructures import FileStorage

from .interface import analyze_text
from ..Common.engineUtils import extract_text_from_file, generate_combined_pdf_report  # Import shared

def run_gemini_job(file_payloads):
    combined_results = []
    for payload in file_payloads:
        file = FileStorage(stream=io.BytesIO(payload["bytes"]), filename=payload["filename"])
        extracted_text = extract_text_from_file(file)
        gemini_output = analyze_text(extracted_text)  # Use interface
        combined_results.append({
            "filename": payload["filename"],
            "text": extracted_text,
            "analysis": gemini_output
        })
    pdf = generate_combined_pdf_report(combined_results, title_suffix="Gemini")
    return pdf.getvalue()