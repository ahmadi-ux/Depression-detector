# Depression Detector - Overview & Quick Start

A comprehensive AI-powered system for detecting depression indicators in student writings using multiple Large Language Models (LLMs). This application combines advanced natural language processing with a modern React web interface.

**For complete documentation, see [README_COMPLETE.md](README_IN_DEPTH.md)**

---

## 🎯 Project Overview

**Research Question:**
> *"Can Large Language Models predict self-reported depression and what specific language patterns can be used to identify depression among students in educational contexts?"*

### Key Capabilities
- **Multi-Model Support**: Compare 8+ different LLMs (Gemini, GPT, Llama, Qwen, Kimi, Grok)
- **Flexible Analysis**: 8 different prompting strategies
- **Real-time Processing**: Instant feedback on submitted texts
- **Research-Grade**: Zero-shot and fine-tuned model evaluation
- **User-Friendly**: Modern web interface with responsive design

---

## 🏗️ System Architecture

```
Frontend (React/Vite)
      ↓
Flask API Server
      ↓
Unified LLM Engine
      ↓
Multiple LLM Providers (Groq, Google, OpenAI, Alibaba, Moonshot, X.AI)
```

---

## 📊 The Challenge

Depression among college students is critical:
- **44%** of college students report depression symptoms
- Traditional screening relies on infrequent surveys (PHQ-9, BDI-II)
- Students often delay seeking help until symptoms are severe
- Current methods lack early warning capabilities

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18.0.0+ and npm 9.0.0+
- Python 3.9+
- API key from Groq, Google Gemini, or OpenAI

### 1. Clone & Navigate
```bash
cd Depression-detector
```

### 2. Backend Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure API keys
cd backend/Common
# Create .env file with GROQ_API_KEY, GOOGLE_API_KEY, etc.
cd ../..
```

### 3. Frontend Setup
```bash
cd vite-project
npm install
cd ..
```

### 4. Run the System

**Terminal 1 - Start Backend:**
```bash
python api/app.py
# Server: http://localhost:5000
```

**Terminal 2 - Start Frontend:**
```bash
cd vite-project
npm run dev
# App: http://localhost:5173
```

Visit `http://localhost:5173` in your browser.

---

## 📁 Project Structure

```
Depression-detector/
├── vite-project/              # Frontend (React/Vite)
├── backend/                   # Processing engine & LLM interfaces
├── api/                       # Flask API server
├── model_tuning/              # ML pipeline & evaluation
├── requirements.txt           # Python dependencies
└── README_COMPLETE.md         # Comprehensive documentation
```

### Key Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **Frontend** | `vite-project/` | React UI for data submission & results |
| **Backend** | `backend/` | LLM orchestration & text analysis |
| **API** | `api/app.py` | REST endpoints for frontend |
| **Model Tuning** | `model_tuning/` | Fine-tuning & evaluation scripts |

---

## 🛠️ Technology Stack

**Frontend:**
- React 19.2.0
- Vite 7.2.4
- Tailwind CSS 3.4.19
- Radix UI components

**Backend:**
- Python 3.9+
- Flask 2.3.3
- Groq, Google, OpenAI APIs

**LLM Models:**
- Llama 3.1 & 3.3 (Groq)
- GPT-4 & GPT-4 Turbo (OpenAI)
- Gemini 1.5 (Google)
- Qwen 2 (Alibaba)
- Kimi K2 (Moonshot)
- Grok (X.AI)
- Compound (Groq)

---

## 📖 Available Analysis Methods

| Method | Description | Use Case |
|--------|-------------|----------|
| **Simple** | Binary classification | Quick assessment |
| **Structured** | Checklist-based scoring | Comprehensive analysis |
| **Feature Extraction** | Linguistic pattern identification | Research insights |
| **Chain-of-Thought** | Step-by-step reasoning | Transparent explanations |
| **Few-Shot** | Example-based learning | Improved accuracy |
| **Free-Form** | Narrative analysis | Detailed insights |
| **Sentence-Level** | Line-by-line breakdown | Granular analysis |
| **Model Comparison** | Multi-model evaluation | Consensus analysis |

