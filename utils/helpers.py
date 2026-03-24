import json
import os
from datetime import datetime
from config import DATA_PATH

def save_json(data, filename: str):
    os.makedirs(DATA_PATH, exist_ok=True)
    path = f"{DATA_PATH}/{filename}"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[Helpers] Saved to {path}")

def load_json(filename: str) -> dict | list:
    path = f"{DATA_PATH}/{filename}"
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def format_verdict_emoji(verdict: str) -> str:
    return {"true": "✅", "false": "❌", "unverified": "⚠️"}.get(verdict, "⚠️")

def format_confidence_bar(confidence: float) -> str:
    filled = int(confidence * 10)
    return "█" * filled + "░" * (10 - filled) + f" {int(confidence*100)}%"

def get_latest_run() -> dict:
    return load_json("latest_run.json")

def get_predictions() -> list:
    data = load_json("predictions.json")
    if isinstance(data, list) and data:
        return data[-1].get("predictions", [])
    return []