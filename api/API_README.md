# API Documentation

The REST API layer handles HTTP requests from the frontend and coordinates with the backend LLM engine to process depression detection analysis requests.

---

## 📁 API Structure

```
api/
├── app.py              # Main Flask application & all endpoints
├── API_README.md       # This file
└── __init__.py         # Package initialization
```

---

## 🚀 Quick Start

### Start the API Server

```bash
cd Depression-detector
python api/app.py
```

**Server runs on:** `http://localhost:5000`

### Test the API

```bash
curl -X POST http://localhost:5000/api/upload \
  -F "text=I feel completely worthless" \
  -F "llm=gemini" \
  -F "prompt=simple"
```

---

## 📡 Endpoints Reference

### 1. Submit Analysis - `POST /api/upload`

Submit text or files for depression detection analysis.

**Request:**
```http
POST /api/upload HTTP/1.1
Host: localhost:5000
Content-Type: multipart/form-data

Parameters:
- text (string, optional): Direct text input (max 10,000 chars)
- files (file, optional): Upload file (PDF, DOCX, TXT)
- llm (string, required): LLM to use
- prompt (string, optional): Analysis type [default: simple]
```

**Supported LLMs:**
- `gemini` - Google Gemini 1.5
- `chatgpt` - OpenAI GPT-4
- `llama` - Llama 3.1 8B
- `llamabig` - Llama 3.3 70B
- `compound` - Compound model ensemble
- `qwen` - Alibaba Qwen 2
- `kimi` - Moonshot Kimi K2
- `grok` - X.AI Grok

**Supported Prompts:**
- `simple` - Binary classification (default)
- `structured` - Checklist-based analysis
- `feature_extraction` - Linguistic features
- `chain_of_thought` - Step-by-step reasoning
- `few_shot` - Example-based learning
- `free_form` - Narrative analysis
- `sentence` - Line-by-line breakdown
- `ollama_compare` - Multi-model comparison

**Success Response (201 Created):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Analysis job submitted successfully"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "Invalid LLM: invalid_model. Available: [...]"
}
```

### 2. Check Job Status - `GET /api/job/<job_id>`

Get the current status and results of an analysis job.

**Request:**
```http
GET /api/job/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Host: localhost:5000
```

**Response (Processing):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Analysis in progress...",
  "progress": 45
}
```

**Response (Completed):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "classification": "depression_detected",
  "confidence": 0.87,
  "analysis": "The text contains several depression indicators...",
  "linguistic_features": {
    "first_person_pronouns": 8,
    "negative_emotion_words": 5,
    "hopelessness_indicators": 3,
    "social_isolation_markers": 2,
    "future_oriented_statements": 0
  },
  "model": "gemini",
  "prompt_type": "simple",
  "created_at": "2026-04-06T10:30:00Z",
  "completed_at": "2026-04-06T10:35:23Z",
  "processing_time_ms": 5234
}
```

**Response (Failed):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "error": "API key invalid or expired",
  "error_details": "GROQ_API_KEY not set"
}
```

### 3. Download Results - `GET /api/download/<job_id>`

Download the analysis results as a PDF report.

**Request:**
```http
GET /api/download/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Host: localhost:5000
```

**Success Response (200 OK):**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="depression_analysis_550e8400.pdf"
[Binary PDF data]
```

**Error Response (404 Not Found):**
```json
{
  "error": "Job not found"
}
```

### 4. Get Available Models - `GET /api/models`

List all available LLM models and prompt types.

**Request:**
```http
GET /api/models HTTP/1.1
Host: localhost:5000
```

**Response:**
```json
{
  "models": ["gemini", "chatgpt", "llama", "llamabig", "compound", "qwen", "kimi", "grok"],
  "prompts": ["simple", "structured", "feature_extraction", "chain_of_thought", "few_shot", "free_form", "sentence", "ollama_compare"],
  "default_model": "gemini",
  "default_prompt": "simple"
}
```

---

## 📊 Request/Response Examples

### Example 1: Simple Text Analysis

**Request:**
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "text=I feel completely sad and nothing makes me happy anymore" \
  -F "llm=gemini" \
  -F "prompt=simple"
```

**Response:**
```json
{
  "job_id": "abc123def456",
  "status": "processing",
  "message": "Analysis job submitted successfully"
}
```

**Check Status:**
```bash
curl http://localhost:5000/api/job/abc123def456
```

---

### Example 2: File Upload with Detailed Analysis

**Request:**
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "files=@student_essay.pdf" \
  -F "llm=chatgpt" \
  -F "prompt=feature_extraction"
```

**Response:**
```json
{
  "job_id": "xyz789uvw123",
  "status": "processing"
}
```

---

### Example 3: Multi-File Analysis

**Request:**
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "files=@essay1.txt" \
  -F "files=@essay2.txt" \
  -F "files=@essay3.docx" \
  -F "llm=llama" \
  -F "prompt=structured"
```

---

