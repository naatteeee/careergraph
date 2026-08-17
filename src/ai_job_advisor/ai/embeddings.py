
from __future__ import annotations

import hashlib
import re
from typing import Protocol, Sequence, runtime_checkable

import numpy as np

from ..config import Settings, get_settings

_TOKEN_RE = re.compile(r"[a-z0-9+#.]+")


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Anything that can turn text into fixed-size float vectors."""

    dim: int

    def embed(self, texts: Sequence[str]) -> np.ndarray:  # pragma: no cover - protocol
        """Return an array of shape ``(len(texts), dim)``."""
        ...


def _normalise(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


class HashingEmbeddingProvider:
    """Deterministic bag-of-tokens hashing embedding.

    Not as expressive as a neural encoder, but fully offline, dependency-free,
    deterministic and good enough to exercise the full pipeline and tests.
    """

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def _embed_one(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        tokens = _TOKEN_RE.findall(text.lower())
        for token in tokens:
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
            vec[idx] += sign
        return vec

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        matrix = np.vstack([self._embed_one(t) for t in texts]) if texts else np.zeros((0, self.dim), dtype=np.float32)
        return _normalise(matrix)


class LocalSentenceTransformerProvider:
    """Wraps a local Sentence-Transformers model (lazy-loaded)."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer  # lazy import

        self._model = SentenceTransformer(model_name)
        self.dim = int(self._model.get_sentence_embedding_dimension())

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        vectors = self._model.encode(list(texts), normalize_embeddings=True, convert_to_numpy=True)
        return vectors.astype(np.float32)


class OpenAICompatibleProvider:
    """Calls any OpenAI-compatible ``/embeddings`` endpoint via HTTP."""

    def __init__(self, base_url: str, api_key: str, model: str, dim: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.dim = dim

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        import requests  # lazy import

        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        resp = requests.post(
            f"{self.base_url}/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"model": self.model, "input": list(texts)},
            timeout=60,
        )
        resp.raise_for_status()
        data = sorted(resp.json()["data"], key=lambda d: d["index"])
        matrix = np.array([d["embedding"] for d in data], dtype=np.float32)
        self.dim = matrix.shape[1]
        return _normalise(matrix)


def get_embedding_provider(settings: Settings | None = None) -> EmbeddingProvider:
    """Factory selecting an embedding provider from configuration."""
    settings = settings or get_settings()
    backend = settings.embedding_backend.lower()
    if backend == "local":
        return LocalSentenceTransformerProvider(settings.st_model_name)
    if backend == "openai":
        return OpenAICompatibleProvider(
            settings.openai_base_url,
            settings.openai_api_key,
            settings.openai_embedding_model,
            settings.embedding_dim,
        )
    return HashingEmbeddingProvider(settings.embedding_dim)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Cosine similarity between rows of ``a`` and rows of ``b``.

    Returns a matrix of shape ``(len(a), len(b))``. Assumes inputs are not
    necessarily normalised.
    """
    a = np.atleast_2d(a)
    b = np.atleast_2d(b)
    return _normalise(a) @ _normalise(b).T
