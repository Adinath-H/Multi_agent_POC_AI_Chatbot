# Multi-Agent AI Chatbot for Document & PPT Generation

A simple Multi-Agent AI chatbot POC for analyzing documents and PowerPoint templates, using RAG and web research, and generating editable DOCX and PPTX files.

## Setup Instructions

### 1. Clone the project

```bash
git clone <repo-url>
cd poc-chatbot
```

### 2. Create virtual environment

For Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create `.env` file

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key       Link: https://console.groq.com/keys
GROQ_MODEL=openai/gpt-oss-20b
GROQ_VISION_MODEL=qwen/qwen3.6-27b
TAVILY_API_KEY=your_tavily_api_key   Link :https://app.tavily.com/home 
APP_SECRET=change-me
DATA_DIR=data
```

Replace:

```text
your_groq_api_key & your_tavily_api_key
```

with your actual API key's.

### 5. Run the application

```bash
uvicorn app.main:app --reload
```

Open the application in your browser:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# Usage Guidelines

### 1. Upload templates

Upload your sample:

```text
Company_Proposal_Template.docx
Company_Presentation_Template.pptx
```

The system analyzes the uploaded files before generating new content.

### 2. Enter a request

Example:

```text
Research the latest Generative AI trends and create a proposal and 12-slide presentation using the uploaded templates.
```

### 3. Generate files

The system processes the request using:

```text
Orchestrator
    ↓
Document/PPT Analysis
    ↓
RAG + Web Research
    ↓
Groq LLM
    ↓
DOCX / PPTX Generation
```

The generated files are editable.

### 4. Edit using chat

You can give additional instructions such as:

```text
Add an executive summary.
```

```text
Add a competitive analysis section.
```

```text
Make the presentation more concise.
```

```text
Update the report using the latest web information.
```

### 5. RAG Knowledge

Place enterprise knowledge files inside:

```text
data/knowledge/
```

Example:

```text
data/knowledge/company_knowledge.txt
```

The system can use this information while generating the response.

## Notes

* Keep your `.env` file private.
* Do not upload API keys to GitHub.
* A valid `GROQ_API_KEY` is required for Groq-based generation.
* `TAVILY_API_KEY` is used for web research.
