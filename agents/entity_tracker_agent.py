import json
import os
from datetime import datetime
from config import DATA_PATH

ENTITIES_FILE = f"{DATA_PATH}/entities.json"

def load_entities() -> dict:
    if os.path.exists(ENTITIES_FILE):
        with open(ENTITIES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_entities(entities: dict):
    os.makedirs(DATA_PATH, exist_ok=True)
    with open(ENTITIES_FILE, "w") as f:
        json.dump(entities, f, indent=2)

def update_entity(entities: dict, name: str, article: dict) -> dict:
    if name not in entities:
        entities[name] = {
            "name": name,
            "mention_count": 0,
            "articles": [],
            "verdicts": {"true": 0, "false": 0, "unverified": 0},
            "credibility_score": 0.5,
            "first_seen": datetime.utcnow().isoformat(),
            "last_seen": datetime.utcnow().isoformat(),
        }
    entity = entities[name]
    entity["mention_count"] += 1
    entity["last_seen"] = datetime.utcnow().isoformat()
    entity["articles"].append({
        "title": article.get("title", "")[:100],
        "url": article.get("url", ""),
        "source": article.get("source", ""),
        "published_at": article.get("published_at", "")
    })
    # update verdict counts
    for verdict in article.get("verdicts", []):
        v = verdict.get("verdict", "unverified")
        if v in entity["verdicts"]:
            entity["verdicts"][v] += 1
    # recalculate credibility score
    total = sum(entity["verdicts"].values())
    if total > 0:
        entity["credibility_score"] = round(
            entity["verdicts"]["true"] / total, 2
        )
    return entities

def run_entity_tracker(articles: list[dict]):
    print("[EntityTracker] Updating entity profiles...")
    entities = load_entities()
    for article in articles:
        for entity_name in article.get("entities", []):
            entities = update_entity(entities, entity_name, article)
    save_entities(entities)
    print(f"[EntityTracker] Tracking {len(entities)} entities")
    return entities