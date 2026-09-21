from ..services.rag import rag


class RAGAgent:
    name = "rag_agent"

    def retrieve(self, query: str, uploaded_files: list[str] | None = None):
        rag.build(uploaded_files or [])
        return rag.search(query, k=5)
