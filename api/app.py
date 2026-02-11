from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io
import json
import logging
from uuid import uuid4
import threading
from datetime import datetime
from backend.unified_engine import run_llm_job
from backend.Common.prompts import get_prompt, get_available_prompts

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

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
    AVAILABLE_LLMS = ["gemini", "llama", "chatgpt", "kimi", "qwen", "compound"]
    
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
        # Call the unified engine with the selected LLM type
        pdf_bytes = run_llm_job(llm, file_payloads, prompt_type)
        
        logger.info(f"[{job_id}] LLM handler completed. PDF size: {len(pdf_bytes)} bytes")
        
        # Store result
        jobs[job_id]["pdf"] = pdf_bytes
        jobs[job_id]["status"] = "complete"
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["progress"] = 100
        
        logger.info(f"[{job_id}] ✓ Job completed successfully")
        logger.info(f"{'='*80}\n")
        
    except Exception as e:
        logger.error(f"[{job_id}] ❌ Job failed with error:")
        logger.error(f"{type(e).__name__}: {str(e)}", exc_info=True)
        
        # Handle errors
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
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
        # Return PDF for download
        return send_file(
            io.BytesIO(job["pdf"]),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{job_id[:16]}_report.pdf"
        )
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
    return jsonify({
        "message": "Depression Detector API", 
        "status": "running",
        "endpoints": {
            "upload": "/api/upload",
            "job_status": "/api/job/<job_id>"
        },
        "supported_inputs": ["files", "text"],
        "supported_llms": list(LLM_HANDLERS.keys()),
        "supported_prompts": get_available_prompts()
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)