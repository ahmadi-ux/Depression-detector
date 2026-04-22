# Depression Detector - Complete System Documentation

A comprehensive AI-powered system for detecting depression indicators in student writings using multiple Large Language Models. This project combines advanced natural language processing with a modern web interface to identify potential depression patterns through linguistic analysis.

![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![License](https://img.shields.io/badge/License-Research-blue)

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Research Objectives](#-research-objectives)
- [System Architecture](#EF%B8%8F-system-architecture)
- [Technology Stack](#%EF%B8%8F-technology-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
  - [Automated Setup (start-all.ps1)](#automated-setup-start-allps1---recommended)
  - [Manual Setup](#manual-setup)
    - [Installation](#1-installation)
    - [Configuration](#2-configuration)
    - [Running the Full Stack](#3-running-the-full-stack)
  - [Backend Only (API Testing)](#backend-only-api-testing)
  - [Frontend Only (Local Development)](#frontend-only-local-development)
- [Component Documentation](#-component-documentation)
  - [Frontend (Vite)](#frontend-vite)
  - [Backend (Flask API)](#backend-flask-api)
  - [LLM Interfaces](#llm-interfaces)
  - [Model Tuning & Evaluation](#model-tuning--evaluation)
- [Configuration](#%EF%B8%8F-configuration)
- [API Reference](#-api-reference)
- [Deployment](#-deployment)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [Research Context](#-research-context)
- [Additional Resources](#-additional-resources)
- [License](#-license)
- [Support](#-support)
- [Citation](#-citation)
- [Quick Reference Links](#-quick-reference-links)

---

## 🎯 Project Overview

**Depression Detector** is a research-driven application investigating whether Large Language Models can effectively predict depression in student populations by analyzing written content. The system provides an end-to-end solution from data collection through model evaluation and user-friendly result delivery.

### Key Capabilities

- **Multi-Model Analysis**: Compare depression detection across 5 different LLMs
- **Flexible Prompting**: 8 different analysis strategies for comprehensive evaluation
- **Real-time Processing**: Instant feedback on submitted texts or files
- **Research-Grade Evaluation**: Zero-shot and fine-tuned model comparison
- **Comprehensive Reporting**: PDF reports with detailed analysis metrics
- **User-Friendly Interface**: Modern web application with intuitive design

---

## 🔬 Research Objectives

### Primary Question
> *"Can Large Language Models predict self-reported depression and what specific language patterns can be used to identify depression among students in educational contexts?"*

### The Challenge

Depression among college students has reached critical levels:
- **44%** of college students report depression symptoms
- Traditional screening relies on infrequent self-report surveys (PHQ-9, BDI-II)
- Students often delay seeking help until symptoms are severe
- Current methods lack temporal tracking and early warning capabilities

### Research Approach

**Phase 1: Model Development**
- Evaluate Llama 3.1 (8B parameters) on public datasets
- Compare with GPT-4 via OpenAI API (zero-shot)
- Analyze Gemini 1.5 via Google API (zero-shot)
- Benchmark against multiple LLMs via Groq API
- Performance metrics: Accuracy, F1 Score, Precision, Recall

**Phase 2: Analysis Methods**
- Simple binary classification
- Structured checklist-based analysis
- Feature extraction and metric identification
- Chain-of-thought reasoning processes
- Few-shot learning with examples
- Free-form narrative analysis
- Sentence-by-sentence breakdown
- Multi-model comparison

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                         │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │         React/Vite Frontend (vite-project/)                   │  │
│  │  ├─ Home Page (project overview)                              │  │
│  │  ├─ Data Upload (file/text input)                             │  │
│  │  ├─ Model/Prompt Selection                                    │  │
│  │  └─ Results Display & Animation                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP/REST API
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    Application Layer (API)                          │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │         Flask API Server (api/app.py)                         │  │
│  │  ├─ /api/upload (handle submissions)                          │  │
│  │  ├─ /api/job/<id> (track job status)                          │  │
│  │  ├─ /api/download/<id> (get results PDF)                      │  │
│  │  └─ CORS middleware (cross-origin support)                    │  │
│  └───────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │ Backend Engine
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│                  Processing & Analysis Layer                        │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │    Unified LLM Engine (backend/unified_engine.py)             │  │
│  │  ├─ LLM Router (select appropriate interface)                 │  │
│  │  ├─ Text Extraction (file → text conversion)                  │  │
│  │  ├─ Prompt Selection (map strategy to template)               │  │
│  │  ├─ Result Aggregation (combine model outputs)                │  │
│  │  └─ PDF Report Generation                                     │  │
│  └───────────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │ Model Dispatch
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│              LLM Interfaces & External Services                     │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐     │
│  │  Llama (Groq)    │ │  Gemini (Google) │ │  ChatGPT (OpenAI)│     │
│  │  LlamaBig (Groq) │ │  Compound (Groq) │ │  Custom Models   │     │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘     │
│  [Via: Groq API]      [Via: Google Cloud]                           │
└─────────────────────────────────────────────────────────────────────┘

Additional Components:
┌─────────────────────────────────────────────────────────────────────┐
│  Model Tuning Pipeline (model_tuning/)                              │
│  ├─ Dataset Preparation                                             │
│  ├─ Fine-tuning Scripts (tune_driver.py, tune_driver_emoDepres.py)  │
│  ├─ Zero-shot Evaluation (backend/zero_shot_evaluation.py)          │
│  └─ Testing & Benchmarking (testing_scripts/)                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Technology Stack

### Frontend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | React | 19.2.0 | UI framework |
| Build Tool | Vite | 7.2.4 | Fast bundling & dev server |
| Styling | Tailwind CSS | 3.4.19 | Utility-first CSS |
| UI Components | Radix UI | Latest | Accessible component library |
| Routing | React Router | 7.10.1 | Client-side navigation |
| Forms | React Hook Form | 7.69.0 | Form state management |
| Validation | Zod | 4.2.1 | Type-safe validation |
| Icons | Lucide React | 0.561.0 | Icon library |

### Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | Flask | 2.3.3 | Web server framework |
| CORS | Flask-CORS | 4.0.0 | Cross-origin requests |
| Environment | python-dotenv | Latest | Environment variables |
| Testing | Pytest | Latest | Unit testing |
| PDF Generation | ReportLab/PyPDF | Latest | Report generation |

### LLM Providers

| Provider | Models | API | Integration |
|----------|--------|-----|-------------|
| **Groq** | Llama 3.1, Compound, LlamaBig, Llama 3.3-70B | REST API | Direct integration |
| **Google** | Gemini 1.5 | google-genai | Native Python SDK |
| **OpenAI** | GPT-4, GPT-4 Turbo | REST API | openai Python SDK |
| **Local** | Ollama (Llama2, etc.) | REST API | Local inference |

### Development & Testing

| Tool | Purpose |
|------|---------|
| ESLint | JavaScript code quality |
| Autoprefixer | CSS vendor prefixes |
| PostCSS | CSS transformation |
| Git | Version control |

---

## 📁 Project Structure

```
Depression-detector/
│
├── vite-project/                          # FRONTEND APPLICATION
│   ├── src/
│   │   ├── components/
│   │   │   ├── sections/
│   │   │   │   ├── Home.jsx               # Landing page
│   │   │   │   ├── Navigation.jsx         # Main nav bar
│   │   │   │   ├── DataUpload.jsx         # File upload UI
│   │   │   │   └── DataUploadTxt.jsx      # Text input UI
│   │   │   ├── ui/                        # Radix UI components
│   │   │   ├── ContactForm.jsx            # Main submission form
│   │   │   ├── SuccessModal.jsx           # Results display
│   │   │   └── ResultAnimation.jsx        # Animation effects
│   │   ├── App.jsx                        # Main component
│   │   ├── main.jsx                       # Entry point
│   │   └── lib/utils.js                   # Utility functions
│   ├── .env.dev                           # Dev environment config
│   ├── .env.prod                          # Prod environment config
│   ├── package.json                       # Dependencies
│   ├── vite.config.js                     # Vite configuration
│   ├── tailwind.config.js                 # Tailwind config
│   └── README.md                          # Frontend documentation
│
├── backend/                               # PROCESSING ENGINE
│   ├── unified_engine.py                  # Main LLM orchestrator
│   ├── zero_shot_evaluation.py            # Model benchmarking
│   ├── __init__.py
│   ├── Common/
│   │   ├── groq_handler.py                # Groq API integration
│   │   ├── engineUtils.py                 # Text extraction, PDF generation
│   │   ├── sentence_analyzer.py           # Sentence-level analysis
│   │   ├── prompts.py                     # Prompt templates
│   │   ├── prompt.txt                     # Prompt definitions
│   │   ├── Utils.py                       # General utilities
│   │   └── .env                           # Backend API keys
│   └── Interfaces/                        # LLM-specific implementations
│       ├── Llama.py                       # Llama interface
│       ├── ChatGPT.py                     # ChatGPT interface
│       ├── Gemini.py                      # Gemini interface
│       ├── Grok.py                        # Grok interface
│       ├── LlamaBig.py                    # LlamaBig interface
│       ├── Compound.py                    # Compound model interface
│       └── README.md                      # Interface documentation
│
├── api/                                   # FLASK API SERVER
│   ├── app.py                             # Main Flask application
│   └── __init__.py
│
├── model_tuning/                          # ML PIPELINE
│   ├── tune_driver.py                     # Training script (standard)
│   ├── tune_driver_emoDepres.py           # Training script (emotion-focused)
│   ├── README.txt                         # Pipeline documentation
│   ├── data_sets/                         # Training datasets (not in repo)
│   └── testing_scripts/                   # Model evaluation scripts
│       ├── GPT_20B_groq_emotion_multilabel.py
│       └── [other testing scripts]
│
├── start-all.ps1                          # Startup script (Windows PowerShell)
├── requirements.txt                       # Python dependencies
├── README.md                              # Overview & quick start
├── README_IN_DEPTH.md                     # Complete documentation
└── vercel.json                            # Deployment configuration
│
├── package.json                           # Root npm config
├── requirements.txt                       # Python dependencies
├── vercel.json                            # Vercel deployment config
├── start-all.ps1                          # Windows startup script
├── README.md                              # Quick start guide
├── README_IN_DEPTH.md                     # Complete documentation
└── INTERNSHIP_REPORT.md                   # Internship summary report

**Key Directories:**
- `api/`: Flask server handles requests
- `backend/`: Core ML processing logic
- `vite-project/`: React frontend UI
- `model_tuning/`: Dataset and model training
```

---

## 📦 Prerequisites

### System Requirements
- **OS**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+)
- **RAM**: Minimum 8GB (16GB recommended)
- **Disk**: 5GB free space
- **Network**: Stable internet connection (for API calls)

### Software Requirements

#### Node.js & npm (for Frontend)
- Node.js v18.0.0+ ([Download](https://nodejs.org/))
- npm v9.0.0+ (included with Node.js)

Verify:
```bash
node --version  # >= v18.0.0
npm --version   # >= v9.0.0
```

#### Python (for Backend)
- Python 3.9+ ([Download](https://www.python.org/))
- Recommended: Python 3.10.x

Verify:
```bash
python --version  # >= 3.9
```

#### Ollama (for Local LLM Inference)
- **Ollama** ([Download](https://ollama.ai/))
- Required for using local Llama models
- Lightweight inference engine (~600MB)

Verify:
```bash
ollama --version
```

#### API Keys Required

You'll need API keys for at least one LLM provider:

1. **Groq** (Recommended - free tier available)
   - [Get API Key](https://console.groq.com/keys)
   - Supports: Llama 3.1, Compound, LlamaBig, Llama 3.3-70B

2. **Google Gemini**
   - [Get API Key](https://aistudio.google.com/app/apikey)
   - Free tier: 60 requests/minute

3. **OpenAI**
   - [Get API Key](https://platform.openai.com/account/api-keys)
   - Paid service (credits-based)

4. **Other Providers** (optional)
   - Alibaba Qwen, Moonshot Kimi, X.AI Grok
   - See [Configuration](#configuration) for setup

### Recommended Tools
- **Git** ([Download](https://git-scm.com/))
- **VS Code** with Python & JavaScript extensions
- **Postman** for API testing
- **Flask Development Tools** for backend debugging

---

## 🚀 Quick Start

### Automated Setup (start-all.ps1) - Recommended

**For Windows users, use the automated startup script:**

```powershell
# Navigate to project root
cd Depression-detector

# Run the startup script
.\start-all.ps1
```

The script automatically:
1. ✅ Starts Ollama server (local LLM inference engine)
2. ✅ Starts Flask API server (backend processing)
3. ✅ Starts Vite frontend development server
4. ✅ Opens new terminal windows for each service
5. ✅ Displays all service URLs

**Services Running At:**
- Ollama: http://localhost:11434
- API: http://localhost:5000
- Frontend: **http://localhost:5173** ← Use this to access the app

---

### Manual Setup

#### 1. Installation

**Clone & Install Dependencies:**
```bash
cd Depression-detector

# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd vite-project
npm install
cd ..
```

#### 2. Configuration

**Set API Keys:**
```bash
cd backend/Common

# Create .env file
# Add your API keys:
# GROQ_API_KEY=your_groq_api_key_here
# GOOGLE_API_KEY=your_google_api_key_here
# OPENAI_API_KEY=your_openai_api_key_here

cd ../..
```

#### 3. Running the Full Stack

**Terminal 1 - Start Ollama:**
```bash
ollama serve
# Output: Listening on 127.0.0.1:11434
```

**Terminal 2 - Start Backend:**
```bash
python api/app.py
# Server runs on http://localhost:5000
```

**Terminal 3 - Start Frontend:**
```bash
cd vite-project
npm run dev
# Frontend runs on http://localhost:5173
```

Then visit: **`http://localhost:5173`** in your browser

---

### Backend Only (API Testing)

```bash
# Install dependencies
pip install -r requirements.txt

# Test analysis with Python
python -c "
from backend.unified_engine import run_llm_job
result = run_llm_job('Test text about depression', 'gemini', 'simple')
print(result)
"
```

---

### Frontend Only (Local Development)

```bash
cd vite-project
npm install
npm run dev
# Frontend accessible at http://localhost:5173
# (Requires backend API running on http://localhost:5000)
```

---

## 📖 Component Documentation

### Frontend (Vite)

**Location:** `vite-project/`

**Documentation:** [vite-project/README.md](vite-project/README.md)

**Key Features:**
- Modern React 19 with hooks
- Real-time form validation (Zod + React Hook Form)
- Responsive Tailwind CSS design
- Radix UI accessible components
- React Router SPA navigation
- Environment-based API configuration

**Development Commands:**
```bash
npm run dev        # Start development server
npm run build      # Create production bundle
npm run lint       # Check code quality
npm run preview    # Preview production build
```

---

### Backend (Flask API)

**Location:** `api/app.py`

**Core Endpoints:**

#### `POST /api/upload`
Submit text/file for depression analysis

**Request:**
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "text=Student writing sample..." \
  -F "llm=gemini" \
  -F "prompt=simple"
```

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "processing",
  "message": "Analysis started"
}
```

#### `GET /api/job/<job_id>`
Get job status and results

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "completed",
  "classification": "depression_detected",
  "confidence": 0.92,
  "analysis": "Detailed analysis text...",
  "metrics": {...}
}
```

#### `GET /api/download/<job_id>`
Download results as PDF report

---

### LLM Interfaces

**Location:** `backend/Interfaces/`

**Supported Models:**

| Model | File | Provider | Capabilities |
|-------|------|----------|--------------|
| Llama 3.1 | `Llama.py` | Groq | 8B parameters, fast inference |
| LlamaBig | `LlamaBig.py` | Groq | 70B parameters, higher quality |
| Compound | `Compound.py` | Groq | Multi-model combination |
| ChatGPT | `ChatGPT.py` | OpenAI | GPT-4, GPT-4 Turbo |
| Gemini | `Gemini.py` | Google | Gemini 1.5, 2.0 |

**Adding a New Model:**

1. Create new file: `backend/Interfaces/YourModel.py`
2. Implement `analyze_text(text: str, prompt: str) -> dict` function
3. Register in `backend/unified_engine.py`:
```python
LLM_INTERFACES = {
    "yourmodel": "backend.Interfaces.YourModel",
}
```
4. Test with `python -c "from backend.unified_engine import get_llm_interface; ..."`

---

### Model Tuning & Evaluation

**Location:** `model_tuning/`

**Components:**

#### Zero-Shot Evaluation
**File:** `backend/zero_shot_evaluation.py`

Benchmark models without fine-tuning:
```bash
python -m backend.zero_shot_evaluation \
  --model llama-3.1-8b-instant \
  --prompt chain_of_thought
```

#### Fine-Tuning Pipeline
**Files:** `tune_driver.py`, `tune_driver_emoDepres.py`

Prepare and fine-tune models:
```bash
python model_tuning/tune_driver.py \
  --dataset data_sets/depression_reddit_cleaned.csv \
  --epochs 3 \
  --batch-size 32
```

#### Testing Scripts
**Directory:** `model_tuning/testing_scripts/`

Run comprehensive model tests:
```bash
python model_tuning/testing_scripts/GPT_20B_groq_emotion_multilabel.py \
  --max-samples 100 \
  --output results.csv
```

---

## ⚙️ Configuration

### Environment Variables

#### Backend Configuration
**File:** `backend/Common/.env`

```env
# LLM API Keys
GROQ_API_KEY=gsk_your_key_here
GOOGLE_API_KEY=your_google_key

# Logging
LOG_LEVEL=INFO
LOG_FILE=depression_detector.log

# Rate Limiting
REQUESTS_PER_MINUTE=30
REQUEST_TIMEOUT=60

# Model Defaults
DEFAULT_LLM=gemini
DEFAULT_PROMPT=simple

# PDF Reporting
ENABLE_PDF_EXPORT=true
PDF_INCLUDE_METRICS=true
```

#### Frontend Configuration
**Development:** `vite-project/.env.dev`
```
VITE_API_URL=http://localhost:5000
```

**Production:** `vite-project/.env.prod`
```
VITE_API_URL=https://api.yourdomain.com
```

### Available Prompt Types

1. **simple** - Binary classification (depression/no depression)
2. **structured** - Checklist-based analysis with scoring
3. **feature_extraction** - Identify specific linguistic patterns
4. **chain_of_thought** - Step-by-step reasoning process
5. **few_shot** - Examples-based learning
6. **free_form** - Narrative detailed analysis
7. **sentence** - Line-by-line breakdown
8. **ollama_compare** - Multi-model comparison

See `backend/Common/prompts.py` for template details.

---

## 🌐 API Reference

### Depression Detector API

**Base URL:** `http://localhost:5000`

#### Submit Analysis

```http
POST /api/upload
Content-Type: multipart/form-data

Parameters:
- text (string): Text to analyze
- llm (string): Model to use (gemini, chatgpt, llama, etc.)
- prompt (string): Analysis type (simple, structured, etc.)
- files (optional): File upload

Response: 201 Created
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Analysis job submitted"
}
```

#### Check Job Status

```http
GET /api/job/550e8400-e29b-41d4-a716-446655440000

Response: 200 OK
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "classification": "depression_detected",
  "confidence": 0.87,
  "analysis": "Detailed analysis results...",
  "created_at": "2026-04-01T10:30:00Z",
  "completed_at": "2026-04-01T10:35:23Z"
}
```

#### Download Results

```http
GET /api/download/550e8400-e29b-41d4-a716-446655440000

Response: 200 OK
Content-Type: application/pdf
Content-Disposition: attachment; filename="analysis_report.pdf"
[Binary PDF data]
```

### LLM Provider APIs

Each model has specific configurations. See `backend/Interfaces/[Model].py` for details.

---

## 🚀 Deployment

### Frontend Deployment (Vercel - Recommended)

**Configuration:** `vite-project/vercel.json`

1. **Connect Repository**
   ```bash
   npm i -g vercel
   vercel login
   vercel link
   ```

2. **Configure Build**
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Framework: Vite

3. **Environment Variables**
   - Set `VITE_API_URL` to production API URL

4. **Deploy**
   ```bash
   vercel deploy --prod
   ```

### Backend Deployment (Heroku / Docker)

#### Option A: Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV FLASK_APP=api/app.py
EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "api.app:app"]
```

```bash
# Build and run
docker build -t depression-detector .
docker run -p 5000:5000 -e GROQ_API_KEY=$GROQ_API_KEY depression-detector
```

#### Option B: Direct Server Deployment

```bash
# Install production dependencies
pip install gunicorn flask

# Run production server
gunicorn --bind 0.0.0.0:5000 --workers 4 api.app:app

# For background daemon use:
pm2 start api/app.py --name depression-detector --interpreter python
```

### Configuration on Server

1. **Set Environment Variables**
   ```bash
   export GROQ_API_KEY=your_key
   export GOOGLE_API_KEY=your_key
   # etc...
   ```

2. **Configure CORS**
   - Update `api/app.py` CORS settings
   - Allow frontend domain

3. **SSL/HTTPS**
   - Use Let's Encrypt for certificates
   - Configure reverse proxy (Nginx/Apache)

4. **Monitoring**
   - Set up error logging
   - Configure performance monitoring
   - Set up automated backups

---

## 🐛 Troubleshooting

### Frontend Issues

#### Port 5173 Already in Use
```bash
# Windows
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :5173
kill -9 <PID>
```

#### Module Not Found
```bash
# Clear and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

#### API Connection Failed
- Check backend is running on `http://localhost:5000`
- Verify `.env.dev` has correct `VITE_API_URL`
- Check browser console (F12) for CORS errors

---

### Backend Issues

#### Import Error: "No module named 'backend'"
```bash
# Ensure working directory is project root
cd c:\Users\sgtjd\...\Depression-detector

# Verify Python path
python -c "import sys; print(sys.path)"

# Test import
python -c "from backend.unified_engine import run_llm_job"
```

#### API Key Errors
```bash
# Verify .env file exists
ls backend/Common/.env

# Test API key
python backend/Common/groq_handler.py

# Check API key format
echo $GROQ_API_KEY
```

#### Rate Limiting / API Errors
- Check provider rate limits
- Monitor request frequency
- See `backend/Common/sentence_analyzer.py` for rate limit config
- Implement retry logic or backoff

---

### Common API Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Check `.env` file, regenerate key |
| 429 Too Many Requests | Rate limit exceeded | Increase delay between requests |
| 500 Internal Server Error | Backend crash | Check Flask logs, verify input format |
| CORS Error | Frontend can't reach backend | Update CORS settings in `api/app.py` |
| File Upload Failed | Large file size | Implement chunking or size limits |

---

## 🤝 Contributing

### Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make Changes**
   - Follow code style guidelines
   - Add tests for new functionality
   - Update documentation

3. **Test Thoroughly**
   ```bash
   npm run lint          # Frontend
   python -m pytest      # Backend
   npm run build         # Production build test
   ```

4. **Commit & Push**
   ```bash
   git commit -m "feat: your feature description"
   git push origin feature/your-feature
   ```

5. **Create Pull Request**
   - Describe changes clearly
   - Link related issues
   - Request review from team members

### Code Standards

**Frontend:**
- Use ESLint configuration
- Follow React hooks best practices
- Component naming: PascalCase
- Variable naming: camelCase
- Use TypeScript when possible

**Backend:**
- Follow PEP 8 style guide
- Use type hints
- Document functions with docstrings
- Implement error handling
- Add logging statements

**Commits:**
- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- Write descriptive messages
- Reference issues when applicable

---

## 🔬 Research Context

### Dataset
- **Source**: Reddit depression community posts (Kaggle: [depression-reddit-cleaned](https://www.kaggle.com/datasets/infamouscoder/depression-reddit-cleaned))
- **Format**: Binary labeled (depressed/non-depressed)
- **Size**: 5000+ posts (exact count varies)
- **Preprocessing**: Text cleaning, normalization

### Models Evaluated
- Llama 3.1 (8B & 70B)
- GPT-4 / GPT-4 Turbo
- Gemini 1.5
- Qwen 2
- Kimi K2
- Grok
- Compound models

### Evaluation Metrics
- **Accuracy**: Overall correctness
- **Precision**: True positives / predicted positives
- **Recall**: True positives / actual positives
- **F1 Score**: Harmonic mean of precision & recall
- **Confusion Matrix**: Classification breakdown

### Key Findings (So Far)
- LLMs can detect depression with reasonable accuracy
- Structured prompts outperform simple classification
- Ensemble approaches improve performance
- Specific linguistic patterns are consistently identified

---

## 📚 Additional Resources

### Documentation
- [Frontend README](vite-project/README.md) - Detailed frontend documentation
- [Backend README](backend/Interfaces/README.md) - Interface documentation
- [Model Tuning README](model_tuning/README.txt) - Training pipeline docs

### External References
- [Groq Documentation](https://console.groq.com/docs)
- [Google Generative AI](https://aistudio.google.com)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com)
- [React Documentation](https://react.dev)
- [Vite Documentation](https://vite.dev)

### Mental Health Resources
- [NAMI Helpline](https://www.nami.org)
- [Crisis Text Line](https://www.crisistextline.org)
- [988 Suicide & Crisis Lifeline](https://988lifeline.org)

---

## 📄 License

This project is part of the Depression Detector research initiative. For licensing information and academic usage, refer to your institution's policies.

---

## 📧 Support

For issues, questions, or feedback:
1. Check the troubleshooting section above
2. Review component-specific READMEs
3. Check GitHub issues if repository is public
4. Contact the research team

---

## 🗣️ Citation

If you use this research in your work, please cite:

```bibtex
@software{depression_detector_2026,
  title="Depression Detector: LLM-Based Analysis of Student Depression Indicators",
  author="[Blue Nucleus GVSU]",
  year=2026,
  url="https://github.com/ahmadi-ux/Depression-detector/tree/main",
  note="Depression detection using Large Language Models"
}
```

---

**Last Updated**: April 2026  
**Version**: 1.0.0  
**Status**: Production Ready  
**Maintainer**: [Blue Nucleus GVSU]

---

## 🎯 Quick Reference Links

| Component | Location | Purpose |
|-----------|----------|---------|
| Frontend | [vite-project/](vite-project/) | User interface |
| Backend | [backend/](backend/) | Processing engine |
| API | [api/](api/) | REST endpoints |
| Models | [model_tuning/](model_tuning/) | ML pipeline |
| Config | [backend/Common/.env]() | API keys & settings |

**Get Started:** Run `npm install && pip install -r requirements.txt` then follow [Quick Start](#quick-start) section.
