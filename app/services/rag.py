from pathlib import Path
import json
import re
import hashlib

import numpy as np

try:
    import faiss
except ImportError:
    faiss = None

from ..config import KNOWLEDGE_DIR
from .parsers import extract_text


class SimpleHashVectorizer:
    def __init__(self, n_features=384):
        self.n_features = n_features

    def transform(self, texts):
        matrix = np.zeros((len(texts), self.n_features), dtype=np.float32)
        for row, text in enumerate(texts):
            tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
            for token in tokens:
                idx = int(hashlib.md5(token.encode()).hexdigest(), 16) % self.n_features
                matrix[row, idx] += 1.0
            norm = np.linalg.norm(matrix[row])
            if norm:
                matrix[row] /= norm
        return matrix


class LocalRAG:
    """Small local vector store for the POC.

    Uses FAISS when installed and falls back to NumPy cosine similarity.
    This keeps the assignment runnable on machines where FAISS is unavailable.
    A production deployment can replace this class with Pinecone.
    """

    def __init__(self):
        self.vectorizer = SimpleHashVectorizer(384)
        self.texts = []
        self.meta = []
        self.matrix = np.zeros((0, 384), dtype=np.float32)
        self.index = faiss.IndexFlatIP(384) if faiss else None

    def build(self, extra_files=None):
        files = list(KNOWLEDGE_DIR.glob("*"))
        for item in extra_files or []:
            files.append(Path(item))
        seen = set()
        self.texts.clear()
        self.meta.clear()
        chunks = []
        for path in files:
            path = Path(path)
            if not path.is_file() or str(path.resolve()) in seen:
                continue
            seen.add(str(path.resolve()))
            try:
                text = extract_text(path)
            except Exception:
                continue
            if not text.strip():
                continue
            words = text.split()
            for start in range(0, len(words), 180):
                chunk = " ".join(words[start:start + 180])
                if chunk.strip():
                    chunks.append(chunk)
                    self.texts.append(chunk)
                    self.meta.append({"source": path.name})
        self.matrix = self.vectorizer.transform(chunks) if chunks else np.zeros((0, 384), dtype=np.float32)
        if faiss:
            self.index = faiss.IndexFlatIP(384)
            if len(self.matrix):
                self.index.add(self.matrix)

    def search(self, query, k=5):
        if not self.texts:
            self.build()
        if not self.texts:
            return []
        q = self.vectorizer.transform([query])[0]
        if faiss and self.index is not None:
            scores, ids = self.index.search(q.reshape(1, -1), min(k, len(self.texts)))
            pairs = zip(scores[0], ids[0])
        else:
            scores = self.matrix @ q
            top = np.argsort(scores)[::-1][:min(k, len(self.texts))]
            pairs = ((float(scores[i]), int(i)) for i in top)
        result = []
        for score, idx in pairs:
            if idx < 0:
                continue
            result.append({"score": float(score), "text": self.texts[idx], "source": self.meta[idx]["source"]})
        return result

    def save_metadata(self, path):
        Path(path).write_text(json.dumps(self.meta, indent=2), encoding="utf-8")


rag = LocalRAG()
