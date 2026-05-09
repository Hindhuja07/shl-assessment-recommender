import re
from functools import lru_cache
from typing import Dict, List, Tuple

import numpy as np

from app.catalog_loader import load_catalog

try:
    import faiss
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover
    faiss = None
    SentenceTransformer = None


WORD_RE = re.compile(r"[a-zA-Z0-9+#.]+")


def normalize(text: str) -> str:
    return " ".join(WORD_RE.findall(text.lower()))


def assessment_text(item: Dict) -> str:
    parts = [
        item.get("name", ""),
        item.get("description", ""),
        item.get("test_type", ""),
        " ".join(item.get("keywords", []) or []),
    ]
    return " ".join(str(p) for p in parts if p)


class Retriever:
    def __init__(self) -> None:
        self.catalog = load_catalog()
        self.model = None
        self.index = None
        self.embeddings = None

        if SentenceTransformer and faiss:
            try:
                self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
                docs = [assessment_text(item) for item in self.catalog]
                vectors = self.model.encode(docs, normalize_embeddings=True).astype("float32")

                self.embeddings = vectors
                self.index = faiss.IndexFlatIP(vectors.shape[1])
                self.index.add(vectors)
            except Exception:
                self.model = None
                self.index = None

    def keyword_score(self, query: str, item: Dict) -> float:
        q_terms = set(normalize(query).split())
        doc = normalize(assessment_text(item))
        name = normalize(item.get("name", ""))

        score = 0.0

        for term in q_terms:
            if len(term) < 2:
                continue

            if term in doc:
                score += 1.0

            if term in name:
                score += 3.0

        skill_boosts = {
            "java": ["java"],
            "python": ["python"],
            "sql": ["sql"],
            "javascript": ["javascript", "java script"],
            "c++": ["c++", "cpp"],
            "excel": ["excel"],
        }

        for skill, variants in skill_boosts.items():
            if skill in q_terms:
                for variant in variants:
                    if variant in name:
                        score += 20.0
                    elif variant in doc:
                        score += 8.0

        # If the user clearly asks for Java, keep Java tests on top.
        # JavaScript contains the word "java", so it needs a specific penalty.
        if "java" in q_terms:
            unrelated = [
                "python",
                "sql",
                "javascript",
                "java script",
                "c++",
                "cpp",
                "c#",
                ".net",
            ]

            for word in unrelated:
                if word in name:
                    score -= 15.0

            if "java 8" in name or name == "java":
                score += 25.0
            elif "java" in name and "javascript" not in name:
                score += 15.0

        return score

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        scored: List[Tuple[float, Dict]] = []

        if self.model is not None and self.index is not None:
            q_vec = self.model.encode([query], normalize_embeddings=True).astype("float32")
            distances, indices = self.index.search(
                q_vec,
                min(max(limit * 3, 10), len(self.catalog)),
            )

            seen = set()

            for distance, idx in zip(distances[0], indices[0]):
                if idx < 0:
                    continue

                item = self.catalog[int(idx)]
                key = item.get("url") or item.get("name")

                if key in seen:
                    continue

                seen.add(key)
                score = float(distance) * 5 + self.keyword_score(query, item)
                scored.append((score, item))
        else:
            for item in self.catalog:
                scored.append((self.keyword_score(query, item), item))

        scored.sort(key=lambda pair: pair[0], reverse=True)

        return [
            item
            for score, item in scored[:limit]
            if score > 0 or len(scored) <= limit
        ]

    def find_by_name(self, name: str) -> Dict | None:
        target = normalize(name)

        for item in self.catalog:
            if normalize(item.get("name", "")) == target:
                return item

        for item in self.catalog:
            if target and target in normalize(item.get("name", "")):
                return item

        return None


@lru_cache(maxsize=1)
def get_retriever() -> Retriever:
    return Retriever()