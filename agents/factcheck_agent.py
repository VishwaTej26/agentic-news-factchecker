from tavily import TavilyClient
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from config import OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE, TAVILY_API_KEY

llm = ChatOpenAI(
    model=LLM_MODEL,
    temperature=LLM_TEMPERATURE,
    openai_api_key=OPENAI_API_KEY
)

tavily = TavilyClient(api_key=TAVILY_API_KEY)

prompt = ChatPromptTemplate.from_template("""
You are a professional fact-checker. Given a claim and evidence from multiple sources,
produce a verdict.

Claim: {claim}

Evidence:
{evidence}

Respond in this exact format:
VERDICT: true/false/unverified
CONFIDENCE: 0.0 to 1.0
REASONING: one or two sentence explanation
""")

def is_valid_claim(claim: str) -> bool:
    if not claim or len(claim.strip()) < 10:
        return False
    skip_phrases = [
        "none", "none identified", "a required part",
        "browser extension", "check your connection",
        "disable any ad blockers"
    ]
    claim_lower = claim.lower().strip()
    return not any(phrase in claim_lower for phrase in skip_phrases)

def search_evidence(claim: str) -> list[dict]:
    sources = []
    try:
        results = tavily.search(
            query=claim,
            search_depth="basic",
            max_results=5
        )
        for r in results.get("results", []):
            sources.append({
                "source": r.get("url", "unknown"),
                "text": r.get("content", "")[:300],
                "url": r.get("url", "")
            })
    except Exception as e:
        print(f"[FactCheck] Search error: {e}")
    return sources

def format_evidence(sources: list[dict]) -> str:
    if not sources:
        return "No external evidence found."
    return "\n".join([
        f"Source {i+1} ({s['source']}): {s['text']}"
        for i, s in enumerate(sources)
    ])

def parse_verdict(text: str) -> dict:
    result = {"verdict": "unverified", "confidence": 0.0, "reasoning": ""}
    for line in text.strip().split("\n"):
        if line.startswith("VERDICT:"):
            result["verdict"] = line.replace("VERDICT:", "").strip().lower()
        elif line.startswith("CONFIDENCE:"):
            try:
                result["confidence"] = float(line.replace("CONFIDENCE:", "").strip())
            except:
                result["confidence"] = 0.0
        elif line.startswith("REASONING:"):
            result["reasoning"] = line.replace("REASONING:", "").strip()
    return result

def factcheck_claim(claim: str) -> dict:
    print(f"[FactCheck] Checking: {claim[:80]}...")
    sources = search_evidence(claim)
    evidence_text = format_evidence(sources)
    try:
        chain = prompt | llm
        response = chain.invoke({
            "claim": claim,
            "evidence": evidence_text
        })
        result = parse_verdict(response.content)
        result["claim"] = claim
        result["sources"] = sources
        return result
    except Exception as e:
        print(f"[FactCheck] LLM error: {e}")
        return {
            "claim": claim,
            "verdict": "unverified",
            "confidence": 0.0,
            "reasoning": f"Error during fact-checking: {e}",
            "sources": sources
        }

def run_factcheck(articles: list[dict]) -> list[dict]:
    print(f"[FactCheck] Starting fact-check run...")
    for article in articles:
        claims = article.get("claims", [])
        verdicts = []
        for claim in claims[:3]:
            if not is_valid_claim(claim):
                continue
            verdict = factcheck_claim(claim)
            verdicts.append(verdict)
        article["verdicts"] = verdicts
    return articles