### Example 4: Structured Analysis with Detail

**Request:**
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "text=I can't sleep, everything feels pointless" \
  -F "llm=llamabig" \
  -F "prompt=chain_of_thought"
```

---

## ⚙️ Configuration

### Environment Setup

The API loads environment variables from `backend/Common/.env`:

```env
# Required API Keys
GROQ_API_KEY=gsk_your_key
GOOGLE_API_KEY=your_google_key

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your_secret_key

# CORS Settings
CORS_ORIGINS=http://localhost:5173,https://yourfrontend.com

# Job Storage
JOB_TIMEOUT=3600  # 1 hour
MAX_JOBS_IN_MEMORY=1000
```

### CORS Configuration

The API is configured to accept requests from the frontend:

```python
CORS(app, expose_headers=["Content-Disposition", "X-Depression-Classification"])
```

**Exposed Headers:**
- `Content-Disposition` - For file downloads
- `X-Depression-Classification` - Custom classification header

**Allowed Origins:**
- Development: `http://localhost:5173`
- Production: Configure in `.env` or `app.py`

### Running on Different Ports

```bash
# Default port 5000
python api/app.py

# Custom port
export FLASK_PORT=8000
python api/app.py

# Or directly
python -c "from api.app import app; app.run(port=8000)"
```

---

## 🔄 Job Processing Flow

```
1. User submits → /api/upload (POST)
                    ↓
2. Validate inputs (LLM, prompt, files/text)
                    ↓
3. Create job_id (UUID)
                    ↓
4. Start async analysis thread
                    ↓
5. Return job_id to user
                    ↓
6. User polls → /api/job/<job_id> (GET)
                    ↓
7. Backend processes request
                    - Extract text from file
                    - Load appropriate LLM interface
                    - Select prompt template
                    - Call LLM
                    - Parse results
                    - Generate PDF
                    ↓
8. Update job status
                    ↓
9. Return results to user
                    ↓
10. User downloads → /api/download/<job_id> (GET)
```

---

## 🚨 Error Handling

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Job status retrieved |
| 201 | Created | Job submitted successfully |
| 400 | Bad Request | Invalid LLM or prompt type |
| 404 | Not Found | Job ID doesn't exist |
| 500 | Server Error | Unhandled exception in backend |
| 503 | Service Unavailable | API key authentication failed |

### Common Error Responses

**Missing Required Parameter:**
```json
{
  "error": "LLM parameter required"
}
```

**Invalid LLM Model:**
```json
{
  "error": "Invalid LLM: unknown_model. Available: [gemini, chatgpt, llama, ...]"
}
```

**API Key Error:**
```json
{
  "error": "Authentication failed",
  "error_details": "GROQ_API_KEY not set in environment"
}
```

**File Too Large:**
```json
{
  "error": "File exceeds maximum size of 10MB"
}
```

**Unsupported File Type:**
```json
{
  "error": "File type not supported. Supported: PDF, DOCX, TXT"
}
```

**Timeout:**
```json
{
  "error": "Analysis request timed out after 60 seconds"
}
```

---

## 🔐 Security Considerations

### Input Validation
- File size limits (10MB max)
- Text input limits (10,000 chars max)
- Filename sanitization
- LLM/prompt validation

### Rate Limiting
- Groq: 30 requests/minute
- Google Gemini: 60 requests/minute
- OpenAI: Per-account tier
- Implement custom limits if needed

### CORS Protection
- Only allow trusted frontend origins
- Validate request headers
- Use secure API keys

### File Handling
- Temporary files deleted after processing
- No sensitive data retention
- Memory-efficient streaming for large files

---

## 🧪 Testing the API

### Using cURL

**Test Connection:**
```bash
curl http://localhost:5000/api/models
```

**Submit Simple Request:**
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "text=Test depression detection" \
  -F "llm=gemini" \
  -F "prompt=simple" \
  -w "\nStatus: %{http_code}\n"
```

**Poll Job Status:**
```bash
curl http://localhost:5000/api/job/<job_id> -s | python -m json.tool
```

### Using Python

```python
import requests

# Submit analysis
response = requests.post(
    "http://localhost:5000/api/upload",
    files={
        "text": (None, "I feel very depressed and hopeless"),
        "llm": (None, "gemini"),
        "prompt": (None, "simple")
    }
)
job = response.json()
job_id = job["job_id"]
print(f"Job ID: {job_id}")

# Check status
import time
while True:
    status = requests.get(f"http://localhost:5000/api/job/{job_id}").json()
    print(f"Status: {status['status']}")
    if status["status"] in ["completed", "failed"]:
        print(f"Result: {status}")
        break
    time.sleep(2)

# Download PDF
if status["status"] == "completed":
    pdf = requests.get(f"http://localhost:5000/api/download/{job_id}")
    with open("report.pdf", "wb") as f:
        f.write(pdf.content)
