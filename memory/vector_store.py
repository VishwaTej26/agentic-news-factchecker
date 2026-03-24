from agents.memory_agent import (
    store_article,
    search_similar,
    get_past_verdict,
    collection
)

def get_collection_stats() -> dict:
    return {
        "total_documents": collection.count(),
        "collection_name": collection.name
    }