import re
import time
from typing import Dict, List, Self
from bs4 import BeautifulSoup
import feedparser
from pydantic import BaseModel
import requests
from tqdm import tqdm


RSS_FEEDS = [
    "https://www.dealnews.com/c142/Electronics/?rss=1",
    "https://www.dealnews.com/c39/Computers/?rss=1",
    "https://www.dealnews.com/c238/Automotive/?rss=1",
    "https://www.dealnews.com/f1912/Smart-Home/?rss=1",
    "https://www.dealnews.com/c196/Home-Garden/?rss=1",
]


def extract(html_snippet: str) -> str:
    """Use BeautifulSoup to clean up HTML snippets and extract readable text."""
    soup = BeautifulSoup(html_snippet, 'html.parser')
    snippet_div = soup.find('div', class_='snippet summary')
    
    if snippet_div:
        description = snippet_div.get_text(strip=True)
        description = BeautifulSoup(description, 'html.parser').get_text()
        description = re.sub('<[^<]+?>', '', description)
        result = description.strip()
    else:
        result = html_snippet
    return result.replace('\n', ' ')


class ScrapedDeal:
    """Represents a deal retrieved from an e-commerce RSS feed."""

    category: str
    title: str
    summary: str
    url: str
    details: str
    features: str

    def __init__(self, entry: Dict[str, str]):
        self.title = entry['title']
        self.summary = extract(entry['summary'])
        self.url = entry['links'][0]['href']
        
        try:
            response = requests.get(self.url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            content_section = soup.find('div', class_='content-section')
            if content_section:
                content = content_section.get_text().replace('\nmore', '').replace('\n', ' ')
            else:
                content = self.summary
        except Exception:
            content = self.summary

        if "Features" in content:
            self.details, self.features = content.split("Features", 1)
        else:
            self.details = content
            self.features = ""

    def __repr__(self) -> str:
        return f"<ScrapedDeal: {self.title}>"

    def describe(self) -> str:
        """Returns structured textual representation for LLM prompt context."""
        return (
            f"Title: {self.title}\n"
            f"Details: {self.details.strip()}\n"
            f"Features: {self.features.strip()}\n"
            f"URL: {self.url}"
        )

    @classmethod
    def fetch(cls, show_progress: bool = False, max_per_feed: int = 10) -> List[Self]:
        """Retrieve deals from selected RSS feeds."""
        deals = []
        feed_iter = tqdm(RSS_FEEDS) if show_progress else RSS_FEEDS
        for feed_url in feed_iter:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:max_per_feed]:
                    deals.append(cls(entry))
                    time.sleep(0.5)
            except Exception:
                continue
        return deals


class Deal(BaseModel):
    """Pydantic model representing a structured Deal."""
    product_description: str
    price: float
    url: str


class DealSelection(BaseModel):
    """Structured response container for LLM Structured Outputs."""
    deals: List[Deal]


class Opportunity(BaseModel):
    """Represents an identified high-margin discount opportunity."""
    deal: Deal
    estimate: float
    discount: float
