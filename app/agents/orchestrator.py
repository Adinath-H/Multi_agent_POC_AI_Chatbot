import json
import re
from pathlib import Path

from ..db import add_artifact, add_trace, latest_artifact
from ..services.generators import clean_filename, generate_docx, generate_pptx
from ..services.llm import llm
from .document_agent import DocumentAgent
from .editing_agent import EditingAgent
from .ppt_agent import PPTAgent
from .rag_agent import RAGAgent
from .validation_agent import ValidationAgent
from .web_agent import WebResearchAgent


class Orchestrator:
    """Simple supervisor that decides which specialist agents to invoke."""

    def __init__(self):
        self.document_agent = DocumentAgent()
        self.ppt_agent = PPTAgent()
        self.web_agent = WebResearchAgent()
        self.rag_agent = RAGAgent()
        self.validator = ValidationAgent()
        self.editor = EditingAgent()

    def _plan(self, message: str) -> dict:
        text = message.lower()
        plan = {
            "research": any(w in text for w in ["latest", "current", "research", "web", "trends", "news"]),
            "rag": any(w in text for w in ["company", "enterprise", "internal", "knowledge", "policy"]),
            "docx": any(w in text for w in ["proposal", "report", "document", "docx"]),
            "pptx": any(w in text for w in ["presentation", "slides", "slide", "ppt", "powerpoint"]),
            "edit": any(w in text for w in ["edit", "add", "remove", "change", "update", "concise", "modify"]),
        }
        # A combined request should normally generate both artifacts.
        if "proposal and" in text and ("presentation" in text or "slides" in text):
            plan["docx"] = plan["pptx"] = True
        return plan

    def _context(self, session_id: str):
        files = []
        from ..config import UPLOAD_DIR
        folder = UPLOAD_DIR / session_id
        if folder.exists():
            files = [str(p) for p in folder.iterdir() if p.is_file()]
        analyses = []
        for path in files:
            try:
                if Path(path).suffix.lower() == ".pptx":
                    analysis = self.ppt_agent.analyze(path)
                else:
                    analysis = self.document_agent.analyze(path)
                analyses.append({"file": Path(path).name, "analysis": analysis})
            except Exception as exc:
                analyses.append({"file": Path(path).name, "error": str(exc)})
        return files, analyses

    def _research_query(self, message: str):
        cleaned = re.sub(r"\b(create|generate|prepare|make|write)\b", "", message, flags=re.I)
        return cleaned[:500]

    def _make_content(self, message: str, analyses, rag_results, web_results, kind: str):
        source_lines = []
        for item in web_results:
            if item.get("url"):
                source_lines.append(f"- {item.get('title', 'Web source')}: {item['url']}")
        for item in rag_results:
            source_lines.append(f"- Internal knowledge: {item['source']}")
        source_block = "\n".join(source_lines) or "- Internal assignment context"
        template_summary = json.dumps(analyses, indent=2)[:3000]
        rag_text = "\n\n".join(x["text"] for x in rag_results)[:2500]
        web_text = "\n\n".join(
            f"{x.get('title')}: {x.get('content')} ({x.get('url')})" for x in web_results
        )[:3000]

        if kind == "docx":
            prompt = f"""
Create a professional enterprise proposal from the user request below.
User request: {message}
Template analysis: {template_summary}
Enterprise knowledge retrieved from RAG:
{rag_text}
Web research:
{web_text}

Write clear, editable document content in markdown with:
# Title
## Executive Summary
## Business Context
## Key Findings
## Proposed Approach
## Implementation Roadmap
## Risks and Governance
## Conclusion
## Sources
Use concise business language. Use only facts supported by the supplied context for factual claims.
Sources to cite:
{source_block}
"""
        else:
            prompt = f"""
Create a professional enterprise slide deck from the user request below.
User request: {message}
Template analysis: {template_summary}
Enterprise knowledge retrieved from RAG:
{rag_text}
Web research:
{web_text}

Return 12 slides unless the user asks for another number.
Use exactly:
[SLIDE 1]
Title
- bullet
- bullet

Keep each slide concise with 3-5 bullets.
Slide 12 should be next steps.
Use only facts supported by the supplied context.
After the last slide, add a final slide named Sources if the requested slide count permits; otherwise include source URLs in speaker-friendly bullets on slide 12.
Sources to cite:
{source_block}
"""
        return llm.ask(prompt)

    def _template_for(self, files, kind):
        suffixes = {"docx": ".docx", "pptx": ".pptx"}
        for file in files:
            if file.lower().endswith(suffixes[kind]):
                return file
        return None

    def _handle_edit(self, session_id: str, message: str, files, analyses):
        results = []
        for kind in ("docx", "pptx"):
            art = latest_artifact(session_id, kind)
            if not art:
                continue
            context = json.dumps(analyses)[:5000]
            if kind == "docx":
                revised = self.editor.edit_document(art["content_text"], message, context)
                template = art.get("source_template") or self._template_for(files, kind)
                out_dir = Path(art["path"]).parent
                filename = clean_filename(f"proposal_v{int(art['version']) + 1}.docx")
                path = out_dir / filename
                generate_docx(revised, str(path), template)
            else:
                revised = self.editor.edit_presentation(art["content_text"], message, context)
                template = art.get("source_template") or self._template_for(files, kind)
                out_dir = Path(art["path"]).parent
                filename = clean_filename(f"presentation_v{int(art['version']) + 1}.pptx")
                path = out_dir / filename
                generate_pptx(revised, str(path), template)
            version = add_artifact(session_id, kind, filename, str(path), template, revised)
            validation = self.validator.validate_file(str(path), kind, revised)
            add_trace(session_id, self.editor.name, f"edited_{kind}_version_{version}", validation)
            results.append({"kind": kind, "filename": filename, "version": version, "validation": validation})
        return results

    def run(self, session_id: str, message: str):
        add_trace(session_id, "supervisor", "received_request", message)
        plan = self._plan(message)
        files, analyses = self._context(session_id)
        add_trace(session_id, "supervisor", "plan", plan)

        if plan["edit"]:
            edited = self._handle_edit(session_id, message, files, analyses)
            if edited:
                return {"answer": "The requested edit was applied as a new artifact version.", "artifacts": edited, "sources": [], "trace": plan}

        rag_results = self.rag_agent.retrieve(message, files) if plan["rag"] or files else []
        if rag_results:
            add_trace(session_id, self.rag_agent.name, "retrieval", [x["source"] for x in rag_results])
        web_results = self.web_agent.research(self._research_query(message)) if plan["research"] else []
        if web_results:
            add_trace(session_id, self.web_agent.name, "web_search", [x["url"] for x in web_results])

        artifacts = []
        out_dir = Path("data") / "generated" / session_id
        out_dir.mkdir(parents=True, exist_ok=True)
        response_parts = []

        if plan["docx"]:
            content = self._make_content(message, analyses, rag_results, web_results, "docx")
            template = self._template_for(files, "docx")
            path = out_dir / "proposal.docx"
            generate_docx(content, str(path), template)
            version = add_artifact(session_id, "docx", path.name, str(path), template, content)
            validation = self.validator.validate_file(str(path), "docx", content)
            add_trace(session_id, "document_generator", f"created_version_{version}", validation)
            artifacts.append({"kind": "docx", "filename": path.name, "version": version, "validation": validation})
            response_parts.append("Created an editable DOCX proposal.")

        if plan["pptx"]:
            content = self._make_content(message, analyses, rag_results, web_results, "pptx")
            template = self._template_for(files, "pptx")
            path = out_dir / "presentation.pptx"
            generate_pptx(content, str(path), template)
            version = add_artifact(session_id, "pptx", path.name, str(path), template, content)
            validation = self.validator.validate_file(str(path), "pptx", content)
            add_trace(session_id, "ppt_generator", f"created_version_{version}", validation)
            artifacts.append({"kind": "pptx", "filename": path.name, "version": version, "validation": validation})
            response_parts.append("Created an editable PPTX presentation.")

        if not artifacts:
            response_parts.append(
                "I understood the request but no artifact type was selected. Mention proposal/document, presentation/slides, or an edit command."
            )

        sources = []
        for item in web_results:
            if item.get("url"):
                sources.append({"title": item.get("title", "Web source"), "url": item["url"], "type": "web"})
        for item in rag_results:
            sources.append({"title": item["source"], "type": "enterprise_rag"})

        add_trace(session_id, "supervisor", "completed", {"artifacts": artifacts, "sources": sources})
        return {"answer": " ".join(response_parts), "artifacts": artifacts, "sources": sources, "trace": plan}


orchestrator = Orchestrator()
