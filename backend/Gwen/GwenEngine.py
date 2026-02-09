from .interface import analyze_text
from ..Common.engineUtils import extract_text_from_file, generate_combined_pdf_report  # Import shared
from groq import Groq
from dotenv import load_dotenv
import os
from werkzeug.datastructures import FileStorage
import io

# Load environment variables
load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

if not client.api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set")

# You can choose different models here
GROQ_MODEL = "qwen/qwen3-32b"   

def run_qwen_job(file_payloads):
    combined_results = []
    for payload in file_payloads:
        file = FileStorage(stream=io.BytesIO(payload["bytes"]), filename=payload["filename"])
        extracted_text = extract_text_from_file(file)
        qwen_output = analyze_text(extracted_text)  # Use interface
        combined_results.append({
            "filename": payload["filename"],
            "text": extracted_text,
            "analysis": qwen_output
        })
    pdf = generate_combined_pdf_report(combined_results, title_suffix="Qwen")
    return pdf.getvalue()