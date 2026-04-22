# Depression Detector - Frontend Application

A modern, user-friendly web application designed to identify potential depression indicators in student writings using advanced Large Language Models (LLMs). This application leverages cutting-edge AI technology to analyze linguistic patterns and provide insights into emotional and mental health indicators.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Development](#development)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Usage Guide](#usage-guide)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## 🎯 Overview

**Depression Detector** is a research-backed application that investigates the following research question:

> *"Can Large Language Models predict self-reported depression, and what specific language patterns can be used to identify depression among students in educational contexts?"*

The application provides an intuitive interface for uploading and analyzing student writings, with support for multiple AI models and sophisticated analysis methodologies. It's built as a modern, responsive web application with real-time feedback and comprehensive reporting features.

---

## ✨ Key Features

- **Multi-Model Support**: Integration with multiple LLM providers (Gemini, GPT, Ollama, and more)
- **Flexible Analysis Methods**: 8+ different prompting strategies including:
  - Simple binary classification
  - Structured checklist analysis
  - Feature extraction metrics
  - Chain-of-thought reasoning
  - Few-shot learning examples
  - Free-form narrative analysis
  - Sentence-by-sentence breakdown
  - Model comparison analysis
- **Rich User Interface**: Clean, modern design with Tailwind CSS and Radix UI components
- **Real-time Results**: Instant feedback with success modals and result animations
- **Text & File Input**: Support for both direct text input and file uploads
- **Responsive Design**: Fully mobile-friendly interface
- **Form Validation**: Robust client-side validation using React Hook Form and Zod
- **Environment Management**: Separate configurations for development and production

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|-----------|
| **Framework** | React 19.2.0 with Vite 7.2.4 |
| **Styling** | Tailwind CSS 3.4.19 + PostCSS |
| **UI Components** | Radix UI, Lucide React Icons |
| **Form Management** | React Hook Form 7.69.0 + Zod 4.2.1 |
| **Routing** | React Router 7.10.1 |
| **Backend Services** | Firebase 12.7.0 |
| **Utilities** | CLSX, Tailwind Merge, Class Variance Authority |
| **Development** | Vite, ESLint, Autoprefixer |

---

## 📦 Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (v18.0.0 or higher) - [Download](https://nodejs.org/)
- **npm** (v9.0.0 or higher) - Usually installed with Node.js
- **Git** - [Download](https://git-scm.com/)
- **Backend API** running locally or accessible via network (default: `http://localhost:5000`)

### Verify Installation
```bash
node --version  # Should be v18.0.0 or higher
npm --version   # Should be v9.0.0 or higher
git --version
```

---

## 🚀 Installation & Setup

> **Quick Tip:** To start all services (Ollama, API, and Frontend) at once from the project root, run: `.\start-all.ps1`

### 1. Clone the Repository
```bash
cd c:\Users\sgtjd\.AVisualStudioProjects\BlueNucleus\Depression-detector
```

### 2. Install Dependencies
```bash
cd vite-project
npm install
```

This will install all required packages listed in `package.json`, including:
- React and React DOM
- Vite build tools
- UI component libraries (Radix UI)
- Form handling and validation tools
- Firebase integration

### 3. Environment Configuration

#### Development Environment
The `.env.dev` file is already configured for local development:
```
VITE_API_URL=http://localhost:5000
```

#### Production Environment
Update `.env.prod` with your production API URL:
```
VITE_API_URL=https://your-production-api.com
```

### 4. Start Development Server

**Option A: Start Frontend Only (Requires backend running separately)**
```bash
npm run dev
# Frontend: http://localhost:5173
```

**Option B: Start All Services at Once (Windows)**
```bash
# From the project root directory
cd ..
.\start-all.ps1
```

The application should now be accessible at `http://localhost:5173` in your browser.

---

## 💻 Development

### Available Scripts

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start development server with hot-reload |
| `npm run build` | Build optimized production bundle |
| `npm run lint` | Run ESLint to check code quality |
| `npm run preview` | Preview production build locally |

### Development Workflow

1. **Start Development Server**
   ```bash
   npm run dev
   ```
   - Hot Module Replacement (HMR) enabled for instant updates
   - Development mode with source maps for debugging

2. **Make Changes**
   - Edit files in the `src/` directory
   - Changes automatically reload in the browser

3. **Check Code Quality**
   ```bash
   npm run lint
   ```
   - Identifies code issues and style violations
   - Fix issues before committing

4. **Build for Production**
   ```bash
   npm run build
   ```
   - Creates optimized production bundle in `dist/` folder
   - Minimized and tree-shaken code

---

## 📁 Project Structure

```
vite-project/
├── public/                          # Static assets
├── src/
│   ├── components/
│   │   ├── sections/
│   │   │   ├── Home.jsx             # Landing page with project overview
│   │   │   ├── Navigation.jsx       # Main navigation bar
│   │   │   ├── DataUpload.jsx       # File upload interface
│   │   │   └── DataUploadTxt.jsx    # Text input interface
│   │   ├── ui/                      # Reusable UI components (Radix-based)
│   │   │   ├── alert.jsx
│   │   │   ├── button.jsx
│   │   │   ├── dialog.jsx
│   │   │   ├── dropdown-menu.jsx
│   │   │   ├── form.jsx
│   │   │   ├── input.jsx
│   │   │   ├── textarea.jsx
│   │   │   └── navigation-menu.jsx
│   │   ├── ContactForm.jsx          # Main form component for data submission
│   │   ├── ResultAnimation.jsx      # Animation for displaying results
│   │   └── SuccessModal.jsx         # Modal for showing analysis results
│   ├── lib/
│   │   └── utils.js                 # Utility functions and helpers
│   ├── App.jsx                      # Main application component with routing
│   ├── main.jsx                     # React DOM entry point
│   ├── App.css                      # Application-level styles
│   └── index.css                    # Global styles and Tailwind directives
├── .env.dev                         # Development environment variables
├── .env.prod                        # Production environment variables
├── index.html                       # HTML entry point
├── vite.config.js                   # Vite configuration
├── tailwind.config.js               # Tailwind CSS configuration
├── postcss.config.js                # PostCSS configuration
├── eslint.config.js                 # ESLint configuration
├── jsconfig.json                    # JavaScript configuration
├── package.json                     # Project dependencies and scripts
└── README.md                        # This file
```

### Key Component Descriptions

#### **Home.jsx**
Landing page introducing the Depression Detector project and its research objectives.

#### **DataUpload.jsx**
Primary interface for file-based analysis featuring:
- LLM provider selection dropdown
- Analysis methodology selection (8+ options)
- File upload dialog
- Integration with backend API

#### **ContactForm.jsx**
Main form component handling:
- Data collection and validation
- Model/prompt option management
- API communication
- Result callback handling

#### **SuccessModal.jsx**
Displays analysis results with:
- Depression classification (present/absent/uncertain)
- Detailed analysis messages
- Result animation effects
- Modal close functionality

---

## ⚙️ Configuration

### Tailwind CSS
Custom styling and animations are configured in `tailwind.config.js`:
- Color palette customization
- Animation definitions
- Component extensions
- Responsive breakpoints

### Vite Configuration
Path aliasing is set up in `vite.config.js`:
- `@` alias maps to `src/` directory
- Enables cleaner import statements: `import Component from '@/components/...'`

### ESLint
Code quality rules enforced via `.eslintrc.js`:
- React hooks rules
- React refresh rules
- General JavaScript best practices

### Environment Variables
Create `.env.local` to override default settings:
```
VITE_API_URL=http://custom-api-url:5000
```

---

## 🌐 Deployment

### Vercel Deployment (Recommended)

1. **Connect Repository**
   - Sign in to [Vercel](https://vercel.com)
   - Import the project from Git

2. **Configure Build Settings**
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Framework: Vite/React

3. **Set Environment Variables**
   - Add `VITE_API_URL` pointing to your production API

4. **Deploy**
   - Click Deploy to publish

### Manual Deployment

1. **Build Production Bundle**
   ```bash
   npm run build
   ```

2. **Upload `dist/` Folder**
   - Upload the contents of the `dist/` folder to your web server
   - Ensure proper routing configuration (single-page app)

3. **Configure Server**
   - Set up CORS headers if API is on different domain
   - Configure environment variables on server

### Vercel Configuration
The `vercel.json` file contains Vercel-specific deployment settings:
- Build configuration
- Environment variable setup
- Deployment routes

---

## 📖 Usage Guide

### Basic Workflow

1. **Navigate to Home Page**
   - Review project information
   - Understand research objectives

2. **Access Data Upload Section**
   - Click "Upload Data" in navigation
   - Choose analysis methodology from dropdown
   - Select LLM provider (Gemini, GPT, Ollama, etc.)

3. **Submit Analysis Request**
   - Upload a text file or enter text directly
   - Choose desired analysis method
   - Click "Analyze"

4. **View Results**
   - Success modal displays analysis results
   - Results include classification and detailed insights
   - Close modal to perform another analysis

### Analysis Methodologies

| Method | Best For | Description |
|--------|----------|-------------|
| **Simple** | Quick classification | Binary yes/no depression indicator |
| **Structured** | Detailed analysis | Checklist-based evaluation |
| **Feature Extraction** | Metrics & patterns | Identifies specific language metrics |
| **Chain-of-Thought** | Transparent reasoning | Step-by-step analysis logic |
| **Few-Shot** | Example-based | Learning from provided examples |
| **Free-Form** | Narrative insights | Narrative-style analysis |
| **Sentence-by-Sentence** | Granular analysis | Line-by-line breakdown |
| **Ollama Compare** | Model comparison | Compares multiple models |

---

## 🐛 Troubleshooting

### Common Issues and Solutions

#### Issue: Port 5173 Already in Use
```bash
# Find and kill process on port 5173
# Windows
netstat -ano | findstr :5173
taskkill /PID <PID> /F

# Then restart
npm run dev
```

#### Issue: API Connection Error
- Verify backend API is running on `http://localhost:5000`
- Check `.env.dev` has correct `VITE_API_URL`
- Check browser console for CORS errors
- Ensure API server has CORS enabled

#### Issue: Dependencies Not Installing
```bash
# Clear npm cache and reinstall
rm -r node_modules
npm cache clean --force
npm install
```

#### Issue: Hot Reload Not Working
```bash
# Restart development server
npm run dev

# Or clear Vite cache
rm -r node_modules/.vite
npm run dev
```

#### Issue: Build Fails
```bash
# Check for lint errors
npm run lint

# Fix fixable issues automatically
npx eslint . --fix

# Try building again
npm run build
```

#### Issue: Module Not Found
- Verify path aliases in `vite.config.js`
- Check that file extensions are included in imports (`.jsx`, `.js`, etc.)
- Ensure `@` alias resolves to `src/` directory correctly

### Getting Help

- Check browser console (F12) for error messages
- Review backend API logs for server-side issues
- Verify network requests in browser Network tab
- Check application state in React DevTools

---

## 🤝 Contributing

### Development Guidelines

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Follow Code Standards**
   - Run linter before committing: `npm run lint`
   - Use meaningful variable and function names
   - Add comments for complex logic
   - Keep components focused and reusable

3. **Component Best Practices**
   - Keep components small and single-responsibility
   - Use React hooks for state management
   - Implement proper error handling
   - Add PropTypes or TypeScript types

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: description of changes"
   ```

5. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Code Style

- **Naming**: Use camelCase for variables/functions, PascalCase for components
- **Formatting**: 2-space indentation, semicolons required
- **Comments**: Use JSDoc for complex functions
- **Imports**: Organize imports alphabetically, separate external/internal

---

## 📄 License

This project is part of the Depression Detector research initiative. For licensing information, refer to the main project repository.

---

## 📧 Support & Questions

For issues, questions, or feature requests:
1. Check existing documentation in the main project README
2. Review backend API documentation
3. Check application console logs for error details
4. Reach out to the research team

---

## 🔬 Research Context

This application serves as the frontend for a machine learning research project investigating depression detection through natural language analysis. The application enables researchers and educators to:

- Analyze student writings for potential depression indicators
- Compare different LLM approaches and prompting strategies
- Collect and analyze language patterns
- Contribute to mental health research in educational settings

For more information about the research methodology and backend implementation, refer to the main project documentation.

---

**Last Updated**: April 2026  
**Version**: 1.0.0  
**Status**: Production Ready
