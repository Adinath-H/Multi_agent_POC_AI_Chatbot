from ..services.parsers import analyze_pptx, extract_pptx_text


class PPTAgent:
    name = "ppt_agent"

    def analyze(self, path: str):
        return analyze_pptx(path)

    def extract(self, path: str):
        return extract_pptx_text(path)
