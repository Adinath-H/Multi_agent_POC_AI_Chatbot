from pathlib import Path

from ..services.parsers import analyze_file, extract_text


class DocumentAgent:
    name = "document_agent"

    def analyze(self, path: str):
        return analyze_file(path)

    def extract(self, path: str):
        return extract_text(path)
