from ..services.research import search_web


class WebResearchAgent:
    name = "web_research_agent"

    def research(self, query: str):
        return search_web(query)
