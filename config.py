import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.0
MAX_TOKENS = 1000

NEWS_TOPICS = ["technology", "geopolitics", "ai"]
MAX_ARTICLES_PER_RUN = 20
NEWS_LANGUAGE = "en"

CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "news_facts"

MIN_SOURCES_FOR_VERDICT = 2
CONFIDENCE_THRESHOLD = 0.6

DATA_PATH = "./data"
LOG_PATH = "./data/logs"

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")