import requests
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from config import OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE, MIN_SOURCES_FOR_VERDICT

llm = ChatOpenAI(
    model=LLM_MODEL,
    temperature=LLM_TEMPERATURE,
    openai_api_key=OPENAI_API_KEY
)

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

def search_evidence(claim: str) -> list[dict]:
    sources = []
    try:
        url = f"https://api.search.brave.com/res/v1/web/search?q={claim}&count=5"
        # fallback to duckduckgo instant answer
        ddg_url = f"https://api.duckduckgo.com/?q={claim}&format=json&no_html=1"
        response = requests.get(ddg_url, timeout=10)
        data = response.json()
        if data.get("AbstractText"):
            sources.append({
                "source": data.get("AbstractSource", "DuckDuckGo"),
                "text": data.get("AbstractText", ""),
                "url": data.get("AbstractURL", "")
            })
        if data.get("RelatedTopics"):
            for topic in data["RelatedTopics"][:3]:
                if isinstance(topic, dict) and topic.get("Text"):
                    sources.append({
                        "source": "DuckDuckGo Related",
                        "text": topic.get("Text", ""),
                        "url": topic.get("FirstURL", "")
                    })
    except Exception as e:
        print(f"[FactCheck] Search error: {e}")
    return sources

def format_evidence(sources: list[dict]) -> str:
    if not sources:
        return "No external evidence found."
    return "\n".join([
        f"Source {i+1} ({s['source']}): {s['text'][:300]}"
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
        for claim in claims[:3]:  # max 3 claims per article to save API cost
            verdict = factcheck_claim(claim)
            verdicts.append(verdict)
        article["verdicts"] = verdicts
    return articles