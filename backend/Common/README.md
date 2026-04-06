# Common Utilities

Shared helpers for text processing, API calls, and result formatting.

---

## 🚀 Quick Usage

### Extract Text
```python
from backend.Common.engineUtils import extract_text_from_file
text = extract_text_from_file(file_object)  # PDF, DOCX, TXT
```

### Get Prompt
```python
from backend.Common.prompts import get_prompt
prompt = get_prompt("simple")  # or "structured", "chain_of_thought", etc.
```

### Analyze Sentences
```python
from backend.Common.sentence_analyzer import analyze_sentences
results = analyze_sentences("Your text here", "gemini")
```

---

## 📋 Prompt Types

- `simple` - Binary yes/no
- `structured` - Checklist analysis
- `feature_extraction` - Linguistic patterns
- `chain_of_thought` - Step-by-step reasoning
- `few_shot` - Example-based
- `free_form` - Detailed narrative
- `sentence` - Line-by-line
- `ollama_compare` - Multi-model comparison

---

## ⚙️ Setup

Create `backend/Common/.env`:
```env
GROQ_API_KEY=gsk_...
GOOGLE_API_KEY=...
OPENAI_API_KEY=sk_...
```

---

## 🔧 Main Functions

| Function | What It Does |
|----------|-------------|
| `extract_text_from_file(file)` | PDF/DOCX/TXT → text |
| `get_prompt(type)` | Get prompt template |
| `analyze_sentences(text, llm)` | Analyze by sentence |

---

## 🐛 Issues

**API key error?** → Check `.env` exists and has correct key  
**Module not found?** → Run from project root  
**File not supported?** → Use PDF, DOCX, or TXT only  

---

**Used by:** All LLM interfaces | Called from: `unified_engine.py`