---

## ⚙️ Configuration

### Environment Variables
Create `backend/Common/.env`:
```env
GROQ_API_KEY=your_groq_key
GOOGLE_API_KEY=your_google_key
OPENAI_API_KEY=your_openai_key
```

### Frontend Config
- Development: `vite-project/.env.dev` → `VITE_API_URL=http://localhost:5000`
- Production: `vite-project/.env.prod` → `VITE_API_URL=https://api.yourdomain.com`

---

## 📚 Documentation

- **Complete Guide**: [README_COMPLETE.md](README_COMPLETE.md) - Full system documentation
- **Frontend**: [vite-project/README.md](vite-project/README.md) - React/Vite details
- **Backend**: [backend/Interfaces/README.md](backend/Interfaces/README.md) - LLM interfaces
- **Model Tuning**: [model_tuning/README.txt](model_tuning/README.txt) - ML pipeline

---

## 🐛 Troubleshooting

### Backend Won't Start
```bash
# Check Python path
python -c "from backend.unified_engine import run_llm_job"

# Verify API keys
echo $GROQ_API_KEY
```

### Frontend Port Issues
```bash
# Windows: Kill process on port 5173
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

### API Connection Error
- Verify backend running on `http://localhost:5000`
- Check `.env.dev` has correct `VITE_API_URL`
- Check browser console (F12) for CORS errors

**For more troubleshooting:** See [README_COMPLETE.md#troubleshooting](README_COMPLETE.md#troubleshooting)

---

## 📱 API Endpoints

### Submit Analysis
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "text=Your text here" \
  -F "llm=gemini" \
  -F "prompt=simple"
```

### Check Results
```bash
curl http://localhost:5000/api/job/<job_id>
```

### Download Report
```bash
curl http://localhost:5000/api/download/<job_id> --output report.pdf
```

---

## 🚀 Deployment

### Frontend (Vercel)
```bash
cd vite-project
npm run build
vercel deploy --prod
```

### Backend (Docker)
```bash
docker build -t depression-detector .
docker run -p 5000:5000 -e GROQ_API_KEY=$GROQ_API_KEY depression-detector
```

**Full deployment guide:** See [README_COMPLETE.md#deployment](README_COMPLETE.md#deployment)

---

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and test
3. Run linter: `npm run lint` (frontend), `black . && pylint .` (backend)
4. Commit: `git commit -m "feat: your feature"`
5. Push: `git push origin feature/your-feature`
6. Create Pull Request

---

## 📊 Research Context

### Datasets
- **Primary**: Reddit depression community (Kaggle)
- **Size**: 5000+ labeled posts
- **Labels**: Depressed / Non-depressed

### Models Evaluated
- Llama 3.1 (8B & 70B)
- GPT-4 / Turbo
- Gemini 1.5
- Qwen 2, Kimi K2, Grok
- Compound models

### Metrics
- Accuracy, Precision, Recall, F1 Score
- Confusion matrices
- Linguistic pattern analysis

---

## 📧 Support & Questions

- **Complete Documentation**: [README_COMPLETE.md](README_COMPLETE.md)
- **Frontend Help**: [vite-project/README.md](vite-project/README.md#troubleshooting)
- **Backend Help**: See component-specific documentation
- **Issues**: Check troubleshooting sections above

---

## 📄 License

Part of the Depression Detector research initiative. See institution policies for academic usage.

---

## 🔗 Quick Links

| Link | Purpose |
|------|---------|
| [Complete Documentation](README_COMPLETE.md) | Full system guide |
| [Frontend](vite-project/) | React application |
| [Backend](backend/) | Processing engine |
| [API](api/app.py) | REST endpoints |
| [Models](model_tuning/) | ML pipeline |

---

**Version**: 1.0.0 | **Status**: Production Ready | **Last Updated**: April 2026

**Next Steps:**
1. Follow [Quick Start](#quick-start) above
2. Read [README_COMPLETE.md](README_COMPLETE.md) for comprehensive guide
3. Check component-specific documentation for details
4. Run example analysis to verify setup
