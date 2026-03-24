import feedparser
import requests
import hashlib
from datetime import datetime
from config import NEWS_API_KEY, NEWS_TOPICS, MAX_ARTICLES_PER_RUN

RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://rss.cnn.com/rss/edition.rss",
    "https://feeds.reuters.com/reuters/topNews",
]

def get_article_hash(title: str) -> str:
    return hashlib.md5(title.encode()).hexdigest()

def scrape_newsapi() -> list[dict]:
    articles = []
    for topic in NEWS_TOPICS:
        try:
            url = (
                f"https://newsapi.org/v2/everything?"
                f"q={topic}&language=en&sortBy=publishedAt"
                f"&pageSize={MAX_ARTICLES_PER_RUN}&apiKey={NEWS_API_KEY}"
            )
            response = requests.get(url, timeout=10)
            data = response.json()
            if data.get("status") == "ok":
                for a in data.get("articles", []):
                    articles.append({
                        "title": a.get("title", ""),
                        "content": a.get("content") or a.get("description", ""),
                        "url": a.get("url", ""),
                        "source": a.get("source", {}).get("name", "unknown"),
                        "published_at": a.get("publishedAt", ""),
                        "topic": topic,
                        "hash": get_article_hash(a.get("title", "")),
                        "ingested_at": datetime.utcnow().isoformat(),
                    })
        except Exception as e:
            print(f"[Scraper] NewsAPI error for topic {topic}: {e}")
    return articles

def scrape_rss_feeds() -> list[dict]:
    articles = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                articles.append({
                    "title": entry.get("title", ""),
                    "content": entry.get("summary", ""),
                    "url": entry.get("link", ""),
                    "source": feed.feed.get("title", "unknown"),
                    "published_at": entry.get("published", ""),
                    "topic": "general",
                    "hash": get_article_hash(entry.get("title", "")),
                    "ingested_at": datetime.utcnow().isoformat(),
                })
        except Exception as e:
            print(f"[Scraper] RSS error for {feed_url}: {e}")
    return articles

def deduplicate(articles: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for article in articles:
        if article["hash"] not in seen:
            seen.add(article["hash"])
            unique.append(article)
    return unique

def run_scraper() -> list[dict]:
    print("[Scraper] Starting ingestion...")
    articles = scrape_newsapi() + scrape_rss_feeds()
    articles = deduplicate(articles)
    print(f"[Scraper] Collected {len(articles)} unique articles")
    return articles