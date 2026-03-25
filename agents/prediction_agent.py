from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from agents.entity_tracker_agent import load_entities
from agents.memory_agent import search_similar
from config import OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE
from datetime import datetime

llm = ChatOpenAI(
    model=LLM_MODEL,
    temperature=0.3,
    openai_api_key=OPENAI_API_KEY
)

prompt = ChatPromptTemplate.from_template("""
You are a news analyst. Based on recent articles and entity history provided,
generate 3 falsifiable predictions about how these stories might develop.

Recent context:
{context}

Top entities in the news:
{entities}

For each prediction respond in this exact format:
PREDICTION: specific falsifiable statement
CONFIDENCE: 0.0 to 1.0
TIMEFRAME: e.g. within 1 week, within 1 month
---
""")

def get_top_entities(n: int = 5) -> str:
    entities = load_entities()
    sorted_entities = sorted(
        entities.values(),
        key=lambda x: x["mention_count"],
        reverse=True
    )[:n]
    return "\n".join([
        f"- {e['name']}: {e['mention_count']} mentions, "
        f"credibility {e['credibility_score']}"
        for e in sorted_entities
    ])

def parse_predictions(text: str) -> list[dict]:
    predictions = []
    blocks = text.strip().split("---")
    for block in blocks:
        if not block.strip():
            continue
        pred = {"prediction": "", "confidence": 0.0, "timeframe": "unknown"}
        for line in block.strip().split("\n"):
            if line.startswith("PREDICTION:"):
                pred["prediction"] = line.replace("PREDICTION:", "").strip()
            elif line.startswith("CONFIDENCE:"):
                try:
                    pred["confidence"] = float(line.replace("CONFIDENCE:", "").strip())
                except:
                    pred["confidence"] = 0.0
            elif line.startswith("TIMEFRAME:"):
                pred["timeframe"] = line.replace("TIMEFRAME:", "").strip()
        if pred["prediction"]:
            predictions.append(pred)
    return predictions

def run_prediction_agent(articles: list[dict]) -> list[dict]:
    print("[Prediction] Generating predictions...")
    context = "\n".join([
        f"- {a.get('title', '')} ({a.get('source', '')})"
        for a in articles[:10]
    ])
    entities = get_top_entities()
    try:
        chain = prompt | llm
        response = chain.invoke({
            "context": context,
            "entities": entities
        })
        predictions = parse_predictions(response.content)
        print(f"[Prediction] Generated {len(predictions)} predictions")
        # save predictions
        import json, os
        from config import DATA_PATH
        os.makedirs(DATA_PATH, exist_ok=True)
        path = f"{DATA_PATH}/predictions.json"
        existing = []
        if os.path.exists(path):
            with open(path) as f:
                existing = json.load(f)
        existing.append({
            "generated_at": datetime.utcnow().isoformat(),
            "predictions": predictions
        })
        with open(path, "w") as f:
            json.dump(existing, f, indent=2)
        return predictions
    except Exception as e:
        print(f"[Prediction] Error: {e}")
        return []