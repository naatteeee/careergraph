from ai_job_advisor.ai.skill_extraction import SkillExtractor, get_default_extractor


def test_extract_basic(extractor):
    text = "We need Python, SQL and machine learning. PyTorch is a plus."
    skills = extractor.extract(text)
    assert "python" in skills
    assert "sql" in skills
    assert "machine learning" in skills
    assert "pytorch" in skills


def test_normalize_aliases(extractor):
    assert extractor.normalize("JS") == "javascript"
    assert extractor.normalize("Postgres") == "postgresql"
    assert extractor.normalize("k8s") == "kubernetes"
    assert extractor.normalize("totally-unknown-skill") is None


def test_longest_alias_wins(extractor):
    # "data analysis" must not be shadowed by a shorter token.
    skills = extractor.extract("strong data analysis experience")
    assert "data analysis" in skills


def test_no_partial_word_match(extractor):
    # "java" must not match inside "javascript".
    skills = extractor.extract("we use javascript heavily")
    assert "javascript" in skills
    assert "java" not in skills


def test_extract_many_counts(extractor):
    texts = ["python and sql", "python only", "sql and excel"]
    counter = extractor.extract_many(texts)
    assert counter["python"] == 2
    assert counter["sql"] == 2
    assert counter["excel"] == 1


def test_empty_text(extractor):
    assert extractor.extract("") == []


def test_custom_taxonomy():
    ex = SkillExtractor(taxonomy={"rust": ["rust", "rustlang"]})
    assert ex.extract("we love rustlang") == ["rust"]
