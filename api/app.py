from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
import io
import json
import logging
import os
import sys
from uuid import uuid4
import threading
from datetime import datetime

# Add parent directory to path so we can import backend module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from backend/Common/.env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', 'Common', '.env'))

from backend.unified_engine import run_llm_job
from backend.Common.prompts import get_prompt, get_available_prompts

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Expose Content-Disposition and classification headers for downloads
CORS(app, expose_headers=["Content-Disposition", "X-Depression-Classification"])

jobs = {}  # In-memory job store (use Redis/DB in prod)

@app.route("/api/upload", methods=["POST"])
def upload():
    """
    Handles both file uploads and direct text input.
    
    Accepts:
    - files: List of files (multipart/form-data)
    - text: Direct text input (form field)
    - llm: LLM engine to use
    - prompt: Prompt template type to use (simple, structured, feature_extraction, chain_of_thought, few_shot, free_form)
    """
    logger.info(f"\n{'='*80}")
    logger.info("UPLOAD ENDPOINT CALLED")
    logger.info(f"{'='*80}")
    
    llm_raw = request.form.get("llm")
    llm = llm_raw.lower() if llm_raw else None
    
    prompt_type = request.form.get("prompt", "simple").lower()
    
    logger.info(f"LLM: {llm}, Prompt Type: {prompt_type}")
    
    # Define available LLMs
    AVAILABLE_LLMS = ["gemini", "llama", "chatgpt", "kimi", "qwen", "compound", "llamabig", "grok"]
    
    # Validate LLM
    if llm not in AVAILABLE_LLMS:
        logger.error(f"Invalid LLM: {llm}")
        return jsonify({"error": f"Invalid LLM: {llm}. Available: {AVAILABLE_LLMS}"}), 400
    
    # Validate prompt type
    available_prompts = get_available_prompts()
    if prompt_type not in available_prompts:
        logger.error(f"Invalid prompt type: {prompt_type}")
        return jsonify({"error": f"Invalid prompt type: {prompt_type}. Available: {available_prompts}"}), 400
    
    # Check for direct text input
    text_input = request.form.get("text")
    files = request.files.getlist("files")
    
    logger.info(f"Files count: {len(files)}, Has text input: {bool(text_input)}")
    
    # Determine input type and prepare payloads
    if text_input:
        # Direct text input - create a virtual "file" payload
        file_payloads = [{
            "filename": "text_input.txt",
            "bytes": text_input.encode('utf-8'),
            "is_text": True  # Flag to indicate this is direct text
        }]
        input_type = "text"
        logger.info(f"Using direct text input ({len(text_input)} chars)")
        
    elif files and len(files) > 0:
        # File uploads
        file_payloads = [{"filename": f.filename, "bytes": f.read()} for f in files]
        input_type = "files"
        logger.info(f"Using file uploads: {[p['filename'] for p in file_payloads]}")
        
    else:
        # No input provided
        logger.error("No files or text provided")
        return jsonify({"error": "No files or text provided"}), 400

    # Create job
    job_id = str(uuid4())
    jobs[job_id] = {
        "status": "processing",
        "progress": 0,
        "input_type": input_type,
        "filenames": [p["filename"] for p in file_payloads],
        "llm": llm,
        "prompt_type": prompt_type,
        "created_at": datetime.now().isoformat()
    }
    
    logger.info(f"Job created: {job_id}")

    # Start processing in background thread
    thread = threading.Thread(target=process_job, args=(job_id, llm, prompt_type, file_payloads))
    thread.daemon = True
    thread.start()
    
    logger.info(f"Background thread started for job {job_id}\n")

    return jsonify({"job_id": job_id, "status": "processing"}), 202


