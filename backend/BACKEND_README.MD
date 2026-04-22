# Backend Architecture & Documentation

The backend orchestrates LLM analysis, handles text processing, and manages model interfaces.

---

## 📁 Backend Structure

```
backend/
├── unified_engine.py          # Main LLM orchestrator & router
├── zero_shot_evaluation.py    # Model benchmarking tool
├── Common/                    # Shared utilities → See Common/README.md
├── Interfaces/                # LLM implementations → See Interfaces/README.md
└── BACKEND_README.md          # This file
```

---

## 🔄 Core Components

### 1. Unified Engine (`unified_engine.py`)

**Purpose:** Routes requests to the right LLM and returns results.

```python
run_llm_job(text: str, llm_type: str, prompt_type: str) -> dict
```

**Workflow:**
1. Validate LLM type & prompt type
2. Dynamically load LLM interface
3. Get prompt template
4. Call LLM API
5. Return standardized results

---

### 2. Common Utilities - [`backend/Common/README.md`](Common/README.md)

Shared tools for:
- Text extraction (PDF, DOCX, TXT)
- Prompt management (8 types)
- Groq API integration
- Sentence-level analysis

**Quick start:**
```python
from backend.Common.prompts import get_prompt
from backend.Common.engineUtils import extract_text_from_file
```

---

### 3. LLM Interfaces - [`backend/Interfaces/README.md`](Interfaces/README.md)

8 LLM models available:
- Groq: Llama 3.1, Llama 3.3, Compound (free)
- Google: Gemini 1.5 (free tier)
- OpenAI: GPT-4 (paid)
- Others: Qwen, Kimi, Grok

**All implement the same interface:**
```python
def analyze_text(text: str, prompt: str) -> dict
```

[See which model to use →](Interfaces/README.md#-which-to-use)

---

## ⚙️ Configuration

**Set up API keys** in `backend/Common/.env`:

```env
GROQ_API_KEY=gsk_...
GOOGLE_API_KEY=...
OPENAI_API_KEY=sk_...
```

[Full configuration details →](Common/README.md#-setup)

---

## 📊 Output Format

All models return standardized JSON:

```json
{
  "classification": "depression_detected",
  "confidence": 0.87,
  "analysis": "Detailed explanation...",
  "linguistic_features": {...},
  "model": "gemini",
  "processing_time_ms": 1234
}
```

---

## 🧪 Testing

### Test Individual Model
```python
from backend.unified_engine import run_llm_job
result = run_llm_job("I feel worthless", "gemini", "simple")
```

### Benchmark All Models
```bash
python -m backend.zero_shot_evaluation --prompt simple
```

### Test Sentence Analysis
```python
from backend.Common.sentence_analyzer import analyze_sentences
result = analyze_sentences("Your text here", "gemini")
```

---

## 🔌 Integration with API

The API calls the backend:

```python
from backend.unified_engine import run_llm_job

result = run_llm_job(
    text=user_input,
    llm_type=request.form.get("llm"),
    prompt_type=request.form.get("prompt")
)
```

**Result:** Returned to frontend as JSON response

---

## 📈 End-to-End Flow

```
User Input (Frontend)
    ↓
API receives /api/upload
    ↓
Backend: unified_engine.py
    ↓
Select appropriate LLM interface
    ↓
Get prompt template
    ↓
Call LLM API (Groq, Google, OpenAI, etc.)
    ↓
Parse & format response
    ↓
Generate PDF report (optional)
    ↓
Return results to frontend
    ↓
User sees classification & confidence
```

---

## 🎯 Key Functions

| Function | Location | Purpose |
|----------|----------|---------|
| `run_llm_job()` | `unified_engine.py` | Main orchestrator |
| `analyze_text()` | `Interfaces/*.py` | Model-specific analysis |
| `extract_text_from_file()` | `Common/engineUtils.py` | File → text |
| `get_prompt()` | `Common/prompts.py` | Get prompt template |
| `analyze_sentences()` | `Common/sentence_analyzer.py` | Sentence-level analysis |

---

## 🐛 Troubleshooting

| Issue | Location |
|-------|----------|
| API key errors | [Common/README.md](Common/README.md#-issues) |
| Model selection | [Interfaces/README.md](Interfaces/README.md#-troubleshooting) |
| File extraction problems | [Common/README.md](Common/README.md#-issues) |
| Rate limiting | [Interfaces/README.md](Interfaces/README.md#-troubleshooting) |

---

## 🤝 Adding New Functionality

**New LLM model?** → See [Interfaces/README.md](Interfaces/README.md#-add-new-model)

**New prompt type?** → Edit `backend/Common/prompts.py` and add to `PROMPTS` dict

**New utility?** → Add to `backend/Common/engineUtils.py`

---

## 📦 Dependencies

```
groq, google-generativeai, openai
PyPDF2, python-docx, reportlab
flask, flask-cors, werkzeug, python-dotenv
```

Install: `pip install -r ../../requirements.txt`

---

## 📚 Documentation

- **This file:** Backend overview & architecture
- [**Common/README.md**](Common/README.md) - Utilities & configuration
- [**Interfaces/README.md**](Interfaces/README.md) - LLM models & integration
- [**Root README**](../../README.md) - Project overview
- [**API_README**](../../api/API_README.md) - REST endpoints

---

**Backend Status:** Production Ready ✓

---

## 📊 Output Format

All backends return standardized JSON:

```json
{
  "classification": "depression_detected",
  "confidence": 0.87,
  "probability_depression": 0.87,
  "probability_no_depression": 0.13,
  "analysis": "Detailed analysis text...",
  "linguistic_features": {
    "first_person_pronouns": 8,
    "negative_emotion_words": 5,
    "hopelessness_indicators": 3,
    "social_isolation_markers": 2,
    "future_oriented_statements": 0
  },
  "model": "gemini",
  "prompt_type": "simple",
  "processing_time_ms": 1234,
  "timestamp": "2026-04-06T10:30:00Z"
}
---

## 🔍 Logging & Debugging

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python -c "from backend.unified_engine import run_llm_job; run_llm_job('test', 'gemini', 'simple')"
```

---

## 🤝 Contributing

**Add new LLM?** → Create `backend/Interfaces/YourModel.py` and register in `unified_engine.py`

**Add new utility?** → Add to `backend/Common/engineUtils.py`

**Add new prompt?** → Add to `backend/Common/prompts.py`

See [Interfaces/README.md](Interfaces/README.md#-add-new-model) for step-by-step guide.

---

## 📦 Dependencies

```
groq, google-generativeai, openai
PyPDF2, python-docx, reportlab
flask, flask-cors, werkzeug, python-dotenv
```

Install: `pip install -r requirements.txt`

---