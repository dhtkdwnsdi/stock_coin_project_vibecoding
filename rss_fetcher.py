import feedparser
from datetime import datetime, timedelta, timezone
import dateutil.parser
import streamlit as st

def fetch_and_filter_feeds(feeds: list[str], days_limit: int = 3) -> list[dict]:
    """Retrieve articles from a list of RSS feed URLs and filter by date."""
    articles = []
    
    # Calculate cutoff date
    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(days=days_limit)
    
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                # Parse published date
                pub_date_str = getattr(entry, "published", getattr(entry, "updated", None))
                if not pub_date_str:
                    continue
                    
                try:
                    pub_date = dateutil.parser.parse(pub_date_str)
                    # Make aware if naive
                    if pub_date.tzinfo is None:
                        pub_date = pub_date.replace(tzinfo=timezone.utc)
                except Exception:
                    continue
                
                if pub_date >= cutoff_date:
                    articles.append({
                        "title": getattr(entry, "title", "제목 없음"),
                        "link": getattr(entry, "link", url),
                        "published": pub_date.isoformat(),
                        "summary": getattr(entry, "summary", "")
                    })
        except Exception as e:
            st.warning(f"Failed to fetch {url}: {e}")
            continue
            
    # Sort articles by date descending
    articles.sort(key=lambda x: x["published"], reverse=True)
    return articles
