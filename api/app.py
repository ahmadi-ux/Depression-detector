from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io
from uuid import uuid4
import threading
from datetime import datetime
from backend.Gemini.geminiEngine import run_gemini_job
from backend.Llama.llamaEngine import run_llama_job 
from backend.ChatGPT.chatGPTEngine import run_chatgpt_job
<<<<<<< HEAD
=======
from backend.Kimik2.KimiEngine import run_kimi_job as run_kimi_job
from backend.Gwen.GwenEngine import run_qwen_job as run_gwen_job
from backend.Compound.CompundEngine import run_compound_job as run_compound_job
>>>>>>> 5d254b0ec8528848b502320433929fdc69a64831

app = Flask(__name__)
CORS(app)

jobs = {}  # In-memory job store (use Redis/DB in prod)

LLM_HANDLERS = {
    "gemini": run_gemini_job,
    "llama": run_llama_job,
<<<<<<< HEAD
    "chatgpt": run_chatgpt_job
=======
    "chatgpt": run_chatgpt_job,
    "kimi": run_kimi_job,
    "qwen": run_gwen_job,
    "compound": run_compound_job
>>>>>>> 5d254b0ec8528848b502320433929fdc69a64831
}

@app.route("/api/upload", methods=["POST"])
def upload():
<<<<<<< HEAD
    llm_raw = request.form.get("llm")
    llm = llm_raw.lower() if llm_raw else None
    files = request.files.getlist("files")

    if not files or len(files) == 0:
        return jsonify({"error": "No files provided"}), 400

    if llm not in LLM_HANDLERS:
        return jsonify({"error": f"Invalid LLM: {llm}"}), 400

    job_id = str(uuid4())
    file_payloads = [{"filename": f.filename, "bytes": f.read()} for f in files]

    jobs[job_id] = {
        "status": "processing",
        "progress": 0,
        "filenames": [f.filename for f in files],
        "created_at": datetime.now().isoformat()
    }

=======
    """
    Handles both file uploads and direct text input.
    
    Accepts:
    - files: List of files (multipart/form-data)
    - text: Direct text input (form field)
    - llm: LLM engine to use
    """
    llm_raw = request.form.get("llm")
    llm = llm_raw.lower() if llm_raw else None
    
    # Validate LLM
    if llm not in LLM_HANDLERS:
        return jsonify({"error": f"Invalid LLM: {llm}"}), 400
    
    # Check for direct text input
    text_input = request.form.get("text")
    files = request.files.getlist("files")
    
    # Determine input type and prepare payloads
    if text_input:
        # Direct text input - create a virtual "file" payload
        file_payloads = [{
            "filename": "text_input.txt",
            "bytes": text_input.encode('utf-8'),
            "is_text": True  # Flag to indicate this is direct text
        }]
        input_type = "text"
        
    elif files and len(files) > 0:
        # File uploads
        file_payloads = [{"filename": f.filename, "bytes": f.read()} for f in files]
        input_type = "files"
        
    else:
        # No input provided
        return jsonify({"error": "No files or text provided"}), 400

    # Create job
    job_id = str(uuid4())
    jobs[job_id] = {
        "status": "processing",
        "progress": 0,
        "input_type": input_type,
        "filenames": [p["filename"] for p in file_payloads],
        "created_at": datetime.now().isoformat()
    }

    # Start processing in background thread
>>>>>>> 5d254b0ec8528848b502320433929fdc69a64831
    thread = threading.Thread(target=process_job, args=(job_id, llm, file_payloads))
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id, "status": "processing"}), 202

<<<<<<< HEAD
def process_job(job_id, llm, file_payloads):
    try:
        pdf_bytes = LLM_HANDLERS[llm](file_payloads)
=======

def process_job(job_id, llm, file_payloads):
    """
    Process the job in background thread.
    Handles both file uploads and text input.
    """
    try:
        # Update progress
        jobs[job_id]["progress"] = 10
        
        # Call the appropriate LLM handler
        pdf_bytes = LLM_HANDLERS[llm](file_payloads)
        
        # Store result
>>>>>>> 5d254b0ec8528848b502320433929fdc69a64831
        jobs[job_id]["pdf"] = pdf_bytes
        jobs[job_id]["status"] = "complete"
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["progress"] = 100
<<<<<<< HEAD
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["failed_at"] = datetime.now().isoformat()

@app.route("/api/job/<job_id>", methods=["GET"])
def get_job(job_id):
=======
        
    except Exception as e:
        # Handle errors
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["failed_at"] = datetime.now().isoformat()
        print(f"Job {job_id} failed: {str(e)}")


@app.route("/api/job/<job_id>", methods=["GET"])
def get_job(job_id):
    """
    Get job status or download PDF if complete.
    """
>>>>>>> 5d254b0ec8528848b502320433929fdc69a64831
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404

    job = jobs[job_id]
<<<<<<< HEAD
    if job["status"] == "complete":
=======
    
    if job["status"] == "complete":
        # Return PDF for download
>>>>>>> 5d254b0ec8528848b502320433929fdc69a64831
        return send_file(
            io.BytesIO(job["pdf"]),
            mimetype="application/pdf",
            as_attachment=True,
<<<<<<< HEAD
            download_name=f"{job_id[:8]}_report.pdf"
        )
    elif job["status"] == "error":
        return jsonify({"status": "error", "error": job["error"]}), 400
    else:
=======
            download_name=f"{job_id[:16]}_report.pdf"
        )
    elif job["status"] == "error":
        # Return error details
        return jsonify({"status": "error", "error": job["error"]}), 400
    else:
        # Return processing status
>>>>>>> 5d254b0ec8528848b502320433929fdc69a64831
        return jsonify({
            "job_id": job_id,
            "status": job["status"],
            "progress": job.get("progress", 0),
<<<<<<< HEAD
=======
            "input_type": job.get("input_type"),
>>>>>>> 5d254b0ec8528848b502320433929fdc69a64831
            "filenames": job.get("filenames"),
            "created_at": job.get("created_at")
        })

<<<<<<< HEAD
@app.route("/", methods=["GET"])
def home():
=======

@app.route("/", methods=["GET"])
def home():
    """API info endpoint"""
>>>>>>> 5d254b0ec8528848b502320433929fdc69a64831
    return jsonify({
        "message": "Depression Detector API", 
        "status": "running",
        "endpoints": {
            "upload": "/api/upload",
            "job_status": "/api/job/<job_id>"
<<<<<<< HEAD
        }
    })

=======
        },
        "supported_inputs": ["files", "text"],
        "supported_llms": list(LLM_HANDLERS.keys())
    })


>>>>>>> 5d254b0ec8528848b502320433929fdc69a64831
if __name__ == "__main__":
    app.run(debug=True, port=5000)