```

### Using JavaScript/Fetch

```javascript
// Submit analysis
const formData = new FormData();
formData.append("text", "I feel completely worthless and hopeless");
formData.append("llm", "gemini");
formData.append("prompt", "simple");

const response = await fetch("http://localhost:5000/api/upload", {
  method: "POST",
  body: formData
});

const job = await response.json();
const jobId = job.job_id;

// Poll status
const pollStatus = async () => {
  const status = await fetch(
    `http://localhost:5000/api/job/${jobId}`
  ).then(r => r.json());
  
  console.log(status);
  
  if (status.status !== "processing") {
    return status;
  }
  
  await new Promise(r => setTimeout(r, 2000));
  return pollStatus();
};

const result = await pollStatus();
console.log("Analysis complete:", result);
```

---

## 🐛 Troubleshooting

### API Won't Start

**Error:** `Address already in use`
```bash
# Kill process on port 5000
lsof -i :5000
kill -9 <PID>

# Or use different port
python -c "from api.app import app; app.run(port=8000)"
```

**Error:** `ModuleNotFoundError: No module named 'backend'`
```bash
# Ensure working directory is project root
cd Depression-detector

# Or adjust path
export PYTHONPATH="${PWD}"
python api/app.py
```

### API Starts But Can't Access

**Check if running:**
```bash
curl http://localhost:5000/api/models
```

**Check firewall:**
- Windows: Allow Python through firewall
- macOS/Linux: Check port isn't blocked

### Requests Hanging

**Possible causes:**
- Backend API key invalid/missing
- LLM provider API down
- Network timeout

**Debug:**
```bash
export FLASK_ENV=development
python api/app.py  # Shows detailed logs
```

### CORS Errors

**Error:** `Access to XMLHttpRequest has been blocked by CORS policy`

**Solution:** Update CORS origins in `app.py`:
```python
CORS(app, 
     origins=["http://localhost:5173", "https://yourdomain.com"],
     expose_headers=["Content-Disposition", "X-Depression-Classification"]
)
```

### Job Status Returns "Failed"

**Common reasons:**
1. API key invalid → Check `.env`
2. API quota exceeded → Wait or upgrade account
3. Text too long → Reduce input size
4. Network timeout → Increase timeout setting

**Check logs:**
```bash
tail -f depression_detector.log
```

---

## 🔍 Monitoring & Logging

### Enable Debug Logging

```bash
export FLASK_DEBUG=1
export LOG_LEVEL=DEBUG
python api/app.py
```

### Log Locations

- **Application logs:** `depression_detector.log`
- **Console output:** Terminal where API is running
- **Request logs:** Check Flask development server output

### Monitoring Job Queue

```python
# Check current jobs in memory
from api.app import jobs
print(f"Active jobs: {len(jobs)}")
for job_id, job in jobs.items():
    print(f"  {job_id}: {job['status']}")
```

---

## 📈 Performance & Scaling

### Current Limitations
- Job storage: In-memory (lost on restart)
- No database backend
- Single server instance
- Rate limits per provider

### Production Improvements

1. **Persistent Storage:**
   ```python
   # Use Redis or database
   from redis import Redis
   redis_client = Redis.from_url(os.getenv("REDIS_URL"))
   ```

2. **Task Queue:**
   ```python
   # Use Celery for async jobs
   from celery import Celery
   celery = Celery(app.name)
   ```

3. **Caching:**
   ```python
   from flask_caching import Cache
   cache = Cache(app, config={'CACHE_TYPE': 'redis'})
   ```

4. **Load Balancing:**
   - Run multiple API instances
   - Use Gunicorn with multiple workers
   - Put behind Nginx reverse proxy

---

## 🚀 Deployment

### Local Development
```bash
python api/app.py
```

### Production with Gunicorn
```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 api.app:app
```

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "api.app:app"]
```

### Environment Variables for Production
```env
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=generate-secure-key-here
CORS_ORIGINS=https://yourdomain.com
JOB_TIMEOUT=1800
```

---

## 📚 Integration with Frontend

The frontend (`vite-project/`) communicates with this API:

```javascript
// Submit request
const response = await fetch("/api/upload", {
  method: "POST",
  body: formData
});

// Poll for results
const checkStatus = async (jobId) => {
  return fetch(`/api/job/${jobId}`).then(r => r.json());
};

// Download report
window.location.href = `/api/download/${jobId}`;
```

---

## 📚 Integration with Backend

The API calls the backend processing engine:

```python
from backend.unified_engine import run_llm_job

# In async thread
result = run_llm_job(
    text=extracted_text,
    llm_type=llm.lower(),
    prompt_type=prompt_type
)
```

---

## 🎯 Key Functions

```python
# Main handlers
def upload()              # POST /api/upload
def get_job_status()      # GET /api/job/<job_id>
def download_report()     # GET /api/download/<job_id>
def get_models()          # GET /api/models

# Helper functions
def process_job()         # Async job processor
def extract_text()        # Text extraction from files
def validate_input()      # Input validation
```

---