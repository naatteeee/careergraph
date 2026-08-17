import numpy as np

from ai_job_advisor.ai.embeddings import (
    HashingEmbeddingProvider,
    cosine_similarity,
    get_embedding_provider,
)
from ai_job_advisor.config import Settings


def test_hashing_shape_and_determinism():
    p = HashingEmbeddingProvider(dim=64)
    a = p.embed(["python developer", "data scientist"])
    b = p.embed(["python developer", "data scientist"])
    assert a.shape == (2, 64)
    assert np.allclose(a, b)  # deterministic


def test_hashing_normalised():
    p = HashingEmbeddingProvider(dim=64)
    v = p.embed(["machine learning engineer"])
    assert abs(np.linalg.norm(v[0]) - 1.0) < 1e-5


def test_empty_input():
    p = HashingEmbeddingProvider(dim=32)
    out = p.embed([])
    assert out.shape == (0, 32)


def test_similar_text_more_similar():
    p = HashingEmbeddingProvider(dim=512)
    vecs = p.embed([
        "python machine learning data science",
        "python machine learning data analysis",
        "marketing sales communication",
    ])
    sim = cosine_similarity(vecs, vecs)
    # row 0 closer to row 1 than to row 2
    assert sim[0, 1] > sim[0, 2]


def test_cosine_range():
    p = HashingEmbeddingProvider(dim=128)
    vecs = p.embed(["abc def", "abc def"])
    sim = cosine_similarity(vecs, vecs)
    assert sim[0, 1] == 1.0 or abs(sim[0, 1] - 1.0) < 1e-5


def test_factory_defaults_to_hashing():
    provider = get_embedding_provider(Settings(embedding_backend="hashing", embedding_dim=256))
    assert isinstance(provider, HashingEmbeddingProvider)
    assert provider.dim == 256
