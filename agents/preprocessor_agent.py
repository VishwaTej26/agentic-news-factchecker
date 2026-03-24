from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from config import OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE

llm = ChatOpenAI(
    model=LLM_MODEL,
    temperature=LLM_TEMPERATURE,
    openai_api_key=OPENAI_API_KEY
)

prompt = ChatPromptTemplate.from_template("""
You are a news analysis assistant. Given a news article, extract the following:

1. ENTITIES: List of people, organizations, locations mentioned
2. CLAIMS: List of specific falsifiable factual statements made in the article
3. ORIGIN: Is this likely AI-generated or human-written? (ai/human/unknown)

Article Title: {title}
Article Content: {content}

Respond in this exact format:
ENTITIES: entity1, entity2, entity3
CLAIMS: claim1 | claim2 | claim3
ORIGIN: human/ai/unknown
""")

def parse_response(text: str) -> dict:
    result = {"entities": [], "claims": [], "origin": "unknown"}
    for line in text.strip().split("\n"):
        if line.startswith("ENTITIES:"):
            result["entities"] = [e.strip() for e in line.replace("ENTITIES:", "").split(",") if e.strip()]
        elif line.startswith("CLAIMS:"):
            result["claims"] = [c.strip() for c in line.replace("CLAIMS:", "").split("|") if c.strip()]
        elif line.startswith("ORIGIN:"):
            result["origin"] = line.replace("ORIGIN:", "").strip().lower()
    return result

def preprocess_article(article: dict) -> dict:
    try:
        chain = prompt | llm
        response = chain.invoke({
            "title": article.get("title", ""),
            "content": article.get("content", "")[:2000]
        })
        parsed = parse_response(response.content)
        article.update(parsed)
        print(f"[Preprocessor] Processed: {article['title'][:60]}...")
    except Exception as e:
        print(f"[Preprocessor] Error: {e}")
        article.update({"entities": [], "claims": [], "origin": "unknown"})
    return article

def run_preprocessor(articles: list[dict]) -> list[dict]:
    print(f"[Preprocessor] Processing {len(articles)} articles...")
    return [preprocess_article(a) for a in articles]