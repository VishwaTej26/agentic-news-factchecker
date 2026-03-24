from agents.scraper_agent import deduplicate, get_article_hash
from agents.preprocessor_agent import parse_response
from agents.factcheck_agent import parse_verdict, format_evidence

def test_deduplication():
    articles = [
        {"title": "Test", "hash": "abc"},
        {"title": "Test", "hash": "abc"},
        {"title": "Other", "hash": "xyz"},
    ]
    result = deduplicate(articles)
    assert len(result) == 2

def test_article_hash():
    h1 = get_article_hash("Same title")
    h2 = get_article_hash("Same title")
    h3 = get_article_hash("Different title")
    assert h1 == h2
    assert h1 != h3

def test_parse_response():
    text = """ENTITIES: OpenAI, Elon Musk, Twitter
CLAIMS: OpenAI released GPT-5 | Elon Musk bought Twitter for 44 billion
ORIGIN: human"""
    result = parse_response(text)
    assert len(result["entities"]) == 3
    assert len(result["claims"]) == 2
    assert result["origin"] == "human"

def test_parse_verdict():
    text = """VERDICT: true
CONFIDENCE: 0.85
REASONING: Multiple sources confirm this claim."""
    result = parse_verdict(text)
    assert result["verdict"] == "true"
    assert result["confidence"] == 0.85
    assert "sources" in result["reasoning"].lower()

def test_format_evidence_empty():
    result = format_evidence([])
    assert "No external evidence" in result

def test_format_evidence_with_sources():
    sources = [
        {"source": "BBC", "text": "Some news text", "url": "https://bbc.com"}
    ]
    result = format_evidence(sources)
    assert "BBC" in result
    assert "Some news text" in result