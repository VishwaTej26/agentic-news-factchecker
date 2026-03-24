from agents.scraper_agent import run_scraper
from agents.preprocessor_agent import run_preprocessor
from agents.factcheck_agent import run_factcheck
from agents.memory_agent import run_memory_storage
from agents.entity_tracker_agent import run_entity_tracker
from agents.prediction_agent import run_prediction_agent
from memory.knowledge_graph import update_graph
import json
import os
from datetime import datetime
from config import DATA_PATH

def run_pipeline():
    print("\n" + "="*50)
    print("AGENTIC NEWS FACT-CHECKER PIPELINE")
    print(f"Started at: {datetime.utcnow().isoformat()}")
    print("="*50 + "\n")

    # Step 1: Scrape
    articles = run_scraper()

    # Step 2: Preprocess
    articles = run_preprocessor(articles)

    # Step 3: Fact-check
    articles = run_factcheck(articles)

    # Step 4: Store in memory
    run_memory_storage(articles)

    # Step 5: Update entity tracker
    run_entity_tracker(articles)

    # Step 6: Update knowledge graph
    update_graph(articles)

    # Step 7: Generate predictions
    predictions = run_prediction_agent(articles)

    # Save full run output
    os.makedirs(DATA_PATH, exist_ok=True)
    output_path = f"{DATA_PATH}/latest_run.json"
    with open(output_path, "w") as f:
        json.dump({
            "run_at": datetime.utcnow().isoformat(),
            "articles_processed": len(articles),
            "predictions": predictions,
            "articles": articles
        }, f, indent=2)

    print("\n" + "="*50)
    print(f"Pipeline complete. {len(articles)} articles processed.")
    print(f"Output saved to {output_path}")
    print("="*50 + "\n")
    return articles, predictions

if __name__ == "__main__":
    run_pipeline()