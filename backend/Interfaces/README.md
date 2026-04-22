# LLM Interfaces

Individual model files. Each implements `analyze_text(text, prompt) -> dict`.

---

## 📁 Available Models

| Model | File | Provider | Speed | Cost |
|-------|------|----------|-------|------|
| Llama 3.1 8B | `Llama.py` | Groq | ⚡⚡⚡ | Free |
| Llama 3.3 70B | `LlamaBig.py` | Groq | ⚡⚡ | Free |
| Compound | `Compound.py` | Groq | ⚡⚡ | Free |
| Gemini 1.5 | `Gemini.py` | Google | ⚡⚡ | Free tier |
| GPT-4 | `ChatGPT.py` | OpenAI | ⚡ | Paid |
| Qwen 2 | `Qwen.py` | Alibaba | ⚡⚡⚡ | Free |
| Kimi K2 | `Kimi2.py` | Moonshot | ⚡⚡ | Paid |
| Grok | `Grok.py` | X.AI | ⚡⚡ | Paid |

---

## 🚀 Quick Usage

```python
from backend.unified_engine import run_llm_job

result = run_llm_job(
    text="I feel worthless",
    llm_type="gemini",          # or llama, chatgpt, etc.
    prompt_type="simple"        # or structured, chain_of_thought, etc.
)
```

---

## 🎯 Which to Use?

- **Testing** → `Llama.py` (fastest, free)
- **Production** → `Gemini.py` (balanced, free tier)
- **Best accuracy** → `ChatGPT.py` (GPT-4)
- **Validation** → `Compound.py` (consensus)

---

## 📝 Add New Model

1. Create `backend/Interfaces/YourModel.py`:
```python
def analyze_text(text: str, prompt: str) -> dict:
    # Your implementation
    return {
        "classification": "depression_detected",
        "confidence": 0.85,
        "analysis": "...",
        "model": "your_model"
    }
```

2. Register in `backend/unified_engine.py`:
```python
LLM_INTERFACES = {"yourmodel": "backend.Interfaces.YourModel"}
LLM_DISPLAY_NAMES = {"yourmodel": "Your Model Name"}
```

3. Add API key to `backend/Common/.env`:
```env
YOUR_MODEL_API_KEY=your_key_here
```

4. Test: `python -c "from backend.unified_engine import run_llm_job; run_llm_job('test', 'yourmodel', 'simple')"`

---

## 🐛 Troubleshooting

| Error | Fix |
|-------|-----|
| API key not found | Check `.env` in `backend/Common/` |
| Connection timeout | API provider down or no internet |
| Rate limited | Wait a minute (Groq: 30/min, Gemini: 60/min) |
| Invalid response | Try different prompt type or reduce text |

---