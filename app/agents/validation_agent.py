from pathlib import Path
from zipfile import ZipFile

from docx import Document
from pptx import Presentation


class ValidationAgent:
    name = "validation_agent"

    def validate_file(self, path: str, kind: str, content: str = ""):
        p = Path(path)
        checks = {
            "exists": p.exists(),
            "non_empty": p.exists() and p.stat().st_size > 100,
        }
        details = []
        if p.exists():
            try:
                if kind == "docx":
                    Document(str(p))
                    checks["opens"] = True
                elif kind == "pptx":
                    Presentation(str(p))
                    checks["opens"] = True
                elif p.suffix.lower() in {".docx", ".pptx"}:
                    with ZipFile(p):
                        checks["opens"] = True
            except Exception as exc:
                checks["opens"] = False
                details.append(str(exc))
        if content:
            checks["has_content"] = len(content.split()) >= 20
            if "source" not in content.lower() and "citation" not in content.lower():
                details.append("No obvious citation/source section found.")
        return {
            "passed": all(v for v in checks.values() if isinstance(v, bool)),
            "checks": checks,
            "details": details,
        }