def process_job(job_id, llm, prompt_type, file_payloads):
    """
    Process the job in background thread.
    Handles both file uploads and text input.
    """
    try:
        logger.info(f"\n{'='*80}")
        logger.info(f"PROCESSING JOB: {job_id}")
        logger.info(f"LLM: {llm}, Prompt Type: {prompt_type}")
        logger.info(f"Files: {len(file_payloads)}")
        logger.info(f"{'='*80}\n")
        
        # Update progress
        jobs[job_id]["progress"] = 10
        
        logger.info(f"[{job_id}] Calling unified LLM engine: {llm}")
        # Call the unified engine - now returns (pdf_bytes, classification)
        pdf_bytes, classification = run_llm_job(llm, file_payloads, prompt_type)
        logger.info(f"[{job_id}] LLM handler completed. PDF size: {len(pdf_bytes)} bytes")
        logger.info(f"[{job_id}] Classification: {classification}")
        
        # Store result
        jobs[job_id]["pdf"] = pdf_bytes
        jobs[job_id]["classification"] = classification
        jobs[job_id]["status"] = "complete"
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["progress"] = 100
        logger.info(f"[{job_id}] ✓ Job completed successfully")
        logger.info(f"{'='*80}\n")
        
    except Exception as e:
        logger.error(f"[{job_id}] ❌ Job failed with error:")
        logger.error(f"{type(e).__name__}: {str(e)}", exc_info=True)
        
        # Compose better error message with context
        error_msg = str(e)
        if "empty response" in error_msg.lower():
            error_msg = f"{error_msg} - Try retrying or using a different LLM model. This often indicates API quota limits or content safety filters."
        elif "not valid json" in error_msg.lower():
            error_msg = f"{error_msg} - The {llm} model returned a malformed response. Try retrying with a different prompt type like 'structured' or 'simple'."
        
        # Handle errors
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = error_msg
        jobs[job_id]["failed_at"] = datetime.now().isoformat()
        
        logger.error(f"{'='*80}\n")


@app.route("/api/job/<job_id>", methods=["GET"])
def get_job(job_id):
    """
    Get job status or download PDF if complete.
    """
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404

    job = jobs[job_id]
    
    if job["status"] == "complete":
        # Compose download filename: <original_filename>_<llm>_<jobid8>.pdf
        filenames = job.get("filenames", [])
        base_name = filenames[0].rsplit('.', 1)[0] if filenames else "report"
        llm = job.get("llm", "LLM")
        jobid8 = job_id[:8]
        download_name = f"{base_name}_{llm}_{jobid8}.pdf"
        
        # Create response with PDF
        response = send_file(
            io.BytesIO(job["pdf"]),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=download_name
        )
        # Add classification to response headers
        classification = job.get("classification", "unknown")
        response.headers["X-Depression-Classification"] = classification
        return response
    elif job["status"] == "error":
        # Return error details
        return jsonify({"status": "error", "error": job["error"]}), 400
    else:
        # Return processing status
        return jsonify({
            "job_id": job_id,
            "status": job["status"],
            "progress": job.get("progress", 0),
            "input_type": job.get("input_type"),
            "filenames": job.get("filenames"),
            "created_at": job.get("created_at")
        })


@app.route("/", methods=["GET"])
def home():
    """API info endpoint"""
    AVAILABLE_LLMS = ["gemini", "llama", "chatgpt", "kimi", "qwen", "compound", "llamabig", "grok"]
    return jsonify({
        "message": "Depression Detector API", 
        "status": "running",
        "endpoints": {
            "upload": "/api/upload",
            "job_status": "/api/job/<job_id>",
            "test_gemini": "/api/test/gemini",
            "test_grok": "/api/test/grok"
        },
        "supported_inputs": ["files", "text"],
        "supported_llms": AVAILABLE_LLMS,
        "supported_prompts": get_available_prompts()
    })


@app.route("/api/test/gemini", methods=["GET"])
def test_gemini_connection():
    """
    Test Gemini API connection and return diagnostic information.
    Useful for debugging API quota, key, or network issues.
    """
    logger.info("Testing Gemini API connection...")
    try:
        from backend.Interfaces.Gemini import test_gemini_connection
        result = test_gemini_connection()
        return jsonify(result)
    except ImportError:
        return jsonify({
            "error": "Could not import Gemini interface",
            "status": "❌ Import failed"
        }), 500
    except Exception as e:
        logger.error(f"Test endpoint error: {e}")
        return jsonify({
            "error": str(e),
            "status": "❌ Test failed"
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)