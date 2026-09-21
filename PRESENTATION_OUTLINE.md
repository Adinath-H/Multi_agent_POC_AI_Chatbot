# Presentation Outline – Multi-Agent Document & PPT AI POC

## Slide 1 – Project Overview
**Multi-Agent AI Chatbot for Document & PPT Generation**
- Enterprise document automation POC
- FastAPI + Groq + RAG + web research

## Slide 2 – Assignment Requirements
- Multi-agent orchestration
- Document/PPT template analysis
- Web research + enterprise RAG
- Editable DOCX/PPTX
- Conversational editing, citations and versioning

## Slide 3 – Architecture
Browser UI -> FastAPI -> Supervisor/Orchestrator -> specialized agents -> artifact generation -> validation/versioning

## Slide 4 – Agents
- Supervisor/Orchestrator
- Document Agent
- PPT Agent
- Web Research Agent
- RAG Agent
- Editing Agent
- Validation Agent

## Slide 5 – Groq LLM Layer
- Groq Python SDK
- `GROQ_API_KEY` from `.env`
- Text model: `openai/gpt-oss-20b`
- Optional vision model: `qwen/qwen3.6-27b`

## Slide 6 – Template Analysis
- DOCX: headings, paragraphs, styles
- PPTX: slide titles, layouts, theme information
- PDF/images: text extraction + OCR fallback

## Slide 7 – Enterprise RAG
- Knowledge files in `data/knowledge/`
- Chunking
- Local vector search
- Source snippets returned for traceability

## Slide 8 – Web Research
- Tavily integration
- Latest external information
- Source URLs preserved in trace data

## Slide 9 – Generation
- Editable DOCX with python-docx
- Editable PPTX with python-pptx
- Template structure/style used as generation context

## Slide 10 – Conversational Editing
Example:
- Add an executive summary
- Make the presentation more concise
- Add competitive analysis
- Update using latest information

## Slide 11 – Validation + Versioning
- File existence and size validation
- SQLite artifact history
- Trace log for each agent/action

## Slide 12 – Demo + Future Scope
- Upload templates
- Research + RAG
- Generate files
- Edit through chat
- Future: stronger pixel-level template cloning, auth, cloud vector DB, deployment
