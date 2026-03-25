import chromadb
import json
import hashlib
from datetime import datetime
from chromadb.utils import embedding_functions
from config import CHROMA_DB_PATH, COLLECTION_NAME, OPENAI_API_KEY

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-3-small"
)

client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=openai_ef
)

def store_article(article: dict):
    try:
        verdict_summary = ""
        for v in article.get("verdicts", []):
            verdict_summary += f"CLAIM: {v.get('claim','')} | VERDICT: {v.get('verdict','')} | CONFIDENCE: {v.get('confidence',0)} | REASONING: {v.get('reasoning','')} "

        doc_text = f"{article.get('title', '')} {article.get('content', '')[:300]} {verdict_summary}"

        metadata = {
            "title": article.get("title", "")[:100],
            "source": article.get("source", "unknown"),
            "topic": article.get("topic", "general"),
            "origin": article.get("origin", "unknown"),
            "published_at": article.get("published_at", ""),
            "ingested_at": article.get("ingested_at", datetime.utcnow().isoformat()),
            "verdict_count": len(article.get("verdicts", [])),
            "main_verdict": article.get("verdicts", [{}])[0].get("verdict", "unverified") if article.get("verdicts") else "unverified",
            "main_confidence": str(article.get("verdicts", [{}])[0].get("confidence", 0.0)) if article.get("verdicts") else "0.0",
        }
        collection.upsert(
            documents=[doc_text],
            metadatas=[metadata],
            ids=[article.get("hash", hashlib.md5(doc_text[:50].encode()).hexdigest())]
        )
        print(f"[Memory] Stored: {article.get('title','')[:60]}")
    except Exception as e:
        print(f"[Memory] Store error: {e}")

def search_similar(query: str, n_results: int = 5) -> list[dict]:
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        return results
    except Exception as e:
        print(f"[Memory] Search error: {e}")
        return []

def get_past_verdict(claim: str) -> dict | None:
    try:
        results = collection.query(
            query_texts=[claim],
            n_results=1
        )
        if results and results["distances"][0]:
            distance = results["distances"][0][0]
            if distance < 0.15:
                return results["metadatas"][0][0]
    except Exception as e:
        print(f"[Memory] Verdict lookup error: {e}")
    return None

def run_memory_storage(articles: list[dict]):
    print(f"[Memory] Storing {len(articles)} articles...")
    for article in articles:
        store_article(article)
    print(f"[Memory] Storage complete. Total docs: {collection.count()}")