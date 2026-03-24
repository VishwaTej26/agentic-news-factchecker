import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# LLM Settings
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.0
MAX_TOKENS = 1000

# News Settings
NEWS_TOPICS = ["technology", "geopolitics", "ai"]
MAX_ARTICLES_PER_RUN = 20
NEWS_LANGUAGE = "en"

# Memory Settings
CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "news_facts"

# Fact Check Settings
MIN_SOURCES_FOR_VERDICT = 2
CONFIDENCE_THRESHOLD = 0.6

# Paths
DATA_PATH = "./data"
LOG_PATH = "./data/logs"
```

Save it. Then open `.env` and paste this:
```
OPENAI_API_KEY=your_openai_api_key_here
NEWS_API_KEY=your_newsapi_key_here