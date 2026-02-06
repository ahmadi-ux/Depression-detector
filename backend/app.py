from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import io
from uuid import uuid4
import threading
from datetime import datetime
from Gemini.geminiEngine import run_gemini_job
from Llama.llamaEngine import run_llama_job 
from ChatGPT.chatGPTEngine import run_chatgpt_job

app = Flask(__name__)
CORS(app)

jobs = {}  # In-memory job store (use Redis/DB in prod)

LLM_HANDLERS = {
    "gemini": run_gemini_job,
    "llama": run_llama_job,
    "chatgpt": run_chatgpt_job
}

@app.route("/api/upload", methods=["POST"])
def upload():
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

    thread = threading.Thread(target=process_job, args=(job_id, llm, file_payloads))
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id, "status": "processing"}), 202

def process_job(job_id, llm, file_payloads):
    try:
        pdf_bytes = LLM_HANDLERS[llm](file_payloads)
        jobs[job_id]["pdf"] = pdf_bytes
        jobs[job_id]["status"] = "complete"
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["progress"] = 100
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["failed_at"] = datetime.now().isoformat()

@app.route("/api/job/<job_id>", methods=["GET"])
def get_job(job_id):
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404

    job = jobs[job_id]
    if job["status"] == "complete":
        return send_file(
            io.BytesIO(job["pdf"]),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{job_id[:8]}_report.pdf"
        )
    elif job["status"] == "error":
        return jsonify({"status": "error", "error": job["error"]}), 400
    else:
        return jsonify({
            "job_id": job_id,
            "status": job["status"],
            "progress": job.get("progress", 0),
            "filenames": job.get("filenames"),
            "created_at": job.get("created_at")
        })

#if __name__ == "__main__":
#    app.run(debug=True, port=5000)